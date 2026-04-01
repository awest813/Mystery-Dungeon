"""
Phase 15 - Home System.

Player house with furniture placement, storage chest, decoration,
and a cozy interior that grows with the player's progress.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from panda3d.core import NodePath


FURNITURE_DEFS: Dict[str, dict] = {
    "bed": {
        "name": "Cozy Bed",
        "description": "Restores HP when sleeping.",
        "size": (2, 1),
        "color": (0.6, 0.4, 0.3, 1),
        "effect": "restore_hp",
    },
    "table": {
        "name": "Wooden Table",
        "description": "A place to display items.",
        "size": (1, 1),
        "color": (0.5, 0.35, 0.2, 1),
        "effect": None,
    },
    "shelf": {
        "name": "Display Shelf",
        "description": "Shows off trophies and rare items.",
        "size": (1, 0.5),
        "color": (0.4, 0.3, 0.15, 1),
        "effect": "display",
    },
    "rug": {
        "name": "Woven Rug",
        "description": "Adds warmth to the room.",
        "size": (2, 2),
        "color": (0.7, 0.5, 0.3, 1),
        "effect": "comfort",
    },
    "lantern": {
        "name": "Hanging Lantern",
        "description": "Provides warm light.",
        "size": (0.3, 0.3),
        "color": (1.0, 0.8, 0.3, 1),
        "effect": "light",
    },
    "plant": {
        "name": "Potted Plant",
        "description": "A touch of nature indoors.",
        "size": (0.4, 0.4),
        "color": (0.3, 0.6, 0.2, 1),
        "effect": "comfort",
    },
    "chest": {
        "name": "Storage Chest",
        "description": "Stores extra items and materials.",
        "size": (1, 0.6),
        "color": (0.5, 0.35, 0.2, 1),
        "effect": "storage",
    },
    "trophy": {
        "name": "Boss Trophy",
        "description": "Proof of defeating the Abyssal King.",
        "size": (0.3, 0.3),
        "color": (1.0, 0.8, 0.0, 1),
        "effect": "display",
        "unlock": "boss_defeated",
    },
}


@dataclass
class PlacedFurniture:
    furniture_id: str
    x: float
    y: float
    rotation: float = 0.0
    node: Optional[NodePath] = None


class HomeSystem:
    """Manages the player's house interior, furniture, and storage."""

    def __init__(self):
        self.furniture: List[PlacedFurniture] = []
        self.storage_items: List[dict] = []
        self.storage_materials: Dict[str, int] = {}
        self._root: Optional[NodePath] = None
        self._is_visible = False

    def place_furniture(self, furniture_id: str, x: float, y: float, rotation: float = 0.0) -> bool:
        """Place a piece of furniture. Returns False if invalid or overlapping."""
        if furniture_id not in FURNITURE_DEFS:
            return False

        # Check bounds (house is 4x4 tiles)
        if not (0 <= x <= 4 and 0 <= y <= 4):
            return False

        # Check overlap
        fdef = FURNITURE_DEFS[furniture_id]
        fw, fh = fdef["size"]
        for placed in self.furniture:
            pdef = FURNITURE_DEFS.get(placed.furniture_id, {})
            pw, ph = pdef.get("size", (1, 1))
            if (abs(placed.x - x) < (fw + pw) / 2 and
                    abs(placed.y - y) < (fh + ph) / 2):
                return False

        pf = PlacedFurniture(furniture_id, x, y, rotation)
        self.furniture.append(pf)
        return True

    def remove_furniture(self, index: int) -> Optional[PlacedFurniture]:
        if 0 <= index < len(self.furniture):
            removed = self.furniture.pop(index)
            if removed.node:
                removed.node.removeNode()
            return removed
        return None

    def add_to_storage(self, item_data: dict):
        self.storage_items.append(item_data)

    def remove_from_storage(self, index: int) -> Optional[dict]:
        if 0 <= index < len(self.storage_items):
            return self.storage_items.pop(index)
        return None

    def add_material_to_storage(self, mat: str, count: int):
        self.storage_materials[mat] = self.storage_materials.get(mat, 0) + count

    def take_material_from_storage(self, mat: str, count: int) -> bool:
        if self.storage_materials.get(mat, 0) >= count:
            self.storage_materials[mat] -= count
            return True
        return False

    def build_visuals(self, parent):
        """Build 3D visuals for all placed furniture."""
        from panda3d.core import NodePath as PNodePath, CardMaker
        self._root = PNodePath("house_interior")
        self._root.reparentTo(parent)

        # Floor
        cm = CardMaker("house_floor")
        cm.setFrame(-2.5, 2.5, -2.5, 2.5)
        floor = self._root.attachNewNode(cm.generate())
        floor.setP(-90)
        floor.setZ(0)
        floor.setColor(0.35, 0.28, 0.2, 1)

        # Walls
        for heading, px, py in [(0, 0, 2.5), (180, 0, -2.5), (90, 2.5, 0), (270, -2.5, 0)]:
            cm = CardMaker(f"house_wall_{heading}")
            cm.setFrame(-2.5, 2.5, 0, 2.5)
            wall = self._root.attachNewNode(cm.generate())
            wall.setH(heading)
            wall.setPos(px, py, 0)
            wall.setColor(0.45, 0.38, 0.3, 1)

        # Furniture
        for pf in self.furniture:
            fdef = FURNITURE_DEFS[pf.furniture_id]
            fw, fh = fdef["size"]
            cm = CardMaker(f"furniture_{pf.furniture_id}")
            cm.setFrame(-fw / 2, fw / 2, -fh / 2, fh / 2)
            node = self._root.attachNewNode(cm.generate())
            node.setP(-90)
            node.setPos(pf.x - 2, pf.y - 2, 0.05)
            node.setH(pf.rotation)
            node.setColor(*fdef["color"])
            pf.node = node

    def show(self):
        if self._root:
            self._root.show()
            self._is_visible = True

    def hide(self):
        if self._root:
            self._root.hide()
            self._is_visible = False

    def clear(self):
        if self._root:
            self._root.removeNode()
            self._root = None
        self.furniture = []
        self._is_visible = False

    def to_dict(self) -> dict:
        return {
            "furniture": [
                {"id": f.furniture_id, "x": f.x, "y": f.y, "rotation": f.rotation}
                for f in self.furniture
            ],
            "storage_items": self.storage_items,
            "storage_materials": self.storage_materials,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HomeSystem":
        home = cls()
        for fd in data.get("furniture", []):
            home.furniture.append(PlacedFurniture(
                furniture_id=fd["id"],
                x=fd["x"],
                y=fd["y"],
                rotation=fd.get("rotation", 0),
            ))
        home.storage_items = data.get("storage_items", [])
        home.storage_materials = data.get("storage_materials", {})
        return home
