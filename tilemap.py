from .tilemap_layer import TilemapLayer


class Tilemap:
    """A class representing a tilemap. It contains a dictionary of tilemap layers."""

    layers: dict[str, TilemapLayer]

    def __init__(self, size: tuple[int, int] = (8, 8)):

        self.layers = {}
        self.size = size

    def add_layer(self, layer: TilemapLayer):
        """Add a layer to the tilemap"""
        layer.initialize_grid(self.size)
        self.layers[layer.name] = layer

    def set_size(self, size: tuple[int, int]):
        """Set the size of the tilemap. This will resize all layers to match."""
        self.size = size
        for layer in self.layers.values():
            layer.set_size(size)
