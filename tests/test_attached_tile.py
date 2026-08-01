"""Tests for AttachedTile: master-adjacent placement, orientation, orphan cleanup."""

import unittest
from pathlib import Path

from pytiling import AttachedTile, Tilemap, TilemapLayer, Tileset
from pytiling.serialization import element_from_dict

ASSETS = Path(__file__).resolve().parents[2] / "assets" / "img" / "tilesets" / "dungeon"


def _make_tilemap() -> Tilemap:
    tilemap = Tilemap((16, 16), (10, 10), (1, 1), (64, 64))
    tilemap.add_layer(TilemapLayer("platforms", Tileset(str(ASSETS / "platforms.png"))))
    tilemap.add_layer(TilemapLayer("traps", Tileset(str(ASSETS / "spike_trap.png"))))
    return tilemap


def _platform(tilemap: Tilemap, position: tuple[int, int]):
    return tilemap.get_layer("platforms").create_autotile_tile_at(position, "platform")


def _spike(tilemap: Tilemap, position: tuple[int, int], **args):
    return tilemap.get_layer("traps").create_attached_tile_at(
        position, "platform", "spike_trap", **args
    )


class TestAttachedTilePlacement(unittest.TestCase):
    def test_placement_rejected_without_adjacent_master(self):
        tilemap = _make_tilemap()
        self.assertIsNone(_spike(tilemap, (5, 5)))
        self.assertEqual(tilemap.get_layer("traps").tiles, [])

    def test_placement_rejected_with_only_diagonal_master(self):
        tilemap = _make_tilemap()
        _platform(tilemap, (6, 6))
        self.assertIsNone(_spike(tilemap, (5, 5)))

    def test_placement_rejected_inside_master(self):
        tilemap = _make_tilemap()
        _platform(tilemap, (5, 5))
        _platform(tilemap, (5, 4))  # adjacent master exists, but cell is a master
        self.assertIsNone(_spike(tilemap, (5, 5)))
        self.assertEqual(len(tilemap.get_layer("traps").tiles), 0)

    def test_orientation_display_for_each_master_direction(self):
        # (spike position, master position, expected display)
        cases = [
            ((5, 4), (5, 5), (0, 0)),  # master below -> points top
            ((5, 6), (5, 5), (1, 1)),  # master above -> points bottom
            ((4, 5), (5, 5), (0, 1)),  # master right -> points left
            ((6, 5), (5, 5), (1, 0)),  # master left -> points right
        ]
        for spike_pos, master_pos, expected in cases:
            with self.subTest(spike=spike_pos, master=master_pos):
                tilemap = _make_tilemap()
                _platform(tilemap, master_pos)
                spike = _spike(tilemap, spike_pos, apply_formatting=True)
                self.assertIsNotNone(spike, f"spike at {spike_pos} rejected")
                self.assertEqual(spike.display, expected)

    def test_orientation_priority_prefers_top_with_multiple_masters(self):
        tilemap = _make_tilemap()
        _platform(tilemap, (5, 5))  # floor below
        _platform(tilemap, (6, 4))  # wall right
        spike = _spike(tilemap, (5, 4), apply_formatting=True)
        self.assertIsNotNone(spike)
        self.assertEqual(spike.display, (0, 0))


class TestAttachedTileMaintenance(unittest.TestCase):
    def test_orphan_spike_removed_with_master(self):
        tilemap = _make_tilemap()
        platform = _platform(tilemap, (5, 5))
        _spike(tilemap, (5, 4), apply_formatting=True)
        _spike(tilemap, (4, 5), apply_formatting=True)
        self.assertEqual(len(tilemap.get_layer("traps").tiles), 2)

        tilemap.get_layer("platforms").remove_tile(platform)
        self.assertEqual(tilemap.get_layer("traps").tiles, [])

    def test_spike_reorients_when_master_setup_changes(self):
        tilemap = _make_tilemap()
        floor = _platform(tilemap, (5, 5))
        _platform(tilemap, (6, 4))  # wall right of the spike
        spike = _spike(tilemap, (5, 4), apply_formatting=True)
        self.assertEqual(spike.display, (0, 0))

        # Floor removed, wall remains -> reorients to point left.
        tilemap.get_layer("platforms").remove_tile(floor)
        self.assertEqual(tilemap.get_layer("traps").tiles, [spike])
        self.assertEqual(spike.display, (0, 1))

    def test_spike_buried_by_new_master_is_removed(self):
        tilemap = _make_tilemap()
        _platform(tilemap, (5, 5))
        _spike(tilemap, (5, 4), apply_formatting=True)

        _platform(tilemap, (5, 4))
        self.assertEqual(tilemap.get_layer("traps").tiles, [])

    def test_format_all_tiles_orients_unformatted_spike(self):
        tilemap = _make_tilemap()
        _platform(tilemap, (5, 5))
        spike = _spike(tilemap, (4, 5))
        self.assertIsNotNone(spike)

        tilemap.format_all_tiles()
        self.assertEqual(spike.display, (0, 1))


class TestAttachedTileSerialization(unittest.TestCase):
    def test_round_trip(self):
        tilemap = _make_tilemap()
        _platform(tilemap, (5, 5))
        spike = _spike(tilemap, (5, 4), apply_formatting=True)

        data = spike.to_dict()
        self.assertEqual(data["__class__"], "AttachedTile")
        self.assertEqual(data["master_name"], "platform")

        restored = element_from_dict(data)
        self.assertIsInstance(restored, AttachedTile)
        self.assertEqual(restored.position, spike.position)
        self.assertEqual(restored.name, "spike_trap")
        self.assertEqual(restored.master_name, "platform")
        self.assertEqual(restored.display, spike.display)


if __name__ == "__main__":
    unittest.main()
