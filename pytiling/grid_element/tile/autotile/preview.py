"""Dry-run autotile preview helpers for editor ghosts."""

from typing import Callable, Iterable
from .autotile_tile import AutotileTile
from .autotile_rule import AutotileRule
from pytiling.layer.tilemap_layer.tilemap_layer_neighbor_processor import (
    TilemapLayerNeighborProcessor,
)


def preview_autotile_displays(
    cells: Iterable[tuple[int, int]],
    occupied: set[tuple[int, int]],
    position_is_valid: Callable[[tuple[int, int]], bool],
    rules: list[AutotileRule],
) -> dict[tuple[int, int], tuple[int, int]]:
    """Return tileset display coords for each cell given a virtual occupancy set."""
    displays: dict[tuple[int, int], tuple[int, int]] = {}
    for cell in cells:
        neighbors = TilemapLayerNeighborProcessor.neighbors_bool_grid_from_occupancy(
            cell, occupied, position_is_valid
        )
        displays[cell] = AutotileTile.display_from_neighbor_grid(neighbors, rules)
    return displays
