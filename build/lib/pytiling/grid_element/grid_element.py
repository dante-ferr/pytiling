from typing import TYPE_CHECKING
from pytiling.utils import Direction

if TYPE_CHECKING:
    from layer import GridLayer


class GridElement:
    def __init__(
        self,
        position: tuple[int, int],
        name: str = "",
        unique: bool = False,
    ):
        self.position = position
        self.name = name
        self.unique = unique

        self.locked = False

        self._layer: "GridLayer | None" = None

    def remove(self):
        """Remove the element from its layer."""
        if self.layer is None:
            raise ValueError("Element is not in a layer to be removed.")
        self.layer.remove_element(self)

    def set_position(self, position: tuple[int, int]):
        """Set the element's position."""
        self.position = position

    @property
    def layer(self) -> "GridLayer":
        """Get the element's layer."""
        if self._layer is None:
            raise ValueError(
                "Layer is not set. Make sure to append the element to a layer before using it."
            )
        return self._layer

    @layer.setter
    def layer(self, layer: "GridLayer"):
        """Set the element's layer."""
        self._layer = layer

    @property
    def element_above(self) -> "GridElement | None":
        """Get the tile above this tile."""
        layer_above = self.layer.layer_above
        if layer_above is None:
            return None

        return layer_above.get_element_at(self.position)

    @property
    def element_below(self) -> "GridElement | None":
        """Get the tile below this tile."""
        layer_below = self.layer.layer_below
        if layer_below is None:
            return

        return layer_below.get_element_at(self.position)

    @property
    def edges(self) -> list[Direction] | None:
        """Returns the edges which the tile is on, or None if the tile is not on the edge."""
        edges: list[Direction] = []
        layer_width, layer_height = self.layer.grid_size

        if self.position[1] == 0:
            edges.append("top")
        if self.position[1] == layer_height - 1:
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
