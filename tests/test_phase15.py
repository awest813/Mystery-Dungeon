"""Tests for Phase 15 – life sim: NPCs, home, festivals, particles."""
import pytest

from systems.npc_schedule import NPC, NPCDef, ScheduleEntry, list_npc_ids
from systems.home_system import HomeSystem, FURNITURE_DEFS, PlacedFurniture
from systems.festivals import FestivalSystem, FESTIVALS, Festival


# -- NPC Schedule --

def test_list_npc_ids():
    ids = list_npc_ids()
    assert len(ids) >= 4
    assert "mayor_elric" in ids
    assert "merchant_lina" in ids

def test_npc_load():
    npc = NPC("mayor_elric")
    assert npc.name == "Mayor Elric"
    assert npc.defn.role == "Mayor"
    assert len(npc.defn.schedule) >= 5

def test_npc_gift_preferred():
    npc = NPC("farmer_bramble")
    delta, msg = npc.gift_item("grain")
    assert delta == 10
    assert "loves" in msg

def test_npc_gift_disliked():
    npc = NPC("farmer_bramble")
    delta, msg = npc.gift_item("dark_crystal")
    assert delta == -5

def test_npc_gift_neutral():
    npc = NPC("mayor_elric")
    delta, msg = npc.gift_item("apple")
    assert delta == 3

def test_npc_gift_twice_same_day():
    npc = NPC("merchant_lina")
    npc.gift_item("honey")
    delta2, msg2 = npc.gift_item("honey")
    assert delta2 == 0
    assert "already" in msg2

def test_npc_reset_daily():
    npc = NPC("merchant_lina")
    npc.gift_item("honey")
    npc.reset_daily()
    delta, _ = npc.gift_item("honey")
    assert delta == 10

def test_npc_dialogue_by_affection():
    npc = NPC("librarian_sage")
    msg1 = npc.talk()
    npc.affection = 80
    msg2 = npc.talk("high_affection")
    assert msg1 != msg2

def test_npc_schedule_update():
    npc = NPC("mayor_elric")
    npc.update_schedule(9, "Spring")
    assert npc.current_activity == "working"
    npc.update_schedule(21, "Spring")
    assert npc.current_activity == "sleeping"

def test_npc_to_dict_roundtrip():
    npc = NPC("blacksmith_grom")
    npc.affection = 50
    npc.x = 13
    npc.y = 12
    d = npc.to_dict()
    npc2 = NPC.from_dict(d)
    assert npc2.affection == 50
    assert npc2.x == 13
    assert npc2.y == 12


# -- Home System --

def test_home_place_furniture():
    home = HomeSystem()
    assert home.place_furniture("bed", 1, 1)
    assert len(home.furniture) == 1

def test_home_place_overlap():
    home = HomeSystem()
    home.place_furniture("bed", 1, 1)
    assert not home.place_furniture("table", 1, 1)

def test_home_place_out_of_bounds():
    home = HomeSystem()
    assert not home.place_furniture("bed", 10, 10)

def test_home_remove_furniture():
    home = HomeSystem()
    home.place_furniture("bed", 1, 1)
    removed = home.remove_furniture(0)
    assert removed is not None
    assert removed.furniture_id == "bed"
    assert len(home.furniture) == 0

def test_home_storage():
    home = HomeSystem()
    home.add_to_storage({"key": "heal_potion"})
    assert len(home.storage_items) == 1
    item = home.remove_from_storage(0)
    assert item["key"] == "heal_potion"

def test_home_material_storage():
    home = HomeSystem()
    home.add_material_to_storage("iron_ore", 5)
    assert home.storage_materials["iron_ore"] == 5
    assert home.take_material_from_storage("iron_ore", 3)
    assert home.storage_materials["iron_ore"] == 2
    assert not home.take_material_from_storage("iron_ore", 5)

def test_home_to_dict_roundtrip():
    home = HomeSystem()
    home.place_furniture("bed", 1, 1)
    home.add_material_to_storage("iron_ore", 3)
    d = home.to_dict()
    home2 = HomeSystem.from_dict(d)
    assert len(home2.furniture) == 1
    assert home2.storage_materials["iron_ore"] == 3

def test_all_furniture_defs():
    for fid, fdef in FURNITURE_DEFS.items():
        assert "name" in fdef
        assert "size" in fdef
        assert "color" in fdef


# -- Festivals --

def test_festivals_defined():
    assert len(FESTIVALS) >= 6
    for f in FESTIVALS:
        assert f.name
        assert f.season in ("Spring", "Summer", "Autumn", "Winter")
        assert f.day > 0

def test_festival_check_match():
    fs = FestivalSystem()
    fest = fs.check_festival("Spring", 7)
    assert fest is not None
    assert fest.id == "spring_bloom"

def test_festival_check_no_match():
    fs = FestivalSystem()
    fest = fs.check_festival("Spring", 1)
    assert fest is None

def test_festival_complete():
    fs = FestivalSystem()
    fs.check_festival("Spring", 7)
    msgs = fs.complete_festival(100)
    assert "Spring Bloom Festival" in " ".join(msgs)
    assert fs.festival_score == 100
    assert fs.active_festival is None

def test_festival_already_completed():
    fs = FestivalSystem()
    fs.check_festival("Spring", 7)
    fs.complete_festival()
    fest = fs.check_festival("Spring", 7)
    assert fest is None

def test_festival_upcoming():
    fs = FestivalSystem()
    upcoming = fs.get_upcoming_festivals("Spring")
    assert len(upcoming) >= 1

def test_festival_to_dict_roundtrip():
    fs = FestivalSystem()
    fs.check_festival("Spring", 7)
    fs.complete_festival(50)
    d = fs.to_dict()
    fs2 = FestivalSystem.from_dict(d)
    assert fs2.festival_score == 50
    assert "spring_bloom" in fs2.completed_festivals
