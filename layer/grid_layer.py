from typing import TypedDict, Callable
import numpy as np
from .layer_checker import LayerChecker
from functools import cached_property
from utils import reduce_grid_towards, expand_grid_towards, Direction
from typing import TYPE_CHECKING, Literal, Any, Union, cast

if TYPE_CHECKING:
    from ..grid_map import GridMap
    from grid_element import GridElement


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

    def initialize_grid(self, size: tuple[int, int]):
        """Initialize the grid of the layer."""
        self.grid = np.empty(size, dtype=object)

    def add_create_tile_callback(self, callback: Callable):
        """Add a callback to be called when any element in the layer is added."""
        self.create_element_callbacks.append(callback)

    def add_remove_tile_callback(self, callback: Callable):
        """Add a callback to be called when any element in the layer is removed."""
        self.remove_element_callbacks.append(callback)

    def add_element(self, element: "GridElement"):
        """Add an element to the layer's grid."""
        element.layer = self
        self.grid[element.position[1], element.position[0]] = element

        for callback in self.create_element_callbacks:
            callback(element)

    def remove_element(self, element: "GridElement"):
        """Remove an element from the layer's grid."""
        self.grid[element.position[1], element.position[0]] = None

        for callback in self.remove_element_callbacks:
            callback(element, self.name)

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
                "Grid is not initialized. Make sure to add this layer to a tilemap before adding tiles."
            )

        assert self._grid is not None
        return self._grid

    @grid.setter
    def grid(self, grid: np.ndarray):
        """Set the grid of the layer."""
        self._grid = grid

    @property
    def grid_size(self) -> tuple[int, int]:
        """Get the size of the grid."""
        return self.grid.shape

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

    def for_grid_position(self, callback: Callable):
        """Loops over each grid position in the layer's grid, calling the given callback."""
        for y in range(self.grid.shape[0]):
            for x in range(self.grid.shape[1]):
                callback(x, y)

    def get_area_around(self, center: tuple[int, int], radius: int) -> Area:
        """Get an area around a center point with a given radius."""
        center_x, center_y = center
        grid_height, grid_width = self.grid.shape

        top_left_x = max(center_x - radius, 0)
        top_left_y = max(center_y - radius, 0)
        bottom_right_x = min(center_x + radius, grid_width - 1)
        bottom_right_y = min(center_y + radius, grid_height - 1)

        return Area(
            top_left=(top_left_x, top_left_y),
            bottom_right=(bottom_right_x, bottom_right_y),
        )

    def loop_over_area(self, area: "Area", callback):
        """Loop over an area of the grid and call a callback function for each tile in the area."""
        top_left_x, top_left_y = area["top_left"]
        bottom_right_x, bottom_right_y = area["bottom_right"]

        for x in range(top_left_x, bottom_right_x + 1):
            for y in range(top_left_y, bottom_right_y + 1):
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
        fill_callback: Callable[[tuple[int, int]], Any],
        size: int,
    ):
        """Expand the grid in the specified direction."""
        self.grid = expand_grid_towards(self.grid, direction, fill_callback, size)

    def reduce_towards(self, direction: Direction, size: int):
        """Reduce the grid in the specified direction."""
        self.grid = reduce_grid_towards(self.grid, direction, size)

    def get_edge_positions(
        self, edge: Union[Direction, Literal["all"]] = "all", retreat=0
    ):
        """Get the positions of the edges of the layer."""
        height, width = self.grid_size
        edge_positions: set[tuple[int, int]] = set()

        if edge in ("left", "all"):
            for y in range(height):
                edge_positions.add((retreat, y))

        if edge in ("right", "all"):
            for y in range(height):
                edge_positions.add((width - 1 - retreat, y))

        if edge in ("bottom", "all"):
            for x in range(width):
                edge_positions.add((x, height - 1 - retreat))

        if edge in ("top", "all"):
            for x in range(width):
                edge_positions.add((x, retreat))

        return list(edge_positions)

    def get_element_at(self, position: tuple[int, int]):
        """Get an element at a given position, or None if there is no element at that position."""
        if self.checker.position_is_valid(position):
            return cast("GridElement", self.grid[position[1], position[0]])
        return None
