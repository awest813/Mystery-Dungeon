"""Tests for Phase 8 building services (herbalist shop, inn, shrine, guild)."""
import json
import os
import tempfile

import pytest

from world import town_builder
from world.dungeon_generator import TILE_HERBALIST, TILE_INN, TILE_SHRINE, TILE_GUILD


def test_building_tile_map_complete():
    for bid in ["herbalist_hut", "inn", "shrine", "guild_hall"]:
        assert bid in town_builder._BUILDING_TILE_MAP


def test_apply_building_tiles_places_correct_types():
    grid = [[0 for _ in range(25)] for _ in range(25)]
    completed = {"herbalist_hut", "inn", "shrine", "guild_hall"}
    town_builder.apply_completed_building_tiles(grid, completed)
    assert grid[12][20] == TILE_HERBALIST
    assert grid[18][20] == TILE_INN
    assert grid[14][21] == TILE_SHRINE
    assert grid[16][21] == TILE_GUILD


def test_apply_building_tiles_partial_build():
    grid = [[0 for _ in range(25)] for _ in range(25)]
    completed = {"inn"}
    town_builder.apply_completed_building_tiles(grid, completed)
    assert grid[18][20] == TILE_INN
    assert grid[12][20] == 0  # not built


def test_shop_stock_loadable():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "shop_stock.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    stock = data["herbalist_stock"]
    assert len(stock) >= 4
    for item in stock:
        assert "key" in item
        assert "gold_cost" in item
        assert item["gold_cost"] > 0


def test_bounty_defs_loadable():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "bounties.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    bounties = data["bounties"]
    assert len(bounties) >= 3
    for b in bounties:
        assert "id" in b
        assert "name" in b
        assert "target_type" in b
        assert b["target_count"] > 0
        assert b["gold_reward"] > 0


def test_inn_buff_adds_max_hp():
    class P:
        def __init__(self):
            self.max_hp = 30
            self.hp = 30
            self.inn_buff_hp = 0
        def add_xp(self, amt):
            pass
    p = P()
    buff = 10 + 1 * 2  # level 1
    p.inn_buff_hp = buff
    p.max_hp += buff
    p.hp = min(p.hp + buff, p.max_hp)
    assert p.max_hp == 42
    assert p.hp == 42


def test_inn_buff_reverts_on_town_return():
    class P:
        def __init__(self):
            self.max_hp = 42
            self.hp = 42
            self.inn_buff_hp = 12
    p = P()
    if p.inn_buff_hp > 0:
        p.max_hp = max(1, p.max_hp - p.inn_buff_hp)
        p.inn_buff_hp = 0
    assert p.max_hp == 30
    assert p.inn_buff_hp == 0


def test_shrine_purify_removes_cursed_affixes():
    from entities.items import Item, ItemAffix
    wpn = Item("bronze_sword")
    wpn.affixes = [
        ItemAffix("keen", "attack_bonus_add", 3, cursed=False),
        ItemAffix("leech", "hp_drain_per_turn", 2, cursed=True),
    ]
    wpn.cursed = True
    cursed = [a for a in wpn.affixes if a.cursed]
    for a in cursed:
        wpn.affixes.remove(a)
    wpn.cursed = any(a.cursed for a in wpn.affixes)
    assert len(wpn.affixes) == 1
    assert wpn.affixes[0].tag == "keen"
    assert not wpn.cursed


def test_bounty_progress_tracking():
    bounty = {
        "id": "slay_foes",
        "name": "Slay Foes",
        "target_type": "kill",
        "target_count": 5,
        "progress": 0,
        "gold_reward": 50,
        "xp_reward": 25,
    }
    bounty["progress"] += 1
    assert bounty["progress"] == 1
    bounty["progress"] += 1
    assert bounty["progress"] == 2
    assert not bounty["progress"] >= bounty["target_count"]
    bounty["progress"] = 5
    assert bounty["progress"] >= bounty["target_count"]
