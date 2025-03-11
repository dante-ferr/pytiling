import pyglet
import numpy as np
from typing import Any, TYPE_CHECKING
from ..utils import refine_texture

if TYPE_CHECKING:
    from layer.tilemap_layer import TilemapLayer
    from .tileset_image import TilesetImage
    from tile.tile import Tile
    from pyglet.image import Texture


class LayerRenderer:
    """A helper object that can be used to render a tilemap layer using pyglet."""

    def __init__(self, layer: "TilemapLayer", tileset_image: "TilesetImage"):
        self.layer = layer
        self.tileset_image = tileset_image
        self.active_tile_textures: dict[tuple[int, int], "Texture"] = {}

        self._initialize_tile_textures()

    @property
    def layer_width(self):
        return self.layer.grid.shape[1]

    @property
    def layer_height(self):
        return self.layer.grid.shape[0]

    def _initialize_tile_textures(self):
        """Create textures for each tile in the layer."""
        self.layer.formatter.add_format_callback(
            lambda tile: self.create_tile_texture(tile)
        )

    def create_tile_texture(self, tile: "Tile"):
        if not tile.position:
            return
        if tile.display is None:
            return

        tile_image = self.tileset_image.get_tile_image(tile.display)
        if tile_image is None:
            return

        texture = tile_image.get_texture()
        refine_texture()

        self.active_tile_textures[tile.position] = texture

    def render(self):
        for x, y in self.active_tile_textures.keys():
            texture = self.active_tile_textures[x, y]
            tile_x_pos, tile_y_pos = self.layer.tilemap_pos_to_actual_pos((x, y))
            texture.blit(int(tile_x_pos), int(tile_y_pos))
