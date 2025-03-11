from typing import TypedDict, Literal, Callable, cast
from ..tile.tile import Tile
import numpy as np
from ..tileset import Tileset
from ..tile.autotile.autotile_rule import AutotileRule
from ..tile.autotile.default_autotile_rules import default_rules
from ..tile.autotile.autotile_tile import AutotileTile
from .layer_neighbor_processor import LayerNeighborProcessor
from .layer_formatter import LayerFormatter


class Area(TypedDict):
    top_left: tuple[int, int]
    bottom_right: tuple[int, int]


class TilemapLayer:
    """A class representing a tilemap layer. It contains a grid of tiles."""

    autotile_rules: dict[str, list[AutotileRule]]

    def __init__(self, name: str, tileset: Tileset):
        self.name = name
        self.tileset = tileset
        self.autotile_rules = {}

        self.create_tile_callbacks: list[Callable] = []
        self.remove_tile_callbacks: list[Callable] = []

        self.concurrent_layers: list[TilemapLayer] = []

        self.neighbor_processor = LayerNeighborProcessor(self)
        self.formatter = LayerFormatter(self)

    def initialize_grid(self, size: tuple[int, int]):
        """Initialize the grid of the tilemap layer."""
        self.grid = np.empty(size, dtype=object)

    @property
    def grid_size(self) -> tuple[int, int]:
        """Get the size of the grid."""
        return self.grid.shape

    @grid_size.setter
    def grid_size(self, size: tuple[int, int]):
        """Set the size of the grid."""
        self.grid = np.resize(self.grid, size)

    @property
    def tile_size(self):
        return self.tileset.tile_size

    @property
    def size(self):
        tile_width, tile_height = self.tile_size
        return (
            self.grid.shape[1] * tile_width,
            self.grid.shape[0] * tile_height,
        )

    def add_concurrent_layer(self, layer: "TilemapLayer"):
        """Add a layer to the list of concurrent layers. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a tile on a layer will remove the tiles at the same position from its concurrent layers."""
        self.concurrent_layers.append(layer)

    def add_create_tile_callback(self, callback: Callable):
        """Add a callback to be called when any tile in the layer is added."""
        self.create_tile_callbacks.append(callback)

    def add_remove_tile_callback(self, callback: Callable):
        """Add a callback to be called when any tile in the layer is removed."""
        self.remove_tile_callbacks.append(callback)

    def add_tile(self, tile: "Tile", apply_formatting=True):
        """Add a tile to the layer's grid. Also formats the tile and its potential neighbors."""
        self._check_grid()
        self._check_position_is_valid(tile.position)

        if self.get_tile_at(tile.position) is not None:
            self.remove_tile(tile, apply_formatting=False)

        tile.layer = self
        self.grid[tile.position[1], tile.position[0]] = tile

        if isinstance(tile, AutotileTile):
            self._handle_add_autotile_tile(tile, apply_formatting)

        if apply_formatting:
            self.formatter.format_tile(tile)

        # Remove concurrent tiles
        for concurrent_layer in self.concurrent_layers:
            concurrent_tile = concurrent_layer.get_tile_at(tile.position)
            if concurrent_tile is not None:
                concurrent_layer.remove_tile(concurrent_tile)

        for callback in self.create_tile_callbacks:
            callback(tile)

    def _handle_add_autotile_tile(self, tile: "AutotileTile", apply_formatting: bool):
        """Handle adding an autotile tile to the layer."""
        if tile.autotile_object is None:
            raise ValueError("Autotile object must be set for autotile tiles.")

        if tile.autotile_object not in self.autotile_rules:
            self.autotile_rules[tile.autotile_object] = default_rules
        tile.rules = self.autotile_rules[tile.autotile_object]

        if apply_formatting:
            self.formatter.format_area(self._get_area_around(tile.position, 2))

    def remove_tile(self, tile: "Tile", apply_formatting=True):
        """Remove a tile from the layer's grid."""
        self._check_grid()
        self._check_position_is_valid(tile.position)

        self.grid[tile.position[1], tile.position[0]] = None
        if apply_formatting:
            self.formatter.format_area(self._get_area_around(tile.position, 1))

        for callback in self.remove_tile_callbacks:
            callback(tile)

    def add_autotile_rule(self, autotile_object, *rules):
        """Append one or more rules to the list of rules for a specific autotile object."""
        for rule in rules:
            self.autotile_rules[autotile_object].append(rule)

    def set_autotile_rules(self, autotile_object, rules):
        """Set the list of rules for a specific autotile object. It resets the rules for that object, so it must be used when it's needed to overwrite the default rules."""
        self.autotile_rules[autotile_object] = rules

    def get_tile_at(self, position: tuple[int, int]):
        """Get a tile at a given position."""
        if self._position_is_valid(position):
            return cast(Tile, self.grid[position[1], position[0]])
        return None

    def _get_area_around(self, center: tuple[int, int], radius: int) -> Area:
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

    def _check_grid(self):
        if self.grid is None:
            raise ValueError(
                "Grid is not initialized. Make sure to add this layer to a tilemap before adding tiles."
            )

    def _check_position_is_valid(self, position: tuple[int, int] | None):
        if position is None:
            raise ValueError(
                "Tile position cannot be None. Ensure to set the position of the tile before adding it to the layer."
            )

        if not self._position_is_valid(position):
            raise ValueError(
                f"Position {position} is not valid, because it is out of bounds for the grid ({self.grid.shape})."
            )

    def _position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.grid.shape[1]
            and position[1] < self.grid.shape[0]
        )

    def loop_over_area(self, area: "Area", callback):
        """Loop over an area of the grid and call a callback function for each tile in the area."""
        top_left_x, top_left_y = area["top_left"]
        bottom_right_x, bottom_right_y = area["bottom_right"]

        for x in range(top_left_x, bottom_right_x + 1):
            for y in range(top_left_y, bottom_right_y + 1):
                callback(x, y)

    def tilemap_pos_to_actual_pos(
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

    def actual_pos_to_tilemap_pos(
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
