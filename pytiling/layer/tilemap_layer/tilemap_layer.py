from typing import Union, cast, TYPE_CHECKING, Literal
from pytiling.tileset.tileset import Tileset
from .tilemap_layer_formatter import TilemapLayerFormatter
from ..grid_layer import GridLayer
from .tilemap_layer_neighbor_processor import TilemapLayerNeighborProcessor
from functools import cached_property
from pytiling.utils import Direction
from pytiling.grid_element.tile import Tile
from pytiling.grid_element.tile.autotile import (
    AutotileTile,
    AutotileRule,
)
from pytiling.grid_element.tile.autotile.default_rules import (
    detailed_default_autotile_rules,
)
from blinker import Signal

if TYPE_CHECKING:
    from grid_element.tile.autotile import AutotileRule


class TilemapLayer(GridLayer):
    """A class representing a tilemap layer. It contains a grid of tiles."""

    autotile_rules: dict[str, list["AutotileRule"]]

    def __init__(
        self,
        name: str,
        tileset: Tileset,
        autotile_rules: (
            Literal["detailed"] | dict[str, list["AutotileRule"]]
        ) = "detailed",
    ):
        super().__init__(name)

        self.name = name
        self.tileset = tileset

        if isinstance(autotile_rules, str):
            self.autotile_rules = {
                "default": self._get_default_autotile_rules(autotile_rules)
            }
        else:
            self.autotile_rules = autotile_rules

        self.autotile_neighbor_processor = TilemapLayerNeighborProcessor(self)

        self.formatter = TilemapLayerFormatter(self)

        self._restart_events()

    def _get_default_autotile_rules(self, rules_type: Literal["detailed"]):
        if rules_type == "detailed":
            return detailed_default_autotile_rules

    def _restart_events(self):
        super()._restart_events()
        self.events: dict[str, Signal] = {
            **self.events,
            "tile_formatted": Signal(),
        }

    def populate_from_data(self, elements_data: list[dict]):
        """Populate the layer with tiles from a list of data dictionaries."""
        from ...serialization import element_from_dict

        for element_data in elements_data:
            element = element_from_dict(element_data)
            # We don't apply formatting here, as it's often done in a final pass
            # after the entire map is loaded.
            self.add_tile(cast("Tile", element), apply_formatting=False)

    def to_dict(self):
        """Serialize the layer to a dictionary."""
        data = super().to_dict()
        data["__class__"] = "TilemapLayer"
        data["tileset"] = self.tileset.tileset_path
        # autotile_rules are not serialized, they should be redefined in code after loading.
        return data

    def create_autotile_tile_at(
        self, position: tuple[int, int], name: str, apply_formatting=False, **args
    ):
        """Create an autotile tile at a given position."""
        tile = AutotileTile(position, name, **args)
        tile_added = self.add_tile(tile, apply_formatting)
        return tile if tile_added else None

    def create_tile_at(
        self,
        position: tuple[int, int],
        display: tuple[int, int],
        name="",
        apply_formatting=False,
        **args
    ):
        """Create a tile at a given position."""
        tile = Tile(position, display, name, **args)
        tile_added = self.add_tile(tile, apply_formatting)
        return tile if tile_added else None

    def add_tile(self, tile: "Tile", apply_formatting=False):
        """Add a tile to the layer's grid. Also formats the tile and its potential neighbors. Returns True if the tile was added, False if it was not."""
        if not super().add_element(tile):
            return False

        if isinstance(tile, AutotileTile):
            self._handle_add_autotile_tile(tile, apply_formatting)

        if apply_formatting:
            tile.format()

        return True

    def _handle_add_autotile_tile(self, tile: "AutotileTile", apply_formatting: bool):
        """Handle adding an autotile tile to the layer."""
        if tile.name not in self.autotile_rules:
            self.autotile_rules[tile.name] = self.autotile_rules["default"]
        tile.rules = self.autotile_rules[tile.name]

        if apply_formatting:
            self.formatter.format_autotile_tile_neighbors(tile)

    def remove_tile_at(self, position: tuple[int, int], apply_formatting=False):
        """Remove a tile at a given position."""
        tile = self.get_tile_at(position)
        if tile is None:
            return None
        return self.remove_tile(tile, apply_formatting)

    def remove_tile(self, tile: "Tile", apply_formatting=False):
        """Remove a tile from the layer's grid. Returns True if the tile was removed, False if it was not."""
        if tile.locked:
            return None

        super().remove_element(tile)
        if isinstance(tile, AutotileTile):
            self._handle_remove_autotile_tile(tile, apply_formatting)

        return tile

    def _handle_remove_autotile_tile(
        self, tile: "AutotileTile", apply_formatting: bool
    ):
        """Handle removing an autotile tile from the layer."""
        if apply_formatting:
            self.formatter.format_autotile_tile_neighbors(tile)

    @property
    def tiles(self):
        """Get all tiles in the layer."""
        return cast(list[Tile], self.elements)

    def add_autotile_rule(self, name, *rules):
        """Append one or more rules to the list of rules for a specific autotile object."""
        for rule in rules:
            self.autotile_rules[name].append(rule)

    def set_autotile_rules(self, name, rules):
        """Set the list of rules for a specific autotile object. It resets the rules for that object, so it must be used when it's needed to overwrite the default rules."""
        self.autotile_rules[name] = rules

    def get_tile_at(self, position: tuple[int, int]):
        """Get a tile at a given position."""
        return cast("Tile | None", self.get_element_at(position))

    def get_edge_tiles(
        self, edge: Union[Direction, Literal["all"]] = "all", size=1, retreat=0
    ) -> "list[Tile | None]":
        """Get a set of tiles on specified edges of the layer's grid, ensuring no duplicates at corners."""
        return [
            cast("Tile | None", element)
            for element in self.get_edge_elements(edge, size, retreat)
        ]

    @cached_property
    def layer_above(self) -> "TilemapLayer | None":
        """Get the layer above this layer (if it exists)."""
        return cast("TilemapLayer | None", super().layer_above)

    @cached_property
    def layer_below(self) -> "TilemapLayer | None":
        """Get the layer below this layer (if it exists)."""
        return cast("TilemapLayer | None", super().layer_below)

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, state):
        super().__setstate__(state)
