import numpy as np
from typing import Any, Callable
from .direction import Direction


def expand_grid_towards(
    grid: np.ndarray,
    direction: Direction,
    fill_callback: Callable[[tuple[int, int]], Any],
    size=1,
) -> np.ndarray:
    """
    Expand the grid in the specified direction using a callback function for filling values.

    Parameters:
        grid: The input grid.
        direction: The direction to expand ("left", "right", "top", "bottom").
        size: The number of rows/columns to add.
        fill_callback: A callback function that generates the value to fill the new rows/columns.
                        It should accept two arguments: row index and column index.

    Returns:
        np.ndarray: The expanded grid.
    """

    def _create_new_grid(
        pad_width: tuple[tuple[int, int], tuple[int, int]],
        grid=grid,
        fill_callback=fill_callback,
        size=size,
    ) -> np.ndarray:
        new_grid = np.pad(grid, pad_width, mode="constant", constant_values=0)

        for i in range(new_grid.shape[0]):
            for j in range(size):
                new_grid[i, j] = fill_callback((i, j))

        return new_grid

    if direction == "left":
        return _create_new_grid(((0, 0), (size, 0)))
    elif direction == "right":
        return _create_new_grid(((0, 0), (0, size)))
    elif direction == "top":  # Should add rows at the end
        return _create_new_grid(((0, size), (0, 0)))
    elif direction == "bottom":  # Should add rows at the beginning
        return _create_new_grid(((size, 0), (0, 0)))
    # elif direction == "top":
    #     return _create_new_grid(((size, 0), (0, 0)))
    # elif direction == "bottom":
    #     return _create_new_grid(((0, size), (0, 0)))


def reduce_grid_towards(grid: np.ndarray, direction: Direction, size=1):
    """
    Reduce the grid in the specified direction.

    Parameters:
        grid: The input grid.
        direction: The direction to reduce ("left", "right", "top", "bottom").
        size: The number of rows/columns to remove.

    Returns:
        np.ndarray: The reduced grid.
    """
    if direction == "left":
        return grid[:, size:]
    elif direction == "right":
        return grid[:, :-size]
    elif direction == "top":
        return grid[size:, :]
    elif direction == "bottom":
        return grid[:-size, :]
