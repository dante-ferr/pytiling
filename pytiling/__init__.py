# import sys
# import os

# current_folder = os.path.dirname(__file__)

# previous_folder = os.path.abspath(os.path.join(current_folder, os.pardir))
# if previous_folder in sys.path:
#     sys.path.remove(previous_folder)

# sys.path.append(current_folder)


from .grid_element import GridElement
from .grid_element.tile.autotile.autotile_tile import AutotileTile
from .grid_element.tile.autotile.autotile_rule import AutotileRule
from .grid_element.tile import Tile
from .layer.tilemap_layer import TilemapLayer
from .layer import GridLayer
from .tilemap import Tilemap
from .tileset.tileset import Tileset
from .tools.tilemap_border_tracer import TilemapBorderTracer
from .physics.pymunk_tilemap_physics import PymunkTilemapPhysics
from .grid_map import GridMap
from .utils.direction import Direction, direction_vectors, opposite_directions

__all__ = [
    "AutotileRule",
    "AutotileTile",
    "Tile",
    "Tilemap",
    "TilemapLayer",
    "GridLayer",
    "Tileset",
    "TilemapBorderTracer",
    "PymunkTilemapPhysics",
    "GridMap",
    "GridElement",
    "Direction",
    "direction_vectors",
    "opposite_directions",
]
