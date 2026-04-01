"""Tests for Phase 14 – synergy, ecology, progression, risk/reward, equipment."""
import pytest

from systems.synergy_engine import (
    SynergyEngine, STATUS_COMBOS, AFFIX_SYNERGIES, TEAM_COMBOS, SKILL_CHAINS, ActiveSynergy
)
from systems.dungeon_ecology import DungeonEcology, ECOLOGY_DATA, EcologyState
from systems.progression_tracker import ProgressionTracker, PROGRESSION_TREE, ProgressNode
from systems.risk_reward import RiskRewardSystem, FLOOR_MODIFIERS, RISK_CHOICES
from systems.equipment_slots import EquipmentSlots, EQUIPMENT_SETS, ARMOR_DEFS, ACCESSORY_DEFS


# -- Synergy Engine --

def test_status_combo_burn_poison():
    class Target:
        burn = True
        poisoned = True
        paralyzed = False
        confused = False
        asleep = False
        frozen = False
    engine = SynergyEngine()
    combos = engine.check_status_combos(Target())
    assert len(combos) > 0
    assert any(c.name == "Withering" for c in combos)

def test_status_combo_no_match():
    class Target:
        burn = True
        poisoned = False
        paralyzed = False
        confused = False
        asleep = False
        frozen = False
    engine = SynergyEngine()
    combos = engine.check_status_combos(Target())
    assert len(combos) == 0

def test_skill_chain_ember_thunder():
    engine = SynergyEngine()
    engine.check_skill_chain("Ember")
    chain = engine.check_skill_chain("Thunder")
    assert chain is not None
    assert chain.name == "Storm Blast"

def test_skill_chain_no_match():
    engine = SynergyEngine()
    engine.check_skill_chain("Slash")
    chain = engine.check_skill_chain("Heal")
    assert chain is None

def test_synergy_damage_application():
    class Target:
        pass
    engine = SynergyEngine()
    engine.active_synergies.append(ActiveSynergy("test", "Test", "bonus_dmg", 10, "test"))
    dmg, msgs = engine.apply_synergy_effects(None, Target(), 5)
    assert dmg == 15
    assert len(msgs) > 0

def test_synergy_tick_expires():
    engine = SynergyEngine()
    # Skill chain synergies are temporary (turns_remaining=1)
    engine.active_synergies.append(ActiveSynergy("ember_then_thunder", "Storm Blast", "bonus_dmg", 10, "test", turns_remaining=1))
    engine.tick()
    # After tick, turns_remaining=0 but it's not a status/affix/team combo, so it expires
    assert len(engine.active_synergies) == 0

def test_all_status_combos_defined():
    for cid, combo in STATUS_COMBOS.items():
        assert "statuses" in combo
        assert "name" in combo
        assert "effect" in combo
        assert "value" in combo

def test_all_affix_synergies_defined():
    for sid, syn in AFFIX_SYNERGIES.items():
        assert "affixes" in syn
        assert "name" in syn
        assert "effect" in syn

def test_all_team_combos_defined():
    for cid, combo in TEAM_COMBOS.items():
        assert "members" in combo
        assert "name" in combo
        assert "effect" in combo

def test_all_skill_chains_defined():
    for cid, chain in SKILL_CHAINS.items():
        assert "sequence" in chain
        assert len(chain["sequence"]) == 2
        assert "name" in chain


# -- Dungeon Ecology --

def test_ecology_data_complete():
    for etype, data in ECOLOGY_DATA.items():
        assert "diet" in data
        assert "fears" in data
        assert "hunts" in data
        assert "pack_size" in data
        assert "aggression" in data

def test_ecology_fear_update():
    state = EcologyState("e1", "slime")
    state.update_fear(["orc"], [])
    assert state.fear_level > 0.0

def test_ecology_fear_with_allies():
    state = EcologyState("e1", "slime")
    state.update_fear(["orc"], ["slime", "slime"])
    assert state.fear_level < 0.3  # Pack courage reduces fear

def test_ecology_hunger_drives_hunting():
    state = EcologyState("e1", "bat")
    for _ in range(10):
        state.update_hunger()
    assert state.is_hunting

def test_ecology_feed_resets_hunger():
    state = EcologyState("e1", "bat")
    for _ in range(10):
        state.update_hunger()
    state.feed()
    assert state.hunger_level == 0.0
    assert not state.is_hunting

def test_ecology_register_unregister():
    eco = DungeonEcology()
    class FakeEnemy:
        def __init__(self):
            self.enemy_type = "slime"
            self.x = 5
            self.y = 5
            self.is_dead = False
    e = FakeEnemy()
    state = eco.register_enemy(e)
    assert state.enemy_type == "slime"
    eco.unregister_enemy(e)
    assert id(e) not in eco.ecology_states


# -- Progression Tracker --

def test_progression_initial_state():
    p = ProgressionTracker()
    assert p.total_xp == 0
    assert "combat_basics" in p.unlocked_nodes

def test_progression_unlock_from_xp():
    p = ProgressionTracker()
    p.add_xp(200)
    assert "status_expert" in p.unlocked_nodes

def test_progression_chained_unlock():
    # Reset module-level state first
    for node in PROGRESSION_TREE.values():
        node.is_unlocked = node.id == "combat_basics"
    p = ProgressionTracker()
    p.add_xp(500)
    # synergy_master requires status_expert (200xp) which requires combat_basics (0xp)
    assert "synergy_master" in p.unlocked_nodes

def test_progression_building_discount():
    for node in PROGRESSION_TREE.values():
        node.is_unlocked = node.id == "combat_basics"
    p = ProgressionTracker()
    p.add_xp(300)
    assert "town_hero" in p.unlocked_nodes
    assert p.get_building_discount() == 0.8
    p.add_xp(300)
    assert p.get_building_discount() == 0.6

def test_progression_to_dict_roundtrip():
    for node in PROGRESSION_TREE.values():
        node.is_unlocked = node.id == "combat_basics"
    p = ProgressionTracker()
    p.add_xp(500)
    p.add_town_rep(50)
    d = p.to_dict()
    p2 = ProgressionTracker.from_dict(d)
    assert p2.total_xp == 500
    assert p2.town_reputation == 50
    assert "status_expert" in p2.unlocked_nodes


# -- Risk & Reward --

def test_risk_roll_below_floor_5():
    rr = RiskRewardSystem()
    assert rr.roll_floor_modifier(3) is None

def test_risk_roll_above_floor_5():
    rr = RiskRewardSystem()
    found = False
    for _ in range(100):
        if rr.roll_floor_modifier(10):
            found = True
            break
    assert found

def test_risk_event_roll():
    rr = RiskRewardSystem()
    found = False
    for _ in range(100):
        if rr.roll_risk_event(10):
            found = True
            break
    assert found

def test_risk_apply_choice():
    class Player:
        def __init__(self):
            self.hp = 30
            self.max_hp = 30
            self.gold = 100
            self.inventory = []
            self.gold_bonus_pct = 0
        def add_gold(self, amt):
            self.gold += amt
    rr = RiskRewardSystem()
    rr.pending_choice = {
        "name": "Cursed Altar",
        "description": "Test",
        "choices": [
            {"label": "Accept", "description": "Test", "effects": {"max_hp_pct": -20, "gold_mult": 150}},
            {"label": "Defy", "description": "Test", "effects": {}},
            {"label": "Bless", "description": "Test", "effects": {"max_hp_pct": 20, "gold_cost": 50}},
        ],
    }
    p = Player()
    msgs = rr.apply_choice(0, p)
    assert p.max_hp < 30
    assert len(msgs) > 0

def test_all_floor_modifiers_defined():
    for fid, mod in FLOOR_MODIFIERS.items():
        assert mod.name
        assert mod.description
        assert mod.positive_effects is not None
        assert mod.negative_effects is not None

def test_all_risk_choices_defined():
    for rid, choice in RISK_CHOICES.items():
        assert choice["name"]
        assert len(choice["choices"]) >= 2


# -- Equipment Slots --

def test_equip_armor():
    eq = EquipmentSlots()
    class Armor:
        key = "leather_armor"
        defense = 2
    eq.equip_armor(Armor())
    assert eq.get_defense() == 2

def test_equip_accessory():
    eq = EquipmentSlots()
    class Accessory:
        key = "power_ring"
        stat = "attack_power"
        value = 2
    eq.equip_accessory(Accessory())
    bonuses = eq.get_stat_bonuses()
    assert bonuses.get("attack_power") == 2

def test_set_bonus_2_piece():
    eq = EquipmentSlots()
    class Weapon:
        key = "iron_blade"
    class Armor:
        key = "chain_mail"
        defense = 4
    class Accessory:
        key = "power_ring"
        stat = "attack_power"
        value = 2
    
    eq.equip_armor(Armor())
    eq.equip_accessory(Accessory())
    eq.update_weapon_key("iron_blade")
    
    info = eq.get_active_set_info()
    assert info is not None
    assert info["matching"] >= 2

def test_all_equipment_sets_defined():
    for sid, sdef in EQUIPMENT_SETS.items():
        assert sdef["name"]
        assert "weapon" in sdef["items"]
        assert "armor" in sdef["items"]
        assert "accessory" in sdef["items"]
        assert "bonus_2" in sdef

def test_all_armor_defined():
    for aid, adef in ARMOR_DEFS.items():
        assert adef["defense"] > 0
        assert adef["rarity"] in ("common", "uncommon", "rare", "legendary")

def test_all_accessories_defined():
    for aid, adef in ACCESSORY_DEFS.items():
        assert adef["stat"]
        assert adef["value"] > 0
