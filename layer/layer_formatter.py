from typing import TYPE_CHECKING, Callable, Literal

if TYPE_CHECKING:
    from .tilemap_layer import TilemapLayer, Area
    from ..tile import Tile


class LayerFormatter:
    def __init__(self, layer: "TilemapLayer"):
        self.layer = layer

        self.format_callbacks: list[Callable] = []

    def add_format_callback(self, callback: Callable):
        """Add a callback to be called when any tile in the layer is formatted."""
        self.format_callbacks.append(callback)

    def format_area(self, area: "Area | Literal['all']" = "all", format_center=False):
        """Format the grid of tiles."""
        radius = 2
        if area == "all":
            area = Area(
                top_left=(0, 0),
                bottom_right=(
                    self.layer.grid.shape[1] - radius,
                    self.layer.grid.shape[0] - radius,
                ),
            )

        def tile_format_callback(x, y):
            area_center = (
                area["bottom_right"][0] // 2,
                area["bottom_right"][1] // 2,
            )
            if not format_center and x == area_center[0] and y == area_center[1]:
                return

            tile = self.layer.get_tile_at((x, y))
            if tile is None:
                return
            self.format_tile(tile)

        self.layer.loop_over_area(area, tile_format_callback)

    def format_tile(self, tile: "Tile"):
        """Format a tile."""
        tile.format()
        for callback in self.format_callbacks:
            callback(tile)

    def format_all_tiles(self):
        """Format all tiles in the layer."""
        self.layer.for_all_tiles(self.format_tile)
