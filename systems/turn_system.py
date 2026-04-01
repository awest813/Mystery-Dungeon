import random
from world.dungeon_generator import TRAP_TYPES
from entities.type_chart import get_type_multiplier, EFFECTIVENESS_LABELS


class TurnSystem:
    def __init__(self, player, enemies, tilemap, log_callback=None, kill_callback=None,
                 post_enemy_callback=None):
        self.player = player
        self.enemies = enemies
        self.tilemap = tilemap
        self.log_callback = log_callback if log_callback else print
        self.kill_callback = kill_callback
        self.post_enemy_callback = post_enemy_callback
        self.is_player_turn = True

    # ------------------------------------------------------------------ #
    #  Occupancy                                                           #
    # ------------------------------------------------------------------ #

    def get_occupants(self):
        """Returns a set of occupied (x,y) coords."""
        occ = {(self.player.x, self.player.y)}
        for e in self.enemies:
            if not e.is_dead:
                occ.add((e.x, e.y))
        return occ

    def enemy_at(self, x, y):
        for e in self.enemies:
            if not e.is_dead and e.x == x and e.y == y:
                return e
        return None

    # ------------------------------------------------------------------ #
    #  Player turn                                                         #
    # ------------------------------------------------------------------ #

    def process_player_turn(self, action_type, target=None):
        """
        Execute the player's turn.
        action_type: "move" | "attack" | "wait" | "skill"
        Returns True if the turn was consumed.
        """
        if not self.is_player_turn:
            return False

        # Status effects may prevent action
        can_act = self.player.tick_status(self.log_callback)
        if self.player.is_dead:
            return True   # starvation / poison killed player mid-tick

        success = False

        if action_type == "move":
            tx, ty = target
            if not self.tilemap.is_in_bounds(tx, ty):
                return False

            # Collision with enemy → attack instead (no recursion: direct call)
            blocker = self.enemy_at(tx, ty)
            if blocker:
                success = self._do_player_attack(blocker)
                # Attack still ends turn
            elif can_act:
                self.player.move_to(tx, ty)
                success = True

        elif action_type == "attack":
            if can_act:
                enemy = target
                success = self._do_player_attack(enemy)

        elif action_type == "skill":
            if can_act:
                success = self._do_player_skill(target)

        elif action_type == "wait":
            self.log_callback("You rest...")
            success = True

        if success:
            self._end_player_turn()

        return success

    def _do_player_attack(self, enemy):
        """Resolve a basic player melee attack."""
        # Evasion check — enemy may dodge
        evasion = getattr(enemy, 'evasion', 0)
        if evasion > 0 and random.randint(1, 100) <= evasion:
            self.log_callback(f"{enemy.name} evaded your attack!")
            return True

        dmg = self.player.effective_attack

        # Crit chance (Phase 7 affix)
        if self.player.crit_chance > 0 and random.randint(1, 100) <= self.player.crit_chance:
            dmg *= 2
            self.log_callback("Critical hit!")

        # Weapon may apply status on hit (base weapon + independent affix effects)
        weapon = self.player.equipped_weapon
        if weapon:
            if weapon.status_on_hit:
                enemy.apply_status(weapon.status_on_hit, self.log_callback)
            for affix in weapon.affixes:
                if affix.status_on_hit:
                    enemy.apply_status(affix.status_on_hit, self.log_callback)

        # Volatile cursed affix: chance to warp enemy on hit
        if (weapon and weapon.get_affix_stat("warp_on_hit")
                and random.randint(1, 100) <= weapon.get_affix_stat("warp_on_hit")):
            self.log_callback(f"{enemy.name} was warped!")
            enemy.x = max(0, enemy.x + random.randint(-3, 3))
            enemy.y = max(0, enemy.y + random.randint(-3, 3))

        enemy.take_damage(dmg)
        self.log_callback(f"You attack {enemy.name} for {dmg}!")

        # Life steal (Phase 7 affix)
        if self.player.life_steal_pct > 0:
            steal = max(1, int(dmg * self.player.life_steal_pct / 100))
            self.player.heal(steal)

        if enemy.is_dead:
            self.log_callback(f"Defeated {enemy.name}!")
            if self.kill_callback:
                self.kill_callback(enemy)
            leveled = self.player.add_xp(enemy.xp_value)
            if leveled:
                self.log_callback(f"Level UP! Now Lv.{self.player.level} | HP+5 ATK+1")
            gold = enemy.gold_drop()
            # Gold bonus affix (Phase 7)
            if self.player.gold_bonus_pct > 0:
                gold = int(gold * (1 + self.player.gold_bonus_pct / 100))
            self.player.add_gold(gold)
            self.log_callback(f"+{gold} gold.")
            # Material drops (Phase 7)
            mats = enemy.get_material_drops()
            if mats:
                for mat_key, count in mats.items():
                    self.player.add_material(mat_key, count)
                mat_str = ", ".join(f"{c}x {k.replace('_',' ').title()}"
                                    for k, c in mats.items())
                self.log_callback(f"Drops: {mat_str}")
        return True

    def _do_player_skill(self, skill):
        """Resolve a skill use. skill is a Skill object; target resolved by direction."""
        if skill is None or skill.pp <= 0:
            self.log_callback("No PP left for that skill!")
            return False

        # Heal self skill
        if skill.hp_restore_frac > 0:
            heal_amt = int(self.player.max_hp * skill.hp_restore_frac)
            self.player.heal(heal_amt)
            self.log_callback(f"{skill.display}! Restored {heal_amt} HP.")
            skill.use()
            return True

        # --- AoE skill: hit all enemies in range ---
        if skill.aoe:
            targets = [e for e in self.enemies
                       if not e.is_dead
                       and abs(e.x - self.player.x) + abs(e.y - self.player.y) <= skill.range]
            if not targets:
                self.log_callback(f"No targets in range for {skill.display}!")
                return False
            self.log_callback(f"{skill.display}!")
            for e in targets:
                evasion = getattr(e, 'evasion', 0)
                if evasion > 0 and random.randint(1, 100) <= evasion:
                    self.log_callback(f"{e.name} evaded!")
                    continue
                dmg = int(self.player.effective_attack * skill.damage_mult)
                if dmg > 0:
                    e.take_damage(dmg)
                    self.log_callback(f"  {e.name} takes {dmg} dmg!")
                if skill.status_inflict:
                    e.apply_status(skill.status_inflict, self.log_callback)
                if e.is_dead:
                    self.log_callback(f"  Defeated {e.name}!")
                    if self.kill_callback:
                        self.kill_callback(e)
                    leveled = self.player.add_xp(e.xp_value)
                    if leveled:
                        self.log_callback(f"Level UP! Now Lv.{self.player.level}!")
                    gold = e.gold_drop()
                    if self.player.gold_bonus_pct > 0:
                        gold = int(gold * (1 + self.player.gold_bonus_pct / 100))
                    self.player.add_gold(gold)
                    mats = e.get_material_drops()
                    if mats:
                        for mat_key, count in mats.items():
                            self.player.add_material(mat_key, count)
                        mat_str = ", ".join(f"{c}x {k.replace('_',' ').title()}"
                                            for k, c in mats.items())
                        self.log_callback(f"  Drops: {mat_str}")
            skill.use()
            return True

        # Find target: closest enemy within range
        best_enemy = None
        best_dist = skill.range + 1
        for e in self.enemies:
            if e.is_dead:
                continue
            dist = abs(e.x - self.player.x) + abs(e.y - self.player.y)
            if dist <= skill.range and dist < best_dist:
                best_dist = dist
                best_enemy = e

        if best_enemy is None:
            self.log_callback(f"No target in range for {skill.display}!")
            return False

        # Evasion check for single-target skills
        evasion = getattr(best_enemy, 'evasion', 0)
        if evasion > 0 and random.randint(1, 100) <= evasion:
            self.log_callback(f"{best_enemy.name} evaded {skill.display}!")
            skill.use()
            return True

        dmg = int(self.player.effective_attack * skill.damage_mult)

        # Type effectiveness
        if dmg > 0 and skill.element:
            enemy_elem = getattr(best_enemy, 'element_type', None)
            mult = get_type_multiplier(skill.element, enemy_elem)
            if mult != 1.0:
                dmg = max(1, int(dmg * mult))
                label = EFFECTIVENESS_LABELS.get(mult)
                if label:
                    self.log_callback(label)

        if dmg > 0:
            best_enemy.take_damage(dmg)
            self.log_callback(f"{skill.display}! {best_enemy.name} takes {dmg} dmg!")
        if skill.status_inflict:
            best_enemy.apply_status(skill.status_inflict, self.log_callback)
        if skill.push:
            # Push enemy one tile away
            dx = best_enemy.x - self.player.x
            dy = best_enemy.y - self.player.y
            nx = best_enemy.x + (1 if dx > 0 else (-1 if dx < 0 else 0))
            ny = best_enemy.y + (1 if dy > 0 else (-1 if dy < 0 else 0))
            if self.tilemap.is_walkable(nx, ny) and not self.enemy_at(nx, ny):
                best_enemy.move_to(nx, ny)
                self.log_callback(f"{best_enemy.name} was pushed back!")

        if best_enemy.is_dead:
            self.log_callback(f"Defeated {best_enemy.name}!")
            if self.kill_callback:
                self.kill_callback(best_enemy)
            leveled = self.player.add_xp(best_enemy.xp_value)
            if leveled:
                self.log_callback(f"Level UP! Now Lv.{self.player.level}!")
            gold = best_enemy.gold_drop()
            if self.player.gold_bonus_pct > 0:
                gold = int(gold * (1 + self.player.gold_bonus_pct / 100))
            self.player.add_gold(gold)
            # Material drops (Phase 7)
            mats = best_enemy.get_material_drops()
            if mats:
                for mat_key, count in mats.items():
                    self.player.add_material(mat_key, count)
                mat_str = ", ".join(f"{c}x {k.replace('_',' ').title()}"
                                    for k, c in mats.items())
                self.log_callback(f"Drops: {mat_str}")

        skill.use()
        return True

    def _end_player_turn(self):
        """Consume hunger, apply terrain effects, then run enemy turns."""
        # Hunger drain (reduced by hunger_save_pct affix – Phase 7)
        save_pct = getattr(self.player, 'hunger_save_pct', 0)
        hunger_cost = 0.6 * (1.0 - save_pct / 100.0)
        self.player.hunger -= hunger_cost
        if self.player.hunger <= 0:
            self.player.hunger = 0
            self.player.take_damage(1)
            self.log_callback("Starving! Took 1 HP damage.")

        # Cursed weapon HP drain per turn (Phase 7)
        drain = getattr(self.player, 'hp_drain_per_turn', 0)
        if drain > 0:
            self.player.take_damage(drain)
            self.log_callback(f"Cursed weapon drains {drain} HP!")

        # Lava terrain damage (FF Tactics / Diablo hazard)
        if self.tilemap.is_lava(self.player.x, self.player.y):
            dmg = max(1, self.player.max_hp // 10)
            self.player.take_damage(dmg)
            self.log_callback(f"Lava! Took {dmg} damage!")

        # Water terrain – could slow but we just notify
        if self.tilemap.is_water(self.player.x, self.player.y):
            self.log_callback("Wading through water...")

        self.is_player_turn = False
        self.resolve_enemies()
        self.is_player_turn = True

    # ------------------------------------------------------------------ #
    #  Trap resolution (called from app.py on step)                       #
    # ------------------------------------------------------------------ #

    def trigger_trap(self, x, y):
        """Called when player steps on a TRAP tile."""
        self.tilemap.reveal_trap(x, y)
        trap_type = random.choice(TRAP_TYPES)
        if trap_type == "spike":
            dmg = random.randint(3, 8)
            self.player.take_damage(dmg)
            self.log_callback(f"Spike trap! -{dmg} HP!")
        elif trap_type == "sleep":
            self.player.apply_status("asleep", self.log_callback)
        elif trap_type == "warp":
            self.log_callback("Warp trap! Teleported!")
            return "warp"   # caller handles repositioning
        elif trap_type == "poison":
            self.player.apply_status("poisoned", self.log_callback)
        elif trap_type == "hunger":
            self.player.hunger = max(0, self.player.hunger - 20)
            self.log_callback("Hunger trap! -20 Hunger!")
        return trap_type

    # ------------------------------------------------------------------ #
    #  Enemy turns                                                         #
    # ------------------------------------------------------------------ #

    def resolve_enemies(self):
        """Run AI for all living enemies."""
        for enemy in self.enemies:
            if enemy.is_dead:
                continue

            # Status effects tick for enemy
            can_act = enemy.tick_status(self.log_callback)
            if enemy.is_dead:
                continue
            if not can_act:
                continue

            occupants = self.get_occupants()
            action, tgt = enemy.decide_action(
                self.player.x, self.player.y, occupants, self.tilemap
            )

            if action == "move":
                tx, ty = tgt
                # Fixed bug: check bounds AND walkability
                if self.tilemap.is_in_bounds(tx, ty) and self.tilemap.is_walkable(tx, ty):
                    enemy.move_to(tx, ty)

            elif action == "attack":
                dmg = enemy.attack_power
                # Damage reduction from guard affix (Phase 7)
                reduce_pct = getattr(self.player, 'dmg_reduce_pct', 0)
                if reduce_pct > 0:
                    dmg = max(1, int(dmg * (1.0 - reduce_pct / 100.0)))
                self.player.take_damage(dmg)
                self.log_callback(f"{enemy.name} hits you for {dmg}!")
                # Enemy status-on-hit
                if enemy.status_on_hit:
                    self.player.apply_status(enemy.status_on_hit, self.log_callback)

        if self.player.is_dead:
            self.log_callback("DEFEATED. Rescued to Town...")

        if self.post_enemy_callback:
            self.post_enemy_callback()
