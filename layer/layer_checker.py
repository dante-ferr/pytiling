from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tilemap_layer import TilemapLayer


class LayerChecker:
    """A class for checking the validity of the properties of a tilemap layer."""

    def __init__(self, layer: "TilemapLayer"):
        self.layer = layer

    def check_grid(self):
        if self.layer._grid is None:
            raise ValueError(
                "Grid is not initialized. Make sure to add this layer to a tilemap before adding tiles."
            )

    def check_position(self, position: tuple[int, int] | None):
        if position is None:
            raise ValueError(
                "Tile position cannot be None. Ensure to set the position of the tile before adding it to the layer."
            )

        if not self.position_is_valid(position):
            raise ValueError(
                f"Position {position} is not valid, because it is out of bounds for the grid ({self.layer.grid.shape})."
            )

    def position_is_valid(self, position: tuple[int, int]):
        return (
            position[0] >= 0
            and position[1] >= 0
            and position[0] < self.layer.grid.shape[1]
            and position[1] < self.layer.grid.shape[0]
        )
