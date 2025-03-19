from .utils import Direction, direction_vectors
from typing import TYPE_CHECKING, Literal, Sequence, Union, Callable

if TYPE_CHECKING:
    from .layer import GridLayer
    from .grid_element import GridElement


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

    def add_create_element_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_create_element_callback(callback)

    def add_remove_element_callback_to_all_layers(self, callback):
        for layer in self.layers:
            layer.add_remove_element_callback(callback)

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
            self.grid_size[0] * tile_width,
            self.grid_size[1] * tile_height,
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
        size=1,
    ):
        """Expand the grid in the specified direction."""
        shift = self._get_shift(direction, size)
        new_size = (
            self.grid_size[0] + shift[0],
            self.grid_size[1] + shift[1],
        )
        if not self._can_expand_towards(new_size):
            return

        # remember: grid_size was here before

        for layer in self.layers:
            layer.expand_towards(direction, size)

        self.grid_size = new_size

        return self.get_edge_positions(direction)

    def _can_expand_towards(self, new_size: tuple[int, int]) -> bool:
        """Check if the grid can expand in the specified direction."""
        return (
            new_size[0] <= self.max_grid_size[0]
            and new_size[1] <= self.max_grid_size[1]
        )

    def reduce_towards(self, direction: Direction, size=1):
        """Reduce the grid in the specified direction. Returns the deleted elements into a dict by layer name."""
        shift = self._get_shift(direction, size)
        new_size = (
            self.grid_size[0] - shift[0],
            self.grid_size[1] - shift[1],
        )
        if not self._can_reduce_towards(new_size):
            return

        deleted_elements: dict[str, list["GridElement | None"]] = {}
        for layer in self.layers:
            deleted_elements[layer.name] = layer.reduce_towards(direction, size)

        self.grid_size = new_size

        return deleted_elements

    def _can_reduce_towards(self, new_size: tuple[int, int]) -> bool:
        """Check if the grid can reduce in the specified direction."""
        return (
            new_size[0] >= self.min_grid_size[0]
            and new_size[1] >= self.min_grid_size[1]
        )

    def _get_shift(self, direction: Direction, size: int) -> tuple[int, int]:
        return (
            abs(direction_vectors[direction][0] * size),
            abs(direction_vectors[direction][1] * size),
        )

    def get_edge_positions(
        self, edge: Union[Direction, Literal["all"]] = "all", size=1, retreat=0
    ):
        """Get the positions of the edges of the layer."""
        # TODO: make it support sizes greater than 1
        width, height = self.grid_size
        edge_positions: set[tuple[int, int]] = set()

        if edge in ("left", "all"):
            for y in range(height):
                edge_positions.add((retreat, y))

        if edge in ("right", "all"):
            for y in range(height):
                edge_positions.add((width - 1 - retreat, y))

        if edge in ("bottom", "all"):
            for x in range(width):
                edge_positions.add((x, height - 1 - retreat))

        if edge in ("top", "all"):
            for x in range(width):
                edge_positions.add((x, retreat))

        return list(edge_positions)

    @property
    def all_elements(self) -> list["GridElement"]:
        """Get a list of all elements in the grid map."""
        elements: list["GridElement"] = []
        for layer in self.layers:
            elements.extend(layer.elements)
        return elements

    def add_layer_concurrence(self, *layer_names: str):
        """Make the specified layers concurrent. Tiles from concurrent layers won't be able to be placed on the same position. So the addition of a tile on a layer will remove the tiles at the same position from its concurrent layers."""
        layers = [self.get_layer(name) for name in layer_names]

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

    def for_grid_position(self, callback: Callable[[tuple[int, int]], None]):
        """Loops over each grid position in the layer's grid, calling the given callback."""
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                callback((x, y))
