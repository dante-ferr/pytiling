from typing import TypedDict, Callable
import numpy as np
from .layer_checker import LayerChecker


class Area(TypedDict):
    top_left: tuple[int, int]
    bottom_right: tuple[int, int]


class GridLayer:
    def __init__(self, name: str):
        self.name = name
        self._tile_size: tuple[int, int] | None = None

        self.checker = LayerChecker(self)

    def initialize_grid(self, size: tuple[int, int]):
        """Initialize the grid of the tilemap layer."""
        self.grid = np.empty(size, dtype=object)

    @property
    def tile_size(self) -> tuple[int, int]:
        """Get the tile size of the layer."""
        if not self._tile_size:
            raise ValueError(
                "Tile size not set for the layer. Ensure it has been added to a tilemap."
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
        """Get the grid of the tilemap layer."""
        self.checker.check_grid()
        assert self._grid is not None
        return self._grid

    @grid.setter
    def grid(self, grid: np.ndarray):
        """Set the grid of the tilemap layer."""
        self._grid = grid

    @property
    def grid_size(self) -> tuple[int, int]:
        """Get the size of the grid."""
        self.checker.check_grid()
        return self.grid.shape

    @grid_size.setter
    def grid_size(self, size: tuple[int, int]):
        """Set the size of the grid."""
        self.grid = np.resize(self.grid, size)

    def grid_pos_to_actual_pos(
        self, position: tuple[int, int], invert_x_axis=False, invert_y_axis=True
    ) -> tuple[float, float]:
        """Convert a tile position in the tilemap layer to an actual position in the window."""
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
        """Convert an actual position in the window to a tile position in the tilemap layer."""
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
        self.checker.check_grid()
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
