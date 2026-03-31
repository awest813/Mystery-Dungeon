import random
from .entity_base import Entity

class EnemyStatus:
    IDLE = 0
    CHASE = 1
    ATTACK = 2

# --- Enemy type definitions (PMD/DQ inspired) ---
ENEMY_TYPES = {
    "slime": {
        "color": (0.2, 0.8, 0.2, 1),
        "max_hp": 8,
        "attack_power": 1,
        "xp_value": 3,
        "gold_range": (1, 3),
        "chase_radius": 6,
        "description": "A squishy slime.",
        "move_pattern": "normal",  # normal, random, aggressive, cautious
    },
    "bat": {
        "color": (0.5, 0.3, 0.6, 1),
        "max_hp": 6,
        "attack_power": 2,
        "xp_value": 4,
        "gold_range": (1, 4),
        "chase_radius": 10,
        "description": "A fast cave bat.",
        "move_pattern": "aggressive",
    },
    "goblin": {
        "color": (0.4, 0.7, 0.2, 1),
        "max_hp": 12,
        "attack_power": 3,
        "xp_value": 6,
        "gold_range": (3, 8),
        "chase_radius": 7,
        "description": "A cunning goblin.",
        "move_pattern": "normal",
    },
    "ghost": {
        "color": (0.7, 0.7, 1.0, 0.6),
        "max_hp": 10,
        "attack_power": 4,
        "xp_value": 8,
        "gold_range": (2, 5),
        "chase_radius": 9,
        "description": "A phasing spirit.",
        "move_pattern": "random",    # moves unpredictably
    },
    "orc": {
        "color": (0.3, 0.5, 0.1, 1),
        "max_hp": 20,
        "attack_power": 5,
        "xp_value": 12,
        "gold_range": (5, 12),
        "chase_radius": 6,
        "description": "A hulking orc brute.",
        "move_pattern": "cautious",  # only attacks when very close
    },
    "fire_imp": {
        "color": (1.0, 0.3, 0.0, 1),
        "max_hp": 14,
        "attack_power": 6,
        "xp_value": 15,
        "gold_range": (4, 10),
        "chase_radius": 8,
        "description": "A fiery imp that burns.",
        "move_pattern": "aggressive",
        "status_on_hit": "burn",
    },
    "ice_wisp": {
        "color": (0.5, 0.8, 1.0, 1),
        "max_hp": 10,
        "attack_power": 4,
        "xp_value": 10,
        "gold_range": (3, 7),
        "chase_radius": 8,
        "description": "A frozen wisp that chills.",
        "move_pattern": "normal",
        "status_on_hit": "paralyzed",
    },
    "dark_knight": {
        "color": (0.15, 0.05, 0.25, 1),
        "max_hp": 35,
        "attack_power": 9,
        "xp_value": 30,
        "gold_range": (15, 30),
        "chase_radius": 10,
        "description": "A dread champion of the abyss.",
        "move_pattern": "aggressive",
        "is_boss": True,
    },
}

FLOOR_ENEMY_POOLS = {
    1:  ["slime", "bat"],
    3:  ["slime", "bat", "goblin"],
    5:  ["bat", "goblin", "ghost"],
    7:  ["goblin", "ghost", "orc"],
    9:  ["orc", "fire_imp", "ice_wisp"],
    11: ["fire_imp", "ice_wisp", "dark_knight"],
}

# Phase 7: material drops per enemy type {material_key: drop_chance}
ENEMY_MATERIAL_DROPS = {
    "slime":       [("slime_gel",    1.0)],
    "bat":         [("bat_wing",     0.7)],
    "goblin":      [("goblin_fang",  0.6), ("iron_ore",   0.3)],
    "ghost":       [("moonstone",    0.4)],
    "orc":         [("orc_hide",     0.6), ("iron_ore",   0.5)],
    "fire_imp":    [("flame_shard",  0.5)],
    "ice_wisp":    [("frost_jewel",  0.5)],
    "dark_knight": [("dark_crystal", 0.8), ("iron_ore",   1.0), ("moonstone", 0.5)],
}

def get_enemy_pool(floor_level):
    """Return the enemy pool appropriate for a given floor."""
    best_key = 1
    for k in sorted(FLOOR_ENEMY_POOLS.keys()):
        if floor_level >= k:
            best_key = k
    return FLOOR_ENEMY_POOLS[best_key]

def get_random_enemy_type(floor_level):
    pool = get_enemy_pool(floor_level)
    return random.choice(pool)


class Enemy(Entity):
    def __init__(self, name, x, y, enemy_type="slime"):
        super().__init__(name, x, y)
        self.enemy_type = enemy_type
        self.apply_type(enemy_type)
        self.status = EnemyStatus.IDLE

    def apply_type(self, enemy_type):
        data = ENEMY_TYPES.get(enemy_type, ENEMY_TYPES["slime"])
        self.visual.setColor(*data["color"])
        self.max_hp = data["max_hp"]
        self.hp = data["max_hp"]
        self.attack_power = data["attack_power"]
        self.xp_value = data["xp_value"]
        self.gold_range = data.get("gold_range", (1, 3))
        self.chase_radius = data.get("chase_radius", 8)
        self.move_pattern = data.get("move_pattern", "normal")
        self.status_on_hit = data.get("status_on_hit", None)
        self.is_boss = data.get("is_boss", False)
        self.base_color = data["color"]

    def reset_for_floor(self, floor_level, enemy_type=None):
        """Re-initialize this enemy with a type suitable for the floor, scaling stats."""
        if enemy_type is None:
            enemy_type = get_random_enemy_type(floor_level)
        self.enemy_type = enemy_type
        self.apply_type(enemy_type)

        # Scale stats with floor (Diablo-style scaling)
        scale = 1.0 + (floor_level - 1) * 0.12
        self.max_hp = max(1, int(self.max_hp * scale))
        self.hp = self.max_hp
        self.attack_power = max(1, int(self.attack_power * scale))
        self.xp_value = int(self.xp_value * (1.0 + (floor_level - 1) * 0.1))

        self.is_dead = False
        self.node.show()

    def gold_drop(self):
        lo, hi = self.gold_range
        return random.randint(lo, hi)

    def get_material_drops(self):
        """
        Returns a dict {material_key: count} based on enemy type and random chance.
        Phase 7 - feeds into the player's material inventory.
        """
        drops = {}
        for mat_key, chance in ENEMY_MATERIAL_DROPS.get(self.enemy_type, []):
            if random.random() < chance:
                drops[mat_key] = drops.get(mat_key, 0) + 1
        return drops

    def decide_action(self, player_x, player_y, occupants, tilemap=None):
        """
        Enhanced AI with move patterns.
        Returns (action_str, target) tuple.
        """
        if self.is_dead:
            return ("dead", None)

        dx = player_x - self.x
        dy = player_y - self.y
        dist = abs(dx) + abs(dy)

        # --- Pattern: random (ghost-like) ---
        if self.move_pattern == "random":
            if dist > self.chase_radius:
                return ("wait", None)
            if dist <= 1:
                return ("attack", (player_x, player_y))
            dirs = [(1,0),(-1,0),(0,1),(0,-1)]
            random.shuffle(dirs)
            for ddx, ddy in dirs:
                nx, ny = self.x + ddx, self.y + ddy
                if (nx, ny) not in occupants:
                    if tilemap is None or tilemap.is_walkable(nx, ny):
                        return ("move", (nx, ny))
            return ("wait", None)

        # --- Pattern: cautious (orc) – only chases when very close ---
        effective_chase = self.chase_radius
        if self.move_pattern == "cautious":
            effective_chase = 4

        # --- Pattern: aggressive – longer chase range ---
        if self.move_pattern == "aggressive":
            effective_chase = self.chase_radius + 2

        if dist > effective_chase:
            return ("wait", None)

        # Attack if adjacent
        if dist <= 1:
            return ("attack", (player_x, player_y))

        # Move toward player using greedy pathfinding
        # Primary axis
        tx, ty = self.x, self.y
        if abs(dx) >= abs(dy):
            tx += (1 if dx > 0 else -1)
        else:
            ty += (1 if dy > 0 else -1)

        if (tx, ty) not in occupants:
            if tilemap is None or tilemap.is_walkable(tx, ty):
                return ("move", (tx, ty))

        # Fallback: opposite axis
        alt_tx, alt_ty = self.x, self.y
        if abs(dx) < abs(dy):
            alt_tx += (1 if dx > 0 else -1)
        else:
            alt_ty += (1 if dy > 0 else -1)

        if (alt_tx, alt_ty) not in occupants:
            if tilemap is None or tilemap.is_walkable(alt_tx, alt_ty):
                return ("move", (alt_tx, alt_ty))

        return ("wait", None)
