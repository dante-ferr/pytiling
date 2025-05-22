from typing import Literal

Direction = Literal["left", "right", "top", "bottom"]
direction_vectors = {
    "left": (-1, 0),
    "right": (1, 0),
    "top": (0, -1),
    "bottom": (0, 1),
}
opposite_directions: dict[Direction, Direction] = {
    "left": "right",
    "right": "left",
    "top": "bottom",
    "bottom": "top",
}
