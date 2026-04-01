"""Tests for Phase 13 – endless dungeon, NG+, and final boss."""
import pytest

from systems.endless_dungeon import EndlessDungeon, ActiveEvent, LEGENDARY_EVENTS
from systems.new_game_plus import NGPlusState, prepare_ngp, apply_ngp


# -- Endless Dungeon --

def test_endless_difficulty_scale_floor_1():
    ed = EndlessDungeon()
    assert ed.get_floor_difficulty_scale(1) == 1.0

def test_endless_difficulty_scale_floor_20():
    ed = EndlessDungeon()
    assert ed.get_floor_difficulty_scale(20) == 1.0

def test_endless_difficulty_scale_floor_30():
    ed = EndlessDungeon()
    assert ed.get_floor_difficulty_scale(30) > 1.0

def test_endless_no_event_below_floor_20():
    ed = EndlessDungeon()
    assert ed.roll_legendary_event(15) is None

def test_endless_event_above_floor_20():
    ed = EndlessDungeon()
    events = []
    for _ in range(200):
        e = ed.roll_legendary_event(25)
        if e:
            events.append(e)
    assert len(events) > 0

def test_endless_event_ticks_down():
    ed = EndlessDungeon()
    event = ActiveEvent("test", "Test Event", "gold_bonus", 50, 2)
    ed.active_events.append(event)
    assert event.remaining_floors == 2
    ed.advance_floor(21)
    assert event.remaining_floors == 1
    ed.advance_floor(21)
    assert len(ed.active_events) == 0

def test_endless_gold_multiplier():
    ed = EndlessDungeon()
    ed.active_events.append(ActiveEvent("golden", "Golden", "gold_bonus", 100, 1))
    assert ed.get_gold_multiplier() == 2.0

def test_endless_vision_radius():
    ed = EndlessDungeon()
    assert ed.get_vision_radius() is None
    ed.active_events.append(ActiveEvent("dark", "Darkness", "reduced_vision", 3, 1))
    assert ed.get_vision_radius() == 3

def test_endless_score_calculation():
    ed = EndlessDungeon()
    score = ed.calculate_score(25, 500, 10)
    assert score == (25 * 100) + (500 // 2) + (10 * 10)

def test_endless_high_score_update():
    ed = EndlessDungeon()
    assert ed.update_high_score(100)
    assert ed.high_score == 100
    assert not ed.update_high_score(50)
    assert ed.update_high_score(200)
    assert ed.high_score == 200

def test_endless_to_dict_roundtrip():
    ed = EndlessDungeon()
    ed.high_score = 500
    ed.active_events.append(ActiveEvent("blizzard", "Blizzard", "enemy_atk_bonus", 20, 2))
    d = ed.to_dict()
    ed2 = EndlessDungeon.from_dict(d)
    assert ed2.high_score == 500
    assert len(ed2.active_events) == 1
    assert ed2.active_events[0].remaining_floors == 2


# -- NG+ --

def test_ngp_state_defaults():
    state = NGPlusState()
    assert state.ngp_level == 0
    assert state.dungeon_difficulty_mult == 1.0

def test_ngp_next_difficulty():
    state = NGPlusState(ngp_level=2)
    assert state.next_difficulty() == 1.5

def test_ngp_to_dict_roundtrip():
    state = NGPlusState(
        ngp_level=1,
        carried_over_materials={"iron_ore": 10},
        carried_over_monsters=[{"id": "m1"}],
    )
    d = state.to_dict()
    state2 = NGPlusState.from_dict(d)
    assert state2.ngp_level == 1
    assert state2.carried_over_materials["iron_ore"] == 10


# -- Final Boss Data --

def test_final_boss_data_loadable():
    from entities.boss import load_final_boss_data
    data = load_final_boss_data()
    assert data is not None
    assert data["name"] == "The Abyssal King"
    assert len(data["phases"]) == 3
    assert data["phases"][0]["max_hp"] == 150
    assert data["phases"][2]["attack_power"] == 25
