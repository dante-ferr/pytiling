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
from typing import TYPE_CHECKING, Literal, Any, Union, cast

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

        self.checker = LayerChecker(self)

        self.create_element_callbacks: list[Callable] = []
        self.remove_element_callbacks: list[Callable[["GridElement", str], None]] = []

        self.concurrent_layers: list["GridLayer"] = []

    def add_concurrent_layer(self, layer: "GridLayer"):
        """Add a layer to the list of concurrent layers. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a element on a layer will remove the elements at the same position from its concurrent layers."""
        self.concurrent_layers.append(layer)

    def _concurrent_elements_at(self, position: tuple[int, int]):
        concurrent_elements: list["GridElement"] = []

        for concurrent_layer in self.concurrent_layers:
            element = concurrent_layer.get_element_at(position)
            if element:
                concurrent_elements.append(element)
        return concurrent_elements

    def initialize_grid(self, size: tuple[int, int]):
        """Initialize the grid of the layer."""
        self.grid = np.empty(size, dtype=object)

    def add_create_element_callback(self, callback: Callable):
        """Add a callback to be called when any element in the layer is added."""
        self.create_element_callbacks.append(callback)

    def add_remove_element_callback(self, callback: Callable):
        """Add a callback to be called when any element in the layer is removed."""
        self.remove_element_callbacks.append(callback)

    def add_element(self, element: "GridElement"):
        """Add an element to the layer's grid."""
        self.checker.check_position(element.position)

        same_layer_element_in_place = self.get_element_at(element.position)
        if same_layer_element_in_place is not None:
            if same_layer_element_in_place.locked:
                return False
            self.remove_element(element)

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

        for callback in self.create_element_callbacks:
            callback(element)

        return True

    def remove_element_at(self, position: tuple[int, int]):
        """Remove a element at a given position."""
        element = self.get_element_at(position)
        if element is None:
            return False
        return self.remove_element(element)

    def remove_element(self, element: "GridElement"):
        """Remove an element from the layer's grid."""
        self.grid[element.position[1], element.position[0]] = None

        for callback in self.remove_element_callbacks:
            callback(element, self.name)

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
            self.grid.shape[1] * tile_width,
            self.grid.shape[0] * tile_height,
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

    def grid_pos_to_actual_pos(
        self, position: tuple[int, int], invert_x_axis=False, invert_y_axis=True
    ) -> tuple[float, float]:
        """Convert a tile position in the layer to an actual position in the window."""
        tile_width, tile_height = self.tile_size
        map_width, map_height = self.size
        pos = [position[0] * tile_width, position[1] * tile_height]

        if invert_x_axis:
            pos[0] = map_width - pos[0]
        if invert_y_axis:
            pos[1] = map_height - pos[1]

        return (pos[0], pos[1])

    def actual_pos_to_grid_pos(
        self, position: tuple[float, float], invert_x_axis=False, invert_y_axis=True
    ):
        """Convert an actual position in the window to a tile position in the layer."""
        tile_width, tile_height = self.tile_size
        map_width, map_height = self.size
        pos: list[int] = [
            int(position[0] // tile_width),
            int(position[1] // tile_height + 1),
        ]

        if invert_x_axis:
            pos[0] = int((map_width - position[0]) // tile_width)
        if invert_y_axis:
            pos[1] = int((map_height - position[1]) // tile_height + 1)

        return (*pos,)

    def for_all_elements(self, callback: Callable):
        """Loops over each element in the layer's grid, calling the given callback."""

        def position_callback(x, y):
            element = self.get_element_at((x, y))
            if element is not None:
                callback(self.get_element_at((x, y)))

        self.for_grid_position(position_callback)

    def for_grid_position(self, callback: Callable):
        """Loops over each grid position in the layer's grid, calling the given callback."""
        for y in range(self.grid.shape[0]):
            for x in range(self.grid.shape[1]):
                callback(x, y)

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
        deleted_elements = self.get_edge_elements(direction, size)
        self.grid = reduce_grid_towards(self.grid, direction, size)

        if direction == "top" or direction == "left":
            self.shift_elements_towards(direction, size)

        return deleted_elements

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
