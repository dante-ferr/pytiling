from typing import TYPE_CHECKING, Literal, Any, Callable
import numpy as np


if TYPE_CHECKING:
    from . import TilemapLayer
    from ...tile import Tile
    from ...tile.autotile import AutotileTile


class TilemapLayerNeighborProcessor:
    """Processes tile neighbors in a tilemap layer, considering out-of-grid spaces as neighbors."""

    def __init__(
        self,
        layer: "TilemapLayer",
        adjancecy_rule: Literal["eight", "four"] = "eight",
        same_autotile_object: bool = False,
    ):
        self.layer = layer
        self.adjacency_rule: Literal["eight", "four"] = adjancecy_rule
        self.same_autotile_object = same_autotile_object

    def get_amount_of_neighbors_of(self, tile: "Tile", radius: int = 1):
        neighbors = 0

        def neighbor_callback(offset_x: int, offset_y: int):
            nonlocal neighbors
            neighbors += 1

        self._for_neighbor_of(neighbor_callback, tile, radius)
        return neighbors

    def get_neighbors_bool_grid(self, tile: "Tile", radius: int = 1):
        matrix_size = self._get_matrix_size(radius)
        neighbors = np.full((matrix_size, matrix_size), False)

        def neighbor_callback(offset_x: int, offset_y: int):
            neighbors[offset_y, offset_x] = True

        self._for_neighbor_of(neighbor_callback, tile, radius)
        return neighbors

    def get_neighbors_of(self, tile: "Tile", radius: int = 1):
        matrix_size = self._get_matrix_size(radius)
        neighbors = np.empty((matrix_size, matrix_size), dtype=object)

        def neighbor_callback(offset_x: int, offset_y: int):
            neighbors[offset_y, offset_x] = self.layer.get_tile_at((offset_x, offset_y))

        self._for_neighbor_of(neighbor_callback, tile, radius)
        return neighbors

    def _for_neighbor_of(self, callback: Callable, tile: "Tile", radius):
        tile_x, tile_y = tile.position
        positions = self._generate_positions(tile_x, tile_y, radius)

        for x, y in positions:
            if not self._is_valid_neighbor(tile, x, y, self.same_autotile_object):
                continue

            offset_x = (x - tile_x) + radius
            offset_y = (y - tile_y) + radius
            callback(offset_x, offset_y)

    def _generate_positions(
        self,
        tile_x: int,
        tile_y: int,
        radius: int,
    ) -> list[tuple[int, int]]:
        """Generates positions to check based on adjacency rule and radius."""
        positions = []
        if self.adjacency_rule == "eight":
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    positions.append((tile_x + dx, tile_y + dy))
        elif self.adjacency_rule == "four":
            if radius != 1:
                raise ValueError("Four neighbors adjacency requires radius=1")
            positions = [
                (tile_x + 1, tile_y),
                (tile_x, tile_y - 1),
                (tile_x - 1, tile_y),
                (tile_x, tile_y + 1),
            ]
        else:
            raise ValueError(f"Invalid adjacency rule: {self.adjacency_rule}")
        return positions

    def _is_valid_neighbor(
        self,
        tile: "Tile",
        x: int,
        y: int,
        same_autotile_object: bool,
    ) -> bool:
        """Determines if a position qualifies as a valid neighbor."""
        is_out_of_grid = not self.layer.checker.position_is_valid((x, y))

        if same_autotile_object:
            if is_out_of_grid:
                return False
            neighbor = self.layer.get_tile_at((x, y))
            return (
                neighbor is not None
                and isinstance(tile, "AutotileTile")
                and isinstance(neighbor, "AutotileTile")
                and neighbor.autotile_object == tile.autotile_object
            )
        else:
            return is_out_of_grid or self.layer.get_tile_at((x, y)) is not None

    def _get_matrix_size(self, radius: int) -> int:
        return radius * 2 + 1
