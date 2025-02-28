from typing import TypedDict, Literal, Any, Callable
from .tile.tile import Tile
import numpy as np
from .tileset import Tileset
from .tile.autotile.autotile_rule import AutotileRule
from .tile.autotile.default_autotile_rules import default_rules
from .tile.autotile.autotile_tile import AutotileTile


class Area(TypedDict):
    top_left: tuple[int, int]
    bottom_right: tuple[int, int]


class TilemapLayer:
    """A class representing a tilemap layer. It contains a grid of tiles."""

    autotile_rules: dict[str, list[AutotileRule]]

    def __init__(self, name: str, tileset: Tileset):
        self.name = name
        self.tileset = tileset
        self.autotile_rules = {}

        self.format_callbacks: list[Callable] = []
        self.individual_format_callbacks: list[Callable] = []

    def initialize_grid(self, size: tuple[int, int]):
        """Initialize the grid of the tilemap layer."""
        self.grid = np.empty(size, dtype=Tile)

    def set_size(self, size: tuple[int, int]):
        """Change the size of the grid."""
        np.resize(self.grid, size)

    def add_format_callback(self, *callbacks: Callable):
        """Add a callback to be called when the any tile in the layer is formatted."""
        for callback in callbacks:
            self.format_callbacks.append(callback)

    def add_individual_format_callback(self, *callbacks: Callable):
        for callback in callbacks:
            self.individual_format_callbacks.append(callback)

    def add_tile(self, tile: Tile, apply_formatting=True):
        """Add a tile to the grid."""
        if self.grid is None:
            raise ValueError(
                "Grid is not initialized. Make sure to add this layer to a tilemap before adding tiles."
            )
        if tile.position is None:
            raise ValueError(
                "Tile position cannot be None. Ensure to set the position of the tile before adding it to the layer."
            )
        if (
            tile.position[0] < 0
            or tile.position[1] < 0
            or tile.position[0] >= self.grid.shape[1]
            or tile.position[1] >= self.grid.shape[0]
        ):
            raise ValueError(
                f"Tile position ({tile.position}) is out of bounds for the grid ({self.grid.shape})."
            )
        if self.grid[tile.position[1], tile.position[0]] is not None:
            return

        tile.set_layer(self)
        if isinstance(tile, AutotileTile):
            if tile.autotile_object is None:
                raise ValueError("Autotile object must be set for autotile tiles.")

            if tile.autotile_object not in self.autotile_rules:
                self.autotile_rules[tile.autotile_object] = default_rules
            tile.rules = self.autotile_rules[tile.autotile_object]

        self.grid[tile.position[1], tile.position[0]] = tile

        if apply_formatting:
            self.format(self._get_area_around(tile.position, 1))
            for callback in self.individual_format_callbacks:
                callback(tile)

    def add_autotile_rule(self, autotile_object, *rules):
        """Append one or more rules to the list of rules for a specific autotile object."""
        for rule in rules:
            self.autotile_rules[autotile_object].append(rule)

    def set_autotile_rules(self, autotile_object, rules):
        """Set the list of rules for a specific autotile object. It resets the rules for that object, so it must be used when it's needed to overwrite the default rules."""
        self.autotile_rules[autotile_object] = rules

    def format(self, area: Area | Literal["all"] = "all"):
        """Format the grid of tiles."""
        radius = 2
        if area == "all":
            area = Area(
                top_left=(0, 0),
                bottom_right=(self.grid.shape[1] - radius, self.grid.shape[0] - radius),
            )

        def tile_format_callback(x, y):
            tile = self.grid[y, x]
            if tile is not None:
                tile.format()

        self._loop_over_area(area, tile_format_callback)

    def get_neighbors_of(
        self,
        tile: Tile,
        radius: int = 1,
        same_autotile_object=False,
        output_type: Literal["tile_grid", "bool_grid", "amount"] = "bool_grid",
        adjacency_rule: Literal[
            "eight_neighbors", "four_neighbors"
        ] = "eight_neighbors",
    ):
        """Get the neighbors of a tile in a given radius."""
        if tile.position is None:
            raise ValueError(
                "Tile position cannot be None. Ensure to set the position of the tile before getting its neighbors."
            )
        neighbors: Any

        matrix_size = radius * 2 + 1
        if output_type == "tile_grid":
            neighbors = np.empty((matrix_size, matrix_size), dtype=Tile)
        elif output_type == "bool_grid":
            neighbors = np.full((matrix_size, matrix_size), False)
        elif output_type == "amount":
            neighbors = 0

        if radius == 0:
            return neighbors

        def tile_neighbors_callback(x, y):
            nonlocal neighbors

            if x == tile.position[0] and y == tile.position[1]:
                return
            neighbor = self.grid[y, x]
            if neighbor is None:
                return
            if (
                same_autotile_object
                and neighbor.autotile_object is not None
                and neighbor.autotile_object != tile.autotile_object
            ):
                return

            if output_type == "tile_grid":
                neighbors[
                    y - tile.position[1] + radius, x - tile.position[0] + radius
                ] = neighbor
            elif output_type == "bool_grid":
                neighbors[
                    y - tile.position[1] + radius, x - tile.position[0] + radius
                ] = True
            elif output_type == "amount":
                neighbors += 1

        if adjacency_rule == "eight_neighbors":
            self._loop_over_area(
                self._get_area_around(tile.position, radius), tile_neighbors_callback
            )
        elif adjacency_rule == "four_neighbors":
            if radius > 1:
                raise ValueError("Radius must be 1 for four neighbors search.")

            tile_x, tile_y = tile.position
            positions = [
                (tile_x + 1, tile_y),
                (tile_x, tile_y - 1),
                (tile_x - 1, tile_y),
                (tile_x, tile_y + 1),
            ]
            for position in positions:
                if self._position_is_valid(position):
                    tile_neighbors_callback(*position)

        return neighbors

    def _loop_over_area(self, area: Area, callback):
        """Loop over an area of the grid and call a callback function for each tile in the area."""
        top_left_x, top_left_y = area["top_left"]
        bottom_right_x, bottom_right_y = area["bottom_right"]

        for x in range(top_left_x, bottom_right_x + 1):
            for y in range(top_left_y, bottom_right_y + 1):
                callback(x, y)

    def _get_area_around(self, center: tuple[int, int], radius: int) -> Area:
        """Get an area around a center point with a given radius."""
        center_x, center_y = center
        grid_height, grid_width = self.grid.shape

        top_left_x = max(center_x - radius, 0)
        top_left_y = max(center_y - radius, 0)
        bottom_right_x = min(center_x + radius, grid_width - 1)
        bottom_right_y = min(center_y + radius, grid_height - 1)

        return Area(
            top_left=(top_left_x, top_left_y),
            bottom_right=(bottom_right_x, bottom_right_y),
        )

    def _position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.grid.shape[1]
            and position[1] < self.grid.shape[0]
        )

    def tilemap_pos_to_actual_pos(
        self, position: tuple[int, int], invert_x_axis=False, invert_y_axis=True
    ):
        """Convert a tile position in the tilemap layer to an actual position in the window."""
        tile_width, tile_height = self.tile_size
        map_width, map_height = self.size
        pos = [position[0] * tile_width, position[1] * tile_height]

        if invert_x_axis:
            pos[0] = map_width - pos[0]
        if invert_y_axis:
            pos[1] = map_height - pos[1]

        return (*pos,)

    def actual_pos_to_tilemap_pos(
        self, position: tuple[int, int], invert_x_axis=False, invert_y_axis=True
    ):
        """Convert an actual position in the window to a tile position in the tilemap layer."""
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

    @property
    def tile_size(self):
        return self.tileset.tile_size

    @property
    def size(self):
        tile_width, tile_height = self.tile_size
        return (
            self.grid.shape[1] * tile_width,
            self.grid.shape[0] * tile_height,
        )
