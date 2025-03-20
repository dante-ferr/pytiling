from typing import cast
import random
from functools import cached_property
from ..grid_element import GridElement
from typing import TYPE_CHECKING
import json

if TYPE_CHECKING:
    from layer.tilemap_layer import TilemapLayer
    from layer import GridLayer


class Tile(GridElement):
    """A class representing a tile. It contains information about its position, object type, and display. It also has a variations dictionary, which stores the chances of each display being chosen."""

    variations_chance_sum = 0.0
    display: tuple[int, int]

    def __init__(
        self,
        position: tuple[int, int],
        display: tuple[int, int] = (0, 0),
        name: str = "",
    ):
        super().__init__(position)
        self.position = position
        self.set_display(display)
        self.name = name

        self.variations: dict[tuple[int, int], float] = {}

    def add_variations_from_json(self, json_path: str, apply_formatting=False):
        with open(json_path, "r") as file:
            variations_data = json.load(file)

        for variation in variations_data:
            display = (variation["display"][0], variation["display"][1])
            self.add_variation(display, variation["chance"])

        if apply_formatting:
            self.format()

    @property
    def layer(self):
        return cast("TilemapLayer", super().layer)

    @layer.setter
    def layer(self, layer: "GridLayer"):
        """Set the tile's layer."""
        self._layer = layer

    def remove(self, apply_formatting=True):
        """Remove the tile from its layer."""
        if self.layer is None:
            raise ValueError("Tile is not in a layer to be removed.")
        self.layer.remove_tile(self, apply_formatting)

    def format(self):
        """Format the tile's display. Return True if the tile's display has changed."""
        previous_display = self.display

        self.set_variation_display()

        self.layer.events["tile_formatted"].send(tile=self)

        return previous_display != self.display

    def set_variation_display(self):
        """Set the tile's display to a random variation."""
        if len(self.variations) > 0:
            chosen_chance = random.random() * self.variations_chance_sum

            chance_sum = 0.0
            for potential_display, chance in self.variations.items():
                chance_sum += chance
                if chosen_chance < chance_sum:
                    self.set_display(potential_display)
                    break

    def add_variation(self, display: tuple[int, int], chance: float):
        """Add a variation to the tile. The tile will randomly choose one of the variations based on the chances provided. Therefore the chance can be any number, but the other variations added to this tile must be taken into account."""
        self.variations[display] = chance
        self.variations_chance_sum += chance

    def reset_variations(self):
        self.variations = {}
        self.variations_chance_sum = 0.0

    def set_display(self, display: tuple[int, int]):
        """Set the tile's display."""
        self.display = display

    @cached_property
    def has_transparency(self) -> bool:
        return self.layer.tileset.tile_has_transparency(self.display)

    @property
    def tile_above(self) -> "Tile | None":
        """Get the tile above this tile."""
        return cast("Tile | None", super().element_above)

    @property
    def tile_below(self) -> "Tile | None":
        """Get the tile below this tile."""
        layer_below = self.layer.layer_below
        if layer_below is None:
            return

        return cast("Tile | None", super().element_below)

    # def get_image(self):
    #     return self.tilemap.tileset.get_tile_image(self.position)
