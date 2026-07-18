"""Tests for multi-tile grid element footprints."""

from pytiling import GridElement, GridLayer, GridMap, footprint_positions, top_left_position


def _make_map(width: int = 8, height: int = 8) -> GridMap:
    return GridMap((16, 16), (width, height), (1, 1), (64, 64))


def _make_layer(width: int = 8, height: int = 8, name: str = "test") -> GridLayer:
    grid_map = _make_map(width, height)
    layer = GridLayer(name)
    grid_map.add_layer(layer)
    return layer


def test_footprint_bottom_left_anchor():
    assert footprint_positions((5, 10), (1, 1)) == [(5, 10)]
    assert footprint_positions((5, 10), (1, 3)) == [(5, 8), (5, 9), (5, 10)]
    assert footprint_positions((2, 4), (2, 2)) == [(2, 3), (3, 3), (2, 4), (3, 4)]
    assert top_left_position((5, 10), (1, 3)) == (5, 8)


def test_add_element_claims_full_footprint():
    layer = _make_layer()
    element = GridElement((4, 5), name="delver", size=(1, 3))
    assert layer.add_element(element)

    assert layer.get_element_at((4, 5)) is element
    assert layer.get_element_at((4, 4)) is element
    assert layer.get_element_at((4, 3)) is element
    assert layer.get_element_at((4, 2)) is None
    assert layer.elements == [element]


def test_remove_from_any_footprint_cell():
    layer = _make_layer()
    element = GridElement((4, 5), name="delver", size=(1, 3))
    layer.add_element(element)

    removed = layer.remove_element_at((4, 3))
    assert removed is element
    assert layer.get_element_at((4, 5)) is None
    assert layer.get_element_at((4, 4)) is None
    assert layer.get_element_at((4, 3)) is None
    assert layer.elements == []


def test_unique_replacement_clears_previous_footprint():
    layer = _make_layer()
    first = GridElement((2, 5), name="delver", unique=True, size=(1, 3))
    second = GridElement((6, 5), name="delver", unique=True, size=(1, 3))
    layer.add_element(first)
    layer.add_element(second)

    assert layer.get_element_at((2, 5)) is None
    assert layer.get_element_at((2, 3)) is None
    assert layer.get_element_at((6, 5)) is second
    assert layer.elements == [second]


def test_concurrent_layers_clear_intersecting_footprints():
    grid_map = _make_map()
    platforms = GridLayer("platforms")
    essentials = GridLayer("essentials")
    grid_map.add_layer(platforms)
    grid_map.add_layer(essentials)
    platforms.add_concurrent_layer(essentials)
    essentials.add_concurrent_layer(platforms)

    platform = GridElement((4, 4), name="platform")
    platforms.add_element(platform)

    delver = GridElement((4, 5), name="delver", size=(1, 3))
    essentials.add_element(delver)

    assert platforms.get_element_at((4, 4)) is None
    assert essentials.get_element_at((4, 4)) is delver


def test_serialization_includes_size():
    element = GridElement((1, 2), name="goal", unique=True, size=(2, 2))
    data = element.to_dict()
    assert data["size"] == [2, 2]

    restored = GridElement((0, 0), name="")
    restored._from_dict_data(data)
    assert restored.size == (2, 2)
