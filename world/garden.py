from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CropPlot:
    crop_id: str
    growth_days_needed: int
    growth_days_current: int = 0
    is_watered: bool = False
    yield_item: str = ""
    yield_count: int = 1
    season_bonus: str = ""

    @property
    def is_ready(self) -> bool:
        return self.growth_days_current >= self.growth_days_needed

    def advance_day(self) -> bool:
        """Advance growth by one day. Returns True if it just became ready."""
        days = 2 if self.is_watered else 1
        self.is_watered = False
        self.growth_days_current += days
        return self.growth_days_current >= self.growth_days_needed


def _default_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "data", "crops.json")


def load_crop_definitions(path: Optional[str] = None) -> Dict:
    path = path or _default_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {"crops": [], "garden_capacity": 4}
    return raw


def get_crop_defs(path: Optional[str] = None) -> Dict[str, dict]:
    data = load_crop_definitions(path)
    return {c["id"]: c for c in data.get("crops", [])}


def get_garden_capacity(path: Optional[str] = None) -> int:
    data = load_crop_definitions(path)
    return data.get("garden_capacity", 4)


def create_plot(crop_id: str, defs: Dict[str, dict]) -> Optional[CropPlot]:
    cd = defs.get(crop_id)
    if not cd:
        return None
    return CropPlot(
        crop_id=crop_id,
        growth_days_needed=cd["growth_days"],
        yield_item=cd["yield_item"],
        yield_count=cd.get("yield_count", 1),
        season_bonus=cd.get("season_bonus", ""),
    )


def harvest_plot(plot: CropPlot, player: Any) -> bool:
    if not plot.is_ready:
        return False
    from entities.items import Item
    for _ in range(plot.yield_count):
        item = Item(plot.yield_item)
        item.is_identified = True
        if hasattr(player, "pick_up_item"):
            player.pick_up_item(item)
    plot.growth_days_current = 0
    return True


def water_plot(plot: CropPlot) -> None:
    plot.is_watered = True
