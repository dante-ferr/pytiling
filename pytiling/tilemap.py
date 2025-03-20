from typing import TYPE_CHECKING, Literal, cast, Sequence, Callable
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

    def on_layer_event(self, event_name: str, callback: Callable):
        for layer in self.layers:
            layer.events[event_name].connect(callback, weak=True)

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

    def get_layer(self, name: str) -> "TilemapLayer":
        """Get a layer by its name."""
        return cast("TilemapLayer", super().get_layer(name))

    @property
    def all_tiles(self):
        """Get all tiles in the tilemap."""
        return cast("list[Tile]", self.all_elements)

    def format_all_tiles(self):
        """Format all tiles in the tilemap."""
        for layer in self.layers:
            layer.formatter.format_all_tiles()
