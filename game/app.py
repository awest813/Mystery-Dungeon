import random

from direct.showbase.ShowBase import ShowBase
import simplepbr

from world.tilemap import TileMap
from world.dungeon_generator import DungeonGenerator
from entities.player import Player
from entities.enemy import Enemy
from entities.items import Item, random_item_for_floor
from systems.turn_system import TurnSystem
from systems.spawn_system import SpawnSystem
from game.save_manager import SaveManager
from ui.hud import GameHUD

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

        # Inventory: F = use first item, Z = drop first item, E = print stats/save
        self.accept("f", self._input_use_item)
        self.accept("z", self._input_drop_item)
        self.accept("e", self._input_action)

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
        self.map.setup_visuals()

        self.player.move_to(15, 14)
        self.player.hp = self.player.max_hp
        self.player.hunger = self.player.max_hunger
        self.player.cure_all_statuses()
        self.player.restore_skill_pp()

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
        """Called after any player move. Handles pickups, traps, stairs."""
        px, py = self.player.x, self.player.y

        # Item pickup
        if self.map.is_item(px, py):
            item_key = random_item_for_floor(self.floor_level)
            item = Item(item_key)
            if self.player.pick_up_item(item):
                self.hud.add_message(f"Picked up {item.display}!")
            else:
                self.hud.add_message(f"Bag full! Left {item.display} behind.")
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
            self.hud.add_message("Orb of Sight! Floor revealed.")
            # (Visual reveal would require full minimap; log the info)
        elif effect == "confuse_enemies":
            for e in self.enemies:
                if not e.is_dead:
                    e.apply_status("confused", self.hud.add_message)
        elif effect == "paralyze_enemies":
            for e in self.enemies:
                if not e.is_dead:
                    e.apply_status("paralyzed", self.hud.add_message)
        elif effect == "escape_dungeon":
            self.hud.add_message("Escape Orb! Returning to town...")
            self.taskMgr.doMethodLater(0.8, lambda t: (self.enter_town(), t.done)[1],
                                       "escape_orb")
        self.player.inventory.pop(inv_idx)
        self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _input_drop_item(self):
        if not self.player.inventory:
            self.hud.add_message("Nothing to drop.")
            return
        dropped = self.player.drop_item(0)
        if dropped:
            self.hud.add_message(f"Dropped {dropped.display}.")
            self.hud.update(self.player, self.floor_level, self.game_state == STATE_TOWN)

    def _input_action(self):
        """E key: save in town, print debug stats in dungeon."""
        if self.player.is_dead:
            self.enter_town()
            return
        if self.game_state == STATE_TOWN:
            self.save_mgr.save_progress(self.player)
            self.hud.add_message("Progress saved.")
        else:
            inv_str = ", ".join(i.display for i in self.player.inventory) or "empty"
            self.hud.add_message(
                f"Lv{self.player.level} HP:{int(self.player.hp)} ATK:{self.player.effective_attack}"
            )
            self.hud.add_message(f"Bag: {inv_str}")
