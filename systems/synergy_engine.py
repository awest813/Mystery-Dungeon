"""
Phase 14 - Synergy Engine.

Connects all combat, status, affix, skill, and team systems into
meaningful combos that reward strategic play.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ------------------------------------------------------------------ #
#  Status Combo Definitions                                            #
# ------------------------------------------------------------------ #

STATUS_COMBOS: Dict[str, dict] = {
    "burn_poison": {
        "statuses": ["burn", "poisoned"],
        "name": "Withering",
        "effect": "dmg_over_time",
        "value": 3,
        "description": "Burn + Poison: Target takes 3 extra damage per turn.",
    },
    "burn_paralyzed": {
        "statuses": ["burn", "paralyzed"],
        "name": "Overload",
        "effect": "bonus_dmg",
        "value": 5,
        "description": "Burn + Paralyzed: Next hit deals +5 damage.",
    },
    "poison_sleep": {
        "statuses": ["poisoned", "asleep"],
        "name": "Nightmare",
        "effect": "bonus_dmg",
        "value": 8,
        "description": "Poison + Sleep: Next hit deals +8 damage.",
    },
    "confused_burn": {
        "statuses": ["confused", "burn"],
        "name": "Delirium",
        "effect": "self_dmg",
        "value": 2,
        "description": "Confused + Burn: Target takes 2 self-damage each turn.",
    },
    "paralyzed_frozen": {
        "statuses": ["paralyzed", "frozen"],
        "name": "Shatter",
        "effect": "bonus_dmg",
        "value": 10,
        "description": "Paralyzed + Frozen: Next hit deals +10 damage.",
    },
}


# ------------------------------------------------------------------ #
#  Affix Synergy Definitions                                           #
# ------------------------------------------------------------------ #

AFFIX_SYNERGIES: Dict[str, dict] = {
    "fiery_leeching": {
        "affixes": ["fiery", "leeching"],
        "name": "Bloodfire",
        "effect": "life_steal_on_burn",
        "value": 5,
        "description": "Fiery + Leeching: Heal 5 HP when burning a target.",
    },
    "freezing_crit": {
        "affixes": ["freezing", "crit"],
        "name": "Frostbite",
        "effect": "crit_on_freeze",
        "value": 15,
        "description": "Freezing + Crit: +15% crit chance vs frozen targets.",
    },
    "guard_thrifty": {
        "affixes": ["guard", "thrifty"],
        "name": "Fortified",
        "effect": "hunger_on_block",
        "value": 5,
        "description": "Guard + Thrifty: Blocking restores 5 hunger.",
    },
    "finder_leeching": {
        "affixes": ["finder", "leeching"],
        "name": "Scavenger",
        "effect": "gold_on_heal",
        "value": 3,
        "description": "Finder + Leeching: Gain 3 gold when healing from lifesteal.",
    },
}


# ------------------------------------------------------------------ #
#  Team Combo Definitions (Player + Companion + Monster)              #
# ------------------------------------------------------------------ #

TEAM_COMBOS: Dict[str, dict] = {
    "lyra_brom": {
        "members": ["lyra", "brom"],
        "name": "Shield & Spell",
        "effect": "atk_buff",
        "value": 3,
        "description": "Lyra + Brom: Brom takes hits while Lyra casts for +3 ATK.",
    },
    "mira_sable": {
        "members": ["mira", "sable"],
        "name": "Shadow Heal",
        "effect": "heal_on_crit",
        "value": 5,
        "description": "Mira + Sable: Sable's crits heal Mira for 5 HP.",
    },
    "finn_lyra": {
        "members": ["finn", "lyra"],
        "name": "Storm Call",
        "effect": "aoe_dmg",
        "value": 4,
        "description": "Finn + Lyra: Every 3rd turn, deal 4 AOE damage.",
    },
    "slime_king_slime": {
        "members": ["slime", "king_slime"],
        "name": "Slime Horde",
        "effect": "spawn_minion",
        "value": 1,
        "description": "Slime + King Slime: Summon a mini-slime ally each floor.",
    },
    "bat_vampire_bat": {
        "members": ["bat", "vampire_bat"],
        "name": "Blood Wings",
        "effect": "life_steal",
        "value": 10,
        "description": "Bat + Vampire Bat: +10% lifesteal for all allies.",
    },
}


# ------------------------------------------------------------------ #
#  Skill Chain Definitions                                             #
# ------------------------------------------------------------------ #

SKILL_CHAINS: Dict[str, dict] = {
    "ember_then_thunder": {
        "sequence": ["Ember", "Thunder"],
        "name": "Storm Blast",
        "effect": "bonus_dmg",
        "value": 10,
        "description": "Ember → Thunder: +10 bonus damage.",
    },
    "ice_shard_then_giga": {
        "sequence": ["Ice Shard", "Giga Impact"],
        "name": "Glacial Crush",
        "effect": "bonus_dmg",
        "value": 15,
        "description": "Ice Shard → Giga Impact: +15 bonus damage.",
    },
    "shadow_claw_then_toxic": {
        "sequence": ["Shadow Claw", "Toxic"],
        "name": "Venom Claw",
        "effect": "poison_plus_dmg",
        "value": 5,
        "description": "Shadow Claw → Toxic: +5 poison damage per turn.",
    },
    "slash_then_headbutt": {
        "sequence": ["Slash", "Headbutt"],
        "name": "Beatdown",
        "effect": "stun_chance",
        "value": 30,
        "description": "Slash → Headbutt: 30% chance to stun.",
    },
}


@dataclass
class ActiveSynergy:
    synergy_id: str
    name: str
    effect: str
    value: int
    description: str
    turns_remaining: int = 0
    is_permanent: bool = True


class SynergyEngine:
    """Detects and applies synergies between statuses, affixes, team members, and skills."""

    def __init__(self):
        self.active_synergies: List[ActiveSynergy] = []
        self._last_skill_used: Optional[str] = None
        self._turn_counter = 0

    # ------------------------------------------------------------------ #
    #  Status Combos                                                       #
    # ------------------------------------------------------------------ #

    def check_status_combos(self, target: Any) -> List[ActiveSynergy]:
        """Check if target's statuses form a combo. Returns triggered synergies."""
        triggered = []
        statuses = set()
        for s in ["burn", "poisoned", "paralyzed", "confused", "asleep", "frozen"]:
            if getattr(target, s, False):
                statuses.add(s)

        for combo_id, combo in STATUS_COMBOS.items():
            if all(s in statuses for s in combo["statuses"]):
                syn = ActiveSynergy(
                    synergy_id=combo_id,
                    name=combo["name"],
                    effect=combo["effect"],
                    value=combo["value"],
                    description=combo["description"],
                )
                if syn not in self.active_synergies:
                    triggered.append(syn)
                    self.active_synergies.append(syn)

        return triggered

    # ------------------------------------------------------------------ #
    #  Affix Synergies                                                     #
    # ------------------------------------------------------------------ #

    def check_affix_synergies(self, weapon: Any) -> List[ActiveSynergy]:
        """Check if weapon's affixes form a synergy."""
        if not weapon or not hasattr(weapon, "affixes"):
            return []

        tags = {a.tag for a in weapon.affixes}
        triggered = []

        for syn_id, syn in AFFIX_SYNERGIES.items():
            if all(a in tags for a in syn["affixes"]):
                syn_obj = ActiveSynergy(
                    synergy_id=syn_id,
                    name=syn["name"],
                    effect=syn["effect"],
                    value=syn["value"],
                    description=syn["description"],
                )
                if syn_obj not in self.active_synergies:
                    triggered.append(syn_obj)
                    self.active_synergies.append(syn_obj)

        return triggered

    # ------------------------------------------------------------------ #
    #  Team Combos                                                         #
    # ------------------------------------------------------------------ #

    def check_team_combos(self, player: Any, companions: list, monsters: list) -> List[ActiveSynergy]:
        """Check if deployed team members form combos."""
        member_ids = set()
        for c in companions:
            if getattr(c, "is_deployed", False):
                member_ids.add(c.companion_id)
        for m in monsters:
            if getattr(m, "is_deployed", False):
                member_ids.add(m.monster_type)

        triggered = []
        for combo_id, combo in TEAM_COMBOS.items():
            if all(m in member_ids for m in combo["members"]):
                syn = ActiveSynergy(
                    synergy_id=combo_id,
                    name=combo["name"],
                    effect=combo["effect"],
                    value=combo["value"],
                    description=combo["description"],
                )
                if syn not in self.active_synergies:
                    triggered.append(syn)
                    self.active_synergies.append(syn)

        return triggered

    # ------------------------------------------------------------------ #
    #  Skill Chains                                                        #
    # ------------------------------------------------------------------ #

    def check_skill_chain(self, skill_name: str) -> Optional[ActiveSynergy]:
        """Check if the current skill continues a chain."""
        if not self._last_skill_used:
            self._last_skill_used = skill_name
            return None

        sequence = (self._last_skill_used, skill_name)
        triggered = None

        for chain_id, chain in SKILL_CHAINS.items():
            if tuple(chain["sequence"]) == sequence:
                triggered = ActiveSynergy(
                    synergy_id=chain_id,
                    name=chain["name"],
                    effect=chain["effect"],
                    value=chain["value"],
                    description=chain["description"],
                    turns_remaining=1,
                )
                break

        self._last_skill_used = skill_name
        return triggered

    # ------------------------------------------------------------------ #
    #  Effect Application                                                  #
    # ------------------------------------------------------------------ #

    def apply_synergy_effects(self, attacker: Any, target: Any, base_damage: int) -> Tuple[int, List[str]]:
        """Apply all active synergy effects to an attack. Returns (modified_damage, messages)."""
        dmg = base_damage
        messages = []

        for syn in self.active_synergies:
            if syn.effect == "bonus_dmg":
                dmg += syn.value
                messages.append(f"  [{syn.name}] +{syn.value} damage!")
            elif syn.effect == "dmg_over_time":
                if hasattr(target, "apply_status"):
                    messages.append(f"  [{syn.name}] +{syn.value} DoT applied!")
            elif syn.effect == "self_dmg":
                if hasattr(target, "take_damage"):
                    target.take_damage(syn.value)
                    messages.append(f"  [{syn.name}] Target takes {syn.value} self-damage!")
            elif syn.effect == "poison_plus_dmg":
                if hasattr(target, "apply_status"):
                    target.apply_status("poisoned", lambda m: None)
                    messages.append(f"  [{syn.name}] Poisoned!")

        return dmg, messages

    def apply_team_synergy_effects(self, player: Any, allies: list) -> List[str]:
        """Apply passive team synergy effects. Returns messages."""
        messages = []
        for syn in self.active_synergies:
            if syn.effect == "atk_buff":
                player.attack_power += syn.value
                messages.append(f"  [{syn.name}] +{syn.value} ATK!")
            elif syn.effect == "life_steal":
                if hasattr(player, "life_steal_pct"):
                    player.life_steal_pct += syn.value
                    messages.append(f"  [{syn.name}] +{syn.value}% lifesteal!")

        return messages

    def tick(self):
        """Advance one turn. Expire temporary synergies."""
        self._turn_counter += 1
        for s in self.active_synergies:
            if s.turns_remaining > 0:
                s.turns_remaining -= 1
        # Keep permanent (0) or still-active (>0); remove expired (was 1, now 0 but was temporary)
        self.active_synergies = [s for s in self.active_synergies if s.turns_remaining != 0 or s.synergy_id in STATUS_COMBOS or s.synergy_id in AFFIX_SYNERGIES or s.synergy_id in TEAM_COMBOS]

    def clear(self):
        """Clear all active synergies."""
        self.active_synergies = []
        self._last_skill_used = None

    def get_active_descriptions(self) -> List[str]:
        return [s.description for s in self.active_synergies]
