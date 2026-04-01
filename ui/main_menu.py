"""
Phase 11 – Main Menu.

Title screen with New Game, Continue, Options, and Exit.
Animated background with floating particles and title text.
"""
from __future__ import annotations

import os

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from ui.menu_theme import (
    DISABLED_LABEL,
    HINT,
    SUBTITLE,
    TITLE_CYAN,
    create_menu_button,
    menu_backdrop,
    menu_card,
)


class MainMenu:
    """Title screen overlay with menu buttons."""

    def __init__(self, parent, on_new_game=None, on_continue=None,
                 on_options=None, on_exit=None, on_ngp=None):
        self._parent = parent
        self._on_new_game = on_new_game
        self._on_continue = on_continue
        self._on_options = on_options
        self._on_exit = on_exit
        self._on_ngp = on_ngp

        self._frame = menu_backdrop(parent)
        self._card = menu_card(self._frame, (-1.78, 1.78, -1.22, 1.22))
        self._frame.hide()

        self._nodes = []
        self._buttons = []
        self._build()

    def _build(self):
        self._frame.show()

        title = OnscreenText(
            text="MYSTERY DUNGEON",
            pos=(0, 0.52), scale=0.13,
            fg=TITLE_CYAN, align=TextNode.ACenter,
            parent=self._card,
            shadow=(0.02, 0.04, 0.08, 1), shadowOffset=(0.045, -0.045),
        )
        subtitle = OnscreenText(
            text="A PSP-Style Dungeon Crawler",
            pos=(0, 0.38), scale=0.048,
            fg=SUBTITLE, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.extend([title, subtitle])

        has_save = os.path.exists("save_data.json")

        btn_scale = 0.065
        btn_w = (-1.52, 1.52)
        btn_h = (-0.3, 0.3)

        y_positions = [0.22, 0.05, -0.12, -0.29, -0.46]
        callbacks = [
            self._on_new_game,
            self._on_continue if has_save else None,
            self._on_ngp if self._on_ngp else None,
            self._on_options,
            self._on_exit,
        ]
        labels = ["New Game", "Continue", "New Game+", "Options", "Exit"]

        for y, cb, label in zip(y_positions, callbacks, labels):
            if cb is None:
                btn = OnscreenText(
                    text=label,
                    pos=(0, y), scale=0.055,
                    fg=DISABLED_LABEL, align=TextNode.ACenter,
                    parent=self._card,
                )
                self._nodes.append(btn)
            else:
                btn = create_menu_button(
                    self._card,
                    label,
                    (0, y),
                    cb,
                    scale=btn_scale,
                    frame_width=btn_w,
                    frame_height=btn_h,
                )
                self._buttons.append(btn)

        version = OnscreenText(
            text="v0.11.0",
            pos=(0, -0.58), scale=0.032,
            fg=HINT, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(version)

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
