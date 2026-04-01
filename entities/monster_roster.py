"""
Phase 12 - Monster Roster and Ranch Management.
"""
import json
import os
from typing import List, Optional, Dict, Tuple, Any

def _default_evolutions_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "monsters", "evolutions.json")

def load_evolutions() -> List[Dict]:
    path = _default_evolutions_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return raw.get("evolutions", [])
    except Exception:
        return []

class CapturedMonster:
    """A captured monster that can be deployed or stay in the Ranch."""

    def __init__(self, monster_id: str, monster_type: str, name: Optional[str] = None):
        self.id = monster_id
        self.monster_type = monster_type
        self.name = name or monster_type.replace("_", " ").title()
        
        self.level = 1
        self.xp = 0
        self.max_hp = 10
        self.hp = 10
        self.attack_power = 2
        
        self.is_deployed = False
        self.is_dead = False
        self.affixes = []
        
        self.x = 0
        self.y = 0
        
        self._node = None
        self._visual = None
        self._shadow = None

    @property
    def node(self):
        if self._node is None:
            from panda3d.core import NodePath
            self._node = NodePath(f"monster_{self.id}")
            from render import make_enemy_model, make_blob_shadow
            from entities.enemy import ENEMY_TYPES
            data = ENEMY_TYPES.get(self.monster_type, ENEMY_TYPES.get("slime", {}))
            color = data.get("color", (0.5, 0.5, 0.5, 1))
            self._visual = make_enemy_model(self.monster_type, color)
            self._visual.reparentTo(self._node)
            self._shadow = make_blob_shadow(0.16)
            self._shadow.reparentTo(self._node)
        return self._node

    @property
    def visual(self):
        _ = self.node
        return self._visual

    def move_to(self, tx, ty):
        self.x = tx
        self.y = ty
        if self._node:
            self._node.setPos(tx, ty, 0.05)

    def update(self, dt):
        pass

    def heal_full(self):
        self.is_dead = False
        self.hp = self.max_hp

    def add_xp(self, amount: int) -> bool:
        self.xp += amount
        xp_to_next = self.level * 10
        leveled_up = False
        while self.xp >= xp_to_next:
            self.xp -= xp_to_next
            self.level += 1
            self.max_hp += 2
            self.attack_power += 1
            self.hp = self.max_hp
            xp_to_next = self.level * 10
            leveled_up = True
        return leveled_up

    def check_evolution(self, inventory_items: List[str]) -> Optional[Dict]:
        evolutions = load_evolutions()
        for ev in evolutions:
            if ev["base_type"] == self.monster_type and self.level >= ev["level_req"]:
                item_req = ev.get("item_req")
                if not item_req or item_req in inventory_items:
                    return ev
        return None

    def evolve(self, ev: Dict):
        self.monster_type = ev["evolved_type"]
        if self.name == ev["base_type"].replace("_", " ").title():
            self.name = self.monster_type.replace("_", " ").title()
        
        bonuses = ev.get("stat_bonuses", {})
        self.max_hp += bonuses.get("max_hp", 0)
        self.attack_power += bonuses.get("attack_power", 0)
        self.hp = self.max_hp
        
        # If node exists, we must recreate it to show new form next run
        if self._node:
            self._node.removeNode()
            self._node = None
            self._visual = None
            self._shadow = None

    def take_turn(self, player_x: int, player_y: int,
                  enemies: List[Any], tilemap: Any) -> Tuple[str, Any]:
        """Simple AI similar to companions."""
        if self.is_dead or self.hp <= 0:
            return ("wait", None)

        if self.hp < self.max_hp * 0.25:
            return ("wait", None)

        best_enemy = None
        best_dist = 999
        for e in enemies:
            if e.is_dead:
                continue
            dist = abs(e.x - self.x) + abs(e.y - self.y)
            if dist < best_dist:
                best_dist = dist
                best_enemy = e

        if best_enemy is None:
            return ("move", (player_x, player_y))

        if best_dist <= 1:
            return ("attack", best_enemy)

        dx = best_enemy.x - self.x
        dy = best_enemy.y - self.y
        tx, ty = self.x, self.y
        if abs(dx) >= abs(dy):
            tx += (1 if dx > 0 else -1)
        else:
            ty += (1 if dy > 0 else -1)

        if tilemap and tilemap.is_walkable(tx, ty):
            return ("move", (tx, ty))
        return ("wait", None)

    def to_dict(self):
        return {
            "id": self.id,
            "monster_type": self.monster_type,
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "max_hp": self.max_hp,
            "attack_power": self.attack_power,
            "is_deployed": self.is_deployed,
            "is_dead": self.is_dead,
            "hp": self.hp,
            "affixes": self.affixes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CapturedMonster":
        cm = cls(data["id"], data["monster_type"], data.get("name"))
        cm.level = data.get("level", 1)
        cm.xp = data.get("xp", 0)
        cm.max_hp = data.get("max_hp", 10)
        cm.attack_power = data.get("attack_power", 2)
        cm.is_deployed = data.get("is_deployed", False)
        cm.is_dead = data.get("is_dead", False)
        cm.hp = data.get("hp", 10)
        cm.affixes = data.get("affixes", [])
        return cm

class MonsterRoster:
    def __init__(self, max_size=30):
        self.max_size = max_size
        self.monsters: List[CapturedMonster] = []
        self.ranch_inventory: Dict[str, int] = {}

    def add_monster(self, monster: CapturedMonster) -> bool:
        if len(self.monsters) >= self.max_size:
            return False
        self.monsters.append(monster)
        return True

    def remove_monster(self, monster_id: str):
        self.monsters = [m for m in self.monsters if m.id != monster_id]

    def get_deployed(self) -> List[CapturedMonster]:
        return [m for m in self.monsters if m.is_deployed]

    def get_ranch_monsters(self) -> List[CapturedMonster]:
        return [m for m in self.monsters if not m.is_deployed]

    def produce_materials(self):
        from entities.enemy import ENEMY_TYPES
        for m in self.get_ranch_monsters():
            base_type = m.monster_type
            enemy_data = ENEMY_TYPES.get(base_type)
            if not enemy_data:
                continue
            drops = enemy_data.get("drops", {})
            if drops:
                import random
                keys = list(drops.keys())
                weights = list(drops.values())
                mat = random.choices(keys, weights=weights, k=1)[0]
                self.ranch_inventory[mat] = self.ranch_inventory.get(mat, 0) + 1

    def to_dict(self):
        return {
            "max_size": self.max_size,
            "monsters": [m.to_dict() for m in self.monsters],
            "ranch_inventory": self.ranch_inventory,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonsterRoster":
        roster = cls(max_size=data.get("max_size", 30))
        roster.ranch_inventory = data.get("ranch_inventory", {})
        for md in data.get("monsters", []):
            roster.monsters.append(CapturedMonster.from_dict(md))
        return roster
