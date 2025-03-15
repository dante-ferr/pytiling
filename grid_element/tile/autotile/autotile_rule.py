from utils import rotate_matrix
import numpy as np


class AutotileRule:
    """
    A class representing an autotile rule. It contains a rule matrix and a display.
    - Rule matrix: a 2D array of integers with shape (3, 3). The center cell of the matrix represents the tile on which the rule applies, while the other ones represent its neighbors.
      - 0: no tile from the same layer
      - 1: autotile tile
      - 2: any tile within the same layer (including no tile)
      - 3: tiles within the same layer with the same object type
    - Display: a tuple of two integers representing the x and y coordinates of the tile's display in the layer's tileset.
    """

    display: tuple[int, int]

    def __init__(
        self,
        rule_matrix: list[list[int]],
        display: tuple[int, int],
    ):
        self.rule_matrix = np.array(rule_matrix)
        self.display = display


def get_rule_group(
    rule_matrix: list[list[int]], display: tuple[int, int], amount: int = 4
):
    """Create a rule group from a base rule matrix and a display. The rule matrix will be rotated and the display will be adjusted accordingly."""
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if amount > 4:
        raise ValueError("Amount must be less than or equal to 4")

    x, y = display
    if amount == 2:
        angles = [0, 90]
        displays = [(x, y), (x, y + 1)]
    else:
        angles = [0, 90, 180, 270][:amount]
        displays = [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)][:amount]

    rule_matrixes = [rotate_matrix(rule_matrix, angle) for angle in angles]

    return [AutotileRule(rm, d) for rm, d in zip(rule_matrixes, displays)]
