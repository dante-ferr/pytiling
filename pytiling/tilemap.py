from typing import TYPE_CHECKING, Literal, cast, Sequence
from .grid_map import GridMap

if TYPE_CHECKING:
    from .tileset.tileset import Tileset
    from .layer.tilemap_layer import TilemapLayer
    from .layer.grid_layer import GridLayer
    from .grid_element.tile import Tile


class Tilemap(GridMap):
    """
    A class representing a tilemap. It contains a dictionary of tilemap layers.
    The layers are ordered by default, but it's not mandatory to use them in order.
    """

    def __init__(
        self,
        tile_size: tuple[int, int],
        grid_size: tuple[int, int] = (5, 5),
        min_grid_size: tuple[int, int] = (5, 5),
        max_grid_size: tuple[int, int] = (100, 100),
    ):
        super().__init__(tile_size, grid_size, min_grid_size, max_grid_size)

        self.tilesets: set["Tileset"] = set()

    def add_layer(self, layer: "GridLayer", position: int | Literal["end"] = "end"):
        """Add a layer to the tilemap. By default, it will be added to the end of the list, so it's a good practice to add layers in order."""
        layer = cast("TilemapLayer", layer)
        self._add_tileset(layer.tileset)

        super().add_layer(layer, position)

    @property
    def layers(self) -> Sequence["TilemapLayer"]:
        return cast(Sequence["TilemapLayer"], super().layers)

    def _add_tileset(self, tileset: "Tileset"):
        tileset.tile_size = self.tile_size
        self.tilesets.add(tileset)

    def add_format_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.formatter.add_format_callback(callback)

    def add_create_tile_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_create_tile_callback(callback)

    def add_remove_tile_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_remove_tile_callback(callback)

    def get_layer(self, name: str) -> "TilemapLayer":
        """Get a layer by its name."""
        return cast("TilemapLayer", super().get_layer(name))

    @property
    def all_tiles(self):
        """Get all tiles in the tilemap."""
        tiles: list["Tile"] = []
        for layer in self.layers:
            tiles.extend(layer.tiles)
        return tiles

    @staticmethod
    def add_layer_concurrence(*layers: "TilemapLayer"):
        """Make the specified layers concurrent. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a tile on a layer will remove the tiles at the same position from its concurrent layers."""
        for layer in layers:
            other_layers = [l for l in layers if l is not layer]
            for other_layer in other_layers:
                layer.add_concurrent_layer(other_layer)

    def position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.grid_size[0]
            and position[1] < self.grid_size[1]
        )
