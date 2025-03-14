from typing import TYPE_CHECKING, Callable
import random

if TYPE_CHECKING:
    from ..layer.tilemap_layer import TilemapLayer


class Tile:
    """A class representing a tile. It contains information about its position, object type, and display. It also has a potential displays dictionary, which stores the chances of each display being chosen."""

    potential_displays_chance_sum = 0.0
    display: tuple[int, int]

    def __init__(
        self,
        position: tuple[int, int],
        display: tuple[int, int] = (0, 0),
    ):
        self.position = position

        self.potential_displays: dict[tuple[int, int], float] = {}
        self.set_display(display)

        self.layer_set_callbacks: list[Callable] = []

        self.locked = False

        self._layer: "TilemapLayer | None" = None

    def remove(self, apply_formatting=True):
        """Remove the tile from its layer."""
        if self.layer is None:
            raise ValueError("Tile is not in a layer to be removed.")
        self.layer.remove_tile(self, apply_formatting)

    @property
    def layer(self):
        if self._layer is None:
            raise ValueError(
                "Layer is not set. Make sure to append the tile to a layer before using it."
            )
        return self._layer

    @layer.setter
    def layer(self, layer: "TilemapLayer"):
        """Set the tile's layer."""
        self._layer = layer
        for callback in self.layer_set_callbacks:
            callback(layer)

    def set_position(self, position: tuple[int, int]):
        """Set the tile's position."""
        self.position = position

    def format(self):
        """Format the tile's display."""
        if len(self.potential_displays) > 0:
            chosen_chance = random.random() * self.potential_displays_chance_sum

            chance_sum = 0.0
            for potential_display, chance in self.potential_displays.items():
                chance_sum += chance
                if chosen_chance < chance_sum:
                    self.set_display(potential_display)
                    break

    def add_potential_display(self, tile_coordinates: tuple[int, int], chance: float):
        """Add a potential display to the tile. The tile will randomly choose one of the potential displays based on the chances provided. Therefore the chance can be any number, but the other potential displays added to this tile must be taken into account."""
        self.potential_displays[tile_coordinates] = chance
        self.potential_displays_chance_sum += chance

    def set_display(self, display: tuple[int, int]):
        """Set the tile's display."""
        self.display = display

    # def get_image(self):
    #     return self.tilemap.tileset.get_tile_image(self.position)
