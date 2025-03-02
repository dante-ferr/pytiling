import numpy as np
import pyglet
from typing import TYPE_CHECKING, Any
from PIL import Image

if TYPE_CHECKING:
    from ..tileset import Tileset


class TilesetImage:
    tiles: np.ndarray[tuple[int, int], Any]

    def __init__(self, tileset: "Tileset"):
        self.tileset = tileset

        self.tiles = np.empty(
            (tileset.size[1], tileset.size[0]),
            dtype=pyglet.image.ImageData,
        )

        self._create_tile_images()

    def _create_tile_images(self):
        tile_byte_images = self.tileset.tile_images

        for x in range(tile_byte_images.shape[1]):
            for y in range(tile_byte_images.shape[0]):
                byte_data = tile_byte_images[y, x]
                if byte_data:
                    self.tiles[y, x] = self._pyglet_image_from_bytes(
                        byte_data, self.tileset, x, y
                    )

    def _pyglet_image_from_bytes(
        self, byte_data: bytes, tileset: "Tileset", x: int, y: int
    ):
        """Create a pyglet image from a byte array."""
        tile_width, tile_height = tileset.tile_size

        image_data = Image.frombytes("RGBA", (tile_width, tile_height), byte_data)
        image_data = image_data.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        byte_data_flipped = image_data.tobytes()

        return pyglet.image.ImageData(
            tile_width, tile_height, "RGBA", byte_data_flipped
        )

    def get_tile_image(self, display: tuple[int, int]) -> pyglet.image.ImageData | None:
        """Get the pyglet image for a tile."""
        return self.tiles[display[1], display[0]]
