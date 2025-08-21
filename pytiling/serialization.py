import json
from typing import TYPE_CHECKING, cast, Callable

if TYPE_CHECKING:
    from .grid_map import GridMap
    from .layer import GridLayer
    from .tileset import Tileset
    from .grid_element import GridElement


ELEMENT_DESERIALIZERS: dict[str, Callable[[dict], "GridElement"]] = {}
LAYER_DESERIALIZERS: dict[str, Callable[[dict, dict[str, "Tileset"]], "GridLayer"]] = {}
MAP_DESERIALIZERS: dict[str, Callable[[dict], "GridMap"]] = {}


def register_element_deserializer(
    class_name: str, deserializer: Callable[[dict], "GridElement"]
):
    """Register a deserializer function for a GridElement subclass."""
    ELEMENT_DESERIALIZERS[class_name] = deserializer


def register_layer_deserializer(
    class_name: str,
    deserializer: Callable[[dict, dict[str, "Tileset"]], "GridLayer"],
):
    """Register a deserializer function for a GridLayer subclass."""
    LAYER_DESERIALIZERS[class_name] = deserializer


def register_map_deserializer(
    class_name: str, deserializer: Callable[[dict], "GridMap"]
):
    """Register a deserializer function for a GridMap subclass."""
    MAP_DESERIALIZERS[class_name] = deserializer


def element_from_dict(data: dict):
    """Deserialize a grid element from a dictionary."""
    class_name = data["__class__"]
    deserializer = ELEMENT_DESERIALIZERS.get(class_name)
    if deserializer:
        return deserializer(data)
    raise ValueError(f"Unknown or unregistered element class: {class_name}")


def layer_from_dict(data: dict, tilesets: dict[str, "Tileset"]) -> "GridLayer":
    """Deserialize a layer from a dictionary."""
    class_name = data["__class__"]
    deserializer = LAYER_DESERIALIZERS.get(class_name)
    if deserializer:
        return deserializer(data, tilesets)
    raise ValueError(f"Unknown or unregistered layer class: {class_name}")


def map_from_dict(data: dict) -> "GridMap":
    """Deserialize a map from a dictionary."""
    class_name = data["__class__"]
    deserializer = MAP_DESERIALIZERS.get(class_name)
    if deserializer:
        return deserializer(data)
    raise ValueError(f"Unknown or unregistered map class: {class_name}")


# Internal deserializers for pytiling base classes


def _initialize_pytiling_deserializers():
    """Registers the deserializers for the core pytiling classes."""

    def _deserialize_tile(data):
        from .grid_element.tile import Tile

        return Tile.from_dict(data)

    def _deserialize_autotile_tile(data):
        from .grid_element.tile.autotile import AutotileTile

        return AutotileTile.from_dict(data)

    def _deserialize_grid_layer(data, tilesets):
        from .layer import GridLayer

        return GridLayer(name=data["name"])

    def _deserialize_tilemap_layer(data, tilesets):
        from .layer.tilemap_layer import TilemapLayer
        from .tileset import Tileset

        tileset_path = data["tileset"]
        if tileset_path not in tilesets:
            tilesets[tileset_path] = Tileset(tileset_path)
        tileset = tilesets[tileset_path]
        return TilemapLayer(name=data["name"], tileset=tileset)

    def _deserialize_grid_map(data):
        from .grid_map import GridMap

        return GridMap.from_dict(data)

    def _deserialize_tilemap(data):
        from .tilemap import Tilemap

        return Tilemap.from_dict(data)

    register_element_deserializer("Tile", _deserialize_tile)
    register_element_deserializer("AutotileTile", _deserialize_autotile_tile)
    register_layer_deserializer("GridLayer", _deserialize_grid_layer)
    register_layer_deserializer("TilemapLayer", _deserialize_tilemap_layer)
    register_map_deserializer("GridMap", _deserialize_grid_map)
    register_map_deserializer("Tilemap", _deserialize_tilemap)


def load_map(filepath: str) -> "GridMap":
    """Load a map from a JSON file."""
    with open(filepath, "r") as f:
        data = json.load(f)
    return map_from_dict(data)


def save_map(grid_map: "GridMap", filepath: str):
    """Save a map to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(grid_map.to_dict(), f, indent=2)


_initialize_pytiling_deserializers()
