from typing import TYPE_CHECKING, Literal, Sequence

if TYPE_CHECKING:
    from layer import GridLayer


class GridMap:
    def __init__(self, grid_size: tuple[int, int], tile_size: tuple[int, int]):
        self.tile_size = tile_size
        self._grid_size = grid_size

        self._layers_dict: dict[str, "GridLayer"] = {}
        self._layers: list["GridLayer"] = []

    def add_layer(self, layer: "GridLayer", position: int | Literal["end"] = "end"):
        """Add a layer to the tilemap. By default, it will be added to the end of the list, so it's a good practice to add layers in order."""
        layer.initialize_grid(self.grid_size)
        self._layers_dict[layer.name] = layer
        if position == "end":
            self._layers.append(layer)
        else:
            self._layers.insert(position, layer)

    @property
    def grid_size(self) -> tuple[int, int]:
        """Get the size of the tilemap."""
        return self._grid_size

    @grid_size.setter
    def grid_size(self, size: tuple[int, int]):
        """Set the size of the tilemap. This will resize all layers to match."""
        self._grid_size = size
        for layer in self._layers:
            layer.grid_size = size

    def position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.grid_size[1]
            and position[1] < self.grid_size[0]
        )

    def get_layer(self, name: str) -> "GridLayer | None":
        """Get a layer by its name."""
        if name in self._layers_dict:
            return self._layers_dict[name]

    @property
    def layers(self) -> Sequence["GridLayer"]:
        """Get all layers."""
        return self._layers

    @property
    def size(self):
        tile_width, tile_height = self.tile_size
        return (
            self.grid_size[1] * tile_width,
            self.grid_size[0] * tile_height,
        )
