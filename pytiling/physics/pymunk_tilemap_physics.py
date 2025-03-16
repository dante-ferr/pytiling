from ..tools.tilemap_border_tracer import TilemapBorderTracer
import pymunk


class PymunkTilemapPhysics:
    lines: list[pymunk.Segment]

    def __init__(self, border_tracer: TilemapBorderTracer, space: pymunk.Space):
        self.border_tracer = border_tracer
        self.space = space
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.space.add(self.body)

        self.lines = []
        border_tracer.add_create_tile_callback(self.create_lines)

    def create_lines(self, tile):
        # Remove all previously added lines
        for line in self.lines:
            self.space.remove(line)
        self.lines.clear()

        # Add new lines
        layer = self.border_tracer.tilemap_layer

        for line in self.border_tracer.lines:
            x1, y1 = line.start
            x2, y2 = line.end
            start = layer.grid_pos_to_actual_pos((x1, y1 - 1))
            end = layer.grid_pos_to_actual_pos((x2, y2 - 1))

            physics_line = pymunk.Segment(self.body, start, end, radius=2)
            physics_line.collision_type = 2
            physics_line.friction = 1
            self.space.add(physics_line)

            self.lines.append(physics_line)
