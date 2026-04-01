"""
Phase 8 – Town building from dungeon materials (data-driven).

Loads `data/buildings.json` and exposes helpers to list affordable builds,
complete construction, and apply optional town tile visuals.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from world.dungeon_generator import TILE_FLOOR, TILE_HERBALIST, TILE_INN, TILE_SHRINE, TILE_GUILD


@dataclass(frozen=True)
class BuildingDef:
    id: str
    name: str
    description: str
    requires: Tuple[str, ...]
    materials: Dict[str, int]
    gold: int


def _default_json_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "buildings.json")


def load_building_definitions(path: Optional[str] = None) -> List[BuildingDef]:
    path = path or _default_json_path()
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    out: List[BuildingDef] = []
    for row in raw.get("buildings", []):
        out.append(
            BuildingDef(
                id=row["id"],
                name=row.get("name", row["id"]),
                description=row.get("description", ""),
                requires=tuple(row.get("requires", [])),
                materials=dict(row.get("materials", {})),
                gold=int(row.get("gold", 0)),
            )
        )
    return out


def _requirements_met(b: BuildingDef, completed: Set[str]) -> bool:
    return all(r in completed for r in b.requires)


def can_build(
    b: BuildingDef,
    player: Any,
    completed: Set[str],
) -> Tuple[bool, str]:
    """Return (ok, reason_if_not)."""
    if b.id in completed:
        return False, "Already built."
    if not _requirements_met(b, completed):
        return False, "Requires other buildings first."
    if not player.has_materials(b.materials):
        return False, "Not enough materials."
    if getattr(player, "gold", 0) < b.gold:
        return False, "Not enough gold."
    return True, ""


def try_build(
    b: BuildingDef,
    player: Any,
    completed: Set[str],
) -> Tuple[bool, str]:
    """
    Spend resources and register the building. Mutates player and completed.
    Returns (success, message_for_hud).
    """
    ok, reason = can_build(b, player, completed)
    if not ok:
        return False, reason
    if not player.spend_materials(b.materials):
        return False, "Not enough materials."
    player.gold -= b.gold
    completed.add(b.id)
    return True, f"Built: {b.name}! {b.description}"


# When a building completes, open these tiles (walkable floor) for a simple “town grew” feel.
_BUILDING_FOOTPRINTS: Dict[str, List[Tuple[int, int]]] = {
    "herbalist_hut": [(12, 20)],
    "inn": [(18, 20)],
    "shrine": [(14, 21)],
    "guild_hall": [(16, 21)],
}

_BUILDING_TILE_MAP: Dict[str, int] = {
    "herbalist_hut": TILE_HERBALIST,
    "inn": TILE_INN,
    "shrine": TILE_SHRINE,
    "guild_hall": TILE_GUILD,
}


def apply_completed_building_tiles(grid: List[List[int]], completed: Set[str]) -> None:
    w, h = len(grid), len(grid[0]) if grid else 0
    for bid, cells in _BUILDING_FOOTPRINTS.items():
        if bid not in completed:
            continue
        for i, (tx, ty) in enumerate(cells):
            if 0 <= tx < w and 0 <= ty < h:
                if i == 0 and bid in _BUILDING_TILE_MAP:
                    grid[tx][ty] = _BUILDING_TILE_MAP[bid]
                else:
                    grid[tx][ty] = TILE_FLOOR


def ensure_town_walkable_for_buildings(grid: List[List[int]], width: int, height: int) -> None:
    """North path from the town square and a small yard for plot + future sites."""
    # Corridor north of the 6x6 square (x 12-17, y 12-17): open y=18-21 at x=13-17
    for y in range(18, min(22, height)):
        for x in range(13, min(18, width)):
            if grid[x][y] == 0:
                grid[x][y] = TILE_FLOOR
