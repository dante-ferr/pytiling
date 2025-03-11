from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .tileset import Tileset
    from .layer.tilemap_layer import TilemapLayer


class Tilemap:
    """
    A class representing a tilemap. It contains a dictionary of tilemap layers.
    The layers are ordered by default, but it's not mandatory to use them in order.
    """

    def __init__(self, size: tuple[int, int] = (8, 8)):
        self._layers_dict: dict[str, "TilemapLayer"] = {}
        self.layers: list["TilemapLayer"] = []
        self.tilesets: set["Tileset"] = set()
        self._tile_size: tuple[int, int] | None = None
        self._grid_size = size

    def add_layer(self, layer: "TilemapLayer", position: int | Literal["end"] = "end"):
        """Add a layer to the tilemap. By default, it will be added to the end of the list, so it's a good practice to add layers in order."""
        layer.initialize_grid(self.grid_size)
        if self._tile_size is not None and layer.tile_size != self._tile_size:
            raise ValueError(
                "Two tilesets with different tile sizes cannot be used on the same tilemap."
            )
        self._tile_size = layer.tile_size
        self.tilesets.add(layer.tileset)

        self._layers_dict[layer.name] = layer
        if position == "end":
            self.layers.append(layer)
        else:
            self.layers.insert(position, layer)

    def add_format_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.formatter.add_format_callback(callback)

    def add_create_tile_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_create_tile_callback(callback)

    def add_remove_tile_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_remove_tile_callback(callback)

    def add_layer_concurrence(self, *layers: "TilemapLayer"):
        """Make the specified layers concurrent. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a tile on a layer will remove the tiles at the same position from its concurrent layers."""
        for layer in layers:
            other_layers = [l for l in layers if l is not layer]
            for other_layer in other_layers:
                layer.add_concurrent_layer(other_layer)

    @property
    def tile_size(self) -> tuple[int, int]:
        """Get the size of a tile in the tilemap."""
        if not self._tile_size:
            raise ValueError(
                "Tile size not set for the tilemap. A layer must be added to the tilemap before getting its tile size."
            )
        return self._tile_size

    @tile_size.setter
    def tile_size(self, size):
        """Set the size of a tile in the tilemap."""
        raise ValueError(
            "Tile size cannot be set manually. It is set automatically when a layer is added to the tilemap."
        )

    @property
    def grid_size(self) -> tuple[int, int]:
        """Get the size of the tilemap."""
        return self._grid_size

    @grid_size.setter
    def grid_size(self, size: tuple[int, int]):
        """Set the size of the tilemap. This will resize all layers to match."""
        self._grid_size = size
        for layer in self.layers:
            layer.grid_size = size

    def position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.grid_size[1]
            and position[1] < self.grid_size[0]
        )

    def get_layer(self, name: str) -> "TilemapLayer":
        """Get a layer by its name."""
        return self._layers_dict[name]

    @property
    def size(self):
        tile_width, tile_height = self.tile_size
        return (
            self.grid_size[1] * tile_width,
            self.grid_size[0] * tile_height,
        )
