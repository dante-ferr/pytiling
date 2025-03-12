from typing import TypedDict, Callable, cast, TYPE_CHECKING
import numpy as np
from ...tileset import Tileset
from ...tile.autotile.default_autotile_rules import default_rules
from ...tile.autotile.autotile_tile import AutotileTile
from .tilemap_layer_formatter import TilemapLayerFormatter
from ..layer_checker import LayerChecker
from ..grid_layer import GridLayer

if TYPE_CHECKING:
    from ...tile import Tile
    from ...tile.autotile import AutotileRule


class TilemapLayer(GridLayer):
    """A class representing a tilemap layer. It contains a grid of tiles."""

    autotile_rules: dict[str, list["AutotileRule"]]

    def __init__(self, name: str, tileset: Tileset):
        super().__init__(name, tileset.tile_size)
        self.name = name
        self.tile_size: tuple[int, int] = tileset.tile_size
        self.tileset = tileset
        self.autotile_rules = {}

        self._grid: np.ndarray | None = None

        self.create_tile_callbacks: list[Callable] = []
        self.remove_tile_callbacks: list[Callable] = []

        self.concurrent_layers: list[TilemapLayer] = []

        self.formatter = TilemapLayerFormatter(self)

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
        self.checker.check_grid()
        self.checker.check_position(tile.position)

        concurrent_tiles = self._concurrent_tiles_at(tile.position)
        for concurrent_tile in concurrent_tiles:
            # If the tile is locked, it can't be removed. Also, this function cannot add the tile, as it conflicts with the concurrent tile.
            if concurrent_tile.locked:
                return
            concurrent_tile.remove()

        if self.get_tile_at(tile.position) is not None:
            self.remove_tile(tile, apply_formatting=False)

        tile.layer = self
        self.grid[tile.position[1], tile.position[0]] = tile

        if isinstance(tile, AutotileTile):
            self._handle_add_autotile_tile(tile, apply_formatting)

        if apply_formatting:
            self.formatter.format_tile(tile)

        for callback in self.create_tile_callbacks:
            callback(tile)

    def _concurrent_tiles_at(self, position: tuple[int, int]):
        concurrent_tiles: list["Tile"] = []

        for concurrent_layer in self.concurrent_layers:
            tile = concurrent_layer.get_tile_at(position)
            if tile:
                concurrent_tiles.append(tile)
        return concurrent_tiles

    def _handle_add_autotile_tile(self, tile: "AutotileTile", apply_formatting: bool):
        """Handle adding an autotile tile to the layer."""
        if tile.autotile_object not in self.autotile_rules:
            self.autotile_rules[tile.autotile_object] = default_rules
        tile.rules = self.autotile_rules[tile.autotile_object]

        if apply_formatting:
            self.formatter.format_area(self.get_area_around(tile.position, 2))

    def remove_tile(self, tile: "Tile", apply_formatting=True):
        """Remove a tile from the layer's grid."""
        self.checker.check_grid()
        if tile.locked:
            return

        self.grid[tile.position[1], tile.position[0]] = None
        if apply_formatting:
            self.formatter.format_area(self.get_area_around(tile.position, 1))

        for callback in self.remove_tile_callbacks:
            callback(tile)

    def for_all_tiles(self, callback: Callable):
        """Loops over each tile in the layer's grid, calling the given callback."""
        self.checker.check_grid()

        def position_callback(x, y):
            tile = self.get_tile_at((x, y))
            if tile is not None:
                callback(self.get_tile_at((x, y)))

        self.for_grid_position(position_callback)

    def add_autotile_rule(self, autotile_object, *rules):
        """Append one or more rules to the list of rules for a specific autotile object."""
        for rule in rules:
            self.autotile_rules[autotile_object].append(rule)

    def set_autotile_rules(self, autotile_object, rules):
        """Set the list of rules for a specific autotile object. It resets the rules for that object, so it must be used when it's needed to overwrite the default rules."""
        self.autotile_rules[autotile_object] = rules

    def get_tile_at(self, position: tuple[int, int]):
        """Get a tile at a given position."""
        if self.checker.position_is_valid(position):
            return cast("Tile", self.grid[position[1], position[0]])
        return None

    def get_edge_tiles(self):
        """Get a list of tiles that are on the edges of the layer's grid, ensuring no duplicates at corners."""
        self.checker.check_grid()

        height, width = self.grid.shape
        edge_tiles = set()

        for y in range(height):
            tile = self.get_tile_at((0, y))
            if tile is not None:
                edge_tiles.add(tile)
            tile = self.get_tile_at((width - 1, y))
            if tile is not None:
                edge_tiles.add(tile)

        for x in range(1, width - 1):
            tile = self.get_tile_at((x, 0))
            if tile is not None:
                edge_tiles.add(tile)
            tile = self.get_tile_at((x, height - 1))
            if tile is not None:
                edge_tiles.add(tile)

        return list(edge_tiles)
