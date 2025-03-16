from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .grid_layer import GridLayer


class LayerChecker:
    """A class for checking the validity of the properties of a tilemap layer."""

    def __init__(self, layer: "GridLayer"):
        self.layer = layer

    def check_position(self, position: tuple[int, int] | None):
        if position is None:
            raise ValueError(
                "Tile position cannot be None. Ensure to set the position of the tile before adding it to the layer."
            )

        if not self.position_is_valid(position):
            raise ValueError(
                f"Position {position} is not valid, because it is out of bounds for the grid {self.layer.grid_size}."
            )

    def position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.layer.grid_size[0]
            and position[1] < self.layer.grid_size[1]
        )
