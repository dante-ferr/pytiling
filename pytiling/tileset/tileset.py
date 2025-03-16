from PIL import Image
import numpy as np
import warnings
from typing import Any, Callable
from .tile_image_wrapper import TileImageWrapper
from functools import cached_property


class Tileset:
    """This object works over a tileset, mainly to get the tiles from it as byte images."""

    def __init__(self, tileset_path: str):
        self.atlas_image = Image.open(tileset_path)
        self._tile_size: tuple[int, int] | None = None
        self._tile_image_wrappers: np.ndarray[tuple[int, int], Any] | None = None

    @property
    def tile_size(self) -> tuple[int, int]:
        """Get the tile size of the tileset."""
        if not self._tile_size:
            raise ValueError(
                "Tile size not set for the tileset. Ensure it has been added to a tilemap (this is done automatically when adding a layer with this tileset to a tilemap)."
            )

        return self._tile_size

    @property
    def tile_image_wrappers(self) -> np.ndarray[tuple[int, int], Any]:
        """Get the tile image wrappers of the tileset."""
        if self._tile_image_wrappers is None:
            raise ValueError(
                "Tile images not set for the tileset. Ensure it has been added to a tilemap (this is done automatically when adding a layer with this tileset to a tilemap)."
            )

        return self._tile_image_wrappers

    @tile_image_wrappers.setter
    def tile_image_wrappers(self, value: np.ndarray[tuple[int, int], Any]):
        """Set the tile image wrappers of the tileset."""
        self._tile_image_wrappers = value

    @tile_size.setter
    def tile_size(self, value: tuple[int, int]):
        """Set the tile size of the tileset."""
        self._tile_size = value

        if not self._tile_image_wrappers:
            self.tile_image_wrappers = self._get_tile_image_wrappers()

    def _get_tile_image_wrappers(self) -> np.ndarray[tuple[int, int], Any]:
        tile_width, tile_height = self.tile_size
        tile_image_wrappers = np.empty(
            (self.grid_size[1], self.grid_size[0]), dtype=object
        )

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

        for x in range(0, self.grid_size[0] * tile_width, tile_width):
            for y in range(0, self.grid_size[1] * tile_height, tile_height):
                tile_image = self.atlas_image.crop(
                    (x, y, x + tile_width, y + tile_height)
                ).tobytes()

                tile_x = x // tile_width
                tile_y = y // tile_height

                tile_image_wrappers[tile_y, tile_x] = TileImageWrapper(tile_image)

        return tile_image_wrappers

    @cached_property
    def grid_size(self) -> tuple[int, int]:
        """Get the grid size of the tileset."""
        if not self.tile_size:
            raise ValueError("Tile size not set for the tileset.")
        return (
            self.atlas_image.width // self.tile_size[0],
            self.atlas_image.height // self.tile_size[1],
        )

    def tile_has_transparency(self, display: tuple[int, int]) -> bool:
        """Check if a tile has transparency."""
        return self.tile_image_wrappers[display[1], display[0]].has_transparency

    @cached_property
    def tile_images(self) -> np.ndarray[tuple[int, int], Any]:
        """Get the tile images as a numpy array. The format of each image is bytes."""

        tile_images = np.empty((self.grid_size[1], self.grid_size[0]), dtype=object)
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                tile_images[y, x] = self.tile_image_wrappers[y, x].image
        return tile_images

    def for_tile_image(self, callback: Callable[[bytes, int, int], None]):
        """
        Call a callback function for each tile image in the tileset.
        The callback function should take three arguments:
        - byte_data: The byte data of the tile image.
        - x: The x position of the tile image.
        - y: The y position of the tile image.
        """
        for x in range(self.tile_images.shape[0]):
            for y in range(self.tile_images.shape[1]):
                byte_data = self.tile_images[x, y]
                if byte_data:
                    callback(byte_data, x, y)
