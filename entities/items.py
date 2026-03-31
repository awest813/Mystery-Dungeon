"""
Item system inspired by PMD, DQ Mystery Dungeon, Chocobo Dungeon, and Diablo.

Item categories:
  food      - Restore hunger and sometimes HP (PMD apples, bread)
  potion    - Restore HP or cure status
  weapon    - Temporary attack boost (equip in slot)
  orb       - Single-use magic effect (PMD Orbs / DQ scrolls)
  key       - Opens sealed rooms
"""

import random

# ---- Item Definitions ----
ITEM_DEFS = {
    # --- Food ---
    "apple": {
        "display": "Apple",
        "category": "food",
        "color": (0.9, 0.2, 0.2, 1),
        "hunger_restore": 40,
        "hp_restore": 0,
        "description": "A crisp apple. Fills the belly.",
    },
    "big_apple": {
        "display": "Big Apple",
        "category": "food",
        "color": (1.0, 0.3, 0.1, 1),
        "hunger_restore": 70,
        "hp_restore": 5,
        "description": "A large apple. Very filling.",
    },
    "oran_berry": {
        "display": "Oran Berry",
        "category": "food",
        "color": (0.2, 0.5, 1.0, 1),
        "hunger_restore": 10,
        "hp_restore": 10,
        "description": "A blue berry. Heals HP.",
    },
    "pecha_berry": {
        "display": "Pecha Berry",
        "category": "food",
        "color": (1.0, 0.6, 0.8, 1),
        "hunger_restore": 5,
        "hp_restore": 0,
        "cure_status": "poisoned",
        "description": "Cures poison.",
    },

    # --- Potions ---
    "heal_potion": {
        "display": "Heal Potion",
        "category": "potion",
        "color": (0.2, 1.0, 0.4, 1),
        "hp_restore": 25,
        "description": "Restores 25 HP.",
    },
    "full_potion": {
        "display": "Max Potion",
        "category": "potion",
        "color": (0.0, 1.0, 0.8, 1),
        "hp_restore": 9999,
        "description": "Fully restores HP.",
    },
    "elixir": {
        "display": "Elixir",
        "category": "potion",
        "color": (0.8, 0.2, 1.0, 1),
        "hp_restore": 15,
        "hunger_restore": 20,
        "description": "Restores HP and hunger.",
    },
    "antidote": {
        "display": "Antidote",
        "category": "potion",
        "color": (0.4, 0.9, 0.3, 1),
        "cure_status": "poisoned",
        "description": "Cures poison.",
    },

    # --- Weapons / Equippable ---
    "bronze_sword": {
        "display": "Bronze Sword",
        "category": "weapon",
        "color": (0.7, 0.5, 0.2, 1),
        "attack_bonus": 3,
        "description": "+3 ATK. A dull bronze blade.",
    },
    "iron_blade": {
        "display": "Iron Blade",
        "category": "weapon",
        "color": (0.6, 0.6, 0.7, 1),
        "attack_bonus": 6,
        "description": "+6 ATK. A reliable iron sword.",
    },
    "flame_sword": {
        "display": "Flame Sword",
        "category": "weapon",
        "color": (1.0, 0.5, 0.0, 1),
        "attack_bonus": 10,
        "status_on_hit": "burn",
        "description": "+10 ATK. Burns foes on hit.",
    },
    "frost_brand": {
        "display": "Frost Brand",
        "category": "weapon",
        "color": (0.3, 0.8, 1.0, 1),
        "attack_bonus": 8,
        "status_on_hit": "paralyzed",
        "description": "+8 ATK. May paralyze foes.",
    },

    # --- Orbs / Scrolls (single-use magic, PMD Orbs / DQ Scrolls) ---
    "orb_of_sight": {
        "display": "Orb of Sight",
        "category": "orb",
        "color": (1.0, 1.0, 0.3, 1),
        "effect": "reveal_map",
        "description": "Reveals the whole floor.",
    },
    "orb_of_foes": {
        "display": "Orb of Foes",
        "category": "orb",
        "color": (1.0, 0.2, 0.2, 1),
        "effect": "confuse_enemies",
        "description": "Confuses all enemies on floor.",
    },
    "orb_of_escape": {
        "display": "Escape Orb",
        "category": "orb",
        "color": (0.5, 1.0, 0.5, 1),
        "effect": "escape_dungeon",
        "description": "Instantly returns to town.",
    },
    "orb_of_freeze": {
        "display": "Orb of Freeze",
        "category": "orb",
        "color": (0.2, 0.7, 1.0, 1),
        "effect": "paralyze_enemies",
        "description": "Paralyzes all enemies briefly.",
    },

    # --- Key ---
    "dungeon_key": {
        "display": "Dungeon Key",
        "category": "key",
        "color": (1.0, 0.9, 0.1, 1),
        "description": "Opens a sealed room.",
    },
}

# Items that can appear on dungeon floors (weighted)
FLOOR_ITEM_TABLE = {
    1:  [("apple", 30), ("oran_berry", 20), ("heal_potion", 15), ("orb_of_sight", 10),
         ("bronze_sword", 10), ("pecha_berry", 10), ("dungeon_key", 5)],
    4:  [("apple", 20), ("big_apple", 10), ("oran_berry", 15), ("heal_potion", 15),
         ("elixir", 10), ("bronze_sword", 8), ("iron_blade", 7), ("orb_of_foes", 8),
         ("orb_of_sight", 5), ("pecha_berry", 7), ("dungeon_key", 5)],
    8:  [("big_apple", 12), ("oran_berry", 12), ("full_potion", 8), ("elixir", 12),
         ("iron_blade", 10), ("flame_sword", 6), ("frost_brand", 6), ("orb_of_escape", 8),
         ("orb_of_foes", 8), ("orb_of_freeze", 8), ("antidote", 10), ("dungeon_key", 5),
         ("heal_potion", 5)],
}

def _get_item_table(floor_level):
    best = 1
    for k in sorted(FLOOR_ITEM_TABLE.keys()):
        if floor_level >= k:
            best = k
    return FLOOR_ITEM_TABLE[best]

def random_item_for_floor(floor_level):
    """Pick a random item key using weighted table for the given floor."""
    table = _get_item_table(floor_level)
    keys = [k for k, _ in table]
    weights = [w for _, w in table]
    return random.choices(keys, weights=weights, k=1)[0]


class Item:
    """A concrete item instance that can be in inventory or on the ground."""
    def __init__(self, item_key):
        self.key = item_key
        data = ITEM_DEFS.get(item_key, ITEM_DEFS["apple"])
        self.display = data["display"]
        self.category = data["category"]
        self.color = data["color"]
        self.description = data["description"]
        # Optional fields
        self.hunger_restore = data.get("hunger_restore", 0)
        self.hp_restore = data.get("hp_restore", 0)
        self.attack_bonus = data.get("attack_bonus", 0)
        self.cure_status = data.get("cure_status", None)
        self.status_on_hit = data.get("status_on_hit", None)
        self.effect = data.get("effect", None)

    def __repr__(self):
        return f"<Item {self.display}>"
