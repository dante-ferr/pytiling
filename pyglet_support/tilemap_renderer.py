import pyglet
from typing import TYPE_CHECKING
from ..tools.tilemap_border_tracer import TilemapBorderTracer
from ..tilemap import Tilemap
from .layer_renderer import LayerRenderer
from .tileset_image import TilesetImage

if TYPE_CHECKING:
    from tileset.tileset import Tileset


class PygletTilemapRenderer:
    """A helper object that can be used to render a tilemap using pyglet."""

    def __init__(self, tilemap: Tilemap):
        self.tilemap = tilemap

        self.layer_batches = {}
        self.tileset_images: dict["Tileset", TilesetImage] = {}

        self.debug_batch = pyglet.graphics.Batch()
        self.debug_shapes: set[pyglet.shapes.ShapeBase] = set()

        self._create_tileset_images()
        self._create_layer_renderers()

    def _create_tileset_images(self):
        """Create a dictionary of numpy 2d arrays of tileset images. Each array corresponds to a tileset."""
        self.tileset_images_dict = {}

        for tileset in self.tilemap.tilesets:
            if tileset is None:
                raise ValueError("Tileset is not set for layer.")
            self.tileset_images[tileset] = TilesetImage(tileset)

    def _create_layer_renderers(self):
        self.layer_renderers: dict[str, LayerRenderer] = {}

        for layer in self.tilemap.layers:
            layer_renderer = LayerRenderer(layer, self.tileset_images[layer.tileset])
            self.layer_renderers[layer.name] = layer_renderer

    def update_debug_lines(self, border_tracer: TilemapBorderTracer):
        """Creates a vertex list for lines in the Pyglet batch."""
        layer = border_tracer.tilemap_layer
        self.debug_shapes = set()

        for line in border_tracer.lines:
            x1, y1 = line.start
            x2, y2 = line.end

            x1, y1 = layer.grid_pos_to_actual_pos((x1, y1 - 1))
            x2, y2 = layer.grid_pos_to_actual_pos((x2, y2 - 1))

            if line.orientation == "vertical":
                color = (255, 0, 0)
            else:
                color = (0, 255, 0)

            line_display = pyglet.shapes.Line(
                x1,
                y1,
                x2,
                y2,
                thickness=1,
                color=color,
                batch=self.debug_batch,
            )
            self.debug_shapes.add(line_display)

            circle = pyglet.shapes.Circle(
                x=x1 + (2 if line.orientation == "vertical" else -2),
                y=y1,
                radius=3,
                color=color,
                batch=self.debug_batch,
            )
            self.debug_shapes.add(circle)
            circle = pyglet.shapes.Circle(
                x=x2 + (2 if line.orientation == "vertical" else -2),
                y=y2,
                radius=3,
                color=color,
                batch=self.debug_batch,
            )
            self.debug_shapes.add(circle)

    def render_all_layers(self):
        """Draw all layers of the tilemap according to their order. So the first layer is drawn first, etc."""
        for layer in self.tilemap.layers:
            self.render_layer(layer.name)

    def render_layer(self, layer_name: str):
        """Draw a layer of the tilemap."""
        layer_renderer = self.layer_renderers[layer_name]
        layer_renderer.render()

    def render_debug(self):
        """Draw debug content."""
        self.debug_batch.draw()
