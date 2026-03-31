from .entity_base import Entity
from .skills import Skill, get_skills_for_level, LEVEL_SKILL_LEARN

# XP needed to reach next level (Diablo/PMD-style curve)
def xp_to_next_level(level):
    return int(20 * (level ** 1.5))

# Stat gains per level (FF Tactics / PMD inspired)
STAT_GAIN_HP     = 5
STAT_GAIN_ATK    = 1


class Player(Entity):
    def __init__(self, x=0, y=0):
        super().__init__("Player", x, y)
        self.visual.setColor(0.3, 0.7, 1.0, 1)   # Hero blue
        self.max_hp = 30
        self.hp = 30
        self.attack_power = 5
        self.level = 1
        self.xp = 0
        self.xp_to_next = xp_to_next_level(1)

        # Resources
        self.max_hunger = 100
        self.hunger = 100
        self.gold = 0
        self.is_dead = False

        # Inventory: list of Item objects (max 10, PMD-style)
        self.inventory = []
        self.max_inventory = 10

        # Equipped weapon: Item | None
        self.equipped_weapon = None
        self._weapon_bonus = 0  # cached attack bonus from weapon

        # Skills: up to 4 (PMD-style), start with Slash
        self.skills = [Skill("slash")]
        self.selected_skill_idx = 0

    # ------------------------------------------------------------------ #
    #  XP / Levelling                                                      #
    # ------------------------------------------------------------------ #

    def add_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self._level_up()
            leveled = True
        return leveled

    def _level_up(self):
        self.level += 1
        self.xp_to_next = xp_to_next_level(self.level)

        # Stat gains
        self.max_hp += STAT_GAIN_HP
        self.hp = min(self.hp + STAT_GAIN_HP, self.max_hp)
        self.attack_power += STAT_GAIN_ATK

        # Learn skill if applicable (PMD: learn moves on level-up)
        if self.level in LEVEL_SKILL_LEARN:
            new_key = LEVEL_SKILL_LEARN[self.level]
            # Check we don't already have it
            existing_keys = [s.key for s in self.skills]
            if new_key not in existing_keys:
                new_skill = Skill(new_key)
                if len(self.skills) < 4:
                    self.skills.append(new_skill)
                else:
                    # Replace oldest (slot 0) – player can manage this
                    self.skills[0] = new_skill

    @property
    def effective_attack(self):
        return self.attack_power + self._weapon_bonus

    # ------------------------------------------------------------------ #
    #  Gold                                                                #
    # ------------------------------------------------------------------ #

    def add_gold(self, amount):
        self.gold += amount

    # ------------------------------------------------------------------ #
    #  Hunger                                                              #
    # ------------------------------------------------------------------ #

    def eat(self, hunger_amount):
        self.hunger = min(self.max_hunger, self.hunger + hunger_amount)

    # ------------------------------------------------------------------ #
    #  Inventory                                                           #
    # ------------------------------------------------------------------ #

    def pick_up_item(self, item):
        """Returns True if item was picked up, False if inventory full."""
        if len(self.inventory) >= self.max_inventory:
            return False
        self.inventory.append(item)
        return True

    def use_item(self, index, log_callback=None):
        """
        Use item at given inventory index.
        Returns True if item was consumed/used.
        """
        if index < 0 or index >= len(self.inventory):
            return False
        item = self.inventory[index]
        used = False

        if item.category == "food":
            self.eat(item.hunger_restore)
            if item.hp_restore:
                actual = min(item.hp_restore, self.max_hp - self.hp)
                self.heal(actual)
            if item.cure_status:
                self.cure_status(item.cure_status)
            if log_callback:
                log_callback(f"You eat the {item.display}.")
            used = True

        elif item.category == "potion":
            restore = min(item.hp_restore, self.max_hp - self.hp)
            self.heal(restore)
            if hasattr(item, 'hunger_restore') and item.hunger_restore:
                self.eat(item.hunger_restore)
            if item.cure_status:
                self.cure_status(item.cure_status)
            if log_callback:
                log_callback(f"You use the {item.display}. +{restore} HP")
            used = True

        elif item.category == "weapon":
            # Unequip current weapon first
            if self.equipped_weapon:
                self.inventory.append(self.equipped_weapon)
            self.equipped_weapon = item
            self._weapon_bonus = item.attack_bonus
            if log_callback:
                log_callback(f"Equipped {item.display}. ATK +{item.attack_bonus}")
            # Remove from inventory and don't mark used=True so we skip pop below
            self.inventory.pop(index)
            return True

        elif item.category == "orb":
            # Orb effects are handled externally by app.py (need world context)
            # Return the item key so caller can resolve the effect
            if log_callback:
                log_callback(f"You use the {item.display}!")
            used = True   # consumed on use; effect resolved by caller

        elif item.category == "key":
            # Keys are used situationally; just return without consuming
            if log_callback:
                log_callback("(Use the key near a sealed door.)")
            return False

        if used:
            self.inventory.pop(index)
        return used

    def drop_item(self, index):
        if 0 <= index < len(self.inventory):
            return self.inventory.pop(index)
        return None

    # ------------------------------------------------------------------ #
    #  Skills                                                              #
    # ------------------------------------------------------------------ #

    @property
    def selected_skill(self):
        if self.skills:
            return self.skills[self.selected_skill_idx % len(self.skills)]
        return None

    def cycle_skill(self, direction=1):
        if self.skills:
            self.selected_skill_idx = (self.selected_skill_idx + direction) % len(self.skills)

    def restore_skill_pp(self):
        for s in self.skills:
            s.restore_pp()

    # ------------------------------------------------------------------ #
    #  Floor entry                                                         #
    # ------------------------------------------------------------------ #

    def on_enter_floor(self):
        """Called when descending to a new floor. Restore some PP (Choco Dungeon style)."""
        for s in self.skills:
            s.pp = min(s.max_pp, s.pp + 3)
