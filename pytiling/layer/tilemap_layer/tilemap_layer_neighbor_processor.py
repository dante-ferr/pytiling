from typing import TYPE_CHECKING, Literal, Callable, Union
import numpy as np
from pytiling.grid_element.tile.autotile import AutotileTile


if TYPE_CHECKING:
    from . import TilemapLayer
    from grid_element.tile import Tile

Neighbor = Union[Literal["out_of_grid"], "Tile"]


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

        def neighbor_callback(neighbor: "Neighbor", _position: tuple[int, int]):
            nonlocal neighbors
            neighbors += 1

        self._for_neighbor_of(neighbor_callback, tile, radius)
        return neighbors

    def get_neighbors_bool_grid(self, tile: "Tile", radius: int = 1):
        matrix_size = self._get_matrix_size(radius)
        neighbors = np.full((matrix_size, matrix_size), False)

        def neighbor_callback(_neighbor: "Neighbor", position: tuple[int, int]):
            offset_x, offset_y = self.calculate_offset(position, tile, radius)
            neighbors[offset_y, offset_x] = True

        self._for_neighbor_of(neighbor_callback, tile, radius)
        return neighbors

    def get_neighbors_of(self, tile: "Tile", radius: int = 1):
        matrix_size = self._get_matrix_size(radius)
        neighbors = np.empty((matrix_size, matrix_size), dtype=object)

        def neighbor_callback(neighbor: "Neighbor", position: tuple[int, int]):
            offset_x, offset_y = self.calculate_offset(position, tile, radius)
            neighbors[offset_y, offset_x] = neighbor

        self._for_neighbor_of(neighbor_callback, tile, radius)
        return neighbors

    def calculate_offset(
        self, position: tuple[int, int], tile: "Tile", radius: int = 1
    ):
        x, y = position

        tile_x, tile_y = tile.position
        return ((x - tile_x) + radius, (y - tile_y) + radius)

    def _for_neighbor_of(
        self,
        callback: Callable[[Neighbor, tuple[int, int]], None],
        tile: "Tile",
        radius,
    ):
        positions = self._generate_positions(tile.position, radius)

        for x, y in positions:
            neighbor = self._get_neighbor_of_tile_at(tile, x, y)
            if neighbor is None:
                continue
            callback(neighbor, (x, y))

    def _generate_positions(
        self,
        center_position: tuple[int, int],
        radius: int,
    ) -> list[tuple[int, int]]:
        """Generates positions to check based on adjacency rule and radius."""
        center_x, center_y = center_position
        positions = []
        if self.adjacency_rule == "eight":
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    positions.append((center_x + dx, center_y + dy))
        elif self.adjacency_rule == "four":
            if radius != 1:
                raise ValueError("Four neighbors adjacency requires radius=1")
            positions = [
                (center_x + 1, center_y),
                (center_x, center_y - 1),
                (center_x - 1, center_y),
                (center_x, center_y + 1),
            ]
        else:
            raise ValueError(f"Invalid adjacency rule: {self.adjacency_rule}")
        return positions

    def _get_neighbor_of_tile_at(
        self,
        tile: "Tile",
        x: int,
        y: int,
    ) -> Union[Neighbor, None]:
        """Determines if a position qualifies as a valid neighbor."""
        is_out_of_grid = not self.layer.checker.position_is_valid((x, y))
        if is_out_of_grid:
            return "out_of_grid"
        neighbor = self.layer.get_tile_at((x, y))

        if self.same_autotile_object:
            if (
                neighbor is not None
                and isinstance(tile, AutotileTile)
                and isinstance(neighbor, AutotileTile)
                and neighbor.tile_object == tile.tile_object
            ):
                return neighbor
        else:
            return neighbor

    def _get_matrix_size(self, radius: int) -> int:
        return radius * 2 + 1
