"""
Phase 15 - NPC Schedule System.

Town NPCs with daily routines, movement paths, dialogue states,
and relationship tracking. Inspired by Story of Seasons and Fantasy Life.
"""
from __future__ import annotations

import json
import os
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from panda3d.core import NodePath


def _default_npc_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "npcs")


@dataclass
class ScheduleEntry:
    hour: int          # 0-23
    x: int
    y: int
    activity: str      # "idle", "working", "walking", "sleeping"
    dialogue: str = ""


@dataclass
class NPCDef:
    id: str
    name: str
    role: str
    color: Tuple[float, float, float, float]
    model_type: str
    schedule: List[ScheduleEntry]
    preferred_gifts: List[str]
    disliked_gifts: List[str]
    dialogues: Dict[str, List[str]]  # context -> list of lines
    shop_stock: Optional[List[dict]] = None


def load_npc_def(npc_id: str) -> Optional[NPCDef]:
    path = os.path.join(_default_npc_path(), f"{npc_id}.json")
    try:
        with open(path, "r") as f:
            raw = json.load(f)
    except Exception:
        return None

    schedule = []
    for s in raw.get("schedule", []):
        schedule.append(ScheduleEntry(
            hour=s["hour"],
            x=s["x"],
            y=s["y"],
            activity=s.get("activity", "idle"),
            dialogue=s.get("dialogue", ""),
        ))

    return NPCDef(
        id=raw["id"],
        name=raw.get("name", npc_id),
        role=raw.get("role", "Villager"),
        color=tuple(raw.get("color", [0.5, 0.5, 0.5, 1])),
        model_type=raw.get("model_type", "goblin"),
        schedule=schedule,
        preferred_gifts=raw.get("preferred_gifts", []),
        disliked_gifts=raw.get("disliked_gifts", []),
        dialogues=raw.get("dialogues", {}),
        shop_stock=raw.get("shop_stock"),
    )


def list_npc_ids() -> List[str]:
    path = _default_npc_path()
    try:
        return [f.replace(".json", "") for f in os.listdir(path) if f.endswith(".json")]
    except Exception:
        return []


NPC_COLORS = {
    "mayor": (0.8, 0.6, 0.2, 1),
    "merchant": (0.6, 0.8, 0.3, 1),
    "blacksmith": (0.7, 0.4, 0.2, 1),
    "librarian": (0.4, 0.5, 0.8, 1),
    "farmer": (0.3, 0.7, 0.3, 1),
}

NPC_MODELS = {
    "mayor": "orc",
    "merchant": "goblin",
    "blacksmith": "orc",
    "librarian": "ghost",
    "farmer": "goblin",
}


class NPC:
    """A town NPC with schedule, dialogue, and gift system."""

    def __init__(self, npc_id: str, x: int = 0, y: int = 0):
        self.npc_id = npc_id
        self.defn = load_npc_def(npc_id)
        if self.defn is None:
            self.defn = NPCDef(
                id=npc_id, name=npc_id, role="Villager",
                color=(0.5, 0.5, 0.5, 1), model_type="goblin",
                schedule=[], preferred_gifts=[], disliked_gifts=[],
                dialogues={},
            )

        self.name = self.defn.name
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.affection = 0
        self.gifted_today = False
        self.current_activity = "idle"

        self._node: Optional[NodePath] = None
        self._visual: Optional[NodePath] = None
        self._shadow: Optional[NodePath] = None

    @property
    def node(self) -> NodePath:
        if self._node is None:
            from panda3d.core import NodePath as PNodePath
            self._node = PNodePath(f"npc_{self.npc_id}")
            from render import make_enemy_model, make_blob_shadow
            color = self.defn.color
            model_type = self.defn.model_type
            self._visual = make_enemy_model(model_type, color)
            self._visual.reparentTo(self._node)
            self._shadow = make_blob_shadow(0.18)
            self._shadow.reparentTo(self._node)
            self._node.setPos(self.x, self.y, 0.05)
        return self._node

    def update(self, dt: float):
        """Move toward target position with smooth interpolation."""
        if self._node is None:
            return
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0.05:
            speed = 2.0
            self.x += (dx / dist) * min(dist, speed * dt)
            self.y += (dy / dist) * min(dist, speed * dt)
            self._node.setPos(self.x, self.y, 0.05)

    def update_schedule(self, hour: int, season: str):
        """Update NPC position and activity based on schedule."""
        # Find the closest schedule entry at or before current hour
        best = None
        for entry in self.defn.schedule:
            if entry.hour <= hour:
                best = entry
            else:
                break

        if best:
            self.target_x = best.x
            self.target_y = best.y
            self.current_activity = best.activity

    def gift_item(self, item_key: str) -> Tuple[int, str]:
        """Give a gift. Returns (affection_change, message)."""
        if self.gifted_today:
            return 0, f"{self.name} already received a gift today."

        self.gifted_today = True
        if item_key in self.defn.preferred_gifts:
            delta = 10
            msg = f"{self.name} loves it! (+{delta} affection)"
        elif item_key in self.defn.disliked_gifts:
            delta = -5
            msg = f"{self.name} doesn't like that... ({delta} affection)"
        else:
            delta = 3
            msg = f"{self.name} accepts the gift. (+{delta} affection)"

        self.affection = max(0, min(100, self.affection + delta))
        return delta, msg

    def talk(self, context: str = "default") -> str:
        """Get dialogue based on context and affection level."""
        dialogues = self.defn.dialogues.get(context, self.defn.dialogues.get("default", []))
        if not dialogues:
            return f"{self.name}: (The {self.defn.role} nods politely.)"

        # Pick dialogue based on affection
        idx = min(len(dialogues) - 1, self.affection // 25)
        return f"{self.name}: {dialogues[idx]}"

    def reset_daily(self):
        self.gifted_today = False

    def reparent_to(self, parent):
        _ = self.node
        if self._node:
            self._node.reparentTo(parent)

    def to_dict(self) -> dict:
        return {
            "id": self.npc_id,
            "affection": self.affection,
            "x": self.x,
            "y": self.y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        npc = cls(data["id"])
        npc.affection = data.get("affection", 0)
        npc.x = data.get("x", 0)
        npc.y = data.get("y", 0)
        npc.target_x = npc.x
        npc.target_y = npc.y
        return npc
