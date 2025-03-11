from typing import TYPE_CHECKING, Literal, Any, cast
import numpy as np
from ..tile.autotile import AutotileTile

if TYPE_CHECKING:
    from .tilemap_layer import TilemapLayer
    from ..tile import Tile


class LayerNeighborProcessor:
    """A class representing a processor that processes the neighbors of a tile in a tilemap layer."""

    def __init__(self, layer: "TilemapLayer"):
        self.layer = layer

    def get_neighbors_of(
        self,
        tile: "Tile",
        radius: int = 1,
        same_autotile_object=False,
        output_type: Literal["tile_grid", "bool_grid", "amount"] = "bool_grid",
        adjacency_rule: Literal[
            "eight_neighbors", "four_neighbors"
        ] = "eight_neighbors",
    ):
        """Get the neighbors of a tile in a given radius."""
        neighbors: Any

        matrix_size = radius * 2 + 1
        if output_type == "tile_grid":
            neighbors = np.empty((matrix_size, matrix_size), dtype=Tile)
        elif output_type == "bool_grid":
            neighbors = np.full((matrix_size, matrix_size), False)
        elif output_type == "amount":
            neighbors = 0

        if radius == 0:
            return neighbors

        def tile_neighbors_callback(x, y):
            nonlocal neighbors
            nonlocal tile
            if tile.position is None:
                return
            tile_position: tuple[int, int] = tile.position

            if x == tile.position[0] and y == tile.position[1]:
                return
            neighbor = self.layer.get_tile_at((x, y))
            if neighbor is None:
                return
            if same_autotile_object:
                tile = cast(AutotileTile, tile)
                neighbor = cast(AutotileTile, neighbor)
                if (
                    neighbor.autotile_object is not None
                    and neighbor.autotile_object != tile.autotile_object
                ):
                    return

            if output_type == "tile_grid":
                neighbors[
                    y - tile_position[1] + radius, x - tile_position[0] + radius
                ] = neighbor
            elif output_type == "bool_grid":
                neighbors[
                    y - tile_position[1] + radius, x - tile_position[0] + radius
                ] = True
            elif output_type == "amount":
                neighbors += 1

        if adjacency_rule == "eight_neighbors":
            self.layer.loop_over_area(
                self.layer._get_area_around(tile.position, radius),
                tile_neighbors_callback,
            )
        elif adjacency_rule == "four_neighbors":
            if radius > 1:
                raise ValueError("Radius must be 1 for four neighbors search.")

            tile_x, tile_y = tile.position
            positions = [
                (tile_x + 1, tile_y),
                (tile_x, tile_y - 1),
                (tile_x - 1, tile_y),
                (tile_x, tile_y + 1),
            ]
            for position in positions:
                if self.layer._position_is_valid(position):
                    tile_neighbors_callback(*position)

        return neighbors
