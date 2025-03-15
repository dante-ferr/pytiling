from .utils import Direction, direction_vectors
from typing import TYPE_CHECKING, Literal, Sequence, Any, Callable

if TYPE_CHECKING:
    from layer import GridLayer


class GridMap:
    def __init__(
        self,
        tile_size: tuple[int, int],
        grid_size: tuple[int, int],
        min_grid_size: tuple[int, int],
        max_grid_size: tuple[int, int],
    ):
        self.tile_size = tile_size
        self.min_grid_size = min_grid_size
        self.max_grid_size = max_grid_size
        self._grid_size = self.clamp_size(grid_size)

        self._layers_dict: dict[str, "GridLayer"] = {}
        self._layers: list["GridLayer"] = []

        self.size_change_callbacks: list[Callable] = []

    def add_size_change_callback(self, callback: Callable):
        """Add a callback to be called when the grid size changes."""
        self.size_change_callbacks.append(callback)

    def add_layer(self, layer: "GridLayer", position: int | Literal["end"] = "end"):
        """Add a layer to the tilemap. By default, it will be added to the end of the list, so it's a good practice to add layers in order."""
        layer.initialize_grid(self.grid_size)
        layer.grid_map = self

        self._layers_dict[layer.name] = layer

        if position == "end":
            self._layers.append(layer)
        else:
            self._layers.insert(position, layer)

    def clamp_size(self, size):
        """Clamp the given size to the maximum and minimum size."""
        return (
            max(self.min_grid_size[0], min(size[0], self.max_grid_size[0])),
            max(self.min_grid_size[1], min(size[1], self.max_grid_size[1])),
        )

    @property
    def size(self):
        tile_width, tile_height = self.tile_size
        return (
            self.grid_size[1] * tile_width,
            self.grid_size[0] * tile_height,
        )

    @property
    def grid_size(self) -> tuple[int, int]:
        """Get the size of the tilemap."""
        return self._grid_size

    @grid_size.setter
    def grid_size(self, value: tuple[int, int]):
        """Set the size of the tilemap. Note that this won't resize the layers."""
        self._grid_size = self.clamp_size(value)

        for callback in self.size_change_callbacks:
            callback()

    def resize(self, size: tuple[int, int]):
        """Set the size of the tilemap. This will resize all layers to match."""
        self._grid_size = size
        for layer in self._layers:
            layer.resize(size)

    def position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.grid_size[1]
            and position[1] < self.grid_size[0]
        )

    def get_layer(self, name: str) -> "GridLayer":
        """Get a layer by its name."""
        if name in self._layers_dict:
            return self._layers_dict[name]
        else:
            raise ValueError(f"Layer {name} not found.")

    def has_layer(self, name: str) -> bool:
        """Check if a layer exists."""
        return name in self._layers_dict

    @property
    def layers(self) -> Sequence["GridLayer"]:
        """Get all layers."""
        return self._layers

    def expand_towards(
        self,
        direction: Direction,
        fill_callback: Callable[[tuple[int, int]], Any],
        size=1,
    ):
        """Expand the grid in the specified direction."""
        if (
            self.grid_size[0] + direction_vectors[direction][0] * size
            > self.max_grid_size[0]
            or self.grid_size[1] + direction_vectors[direction][1] * size
            > self.max_grid_size[1]
        ):
            return

        print("Expanding towards", direction, size)
        self.grid_size = (
            self.grid_size[0] + abs(direction_vectors[direction][0] * size),
            self.grid_size[1] + abs(direction_vectors[direction][1] * size),
        )

        for layer in self.layers:
            layer.expand_towards(direction, fill_callback, size)

    def reduce_towards(self, direction: Direction, size=1):
        """Reduce the grid in the specified direction."""
        if (
            self.grid_size[0] - direction_vectors[direction][0] * size
            <= self.min_grid_size[0]
            or self.grid_size[1] - direction_vectors[direction][1] * size
            <= self.min_grid_size[1]
        ):
            return

        self.grid_size = (
            self.grid_size[0] - abs(direction_vectors[direction][0] * size),
            self.grid_size[1] - abs(direction_vectors[direction][1] * size),
        )

        print("Reducing towards", direction, size)

        for layer in self.layers:
            layer.reduce_towards(direction, size)
