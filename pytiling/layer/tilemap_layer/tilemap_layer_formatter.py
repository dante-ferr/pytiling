from typing import TYPE_CHECKING, Callable, Literal
from pytiling.grid_element.tile.autotile import AutotileTile

if TYPE_CHECKING:
    from . import TilemapLayer
    from ..grid_layer import Area
    from grid_element.tile import Tile


class TilemapLayerFormatter:
    def __init__(self, layer: "TilemapLayer"):
        self.layer = layer

        self.format_callbacks: list[Callable] = []

    def add_format_callback(self, callback: Callable):
        """Add a callback to be called when the layer is formatted and the tile's display has changed."""
        self.format_callbacks.append(callback)

    def format_autotile_tile_neighbors(self, tile: "AutotileTile"):
        # self.formatter.format_area(self.get_area_around(tile.position, 2))
        tile_neighbors = self.layer.autotile_neighbor_processor.get_neighbors_of(
            tile, radius=2
        )
        for row in tile_neighbors:
            for neighbor in row:
                if not isinstance(neighbor, AutotileTile):
                    continue
                self.format_tile(neighbor)

    def format_tile(self, tile: "Tile"):
        """Format a tile."""
        tile_changed = tile.format()

        if tile_changed:
            for callback in self.format_callbacks:
                callback(tile)

    def format_all_tiles(self):
        """Format all tiles in the layer."""
        self.layer.for_all_elements(self.format_tile)
