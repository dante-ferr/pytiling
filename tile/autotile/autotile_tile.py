from ..tile import Tile
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...layer.layer_neighbor_processor import LayerNeighborProcessor
    from .autotile_rule import AutotileRule
    from layer import TilemapLayer


class AutotileTile(Tile):
    """A class representing an autotile tile. It extends the Tile class and adds the ability to change its display based on the rules it has. Each rule defines a specific display based on the tile's neighbors."""

    rules: list["AutotileRule"]
    is_deep = False

    def __init__(self, position: tuple[int, int], autotile_object: str):
        super().__init__(position)
        self.autotile_object = autotile_object

        self.layer_neighbor_processor: "LayerNeighborProcessor | None" = None
        self.layer_set_callbacks.append(self._on_layer_set)

        self.display = (0, 0)

    def _on_layer_set(self, layer: "TilemapLayer"):
        from ...layer.layer_neighbor_processor import LayerNeighborProcessor

        self.layer_neighbor_processor = LayerNeighborProcessor(layer)

    def format(self):
        """Format the tile's display"""
        if self.layer_neighbor_processor is None:
            return

        if (
            self.layer_neighbor_processor.get_amount_of_neighbors_of(self, radius=2)
            == 16
        ):
            self.is_deep = True
        else:
            self.is_deep = False

        neighbors = self.layer_neighbor_processor.get_neighbors_of(self)
        self._rule_format(neighbors)

        super().format()

    def _rule_format(self, filtered_neighbors):
        """Change the tile's display based on the rules it has."""

        def find_display(rule_index: int):
            if rule_index >= len(self.rules):
                warnings.warn("No display found", UserWarning)
                return (0, 0)
            rule = self.layer.autotile_rules[self.autotile_object][rule_index]

            for y, row in enumerate(rule.rule_matrix):
                for x, cell in enumerate(row):
                    if cell == 1:
                        continue
                    if cell == 2:
                        continue

                    neighbor_cell = filtered_neighbors[y, x]
                    if (neighbor_cell and cell == 0) or (
                        (not neighbor_cell) and cell == 3
                    ):
                        return find_display(rule_index + 1)

            return rule.display

        self.display = find_display(0)
