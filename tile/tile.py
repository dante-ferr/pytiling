from typing import TYPE_CHECKING, Callable
import random

if TYPE_CHECKING:
    from ..tilemap_layer import TilemapLayer


class Tile:
    """A class representing a tile. It contains information about its position, object type, and display. It also has a potential displays dictionary, which stores the chances of each display being chosen."""

    potential_displays_chance_sum = 0.0

    def __init__(
        self,
        position: tuple[int, int] | None = None,
        display: tuple[int, int] | None = None,
    ):
        self.position = position
        self.display: tuple[int, int] | None = None

        self.potential_displays: dict[tuple[int, int], float] = {}
        self.set_display(display)

        self.format_callbacks: list[Callable] = []

    def set_layer(self, layer: "TilemapLayer"):
        """Set the tile's layer."""
        self.layer = layer

    def set_position(self, position: tuple[int, int] | None):
        """Set the tile's position."""
        self.position = position

    def format(self, individual_callbacks: list[Callable] = []):
        """Format the tile's display."""
        for callback in self.format_callbacks:
            callback(self)
        for callback in self.layer.format_callbacks:
            callback(self)

        if len(self.potential_displays) > 0:
            chosen_chance = random.random() * self.potential_displays_chance_sum

            chance_sum = 0.0
            for potential_display, chance in self.potential_displays.items():
                chance_sum += chance
                if chosen_chance < chance_sum:
                    self.set_display(potential_display)
                    break

    def add_format_callback(self, *callbacks: Callable):
        """Add a callback to be called when the tile is formatted."""
        for callback in callbacks:
            self.format_callbacks.append(callback)

    def add_potential_display(self, tile_coordinates: tuple[int, int], chance: float):
        """Add a potential display to the tile. The tile will randomly choose one of the potential displays based on the chances provided. Therefore the chance can be any number, but the other potential displays added to this tile must be taken into account."""
        self.potential_displays[tile_coordinates] = chance
        self.potential_displays_chance_sum += chance

    def set_display(self, display: tuple[int, int] | None):
        """Set the tile's display."""
        self.display = display

    # def get_image(self):
    #     return self.tilemap.tileset.get_tile_image(self.position)
