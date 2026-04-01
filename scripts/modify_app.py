import sys

fn = r"d:\Games\Mystery-Dungeon\game\app.py"
with open(fn, 'r', encoding='utf-8') as f:
    data = f.read()

# 1. Imports
if 'from ui.debug_menu import DebugMenu' not in data:
    data = data.replace(
        'from ui.festival_screen import FestivalScreen',
        'from ui.festival_screen import FestivalScreen\nfrom ui.debug_menu import DebugMenu'
    )

# 2. Constants
if 'MENU_DEBUG = 7' not in data:
    data = data.replace(
        'MENU_FESTIVAL = 6',
        'MENU_FESTIVAL = 6\nMENU_DEBUG = 7'
    )

# 3. Initialization
if 'self.debug_menu = DebugMenu' not in data:
    initialization_block = """            on_skip=self._festival_skip,
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
        )"""
    data = data.replace(
        '            on_skip=self._festival_skip,\n            on_close=self._festival_close,\n        )',
        initialization_block
    )

# 4. Input binding
if 'self.accept("f1", self._input_debug)' not in data:
    data = data.replace(
        '        self.accept("escape", self._input_menu)',
        '        self.accept("escape", self._input_menu)\n        self.accept("f1", self._input_debug)'
    )

# 5. Menu states
if 'self.debug_menu.hide()' not in data:
    data = data.replace(
        '        self.ranch_screen.hide()',
        '        self.ranch_screen.hide()\n        self.debug_menu.hide()'
    )

if 'elif state == MENU_DEBUG:' not in data:
    data = data.replace(
        '        elif state == MENU_FESTIVAL:',
        '        elif state == MENU_FESTIVAL:\n            self.hud.hide()\n            if self.festivals.active_festival:\n                self.festival_screen.show(self.festivals.active_festival)\n        elif state == MENU_DEBUG:\n            self.debug_menu.show()'
    )
    # Correct previous entry
    data = data.replace(
        '        elif state == MENU_FESTIVAL:\n            self.hud.hide()\n            if self.festivals.active_festival:\n                self.festival_screen.show(self.festivals.active_festival)\n        elif state == MENU_FESTIVAL:',
        '        elif state == MENU_FESTIVAL:'
    )

if 'elif state == MENU_DEBUG:' not in data: # input handling
    data = data.replace(
        '        elif state == MENU_RANCH:\n            self._set_menu(MENU_NONE)',
        '        elif state == MENU_RANCH:\n            self._set_menu(MENU_NONE)\n        elif state == MENU_DEBUG:\n            self._set_menu(MENU_NONE)'
    )

# 6. Debug Methods - Add before _on_new_game
if 'def _input_debug(self):' not in data:
    debug_methods = """
    # ------------------------------------------------------------------ #
    #  Debug Actions                                                       #
    # ------------------------------------------------------------------ #

    def _input_debug(self):
        \"\"\"F1 key: toggle debug menu.\"\"\"
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

"""
    data = data.replace('    def _on_new_game(self):', debug_methods + '    def _on_new_game(self):')

with open(fn, 'w', encoding='utf-8', newline='\n') as f:
    f.write(data)

print("Modification successful!")
