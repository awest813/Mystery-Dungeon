"""
Phase 10 – Companion AI for dungeon turns.

Companions act after the player, using simple AI to attack nearby enemies
or follow the player. Up to 2 companions can be deployed at once.
"""
from __future__ import annotations

from typing import Any, List, Tuple, Callable


class CompanionAI:
    """Manages turn resolution for deployed companions."""

    def __init__(self, companions: List[Any], log_callback: Callable = None):
        self.companions = companions
        self.log = log_callback or (lambda m: None)

    def resolve_companion_turns(self, player_x: int, player_y: int,
                                enemies: List[Any], tilemap: Any) -> None:
        """Run AI for all deployed companions."""
        for comp in self.companions:
            if not comp.is_deployed or comp.is_dead or comp.hp <= 0:
                continue

            action, target = comp.take_turn(player_x, player_y, enemies, tilemap)

            if action == "attack" and target and not target.is_dead:
                dmg = comp.attack_power
                target.take_damage(dmg)
                self.log(f"{comp.name} attacks {target.name} for {dmg}!")
                if target.is_dead:
                    self.log(f"{comp.name} defeated {target.name}!")

            elif action == "move" and target:
                tx, ty = target
                if tilemap and tilemap.is_walkable(tx, ty):
                    occupied = {(e.x, e.y) for e in enemies if not e.is_dead}
                    occupied.add((player_x, player_y))
                    for c in self.companions:
                        if c is not comp and c.is_deployed:
                            occupied.add((c.x, c.y))
                    if (tx, ty) not in occupied:
                        comp.move_to(tx, ty)

            elif action == "wait":
                pass
