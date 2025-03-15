from typing import cast
import random
from functools import cached_property
from utils import Direction
from ..grid_element import GridElement
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from layer.tilemap_layer import TilemapLayer
    from layer import GridLayer


class Tile(GridElement):
    """A class representing a tile. It contains information about its position, object type, and display. It also has a potential displays dictionary, which stores the chances of each display being chosen."""

    potential_displays_chance_sum = 0.0
    display: tuple[int, int]

    def __init__(
        self,
        position: tuple[int, int],
        display: tuple[int, int] = (0, 0),
        tile_object: str = "",
    ):
        super().__init__(position)
        self.position = position
        self.set_display(display)
        self.tile_object = tile_object

        self.potential_displays: dict[tuple[int, int], float] = {}

        self.locked = False

    @property
    def layer(self):
        return cast("TilemapLayer", super().layer)

    @layer.setter
    def layer(self, layer: "GridLayer"):
        """Set the tile's layer."""
        super().layer = layer

    def remove(self, apply_formatting=True):
        """Remove the tile from its layer."""
        if self.layer is None:
            raise ValueError("Tile is not in a layer to be removed.")
        self.layer.remove_tile(self, apply_formatting)

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

    @property
    def edges(self) -> list[Direction] | None:
        """Returns the edges which the tile is on, or None if the tile is not on the edge."""
        edges: list[Direction] = []
        layer_width, layer_height = self.layer.size

        if self.position[1] == 0:
            edges.append("top")
        elif self.position[1] == layer_height - 1:
            edges.append("bottom")
        if self.position[0] == 0:
            edges.append("left")
        if self.position[0] == layer_width - 1:
            edges.append("right")

        if len(edges) == 0:
            return None
        return edges

    @property
    def is_on_edge(self) -> bool:
        """Returns True if the tile is on an edge, False otherwise."""
        return (
            self.position[0] == 0
            or self.position[0] == self.layer.size[0] - 1
            or self.position[1] == 0
            or self.position[1] == self.layer.size[1] - 1
        )

    # def get_image(self):
    #     return self.tilemap.tileset.get_tile_image(self.position)
