from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CraftingBlueprint:
    id: str
    name: str
    description: str
    materials: Dict[str, int]
    result_item: str


def _default_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "recipes", "crafting.json")


def load_blueprints(path: Optional[str] = None) -> List[CraftingBlueprint]:
    path = path or _default_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return []
    out: List[CraftingBlueprint] = []
    for row in raw.get("blueprints", []):
        out.append(CraftingBlueprint(
            id=row["id"],
            name=row.get("name", row["id"]),
            description=row.get("description", ""),
            materials=dict(row.get("materials", {})),
            result_item=row.get("result_item", "apple"),
        ))
    return out


def can_craft(bp: CraftingBlueprint, player: Any) -> bool:
    if not hasattr(player, "materials"):
        return False
    if len(getattr(player, "inventory", [])) >= getattr(player, "max_inventory", 10):
        return False
    return all(
        player.materials.get(k, 0) >= v for k, v in bp.materials.items()
    )


def craft(bp: CraftingBlueprint, player: Any, loot_gen=None, floor_level=1) -> bool:
    if not can_craft(bp, player):
        return False
    for k, v in bp.materials.items():
        player.materials[k] -= v
    if loot_gen is not None:
        item = loot_gen.generate(bp.result_item, floor_level)
    else:
        from entities.items import Item
        item = Item(bp.result_item)
        item.is_identified = True
    player.inventory.append(item)
    return True
