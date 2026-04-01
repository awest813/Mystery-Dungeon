"""
Phase 10 – Romanceable Companions.

Companions join the player's party, develop relationships, and have narrative arcs.
Inspired by Persona Q social links, Stardew Valley romance, and Fire Emblem support conversations.
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


SUPPORT_RANKS = ["C", "B", "A", "S"]
SUPPORT_THRESHOLDS = {
    "C": 0,
    "B": 25,
    "A": 55,
    "S": 85,
}

COMPANION_COLORS = {
    "lyra": (0.6, 0.3, 0.9, 1),
    "brom": (0.7, 0.5, 0.3, 1),
    "mira": (0.3, 0.9, 0.6, 1),
    "sable": (0.4, 0.4, 0.4, 1),
    "finn": (0.3, 0.6, 0.3, 1),
}

COMPANION_MODELS = {
    "lyra": "ice_wisp",
    "brom": "orc",
    "mira": "ghost",
    "sable": "bat",
    "finn": "goblin",
}


@dataclass
class CompanionDef:
    id: str
    name: str
    role: str
    max_hp: int
    attack_power: int
    xp_value: int
    preferred_items: List[str]
    disliked_items: List[str]
    description: str
    personality: str


def _default_companion_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "companions")


def load_companion_def(companion_id: str) -> Optional[CompanionDef]:
    path = os.path.join(_default_companion_path(), f"{companion_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return None
    return CompanionDef(
        id=raw["id"],
        name=raw.get("name", companion_id),
        role=raw.get("role", "Fighter"),
        max_hp=raw.get("max_hp", 20),
        attack_power=raw.get("attack_power", 3),
        xp_value=raw.get("xp_value", 5),
        preferred_items=raw.get("preferred_items", []),
        disliked_items=raw.get("disliked_items", []),
        description=raw.get("description", ""),
        personality=raw.get("personality", ""),
    )


class Companion:
    """A romanceable companion that can join the player's party."""

    def __init__(self, companion_id: str, x: int = 0, y: int = 0):
        self.name = companion_id
        self.x = x
        self.y = y
        self.companion_id = companion_id
        self.defn = load_companion_def(companion_id)
        if self.defn is None:
            self.defn = CompanionDef(
                id=companion_id, name=companion_id, role="Fighter",
                max_hp=20, attack_power=3, xp_value=5,
                preferred_items=[], disliked_items=[],
                description="A mysterious companion.", personality="",
            )

        self.name = self.defn.name
        self.max_hp = self.defn.max_hp
        self.hp = self.defn.max_hp
        self.attack_power = self.defn.attack_power
        self.xp_value = self.defn.xp_value
        self.is_dead = False

        self.affection = 0
        self.support_rank = "C"
        self.is_romance = False
        self.is_deployed = False

        self._gift_log: List[str] = []
        self._talked_today = False

        # Visual node (lazy)
        self._node = None
        self._visual = None

    @property
    def node(self):
        if self._node is None:
            from panda3d.core import NodePath
            self._node = NodePath(self.companion_id)
            from render import make_enemy_model, make_blob_shadow
            model_name = COMPANION_MODELS.get(self.companion_id, "goblin")
            color = COMPANION_COLORS.get(self.companion_id, (0.5, 0.5, 0.5, 1))
            self._visual = make_enemy_model(model_name, color)
            self._visual.reparentTo(self._node)
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

    # ------------------------------------------------------------------ #
    #  Affection & Support                                                 #
    # ------------------------------------------------------------------ #

    def add_affection(self, amount: int) -> bool:
        """Add affection. Returns True if support rank increased."""
        old_rank = self.support_rank
        self.affection = min(100, self.affection + amount)
        self._update_support_rank()
        return self.support_rank != old_rank

    def _update_support_rank(self) -> None:
        for rank in reversed(SUPPORT_RANKS):
            if self.affection >= SUPPORT_THRESHOLDS[rank]:
                if self.support_rank != rank:
                    self.support_rank = rank
                return

    def gift_item(self, item_key: str) -> Tuple[int, str]:
        """
        Give a gift. Returns (affection_change, message).
        """
        if item_key in self.defn.preferred_items:
            delta = 8
            msg = f"{self.name} loves it! (+{delta} affection)"
        elif item_key in self.defn.disliked_items:
            delta = -3
            msg = f"{self.name} doesn't like that... ({delta} affection)"
        else:
            delta = 2
            msg = f"{self.name} accepts the gift. (+{delta} affection)"

        if self._gift_log and self._gift_log[-1] == item_key:
            delta = max(0, delta - 2)
            msg += " (already received one today)"

        self._gift_log.append(item_key)
        self.add_affection(delta)
        return delta, msg

    def talk(self) -> Tuple[int, str]:
        """Talk at the Inn. Returns (affection_change, message)."""
        if self._talked_today:
            return 0, f"{self.name} already talked today."
        self._talked_today = True
        self.add_affection(3)
        return 3, f"Talked with {self.name}. (+3 affection)"

    def reset_daily(self) -> None:
        self._talked_today = False
        self._gift_log = []

    # ------------------------------------------------------------------ #
    #  Dungeon Combat                                                      #
    # ------------------------------------------------------------------ #

    def take_turn(self, player_x: int, player_y: int,
                  enemies: List[Any], tilemap: Any) -> Tuple[str, Any]:
        """
        Decide companion action for this turn.
        Returns (action, target) like enemy AI.
        """
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

    def on_defeat(self) -> str:
        """Companion defeated — retreats to town."""
        self.is_deployed = False
        return f"{self.name} was defeated and retreated to town."

    # ------------------------------------------------------------------ #
    #  Serialization                                                       #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.companion_id,
            "affection": self.affection,
            "support_rank": self.support_rank,
            "is_romance": self.is_romance,
            "is_deployed": self.is_deployed,
            "hp": self.hp,
            "max_hp": self.max_hp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Companion":
        comp = cls(data["id"])
        comp.affection = data.get("affection", 0)
        comp.support_rank = data.get("support_rank", "C")
        comp.is_romance = data.get("is_romance", False)
        comp.is_deployed = data.get("is_deployed", False)
        comp.hp = data.get("hp", comp.max_hp)
        comp.max_hp = data.get("max_hp", comp.max_hp)
        comp._update_support_rank()
        return comp
