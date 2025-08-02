from typing import TYPE_CHECKING
import pyglet

if TYPE_CHECKING:
    from pytiling.layer.tilemap_layer.tilemap_layer import TilemapLayer
    from .tileset_image import TilesetImage
    from pytiling.grid_element.tile import Tile


class LayerRenderer:
    def __init__(self, layer: "TilemapLayer", tileset_image: "TilesetImage"):
        self.layer = layer
        self.tileset_image = tileset_image
        self.batch = pyglet.graphics.Batch()
        self.sprites = []  # Keep references to sprites

        self._initialize_tile_sprites()

    def _initialize_tile_sprites(self):
        """Create sprites for each tile and add them to the batch."""
        self.layer.events["tile_formatted"].connect(
            self._handle_tile_formatted, weak=True
        )
        self.layer.for_all_elements(self.create_tile_sprite)

    def _handle_tile_formatted(self, sender, tile: "Tile"):
        self.create_tile_sprite(tile)

    def create_tile_sprite(self, tile: "Tile"):
        if not tile.position or tile.display is None:
            return

        tile_image = self.tileset_image.get_tile_image(tile.display)
        if tile_image is None:
            return

        x, y = tile.position
        tile_x, tile_y = self.layer.grid_pos_to_actual_pos((x, y))
        # Create sprite with texture and add to batch
        spr = pyglet.sprite.Sprite(
            tile_image.get_texture(), x=tile_x, y=tile_y, batch=self.batch
        )
        self.sprites.append(spr)

    def render(self):
        self.batch.draw()
