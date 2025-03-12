from typing import TYPE_CHECKING, Callable
from pyglet.window import mouse

if TYPE_CHECKING:
    from .layer_renderer import LayerRenderer
    from tile.tile import Tile


def create_tile_on_click(
    layer_renderer: "LayerRenderer",
    create_tile_callback: Callable[[int, int], "Tile"],
):
    """Create a callback function that can be used to create a tile on click. The output callback must be pushed as a handle of the pyglet window. It takes the grid coordinates of the tile and returns a tile. The tile will be added to the layer and the sprite will be drawn. The callback must be called from the main thread."""

    def on_mouse_press(x, y, button, modifiers):
        if button == mouse.LEFT:
            grid_x, grid_y = layer_renderer.layer.actual_pos_to_grid_pos((x, y))
            tile = create_tile_callback(grid_x, grid_y)
            # tile.set_position((grid_x, grid_y))
            layer_renderer.layer.add_tile(tile)

    return on_mouse_press
