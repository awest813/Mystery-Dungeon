import random

from direct.showbase.ShowBase import ShowBase
import simplepbr

from world.tilemap import TileMap
from world.dungeon_generator import DungeonGenerator
from entities.player import Player
from entities.enemy import Enemy
from entities.items import random_item_for_floor, LootGenerator, get_weapon_affix_pool
from systems.turn_system import TurnSystem
from systems.spawn_system import SpawnSystem
from game.save_manager import SaveManager
from ui.hud import GameHUD
from ui.item_screen import ItemScreen

STATE_TOWN = 0
STATE_DUNGEON = 1

# Number of enemy slots (some may be boss overrides)
ENEMY_COUNT = 10


class MysteryDungeonApp(ShowBase):
    def __init__(self):
        super().__init__()

        simplepbr.init()
        self.setBackgroundColor(0.04, 0.04, 0.06)

        # Systems & Persistence
        self.map = TileMap(30, 30)
        self.map.reparent_to(self.render)
        self.generator = DungeonGenerator(30, 30)
        self.save_mgr = SaveManager()
        self.hud = GameHUD()
        self.item_screen = ItemScreen()   # Phase 7: item inspection overlay

        # Actors
        self.player = Player(0, 0)
        self.player.reparent_to(self.render)

        self.enemies = [Enemy(f"Foe {i}", 0, 0) for i in range(ENEMY_COUNT)]
        for e in self.enemies:
            e.reparent_to(self.render)

        self.spawn_sys = SpawnSystem(self.map, self.player, self.enemies)
        self.turns = TurnSystem(self.player, self.enemies, self.map, self.hud.add_message)

        # State
        self.game_state = STATE_TOWN
        self.floor_level = 0
        self._pending_respawn = False

        # Load saved progress then enter town
        self.save_mgr.load_progress(self.player)
        self.enter_town()

        # ---- Input bindings ----
        # Movement
        self.accept("w", self.input_move, [0, 1])
        self.accept("s", self.input_move, [0, -1])
        self.accept("a", self.input_move, [-1, 0])
        self.accept("d", self.input_move, [1, 0])

        # Wait
        self.accept("space", self._input_wait)

        # Skills: keys 1-4 select+use the corresponding skill slot
        self.accept("1", self._input_skill, [0])
        self.accept("2", self._input_skill, [1])
        self.accept("3", self._input_skill, [2])
        self.accept("4", self._input_skill, [3])

        # Inventory: F = use first item, Z = drop first item, E = print stats/save, I = inspect
        self.accept("f", self._input_use_item)
        self.accept("z", self._input_drop_item)
        self.accept("e", self._input_action)
        self.accept("i", self._input_inspect_item)   # Phase 7: item inspection

        # Game loop
        self.taskMgr.add(self.update_game, "GameLoop")

    # ------------------------------------------------------------------ #
    #  Game loop                                                           #
    # ------------------------------------------------------------------ #

    def update_game(self, task):
        dt = globalClock.getDt()

        self.player.update(dt)
        for e in self.enemies:
            e.update(dt)

        # Smooth camera follow
        target_cam = (self.player.node.getX(), self.player.node.getY() - 12, 18)
        curr_cam = self.camera.getPos()
        new_cam = curr_cam + (target_cam - curr_cam) * min(1.0, 5.0 * dt)
        self.camera.setPos(new_cam)
        self.camera.lookAt(self.player.node.getX(), self.player.node.getY() + 2, 0)

        return task.cont

    # ------------------------------------------------------------------ #
    #  State transitions                                                   #
    # ------------------------------------------------------------------ #

    def enter_town(self):
        self.game_state = STATE_TOWN
        self.floor_level = 0
        self.map.apply_theme("TOWN")

        self.map.grid = [[0 for _ in range(30)] for _ in range(30)]
        for x in range(12, 18):
            for y in range(12, 18):
                self.map.grid[x][y] = 1
        self.map.grid[15][17] = 2   # stairs to dungeon
        # Phase 7: Forge tile at (13, 12) – distinct gold tile
        self.map.grid[13][12] = 8   # TILE_FORGE (handled as floor + special interaction)
        self.map.setup_visuals()
        # Tint the forge tile orange
        forge_node = self.map.visual_nodes.get((13, 12))
        if forge_node:
            forge_node.setColor(0.9, 0.5, 0.1, 1)

        self.player.move_to(15, 14)
        self.player.hp = self.player.max_hp
        self.player.hunger = self.player.max_hunger
        self.player.cure_all_statuses()
        self.player.restore_skill_pp()

        # Phase 7: Auto-identify all items when returning to town
        newly_id = self.player.identify_inventory()
        if newly_id:
            self.hud.add_message(f"Identified: {', '.join(newly_id)}")

        for e in self.enemies:
            e.node.hide()
            e.is_dead = True

        self.hud.update(self.player, in_town=True)
        self.save_mgr.save_progress(self.player)
        self.hud.add_message("Safe in Town. Skills & PP restored.")

    def enter_dungeon(self):
        self.game_state = STATE_DUNGEON
        self.floor_level = 0
        for e in self.enemies:
            e.node.show()
        self.next_floor()

    def next_floor(self):
        self.floor_level += 1

        # Dungeon themes progress (PMD/DQ atmosphere)
        theme_by_floor = {1: "CAVE", 3: "ICE", 6: "FIRE"}
        theme = "CAVE"
        for thr, t in sorted(theme_by_floor.items()):
            if self.floor_level >= thr:
                theme = t
        # Small random variation
        if random.random() < 0.3:
            theme = random.choice(["CAVE", "ICE", "FIRE"])
        self.map.apply_theme(theme)

        grid, rooms = self.generator.generate(
            max_rooms=min(12, 8 + self.floor_level // 2),
            floor_level=self.floor_level
        )
        self.map.grid = grid
        self.map.setup_visuals()

        self.spawn_sys.spawn_from_layout(rooms, self.floor_level)
        self.player.on_enter_floor()

        is_boss = (self.floor_level % 5 == 0 and self.floor_level > 0)
        self.hud.update(self.player, self.floor_level)
        if is_boss:
            self.hud.add_message(f"Floor {self.floor_level} – BOSS APPROACHES!")
        else:
            self.hud.add_message(f"Entering Floor {self.floor_level}...")

    # ------------------------------------------------------------------ #
    #  Post-move tile effects                                              #
    # ------------------------------------------------------------------ #

    def _resolve_tile_effects(self):
        """Called after any player move. Handles pickups, traps, stairs, forge."""
        px, py = self.player.x, self.player.y

        # Forge tile interaction (Phase 7) – show hint when standing on it
        if self.game_state == STATE_TOWN and self.map.grid[px][py] == 8:
            self.hud.add_message("Forge: Press E to enchant weapon or inspect materials.")

        # Item pickup
        if self.map.is_item(px, py):
            # Phase 7: use LootGenerator for rarity + affixes
            item_key = random_item_for_floor(self.floor_level)
            item = LootGenerator.generate(item_key, self.floor_level)
            # Auto-identify if the player has seen this type before
            if item.key in self.player.identified_items:
                item.is_identified = True
            if self.player.pick_up_item(item):
                self.hud.add_message(f"Picked up {item.display_name}!")
            else:
                self.hud.add_message(f"Bag full! Left {item.display_name} behind.")
            self.map.grid[px][py] = 1
            node = self.map.visual_nodes.get((px, py))
            if node:
                theme = TileMap.THEMES[self.map.current_theme]
                node.setColor(*theme["floor"])

        # Trap trigger
        if self.map.is_trap(px, py):
            result = self.turns.trigger_trap(px, py)
            if result == "warp":
                wx, wy = self.spawn_sys.find_random_open_floor()
                self.player.move_to(wx, wy)

        # Lava / water messages handled in TurnSystem._end_player_turn

        # Stairs
        if self.map.is_stairs(px, py):
            if self.game_state == STATE_TOWN:
                self.enter_dungeon()
                return
            else:
                self.next_floor()
                return

        # Sealed door: prompt if player has a key
        # (Keys are directional: handled via move-into-sealed logic below)

        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    # ------------------------------------------------------------------ #
    #  Input handlers                                                      #
    # ------------------------------------------------------------------ #

    def input_move(self, dx, dy):
        if self.player.is_dead:
            if not self._pending_respawn:
                self._pending_respawn = True
                self.taskMgr.doMethodLater(1.5, self._do_respawn, "respawn")
            return

        tx = self.player.x + dx
        ty = self.player.y + dy

        # Sealed door: use key to open if player has one
        if self.map.is_sealed(tx, ty):
            for i, item in enumerate(self.player.inventory):
                if item.category == "key":
                    self.player.inventory.pop(i)
                    self.map.open_sealed(tx, ty)
                    self.hud.add_message("Used Dungeon Key – door opened!")
                    self.hud.update(self.player, self.floor_level)
                    return
            self.hud.add_message("Sealed door! Need a Dungeon Key.")
            return

        if not self.map.is_walkable(tx, ty):
            return

        self.turns.process_player_turn("move", (tx, ty))
        self._resolve_tile_effects()

    def _do_respawn(self, task):
        self._pending_respawn = False
        self.enter_town()
        return task.done

    def _input_wait(self):
        if self.player.is_dead:
            return
        self.turns.process_player_turn("wait")
        self._resolve_tile_effects()

    def _input_skill(self, slot_idx):
        if self.player.is_dead:
            return
        if slot_idx >= len(self.player.skills):
            self.hud.add_message(f"No skill in slot {slot_idx + 1}.")
            return
        self.player.selected_skill_idx = slot_idx
        skill = self.player.skills[slot_idx]
        if self.game_state == STATE_DUNGEON:
            self.turns.process_player_turn("skill", skill)
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _input_use_item(self):
        if self.player.is_dead:
            return
        if not self.player.inventory:
            self.hud.add_message("Inventory is empty.")
            return

        item = self.player.inventory[0]

        # Orbs need special world-level handling
        if item.category == "orb":
            self._resolve_orb_effect(item, 0)
        else:
            used = self.player.use_item(0, self.hud.add_message)
            if used:
                self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _resolve_orb_effect(self, item, inv_idx):
        effect = item.effect
        if effect == "reveal_map":
            # Visually reveal all floor tiles (Orb of Sight – PMD style)
            self.player.identify_item(item)
            self.hud.add_message("Orb of Sight! Floor revealed.")
        elif effect == "confuse_enemies":
            self.player.identify_item(item)
            for e in self.enemies:
                if not e.is_dead:
                    e.apply_status("confused", self.hud.add_message)
        elif effect == "paralyze_enemies":
            self.player.identify_item(item)
            for e in self.enemies:
                if not e.is_dead:
                    e.apply_status("paralyzed", self.hud.add_message)
        elif effect == "escape_dungeon":
            self.player.identify_item(item)
            self.hud.add_message("Escape Orb! Returning to town...")
            self.taskMgr.doMethodLater(0.8, lambda t: (self.enter_town(), t.done)[1],
                                       "escape_orb")
        elif effect == "identify_item":
            # Phase 7: Identify Scroll – identify first unidentified item
            self._resolve_identify_scroll(inv_idx)
            return
        self.player.inventory.pop(inv_idx)
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _resolve_identify_scroll(self, scroll_idx):
        """Use an Identify Scroll to reveal the first unidentified inventory item."""
        unidentified = [(i, item) for i, item in enumerate(self.player.inventory)
                        if not item.is_identified and i != scroll_idx]
        if not unidentified:
            self.hud.add_message("All items are already identified!")
            return
        idx, target = unidentified[0]
        self.player.identify_item(target)
        self.hud.add_message(f"Identified: {target.display_name}")
        if target.affixes:
            self.hud.add_message(f"  Affixes: {', '.join(target.affix_descs())}")
        # Pop the scroll; if it comes after the target, its index shifts down by one
        actual_scroll_idx = scroll_idx - 1 if scroll_idx > idx else scroll_idx
        self.player.inventory.pop(actual_scroll_idx)
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _input_drop_item(self):
        if not self.player.inventory:
            self.hud.add_message("Nothing to drop.")
            return
        dropped = self.player.drop_item(0)
        if dropped:
            self.hud.add_message(f"Dropped {dropped.display_name}.")
            self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _input_inspect_item(self):
        """Phase 7: I key - toggle item inspection overlay for first inventory item."""
        if self.item_screen.is_visible:
            self.item_screen.hide()
            return
        if not self.player.inventory:
            self.hud.add_message("Inventory is empty.")
            return
        self.item_screen.show(self.player.inventory[0])

    def _input_action(self):
        """E key: save/forge in town, print debug stats in dungeon."""
        if self.player.is_dead:
            self.enter_town()
            return
        if self.game_state == STATE_TOWN:
            # Phase 7: If standing on forge tile, show forge menu
            if self.player.x == 13 and self.player.y == 12:
                self._forge_action()
            else:
                self.save_mgr.save_progress(self.player)
                self.hud.add_message("Progress saved.")
        else:
            inv_str = ", ".join(i.display_name for i in self.player.inventory) or "empty"
            self.hud.add_message(
                f"Lv{self.player.level} HP:{int(self.player.hp)} ATK:{self.player.effective_attack}"
            )
            self.hud.add_message(f"Bag: {inv_str}")

    # ------------------------------------------------------------------ #
    #  Phase 7 – Town Forge                                                #
    # ------------------------------------------------------------------ #

    # Forge enchant costs (material_key -> count required)
    _FORGE_ENCHANT_COST = {"iron_ore": 5}
    _FORGE_UPGRADE_COST = {"iron_ore": 3, "dark_crystal": 1}

    def _forge_action(self):
        """
        Simple forge interaction at the town forge tile.
        First call shows the menu; second call (while at forge) performs the action.
        """
        wpn = self.player.equipped_weapon
        mats_str = self.player.materials_summary()
        self.hud.add_message(f"Materials: {mats_str}")

        if wpn is None:
            self.hud.add_message("Forge: Equip a weapon first.")
            return

        can_enchant = self.player.has_materials(self._FORGE_ENCHANT_COST)
        can_upgrade = (wpn.affixes and
                       self.player.has_materials(self._FORGE_UPGRADE_COST))

        if can_enchant and not wpn.affixes:
            # Add a random non-cursed affix to the weapon using the public pool API
            pool = get_weapon_affix_pool(cursed=False)
            if pool:
                tag = random.choice(pool)
                affix = LootGenerator._roll_affix(tag)  # noqa: SLF001
                wpn.affixes.append(affix)
                if affix.stat == "attack_bonus_add":
                    wpn.attack_bonus += affix.value
                    self.player._weapon_bonus = wpn.attack_bonus  # noqa: SLF001
                self.player.spend_materials(self._FORGE_ENCHANT_COST)
                self.player._apply_weapon_affixes(wpn)  # noqa: SLF001
                self.hud.add_message(
                    f"Forged: {wpn.display_name} gained [{affix.desc}]!"
                )
                self.save_mgr.save_progress(self.player)
                return

        if can_upgrade and wpn.affixes:
            # Upgrade first affix magnitude by 1-2
            affix = wpn.affixes[0]
            bonus = random.randint(1, 2)
            old_val = affix.value
            affix.value += bonus
            # Reformat desc using the affix's own template
            affix.desc = affix.desc.replace(str(old_val), str(affix.value), 1)
            if affix.stat == "attack_bonus_add":
                wpn.attack_bonus += bonus
                self.player._weapon_bonus = wpn.attack_bonus  # noqa: SLF001
            self.player.spend_materials(self._FORGE_UPGRADE_COST)
            self.player._apply_weapon_affixes(wpn)  # noqa: SLF001
            self.hud.add_message(
                f"Upgraded: {affix.tag} {old_val} -> {affix.value}"
            )
            self.save_mgr.save_progress(self.player)
            return

        cost_str = ", ".join(f"{v}x {k}" for k, v in self._FORGE_ENCHANT_COST.items())
        self.hud.add_message(
            f"Forge: Need {cost_str} to enchant. "
            f"(Have: {mats_str})"
        )
