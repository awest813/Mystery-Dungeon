"""
Skill / Move system inspired by PMD (4 moves), FF Tactics (job abilities),
and Persona Q (skill inheritance).

Each skill has PP (uses per floor) and an effect function signature:
  effect(user, target_pos, tilemap, enemies, log_callback) -> bool (did it connect)
"""

SKILL_DEFS = {
    # --- Offensive ---
    "slash": {
        "display": "Slash",
        "pp": 12,
        "max_pp": 12,
        "range": 1,
        "damage_mult": 1.5,
        "description": "A sharp sword slash. 1.5x damage.",
        "element": None,
        "learn_level": 1,
    },
    "headbutt": {
        "display": "Headbutt",
        "pp": 15,
        "max_pp": 15,
        "range": 1,
        "damage_mult": 1.2,
        "push": True,
        "description": "Rams the enemy, pushing it back.",
        "element": None,
        "learn_level": 2,
    },
    "ember": {
        "display": "Ember",
        "pp": 10,
        "max_pp": 10,
        "range": 3,
        "damage_mult": 1.3,
        "status_inflict": "burn",
        "description": "Shoots fire. May burn. Range 3.",
        "element": "fire",
        "learn_level": 3,
    },
    "ice_shard": {
        "display": "Ice Shard",
        "pp": 10,
        "max_pp": 10,
        "range": 3,
        "damage_mult": 1.2,
        "status_inflict": "paralyzed",
        "description": "Throws ice. May paralyze. Range 3.",
        "element": "ice",
        "learn_level": 4,
    },
    "thunder": {
        "display": "Thunder",
        "pp": 8,
        "max_pp": 8,
        "range": 4,
        "damage_mult": 2.0,
        "description": "Powerful lightning bolt. Range 4.",
        "element": "lightning",
        "learn_level": 6,
    },
    "shadow_claw": {
        "display": "Shadow Claw",
        "pp": 12,
        "max_pp": 12,
        "range": 1,
        "damage_mult": 1.8,
        "status_inflict": "confused",
        "description": "Dark swipe. May confuse. High crit.",
        "element": "dark",
        "learn_level": 8,
    },
    "giga_impact": {
        "display": "Giga Impact",
        "pp": 5,
        "max_pp": 5,
        "range": 1,
        "damage_mult": 3.0,
        "description": "Massive blow. 3x damage, few uses.",
        "element": None,
        "learn_level": 10,
    },

    # --- Utility / Support ---
    "heal": {
        "display": "Heal",
        "pp": 6,
        "max_pp": 6,
        "range": 0,
        "hp_restore_frac": 0.3,
        "description": "Restore 30% of max HP.",
        "element": None,
        "learn_level": 5,
    },
    "sleep_powder": {
        "display": "Sleep Powder",
        "pp": 8,
        "max_pp": 8,
        "range": 3,
        "damage_mult": 0,
        "status_inflict": "asleep",
        "description": "Puts target to sleep. Range 3.",
        "element": None,
        "learn_level": 4,
    },
    "toxic": {
        "display": "Toxic",
        "pp": 10,
        "max_pp": 10,
        "range": 2,
        "damage_mult": 0,
        "status_inflict": "poisoned",
        "description": "Badly poisons the target. Range 2.",
        "element": None,
        "learn_level": 3,
    },
}

# Which skills the player starts with or learns at each level
LEVEL_SKILL_LEARN = {
    1:  "slash",
    2:  "headbutt",
    3:  "ember",
    4:  "sleep_powder",
    5:  "heal",
    6:  "thunder",
    7:  "toxic",
    8:  "shadow_claw",
    10: "giga_impact",
}


class Skill:
    def __init__(self, key):
        data = SKILL_DEFS[key]
        self.key = key
        self.display = data["display"]
        self.pp = data["pp"]
        self.max_pp = data["max_pp"]
        self.range = data["range"]
        self.damage_mult = data.get("damage_mult", 1.0)
        self.push = data.get("push", False)
        self.status_inflict = data.get("status_inflict", None)
        self.hp_restore_frac = data.get("hp_restore_frac", 0)
        self.element = data.get("element", None)
        self.description = data["description"]

    def restore_pp(self):
        self.pp = self.max_pp

    def use(self):
        """Decrement PP. Returns True if usable."""
        if self.pp <= 0:
            return False
        self.pp -= 1
        return True

    def __repr__(self):
        return f"<Skill {self.display} PP:{self.pp}/{self.max_pp}>"


def get_skills_for_level(level):
    """Returns the list of Skill objects the player should know at this level."""
    known = []
    for lvl, key in sorted(LEVEL_SKILL_LEARN.items()):
        if level >= lvl:
            known.append(Skill(key))
    # PMD-style: cap at 4 skills (latest 4 learned)
    return known[-4:]
