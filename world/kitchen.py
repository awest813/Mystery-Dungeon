from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MealBuff:
    stat: str
    value: int
    status_immune: str = ""


@dataclass
class CookingRecipe:
    id: str
    name: str
    description: str
    ingredients: Dict[str, int]
    buff: MealBuff


def _default_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "recipes", "cooking.json")


def load_recipes(path: Optional[str] = None) -> List[CookingRecipe]:
    path = path or _default_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return []
    out: List[CookingRecipe] = []
    for row in raw.get("recipes", []):
        buff_data = row.get("buff", {})
        buff = MealBuff(
            stat=buff_data.get("stat", ""),
            value=buff_data.get("value", 0),
            status_immune=buff_data.get("status_immune", ""),
        )
        out.append(CookingRecipe(
            id=row["id"],
            name=row.get("name", row["id"]),
            description=row.get("description", ""),
            ingredients=dict(row.get("ingredients", {})),
            buff=buff,
        ))
    return out


def can_cook(recipe: CookingRecipe, player: Any) -> bool:
    if not hasattr(player, "materials"):
        return False
    return all(
        player.materials.get(k, 0) >= v for k, v in recipe.ingredients.items()
    )


def cook(recipe: CookingRecipe, player: Any) -> bool:
    if not can_cook(recipe, player):
        return False
    for k, v in recipe.ingredients.items():
        player.materials[k] -= v
    return True
