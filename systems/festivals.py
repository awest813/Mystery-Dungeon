"""
Phase 15 - Festival System.

Seasonal events, mini-games, and special rewards that occur on specific days.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Festival:
    id: str
    name: str
    season: str
    day: int
    description: str
    rewards: Dict[str, int]
    mini_game: Optional[str] = None


FESTIVALS: List[Festival] = [
    Festival(
        "spring_bloom", "Spring Bloom Festival", "Spring", 7,
        "Celebrate the first flowers of spring! Gift flowers for bonus affection.",
        {"gold": 30, "xp": 15},
        "flower_picking",
    ),
    Festival(
        "summer_fair", "Summer Fair", "Summer", 14,
        "A lively fair with games and treats. Win prizes at the mini-games!",
        {"gold": 50, "xp": 25},
        "fishing_contest",
    ),
    Festival(
        "harvest_moon", "Harvest Moon Festival", "Autumn", 14,
        "Give thanks for the harvest. Cook your best dish for the contest.",
        {"gold": 40, "xp": 20},
        "cooking_contest",
    ),
    Festival(
        "starlight_night", "Starlight Night", "Autumn", 28,
        "A quiet evening under the stars. Perfect for deep conversations.",
        {"gold": 20, "xp": 30},
        None,
    ),
    Festival(
        "snow_festival", "Snow Festival", "Winter", 7,
        "Build snow sculptures and enjoy warm drinks by the fire.",
        {"gold": 25, "xp": 15},
        "snowball_fight",
    ),
    Festival(
        "new_years", "New Year's Eve", "Winter", 28,
        "Ring in the new year with the whole town. Reflect on the past year.",
        {"gold": 60, "xp": 40},
        None,
    ),
]


class FestivalSystem:
    """Manages seasonal festivals and their triggers."""

    def __init__(self):
        self.active_festival: Optional[Festival] = None
        self.completed_festivals: List[str] = []
        self.festival_score: int = 0

    def check_festival(self, season: str, day: int) -> Optional[Festival]:
        """Check if today is a festival day."""
        for fest in FESTIVALS:
            if fest.season == season and fest.day == day:
                if fest.id not in self.completed_festivals:
                    self.active_festival = fest
                    return fest
        return None

    def complete_festival(self, score: int = 0) -> List[str]:
        """Complete the active festival. Returns reward messages."""
        if not self.active_festival:
            return ["No active festival."]

        msgs = []
        fest = self.active_festival
        self.completed_festivals.append(fest.id)
        self.festival_score += score

        for reward_type, amount in fest.rewards.items():
            msgs.append(f"Festival Reward: +{amount} {reward_type}")

        msgs.append(f"Completed: {fest.name}!")
        self.active_festival = None
        return msgs

    def get_upcoming_festivals(self, season: str) -> List[Festival]:
        """Get festivals for the current season that haven't occurred."""
        return [
            f for f in FESTIVALS
            if f.season == season and f.id not in self.completed_festivals
        ]

    def reset_season(self):
        """Reset festival tracking for a new season."""
        # Don't reset completed_festivals - they're permanent
        self.active_festival = None

    def to_dict(self) -> dict:
        return {
            "completed_festivals": self.completed_festivals,
            "festival_score": self.festival_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FestivalSystem":
        fs = cls()
        fs.completed_festivals = data.get("completed_festivals", [])
        fs.festival_score = data.get("festival_score", 0)
        return fs
