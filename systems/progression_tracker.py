"""
Phase 14 - Progression Tracker.

Unifies XP, town reputation, companion bonds, monster loyalty,
and skill mastery into a single cohesive progression system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProgressNode:
    """A single node in a progression tree."""
    id: str
    name: str
    description: str
    xp_required: int
    is_unlocked: bool = False
    parent_id: Optional[str] = None


PROGRESSION_TREE: Dict[str, ProgressNode] = {
    "combat_basics": ProgressNode("combat_basics", "Combat Basics", "Learn basic combat.", 0, True),
    "status_expert": ProgressNode("status_expert", "Status Expert", "Status effects last 1 turn longer.", 200, False, "combat_basics"),
    "synergy_master": ProgressNode("synergy_master", "Synergy Master", "Synergy damage +50%.", 500, False, "status_expert"),
    "team_leader": ProgressNode("team_leader", "Team Leader", "Deploy 3 allies instead of 2.", 400, False, "combat_basics"),
    "ranch_hand": ProgressNode("ranch_hand", "Ranch Hand", "Ranch produces +1 material per day.", 150, False),
    "ranch_master": ProgressNode("ranch_master", "Ranch Master", "Ranch produces +2 materials, evolves cost -1 item.", 400, False, "ranch_hand"),
    "town_hero": ProgressNode("town_hero", "Town Hero", "Building costs -20%.", 300, False),
    "town_legend": ProgressNode("town_legend", "Town Legend", "Building costs -40%.", 600, False, "town_hero"),
    "monster_whisperer": ProgressNode("monster_whisperer", "Monster Whisperer", "Capture chance +20%.", 350, False, "ranch_hand"),
    "dungeon_veteran": ProgressNode("dungeon_veteran", "Dungeon Veteran", "Start each floor at full HP.", 500, False, "combat_basics"),
}


class ProgressionTracker:
    """Tracks unified progression across all systems."""

    def __init__(self):
        self.total_xp = 0
        self.town_reputation = 0        # 0-100, affects shop prices and building costs
        self.companion_bonds: Dict[str, int] = {}  # companion_id -> bond_level (0-10)
        self.monster_loyalty: Dict[str, int] = {}  # monster_id -> loyalty (0-10)
        self.skill_mastery: Dict[str, int] = {}    # skill_key -> mastery_level (0-5)
        self.unlocked_nodes: set = {"combat_basics"}
        self.milestones: List[str] = []

    def add_xp(self, amount: int) -> List[str]:
        """Add XP and check for unlocks. Returns list of new unlocks."""
        self.total_xp += amount
        new_unlocks = []

        for node_id, node in PROGRESSION_TREE.items():
            if node.is_unlocked:
                continue
            if node.parent_id and node.parent_id not in self.unlocked_nodes:
                continue
            if self.total_xp >= node.xp_required:
                node.is_unlocked = True
                self.unlocked_nodes.add(node_id)
                new_unlocks.append(node.name)
                self.milestones.append(f"Unlocked: {node.name}!")

        return new_unlocks

    def add_town_rep(self, amount: int):
        """Add town reputation."""
        self.town_reputation = min(100, max(0, self.town_reputation + amount))

    def get_building_discount(self) -> float:
        """Returns discount multiplier based on town progression."""
        if "town_legend" in self.unlocked_nodes:
            return 0.6
        if "town_hero" in self.unlocked_nodes:
            return 0.8
        return 1.0

    def get_capture_bonus(self) -> int:
        """Returns capture chance bonus from progression."""
        if "monster_whisperer" in self.unlocked_nodes:
            return 20
        return 0

    def get_synergy_bonus(self) -> float:
        """Returns synergy damage multiplier."""
        if "synergy_master" in self.unlocked_nodes:
            return 1.5
        return 1.0

    def get_deploy_limit(self) -> int:
        """Returns max deployable allies."""
        if "team_leader" in self.unlocked_nodes:
            return 3
        return 2

    def get_ranch_bonus(self) -> int:
        """Returns extra materials from ranch."""
        if "ranch_master" in self.unlocked_nodes:
            return 2
        if "ranch_hand" in self.unlocked_nodes:
            return 1
        return 0

    def get_full_hp_start(self) -> bool:
        """Returns whether player starts each floor at full HP."""
        return "dungeon_veteran" in self.unlocked_nodes

    def get_status_duration_bonus(self) -> int:
        """Returns extra turns for status effects."""
        if "status_expert" in self.unlocked_nodes:
            return 1
        return 0

    def add_companion_bond(self, companion_id: str, amount: int):
        current = self.companion_bonds.get(companion_id, 0)
        self.companion_bonds[companion_id] = min(10, current + amount)

    def add_monster_loyalty(self, monster_id: str, amount: int):
        current = self.monster_loyalty.get(monster_id, 0)
        self.monster_loyalty[monster_id] = min(10, current + amount)

    def add_skill_mastery(self, skill_key: str, amount: int):
        current = self.skill_mastery.get(skill_key, 0)
        self.skill_mastery[skill_key] = min(5, current + amount)

    def to_dict(self) -> dict:
        return {
            "total_xp": self.total_xp,
            "town_reputation": self.town_reputation,
            "companion_bonds": self.companion_bonds,
            "monster_loyalty": self.monster_loyalty,
            "skill_mastery": self.skill_mastery,
            "unlocked_nodes": sorted(self.unlocked_nodes),
            "milestones": self.milestones[-10:],  # Keep last 10
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressionTracker":
        tracker = cls()
        tracker.total_xp = data.get("total_xp", 0)
        tracker.town_reputation = data.get("town_reputation", 0)
        tracker.companion_bonds = data.get("companion_bonds", {})
        tracker.monster_loyalty = data.get("monster_loyalty", {})
        tracker.skill_mastery = data.get("skill_mastery", {})
        tracker.unlocked_nodes = set(data.get("unlocked_nodes", ["combat_basics"]))
        tracker.milestones = data.get("milestones", [])

        # Restore node states
        for node_id in tracker.unlocked_nodes:
            if node_id in PROGRESSION_TREE:
                PROGRESSION_TREE[node_id].is_unlocked = True

        return tracker
