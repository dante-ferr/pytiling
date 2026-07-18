from typing import TYPE_CHECKING, Iterable
from pytiling.utils import Direction

if TYPE_CHECKING:
    from layer import GridLayer


def footprint_positions(
    position: tuple[int, int], size: tuple[int, int] = (1, 1)
) -> list[tuple[int, int]]:
    """Return all grid cells occupied by an element.

    ``position`` is the bottom-left cell of the footprint (Y increases downward).
    A size of ``(w, h)`` occupies ``x..x+w-1`` and ``y-(h-1)..y``.
    """
    x, y = position
    width, height = size
    if width < 1 or height < 1:
        raise ValueError(f"Element size must be at least (1, 1), got {size}.")
    top_y = y - (height - 1)
    return [(x + dx, top_y + dy) for dy in range(height) for dx in range(width)]


def top_left_position(
    position: tuple[int, int], size: tuple[int, int] = (1, 1)
) -> tuple[int, int]:
    """Return the top-left cell of a bottom-left–anchored footprint."""
    width, height = size
    if width < 1 or height < 1:
        raise ValueError(f"Element size must be at least (1, 1), got {size}.")
    return (position[0], position[1] - (height - 1))


class GridElement:
    def __init__(
        self,
        position: tuple[int, int],
        name: str = "",
        unique: bool = False,
        size: tuple[int, int] = (1, 1),
    ):
        self.position = position
        self.name = name
        self.unique = unique
        self.size = (int(size[0]), int(size[1]))
        if self.size[0] < 1 or self.size[1] < 1:
            raise ValueError(f"Element size must be at least (1, 1), got {size}.")

        self.locked = False

        self._layer: "GridLayer | None" = None

    def to_dict(self):
        """Serialize the grid element to a dictionary."""
        return {
            "__class__": self.__class__.__name__,
            "position": self.position,
            "name": self.name,
            "unique": self.unique,
            "locked": self.locked,
            "size": list(self.size),
        }

    def _from_dict_data(self, data: dict):
        """Helper to populate grid element from a dictionary."""
        self.locked = data.get("locked", False)
        self.unique = data.get("unique", False)
        raw_size = data.get("size", (1, 1))
        self.size = (int(raw_size[0]), int(raw_size[1]))

    def remove(self):
        """Remove the element from its layer."""
        if self.layer is None:
            raise ValueError("Element is not in a layer to be removed.")
        self.layer.remove_element(self)

    def set_position(self, position: tuple[int, int]):
        """Set the element's position."""
        self.position = position

    def footprint_positions(self) -> list[tuple[int, int]]:
        """Cells occupied by this element (bottom-left anchored)."""
        return footprint_positions(self.position, self.size)

    def top_left_position(self) -> tuple[int, int]:
        """Top-left cell of this element's footprint."""
        return top_left_position(self.position, self.size)

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


def unique_elements(elements: Iterable["GridElement | None"]) -> list["GridElement"]:
    """Deduplicate elements by identity while preserving first-seen order."""
    seen: set[int] = set()
    result: list[GridElement] = []
    for element in elements:
        if element is None:
            continue
        element_id = id(element)
        if element_id in seen:
            continue
        seen.add(element_id)
        result.append(element)
    return result
