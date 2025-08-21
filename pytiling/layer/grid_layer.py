from typing import TypedDict, Callable
import numpy as np
from .layer_checker import LayerChecker
from functools import cached_property
from pytiling.utils import (
    reduce_grid_towards,
    expand_grid_towards,
    Direction,
    opposite_directions,
    direction_vectors,
)
from typing import TYPE_CHECKING, Literal, Union, cast
from blinker import Signal

if TYPE_CHECKING:
    from ..grid_map import GridMap
    from pytiling.grid_element import GridElement


class Area(TypedDict):
    top_left: tuple[int, int]
    bottom_right: tuple[int, int]


class GridLayer:

    def __init__(self, name: str):
        self.name = name
        self._tile_size: tuple[int, int] | None = None
        self._grid_map: "GridMap | None" = None
        self._grid: np.ndarray | None = None

        self.checker = LayerChecker(self)

        self.concurrent_layers: set["GridLayer"] = set()

        self._restart_events()

    def _restart_events(self):
        self.events: dict[str, Signal] = {
            "element_created": Signal(),
            "element_removed": Signal(),
            "element_directly_removed": Signal(),
        }

    def populate_from_data(self, elements_data: list[dict]):
        """Populate the layer with elements from a list of data dictionaries."""
        from ..serialization import element_from_dict

        for element_data in elements_data:
            element = element_from_dict(element_data)
            self.add_element(element)

    def to_dict(self):
        """Serialize the layer to a dictionary."""
        elements_data = []
        for element in self.elements:
            elements_data.append(element.to_dict())

        return {
            "__class__": "GridLayer",
            "name": self.name,
            "grid_size": self.grid_size,
            "elements": elements_data,
            "concurrent_layers": [layer.name for layer in self.concurrent_layers],
        }

    def add_concurrent_layer(self, layer: "GridLayer"):
        """Add a layer to the list of concurrent layers. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a element on a layer will remove the elements at the same position from its concurrent layers."""
        self.concurrent_layers.add(layer)

    def _concurrent_elements_at(self, position: tuple[int, int]):
        concurrent_elements: list["GridElement"] = []

        for concurrent_layer in self.concurrent_layers:
            element = concurrent_layer.get_element_at(position)
            if element:
                concurrent_elements.append(element)
        return concurrent_elements

    def initialize_grid(self, size: tuple[int, int]):
        """Initialize the grid of the layer."""
        if self._grid is None:
            self._grid = np.empty((size[1], size[0]), dtype=object)

    def add_element(self, element: "GridElement"):
        """Add an element to the layer's grid."""
        self.checker.check_position(element.position)

        same_layer_element_in_place = self.get_element_at(element.position)
        if same_layer_element_in_place is not None:
            if same_layer_element_in_place.locked:
                return False
            self._remove_element(element)

        concurrent_elements_in_place = self._concurrent_elements_at(element.position)
        for concurrent_element in concurrent_elements_in_place:
            # If the element is locked, it can't be removed. Also, this function cannot add the element, as it conflicts with the concurrent element.
            if concurrent_element.locked:
                return False
            concurrent_element.remove()

        if element.unique:
            namesakes = self.get_namesakes(element.name)
            for namesake in namesakes:
                namesake.remove()

        element.layer = self
        self.grid[element.position[1], element.position[0]] = element

        self.events["element_created"].send(element=element)

        return True

    def remove_element_at(self, position: tuple[int, int]):
        """Remove a element at a given position."""
        element = self.get_element_at(position)
        if element is None:
            return None

        self.remove_element(element)
        return element

    def remove_element(self, element: "GridElement"):
        """Remove an element from the layer's grid."""
        self._remove_element(element)

        self.events["element_directly_removed"].send(
            element=element, layer_name=self.name
        )

    def _remove_element(self, element: "GridElement"):
        """Private method to remove an element from the layer's grid. The difference
        between this method and remove_element resides in the sent event: while this
        sends a generic element_removed event, remove_element sends a element_directly_removed event.
        """
        self.grid[element.position[1], element.position[0]] = None

        self.events["element_removed"].send(element=element, layer_name=self.name)

    def amount_of_namesakes(self, name: str):
        amount = 0

        def _check_name(element: "GridElement"):
            nonlocal amount
            if element.name == name:
                amount += 1

        self.for_all_elements(_check_name)
        return amount

    def get_namesakes(self, name: str):
        namesakes: list["GridElement"] = []

        def _check_name(element: "GridElement"):
            if element.name == name:
                namesakes.append(element)

        self.for_all_elements(_check_name)

        return namesakes

    def has_element_named(self, name: str):
        return self.amount_of_namesakes(name) > 0

    def has_element_at(self, position: tuple[int, int]):
        return self.get_element_at(position) is not None

    def grid_pos_to_actual_pos(
        self, position: tuple[int, int], invert_x_axis=False, invert_y_axis=True
    ) -> tuple[float, float]:
        return self.grid_map.grid_pos_to_actual_pos(
            position, invert_x_axis, invert_y_axis
        )

    def actual_pos_to_grid_pos(
        self, position: tuple[float, float], invert_x_axis=False, invert_y_axis=True
    ):
        return self.grid_map.actual_pos_to_grid_pos(
            position, invert_x_axis, invert_y_axis
        )

    @property
    def grid_map(self) -> "GridMap":
        """Get the grid_map of the layer."""
        if not self._grid_map:
            raise ValueError(
                "Grid map not set for the layer. Ensure it has been added to a map."
            )
        return self._grid_map

    @grid_map.setter
    def grid_map(self, grid_map: "GridMap"):
        """Set the grid_map of the layer."""
        self._grid_map = grid_map
        self.tile_size = grid_map.tile_size

    @property
    def tile_size(self) -> tuple[int, int]:
        """Get the tile size of the layer."""
        if not self._tile_size:
            raise ValueError(
                "Tile size not set for the layer. Ensure it has been added to a map."
            )

        return self._tile_size

    @tile_size.setter
    def tile_size(self, tile_size: tuple[int, int]):
        """Set the tile size of the layer."""
        self._tile_size = tile_size

    @property
    def size(self):
        tile_width, tile_height = self.tile_size
        return (
            self.grid_size[0] * tile_width,
            self.grid_size[1] * tile_height,
        )

    @property
    def grid(self) -> np.ndarray:
        """Get the grid of the layer."""
        if self._grid is None:
            raise ValueError(
                "Grid is not initialized. Make sure to add this layer to a map before anything else."
            )

        return self._grid

    @grid.setter
    def grid(self, grid: np.ndarray):
        """Set the grid of the layer."""
        self._grid = grid

    @property
    def grid_size(self) -> tuple[int, int]:
        """Get the size of the grid."""
        return (self.grid.shape[1], self.grid.shape[0])

    def resize(self, size: tuple[int, int]):
        """Set the size of the grid."""
        self.grid = np.resize(self.grid, size)

    def for_all_elements(self, callback: Callable):
        """Loops over each element in the layer's grid, calling the given callback."""

        def position_callback(position):
            element = self.get_element_at(position)
            if element is not None:
                callback(self.get_element_at(position))

        self.grid_map.for_grid_position(position_callback)

    @cached_property
    def layer_above(self) -> "GridLayer | None":
        """Get the layer above this layer (if it exists)."""
        if self.index + 1 < len(self.grid_map.layers):
            return self.grid_map.layers[self.index + 1]
        return None

    @cached_property
    def layer_below(self) -> "GridLayer | None":
        """Get the layer below this layer (if it exists)."""
        if self.index - 1 >= 0:
            return self.grid_map.layers[self.index - 1]
        return None

    @cached_property
    def index(self) -> int:
        """Get the index of the layer in the layer stack."""
        return self.grid_map.layers.index(self)

    def expand_towards(
        self,
        direction: Direction,
        size: int,
    ):
        """Expand the grid in the specified direction. Returns the positions that were added."""
        self.grid = expand_grid_towards(self.grid, direction, size)

        if direction == "top" or direction == "left":
            self.shift_elements_towards(opposite_directions[direction], size)

    def reduce_towards(self, direction: Direction, size: int):
        """Reduce the grid in the specified direction."""
        self.grid = reduce_grid_towards(self.grid, direction, size)

        if direction == "top" or direction == "left":
            self.shift_elements_towards(direction, size)

    def shift_elements_towards(self, direction: Direction, size: int):
        """Shift the grid in the specified direction."""
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                element = self.grid[y, x]
                if element is None:
                    continue
                element.position = (
                    element.position[0] + direction_vectors[direction][0] * size,
                    element.position[1] + direction_vectors[direction][1] * size,
                )

    def get_edge_elements(
        self, edge: Union[Direction, Literal["all"]] = "all", size=1, retreat=0
    ):
        """Get a set of elements on specified edges of the layer's grid, ensuring no duplicates at corners."""
        edge_elements: "list[GridElement | None]" = []

        for pos in self.grid_map.get_edge_positions(edge, size, retreat=retreat):
            element = self.get_element_at(pos)
            edge_elements.append(element)

        return edge_elements

    def get_element_at(self, position: tuple[int, int]):
        """Get an element at a given position, or None if there is no element at that position."""
        if self.checker.position_is_valid(position):
            return cast("GridElement", self.grid[position[1], position[0]])
        return None

    @property
    def elements(self) -> list["GridElement"]:
        """Get a list of all elements in the layer."""
        elements: list["GridElement"] = []
        self.for_all_elements(lambda element: elements.append(element))
        return elements

    def get_elements(self, *names: str) -> list["GridElement"]:
        """Get a list of elements with any of the given names."""
        elements: list["GridElement"] = []
        for element in self.elements:
            for name in names:
                if element.name == name:
                    elements.append(element)

        return elements

    def __getstate__(self):
        state = self.__dict__.copy()

        state["events"] = {}
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        self._restart_events()
