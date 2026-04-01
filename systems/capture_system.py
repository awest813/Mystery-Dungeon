"""
Phase 12 - Capture System.
Handles befriend chance and capture mechanics.
"""
import random
from typing import Optional

def calculate_capture_chance(enemy, player, friend_orb_active: bool = False) -> float:
    """Calculates capture chance.
    Base chance: 15%
    HP penalty: Higher HP lowers chance (at 25% HP it's max, at 100% it's 0%)
    Level bonus: +5% per level player is above enemy
    Friend Orb: +50% chance
    Bosses: 0% chance (must be defeated first)
    """
    if getattr(enemy, 'is_boss', False):
        return 0.0

    hp_pct = enemy.hp / max(1, enemy.max_hp)
    if hp_pct > 0.25:
        return 0.0 # Only capture at <= 25% HP

    base_chance = 0.15
    hp_bonus = (0.25 - hp_pct) * 0.4 # up to +10% at 0 HP
    
    # Estimate enemy level from xp_value roughly
    enemy_level = max(1, enemy.xp_value // 2)
    level_diff = player.level - enemy_level
    level_bonus = max(0, level_diff * 0.05)

    orb_bonus = 0.5 if friend_orb_active else 0.0

    chance = base_chance + hp_bonus + level_bonus + orb_bonus
    return min(1.0, chance)

def attempt_capture(enemy, player, friend_orb_active: bool = False) -> bool:
    chance = calculate_capture_chance(enemy, player, friend_orb_active)
    return random.random() < chance
