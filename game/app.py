import json
import math
import os
import random

from direct.showbase.ShowBase import ShowBase
from panda3d.core import ClockObject

import simplepbr

from world.tilemap import TileMap
from world.dungeon_generator import DungeonGenerator, TILE_FORGE, TILE_TOWN_PLOT, TILE_COMPANION, TILE_GARDEN, TILE_FLOOR, TILE_RANCH
from world import town_builder
from entities.player import Player
from entities.enemy import Enemy
from entities.items import Item, random_item_for_floor, LootGenerator, get_weapon_affix_pool
from systems.turn_system import TurnSystem
from systems.spawn_system import SpawnSystem
from systems.synergy_engine import SynergyEngine
from systems.dungeon_ecology import DungeonEcology
from systems.progression_tracker import ProgressionTracker
from systems.risk_reward import RiskRewardSystem
from systems.equipment_slots import EquipmentSlots
from systems.npc_schedule import NPC, list_npc_ids
from systems.home_system import HomeSystem
from systems.festivals import FestivalSystem
from game.save_manager import SaveManager
from game.calendar import Calendar
from ui.hud import GameHUD
from ui.item_screen import ItemScreen
from ui.companion_screen import CompanionScreen
from ui.main_menu import MainMenu
from ui.pause_menu import PauseMenu
from ui.inventory_screen import InventoryScreen
from ui.death_screen import DeathScreen
from ui.ranch_screen import RanchScreen
from ui.festival_screen import FestivalScreen
from ui.debug_menu import DebugMenu
from render.particles import AmbientParticles
from render.post_process import PostProcess

STATE_TOWN = 0
STATE_DUNGEON = 1

MENU_NONE = 0
MENU_MAIN = 1
MENU_PAUSE = 2
MENU_INVENTORY = 3
MENU_DEATH = 4
MENU_RANCH = 5
MENU_FESTIVAL = 6
MENU_DEBUG = 7

# Number of enemy slots (some may be boss overrides)
ENEMY_COUNT = 10


class MysteryDungeonApp(ShowBase):
    def __init__(self):
        super().__init__()

        simplepbr.init()
        self.setBackgroundColor(0.04, 0.04, 0.06)

        self._setup_scene_lighting()

        # Systems & Persistence
        self.map = TileMap(30, 30)
        self.map.reparent_to(self.render)
        self.generator = DungeonGenerator(30, 30)
        self.save_mgr = SaveManager()
        self.hud = GameHUD()
        self.item_screen = ItemScreen()
        self.companion_screen = CompanionScreen()
        self.ranch_screen = RanchScreen(
            self.render2d,
            on_deploy=self._ranch_deploy,
            on_evolve=self._ranch_evolve,
            on_close=self._ranch_close,
        )
        self.festival_screen = FestivalScreen(
            self.render2d,
            on_participate=self._festival_participate,
            on_skip=self._festival_skip,
            on_close=self._festival_close,
        )
        self.debug_menu = DebugMenu(
            self.render2d,
            on_heal=self._debug_heal,
            on_gold=self._debug_gold,
            on_items=self._debug_items,
            on_village=self._debug_village,
            on_skip=self._debug_skip,
            on_level=self._debug_level,
            on_godmode=self._debug_godmode,
            on_close=self._input_debug,
        )

        # Phase 15: Visual systems
        self._post_process = PostProcess(self)
        self._ambient_particles = None  # Created after first render frame
        self._npc_labels = {}  # NPC name labels

        # Phase 11 – Menus
        self.menu_state = MENU_MAIN
        self.main_menu = MainMenu(
            self.render2d,
            on_new_game=self._on_new_game,
            on_continue=self._on_continue,
            on_options=self._on_options,
            on_exit=self._on_exit,
            on_ngp=self._on_ngp,
        )
        self.pause_menu = PauseMenu(
            self.render2d,
            on_resume=self._on_pause_resume,
            on_inventory=self._on_pause_inventory,
            on_skills=self._on_pause_skills,
            on_save=self._on_pause_save,
            on_quit=self._on_pause_quit,
            on_debug=self._input_debug,
        )
        self.inventory_screen = InventoryScreen(
            self.render2d,
            on_use=self._inv_use,
            on_drop=self._inv_drop,
            on_equip=self._inv_equip,
            on_close=self._inv_close,
        )
        self.death_screen = DeathScreen(
            self.render2d,
            on_rescue=self._on_rescue,
            on_quit=self._on_death_quit,
        )

        # Phase 8 – town construction (data/buildings.json)
        self._building_defs = town_builder.load_building_definitions()
        self._town_build_index = 0
        self._herbalist_index = 0
        self._shrine_index = 0

        # Phase 8 – building service data
        self._herbalist_stock = self._load_json("data", "shop_stock.json", "herbalist_stock")
        self._bounty_defs = self._load_json("data", "bounties.json", "bounties")

        # Phase 9 – cooking, crafting, garden, calendar
        self._cook_index = 0
        self._craft_index = 0
        self._garden_index = 0

        # Actors
        self.player = Player(0, 0)
        self.player.reparent_to(self.render)

        self.enemies = [Enemy(f"Foe {i}", 0, 0) for i in range(ENEMY_COUNT)]
        for e in self.enemies:
            e.reparent_to(self.render)

        self.spawn_sys = SpawnSystem(self.map, self.player, self.enemies)
        self.turns = TurnSystem(self.player, self.enemies, self.map, self.hud.add_message,
                                kill_callback=self._on_enemy_killed,
                                post_enemy_callback=self._resolve_companion_turns)

        # Phase 10: companion AI
        from systems.companion_ai import CompanionAI
        self.companion_ai = CompanionAI(self.player.companions, self.hud.add_message)

        # State
        self.game_state = STATE_TOWN
        self.floor_level = 0
        self._pending_respawn = False

        # Load saved progress
        self.save_mgr.load_progress(self.player)

        # Phase 10: ensure all 5 companions exist
        COMP_IDS = ["lyra", "brom", "mira", "sable", "finn"]
        existing = {c.companion_id for c in self.player.companions}
        for cid in COMP_IDS:
            if cid not in existing:
                from entities.companion import Companion
                self.player.companions.append(Companion(cid))

        # Phase 12: ensure monster roster exists
        if not hasattr(self.player, 'monster_roster') or self.player.monster_roster is None:
            from entities.monster_roster import MonsterRoster
            self.player.monster_roster = MonsterRoster()

        # Phase 13: ensure endless dungeon and NG+ state exist
        if not hasattr(self.player, 'endless_dungeon') or self.player.endless_dungeon is None:
            from systems.endless_dungeon import EndlessDungeon
            self.player.endless_dungeon = EndlessDungeon()
        if not hasattr(self.player, 'ngp_state'):
            self.player.ngp_state = None

        # Phase 14: Core system integrations
        self.synergy = SynergyEngine()
        self.ecology = DungeonEcology()
        self.progression = ProgressionTracker()
        self.risk_reward = RiskRewardSystem()
        self.equipment = EquipmentSlots()

        # Phase 15: Life sim systems
        self.npcs: List[NPC] = []
        self.home = HomeSystem()
        self.festivals = FestivalSystem()
        self._ambient_particles = None  # lazy init when render is ready

        # Link equipment to player
        self.player.equipment = self.equipment
        self.player.synergy = self.synergy
        self.player.progression = self.progression
        self.player.risk_reward = self.risk_reward
        self.player.home = self.home
        self.player.festivals = self.festivals

        self._pending_capture = None
        self._capture_enemy = None
        self._boss_fight_active = False

        # Show main menu first
        self.main_menu.show()
        self.hud.hide()

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
        self.accept("e", self._input_e_key)
        self.accept("i", self._input_inspect_item)   # Phase 7: item inspection
        self.accept("c", self._input_companions)      # Phase 10: companion screen

        # Phase 14: risk event choice keys
        self.accept("1", self._input_risk_choice, [0])
        self.accept("2", self._input_risk_choice, [1])
        self.accept("3", self._input_risk_choice, [2])

        # Phase 15: life sim keys
        self.accept("h", self._input_home)        # H key: enter house
        self.accept("t", self._input_talk_npc)     # T key: talk to nearby NPC
        self.accept("g", self._input_gift_npc)     # G key: gift nearby NPC

        # Phase 11 – Menu keys
        self.accept("escape", self._input_menu)
        self.accept("f1", self._input_debug)
        self.accept("arrow_up", self._input_menu_nav, [-1])
        self.accept("arrow_down", self._input_menu_nav, [1])
        self.accept("enter", self._input_menu_confirm)

        # Game loop
        self.taskMgr.add(self.update_game, "GameLoop")
        self._time_accum = 0.0

    def _setup_scene_lighting(self):
        from panda3d.core import AmbientLight, DirectionalLight
        alight = AmbientLight("scene_ambient")
        alight.setColor((0.35, 0.35, 0.42, 1))
        self._ambient_np = self.render.attachNewNode(alight)
        self.render.setLight(self._ambient_np)

        dlight = DirectionalLight("scene_dir")
        dlight.setColor((0.75, 0.70, 0.65, 1))
        self._dir_np = self.render.attachNewNode(dlight)
        self._dir_np.setHpr(-30, -50, 0)
        self.render.setLight(self._dir_np)

        self.disableMouse()

    # ------------------------------------------------------------------ #
    #  Game loop                                                           #
    # ------------------------------------------------------------------ #

    def update_game(self, task):
        dt = ClockObject.getGlobalClock().getDt()
        self._time_accum += dt

        self.player.update(dt)
        for e in self.enemies:
            e.update(dt)
            if not e.is_dead:
                self._animate_entity(e, dt)

        # Phase 13: check for boss defeat
        if self._boss_fight_active:
            from entities.boss import FinalBoss
            boss = next((e for e in self.enemies if isinstance(e, FinalBoss)), None)
            if boss and boss.is_dead:
                self._on_boss_defeated()

        # Phase 10: update companion visuals
        for c in self.player.companions:
            if c.is_deployed and not c.is_dead:
                c.update(dt)

        # Phase 12: update deployed monster visuals
        for m in self.player.monster_roster.get_deployed():
            if not m.is_dead:
                m.update(dt)

        # Phase 15: update NPCs and particles
        for npc in self.npcs:
            npc.update(dt)
        self._update_npc_labels()
        if self._ambient_particles:
            self._ambient_particles.update(dt)

        px = self.player.node.getX()
        py = self.player.node.getY()

        target_cam = (px - 8, py - 10, 14)
        curr_cam = self.camera.getPos()
        new_cam = curr_cam + (target_cam - curr_cam) * min(1.0, 5.0 * dt)
        self.camera.setPos(new_cam)
        self.camera.lookAt(px + 1, py + 1, 0.5)

        return task.cont

    def _animate_entity(self, entity, dt):
        t = self._time_accum
        bob = math.sin(t * 3.0 + hash(entity.name) % 100) * 0.03
        z = entity.node.getZ()
        entity.node.setZ(z + bob * dt)

    # ------------------------------------------------------------------ #
    #  State transitions                                                   #
    # ------------------------------------------------------------------ #

    def enter_town(self):
        self.game_state = STATE_TOWN
        self.floor_level = 0
        self.map.apply_theme("TOWN")

        # Phase 9: advance calendar, consume meals, grow garden
        if not hasattr(self, 'calendar') or self.calendar is None:
            self.calendar = Calendar(1)
        self.calendar.advance_day()

        self._apply_meal_buffs()
        self._advance_garden()

        w, h = self.map.width, self.map.height
        self.map.grid = [[0 for _ in range(h)] for _ in range(w)]
        for x in range(12, 18):
            for y in range(12, 18):
                self.map.grid[x][y] = 1
        self.map.grid[15][17] = 2
        self.map.grid[13][12] = TILE_FORGE
        town_builder.ensure_town_walkable_for_buildings(self.map.grid, w, h)
        self.map.grid[15][20] = TILE_TOWN_PLOT

        # Phase 9: place garden tile
        self.map.grid[12][17] = TILE_GARDEN
        # Phase 10: companion meeting spot
        self.map.grid[17][17] = TILE_COMPANION
        # Phase 12: monster ranch
        self.map.grid[13][21] = TILE_RANCH

        town_builder.apply_completed_building_tiles(
            self.map.grid, self.player.completed_buildings
        )
        self.map.setup_visuals()
        forge_node = self.map.visual_nodes.get((13, 12))
        if forge_node:
            forge_node.setColor(0.9, 0.5, 0.1, 1)

        self.player.move_to(15, 14)
        if self.player.inn_buff_hp > 0:
            self.player.max_hp = max(1, self.player.max_hp - self.player.inn_buff_hp)
            self.player.inn_buff_hp = 0
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

        # Phase 15: setup NPCs in town
        self._setup_npcs()

        # Phase 15: update NPC schedules based on calendar
        if hasattr(self, 'calendar') and self.calendar:
            hour = (self.calendar.day * 6) % 24
            season = self.calendar.season
            for npc in self.npcs:
                npc.update_schedule(hour, season)
                npc.reset_daily()

            # Phase 15: activate seasonal particles and post-processing
            if self._ambient_particles is None:
                self._ambient_particles = AmbientParticles(self.render)
            self._ambient_particles.clear()
            self._ambient_particles.set_season(season)
            self._post_process.set_season_grade(season)

        # Phase 15: check for festival
        if hasattr(self, 'calendar') and self.calendar:
            fest = self.festivals.check_festival(self.calendar.season, self.calendar.day_in_season)
            if fest:
                self.hud.add_message(f"🎉 {fest.name}! {fest.description}")

        self.hud.update(self.player, in_town=True)
        self.save_mgr.save_progress(self.player)
        season_msg = f"Day {self.calendar.day} — {self.calendar.season}"
        self.hud.add_message(f"Safe in Town. Skills & PP restored. {season_msg}")

    def enter_dungeon(self):
        self.game_state = STATE_DUNGEON
        self.floor_level = 0
        for e in self.enemies:
            e.node.show()

        # Phase 10: deploy companions
        for c in self.player.companions:
            if c.is_deployed:
                c.is_dead = False
                c.hp = c.max_hp
                c.node.show()
                sx, sy = self.player.x, self.player.y
                c.move_to(sx + 1, sy)

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

        # Phase 14: ecology registration
        self.ecology.clear()
        for e in self.enemies:
            if not e.is_dead:
                self.ecology.register_enemy(e)
        self.ecology.update_ecology(self.enemies)
        for msg in self.ecology.get_floor_events():
            self.hud.add_message(msg)

        # Phase 14: risk/reward floor events
        self.risk_reward.clear_floor()
        modifier = self.risk_reward.roll_floor_modifier(self.floor_level)
        if modifier:
            self.hud.add_message(f"Floor Modifier: {modifier.name} — {modifier.description}")
        
        risk_event = self.risk_reward.roll_risk_event(self.floor_level)
        if risk_event:
            self.hud.add_message(f"Event: {risk_event['name']} — {risk_event['description']}")
            self.hud.add_message("  Press E to interact when ready.")

        # Phase 14: progression check
        if self.player.level > 1:
            unlocks = self.progression.add_xp(self.player.level * 10)
            for u in unlocks:
                self.hud.add_message(f"Progression Unlocked: {u}!")

        # Phase 14: dungeon veteran perk
        if self.progression.get_full_hp_start():
            self.player.hp = self.player.max_hp

        is_boss = (self.floor_level % 5 == 0 and self.floor_level > 0)
        self._tick_bounty("floor")

        # Phase 13: endless dungeon scaling and legendary events
        if hasattr(self.player, 'endless_dungeon') and self.floor_level >= 20:
            event_msgs = self.player.endless_dungeon.advance_floor(self.floor_level)
            for msg in event_msgs:
                self.hud.add_message(msg)
            
            # Check for final boss trigger
            if self.floor_level == 25 and not self._boss_fight_active:
                self._spawn_final_boss()

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

        # Forge tile (Phase 7/8)
        if self.game_state == STATE_TOWN and self.map.is_forge(px, py):
            self.hud.add_message("Forge: Press E to enchant weapon or inspect materials.")

        # Town plot (Phase 8)
        if self.game_state == STATE_TOWN and self.map.is_town_plot(px, py):
            self.hud.add_message("Town Plot: Press E to build (cycles blueprints).")

        # Phase 8 – building service tiles
        if self.game_state == STATE_TOWN:
            if self.map.is_herbalist(px, py):
                self.hud.add_message("Herbalist: Press E to cook or buy.")
            elif self.map.is_inn(px, py):
                self.hud.add_message("Inn: Press E to rest (+HP buff for next run).")
            elif self.map.is_shrine(px, py):
                self.hud.add_message("Shrine: Press E for purify/bless services.")
            elif self.map.is_guild(px, py):
                self.hud.add_message("Guild: Press E for bounty board.")
            elif self.map.is_garden(px, py):
                self.hud.add_message("Garden: Press E to plant/water/harvest.")
            elif self.map.is_companion_tile(px, py):
                self.hud.add_message("Companions: Press E to talk/gift/deploy.")
            elif self.map.is_ranch(px, py):
                self.hud.add_message("Ranch: Press E to manage captured monsters.")

        # Material node (Phase 8) – dungeon only
        if self.game_state == STATE_DUNGEON and self.map.is_material_node(px, py):
            self._harvest_material_node(px, py)

        # Item pickup
        if self.map.is_item(px, py):
            item_key = random_item_for_floor(self.floor_level)
            item = LootGenerator.generate(item_key, self.floor_level)
            if item.key in self.player.identified_items:
                item.is_identified = True
            if self.player.pick_up_item(item):
                self.hud.add_message(f"Picked up {item.display_name}!")
            else:
                self.hud.add_message(f"Bag full! Left {item.display_name} behind.")
            self.map.grid[px][py] = 1
            old_node = self.map.visual_nodes.pop((px, py), None)
            if old_node:
                old_node.removeNode()
            self.map._place_floor_tile(px, py, TILE_FLOOR)

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
        if self.menu_state != MENU_NONE:
            return
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
        self._set_menu(MENU_DEATH)
        return task.done

    def _input_wait(self):
        if self.menu_state != MENU_NONE:
            return
        if self.player.is_dead or self.game_state != STATE_DUNGEON:
            return
        self._end_player_turn()

    def _input_skill(self, idx):
        if self.menu_state != MENU_NONE:
            return
        if self.player.is_dead or self.game_state != STATE_DUNGEON:
            return
        if idx < len(self.player.skills):
            self.player.selected_skill_idx = idx
            self.turns.do_player_skill(self.player.skills[idx])
            self._resolve_tile_effects()
            self.hud.update(self.player, self.floor_level)

    def _input_use_item(self):
        if self.menu_state != MENU_NONE:
            return
        if self.player.is_dead:
            return
        if not self.player.inventory:
            self.hud.add_message("Inventory is empty.")
            return
        used = self.player.use_item(0, self.hud.add_message)
        if used:
            self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _input_drop_item(self):
        if self.menu_state != MENU_NONE:
            return
        if not self.player.inventory:
            self.hud.add_message("Nothing to drop.")
            return
        dropped = self.player.drop_item(0)
        if dropped:
            self.hud.add_message(f"Dropped {dropped.display_name}.")
            self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _input_inspect_item(self):
        """Phase 7: I key - toggle item inspection overlay for first inventory item."""
        if self.menu_state != MENU_NONE:
            return
        if self.item_screen.is_visible:
            self.item_screen.hide()
            return
        if not self.player.inventory:
            self.hud.add_message("Inventory is empty.")
            return
        self.item_screen.show(self.player.inventory[0])

    def _input_companions(self):
        """Phase 10: C key - toggle companion screen."""
        if self.menu_state != MENU_NONE:
            return
        if self.companion_screen.is_visible:
            self.companion_screen.hide()
            return
        deployed = self.player.active_companions
        self.companion_screen.show(self.player.companions, deployed)

    def _input_action(self):
        """E key: save/forge in town, print debug stats in dungeon."""
        if self.menu_state != MENU_NONE:
            return
        if self.player.is_dead:
            self.enter_town()
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
            # Phase 14: skill chain check
            chain = self.synergy.check_skill_chain(skill.display)
            if chain:
                self.hud.add_message(f"Skill Chain! {chain.name}: {chain.description}")
            
            self.turns.process_player_turn("skill", skill)
            
            # Phase 14: check status combos on enemies
            for e in self.enemies:
                if not e.is_dead:
                    combos = self.synergy.check_status_combos(e)
                    for c in combos:
                        self.hud.add_message(f"Combo! {c.name}: {c.description}")
            
            # Phase 14: ecology update
            self.ecology.update_ecology(self.enemies)
            for msg in self.ecology.get_floor_events():
                self.hud.add_message(msg)
        
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

    def _input_companions(self):
        """Phase 10: C key - toggle companion screen."""
        if self.menu_state != MENU_NONE:
            return
        if self.companion_screen.is_visible:
            self.companion_screen.hide()
            return
        deployed = self.player.active_companions
        self.companion_screen.show(self.player.companions, deployed)

    def _input_risk_choice(self, idx):
        """Phase 14: 1/2/3 keys for risk event choices."""
        if self.menu_state != MENU_NONE:
            return
        if not self.risk_reward.pending_choice:
            return
        msgs = self.risk_reward.apply_choice(idx, self.player)
        for m in msgs:
            self.hud.add_message(m)
        self.save_mgr.save_progress(self.player)

    def _input_e_key(self):
        """E key: context-sensitive action."""
        if self.menu_state == MENU_RANCH:
            self._input_menu_evolve()
        else:
            self._input_action()

    def _input_action(self):
        """E key: save/forge in town, print debug stats in dungeon."""
        if self.player.is_dead:
            self.enter_town()
            return
        if self.game_state == STATE_TOWN:
            if self.map.is_forge(self.player.x, self.player.y):
                self._forge_action()
            elif self.map.is_town_plot(self.player.x, self.player.y):
                self._town_plot_action()
            elif self.map.is_herbalist(self.player.x, self.player.y):
                self._herbalist_action()
            elif self.map.is_inn(self.player.x, self.player.y):
                self._inn_action()
            elif self.map.is_shrine(self.player.x, self.player.y):
                self._shrine_action()
            elif self.map.is_guild(self.player.x, self.player.y):
                self._guild_action()
            elif self.map.is_garden(self.player.x, self.player.y):
                self._garden_action()
            elif self.map.is_companion_tile(self.player.x, self.player.y):
                self._companion_action()
            elif self.map.is_ranch(self.player.x, self.player.y):
                self._ranch_action()
            else:
                self.save_mgr.save_progress(self.player)
                self.hud.add_message("Progress saved.")
        else:
            # Phase 14: handle risk events in dungeon
            if self.risk_reward.pending_choice:
                self.hud.add_message(f"Event: {self.risk_reward.pending_choice['name']}")
                self.hud.add_message("  Press 1/2/3 to choose, or E again to decline.")
                return
            
            inv_str = ", ".join(i.display_name for i in self.player.inventory) or "empty"
            self.hud.add_message(
                f"Lv{self.player.level} HP:{int(self.player.hp)} ATK:{self.player.effective_attack}"
            )
            self.hud.add_message(f"Bag: {inv_str}")
            
            # Phase 14: show active synergies
            syn_descs = self.synergy.get_active_descriptions()
            if syn_descs:
                for d in syn_descs[:3]:
                    self.hud.add_message(f"  Synergy: {d}")

    # ------------------------------------------------------------------ #
    #  Phase 7 – Town Forge                                                #
    # ------------------------------------------------------------------ #

    def _harvest_material_node(self, px, py):
        """Convert a material-node tile to floor and grant themed loot."""
        theme = self.map.current_theme
        tables = {
            "ICE": [("frost_jewel", 3), ("bat_wing", 2), ("moonstone", 1)],
            "FIRE": [("flame_shard", 3), ("iron_ore", 3), ("orc_hide", 2)],
            "CAVE": [("iron_ore", 3), ("slime_gel", 3), ("goblin_fang", 2)],
        }
        keys, weights = zip(*tables.get(theme, tables["CAVE"]))
        mat = random.choices(keys, weights=weights, k=1)[0]
        amt = random.randint(1, 2)
        self.player.add_material(mat, amt)
        self.map.grid[px][py] = 1
        old_node = self.map.visual_nodes.pop((px, py), None)
        if old_node:
            old_node.removeNode()
        self.map._place_floor_tile(px, py, TILE_FLOOR)
        self.hud.add_message(
            f"Gathered {amt}× {mat.replace('_', ' ').title()} from the deposit."
        )
        self._tick_bounty("material")

    def _town_plot_action(self):
        """Cycle buildable structures; spend mats + gold when affordable."""
        pending = [b for b in self._building_defs if b.id not in self.player.completed_buildings]
        if not pending:
            self.hud.add_message("Town Plot: Everything in this blueprint book is built!")
            return
        self._town_build_index %= len(pending)
        target = pending[self._town_build_index]
        ok, reason = town_builder.can_build(
            target, self.player, self.player.completed_buildings
        )
        mats_line = ", ".join(f"{v}× {k.replace('_', ' ')}" for k, v in sorted(target.materials.items()))
        gold_line = f" + {target.gold}g" if target.gold else ""
        self.hud.add_message(
            f"Blueprint [{self._town_build_index + 1}/{len(pending)}]: {target.name}"
        )
        self.hud.add_message(f"  Cost: {mats_line}{gold_line}")
        if not ok:
            self.hud.add_message(f"  ({reason}) Press E for next blueprint.")
            self._town_build_index += 1
            return
        success, msg = town_builder.try_build(
            target, self.player, self.player.completed_buildings
        )
        if success:
            self.hud.add_message(msg)
            town_builder.apply_completed_building_tiles(
                self.map.grid, self.player.completed_buildings
            )
            self.map.setup_visuals()
            forge_node = self.map.visual_nodes.get((13, 12))
            if forge_node:
                forge_node.setColor(0.9, 0.5, 0.1, 1)
            self._town_build_index = 0
            self.save_mgr.save_progress(self.player)
            return
        self.hud.add_message(msg)
        self._town_build_index += 1

    # Forge costs — Phase 8 Forge Lv2 lowers material needs slightly
    _FORGE_ENCHANT_COST = {"iron_ore": 5}
    _FORGE_ENCHANT_COST_LV2 = {"iron_ore": 3, "flame_shard": 2}
    _FORGE_UPGRADE_COST = {"iron_ore": 3, "dark_crystal": 1}
    _FORGE_UPGRADE_COST_LV2 = {"iron_ore": 2, "dark_crystal": 1}

    def _forge_action(self):
        """
        Simple forge interaction at the town forge tile.
        First call shows the menu; second call (while at forge) performs the action.
        """
        wpn = self.player.equipped_weapon
        mats_str = self.player.materials_summary()
        self.hud.add_message(f"Materials: {mats_str}")
        if "forge_lv2" in self.player.completed_buildings:
            self.hud.add_message("Forge Lv2 active — improved material efficiency.")

        if wpn is None:
            self.hud.add_message("Forge: Equip a weapon first.")
            return

        enc_cost = (
            self._FORGE_ENCHANT_COST_LV2
            if "forge_lv2" in self.player.completed_buildings
            else self._FORGE_ENCHANT_COST
        )
        up_cost = (
            self._FORGE_UPGRADE_COST_LV2
            if "forge_lv2" in self.player.completed_buildings
            else self._FORGE_UPGRADE_COST
        )

        can_enchant = self.player.has_materials(enc_cost)
        can_upgrade = wpn.affixes and self.player.has_materials(up_cost)

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
                self.player.spend_materials(enc_cost)
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
            self.player.spend_materials(up_cost)
            self.player._apply_weapon_affixes(wpn)  # noqa: SLF001
            self.hud.add_message(
                f"Upgraded: {affix.tag} {old_val} -> {affix.value}"
            )
            self.save_mgr.save_progress(self.player)
            return

        cost_str = ", ".join(f"{v}x {k}" for k, v in enc_cost.items())
        self.hud.add_message(
            f"Forge: Need {cost_str} to enchant. "
            f"(Have: {mats_str})"
        )

    # ------------------------------------------------------------------ #
    #  Phase 8 – Building Services                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_json(subdir, filename, key):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "..", subdir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(key, [])
        except Exception:
            return []

    def _tick_bounty(self, event_type, amount=1):
        bounty = self.player.active_bounty
        if bounty is None or self.game_state != STATE_DUNGEON:
            return
        if bounty["target_type"] == event_type:
            bounty["progress"] += amount
            if bounty["progress"] >= bounty["target_count"]:
                self.hud.add_message(
                    f"Bounty done: {bounty['name']}! Return to Guild to claim."
                )

    def _resolve_companion_turns(self):
        """Run companion AI after enemy turns."""
        deployed = [c for c in self.player.companions if c.is_deployed and not c.is_dead]
        if not deployed:
            return
        for c in deployed:
            c.node.show()
        self.companion_ai.companions = deployed
        self.companion_ai.resolve_companion_turns(
            self.player.x, self.player.y, self.enemies, self.map
        )

    def _on_enemy_killed(self, enemy):
        self._tick_bounty("kill")

    # -- Herbalist Hut --

    def _herbalist_action(self):
        stock = self._herbalist_stock
        if not stock:
            self.hud.add_message("Herbalist: No stock available.")
            return
        self._herbalist_index %= len(stock)
        item_info = stock[self._herbalist_index]
        can_afford = self.player.gold >= item_info["gold_cost"]
        has_space = len(self.player.inventory) < self.player.max_inventory
        self.hud.add_message(
            f"Shop [{self._herbalist_index + 1}/{len(stock)}]: "
            f"{item_info['display']} — {item_info['gold_cost']}g"
        )
        if not can_afford:
            self.hud.add_message("  Not enough gold. Press E for next item.")
            self._herbalist_index += 1
            return
        if not has_space:
            self.hud.add_message("  Bag full! Press E for next item.")
            self._herbalist_index += 1
            return
        item = Item(item_info["key"])
        item.is_identified = True
        self.player.gold -= item_info["gold_cost"]
        self.player.inventory.append(item)
        self.hud.add_message(f"  Bought {item.display}! (-{item_info['gold_cost']}g)")
        self._herbalist_index += 1
        self.save_mgr.save_progress(self.player)

    # -- Inn --

    def _inn_action(self):
        if self.player.inn_buff_hp > 0:
            self.hud.add_message(
                f"Inn: Already well-rested (+{self.player.inn_buff_hp} max HP)."
            )
            return
        buff = 10 + self.player.level * 2
        self.player.inn_buff_hp = buff
        self.player.max_hp += buff
        self.player.hp = min(self.player.hp + buff, self.player.max_hp)
        self.hud.add_message(f"Inn: Well-rested! +{buff} max HP for next dungeon run.")
        self.save_mgr.save_progress(self.player)

    # -- Shrine --

    _SHRINE_PURIFY_COST = 50
    _SHRINE_BLESS_COST_GOLD = 80
    _SHRINE_BLESS_COST_MATS = {"moonstone": 2}

    def _shrine_action(self):
        wpn = self.player.equipped_weapon
        if wpn is None:
            self.hud.add_message("Shrine: Equip a weapon first.")
            return
        services = ["purify", "bless"]
        service = services[self._shrine_index % len(services)]

        if service == "purify":
            cursed_affixes = [a for a in wpn.affixes if a.cursed]
            if not cursed_affixes:
                self.hud.add_message(
                    "Shrine: No cursed affixes to purify. Press E for next service."
                )
                self._shrine_index += 1
                return
            cost = self._SHRINE_PURIFY_COST
            if self.player.gold < cost:
                self.hud.add_message(
                    f"Shrine: Purify costs {cost}g. Press E for next service."
                )
                self._shrine_index += 1
                return
            for a in cursed_affixes:
                wpn.affixes.remove(a)
            wpn.cursed = any(a.cursed for a in wpn.affixes)
            self.player._apply_weapon_affixes(wpn)
            self.player.gold -= cost
            self.hud.add_message(
                f"Shrine: Purified! Removed {len(cursed_affixes)} cursed affix(es). (-{cost}g)"
            )
            self._shrine_index += 1
            self.save_mgr.save_progress(self.player)
            return

        if service == "bless":
            cost_g = self._SHRINE_BLESS_COST_GOLD
            cost_m = self._SHRINE_BLESS_COST_MATS
            can_afford = self.player.gold >= cost_g and self.player.has_materials(cost_m)
            if not can_afford:
                mats_str = ", ".join(f"{v}x {k}" for k, v in cost_m.items())
                self.hud.add_message(
                    f"Shrine: Bless costs {cost_g}g + {mats_str}. Press E for next service."
                )
                self._shrine_index += 1
                return
            pool = get_weapon_affix_pool(cursed=False)
            existing_tags = {a.tag for a in wpn.affixes}
            available = [t for t in pool if t not in existing_tags]
            if not available:
                self.hud.add_message(
                    "Shrine: No new affixes to add. Press E for next service."
                )
                self._shrine_index += 1
                return
            tag = random.choice(available)
            affix = LootGenerator._roll_affix(tag)
            wpn.affixes.append(affix)
            if affix.stat == "attack_bonus_add":
                wpn.attack_bonus += affix.value
                self.player._weapon_bonus = wpn.attack_bonus
            self.player._apply_weapon_affixes(wpn)
            self.player.gold -= cost_g
            self.player.spend_materials(cost_m)
            self.hud.add_message(f"Shrine: Blessed! Gained [{affix.desc}].")
            self._shrine_index += 1
            self.save_mgr.save_progress(self.player)
            return

    # -- Guild Hall --

    def _guild_action(self):
        bounty = self.player.active_bounty

        if bounty is None:
            if not self._bounty_defs:
                self.hud.add_message("Guild: No bounties available.")
                return
            b = random.choice(self._bounty_defs)
            self.player.active_bounty = {
                "id": b["id"],
                "name": b["name"],
                "description": b["description"],
                "target_type": b["target_type"],
                "target_count": b["target_count"],
                "progress": 0,
                "gold_reward": b["gold_reward"],
                "xp_reward": b["xp_reward"],
            }
            self.hud.add_message(f"Guild: Accepted — {b['name']}")
            self.hud.add_message(
                f"  {b['description']} (+{b['gold_reward']}g +{b['xp_reward']}XP)"
            )
            self.save_mgr.save_progress(self.player)
            return

        if bounty["progress"] >= bounty["target_count"]:
            self.player.add_gold(bounty["gold_reward"])
            self.player.add_xp(bounty["xp_reward"])
            self.hud.add_message(
                f"Bounty complete! +{bounty['gold_reward']}g +{bounty['xp_reward']}XP"
            )
            self.player.active_bounty = None
            self.save_mgr.save_progress(self.player)
            return

        remaining = bounty["target_count"] - bounty["progress"]
        self.hud.add_message(
            f"Bounty: {bounty['name']} ({bounty['progress']}/{bounty['target_count']}, "
            f"{remaining} left)"
        )

    # ------------------------------------------------------------------ #
    #  Phase 9 – Kitchen / Cooking (at Herbalist Hut)                        #
    # ------------------------------------------------------------------ #

    def _herbalist_action(self):
        if self._herbalist_index % 2 == 0:
            self._herbalist_buy()
        else:
            self._herbalist_cook()
        self._herbalist_index += 1

    def _herbalist_buy(self):
        stock = self._herbalist_stock
        if not stock:
            self.hud.add_message("Herbalist: No stock available.")
            return
        self._herbalist_stock_idx = getattr(self, '_herbalist_stock_idx', 0)
        self._herbalist_stock_idx %= len(stock)
        item_info = stock[self._herbalist_stock_idx]
        can_afford = self.player.gold >= item_info["gold_cost"]
        has_space = len(self.player.inventory) < self.player.max_inventory
        self.hud.add_message(
            f"Shop [{self._herbalist_stock_idx + 1}/{len(stock)}]: "
            f"{item_info['display']} — {item_info['gold_cost']}g"
        )
        if not can_afford:
            self.hud.add_message("  Not enough gold.")
            return
        if not has_space:
            self.hud.add_message("  Bag full!")
            return
        item = Item(item_info["key"])
        item.is_identified = True
        self.player.gold -= item_info["gold_cost"]
        self.player.inventory.append(item)
        self.hud.add_message(f"  Bought {item.display}!")
        self._herbalist_stock_idx += 1
        self.save_mgr.save_progress(self.player)

    def _herbalist_cook(self):
        from world.kitchen import load_recipes, can_cook, cook
        recipes = load_recipes()
        if not recipes:
            self.hud.add_message("Kitchen: No recipes known.")
            return
        self._cook_index %= len(recipes)
        r = recipes[self._cook_index]
        self.hud.add_message(
            f"Cook [{self._cook_index + 1}/{len(recipes)}]: {r.name}"
        )
        self.hud.add_message(
            f"  {r.description} "
            f"(need: {', '.join(f'{v}x {k}' for k, v in r.ingredients.items())})"
        )
        if not can_cook(r, self.player):
            self.hud.add_message("  Missing ingredients. Press E for next recipe.")
            self._cook_index += 1
            return
        if len(getattr(self.player, 'active_meals', [])) >= 2:
            self.hud.add_message("  2 meals already active! Eat in dungeon first.")
            self._cook_index += 1
            return
        cook(r, self.player)
        if not hasattr(self.player, 'active_meals'):
            self.player.active_meals = []
        self.player.active_meals.append({
            "name": r.name,
            "buff_stat": r.buff.stat,
            "buff_value": r.buff.value,
            "status_immune": r.buff.status_immune,
        })
        self.hud.add_message(f"  Cooked {r.name}! Buff active for next run.")
        self._cook_index += 1
        self.save_mgr.save_progress(self.player)

    # ------------------------------------------------------------------ #
    #  Phase 9 – Crafting (at Forge Lv2)                                   #
    # ------------------------------------------------------------------ #

    def _crafting_action(self):
        from world.workbench import load_blueprints, can_craft, craft
        blueprints = load_blueprints()
        if not blueprints:
            self.hud.add_message("Workbench: No blueprints known.")
            return
        self._craft_index %= len(blueprints)
        bp = blueprints[self._craft_index]
        self.hud.add_message(
            f"Craft [{self._craft_index + 1}/{len(blueprints)}]: {bp.name}"
        )
        self.hud.add_message(
            f"  {bp.description} "
            f"(need: {', '.join(f'{v}x {k}' for k, v in bp.materials.items())})"
        )
        if not can_craft(bp, self.player):
            self.hud.add_message("  Can't craft. Press E for next blueprint.")
            self._craft_index += 1
            return
        if craft(bp, self.player, LootGenerator, 1):
            self.hud.add_message(f"  Crafted {bp.name}!")
        else:
            self.hud.add_message("  Craft failed.")
        self._craft_index += 1
        self.save_mgr.save_progress(self.player)

    # ------------------------------------------------------------------ #
    #  Phase 9 – Garden                                                      #
    # ------------------------------------------------------------------ #

    def _garden_action(self):
        if self._garden_index % 3 == 0:
            self._garden_plant()
        elif self._garden_index % 3 == 1:
            self._garden_water()
        else:
            self._garden_harvest()
        self._garden_index += 1

    def _garden_plant(self):
        from world.garden import get_crop_defs, create_plot, get_garden_capacity
        defs = get_crop_defs()
        crop_ids = list(defs.keys())
        if not crop_ids:
            self.hud.add_message("Garden: No crops available.")
            return
        plots = getattr(self.player, 'garden_plots', [])
        cap = get_garden_capacity()
        if len(plots) >= cap:
            self.hud.add_message(f"Garden: Full ({len(plots)}/{cap} plots used).")
            return
        self._garden_crop_idx = getattr(self, '_garden_crop_idx', 0)
        self._garden_crop_idx %= len(crop_ids)
        cid = crop_ids[self._garden_crop_idx]
        cd = defs[cid]
        self.hud.add_message(
            f"Plant [{self._garden_crop_idx + 1}/{len(crop_ids)}]: {cd['name']} "
            f"({cd['growth_days']} days)"
        )
        plot = create_plot(cid, defs)
        if plot:
            if not hasattr(self.player, 'garden_plots'):
                self.player.garden_plots = []
            self.player.garden_plots.append(plot)
            self.hud.add_message(f"  Planted {cd['name']}! ({len(plots) + 1}/{cap})")
            self._garden_crop_idx += 1
            self.save_mgr.save_progress(self.player)

    def _garden_water(self):
        plots = getattr(self.player, 'garden_plots', [])
        if not plots:
            self.hud.add_message("Garden: Nothing planted. Press E to plant.")
            return
        for plot in plots:
            if not plot.is_ready:
                from world.garden import water_plot
                water_plot(plot)
                self.hud.add_message(
                    f"Watered {plot.crop_id} ({plot.growth_days_current}/{plot.growth_days_needed})."
                )
                self.save_mgr.save_progress(self.player)
                return
        self.hud.add_message("Garden: All crops are ready to harvest!")

    def _garden_harvest(self):
        plots = getattr(self.player, 'garden_plots', [])
        if not plots:
            self.hud.add_message("Garden: Nothing planted. Press E to plant.")
            return
        from world.garden import harvest_plot
        for plot in plots:
            if plot.is_ready:
                items_before = len(self.player.inventory)
                harvest_plot(plot, self.player)
                gained = len(self.player.inventory) - items_before
                if gained > 0:
                    self.hud.add_message(f"Harvested {gained}x {plot.crop_id}!")
                    self.save_mgr.save_progress(self.player)
                    return
        self.hud.add_message("Garden: No crops ready. Press E to water.")

    # ------------------------------------------------------------------ #
    #  Phase 9 – Calendar & Buffs                                           #
    # ------------------------------------------------------------------ #

    def _apply_meal_buffs(self):
        meals = getattr(self.player, 'active_meals', [])
        if not meals:
            return
        self.player.active_meals = []
        for meal in meals:
            stat = meal["buff_stat"]
            value = meal["buff_value"]
            immune = meal.get("status_immune", "")
            if stat == "max_hp_pct":
                bonus = int(self.player.max_hp * value / 100)
                self.player.max_hp += bonus
                self.player.hp += bonus
                self.hud.add_message(f"{meal['name']}: +{bonus} max HP this run.")
            elif stat == "atk_pct":
                bonus = int(self.player.attack_power * value / 100)
                self.player.attack_power += bonus
                self.hud.add_message(f"{meal['name']}: +{bonus} ATK this run.")
            elif stat == "dmg_reduce_pct":
                self.player.dmg_reduce_pct = getattr(self.player, 'dmg_reduce_pct', 0) + value
                self.hud.add_message(f"{meal['name']}: -{value}% damage taken this run.")
            elif stat == "auto_revive":
                self.player._auto_revive = True
                self.hud.add_message(f"{meal['name']}: Auto-revive once this run.")
            elif stat == "gold_bonus_pct":
                self.player.gold_bonus_pct = getattr(self.player, 'gold_bonus_pct', 0) + value
                self.hud.add_message(f"{meal['name']}: +{value}% gold drops this run.")
            elif stat == "hunger_save_pct":
                self.player.hunger_save_pct = getattr(self.player, 'hunger_save_pct', 0) + value
                self.hud.add_message(f"{meal['name']}: -{value}% hunger drain this run.")
            if immune:
                self.hud.add_message(f"  Immune to {immune}.")

    def _advance_garden(self):
        plots = getattr(self.player, 'garden_plots', [])
        if not plots:
            return
        from world.garden import CropPlot
        ready_names = []
        season = self.calendar.season if hasattr(self, 'calendar') else ""
        for plot in plots:
            if season and plot.season_bonus == season.upper():
                plot.growth_days_current += 1
            just_ready = plot.advance_day()
            if just_ready:
                ready_names.append(plot.crop_id)
        if ready_names:
            self.hud.add_message(f"Garden: {', '.join(ready_names)} ready to harvest!")
        self.save_mgr.save_progress(self.player)

    # ------------------------------------------------------------------ #
    #  Phase 10 – Companions                                                 #
    # ------------------------------------------------------------------ #

    def _companion_action(self):
        """E key at companion tile: talk, gift, or deploy companions."""
        companions = self.player.companions
        if not companions:
            self.hud.add_message("No companions available.")
            return

        undeployed = [c for c in companions if not c.is_deployed]
        deployed = [c for c in companions if c.is_deployed]

        self.hud.add_message("--- Companions ---")
        for c in companions:
            tag = " [Deployed]" if c.is_deployed else ""
            self.hud.add_message(
                f"  {c.name} (Rank {c.support_rank}, Affection {c.affection}){tag}"
            )

        if deployed:
            for c in deployed:
                c.is_deployed = False
                self.hud.add_message(f"{c.name} recalled to town.")
            self.player.active_companions = set()
            self.save_mgr.save_progress(self.player)
            return

        if not undeployed:
            self.hud.add_message("All companions are deployed!")
            return

        self._companion_deploy_idx = getattr(self, '_companion_deploy_idx', 0)
        self._companion_deploy_idx %= len(undeployed)
        target = undeployed[self._companion_deploy_idx]

        active_count = len(self.player.active_companions)
        if active_count >= 2:
            self.hud.add_message("Max 2 companions deployed. Recall first.")
            self._companion_deploy_idx += 1
            return

        target.is_deployed = True
        self.player.active_companions.add(target.companion_id)
        self.hud.add_message(f"{target.name} deployed! (Press E again to recall)")
        self._companion_deploy_idx += 1
        self.save_mgr.save_progress(self.player)

    # ------------------------------------------------------------------ #
    #  Phase 11 – Menu System                                                #
    # ------------------------------------------------------------------ #

    def _set_menu(self, state):
        """Switch menu state, hiding all others."""
        self.menu_state = state
        self.main_menu.hide()
        self.pause_menu.hide()
        self.inventory_screen.hide()
        self.death_screen.hide()
        self.ranch_screen.hide()
        self.debug_menu.hide()
        if state == MENU_NONE:
            self.hud.show()
        elif state == MENU_MAIN:
            self.hud.hide()
            self.main_menu.show()
        elif state == MENU_PAUSE:
            self.pause_menu.show()
        elif state == MENU_INVENTORY:
            self.inventory_screen.show(self.player.inventory)
        elif state == MENU_DEATH:
            self.death_screen.show()
        elif state == MENU_RANCH:
            roster = self.player.monster_roster
            inv_keys = [i.key for i in self.player.inventory]
            self.ranch_screen.show(roster.monsters, inv_keys)
        elif state == MENU_FESTIVAL:
            self.hud.hide()
            if self.festivals.active_festival:
                self.festival_screen.show(self.festivals.active_festival)
        elif state == MENU_DEBUG:
            self.debug_menu.show()
            self.hud.hide()
            if self.festivals.active_festival:
                self.festival_screen.show(self.festivals.active_festival)
        self.festival_screen.hide()

    def _input_menu(self):
        """Escape key: toggle pause or close menus."""
        if self.menu_state == MENU_NONE:
            if self.game_state in (STATE_TOWN, STATE_DUNGEON):
                self._set_menu(MENU_PAUSE)
        elif self.menu_state == MENU_PAUSE:
            self._set_menu(MENU_NONE)
        elif self.menu_state == MENU_INVENTORY:
            self._set_menu(MENU_PAUSE)
        elif self.menu_state == MENU_RANCH:
            self._set_menu(MENU_NONE)
        elif self.menu_state == MENU_DEATH:
            pass  # Death screen has its own buttons

    def _input_menu_nav(self, direction):
        """Arrow keys: navigate menu selection."""
        if self.menu_state == MENU_INVENTORY:
            self.inventory_screen.navigate(direction)
        elif self.menu_state == MENU_RANCH:
            self.ranch_screen.navigate(direction)

    def _input_menu_confirm(self):
        """Enter key: confirm menu action."""
        if self.menu_state == MENU_INVENTORY:
            self.inventory_screen.use_selected()
        elif self.menu_state == MENU_RANCH:
            self.ranch_screen.deploy_selected()

    def _input_menu_evolve(self):
        """E key in Ranch screen: evolve selected monster."""
        if self.menu_state == MENU_RANCH:
            self.ranch_screen.evolve_selected()


    # ------------------------------------------------------------------ #
    #  Debug Actions                                                       #
    # ------------------------------------------------------------------ #

    def _input_debug(self):
        """F1 key: toggle debug menu."""
        if self.menu_state == MENU_NONE:
            self._set_menu(MENU_DEBUG)
        elif self.menu_state == MENU_DEBUG:
            self._set_menu(MENU_NONE)

    def _debug_heal(self):
        self.player.hp = self.player.max_hp
        self.player.hunger = self.player.max_hunger
        self.hud.add_message("Debug: Healed player.")
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _debug_gold(self):
        self.player.add_gold(1000)
        self.hud.add_message("Debug: Added 1000 Gold.")
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _debug_items(self):
        from entities.items import random_item_for_floor, LootGenerator
        item_key = random_item_for_floor(self.floor_level)
        item = LootGenerator.generate(item_key, self.floor_level)
        if self.player.pick_up_item(item):
            self.hud.add_message(f"Debug: Spawned {item.display_name}.")
        else:
            self.hud.add_message("Debug: Bag full.")
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _debug_village(self):
        self._set_menu(MENU_NONE)
        self.enter_town()

    def _debug_skip(self):
        if self.game_state == STATE_DUNGEON:
            self._set_menu(MENU_NONE)
            self.next_floor()

    def _debug_level(self):
        for _ in range(5):
            self.player._level_up()
        self.hud.add_message("Debug: Level Up (+5).")
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _debug_godmode(self):
        self.player.god_mode = not self.player.god_mode
        status = "ON" if self.player.god_mode else "OFF"
        self.hud.add_message(f"Debug: God Mode {status}.")

    def _on_new_game(self):
        """Start a fresh game."""
        self.main_menu.hide()
        self.hud.show()
        self.menu_state = MENU_NONE
        self.player = Player(0, 0)
        self.player.reparent_to(self.render)
        self.enemies = [Enemy(f"Foe {i}", 0, 0) for i in range(ENEMY_COUNT)]
        for e in self.enemies:
            e.reparent_to(self.render)
        self.spawn_sys = SpawnSystem(self.map, self.player, self.enemies)
        self.turns = TurnSystem(self.player, self.enemies, self.map, self.hud.add_message,
                                kill_callback=self._on_enemy_killed,
                                post_enemy_callback=self._resolve_companion_turns)
        self.companion_ai = CompanionAI(self.player.companions, self.hud.add_message)

        COMP_IDS = ["lyra", "brom", "mira", "sable", "finn"]
        from entities.companion import Companion
        for cid in COMP_IDS:
            self.player.companions.append(Companion(cid))

        self.calendar = Calendar(1)
        self.enter_town()

    def _on_continue(self):
        """Continue from saved game."""
        self.main_menu.hide()
        self.hud.show()
        self.menu_state = MENU_NONE
        self.save_mgr.load_progress(self.player)

        COMP_IDS = ["lyra", "brom", "mira", "sable", "finn"]
        existing = {c.companion_id for c in self.player.companions}
        from entities.companion import Companion
        for cid in COMP_IDS:
            if cid not in existing:
                self.player.companions.append(Companion(cid))

        self.enter_town()

    def _on_options(self):
        """Options placeholder."""
        self.hud.add_message("Options: Not yet implemented.")

    def _on_exit(self):
        """Exit the game."""
        self.userExit()

    def _on_ngp(self):
        """New Game+ from title screen."""
        if not os.path.exists("save_data.json"):
            self.hud.add_message("No save data for New Game+.")
            return
        self.main_menu.hide()
        self.hud.show()
        self.menu_state = MENU_NONE
        self.save_mgr.load_progress(self.player)
        self._start_new_game_plus()

    def _on_pause_resume(self):
        """Resume from pause."""
        self._set_menu(MENU_NONE)

    def _on_pause_inventory(self):
        """Open inventory from pause."""
        self._set_menu(MENU_INVENTORY)

    def _on_pause_skills(self):
        """Show skills info."""
        skills = self.player.skills
        if not skills:
            self.hud.add_message("No skills learned.")
            return
        for s in skills:
            self.hud.add_message(f"{s.display} — PP: {s.pp}/{s.max_pp}")

    def _on_pause_save(self):
        """Save and resume."""
        self.save_mgr.save_progress(self.player)
        self.hud.add_message("Game saved.")
        self._set_menu(MENU_NONE)

    def _on_pause_quit(self):
        """Quit to title."""
        self.save_mgr.save_progress(self.player)
        self._set_menu(MENU_MAIN)

    def _inv_use(self, idx):
        """Use item from inventory screen."""
        if idx < len(self.player.inventory):
            self.player.use_item(idx, self.hud.add_message)
            self.inventory_screen.show(self.player.inventory)
            self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _inv_drop(self, idx):
        """Drop item from inventory screen."""
        if idx < len(self.player.inventory):
            dropped = self.player.drop_item(idx)
            if dropped:
                self.hud.add_message(f"Dropped {dropped.display_name}.")
            self.inventory_screen.show(self.player.inventory)
            self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _inv_equip(self, idx):
        """Equip weapon from inventory screen."""
        if idx < len(self.player.inventory):
            item = self.player.inventory[idx]
            if item.category == "weapon":
                self.player.use_item(idx, self.hud.add_message)
                self.inventory_screen.show(self.player.inventory)
                self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)
            else:
                self.hud.add_message("Can only equip weapons from here.")

    def _inv_close(self):
        """Close inventory screen."""
        self._set_menu(MENU_PAUSE)

    def _on_rescue(self):
        """Rescue from death: return to town with penalties."""
        self.death_screen.hide()
        self.player.gold = max(0, int(self.player.gold * 0.9))
        self.player.hunger = max(0, int(self.player.hunger * 0.5))
        self.player.hp = self.player.max_hp
        self.player.cure_all_statuses()
        self.player.restore_skill_pp()
        for c in self.player.companions:
            c.is_deployed = False
            c.is_dead = False
            c.hp = c.max_hp
        self.player.active_companions = set()
        self.enter_town()
        self._set_menu(MENU_NONE)

    def _on_death_quit(self):
        """Quit to title from death screen."""
        self.death_screen.hide()
        self._set_menu(MENU_MAIN)

    # ------------------------------------------------------------------ #
    #  Phase 12 – Monster Ranch / Capture                                    #
    # ------------------------------------------------------------------ #

    def _ranch_action(self):
        """Open Ranch screen from town."""
        self._set_menu(MENU_RANCH)

    def _ranch_deploy(self, idx):
        """Toggle deploy for selected monster."""
        roster = self.player.monster_roster
        if idx < len(roster.monsters):
            m = roster.monsters[idx]
            deployed = roster.get_deployed()
            if m.is_deployed:
                m.is_deployed = False
                self.hud.add_message(f"{m.name} recalled to Ranch.")
            elif len(deployed) >= 2:
                self.hud.add_message("Max 2 monsters deployed. Recall one first.")
            else:
                m.is_deployed = True
                self.hud.add_message(f"{m.name} deployed!")
            self.ranch_screen.show(roster.monsters, [i.key for i in self.player.inventory])
            self.save_mgr.save_progress(self.player)

    def _ranch_evolve(self, idx):
        """Attempt evolution for selected monster."""
        roster = self.player.monster_roster
        if idx < len(roster.monsters):
            m = roster.monsters[idx]
            inv_keys = [i.key for i in self.player.inventory]
            ev = m.check_evolution(inv_keys)
            if ev:
                item_req = ev.get("item_req")
                if item_req:
                    for i, item in enumerate(self.player.inventory):
                        if item.key == item_req:
                            self.player.inventory.pop(i)
                            break
                m.evolve(ev)
                self.hud.add_message(f"{m.name} evolved into {m.monster_type.replace('_', ' ').title()}!")
                self.ranch_screen.show(roster.monsters, [i.key for i in self.player.inventory])
                self.save_mgr.save_progress(self.player)
            else:
                self.hud.add_message(f"{m.name} cannot evolve yet.")

    def _ranch_close(self):
        """Close Ranch screen."""
        self._set_menu(MENU_NONE)

    def _on_enemy_killed(self, enemy):
        self._tick_bounty("kill")
        # Phase 12: check for capture opportunity
        if self._pending_capture and self._capture_enemy is enemy:
            self._pending_capture = False
            self._capture_enemy = None

    # ------------------------------------------------------------------ #
    #  Phase 13 – Final Boss & Endgame                                       #
    # ------------------------------------------------------------------ #

    def _spawn_final_boss(self):
        """Spawn the final boss at floor 25."""
        from entities.boss import FinalBoss
        self._boss_fight_active = True
        
        # Find a walkable tile near the player
        boss = FinalBoss(self.player.x + 2, self.player.y)
        boss.reparent_to(self.render)
        boss.node.show()
        self.enemies.append(boss)
        
        self.hud.add_message("The Abyssal King appears! The final battle begins!")

    def _on_boss_defeated(self):
        """Handle final boss defeat."""
        self._boss_fight_active = False
        self.hud.add_message("The Abyssal King has been defeated!")
        
        # Rewards
        self.player.add_gold(500)
        self.player.add_xp(200)
        
        # Calculate score
        score = self.player.endless_dungeon.calculate_score(
            self.floor_level, self.player.gold, 0
        )
        if self.player.endless_dungeon.update_high_score(score):
            self.hud.add_message(f"New High Score: {score}!")
        
        # Offer NG+
        self.hud.add_message("New Game+ available! Return to town to begin.")
        self.save_mgr.save_progress(self.player)

    def _start_new_game_plus(self):
        """Start NG+: carry over roster/companions, reset dungeon."""
        from systems.new_game_plus import prepare_ngp, apply_ngp, NGPlusState
        
        state = prepare_ngp(self.player, self.player.monster_roster)
        
        # Reset player
        self.player = Player(0, 0)
        self.player.reparent_to(self.render)
        self.player.ngp_state = state
        
        # Reset enemies
        self.enemies = [Enemy(f"Foe {i}", 0, 0) for i in range(ENEMY_COUNT)]
        for e in self.enemies:
            e.reparent_to(self.render)
        
        self.spawn_sys = SpawnSystem(self.map, self.player, self.enemies)
        self.turns = TurnSystem(self.player, self.enemies, self.map, self.hud.add_message,
                                kill_callback=self._on_enemy_killed,
                                post_enemy_callback=self._resolve_companion_turns)
        
        # Apply carry-over
        apply_ngp(self.player, self.player.monster_roster, state)
        
        # Reset companions
        COMP_IDS = ["lyra", "brom", "mira", "sable", "finn"]
        existing = {c.companion_id for c in self.player.companions}
        for cid in COMP_IDS:
            if cid not in existing:
                from entities.companion import Companion
                self.player.companions.append(Companion(cid))
        
        self._boss_fight_active = False
        self.hud.add_message(f"New Game+ {state.ngp_level}! Dungeons are harder!")
        self.enter_town()
        self._set_menu(MENU_NONE)

    # ------------------------------------------------------------------ #
    #  Phase 15 – Life Sim: NPCs, Home, Festivals                            #
    # ------------------------------------------------------------------ #

    def _setup_npcs(self):
        """Load and place NPCs in town."""
        # Clear old NPCs and labels
        for npc in self.npcs:
            if npc._node:
                npc._node.removeNode()
        for label in self._npc_labels.values():
            label.removeNode()
        self.npcs = []
        self._npc_labels = {}

        from direct.gui.OnscreenText import OnscreenText
        from panda3d.core import TextNode

        for npc_id in list_npc_ids():
            npc = NPC(npc_id)
            npc.reparent_to(self.render)
            self.npcs.append(npc)
            npc.node.show()

            # Create name label above NPC
            label = OnscreenText(
                text=npc.name,
                pos=(0, 0), scale=0.04,
                fg=(1.0, 1.0, 0.8, 1), align=TextNode.ACenter,
                parent=self.render2d,
            )
            self._npc_labels[npc_id] = label

    def _update_npc_labels(self):
        """Update NPC label positions to follow NPCs in screen space."""
        if not hasattr(self, '_npc_labels'):
            return
        for npc in self.npcs:
            label = self._npc_labels.get(npc.npc_id)
            if not label:
                continue
            # Convert 3D position to 2D screen position
            pos3d = npc.node.getPos(self.render)
            pos3d.setZ(pos3d.getZ() + 1.2)
            pos2d = self.cam.getRelativePoint(self.render, pos3d)
            if self.camLens:
                pos2d = self.camLens.project(pos2d)
                if pos2d:
                    x, y = pos2d
                    label.setPos(x, y)
                    # Hide if behind camera
                    if pos3d.getY(self.cam) < 0:
                        label.hide()
                    else:
                        label.show()

    def _get_nearby_npc(self) -> Optional[NPC]:
        """Find the closest NPC to the player."""
        best = None
        best_dist = 3.0  # Interaction radius
        for npc in self.npcs:
            dist = abs(npc.x - self.player.x) + abs(npc.y - self.player.y)
            if dist < best_dist:
                best_dist = dist
                best = npc
        return best

    def _input_home(self):
        """H key: enter/exit player house."""
        if self.game_state != STATE_TOWN:
            self.hud.add_message("Can only enter home in town.")
            return
        if self.home._is_visible:
            self.home.hide()
            self.hud.add_message("Left the house.")
        else:
            self.home.build_visuals(self.render)
            self.home.show()
            self.hud.add_message("Entered your cozy home. Press H to leave.")

    def _input_talk_npc(self):
        """T key: talk to nearby NPC."""
        if self.game_state != STATE_TOWN:
            self.hud.add_message("No NPCs here.")
            return
        npc = self._get_nearby_npc()
        if npc:
            context = "festival" if self.festivals.active_festival else "default"
            if npc.affection >= 75:
                context = "high_affection"
            msg = npc.talk(context)
            self.hud.add_message(msg)
            # Small affection boost for talking
            if hasattr(self, 'progression'):
                self.progression.add_companion_bond(npc.npc_id, 1)
        else:
            self.hud.add_message("No NPC nearby. Press T when close to someone.")

    def _input_gift_npc(self):
        """G key: give gift to nearby NPC."""
        if self.game_state != STATE_TOWN:
            return
        if not self.player.inventory:
            self.hud.add_message("No items to gift.")
            return
        npc = self._get_nearby_npc()
        if not npc:
            self.hud.add_message("No NPC nearby.")
            return
        item = self.player.inventory[0]
        delta, msg = npc.gift_item(item.key)
        self.hud.add_message(msg)
        if delta > 0:
            self.player.inventory.pop(0)
            if hasattr(self, 'progression'):
                self.progression.add_companion_bond(npc.npc_id, 2)

    # ------------------------------------------------------------------ #
    #  Phase 15 – Festival Screen                                           #
    # ------------------------------------------------------------------ #

    def _festival_participate(self):
        """Participate in the active festival."""
        if not self.festivals.active_festival:
            return
        score = random.randint(50, 150)
        msgs = self.festivals.complete_festival(score)
        for m in msgs:
            self.hud.add_message(m)
        self._festival_close()

    def _festival_skip(self):
        """Skip the festival for now."""
        self.festivals.active_festival = None
        self._festival_close()

    def _festival_close(self):
        """Close festival screen."""
        self.festival_screen.hide()
        self._set_menu(MENU_NONE)

    def _show_festival_if_active(self):
        """Check and display festival screen if one is active."""
        if self.festivals.active_festival and self.game_state == STATE_TOWN:
            self._set_menu(MENU_FESTIVAL)
            self.festival_screen.show(self.festivals.active_festival)
