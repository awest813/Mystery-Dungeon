"""
Phase 13 - Final Boss Entity.

Multi-phase boss that triggers at floor 25 with escalating difficulty.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from panda3d.core import NodePath, CardMaker
from entities.entity_base import Entity
from render import make_enemy_model, make_blob_shadow


def _default_boss_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "bosses", "final_boss.json")


def load_final_boss_data() -> Optional[Dict]:
    path = _default_boss_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return raw.get("final_boss")
    except Exception:
        return None


class FinalBoss(Entity):
    """Multi-phase final boss encountered at floor 25."""

    def __init__(self, x: int = 0, y: int = 0):
        super().__init__("The Abyssal King", x, y)
        self.boss_data = load_final_boss_data()
        if not self.boss_data:
            self.boss_data = {
                "name": "The Abyssal King",
                "phases": [
                    {"name": "Phase 1", "max_hp": 150, "attack_power": 15},
                    {"name": "Phase 2", "max_hp": 100, "attack_power": 20},
                    {"name": "Phase 3", "max_hp": 60, "attack_power": 25},
                ],
            }

        self.current_phase = 0
        self._load_phase(0)
        self.is_boss = True

    def _load_phase(self, phase_idx: int):
        phases = self.boss_data.get("phases", [])
        if phase_idx >= len(phases):
            return
        phase = phases[phase_idx]
        self.phase_name = phase.get("name", f"Phase {phase_idx + 1}")
        self.max_hp = phase.get("max_hp", 100)
        self.hp = self.max_hp
        self.attack_power = phase.get("attack_power", 10)
        self.skills = phase.get("skills", [])

        # Visual update per phase
        colors = [
            (0.3, 0.1, 0.5, 1),   # Phase 1: dark purple
            (0.5, 0.1, 0.1, 1),   # Phase 2: angry red
            (0.1, 0.0, 0.2, 1),   # Phase 3: void black
        ]
        color = colors[min(phase_idx, len(colors) - 1)]

        # Rebuild visual
        if self.visual:
            self.visual.removeNode()
        if self.shadow:
            self.shadow.removeNode()

        self.visual = make_enemy_model("dark_knight", color)
        if hasattr(self, 'node') and self.node:
            parent = self.node.getParent()
            if parent:
                self.visual.reparentTo(parent)

        self.shadow = make_blob_shadow(0.30)
        if parent:
            self.shadow.reparentTo(parent)

    def take_damage(self, amount: int) -> int:
        result = super().take_damage(amount)
        if not self.is_dead and self.hp <= 0:
            self._advance_phase()
        return result

    def _advance_phase(self):
        self.current_phase += 1
        phases = self.boss_data.get("phases", [])
        if self.current_phase < len(phases):
            self.is_dead = False
            self._load_phase(self.current_phase)
        else:
            self.is_dead = True
            self.on_death()

    def get_phase_info(self) -> str:
        return self.phase_name

    def to_dict(self) -> dict:
        return {
            "type": "final_boss",
            "current_phase": self.current_phase,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "x": self.x,
            "y": self.y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FinalBoss":
        boss = cls(data.get("x", 0), data.get("y", 0))
        boss.current_phase = data.get("current_phase", 0)
        boss._load_phase(boss.current_phase)
        boss.hp = data.get("hp", boss.max_hp)
        return boss
