"""
Phase 11 – Death Screen.

Game over overlay with rescue (return to town with penalties) or quit options.
"""
from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from ui.menu_theme import (
    BODY,
    HINT,
    MUTED,
    TITLE_DANGER,
    create_menu_button,
    menu_backdrop,
    menu_card,
)


class DeathScreen:
    """Game over overlay with rescue/quit choices."""

    def __init__(self, parent, on_rescue=None, on_quit=None):
        self._parent = parent
        self._on_rescue = on_rescue
        self._on_quit = on_quit

        self._frame = menu_backdrop(parent)
        self._card = menu_card(self._frame, (-1.65, 1.65, -1.15, 1.15))
        self._frame.hide()

        self._nodes = []
        self._buttons = []
        self._build()

    def _build(self):
        title = OnscreenText(
            text="DEFEATED",
            pos=(0, 0.38), scale=0.12,
            fg=TITLE_DANGER, align=TextNode.ACenter,
            parent=self._card,
            shadow=(0.08, 0.02, 0.02, 1), shadowOffset=(0.04, -0.04),
        )
        self._nodes.append(title)

        msg = OnscreenText(
            text="Your party has fallen in the dungeon...",
            pos=(0, 0.24), scale=0.048,
            fg=BODY, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(msg)

        penalty = OnscreenText(
            text="Rescue: Return to town. Lose 10% gold and half hunger.",
            pos=(0, 0.10), scale=0.038,
            fg=MUTED, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(penalty)

        if self._on_rescue:
            rescue_btn = create_menu_button(
                self._card,
                "Rescue (Return to Town)",
                (0, -0.12),
                self._on_rescue,
                scale=0.058,
                frame_width=(-1.35, 1.35),
                frame_height=(-0.26, 0.26),
            )
            self._buttons.append(rescue_btn)

        if self._on_quit:
            quit_btn = create_menu_button(
                self._card,
                "Quit to Title",
                (0, -0.34),
                self._on_quit,
                scale=0.058,
                frame_width=(-1.35, 1.35),
                frame_height=(-0.26, 0.26),
                variant="danger",
            )
            self._buttons.append(quit_btn)

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

    def destroy(self):
        self._frame.destroy()
