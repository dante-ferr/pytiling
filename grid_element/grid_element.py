from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from layer import GridLayer


class GridElement:
    def __init__(self, position: tuple[int, int]):
        self.position = position

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
    def layer(self):
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
