from typing import TYPE_CHECKING, Literal, cast
from .grid_map import GridMap

if TYPE_CHECKING:
    from .tileset import Tileset
    from .layer.tilemap_layer import TilemapLayer
    from .layer.grid_layer import GridLayer


class Tilemap(GridMap):
    """
    A class representing a tilemap. It contains a dictionary of tilemap layers.
    The layers are ordered by default, but it's not mandatory to use them in order.
    """

    def __init__(self, grid_size: tuple[int, int]):
        super().__init__(grid_size)

        self.tilesets: set["Tileset"] = set()

    def add_layer(self, layer: "GridLayer", position: int | Literal["end"] = "end"):
        """Add a layer to the tilemap. By default, it will be added to the end of the list, so it's a good practice to add layers in order."""
        layer = cast("TilemapLayer", layer)

        if self._tile_size is not None and layer.tile_size != self._tile_size:
            raise ValueError(
                "Two tilesets with different tile sizes cannot be used on the same tilemap."
            )
        self._tile_size = layer.tile_size
        self.tilesets.add(layer.tileset)

        super().add_layer(layer, position)

    @property
    def layers(self) -> list["TilemapLayer"]:
        """Get the layers of the tilemap."""
        return cast(list["TilemapLayer"], self._layers)

    def add_format_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.formatter.add_format_callback(callback)

    def add_create_tile_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_create_tile_callback(callback)

    def add_remove_tile_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_remove_tile_callback(callback)

    @staticmethod
    def add_layer_concurrence(*layers: "TilemapLayer"):
        """Make the specified layers concurrent. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a tile on a layer will remove the tiles at the same position from its concurrent layers."""
        for layer in layers:
            other_layers = [l for l in layers if l is not layer]
            for other_layer in other_layers:
                layer.add_concurrent_layer(other_layer)
