"""
Phase 14 - Risk & Reward System.

Push-your-luck mechanics: cursed altars, floor modifiers, gamble orbs,
blessed/cursed floor events that let players choose between safety and power.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FloorModifier:
    id: str
    name: str
    description: str
    positive_effects: Dict[str, int]
    negative_effects: Dict[str, int]
    is_active: bool = True


# ------------------------------------------------------------------ #
#  Floor Modifier Pool                                                 #
# ------------------------------------------------------------------ #

FLOOR_MODIFIERS: Dict[str, FloorModifier] = {
    "double_edged": FloorModifier(
        "double_edged", "Double-Edged Floor",
        "All damage dealt and received is doubled.",
        {"dmg_dealt_mult": 200},
        {"dmg_taken_mult": 200},
    ),
    "glass_cannon": FloorModifier(
        "glass_cannon", "Glass Cannon",
        "+50% ATK, -50% DEF.",
        {"atk_bonus_pct": 50},
        {"def_penalty_pct": 50},
    ),
    "starving": FloorModifier(
        "starving", "Starving Floor",
        "Hunger drains 2x faster, but gold drops 2x.",
        {},
        {"hunger_mult": 200, "gold_mult": 200},
    ),
    "blessed_ground": FloorModifier(
        "blessed_ground", "Blessed Ground",
        "All healing is doubled, but enemies are aggressive.",
        {"heal_mult": 200},
        {"enemy_aggro": 100},
    ),
    "cursed_ground": FloorModifier(
        "cursed_ground", "Cursed Ground",
        "Random status on move, but item drops are rare+.",
        {},
        {"random_status": 10},
    ),
    "heavy_gravity": FloorModifier(
        "heavy_gravity", "Heavy Gravity",
        "Movement costs double PP for skills.",
        {},
        {"skill_pp_mult": 200},
    ),
    "lucky_floor": FloorModifier(
        "lucky_floor", "Lucky Floor",
        "+25% crit chance, +25% enemy crit chance.",
        {"crit_bonus": 25},
        {"enemy_crit_bonus": 25},
    ),
}


# ------------------------------------------------------------------ #
#  Risk Choices (Altar / Event)                                        #
# ------------------------------------------------------------------ #

RISK_CHOICES: Dict[str, dict] = {
    "cursed_altar": {
        "name": "Cursed Altar",
        "description": "An altar pulses with dark energy. Make a choice.",
        "choices": [
            {
                "label": "Accept the Curse",
                "description": "-20% max HP, +50% gold drops this floor",
                "effects": {"max_hp_pct": -20, "gold_mult": 150},
            },
            {
                "label": "Defy the Curse",
                "description": "No effect, but altar shatters (may anger dungeon)",
                "effects": {},
            },
            {
                "label": "Bless the Altar",
                "description": "Costs 50 gold. +20% max HP, normal drops",
                "effects": {"max_hp_pct": 20, "gold_cost": 50},
            },
        ],
    },
    "mystery_portal": {
        "name": "Mystery Portal",
        "description": "A swirling portal. Where does it lead?",
        "choices": [
            {
                "label": "Enter the Portal",
                "description": "Skip to next floor, but lose 1 random item",
                "effects": {"skip_floor": True, "lose_item": 1},
            },
            {
                "label": "Ignore the Portal",
                "description": "Nothing happens. Safe choice.",
                "effects": {},
            },
            {
                "label": "Seal the Portal",
                "description": "Costs 30 gold. Gain a rare item next floor.",
                "effects": {"gold_cost": 30, "rare_item_next": True},
            },
        ],
    },
    "traders_cart": {
        "name": "Mysterious Trader",
        "description": "A hooded figure offers a trade.",
        "choices": [
            {
                "label": "Trade HP for Gold",
                "description": "Lose 10 HP, gain 50 gold",
                "effects": {"hp_cost": 10, "gold_gain": 50},
            },
            {
                "label": "Trade Gold for HP",
                "description": "Lose 30 gold, restore 20 HP",
                "effects": {"gold_cost": 30, "hp_gain": 20},
            },
            {
                "label": "Decline",
                "description": "Walk away safely.",
                "effects": {},
            },
        ],
    },
}


class RiskRewardSystem:
    """Manages floor modifiers, risk choices, and push-your-luck events."""

    def __init__(self):
        self.active_modifiers: List[FloorModifier] = []
        self.pending_choice: Optional[dict] = None
        self.risk_level: float = 0.0  # 0.0 = safe, 1.0 = extreme

    def roll_floor_modifier(self, floor_level: int) -> Optional[FloorModifier]:
        """15% chance per floor 5+ to get a floor modifier."""
        if floor_level < 5:
            return None
        if random.random() > 0.15:
            return None

        modifier_id = random.choice(list(FLOOR_MODIFIERS.keys()))
        modifier = FLOOR_MODIFIERS[modifier_id]
        self.active_modifiers.append(modifier)
        return modifier

    def roll_risk_event(self, floor_level: int) -> Optional[dict]:
        """10% chance per floor 3+ to trigger a risk choice event."""
        if floor_level < 3:
            return None
        if random.random() > 0.10:
            return None

        event_id = random.choice(list(RISK_CHOICES.keys()))
        event = RISK_CHOICES[event_id]
        self.pending_choice = dict(event)
        self.pending_choice["id"] = event_id
        return self.pending_choice

    def apply_choice(self, choice_idx: int, player: Any) -> List[str]:
        """Apply a risk choice. Returns messages."""
        if not self.pending_choice:
            return ["No pending choice."]

        choices = self.pending_choice.get("choices", [])
        if choice_idx >= len(choices):
            return ["Invalid choice."]

        choice = choices[choice_idx]
        effects = choice.get("effects", {})
        messages = [f"Chose: {choice['label']}"]

        # Apply effects
        if effects.get("max_hp_pct"):
            bonus = int(player.max_hp * effects["max_hp_pct"] / 100)
            player.max_hp += bonus
            player.hp = min(player.hp + bonus, player.max_hp)
            messages.append(f"  Max HP {'+' if bonus > 0 else ''}{bonus}")

        if effects.get("gold_mult"):
            if not hasattr(player, "gold_bonus_pct"):
                player.gold_bonus_pct = 0
            player.gold_bonus_pct += effects["gold_mult"] - 100

        if effects.get("gold_cost"):
            if player.gold >= effects["gold_cost"]:
                player.gold -= effects["gold_cost"]
                messages.append(f"  Paid {effects['gold_cost']}g")
            else:
                messages.append("  Not enough gold! Choice failed.")

        if effects.get("hp_cost"):
            player.hp = max(1, player.hp - effects["hp_cost"])
            messages.append(f"  Lost {effects['hp_cost']} HP")

        if effects.get("hp_gain"):
            player.hp = min(player.max_hp, player.hp + effects["hp_gain"])
            messages.append(f"  Restored {effects['hp_gain']} HP")

        if effects.get("gold_gain"):
            player.add_gold(effects["gold_gain"])
            messages.append(f"  Gained {effects['gold_gain']}g")

        if effects.get("skip_floor"):
            messages.append("  Portal activated!")

        if effects.get("lose_item"):
            if player.inventory:
                lost = player.inventory.pop(0)
                messages.append(f"  Lost {lost.display_name}")

        self.pending_choice = None
        self.risk_level = min(1.0, self.risk_level + 0.2)
        return messages

    def get_dmg_multiplier(self) -> float:
        mult = 1.0
        for mod in self.active_modifiers:
            mult *= mod.positive_effects.get("dmg_dealt_mult", 100) / 100
        return mult

    def get_dmg_taken_multiplier(self) -> float:
        mult = 1.0
        for mod in self.active_modifiers:
            mult *= mod.negative_effects.get("dmg_taken_mult", 100) / 100
        return mult

    def get_hunger_multiplier(self) -> float:
        mult = 1.0
        for mod in self.active_modifiers:
            mult *= mod.negative_effects.get("hunger_mult", 100) / 100
        return mult

    def get_gold_multiplier(self) -> float:
        mult = 1.0
        for mod in self.active_modifiers:
            mult *= mod.negative_effects.get("gold_mult", 100) / 100
            mult *= mod.positive_effects.get("gold_mult", 100) / 100
        return mult

    def get_heal_multiplier(self) -> float:
        mult = 1.0
        for mod in self.active_modifiers:
            mult *= mod.positive_effects.get("heal_mult", 100) / 100
        return mult

    def clear_floor(self):
        """Clear modifiers between floors."""
        self.active_modifiers = []
        self.pending_choice = None

    def get_active_descriptions(self) -> List[str]:
        return [f"{m.name}: {m.description}" for m in self.active_modifiers]
