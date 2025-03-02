import pyglet
import numpy as np
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tilemap_layer import TilemapLayer
    from .tileset_image import TilesetImage
    from tile.tile import Tile


class LayerRenderer:
    """A helper object that can be used to render a tilemap layer using pyglet."""

    tile_sprites: np.ndarray[tuple[int, int], Any]

    def __init__(self, layer: "TilemapLayer", tileset_image: "TilesetImage"):
        self.layer = layer
        self.tileset_image = tileset_image

        self.tile_sprites = np.empty(
            (layer.grid.shape[0], layer.grid.shape[1]), dtype=object
        )
        self.batch = pyglet.graphics.Batch()

        self._initialize_tile_sprites()

    @property
    def layer_width(self):
        return self.layer.grid.shape[1]

    @property
    def layer_height(self):
        return self.layer.grid.shape[0]

    def _initialize_tile_sprites(self):
        """Create a dictionary of numpy 2d arrays of tile sprites. Each array corresponds to a layer in the tilemap."""
        self.layer.add_format_callback(lambda tile: self.create_tile_sprite(tile))

        # for x in range(self.layer_width):
        #     for y in range(self.layer_height):
        #         tile = self.layer.grid[y, x]
        #         if tile is None:
        #             continue
        #         self.create_tile_sprite(tile)

    def create_tile_sprite(self, tile: "Tile"):
        if not tile.position:
            return
        x, y = tile.position
        if tile.display is None:
            return

        tile_x_pos, tile_y_pos = self.layer.tilemap_pos_to_actual_pos(tile.position)

        tile_image = self.tileset_image.get_tile_image(tile.display)
        if tile_image is None:
            return

        tile_sprite = pyglet.sprite.Sprite(
            tile_image, tile_x_pos, tile_y_pos, batch=self.batch
        )
        tile_sprite.scale_x = 1
        tile_sprite.scale_y = 1
        self.tile_sprites[y, x] = tile_sprite

    def render(self):
        self.batch.draw()
