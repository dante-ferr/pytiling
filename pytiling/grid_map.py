from .utils import Direction, direction_vectors
from typing import TYPE_CHECKING, Literal, Sequence, Union, Callable, cast
from blinker import Signal

if TYPE_CHECKING:
    from .layer import GridLayer
    from .grid_element import GridElement


class GridMap:
    RemovedPositions = list[tuple[int, int]]
    NewPositions = list[tuple[int, int]]

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

        self._restart_events()

    def _restart_events(self):
        self.events: dict[str, Signal] = {
            "expanded": Signal(),
            "reducted": Signal(),
        }

    def to_dict(self):
        """Serialize the map to a dictionary."""
        return {
            "__class__": "GridMap",
            "tile_size": self.tile_size,
            "grid_size": self.grid_size,
            "min_grid_size": self.min_grid_size,
            "max_grid_size": self.max_grid_size,
            "layers": [layer.to_dict() for layer in self.layers],
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserialize a map from a dictionary."""
        instance = cls._from_dict_base(data)
        cls._setup_concurrency_from_data(data["layers"], instance)

        return instance

    @classmethod
    def _from_dict_base(cls, data: dict):
        """Creates an instance and populates it from a dictionary, without setting up concurrences."""
        from .serialization import layer_from_dict

        instance = cls._instance_from_data(data)

        tilesets = {}  # To reuse tileset objects

        # First, create layers and add them to the map to initialize them.
        # This ensures that layer.grid and layer.grid_map are set before elements are added.
        for layer_data in data["layers"]:
            layer = layer_from_dict(layer_data, tilesets)
            instance.add_layer(layer)

        # Second, populate elements.
        cls._populate_layers_from_data(data["layers"], instance)
        return instance

    @classmethod
    def _instance_from_data(cls, data: dict):
        return cls(
            tile_size=tuple(data["tile_size"]),
            grid_size=tuple(data["grid_size"]),
            min_grid_size=tuple(data["min_grid_size"]),
            max_grid_size=tuple(data["max_grid_size"]),
        )

    @classmethod
    def _populate_layers_from_data(cls, layers_data: list[dict], instance: "GridMap"):
        for layer_data in layers_data:
            layer = instance.get_layer(layer_data["name"])
            layer.populate_from_data(layer_data["elements"])

    @classmethod
    def _setup_concurrency_from_data(cls, layers_data: list[dict], instance: "GridMap"):
        for layer_data in layers_data:
            if "concurrent_layers" in layer_data and layer_data["concurrent_layers"]:
                layer = instance.get_layer(layer_data["name"])
                concurrent_layer_names: list[str] = layer_data["concurrent_layers"]
                for concurrent_layer_name in concurrent_layer_names:
                    concurrent_layer = instance.get_layer(concurrent_layer_name)
                    layer.add_concurrent_layer(concurrent_layer)

    def on_layer_event(self, event_name: str, callback: Callable):
        for layer in self.layers:
            layer.events[event_name].connect(callback, weak=True)

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
        """Expand the grid in the specified direction. Returns the new positions into a list."""
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

        old_grid_size = self.grid_size
        self.grid_size = new_size
        new_positions = self.get_edge_positions(direction, size=size)

        self.events["expanded"].send(
            direction=direction, size=size, new_positions=new_positions
        )

        return new_positions

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

        removed_positions = self.get_edge_positions(direction, size=size)
        for layer in self.layers:
            layer.reduce_towards(direction, size)

        self.grid_size = new_size

        self.events["reducted"].send(
            direction=direction, size=size, removed_positions=list(removed_positions)
        )

        return removed_positions

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
        self,
        edge: Union[Direction, Literal["all"]] = "all",
        size=1,
        retreat=0,
    ):
        """
        Get the positions of the edges of the layer.
        When used for expansion, old_grid_size should be provided to get the newly added positions.
        """
        width, height = self.grid_size
        edge_positions: set[tuple[int, int]] = set()

        for i in range(size):
            current_retreat = retreat + i
            if edge in ("left", "all"):
                for y in range(height):
                    edge_positions.add((current_retreat, y))

            if edge in ("right", "all"):
                for y in range(height):
                    edge_positions.add((width - 1 - current_retreat, y))

            if edge in ("bottom", "all"):
                for x in range(width):
                    edge_positions.add((x, height - 1 - current_retreat))

            if edge in ("top", "all"):
                for x in range(width):
                    edge_positions.add((x, current_retreat))

        return list(edge_positions)

    @property
    def all_elements(self) -> list["GridElement"]:
        """Get a list of all elements in the grid map."""
        elements: list["GridElement"] = []
        for layer in self.layers:
            elements.extend(layer.elements)
        return elements

    def remove_all_elements_at(self, position: tuple[int, int]):
        for element in self.all_elements_at(position):
            element.remove()

    def all_elements_at(self, position: tuple[int, int]):
        elements: list["GridElement"] = []
        for layer in self.layers:
            element = layer.get_element_at(position)
            if element:
                elements.append(element)
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

    def grid_pos_to_actual_pos(
        self, position: tuple[int, int], invert_x_axis=False, invert_y_axis=True
    ) -> tuple[float, float]:
        """Convert a tile position in the layer to an actual position in the window."""
        tile_width, tile_height = self.tile_size
        map_width, map_height = self.size
        pos = [position[0] * tile_width, position[1] * tile_height]

        if invert_x_axis:
            pos[0] = map_width - pos[0]
        if invert_y_axis:
            pos[1] = map_height - pos[1]

        return (pos[0], pos[1])

    def actual_pos_to_grid_pos(
        self, position: tuple[float, float], invert_x_axis=False, invert_y_axis=True
    ):
        """Convert an actual position in the window to a tile position in the layer."""
        tile_width, tile_height = self.tile_size
        map_width, map_height = self.size
        pos: list[int] = [
            int(position[0] // tile_width),
            int(position[1] // tile_height + 1),
        ]

        if invert_x_axis:
            pos[0] = int((map_width - position[0]) // tile_width)
        if invert_y_axis:
            pos[1] = int((map_height - position[1]) // tile_height + 1)

        return (*pos,)

    def __getstate__(self):
        state = self.__dict__.copy()

        state["events"] = {}
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        self._restart_events()
