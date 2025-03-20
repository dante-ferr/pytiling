from ..layer.tilemap_layer import TilemapLayer
import math
from typing import Literal, Callable
from pytiling.grid_element.tile import Tile
from typing import TypedDict
from ..layer.tilemap_layer import TilemapLayerNeighborProcessor
from blinker import Signal


def order_pos(positions: tuple[tuple[int, int], tuple[int, int]]):
    return (
        (
            min(positions[0][0], positions[1][0]),
            min(positions[0][1], positions[1][1]),
        ),
        (
            max(positions[0][0], positions[1][0]),
            max(positions[0][1], positions[1][1]),
        ),
    )


class Line:
    def __init__(
        self,
        positions: tuple[tuple[int, int], tuple[int, int]],
        orientation: Literal["horizontal", "vertical"],
    ):
        self.start, self.end = order_pos(positions)
        self.orientation = orientation

    @property
    def length(self):
        return math.sqrt(
            (self.end[0] - self.start[0]) ** 2 + (self.end[1] - self.start[1]) ** 2
        )


class Lines(TypedDict):
    horizontal: Line | None
    vertical: Line | None


class Node:
    lines: Lines

    def __init__(self):
        self.lines = {
            "horizontal": None,
            "vertical": None,
        }

    def add_line(self, line: Line):
        self.lines[line.orientation] = line


class TilemapBorderTracer:
    """Tool that can be used to trace the borders of a tilemap layer. This can be useful in plenty of situations, such as creating collision detection or pathfinding."""

    def __init__(self, tilemap_layer: TilemapLayer):
        self.tilemap_layer = tilemap_layer
        self.nodes: dict[tuple[int, int], Node] = {}
        self.lines: set[Line] = set()

        self.neighbor_processor = TilemapLayerNeighborProcessor(
            tilemap_layer, same_autotile_object=True, adjancecy_rule="four"
        )

        self.events: dict[str, Signal] = {
            "tile_created": Signal(),
        }

        tilemap_layer.events["element_created"].connect(
            self._handle_create_tile, weak=True
        )

    def _handle_create_tile(self, sender, tile: Tile):
        """Executed when a tile is added. This function will check if the tile is a border tile and if it is, it will create lines in the tilemap border."""
        neighbors = self.neighbor_processor.get_neighbors_bool_grid(tile)
        if tile.position is None:
            return

        def handle_neighbor(
            pos: tuple[int, int],
            contact_line: tuple[tuple[int, int], tuple[int, int]],
            orientation: Literal["horizontal", "vertical"],
        ):
            pos = (
                pos[0] + 1 - x,
                pos[1] + 1 - y,
            )
            contact_x, contact_y = contact_line

            if neighbors[pos[1], pos[0]]:
                self._split_line((contact_x, contact_y), orientation)
            else:
                self._process_border((contact_x, contact_y), orientation)

        x, y = tile.position
        handle_neighbor((x + 1, y), ((x + 1, y), (x + 1, y + 1)), "vertical")
        handle_neighbor((x, y - 1), ((x, y), (x + 1, y)), "horizontal")
        handle_neighbor((x - 1, y), ((x, y), (x, y + 1)), "vertical")
        handle_neighbor((x, y + 1), ((x, y + 1), (x + 1, y + 1)), "horizontal")

        self.events["tile_created"].send(tile=tile)

    def _process_border(
        self,
        positions: tuple[tuple[int, int], tuple[int, int]],
        orientation: Literal["horizontal", "vertical"],
    ):
        """Process a border (line between a tile and a empty space in the tilemap). If there are no nodes here, they will be created. If there are nodes here, they will be linked by a line."""
        pos = order_pos(positions)
        node_1, node_2 = (self.nodes.get(pos[0]), self.nodes.get(pos[1]))
        line_1, line_2 = (
            node_1.lines[orientation] if node_1 else None,
            node_2.lines[orientation] if node_2 else None,
        )

        if not node_1:
            node_1 = Node()
            self.nodes[pos[0]] = node_1
        if not node_2:
            node_2 = Node()
            self.nodes[pos[1]] = node_2

        if line_1 and line_2:
            if line_1 != line_2:
                self._merge_lines(line_1, line_2)
        elif line_1:
            node_2.add_line(line_1)
            self._extend_line(line_1, pos[1])
        elif line_2:
            node_1.add_line(line_2)
            self._extend_line(line_2, pos[0])
        else:
            line = Line((pos[0], pos[1]), orientation=orientation)
            self.nodes[pos[0]].add_line(line)
            self.nodes[pos[1]].add_line(line)
            self.lines.add(line)

    def _split_line(
        self,
        positions: tuple[tuple[int, int], tuple[int, int]],
        orientation: Literal["horizontal", "vertical"],
    ):
        """Split a line if it links the nodes of the given border."""
        pos = order_pos(positions)
        node_1, node_2 = (self.nodes.get(pos[0]), self.nodes.get(pos[1]))
        if node_1 is None or node_2 is None:
            raise ValueError("Nodes must exist for split.")
        line_1, line_2 = (
            node_1.lines[orientation],
            node_2.lines[orientation],
        )
        if line_1 is None or line_2 is None:
            raise ValueError("Lines must exist for split.")

        if line_1 == line_2:
            line = line_1
            self._remove_line(line)
            new_line_1 = Line(
                (line.start, pos[0]),
                orientation=orientation,
            )
            new_line_2 = Line(
                (pos[1], line.end),
                orientation=orientation,
            )

            self._add_line(new_line_1)
            self._add_line(new_line_2)

    def _merge_lines(self, *lines):
        """Merge different adjacent lines."""
        if len(lines) == 1:
            return

        largest_line = max(lines, key=lambda line: line.length)
        largest_line.start = (
            min(lines, key=lambda line: line.start[0]).start[0],
            min(lines, key=lambda line: line.start[1]).start[1],
        )
        largest_line.end = (
            max(lines, key=lambda line: line.end[0]).end[0],
            max(lines, key=lambda line: line.end[1]).end[1],
        )

        for line in lines:
            if line == largest_line:
                continue
            self._remove_line(line)

        self._add_line(largest_line)

    def _extend_line(self, line: Line, pos: tuple[int, int]):
        """Extend a line to a new position."""
        if line.orientation == "vertical":
            if pos[0] != line.start[0]:
                raise ValueError(
                    "Position must be on the same vertical axis as the line."
                )
        elif line.orientation == "horizontal":
            if pos[1] != line.start[1]:
                raise ValueError(
                    "Position must be on the same horizontal axis as the line."
                )

        line.start = (
            min(pos[0], line.start[0]),
            min(pos[1], line.start[1]),
        )
        line.end = (
            max(pos[0], line.end[0]),
            max(pos[1], line.end[1]),
        )

    def _remove_line(self, line: Line):
        """Remove a line from the tilemap border, as well as its reference in the nodes that lay on its positions."""
        for x in range(line.start[0], line.end[0] + 1):
            for y in range(line.start[1], line.end[1] + 1):
                self.nodes[(x, y)].lines[line.orientation] = None
        self.lines.remove(line)

    def _add_line(self, line: Line):
        """Add a line from the tilemap border and its reference in the nodes that lay on its positions."""
        if line.length == 0:
            return

        for x in range(line.start[0], line.end[0] + 1):
            for y in range(line.start[1], line.end[1] + 1):
                self.nodes[(x, y)].lines[line.orientation] = line
        self.lines.add(line)
