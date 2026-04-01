"""
Phase 13 - New Game+ System.

Carries forward monster roster, companion bonds, and materials into a harder dungeon.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class NGPlusState:
    ngp_level: int = 0
    carried_over_materials: Dict[str, int] = None
    carried_over_monsters: List[dict] = None
    carried_over_companions: List[dict] = None
    dungeon_difficulty_mult: float = 1.0

    def __post_init__(self):
        if self.carried_over_materials is None:
            self.carried_over_materials = {}
        if self.carried_over_monsters is None:
            self.carried_over_monsters = []
        if self.carried_over_companions is None:
            self.carried_over_companions = []

    def next_difficulty(self) -> float:
        return 1.0 + (self.ngp_level * 0.25)

    def to_dict(self) -> dict:
        return {
            "ngp_level": self.ngp_level,
            "carried_over_materials": self.carried_over_materials,
            "carried_over_monsters": self.carried_over_monsters,
            "carried_over_companions": self.carried_over_companions,
            "dungeon_difficulty_mult": self.dungeon_difficulty_mult,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NGPlusState":
        return cls(
            ngp_level=data.get("ngp_level", 0),
            carried_over_materials=data.get("carried_over_materials", {}),
            carried_over_monsters=data.get("carried_over_monsters", []),
            carried_over_companions=data.get("carried_over_companions", []),
            dungeon_difficulty_mult=data.get("dungeon_difficulty_mult", 1.0),
        )


def prepare_ngp(player: Any, roster: Any) -> NGPlusState:
    """Extract carry-over data from current save."""
    state = NGPlusState(
        ngp_level=getattr(player, 'ngp_level', 0) + 1,
        carried_over_materials=dict(getattr(player, 'materials', {})),
        carried_over_monsters=[m.to_dict() for m in getattr(roster, 'monsters', [])],
        carried_over_companions=[c.to_dict() for c in getattr(player, 'companions', [])],
        dungeon_difficulty_mult=1.0 + (getattr(player, 'ngp_level', 0) * 0.25),
    )
    return state


def apply_ngp(player: Any, roster: Any, state: NGPlusState) -> None:
    """Apply NG+ carry-over data to a fresh player."""
    player.ngp_level = state.ngp_level
    player.materials = dict(state.carried_over_materials)
    
    from entities.monster_roster import CapturedMonster
    roster.monsters = []
    for md in state.carried_over_monsters:
        roster.monsters.append(CapturedMonster.from_dict(md))

    from entities.companion import Companion
    player.companions = []
    for cd in state.carried_over_companions:
        player.companions.append(Companion.from_dict(cd))
