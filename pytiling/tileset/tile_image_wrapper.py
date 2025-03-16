from PIL import Image
import io
from functools import cached_property


class TileImageWrapper:
    """This class represents a tile image. It contains the image data and the tile size."""

    def __init__(self, image: bytes):
        self.image = image

    @cached_property
    def has_transparency(self) -> bool:
        image = Image.open(io.BytesIO(self.image))

        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            alpha = image.getchannel("A")
            return any(pixel < 255 for pixel in alpha.getdata())

        return False
