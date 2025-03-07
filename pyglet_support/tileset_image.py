import numpy as np
import pyglet
from typing import TYPE_CHECKING, Any
from PIL import Image

if TYPE_CHECKING:
    from ..tileset import Tileset


class TilesetImage:
    def __init__(self, tileset: "Tileset"):
        self.tileset = tileset

        self.tile_images = np.empty(
            (tileset.size[0], tileset.size[1]),
            dtype=object,
        )

        self.tileset.for_tile_image(self._populate_tile_images)

    def _populate_tile_images(self, byte_data: bytes, x: int, y: int):
        """Populate the tile images array with pyglet images."""
        self.tile_images[x, y] = self._create_pyglet_image_from_bytes(byte_data)

    def _create_pyglet_image_from_bytes(self, byte_data: bytes):
        """Create a pyglet image from a byte data."""
        tile_width, tile_height = self.tileset.tile_size

        image_data = Image.frombytes("RGBA", (tile_width, tile_height), byte_data)
        image_data = image_data.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        byte_data_flipped = image_data.tobytes()
        return pyglet.image.ImageData(
            tile_width, tile_height, "RGBA", byte_data_flipped
        )

    def get_tile_image(self, display: tuple[int, int]) -> pyglet.image.ImageData | None:
        """Get the pyglet image for a tile."""
        return self.tile_images[display[0], display[1]]
