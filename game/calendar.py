from __future__ import annotations

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
DAYS_PER_WEEK = 7
DAYS_PER_SEASON = 28

SEASON_EFFECTS = {
    "Spring": {
        "herb_growth_bonus": 1,
        "description": "Herb crops grow faster",
    },
    "Summer": {
        "fire_enemy_atk_bonus": 10,
        "description": "Fire enemies +10% ATK",
    },
    "Autumn": {
        "gold_drop_bonus": 10,
        "description": "Gold drops +10%",
    },
    "Winter": {
        "hunger_drain_bonus": 20,
        "description": "Hunger drains 20% faster",
    },
}


class Calendar:
    def __init__(self, day: int = 1):
        self.day = day

    @property
    def season_index(self) -> int:
        return ((self.day - 1) // DAYS_PER_SEASON) % len(SEASONS)

    @property
    def season(self) -> str:
        return SEASONS[self.season_index]

    @property
    def day_in_season(self) -> int:
        return ((self.day - 1) % DAYS_PER_SEASON) + 1

    @property
    def week_in_season(self) -> int:
        return (self.day_in_season - 1) // DAYS_PER_WEEK + 1

    def advance_day(self) -> None:
        self.day += 1

    def get_season_effect(self) -> dict:
        return SEASON_EFFECTS.get(self.season, {})

    def to_dict(self) -> dict:
        return {"day": self.day}

    @classmethod
    def from_dict(cls, data: dict) -> Calendar:
        return cls(day=data.get("day", 1))
