from PIL import Image
import numpy as np
import warnings
from typing import Any


class Tileset:
    """This object works over a tileset, mainly to get the tiles from it as byte images."""

    tile_size: tuple[int, int]

    def __init__(self, tileset_path: str, tile_size: tuple[int, int]):
        self.atlas_image = Image.open(tileset_path)
        self.tile_size = tile_size

        tile_width, tile_height = self.tile_size
        self.size = (
            self.atlas_image.size[0] // tile_width,
            self.atlas_image.size[1] // tile_height,
        )

    def get_tile_images(self):
        tile_images = np.empty((self.size[1], self.size[0]), dtype=Any)

        tile_width, tile_height = self.tile_size

        if self.atlas_image.width % tile_width != 0:
            warnings.warn(
                "The atlas image width is not a multiple of the tile width. The last tile won't be used.",
                UserWarning,
            )
        if self.atlas_image.height % tile_height != 0:
            warnings.warn(
                "The atlas image height is not a multiple of the tile height. The last tile won't be used.",
                UserWarning,
            )

        for x in range(0, self.size[0] * tile_width, tile_width):
            for y in range(0, self.size[1] * tile_height, tile_height):
                tile_image = self.atlas_image.crop(
                    (x, y, x + tile_width, y + tile_height)
                ).tobytes()

                tile_x = x // tile_width
                tile_y = y // tile_height

                tile_images[tile_y, tile_x] = tile_image

        return tile_images

    # def get_tile_image(self, tile_position: tuple[int, int]) -> bytes:
    #     return self.tile_images[tile_position]
