"""Tests for Phase 12 – monster collecting, capture, and evolution."""
import pytest

from entities.monster_roster import CapturedMonster, MonsterRoster, load_evolutions
from systems.capture_system import calculate_capture_chance, attempt_capture


# -- Evolution Data --

def test_load_evolutions():
    evos = load_evolutions()
    assert len(evos) == 5

def test_evolution_slime_has_item_req():
    evos = load_evolutions()
    slime = [e for e in evos if e["base_type"] == "slime"][0]
    assert slime["evolved_type"] == "king_slime"
    assert slime["level_req"] == 10
    assert slime["item_req"] == "slime_crown"

def test_evolution_ghost_no_item_req():
    evos = load_evolutions()
    ghost = [e for e in evos if e["base_type"] == "ghost"][0]
    assert ghost["evolved_type"] == "wraith"
    assert ghost["item_req"] is None


# -- CapturedMonster --

def test_captured_monster_init():
    m = CapturedMonster("m1", "slime", "Slimy")
    assert m.name == "Slimy"
    assert m.monster_type == "slime"
    assert m.level == 1
    assert m.hp == 10

def test_monster_add_xp_levels_up():
    m = CapturedMonster("m1", "slime")
    assert not m.add_xp(5)
    assert m.level == 1
    assert m.add_xp(5)
    assert m.level == 2
    assert m.max_hp == 12
    assert m.attack_power == 3

def test_monster_heal_full():
    m = CapturedMonster("m1", "slime")
    m.hp = 1
    m.is_dead = True
    m.heal_full()
    assert m.hp == m.max_hp
    assert not m.is_dead

def test_monster_check_evolution_not_ready():
    m = CapturedMonster("m1", "slime")
    assert m.check_evolution([]) is None

def test_monster_check_evolution_ready():
    m = CapturedMonster("m1", "slime")
    m.level = 10
    assert m.check_evolution(["slime_crown"]) is not None

def test_monster_check_evolution_no_item():
    m = CapturedMonster("m1", "slime")
    m.level = 10
    assert m.check_evolution([]) is None

def test_monster_evolve_applies_bonuses():
    m = CapturedMonster("m1", "slime")
    m.level = 10
    ev = m.check_evolution(["slime_crown"])
    assert ev is not None
    old_hp = m.max_hp
    m.evolve(ev)
    assert m.monster_type == "king_slime"
    assert m.max_hp > old_hp
    assert m.attack_power > 2

def test_monster_evolve_no_item_ghost():
    m = CapturedMonster("m1", "ghost")
    m.level = 15
    ev = m.check_evolution([])
    assert ev is not None
    m.evolve(ev)
    assert m.monster_type == "wraith"

def test_monster_to_dict_roundtrip():
    m = CapturedMonster("m1", "slime")
    m.level = 5
    m.max_hp = 20
    d = m.to_dict()
    m2 = CapturedMonster.from_dict(d)
    assert m2.monster_type == "slime"
    assert m2.level == 5
    assert m2.max_hp == 20


# -- MonsterRoster --

def test_roster_add_monster():
    r = MonsterRoster(max_size=2)
    m1 = CapturedMonster("m1", "slime")
    m2 = CapturedMonster("m2", "bat")
    assert r.add_monster(m1)
    assert r.add_monster(m2)
    assert len(r.monsters) == 2

def test_roster_max_size():
    r = MonsterRoster(max_size=1)
    m1 = CapturedMonster("m1", "slime")
    m2 = CapturedMonster("m2", "bat")
    assert r.add_monster(m1)
    assert not r.add_monster(m2)

def test_roster_remove_monster():
    r = MonsterRoster()
    m1 = CapturedMonster("m1", "slime")
    m2 = CapturedMonster("m2", "bat")
    r.add_monster(m1)
    r.add_monster(m2)
    r.remove_monster("m1")
    assert len(r.monsters) == 1
    assert r.monsters[0].id == "m2"

def test_roster_deployed_vs_ranch():
    r = MonsterRoster()
    m1 = CapturedMonster("m1", "slime")
    m2 = CapturedMonster("m2", "bat")
    m1.is_deployed = True
    r.add_monster(m1)
    r.add_monster(m2)
    assert len(r.get_deployed()) == 1
    assert len(r.get_ranch_monsters()) == 1

def test_roster_to_dict_roundtrip():
    r = MonsterRoster()
    m = CapturedMonster("m1", "slime")
    m.level = 5
    r.add_monster(m)
    r.ranch_inventory["slime_gel"] = 3
    d = r.to_dict()
    r2 = MonsterRoster.from_dict(d)
    assert len(r2.monsters) == 1
    assert r2.monsters[0].level == 5
    assert r2.ranch_inventory["slime_gel"] == 3


# -- Capture System --

class FakeEnemy:
    def __init__(self, hp, max_hp, xp_value, is_boss=False):
        self.hp = hp
        self.max_hp = max_hp
        self.xp_value = xp_value
        self.is_boss = is_boss

class FakePlayer:
    def __init__(self, level):
        self.level = level

def test_capture_boss_impossible():
    e = FakeEnemy(2, 20, 10, is_boss=True)
    p = FakePlayer(10)
    assert calculate_capture_chance(e, p) == 0.0

def test_capture_above_25hp_zero_chance():
    e = FakeEnemy(6, 20, 5)
    p = FakePlayer(5)
    assert calculate_capture_chance(e, p) == 0.0

def test_capture_at_low_hp_positive_chance():
    e = FakeEnemy(4, 20, 5)
    p = FakePlayer(5)
    assert calculate_capture_chance(e, p) > 0.0

def test_capture_friend_orb_boosts_chance():
    e = FakeEnemy(4, 20, 5)
    p = FakePlayer(5)
    base = calculate_capture_chance(e, p)
    boosted = calculate_capture_chance(e, p, friend_orb_active=True)
    assert boosted > base

def test_capture_higher_player_level_boosts():
    e = FakeEnemy(4, 20, 2)
    p_low = FakePlayer(2)
    p_high = FakePlayer(10)
    assert calculate_capture_chance(e, p_high) > calculate_capture_chance(e, p_low)
