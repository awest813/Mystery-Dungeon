"""
Phase 14 - Dungeon Ecology.

Enemies have relationships, food chains, territorial behavior, pack tactics,
and emotional states (fear/aggro) that make the dungeon feel alive.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ------------------------------------------------------------------ #
#  Ecology Definitions                                                 #
# ------------------------------------------------------------------ #

ECOLOGY_DATA: Dict[str, dict] = {
    "slime": {
        "diet": "scavenger",
        "fears": ["bat", "orc"],
        "hunts": [],
        "pack_size": (2, 4),
        "territory_radius": 3,
        "aggression": 0.3,
    },
    "bat": {
        "diet": "predator",
        "fears": ["orc"],
        "hunts": ["slime"],
        "pack_size": (1, 2),
        "territory_radius": 5,
        "aggression": 0.7,
    },
    "goblin": {
        "diet": "omnivore",
        "fears": ["orc", "dark_knight"],
        "hunts": ["slime"],
        "pack_size": (2, 5),
        "territory_radius": 4,
        "aggression": 0.5,
    },
    "ghost": {
        "diet": "spectral",
        "fears": [],
        "hunts": [],
        "pack_size": (1, 1),
        "territory_radius": 6,
        "aggression": 0.4,
    },
    "orc": {
        "diet": "predator",
        "fears": ["dark_knight"],
        "hunts": ["slime", "goblin"],
        "pack_size": (1, 3),
        "territory_radius": 5,
        "aggression": 0.8,
    },
    "fire_imp": {
        "diet": "elemental",
        "fears": ["ice_wisp"],
        "hunts": [],
        "pack_size": (2, 3),
        "territory_radius": 4,
        "aggression": 0.9,
    },
    "ice_wisp": {
        "diet": "elemental",
        "fears": ["fire_imp"],
        "hunts": [],
        "pack_size": (1, 2),
        "territory_radius": 5,
        "aggression": 0.6,
    },
    "dark_knight": {
        "diet": "apex",
        "fears": [],
        "hunts": ["slime", "goblin", "orc", "bat"],
        "pack_size": (1, 1),
        "territory_radius": 8,
        "aggression": 1.0,
    },
}


@dataclass
class EcologyState:
    """Per-enemy ecology state tracked during a dungeon run."""
    enemy_id: str
    enemy_type: str
    fear_level: float = 0.0       # 0.0 = calm, 1.0 = fleeing
    aggro_level: float = 0.5      # 0.0 = passive, 1.0 = hyper-aggressive
    hunger_level: float = 0.5     # 0.0 = full, 1.0 = starving
    territory_center: Tuple[int, int] = (0, 0)
    pack_members: List[str] = field(default_factory=list)
    last_seen_prey: Optional[Tuple[int, int]] = None
    is_fleeing: bool = False
    is_hunting: bool = False

    def update_fear(self, nearby_threats: List[str], nearby_allies: List[str]):
        """Update fear based on nearby entities."""
        eco = ECOLOGY_DATA.get(self.enemy_type, {})
        fears = eco.get("fears", [])
        threat_count = sum(1 for t in nearby_threats if t in fears)
        ally_count = len(nearby_allies)

        if threat_count > 0:
            self.fear_level = min(1.0, self.fear_level + 0.3 * threat_count)
        else:
            self.fear_level = max(0.0, self.fear_level - 0.1)

        self.is_fleeing = self.fear_level > 0.7

        # Pack courage: more allies = less fear
        if ally_count >= 2:
            self.fear_level = max(0.0, self.fear_level - 0.2)

    def update_hunger(self):
        """Hunger increases over time, drives hunting behavior."""
        self.hunger_level = min(1.0, self.hunger_level + 0.05)
        if self.hunger_level > 0.7:
            self.is_hunting = True

    def feed(self):
        """Reset hunger after eating."""
        self.hunger_level = 0.0
        self.is_hunting = False


class DungeonEcology:
    """Manages ecology for all enemies on a floor."""

    def __init__(self):
        self.ecology_states: Dict[str, EcologyState] = {}
        self.food_chain_events: List[str] = []

    def register_enemy(self, enemy: Any) -> EcologyState:
        """Register an enemy with the ecology system."""
        etype = getattr(enemy, "enemy_type", "slime")
        state = EcologyState(
            enemy_id=id(enemy),
            enemy_type=etype,
            territory_center=(enemy.x, enemy.y),
        )
        self.ecology_states[id(enemy)] = state
        return state

    def unregister_enemy(self, enemy: Any):
        eid = id(enemy)
        if eid in self.ecology_states:
            del self.ecology_states[eid]

    def get_nearby_entities(self, enemy: Any, all_enemies: list, radius: int) -> Tuple[List[str], List[str]]:
        """Get types of nearby threats and allies."""
        threats = []
        allies = []
        eco = ECOLOGY_DATA.get(enemy.enemy_type, {})
        fears = eco.get("fears", [])
        hunts = eco.get("hunts", [])

        for other in all_enemies:
            if other is enemy or other.is_dead:
                continue
            dist = abs(other.x - enemy.x) + abs(other.y - enemy.y)
            if dist <= radius:
                other_type = getattr(other, "enemy_type", "")
                if other_type in fears:
                    threats.append(other_type)
                elif other_type in hunts:
                    threats.append(other_type)  # prey counts as "threat" to hunting drive
                elif other_type == enemy.enemy_type:
                    allies.append(other_type)

        return threats, allies

    def update_ecology(self, enemies: list):
        """Update ecology state for all enemies."""
        for enemy in enemies:
            if enemy.is_dead:
                self.unregister_enemy(enemy)
                continue

            eid = id(enemy)
            if eid not in self.ecology_states:
                self.register_enemy(enemy)

            state = self.ecology_states[eid]
            eco = ECOLOGY_DATA.get(enemy.enemy_type, {})
            radius = eco.get("territory_radius", 4)

            threats, allies = self.get_nearby_entities(enemy, enemies, radius)
            state.update_fear(threats, allies)
            state.update_hunger()

            # Check for food chain events
            if state.is_hunting and threats:
                prey_type = threats[0]
                self.food_chain_events.append(
                    f"{enemy.enemy_type.replace('_', ' ').title()} is hunting {prey_type.replace('_', ' ')}!"
                )

    def modify_enemy_behavior(self, enemy: Any, action: str, target: Any) -> Tuple[str, Any]:
        """Modify enemy AI based on ecology state."""
        eid = id(enemy)
        state = self.ecology_states.get(eid)
        if not state:
            return action, target

        # Fleeing behavior overrides everything
        if state.is_fleeing:
            if action == "attack":
                return "move", (enemy.x + random.choice([-1, 1]), enemy.y + random.choice([-1, 1]))

        # Hunting behavior: prioritize prey over player
        if state.is_hunting and state.last_seen_prey:
            px, py = state.last_seen_prey
            dist = abs(px - enemy.x) + abs(py - enemy.y)
            if dist <= 1:
                return "attack", target
            return "move", (px, py)

        # Pack tactics: if allies nearby, be more aggressive
        if len(state.pack_members) >= 2:
            if action == "wait" and random.random() < 0.5:
                return "attack", target

        return action, target

    def on_enemy_killed(self, killer: Any, victim: Any, all_enemies: list):
        """Handle ecology effects when an enemy dies."""
        # Nearby enemies of same type get scared
        victim_type = getattr(victim, "enemy_type", "")
        for enemy in all_enemies:
            if enemy.is_dead or enemy is victim or enemy is killer:
                continue
            dist = abs(enemy.x - victim.x) + abs(enemy.y - victim.y)
            if dist <= 5:
                eid = id(enemy)
                state = self.ecology_states.get(eid)
                if state:
                    state.fear_level = min(1.0, state.fear_level + 0.3)
                    if state.fear_level > 0.7:
                        self.food_chain_events.append(
                            f"{enemy.enemy_type.replace('_', ' ').title()} flees in terror!"
                        )

        # Predator eats prey
        killer_type = getattr(killer, "enemy_type", "")
        killer_eco = ECOLOGY_DATA.get(killer_type, {})
        if victim_type in killer_eco.get("hunts", []):
            state = self.ecology_states.get(id(killer))
            if state:
                state.feed()
                self.food_chain_events.append(
                    f"{killer_type.replace('_', ' ').title()} devours {victim_type.replace('_', ' ')}!"
                )

    def get_floor_events(self) -> List[str]:
        """Get and clear pending ecology events."""
        events = list(self.food_chain_events)
        self.food_chain_events = []
        return events

    def clear(self):
        self.ecology_states = {}
        self.food_chain_events = []
