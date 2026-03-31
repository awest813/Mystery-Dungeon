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

        # Phase 7 – Materials & Identification
        self.materials = {}          # {material_key: count}
        self.identified_items = set()  # set of item_keys globally identified this save

        # Phase 7 – Affix-derived combat stats (recalculated on equip/unequip)
        self.crit_chance = 0          # % chance to deal double damage
        self.life_steal_pct = 0       # % of damage dealt restored as HP
        self.dmg_reduce_pct = 0       # % incoming damage reduction
        self.hunger_save_pct = 0      # % hunger drain reduction
        self.gold_bonus_pct = 0       # % extra gold drops
        self.hp_drain_per_turn = 0    # HP lost per turn (cursed)

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
    #  Gold & Materials (Phase 7)                                          #
    # ------------------------------------------------------------------ #

    def add_gold(self, amount):
        self.gold += amount

    def add_material(self, key, amount=1):
        """Add to the player's material stash."""
        self.materials[key] = self.materials.get(key, 0) + amount

    def has_materials(self, cost_dict):
        """Returns True if the player can afford the given material cost."""
        return all(self.materials.get(k, 0) >= v for k, v in cost_dict.items())

    def spend_materials(self, cost_dict):
        """Deduct materials. Returns True on success, False if insufficient."""
        if not self.has_materials(cost_dict):
            return False
        for k, v in cost_dict.items():
            self.materials[k] -= v
        return True

    def materials_summary(self):
        """Return a compact string listing non-zero materials."""
        parts = [f"{v}x {k.replace('_', ' ').title()}"
                 for k, v in sorted(self.materials.items()) if v > 0]
        return ", ".join(parts) if parts else "none"

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
            # Using identifies it
            self.identify_item(item)
            if log_callback:
                log_callback(f"You eat the {item.display_name}.")
            used = True

        elif item.category == "potion":
            restore = min(item.hp_restore, self.max_hp - self.hp)
            self.heal(restore)
            if hasattr(item, 'hunger_restore') and item.hunger_restore:
                self.eat(item.hunger_restore)
            if item.cure_status:
                self.cure_status(item.cure_status)
            # Using identifies it
            self.identify_item(item)
            if log_callback:
                log_callback(f"You use the {item.display_name}. +{restore} HP")
            used = True

        elif item.category == "weapon":
            # Unequip current weapon first (restore affix stats)
            if self.equipped_weapon:
                self._unapply_weapon_affixes(self.equipped_weapon)
                self.inventory.append(self.equipped_weapon)
            self.equipped_weapon = item
            self._weapon_bonus = item.attack_bonus
            self._apply_weapon_affixes(item)
            self.identify_item(item)
            affix_str = (f"  [{', '.join(item.affix_descs())}]"
                         if item.affixes else "")
            if log_callback:
                log_callback(
                    f"Equipped {item.display_name}. ATK +{item.attack_bonus}{affix_str}"
                )
            self.inventory.pop(index)
            return True

        elif item.category == "orb":
            # Orb effects are handled externally by app.py (need world context)
            # Return the item key so caller can resolve the effect
            if log_callback:
                log_callback(f"You use the {item.display_name}!")
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
    #  Phase 7 – Item Identification                                       #
    # ------------------------------------------------------------------ #

    def identify_item(self, item):
        """Mark a single item as identified and remember the type globally."""
        item.is_identified = True
        self.identified_items.add(item.key)

    def identify_inventory(self):
        """
        Identify all items in inventory and equipped slot (called on town return).
        Returns a list of newly-identified item display names.
        """
        newly_identified = []
        all_items = list(self.inventory)
        if self.equipped_weapon:
            all_items.append(self.equipped_weapon)
        for item in all_items:
            if not item.is_identified:
                item.is_identified = True
                self.identified_items.add(item.key)
                newly_identified.append(item.display)
        return newly_identified

    def mark_known_items_identified(self):
        """
        Auto-identify any items in inventory whose type has been seen before.
        Called when picking up a new item.
        """
        for item in self.inventory:
            if item.key in self.identified_items:
                item.is_identified = True

    # ------------------------------------------------------------------ #
    #  Phase 7 – Weapon Affix Application                                  #
    # ------------------------------------------------------------------ #

    def _apply_weapon_affixes(self, weapon):
        """Cache affix-derived stats from the equipped weapon onto the player."""
        self.crit_chance       = weapon.get_affix_stat("crit_chance")
        self.life_steal_pct    = weapon.get_affix_stat("life_steal_pct")
        self.dmg_reduce_pct    = weapon.get_affix_stat("dmg_reduce_pct")
        self.hunger_save_pct   = weapon.get_affix_stat("hunger_save_pct")
        self.gold_bonus_pct    = weapon.get_affix_stat("gold_bonus_pct")
        self.hp_drain_per_turn = weapon.get_affix_stat("hp_drain_per_turn")
        # Bonus HP from hardy affix
        bonus_hp = weapon.get_affix_stat("bonus_max_hp")
        if bonus_hp:
            self.max_hp += bonus_hp
            self.hp = min(self.hp + bonus_hp, self.max_hp)

    def _unapply_weapon_affixes(self, weapon):
        """Remove affix-derived stat bonuses when unequipping."""
        self.crit_chance = 0
        self.life_steal_pct = 0
        self.dmg_reduce_pct = 0
        self.hunger_save_pct = 0
        self.gold_bonus_pct = 0
        self.hp_drain_per_turn = 0
        bonus_hp = weapon.get_affix_stat("bonus_max_hp")
        if bonus_hp:
            self.max_hp = max(1, self.max_hp - bonus_hp)
            self.hp = min(self.hp, self.max_hp)

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
