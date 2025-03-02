from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tileset import Tileset
    from .tilemap_layer import TilemapLayer


class Tilemap:
    """A class representing a tilemap. It contains a dictionary of tilemap layers."""

    layers: dict[str, "TilemapLayer"]
    tilesets: set["Tileset"]

    def __init__(self, size: tuple[int, int] = (8, 8)):

        self.layers = {}
        self.tilesets = set()
        self.size = size

    def add_layer(self, layer: "TilemapLayer"):
        """Add a layer to the tilemap"""
        layer.initialize_grid(self.size)
        self.tilesets.add(layer.tileset)
        self.layers[layer.name] = layer

    def set_size(self, size: tuple[int, int]):
        """Set the size of the tilemap. This will resize all layers to match."""
        self.size = size
        for layer in self.layers.values():
            layer.set_size(size)
