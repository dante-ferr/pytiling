from .. import Tile
import warnings
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from pytiling.layer.tilemap_layer.tilemap_layer_neighbor_processor import (
        TilemapLayerNeighborProcessor,
    )
    from .autotile_rule import AutotileRule
    from pytiling.layer.tilemap_layer import TilemapLayer
    from pytiling.layer import GridLayer


class AutotileTile(Tile):
    """A class representing an autotile tile. It extends the Tile class and adds the ability to change its display based on the rules it has. Each rule defines a specific display based on the tile's neighbors."""

    rules: list["AutotileRule"]
    is_deep = False

    def __init__(self, position: tuple[int, int], name: str):
        super().__init__(position, name=name)

        self.layer_neighbor_processor: "TilemapLayerNeighborProcessor | None" = None

        self.display = (0, 0)

    @property
    def layer(self):
        return super().layer

    @layer.setter
    def layer(self, layer: "GridLayer"):
        """Set the tile's layer."""
        layer = cast("TilemapLayer", layer)
        self._on_layer_set(layer)
        self._layer = layer

    def _on_layer_set(self, layer: "TilemapLayer"):
        self.layer_neighbor_processor = layer.autotile_neighbor_processor

    def format(self):
        """Format the tile's display. Return True if the tile's display has changed."""
        previous_display = self.display

        if self.layer_neighbor_processor is None:
            raise ValueError("Tile is not in a layer to be formatted.")

        if (
            self.layer_neighbor_processor.get_amount_of_neighbors_of(self, radius=2)
            == 16
        ):
            self.is_deep = True
        else:
            self.is_deep = False

        neighbors_bool_grid = self.layer_neighbor_processor.get_neighbors_bool_grid(
            self
        )
        self._rule_format(neighbors_bool_grid)

        super().format()

        return self.display != previous_display

    def _rule_format(self, neighbors_bool_grid):
        """Change the tile's display based on the rules it has."""

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

        self.display = find_display(0)
