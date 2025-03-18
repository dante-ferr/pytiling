from .. import Tile
import warnings
from typing import TYPE_CHECKING, cast, Callable, TypedDict
import json
import os

if TYPE_CHECKING:
    from pytiling.layer.tilemap_layer.tilemap_layer_neighbor_processor import (
        TilemapLayerNeighborProcessor,
    )
    from .autotile_rule import AutotileRule
    from pytiling.layer.tilemap_layer import TilemapLayer
    from pytiling.layer import GridLayer


class Variation(TypedDict):
    display: list[int]
    chance: float


DEFAULT_SHALLOW_TILE_VARIATIONS_FILENAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "default_shallow_tile_variations.json"
)


class AutotileTile(Tile):
    """A class representing an autotile tile. It extends the Tile class and adds the ability to change its display based on the rules it has. Each rule defines a specific display based on the tile's neighbors."""

    def __init__(
        self,
        position: tuple[int, int],
        name: str,
        default_shallow_tile_variations: bool = False,
    ):
        super().__init__(position, name=name)

        self.display = (0, 0)
        self.rules: list["AutotileRule"] = []
        self.post_autotile_callbacks: list[Callable] = []

        if default_shallow_tile_variations:
            self.set_default_shallow_tile_variations()

    def set_default_shallow_tile_variations(self):
        def _callback(tile: "AutotileTile"):
            if tile.is_shallow:
                tile.add_variations_from_json(DEFAULT_SHALLOW_TILE_VARIATIONS_FILENAME)

        self.add_post_autotile_callback(_callback)

    def add_post_autotile_callback(self, callback: Callable):
        """Add a callback to be called after the autotile calculation is done."""
        self.post_autotile_callbacks.append(callback)

    @property
    def layer(self):
        return super().layer

    @layer.setter
    def layer(self, layer: "GridLayer"):
        """Set the tile's layer."""
        layer = cast("TilemapLayer", layer)
        self._layer = layer

    @property
    def neighbor_processor(self):
        return self.layer.autotile_neighbor_processor

    def format(self):
        """Format the tile's display. Return True if the tile's display has changed."""
        previous_display = self.display

        neighbors_bool_grid = self.neighbor_processor.get_neighbors_bool_grid(self)

        display_changed = self._autotile_calculate(neighbors_bool_grid)
        for callback in self.post_autotile_callbacks:
            callback(self)

        super().format()

        return self.display != previous_display

    def _autotile_calculate(self, neighbors_bool_grid):
        """Change the tile's display based on the rules it has. Returns True if the tile's display has changed, or False otherwise."""
        self.reset_variations()

        def find_display(rule_index: int):
            if rule_index >= len(self.rules):
                warnings.warn("No display found", UserWarning)
                return (0, 0)
            rule = self.layer.autotile_rules[self.name][rule_index]

            for y, row in enumerate(rule.rule_matrix):
                for x, cell in enumerate(row):
                    if cell == 1:
                        continue
                    if cell == 2:
                        continue

                    neighbor_exists = neighbors_bool_grid[y, x]
                    if (neighbor_exists and cell == 0) or (
                        (not neighbor_exists) and cell == 3
                    ):
                        return find_display(rule_index + 1)

            return rule.display

        previous_display = self.display
        self.display = find_display(0)
        return self.display != previous_display

    @property
    def is_deep(self):
        return self.neighbor_processor.get_amount_of_neighbors_of(self, radius=2) == 24

    @property
    def is_shallow(self):
        return (
            self.neighbor_processor.get_amount_of_neighbors_of(self, radius=1) == 8
            and not self.is_deep
        )

    @property
    def is_border(self):
        return self.neighbor_processor.get_amount_of_neighbors_of(self, radius=1) < 8
