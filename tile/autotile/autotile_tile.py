from ..tile import Tile
from .autotile_rule import AutotileRule

import warnings


class AutotileTile(Tile):
    """A class representing an autotile tile. It extends the Tile class and adds the ability to change its display based on the rules it has. Each rule defines a specific display based on the tile's neighbors."""

    rules: list[AutotileRule]
    is_deep = False

    def __init__(self, position: tuple[int, int], autotile_object: str):
        super().__init__(position)
        self.autotile_object = autotile_object

        self.display = None

    def format(self):
        """Format the tile's display"""
        if self.layer is None:
            return

        if (
            self.layer.get_neighbors_of(
                self, radius=2, same_autotile_object=True, output_type="amount"
            )
            == 16
        ):
            self.is_deep = True
        else:
            self.is_deep = False

        neighbors = self.layer.get_neighbors_of(self, same_autotile_object=True)
        self._rule_format(neighbors)

        super().format()

    def _rule_format(self, filtered_neighbors):
        """Change the tile's display based on the rules it has."""

        def find_display(rule_index: int):
            if rule_index >= len(self.rules):
                warnings.warn("No display found", UserWarning)
                return
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
