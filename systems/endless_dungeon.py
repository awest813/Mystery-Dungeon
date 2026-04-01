"""
Phase 13 - Endless Dungeon System.

Scales difficulty past floor 20 with legendary events, modifier stacking,
and a high-score leaderboard.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

LEGENDARY_EVENTS = {
    "blizzard": {
        "description": "Blizzard! All enemies move slower but deal +20% damage.",
        "effect": "enemy_atk_bonus",
        "value": 20,
        "duration_floors": 3,
    },
    "golden_floor": {
        "description": "Golden Floor! All items are rare+ and gold drops doubled.",
        "effect": "gold_bonus",
        "value": 100,
        "duration_floors": 1,
    },
    "monster_stampede": {
        "description": "Monster Stampede! +50% more enemies spawn.",
        "effect": "extra_spawns",
        "value": 50,
        "duration_floors": 2,
    },
    "darkness": {
        "description": "Darkness! Visibility reduced to 3 tiles.",
        "effect": "reduced_vision",
        "value": 3,
        "duration_floors": 2,
    },
    "blessing": {
        "description": "Dungeon Blessing! HP fully restored, all PP restored.",
        "effect": "full_restore",
        "value": 0,
        "duration_floors": 0,
    },
}


@dataclass
class ActiveEvent:
    event_id: str
    description: str
    effect: str
    value: int
    remaining_floors: int

    def tick(self) -> bool:
        """Advance one floor. Returns True if event expired."""
        self.remaining_floors -= 1
        return self.remaining_floors <= 0


class EndlessDungeon:
    """Manages scaling difficulty and legendary events for floors 20+."""

    def __init__(self):
        self.active_events: List[ActiveEvent] = []
        self.floor_modifiers: Dict[str, int] = {}
        self.high_score = 0

    def get_floor_difficulty_scale(self, floor_level: int) -> float:
        """Returns a multiplier for enemy stats. 1.0 at floor 1, scales up."""
        if floor_level <= 20:
            return 1.0
        extra = floor_level - 20
        return 1.0 + (extra * 0.08)

    def get_enemy_stat_bonus(self, floor_level: int) -> Dict[str, int]:
        """Returns flat stat bonuses for enemies on this floor."""
        bonus = {"attack_power": 0, "max_hp": 0}
        if floor_level > 20:
            extra = floor_level - 20
            bonus["attack_power"] = extra // 3
            bonus["max_hp"] = extra * 3
        for event in self.active_events:
            if event.effect == "enemy_atk_bonus":
                bonus["attack_power"] += event.value
        return bonus

    def roll_legendary_event(self, floor_level: int) -> Optional[ActiveEvent]:
        """10% chance per floor 20+ to trigger a legendary event."""
        if floor_level < 20:
            return None
        if random.random() > 0.10:
            return None

        event_id = random.choice(list(LEGENDARY_EVENTS.keys()))
        data = LEGENDARY_EVENTS[event_id]
        return ActiveEvent(
            event_id=event_id,
            description=data["description"],
            effect=data["effect"],
            value=data["value"],
            remaining_floors=data["duration_floors"],
        )

    def advance_floor(self, floor_level: int) -> List[str]:
        """Call when entering a new floor. Returns list of event messages."""
        messages = []

        # Tick existing events
        expired = []
        for event in self.active_events:
            if event.tick():
                expired.append(event)
                messages.append(f"Event ended: {event.event_id.replace('_', ' ').title()}")
        for e in expired:
            self.active_events.remove(e)

        # Roll new event
        new_event = self.roll_legendary_event(floor_level)
        if new_event:
            self.active_events.append(new_event)
            messages.append(new_event.description)

        return messages

    def get_gold_multiplier(self) -> float:
        mult = 1.0
        for event in self.active_events:
            if event.effect == "gold_bonus":
                mult += event.value / 100
        return mult

    def get_extra_spawn_pct(self) -> int:
        extra = 0
        for event in self.active_events:
            if event.effect == "extra_spawns":
                extra += event.value
        return extra

    def get_vision_radius(self) -> Optional[int]:
        for event in self.active_events:
            if event.effect == "reduced_vision":
                return event.value
        return None

    def has_full_restore(self) -> bool:
        for event in self.active_events:
            if event.effect == "full_restore":
                return True
        return False

    def consume_full_restore(self):
        self.active_events = [e for e in self.active_events if e.effect != "full_restore"]

    def calculate_score(self, floor_level: int, gold: int, kills: int) -> int:
        return (floor_level * 100) + (gold // 2) + (kills * 10)

    def update_high_score(self, score: int) -> bool:
        if score > self.high_score:
            self.high_score = score
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "high_score": self.high_score,
            "active_events": [
                {"event_id": e.event_id, "remaining_floors": e.remaining_floors}
                for e in self.active_events
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EndlessDungeon":
        ed = cls()
        ed.high_score = data.get("high_score", 0)
        for ed_data in data.get("active_events", []):
            eid = ed_data["event_id"]
            if eid in LEGENDARY_EVENTS:
                ld = LEGENDARY_EVENTS[eid]
                ed.active_events.append(ActiveEvent(
                    event_id=eid,
                    description=ld["description"],
                    effect=ld["effect"],
                    value=ld["value"],
                    remaining_floors=ed_data.get("remaining_floors", 1),
                ))
        return ed
