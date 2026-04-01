"""
Phase 14 - Equipment Slots & Set Bonuses.

Extends the item system with armor, accessories, and set bonuses
that reward collecting matching gear.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set, Tuple

# ------------------------------------------------------------------ #
#  Armor Definitions                                                   #
# ------------------------------------------------------------------ #

ARMOR_DEFS: Dict[str, dict] = {
    "leather_armor": {
        "display": "Leather Armor",
        "defense": 2,
        "weight": 1,
        "rarity": "common",
    },
    "chain_mail": {
        "display": "Chain Mail",
        "defense": 4,
        "weight": 2,
        "rarity": "uncommon",
    },
    "plate_armor": {
        "display": "Plate Armor",
        "defense": 7,
        "weight": 3,
        "rarity": "rare",
    },
    "dragon_scale": {
        "display": "Dragon Scale",
        "defense": 10,
        "weight": 2,
        "rarity": "legendary",
    },
}

# ------------------------------------------------------------------ #
#  Accessory Definitions                                               #
# ------------------------------------------------------------------ #

ACCESSORY_DEFS: Dict[str, dict] = {
    "power_ring": {
        "display": "Power Ring",
        "stat": "attack_power",
        "value": 2,
        "rarity": "uncommon",
    },
    "vitality_amulet": {
        "display": "Vitality Amulet",
        "stat": "max_hp",
        "value": 10,
        "rarity": "uncommon",
    },
    "speed_boots": {
        "display": "Speed Boots",
        "stat": "move_speed",
        "value": 1,
        "rarity": "rare",
    },
    "lucky_charm": {
        "display": "Lucky Charm",
        "stat": "gold_bonus_pct",
        "value": 15,
        "rarity": "rare",
    },
    "warding_stone": {
        "display": "Warding Stone",
        "stat": "status_resist",
        "value": 1,
        "rarity": "rare",
    },
    "abyssal_crown": {
        "display": "Abyssal Crown",
        "stat": "all_stats",
        "value": 3,
        "rarity": "legendary",
    },
}

# ------------------------------------------------------------------ #
#  Set Definitions                                                     #
# ------------------------------------------------------------------ #

EQUIPMENT_SETS: Dict[str, dict] = {
    "warrior_set": {
        "name": "Warrior's Might",
        "items": {"weapon": "iron_blade", "armor": "chain_mail", "accessory": "power_ring"},
        "bonus_2": {"stat": "attack_power", "value": 3, "desc": "+3 ATK"},
        "bonus_3": {"stat": "crit_chance", "value": 10, "desc": "+10% crit"},
    },
    "guardian_set": {
        "name": "Guardian's Wall",
        "items": {"weapon": "bronze_sword", "armor": "plate_armor", "accessory": "vitality_amulet"},
        "bonus_2": {"stat": "max_hp", "value": 15, "desc": "+15 max HP"},
        "bonus_3": {"stat": "dmg_reduce_pct", "value": 10, "desc": "-10% dmg taken"},
    },
    "dragon_set": {
        "name": "Dragon's Legacy",
        "items": {"weapon": "flame_sword", "armor": "dragon_scale", "accessory": "abyssal_crown"},
        "bonus_2": {"stat": "bonus_fire_dmg", "value": 5, "desc": "+5 fire dmg"},
        "bonus_3": {"stat": "all_stats", "value": 5, "desc": "+5 all stats"},
    },
}


class EquipmentSlots:
    """Manages equipped armor and accessory with set bonus tracking."""

    def __init__(self):
        self.equipped_armor: Optional[Any] = None
        self.equipped_accessory: Optional[Any] = None
        self.active_set: Optional[str] = None

    def equip_armor(self, armor: Any) -> Optional[Any]:
        """Equip armor. Returns previously equipped armor."""
        old = self.equipped_armor
        self.equipped_armor = armor
        self._check_set_bonus()
        return old

    def equip_accessory(self, accessory: Any) -> Optional[Any]:
        """Equip accessory. Returns previously equipped accessory."""
        old = self.equipped_accessory
        self.equipped_accessory = accessory
        self._check_set_bonus()
        return old

    def get_defense(self) -> int:
        total = 0
        if self.equipped_armor:
            total += self.equipped_armor.defense
        return total

    def get_stat_bonuses(self) -> Dict[str, int]:
        bonuses = {}
        if self.equipped_armor:
            bonuses["defense"] = self.equipped_armor.defense
        if self.equipped_accessory:
            stat = getattr(self.equipped_accessory, "stat", None)
            value = getattr(self.equipped_accessory, "value", 0)
            if stat:
                bonuses[stat] = bonuses.get(stat, 0) + value

        # Set bonuses
        if self.active_set and self.active_set in EQUIPMENT_SETS:
            set_def = EQUIPMENT_SETS[self.active_set]
            items = set_def["items"]
            equipped_items = {
                "weapon": getattr(self, "_equipped_weapon_key", ""),
                "armor": getattr(self.equipped_armor, "key", ""),
                "accessory": getattr(self.equipped_accessory, "key", ""),
            }
            matching = sum(1 for slot, key in items.items() if equipped_items.get(slot) == key)
            if matching >= 3 and "bonus_3" in set_def:
                b = set_def["bonus_3"]
                bonuses[b["stat"]] = bonuses.get(b["stat"], 0) + b["value"]
            elif matching >= 2 and "bonus_2" in set_def:
                b = set_def["bonus_2"]
                bonuses[b["stat"]] = bonuses.get(b["stat"], 0) + b["value"]

        return bonuses

    def _check_set_bonus(self):
        """Check if current equipment forms a set."""
        self.active_set = None
        equipped_items = {
            "weapon": getattr(self, "_equipped_weapon_key", ""),
            "armor": getattr(self.equipped_armor, "key", "") if self.equipped_armor else "",
            "accessory": getattr(self.equipped_accessory, "key", "") if self.equipped_accessory else "",
        }

        for set_id, set_def in EQUIPMENT_SETS.items():
            items = set_def["items"]
            matching = sum(1 for slot, key in items.items() if equipped_items.get(slot) == key)
            if matching >= 2:
                self.active_set = set_id
                return

    def update_weapon_key(self, weapon_key: str):
        """Update the equipped weapon key for set checking."""
        self._equipped_weapon_key = weapon_key
        self._check_set_bonus()

    def get_active_set_info(self) -> Optional[dict]:
        if not self.active_set:
            return None
        set_def = EQUIPMENT_SETS[self.active_set]
        equipped_items = {
            "weapon": getattr(self, "_equipped_weapon_key", ""),
            "armor": getattr(self.equipped_armor, "key", "") if self.equipped_armor else "",
            "accessory": getattr(self.equipped_accessory, "key", "") if self.equipped_accessory else "",
        }
        items = set_def["items"]
        matching = sum(1 for slot, key in items.items() if equipped_items.get(slot) == key)
        bonus = set_def.get(f"bonus_{matching}", set_def.get("bonus_2"))
        return {
            "name": set_def["name"],
            "matching": matching,
            "total": len(items),
            "bonus": bonus,
        }
