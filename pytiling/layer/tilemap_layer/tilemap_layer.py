from typing import Union, Callable, cast, TYPE_CHECKING, Literal
import numpy as np
from pytiling.tileset.tileset import Tileset
from pytiling.grid_element.tile.autotile.default_autotile_rules import default_rules
from pytiling.grid_element.tile.autotile.autotile_tile import AutotileTile
from .tilemap_layer_formatter import TilemapLayerFormatter
from ..layer_checker import LayerChecker
from ..grid_layer import GridLayer
from .tilemap_layer_neighbor_processor import TilemapLayerNeighborProcessor
from functools import cached_property
from pytiling.utils import Direction

if TYPE_CHECKING:
    from grid_element.tile import Tile
    from grid_element.tile.autotile import AutotileRule


class TilemapLayer(GridLayer):
    """A class representing a tilemap layer. It contains a grid of tiles."""

    autotile_rules: dict[str, list["AutotileRule"]]

    def __init__(self, name: str, tileset: Tileset):
        super().__init__(name)
        self.name = name
        self.tileset = tileset
        self.autotile_rules = {}
        self.autotile_neighbor_processor = TilemapLayerNeighborProcessor(self)

        self.concurrent_layers: list[TilemapLayer] = []

        self.formatter = TilemapLayerFormatter(self)

    def add_concurrent_layer(self, layer: "TilemapLayer"):
        """Add a layer to the list of concurrent layers. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a tile on a layer will remove the tiles at the same position from its concurrent layers."""
        self.concurrent_layers.append(layer)

    def add_tile(self, tile: "Tile", apply_formatting=True):
        """Add a tile to the layer's grid. Also formats the tile and its potential neighbors."""
        print(f"Grid size: {self.grid.shape}")
        self.checker.check_position(tile.position)

        # TODO: Make concurrency a feature of grid_layer.
        concurrent_tiles_in_place = self._concurrent_tiles_at(tile.position)
        for concurrent_tile in concurrent_tiles_in_place:
            # If the tile is locked, it can't be removed. Also, this function cannot add the tile, as it conflicts with the concurrent tile.
            if concurrent_tile.locked:
                return
            concurrent_tile.remove()

        same_layer_tile_in_place = self.get_tile_at(tile.position)
        if same_layer_tile_in_place is not None:
            if same_layer_tile_in_place.locked:
                return
            self.remove_tile(tile, apply_formatting=False)

        super().add_element(tile)

        if isinstance(tile, AutotileTile):
            self._handle_add_autotile_tile(tile, apply_formatting)

        if apply_formatting:
            self.formatter.format_tile(tile)

    def _concurrent_tiles_at(self, position: tuple[int, int]):
        concurrent_tiles: list["Tile"] = []

        for concurrent_layer in self.concurrent_layers:
            tile = concurrent_layer.get_tile_at(position)
            if tile:
                concurrent_tiles.append(tile)
        return concurrent_tiles

    def _handle_add_autotile_tile(self, tile: "AutotileTile", apply_formatting: bool):
        """Handle adding an autotile tile to the layer."""
        if tile.tile_object not in self.autotile_rules:
            self.autotile_rules[tile.tile_object] = default_rules
        tile.rules = self.autotile_rules[tile.tile_object]

        if apply_formatting:
            self._format_autotile_tile_neighbors(tile)

    def _format_autotile_tile_neighbors(self, tile: "AutotileTile"):
        tile_neighbors = self.autotile_neighbor_processor.get_neighbors_of(
            tile, radius=2
        )
        for row in tile_neighbors:
            for neighbor in row:
                if not isinstance(neighbor, AutotileTile):
                    continue
                self.formatter.format_tile(neighbor)

    def remove_tile(self, tile: "Tile", apply_formatting=True):
        """Remove a tile from the layer's grid."""
        if tile.locked:
            return

        super().remove_element(tile)
        if apply_formatting:
            self.formatter.format_area(self.get_area_around(tile.position, 1))

    @property
    def tiles(self):
        """Get all tiles in the layer."""
        tiles: list["Tile"] = []
        self.for_all_tiles(lambda tile: tiles.append(tile))
        return tiles

    def for_all_tiles(self, callback: Callable):
        """Loops over each tile in the layer's grid, calling the given callback."""

        def position_callback(x, y):
            tile = self.get_tile_at((x, y))
            if tile is not None:
                callback(self.get_tile_at((x, y)))

        self.for_grid_position(position_callback)

    def add_autotile_rule(self, tile_object, *rules):
        """Append one or more rules to the list of rules for a specific autotile object."""
        for rule in rules:
            self.autotile_rules[tile_object].append(rule)

    def set_autotile_rules(self, tile_object, rules):
        """Set the list of rules for a specific autotile object. It resets the rules for that object, so it must be used when it's needed to overwrite the default rules."""
        self.autotile_rules[tile_object] = rules

    def get_tile_at(self, position: tuple[int, int]):
        """Get a tile at a given position."""
        if self.checker.position_is_valid(position):
            return cast("Tile", self.grid[position[1], position[0]])
        return None

    def get_edge_tiles(
        self, edge: Union[Direction, Literal["all"]] = "all", retreat=0
    ) -> "list[Tile | None]":
        """Get a set of tiles on specified edges of the layer's grid, ensuring no duplicates at corners."""
        return [
            cast("Tile | None", element)
            for element in self.get_edge_elements(edge, retreat)
        ]

    @cached_property
    def layer_above(self) -> "TilemapLayer | None":
        """Get the layer above this layer (if it exists)."""
        return cast("TilemapLayer | None", super().layer_above)

    @cached_property
    def layer_below(self) -> "TilemapLayer | None":
        """Get the layer below this layer (if it exists)."""
        return cast("TilemapLayer | None", super().layer_below)
