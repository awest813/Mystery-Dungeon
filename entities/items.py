"""
Item system inspired by PMD, DQ Mystery Dungeon, Chocobo Dungeon, and Diablo.

Item categories:
  food      - Restore hunger and sometimes HP (PMD apples, bread)
  potion    - Restore HP or cure status
  weapon    - Temporary attack boost (equip in slot)
  orb       - Single-use magic effect (PMD Orbs / DQ scrolls)
  key       - Opens sealed rooms

Phase 7 additions:
  - Rarity tiers: Common / Uncommon / Rare / Legendary / Cursed
  - Affix system (Diablo 2 style): offensive, defensive, utility, cursed affixes
  - Item identification (NetHack / Choco Dungeon style): unidentified mystery names
  - LootGenerator factory with floor-scaled rarity weights
"""

import random

# ------------------------------------------------------------------ #
#  Phase 7 – Rarity Tiers                                             #
# ------------------------------------------------------------------ #

RARITY_TIERS = {
    "common":    {"display": "Common",    "color": (0.7, 0.7, 0.7, 1), "weight": 55, "affix_count": (0, 0)},
    "uncommon":  {"display": "Uncommon",  "color": (0.3, 0.9, 0.3, 1), "weight": 30, "affix_count": (1, 1)},
    "rare":      {"display": "Rare",      "color": (0.3, 0.5, 1.0, 1), "weight": 12, "affix_count": (2, 3)},
    "legendary": {"display": "Legendary", "color": (1.0, 0.8, 0.0, 1), "weight": 2,  "affix_count": (3, 5)},
    "cursed":    {"display": "Cursed",    "color": (0.7, 0.2, 1.0, 1), "weight": 1,  "affix_count": (1, 2)},
}

# Mystery names shown before an item type is identified (NetHack / Choco Dungeon style).
# Food is always identified – you can tell an apple from a berry.
MYSTERY_NAMES = {
    "heal_potion":   "Red Vial",
    "full_potion":   "Shimmering Vial",
    "elixir":        "Purple Flask",
    "antidote":      "Green Bottle",
    "bronze_sword":  "Tarnished Blade",
    "iron_blade":    "Heavy Sword",
    "flame_sword":   "Ember-Warm Blade",
    "frost_brand":   "Cold-Hued Sword",
    "orb_of_sight":  "Cloudy Sphere",
    "orb_of_foes":   "Red Orb",
    "orb_of_escape": "Green Orb",
    "orb_of_freeze": "Blue Orb",
    "dungeon_key":   "Old Key",
}

# ------------------------------------------------------------------ #
#  Phase 7 – Affix Definitions                                        #
# ------------------------------------------------------------------ #

_AFFIX_DEFS = {
    # tag: {stat, range (min, max), desc template, category, optional status_on_hit / cursed}
    # Offensive
    "keen":     {"stat": "attack_bonus_add", "range": (2, 6),   "desc": "+{v} ATK",            "category": "offensive"},
    "crit":     {"stat": "crit_chance",      "range": (10, 25), "desc": "+{v}% crit chance",   "category": "offensive"},
    "fiery":    {"stat": "bonus_fire_dmg",   "range": (1, 4),   "desc": "+{v} fire dmg",       "category": "offensive", "status_on_hit": "burn"},
    "freezing": {"stat": "bonus_ice_dmg",    "range": (1, 4),   "desc": "+{v} ice dmg",        "category": "offensive", "status_on_hit": "paralyzed"},
    "leeching": {"stat": "life_steal_pct",   "range": (5, 20),  "desc": "+{v}% life steal",    "category": "offensive"},
    # Defensive
    "hardy":    {"stat": "bonus_max_hp",     "range": (5, 20),  "desc": "+{v} max HP",         "category": "defensive"},
    "guard":    {"stat": "dmg_reduce_pct",   "range": (5, 15),  "desc": "-{v}% dmg taken",     "category": "defensive"},
    "resist":   {"stat": "status_resist",    "range": (1, 2),   "desc": "Status -{v}t",        "category": "defensive"},
    # Utility
    "thrifty":  {"stat": "hunger_save_pct",  "range": (10, 30), "desc": "-{v}% hunger drain",  "category": "utility"},
    "finder":   {"stat": "gold_bonus_pct",   "range": (10, 25), "desc": "+{v}% gold drops",    "category": "utility"},
    # Cursed
    "leech":    {"stat": "hp_drain_per_turn","range": (1, 3),   "desc": "-{v} HP/turn",        "category": "cursed", "cursed": True},
    "fumble":   {"stat": "confuse_on_move",  "range": (10, 20), "desc": "+{v}% confuse chance","category": "cursed", "cursed": True},
    "volatile": {"stat": "warp_on_hit",      "range": (5, 15),  "desc": "+{v}% warp on hit",   "category": "cursed", "cursed": True},
}

# Which affix tags can appear on each item category
_AFFIX_POOLS_BY_CATEGORY = {
    "weapon": list(_AFFIX_DEFS.keys()),   # weapons can get any affix
    "potion": [],
    "food":   [],
    "orb":    [],
    "key":    [],
}

# ------------------------------------------------------------------ #
#  Phase 7 – Legendary Unique Definitions                             #
# ------------------------------------------------------------------ #

LEGENDARY_UNIQUES = {
    "bronze_sword": {
        "name":   "Excalibur Shard",
        "flavor": "A fragment of the legendary blade. Radiates holy warmth.",
        "affixes": [("keen", 15), ("crit", 25), ("leeching", 15)],
    },
    "iron_blade": {
        "name":   "Blade of the Fallen Knight",
        "flavor": "Carries the grief of its last wielder into every swing.",
        "affixes": [("keen", 10), ("guard", 12), ("hardy", 18)],
    },
    "flame_sword": {
        "name":   "Emberveil",
        "flavor": "The hilt is forever warm. It chooses its bearer.",
        "affixes": [("keen", 8), ("fiery", 4), ("crit", 20), ("thrifty", 20)],
    },
    "frost_brand": {
        "name":   "Winter's Lament",
        "flavor": "Forged at the deepest frost pocket of the Abyss.",
        "affixes": [("keen", 8), ("freezing", 4), ("guard", 12), ("resist", 2)],
    },
}

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

    # --- Phase 7 additions ---
    "identify_scroll": {
        "display": "Identify Scroll",
        "category": "orb",
        "color": (0.9, 0.9, 0.6, 1),
        "effect": "identify_item",
        "description": "Identifies one unidentified item in inventory.",
    },
}

# Items that can appear on dungeon floors (weighted)
FLOOR_ITEM_TABLE = {
    1:  [("apple", 30), ("oran_berry", 20), ("heal_potion", 15), ("orb_of_sight", 10),
         ("bronze_sword", 10), ("pecha_berry", 10), ("dungeon_key", 5),
         ("identify_scroll", 5)],
    4:  [("apple", 20), ("big_apple", 10), ("oran_berry", 15), ("heal_potion", 15),
         ("elixir", 10), ("bronze_sword", 8), ("iron_blade", 7), ("orb_of_foes", 8),
         ("orb_of_sight", 5), ("pecha_berry", 7), ("dungeon_key", 5),
         ("identify_scroll", 5)],
    8:  [("big_apple", 12), ("oran_berry", 12), ("full_potion", 8), ("elixir", 12),
         ("iron_blade", 10), ("flame_sword", 6), ("frost_brand", 6), ("orb_of_escape", 8),
         ("orb_of_foes", 8), ("orb_of_freeze", 8), ("antidote", 10), ("dungeon_key", 5),
         ("heal_potion", 5), ("identify_scroll", 4)],
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


def get_weapon_affix_pool(cursed=False):
    """
    Public API: return the list of affix tags available for weapons.
    If cursed=False (default), exclude cursed affixes.
    """
    pool = _AFFIX_POOLS_BY_CATEGORY.get("weapon", [])
    if not cursed:
        return [k for k in pool if not _AFFIX_DEFS.get(k, {}).get("cursed")]
    return pool


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
        # Phase 7 fields
        self.rarity = "common"
        self.affixes = []
        self.flavor = ""
        self.cursed = False
        self.mystery_name = MYSTERY_NAMES.get(item_key)
        # Food is always identified; everything else starts identified until
        # LootGenerator explicitly marks it unidentified.
        self.is_identified = (self.mystery_name is None)

    @property
    def display_name(self):
        """Returns the mystery name if unidentified, otherwise the true name."""
        rarity_prefix = (
            f"[{RARITY_TIERS[self.rarity]['display']}] "
            if self.rarity != "common" else ""
        )
        if not self.is_identified and self.mystery_name:
            return f"{rarity_prefix}??? {self.mystery_name}"
        return f"{rarity_prefix}{self.display}"

    def get_affix_stat(self, stat_name, default=0):
        """Sum all affix values for the given stat name."""
        total = sum(a.value for a in self.affixes if a.stat == stat_name)
        return total if total else default

    def affix_descs(self):
        """Returns a list of affix description strings."""
        return [a.desc for a in self.affixes]

    def to_dict(self):
        """Serialize for save / load."""
        return {
            "key":           self.key,
            "rarity":        self.rarity,
            "affixes":       [a.to_dict() for a in self.affixes],
            "flavor":        self.flavor,
            "cursed":        self.cursed,
            "is_identified": self.is_identified,
            "display":       self.display,   # preserve legendary unique names
            "attack_bonus":  self.attack_bonus,
        }

    @staticmethod
    def from_dict(d):
        """Deserialize from save data."""
        item = Item(d["key"])
        item.rarity = d.get("rarity", "common")
        item.affixes = [ItemAffix.from_dict(a) for a in d.get("affixes", [])]
        item.flavor = d.get("flavor", "")
        item.cursed = d.get("cursed", False)
        item.is_identified = d.get("is_identified", True)
        if d.get("display"):
            item.display = d["display"]
        if "attack_bonus" in d:
            item.attack_bonus = d["attack_bonus"]
        return item

    def __repr__(self):
        return f"<Item {self.display_name}>"


# ------------------------------------------------------------------ #
#  Phase 7 – ItemAffix                                                #
# ------------------------------------------------------------------ #

class ItemAffix:
    """A single prefix or suffix affix rolled onto an item."""

    def __init__(self, tag, stat, value, cursed=False, status_on_hit=None):
        self.tag = tag
        self.stat = stat
        self.value = value
        self.cursed = cursed
        self.status_on_hit = status_on_hit
        template = _AFFIX_DEFS.get(tag, {}).get("desc", f"+{value} {stat}")
        self.desc = template.replace("{v}", str(value))

    def __repr__(self):
        return f"<Affix {self.tag}:{self.value}>"

    def to_dict(self):
        return {
            "tag":          self.tag,
            "stat":         self.stat,
            "value":        self.value,
            "cursed":       self.cursed,
            "status_on_hit": self.status_on_hit,
        }

    @staticmethod
    def from_dict(d):
        return ItemAffix(
            tag=d["tag"],
            stat=d["stat"],
            value=d["value"],
            cursed=d.get("cursed", False),
            status_on_hit=d.get("status_on_hit"),
        )


# ------------------------------------------------------------------ #
#  Phase 7 – LootGenerator                                            #
# ------------------------------------------------------------------ #

class LootGenerator:
    """
    Factory that creates Item instances with procedural rarity and affixes.
    Inspired by Diablo 2 item generation and PMD IQ items.
    """

    @staticmethod
    def pick_rarity(floor_level):
        """
        Choose a rarity tier. Higher floors increase the weight of rare/
        legendary/cursed outcomes.
        """
        tiers = list(RARITY_TIERS.keys())
        weights = []
        for tier in tiers:
            base = RARITY_TIERS[tier]["weight"]
            if tier in ("rare", "legendary", "cursed"):
                base = base + (floor_level - 1) * 0.5
            weights.append(max(base, 0.5))
        return random.choices(tiers, weights=weights, k=1)[0]

    @staticmethod
    def _roll_affix(tag):
        defn = _AFFIX_DEFS[tag]
        lo, hi = defn["range"]
        value = random.randint(lo, hi)
        return ItemAffix(
            tag=tag,
            stat=defn["stat"],
            value=value,
            cursed=defn.get("cursed", False),
            status_on_hit=defn.get("status_on_hit"),
        )

    @staticmethod
    def roll_affixes(rarity, item_category):
        """Generate the correct number of affixes for the given rarity / category."""
        pool_keys = _AFFIX_POOLS_BY_CATEGORY.get(item_category, [])
        if not pool_keys:
            return []
        lo, hi = RARITY_TIERS[rarity]["affix_count"]
        count = random.randint(lo, hi)
        if count == 0:
            return []

        cursed_keys = [k for k in pool_keys if _AFFIX_DEFS.get(k, {}).get("cursed")]
        normal_keys = [k for k in pool_keys if not _AFFIX_DEFS.get(k, {}).get("cursed")]

        selected_tags = []
        if rarity == "cursed" and cursed_keys:
            selected_tags.append(random.choice(cursed_keys))
            count -= 1

        remaining_pool = [k for k in normal_keys if k not in selected_tags]
        sample_count = min(count, len(remaining_pool))
        if sample_count > 0:
            selected_tags.extend(random.sample(remaining_pool, sample_count))

        return [LootGenerator._roll_affix(tag) for tag in selected_tags]

    @staticmethod
    def generate(item_key, floor_level=1, forced_rarity=None):
        """
        Create an Item with procedural rarity and affixes.
        Pass forced_rarity to guarantee a tier (e.g. for forge rewards).
        """
        item = Item(item_key)
        rarity = forced_rarity or LootGenerator.pick_rarity(floor_level)
        item.rarity = rarity

        if rarity == "legendary" and item_key in LEGENDARY_UNIQUES:
            unique = LEGENDARY_UNIQUES[item_key]
            item.display = unique["name"]
            item.flavor = unique.get("flavor", "")
            item.affixes = [
                ItemAffix(
                    tag=tag,
                    stat=_AFFIX_DEFS[tag]["stat"],
                    value=value,
                    cursed=_AFFIX_DEFS.get(tag, {}).get("cursed", False),
                    status_on_hit=_AFFIX_DEFS.get(tag, {}).get("status_on_hit"),
                )
                for tag, value in unique["affixes"]
            ]
        else:
            item.flavor = ""
            item.affixes = LootGenerator.roll_affixes(rarity, item.category)

        # Fold attack_bonus_add affixes into item.attack_bonus so existing
        # equip logic (player._weapon_bonus = item.attack_bonus) still works.
        bonus_add = item.get_affix_stat("attack_bonus_add")
        if bonus_add:
            item.attack_bonus += bonus_add

        item.cursed = (rarity == "cursed") or any(a.cursed for a in item.affixes)

        # Food is always identified; common items are auto-identified.
        if item.category == "food" or rarity == "common":
            item.is_identified = True
        else:
            item.is_identified = False   # identified globally when type is seen

        return item
