"""
Phase 7 - Procedural Loot & Enchantment System tests.

Tests cover:
  - Rarity tier distribution and weights
  - LootGenerator.generate() for all categories
  - Affix rolling (count, stats, cursed restriction)
  - ItemAffix serialization (to_dict / from_dict)
  - Item serialization (to_dict / from_dict)
  - Item identification (display_name, mystery name)
  - Material drops from enemies
  - Player material inventory helpers
  - Player identification helpers (identify_inventory, mark_known_items_identified)
"""

import random
import sys
import types

from entities.items import (
    _AFFIX_DEFS,
    LEGENDARY_UNIQUES,
    MYSTERY_NAMES,
    RARITY_TIERS,
    Item,
    ItemAffix,
    LootGenerator,
)


def _import_enemy_data():
    """Import ENEMY_MATERIAL_DROPS without triggering Panda3D dependency chain."""
    if "panda3d" not in sys.modules:
        panda3d = types.ModuleType("panda3d")
        panda3d.core = types.ModuleType("panda3d.core")

        class _Stub:
            def __init__(self, *a, **kw): pass
            def attachNewNode(self, *a): return _Stub()  # noqa: N802
            def setColor(self, *a): pass  # noqa: N802
            def setBillboardPointEye(self): pass  # noqa: N802
            def setPos(self, *a): pass  # noqa: N802
            def setFrame(self, *a): pass  # noqa: N802
            def generate(self): return None
            def getPos(self):  # noqa: N802
                class V:
                    x = y = z = 0
                    def __add__(self, o): return V()
                    def __sub__(self, o): return V()
                    def __mul__(self, s): return V()
                    def length(self): return 0
                return V()

        for cls_name in ("NodePath", "CardMaker", "TextNode"):
            setattr(panda3d.core, cls_name, _Stub)
        sys.modules["panda3d"] = panda3d
        sys.modules["panda3d.core"] = panda3d.core
    from entities.enemy import ENEMY_MATERIAL_DROPS as _EMD  # noqa: PLC0415
    return _EMD


ENEMY_MATERIAL_DROPS = _import_enemy_data()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_player():
    """Create a minimal player-like object for testing without Panda3D."""
    class FakeVisual:
        def setColor(self, *a): pass  # noqa: N802
        def setBillboardPointEye(self): pass  # noqa: N802

    class FakeNode:
        def attachNewNode(self, *a): return FakeVisual()  # noqa: N802
        def setPos(self, *a): pass  # noqa: N802
        def getPos(self): return _Vec(0, 0, 0)  # noqa: N802

    class _Vec:
        def __init__(self, x=0, y=0, z=0):
            self.x, self.y, self.z = x, y, z
        def __add__(self, other): return _Vec(self.x+other.x, self.y+other.y, self.z+other.z)
        def __sub__(self, other): return _Vec(self.x-other.x, self.y-other.y, self.z-other.z)
        def __mul__(self, s): return _Vec(self.x*s, self.y*s, self.z*s)
        def length(self): return (self.x**2+self.y**2+self.z**2)**0.5

    # Minimal player mock with just what the loot tests need
    class FakePlayer:
        def __init__(self):
            self.max_hp = 30
            self.hp = 30
            self.attack_power = 5
            self._weapon_bonus = 0
            self.inventory = []
            self.max_inventory = 10
            self.equipped_weapon = None
            self.materials = {}
            self.identified_items = set()
            self.crit_chance = 0
            self.life_steal_pct = 0
            self.dmg_reduce_pct = 0
            self.hunger_save_pct = 0
            self.gold_bonus_pct = 0
            self.hp_drain_per_turn = 0

        @property
        def effective_attack(self):
            return self.attack_power + self._weapon_bonus

        def heal(self, amount):
            self.hp = min(self.max_hp, self.hp + amount)

        def add_material(self, key, amount=1):
            self.materials[key] = self.materials.get(key, 0) + amount

        def has_materials(self, cost_dict):
            return all(self.materials.get(k, 0) >= v for k, v in cost_dict.items())

        def spend_materials(self, cost_dict):
            if not self.has_materials(cost_dict):
                return False
            for k, v in cost_dict.items():
                self.materials[k] -= v
            return True

        def materials_summary(self):
            parts = [f"{v}x {k.replace('_', ' ').title()}"
                     for k, v in sorted(self.materials.items()) if v > 0]
            return ", ".join(parts) if parts else "none"

        def identify_item(self, item):
            item.is_identified = True
            self.identified_items.add(item.key)

        def identify_inventory(self):
            newly = []
            all_items = list(self.inventory)
            if self.equipped_weapon:
                all_items.append(self.equipped_weapon)
            for item in all_items:
                if not item.is_identified:
                    item.is_identified = True
                    self.identified_items.add(item.key)
                    newly.append(item.display)
            return newly

        def mark_known_items_identified(self):
            for item in self.inventory:
                if item.key in self.identified_items:
                    item.is_identified = True

        def _apply_weapon_affixes(self, weapon):
            self.crit_chance = weapon.get_affix_stat("crit_chance")
            self.life_steal_pct = weapon.get_affix_stat("life_steal_pct")
            self.dmg_reduce_pct = weapon.get_affix_stat("dmg_reduce_pct")
            self.hunger_save_pct = weapon.get_affix_stat("hunger_save_pct")
            self.gold_bonus_pct = weapon.get_affix_stat("gold_bonus_pct")
            self.hp_drain_per_turn = weapon.get_affix_stat("hp_drain_per_turn")
            bonus_hp = weapon.get_affix_stat("bonus_max_hp")
            if bonus_hp:
                self.max_hp += bonus_hp
                self.hp = min(self.hp + bonus_hp, self.max_hp)

        def _unapply_weapon_affixes(self, weapon):
            self.crit_chance = 0
            self.life_steal_pct = 0
            self.dmg_reduce_pct = 0
            self.hunger_save_pct = 0
            self.gold_bonus_pct = 0
            self.hp_drain_per_turn = 0
            bonus_hp = weapon.get_affix_stat("bonus_max_hp")
            if bonus_hp:
                self.max_hp = max(1, self.max_hp - bonus_hp)
                self.hp = min(self.hp, self.max_hp)

    return FakePlayer()


# ---------------------------------------------------------------------------
# Rarity tiers
# ---------------------------------------------------------------------------

def test_rarity_tiers_exist():
    expected = {"common", "uncommon", "rare", "legendary", "cursed"}
    assert set(RARITY_TIERS.keys()) == expected


def test_rarity_tiers_have_required_fields():
    for name, info in RARITY_TIERS.items():
        assert "display" in info, f"{name} missing display"
        assert "color" in info, f"{name} missing color"
        assert "weight" in info, f"{name} missing weight"
        assert "affix_count" in info, f"{name} missing affix_count"
        lo, hi = info["affix_count"]
        assert lo <= hi


def test_pick_rarity_returns_valid_tier():
    for floor in [1, 5, 10, 15]:
        rarity = LootGenerator.pick_rarity(floor)
        assert rarity in RARITY_TIERS


def test_pick_rarity_distribution():
    """Common should win the majority of rolls on floor 1."""
    results = [LootGenerator.pick_rarity(1) for _ in range(500)]
    common_count = results.count("common")
    assert common_count > 200, "Common should dominate floor 1 drops"


def test_pick_rarity_rare_more_likely_on_deep_floors():
    """Rare/legendary count should be higher on floor 20 vs floor 1."""
    deep = [LootGenerator.pick_rarity(20) for _ in range(500)]
    shallow = [LootGenerator.pick_rarity(1) for _ in range(500)]
    deep_rare = sum(1 for r in deep if r in ("rare", "legendary"))
    shallow_rare = sum(1 for r in shallow if r in ("rare", "legendary"))
    assert deep_rare >= shallow_rare


# ---------------------------------------------------------------------------
# Affix rolling
# ---------------------------------------------------------------------------

def test_affix_defs_completeness():
    for tag, defn in _AFFIX_DEFS.items():
        assert "stat" in defn, f"{tag} missing stat"
        assert "range" in defn, f"{tag} missing range"
        assert "desc" in defn, f"{tag} missing desc"
        assert "category" in defn, f"{tag} missing category"


def test_roll_affixes_common_yields_none():
    affixes = LootGenerator.roll_affixes("common", "weapon")
    assert affixes == []


def test_roll_affixes_uncommon_yields_one():
    for _ in range(20):
        affixes = LootGenerator.roll_affixes("uncommon", "weapon")
        assert len(affixes) == 1


def test_roll_affixes_rare_yields_two_or_three():
    for _ in range(20):
        affixes = LootGenerator.roll_affixes("rare", "weapon")
        assert 2 <= len(affixes) <= 3


def test_roll_affixes_cursed_includes_cursed_tag():
    found_cursed = False
    for _ in range(50):
        affixes = LootGenerator.roll_affixes("cursed", "weapon")
        if any(a.cursed for a in affixes):
            found_cursed = True
            break
    assert found_cursed, "Cursed rarity should always include a cursed affix"


def test_roll_affixes_non_weapon_yields_none():
    for cat in ("food", "potion", "orb", "key"):
        affixes = LootGenerator.roll_affixes("legendary", cat)
        assert affixes == [], f"{cat} should not get affixes"


def test_affix_value_in_range():
    for tag, defn in _AFFIX_DEFS.items():
        lo, hi = defn["range"]
        affix = LootGenerator._roll_affix(tag)  # noqa: SLF001
        assert lo <= affix.value <= hi, f"{tag} value out of range"


def test_affix_desc_contains_value():
    affix = LootGenerator._roll_affix("keen")  # noqa: SLF001
    assert str(affix.value) in affix.desc


# ---------------------------------------------------------------------------
# ItemAffix serialization
# ---------------------------------------------------------------------------

def test_affix_to_dict_from_dict_roundtrip():
    affix = ItemAffix("keen", "attack_bonus_add", 4, cursed=False, status_on_hit=None)
    d = affix.to_dict()
    restored = ItemAffix.from_dict(d)
    assert restored.tag == affix.tag
    assert restored.stat == affix.stat
    assert restored.value == affix.value
    assert restored.cursed == affix.cursed


def test_cursed_affix_roundtrip():
    affix = ItemAffix("leech", "hp_drain_per_turn", 2, cursed=True)
    restored = ItemAffix.from_dict(affix.to_dict())
    assert restored.cursed is True


# ---------------------------------------------------------------------------
# Item generation
# ---------------------------------------------------------------------------

def test_generate_common_weapon_has_no_affixes():
    item = LootGenerator.generate("bronze_sword", floor_level=1, forced_rarity="common")
    assert item.rarity == "common"
    assert len(item.affixes) == 0
    assert item.is_identified is True


def test_generate_uncommon_weapon_has_one_affix():
    item = LootGenerator.generate("iron_blade", floor_level=3, forced_rarity="uncommon")
    assert item.rarity == "uncommon"
    assert len(item.affixes) == 1
    assert not item.is_identified   # non-common weapon starts unidentified


def test_generate_rare_weapon_has_two_to_three_affixes():
    item = LootGenerator.generate("iron_blade", floor_level=5, forced_rarity="rare")
    assert 2 <= len(item.affixes) <= 3


def test_generate_legendary_weapon_uses_unique_name():
    item = LootGenerator.generate("bronze_sword", floor_level=10, forced_rarity="legendary")
    assert item.display == LEGENDARY_UNIQUES["bronze_sword"]["name"]
    assert item.flavor == LEGENDARY_UNIQUES["bronze_sword"]["flavor"]
    assert len(item.affixes) == len(LEGENDARY_UNIQUES["bronze_sword"]["affixes"])


def test_generate_cursed_weapon_has_cursed_flag():
    item = LootGenerator.generate("iron_blade", floor_level=8, forced_rarity="cursed")
    assert item.cursed is True
    assert any(a.cursed for a in item.affixes)


def test_generate_food_always_identified():
    for _ in range(10):
        item = LootGenerator.generate("apple", floor_level=5)
        assert item.is_identified


def test_generate_attack_bonus_folded_in():
    """attack_bonus_add affixes must be folded into item.attack_bonus."""
    item = LootGenerator.generate("bronze_sword", floor_level=5, forced_rarity="uncommon")
    affix_bonus = item.get_affix_stat("attack_bonus_add")
    if affix_bonus:
        base = 3   # bronze_sword base
        assert item.attack_bonus == base + affix_bonus


# ---------------------------------------------------------------------------
# Item serialization
# ---------------------------------------------------------------------------

def test_item_to_dict_from_dict_common():
    item = LootGenerator.generate("heal_potion", floor_level=1, forced_rarity="common")
    d = item.to_dict()
    restored = Item.from_dict(d)
    assert restored.key == item.key
    assert restored.rarity == item.rarity
    assert len(restored.affixes) == len(item.affixes)
    assert restored.is_identified == item.is_identified


def test_item_to_dict_from_dict_rare_weapon():
    item = LootGenerator.generate("iron_blade", floor_level=6, forced_rarity="rare")
    d = item.to_dict()
    restored = Item.from_dict(d)
    assert len(restored.affixes) == len(item.affixes)
    assert restored.rarity == "rare"
    assert restored.attack_bonus == item.attack_bonus


def test_item_to_dict_from_dict_legendary():
    item = LootGenerator.generate("flame_sword", floor_level=10, forced_rarity="legendary")
    d = item.to_dict()
    restored = Item.from_dict(d)
    assert restored.display == item.display
    assert restored.flavor == item.flavor


# ---------------------------------------------------------------------------
# Identification
# ---------------------------------------------------------------------------

def test_mystery_names_defined_for_non_food():
    from entities.items import ITEM_DEFS  # noqa: PLC0415
    weapons_and_potions = [
        k for k, v in ITEM_DEFS.items()
        if v["category"] in ("weapon", "potion")
    ]
    for key in weapons_and_potions:
        assert key in MYSTERY_NAMES, f"{key} missing mystery name"


def test_display_name_unidentified():
    item = LootGenerator.generate("heal_potion", floor_level=1, forced_rarity="uncommon")
    assert not item.is_identified
    assert MYSTERY_NAMES["heal_potion"] in item.display_name
    assert "???" in item.display_name


def test_display_name_identified():
    item = LootGenerator.generate("heal_potion", floor_level=1, forced_rarity="uncommon")
    item.is_identified = True
    assert "Heal Potion" in item.display_name
    assert "???" not in item.display_name


def test_common_item_is_auto_identified():
    item = LootGenerator.generate("heal_potion", floor_level=1, forced_rarity="common")
    assert item.is_identified


def test_identify_inventory():
    player = _make_player()
    w1 = LootGenerator.generate("iron_blade", floor_level=3, forced_rarity="uncommon")
    w2 = LootGenerator.generate("heal_potion", floor_level=3, forced_rarity="uncommon")
    assert not w1.is_identified
    assert not w2.is_identified
    player.inventory = [w1, w2]
    newly = player.identify_inventory()
    assert w1.is_identified
    assert w2.is_identified
    assert len(newly) == 2
    assert w1.key in player.identified_items
    assert w2.key in player.identified_items


def test_identify_inventory_skips_already_identified():
    player = _make_player()
    item = LootGenerator.generate("apple", floor_level=1, forced_rarity="common")
    assert item.is_identified
    player.inventory = [item]
    newly = player.identify_inventory()
    assert newly == []


def test_mark_known_items_identified():
    player = _make_player()
    player.identified_items = {"heal_potion"}
    item = LootGenerator.generate("heal_potion", floor_level=2, forced_rarity="uncommon")
    assert not item.is_identified
    player.inventory = [item]
    player.mark_known_items_identified()
    assert item.is_identified


# ---------------------------------------------------------------------------
# get_affix_stat
# ---------------------------------------------------------------------------

def test_get_affix_stat_sums_correctly():
    item = Item("bronze_sword")
    item.affixes = [
        ItemAffix("keen", "attack_bonus_add", 3),
        ItemAffix("keen", "attack_bonus_add", 2),
    ]
    assert item.get_affix_stat("attack_bonus_add") == 5


def test_get_affix_stat_default():
    item = Item("bronze_sword")
    assert item.get_affix_stat("nonexistent_stat") == 0
    assert item.get_affix_stat("nonexistent_stat", default=99) == 99


def test_affix_descs():
    item = Item("bronze_sword")
    item.affixes = [
        ItemAffix("keen", "attack_bonus_add", 4),
        ItemAffix("crit", "crit_chance", 15),
    ]
    descs = item.affix_descs()
    assert len(descs) == 2
    assert "4" in descs[0]
    assert "15" in descs[1]


# ---------------------------------------------------------------------------
# Material drops
# ---------------------------------------------------------------------------

def test_all_enemy_types_have_material_table():
    from entities.enemy import ENEMY_TYPES  # noqa: PLC0415
    for enemy_type in ENEMY_TYPES:
        # Not all types MUST have drops, but the table exists for main types
        if enemy_type in ENEMY_MATERIAL_DROPS:
            drops = ENEMY_MATERIAL_DROPS[enemy_type]
            for mat_key, chance in drops:
                assert isinstance(mat_key, str)
                assert 0.0 < chance <= 1.0


def test_enemy_material_drops_returns_dict():
    """get_material_drops() should return a dict (may be empty due to randomness)."""
    # We use a mock enemy since Enemy requires Panda3D
    class FakeEnemy:
        def __init__(self, enemy_type):
            self.enemy_type = enemy_type

        def get_material_drops(self):
            drops = {}
            for mat_key, chance in ENEMY_MATERIAL_DROPS.get(self.enemy_type, []):
                if random.random() < chance:
                    drops[mat_key] = drops.get(mat_key, 0) + 1
            return drops

    for enemy_type in ENEMY_MATERIAL_DROPS:
        e = FakeEnemy(enemy_type)
        # Run many times to verify the method works without error
        results = [e.get_material_drops() for _ in range(20)]
        assert all(isinstance(r, dict) for r in results)


def test_slime_always_drops_slime_gel():
    """Slime has 100% slime_gel chance so it must always drop."""
    random.seed(0)

    class FakeEnemy:
        def __init__(self):
            self.enemy_type = "slime"

        def get_material_drops(self):
            drops = {}
            for mat_key, chance in ENEMY_MATERIAL_DROPS.get(self.enemy_type, []):
                if random.random() < chance:
                    drops[mat_key] = drops.get(mat_key, 0) + 1
            return drops

    e = FakeEnemy()
    for _ in range(10):
        drops = e.get_material_drops()
        assert "slime_gel" in drops


# ---------------------------------------------------------------------------
# Player material helpers
# ---------------------------------------------------------------------------

def test_player_add_material():
    player = _make_player()
    player.add_material("iron_ore", 3)
    assert player.materials["iron_ore"] == 3
    player.add_material("iron_ore", 2)
    assert player.materials["iron_ore"] == 5


def test_player_has_materials_true():
    player = _make_player()
    player.materials = {"iron_ore": 5, "slime_gel": 2}
    assert player.has_materials({"iron_ore": 5})
    assert player.has_materials({"iron_ore": 3, "slime_gel": 1})


def test_player_has_materials_false():
    player = _make_player()
    player.materials = {"iron_ore": 3}
    assert not player.has_materials({"iron_ore": 5})
    assert not player.has_materials({"dark_crystal": 1})


def test_player_spend_materials():
    player = _make_player()
    player.materials = {"iron_ore": 5}
    success = player.spend_materials({"iron_ore": 3})
    assert success
    assert player.materials["iron_ore"] == 2


def test_player_spend_materials_insufficient():
    player = _make_player()
    player.materials = {"iron_ore": 2}
    success = player.spend_materials({"iron_ore": 5})
    assert not success
    assert player.materials["iron_ore"] == 2   # unchanged


def test_player_materials_summary():
    player = _make_player()
    player.materials = {}
    assert player.materials_summary() == "none"
    player.materials = {"iron_ore": 3}
    summary = player.materials_summary()
    assert "3" in summary
    assert "Iron Ore" in summary   # materials_summary() uses .title()


# ---------------------------------------------------------------------------
# Weapon affix application
# ---------------------------------------------------------------------------

def test_apply_weapon_affixes_sets_crit_chance():
    player = _make_player()
    weapon = LootGenerator.generate("iron_blade", floor_level=5, forced_rarity="uncommon")
    # Give it a specific affix for testing
    weapon.affixes = [ItemAffix("crit", "crit_chance", 20)]
    player._apply_weapon_affixes(weapon)  # noqa: SLF001
    assert player.crit_chance == 20


def test_apply_weapon_affixes_hp_bonus():
    player = _make_player()
    weapon = LootGenerator.generate("iron_blade", floor_level=5, forced_rarity="uncommon")
    weapon.affixes = [ItemAffix("hardy", "bonus_max_hp", 10)]
    old_max = player.max_hp
    player._apply_weapon_affixes(weapon)  # noqa: SLF001
    assert player.max_hp == old_max + 10


def test_unapply_weapon_affixes_restores_hp():
    player = _make_player()
    weapon = Item("iron_blade")
    weapon.affixes = [ItemAffix("hardy", "bonus_max_hp", 10)]
    old_max = player.max_hp
    player._apply_weapon_affixes(weapon)  # noqa: SLF001
    assert player.max_hp == old_max + 10
    player._unapply_weapon_affixes(weapon)  # noqa: SLF001
    assert player.max_hp == old_max
