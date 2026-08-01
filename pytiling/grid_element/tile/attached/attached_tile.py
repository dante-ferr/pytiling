from typing import TYPE_CHECKING, Optional
from ..tile import Tile
from ....utils.direction import Direction, direction_vectors, opposite_directions

if TYPE_CHECKING:
    from ....layer.grid_layer import GridLayer
    from ....grid_map import GridMap


class AttachedTile(Tile):
    """A tile that must stay 4-adjacent to a "master" tile type living on a
    sibling layer (e.g. a spike trap attached to a platform).

    The tile's display is derived from its orientation, which points away from
    the master: a spike on top of a floor platform points "top". When several
    masters are adjacent, the first match in ``orientation_priority`` wins.

    Default atlas layout (per direction the tile points):
      - top:    (0, 0)
      - right:  (1, 0)
      - left:   (0, 1)
      - bottom: (1, 1)
    """

    DEFAULT_ORIENTATION_DISPLAYS: dict[Direction, tuple[int, int]] = {
        "top": (0, 0),
        "right": (1, 0),
        "left": (0, 1),
        "bottom": (1, 1),
    }
    DEFAULT_ORIENTATION_PRIORITY: tuple[Direction, ...] = (
        "top",
        "right",
        "left",
        "bottom",
    )

    def __init__(
        self,
        position: tuple[int, int],
        master_name: str,
        name: str = "",
        orientation_displays: "dict[Direction, tuple[int, int]] | None" = None,
        orientation_priority: "tuple[Direction, ...] | None" = None,
        display: tuple[int, int] = (0, 0),
    ):
        super().__init__(position, display, name)
        self.master_name = master_name
        self.orientation_displays = (
            dict(orientation_displays)
            if orientation_displays is not None
            else dict(self.DEFAULT_ORIENTATION_DISPLAYS)
        )
        self.orientation_priority = (
            tuple(orientation_priority)
            if orientation_priority is not None
            else self.DEFAULT_ORIENTATION_PRIORITY
        )

    @classmethod
    def find_master_orientation(
        cls,
        position: tuple[int, int],
        grid_map: "GridMap",
        master_name: str,
        orientation_priority: "tuple[Direction, ...] | None" = None,
    ) -> Optional[Direction]:
        """Orientation (direction pointing away from the master) for an attached
        tile at ``position``, or None when no master tile is 4-adjacent.

        Also None when ``position`` itself is occupied by a master tile:
        attached tiles live next to their master, never inside it."""
        priority = orientation_priority or cls.DEFAULT_ORIENTATION_PRIORITY
        x, y = position
        for layer in grid_map.layers:
            element = layer.get_element_at(position)
            if element is not None and element.name == master_name:
                return None
        for orientation in priority:
            master_direction = opposite_directions[orientation]
            dx, dy = direction_vectors[master_direction]
            master_position = (x + dx, y + dy)
            for layer in grid_map.layers:
                element = layer.get_element_at(master_position)
                if element is not None and element.name == master_name:
                    return orientation
        return None

    def master_orientation(self, layer: "GridLayer | None" = None) -> Optional[Direction]:
        """Resolve this tile's orientation against its layer's grid map. ``layer``
        can be passed when the tile is not part of a layer yet (pre-add check)."""
        layer = layer or self.layer
        if layer is None:
            return None
        return self.find_master_orientation(
            self.position, layer.grid_map, self.master_name, self.orientation_priority
        )

    def format(self):
        """Reorient the display towards the current master. Returns True if the display changed."""
        previous_display = self.display

        orientation = self.master_orientation()
        if orientation is not None:
            self.set_display(self.orientation_displays[orientation])

        super().format()

        return previous_display != self.display

    def to_dict(self):
        data = super().to_dict()
        data.update(
            {
                "master_name": self.master_name,
                "orientation_displays": {
                    direction: list(display)
                    for direction, display in self.orientation_displays.items()
                },
                "orientation_priority": list(self.orientation_priority),
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AttachedTile":
        orientation_displays = data.get("orientation_displays")
        orientation_priority = data.get("orientation_priority")
        tile = cls(
            position=tuple(data["position"]),
            master_name=data["master_name"],
            name=data["name"],
            orientation_displays=(
                {
                    direction: tuple(display)
                    for direction, display in orientation_displays.items()
                }
                if orientation_displays is not None
                else None
            ),
            orientation_priority=(
                tuple(orientation_priority)
                if orientation_priority is not None
                else None
            ),
            display=tuple(data.get("display", (0, 0))),
        )
        tile._from_dict_data(data)
        return tile
