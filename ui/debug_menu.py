from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from ui.menu_theme import (
    HINT,
    TITLE_DEBUG,
    create_menu_button,
    menu_backdrop,
    menu_card,
)


class DebugMenu:
    """Debug and Cheat overlay for development testing."""

    def __init__(self, parent,
                 on_heal=None,
                 on_gold=None,
                 on_items=None,
                 on_village=None,
                 on_skip=None,
                 on_level=None,
                 on_godmode=None,
                 on_close=None):
        self._parent = parent
        self._on_heal = on_heal
        self._on_gold = on_gold
        self._on_items = on_items
        self._on_village = on_village
        self._on_skip = on_skip
        self._on_level = on_level
        self._on_godmode = on_godmode
        self._on_close = on_close

        self._frame = menu_backdrop(
            parent,
            frame_size=(-0.88, 0.88, -0.94, 0.94),
        )
        self._card = menu_card(self._frame, (-0.82, 0.82, -0.88, 0.88))
        self._frame.hide()

        self._nodes = []
        self._buttons = []
        self._build()

    def _build(self):
        title = OnscreenText(
            text="DEBUG MENU",
            pos=(0, 0.78), scale=0.072,
            fg=TITLE_DEBUG, align=TextNode.ACenter,
            parent=self._card,
            shadow=(0.05, 0.02, 0.02, 1), shadowOffset=(0.03, -0.03),
        )
        self._nodes.append(title)

        hint = OnscreenText(
            text="Developer tools — use sparingly",
            pos=(0, 0.66), scale=0.032,
            fg=HINT, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(hint)

        options = [
            ("Heal Player", self._on_heal),
            ("Give 1000 Gold", self._on_gold),
            ("Give Items (Loot Roll)", self._on_items),
            ("Return to Town", self._on_village),
            ("Skip Floor", self._on_skip),
            ("Level Up (+5)", self._on_level),
            ("Toggle God Mode", self._on_godmode),
            ("Close Debug [F1]", self._on_close),
        ]

        y_start = 0.52
        y_step = 0.13

        for i, (label, cb) in enumerate(options):
            if cb is None:
                continue
            y_pos = y_start - (i * y_step)
            btn = create_menu_button(
                self._card,
                label,
                (0, y_pos),
                cb,
                scale=0.048,
                frame_width=(-1.15, 1.15),
                frame_height=(-0.22, 0.22),
                variant="debug",
            )
            self._buttons.append(btn)

    def show(self):
        self._frame.show()
        self._card.show()
        for n in self._nodes:
            n.show()
        for b in self._buttons:
            b.show()

    def hide(self):
        self._frame.hide()
        self._card.hide()
        for n in self._nodes:
            n.hide()
        for b in self._buttons:
            b.hide()

    def is_visible(self):
        return not self._frame.isHidden()

    def destroy(self):
        self._frame.destroy()
