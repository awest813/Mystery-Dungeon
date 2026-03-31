"""Tests for Phase 8 town building (data/buildings.json + town_builder)."""
import json
import os
import tempfile

import pytest

from world import town_builder


@pytest.fixture
def sample_buildings_path():
    data = {
        "buildings": [
            {
                "id": "a",
                "name": "Building A",
                "description": "First",
                "requires": [],
                "materials": {"iron_ore": 2},
                "gold": 0,
            },
            {
                "id": "b",
                "name": "Building B",
                "description": "Second",
                "requires": ["a"],
                "materials": {"slime_gel": 1},
                "gold": 10,
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    yield path
    os.unlink(path)


def test_load_building_definitions(sample_buildings_path):
    defs = town_builder.load_building_definitions(sample_buildings_path)
    assert len(defs) == 2
    assert defs[0].id == "a"
    assert defs[1].requires == ("a",)


def test_can_build_requires_prereq(sample_buildings_path):
    defs = town_builder.load_building_definitions(sample_buildings_path)
    b_b = defs[1]

    class P:
        def __init__(self):
            self.materials = {"slime_gel": 5}
            self.gold = 100

        def has_materials(self, d):
            return all(self.materials.get(k, 0) >= v for k, v in d.items())

    player = P()
    completed = set()
    ok, reason = town_builder.can_build(b_b, player, completed)
    assert not ok
    assert "Requires" in reason or "first" in reason.lower() or "other" in reason.lower()

    completed.add("a")
    ok, _ = town_builder.can_build(b_b, player, completed)
    assert ok


def test_try_build_spends_and_registers(sample_buildings_path):
    defs = town_builder.load_building_definitions(sample_buildings_path)
    b_a = defs[0]

    class P:
        def __init__(self):
            self.materials = {"iron_ore": 5}
            self.gold = 0

        def has_materials(self, d):
            return all(self.materials.get(k, 0) >= v for k, v in d.items())

        def spend_materials(self, d):
            if not self.has_materials(d):
                return False
            for k, v in d.items():
                self.materials[k] -= v
            return True

    player = P()
    completed = set()
    ok, msg = town_builder.try_build(b_a, player, completed)
    assert ok
    assert "a" in completed
    assert player.materials["iron_ore"] == 3
    assert "Built" in msg


def test_apply_completed_building_tiles_opens_cells():
    grid = [[0 for _ in range(25)] for _ in range(25)]
    completed = {"herbalist_hut"}
    town_builder.apply_completed_building_tiles(grid, completed)
    assert grid[12][20] == 1  # TILE_FLOOR
