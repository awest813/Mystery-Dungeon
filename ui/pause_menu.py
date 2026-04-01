"""
Phase 11 – Pause Menu.

In-game pause overlay with Inventory, Skills, Save, and Quit options.
Opens with Escape key.
"""
from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from ui.menu_theme import (
    HINT,
    TITLE_SILVER,
    create_menu_button,
    menu_backdrop,
    menu_card,
)


class PauseMenu:
    """Pause overlay with game management options."""

    def __init__(self, parent, on_resume=None, on_inventory=None,
                 on_skills=None, on_save=None, on_quit=None, on_debug=None):
        self._parent = parent
        self._on_resume = on_resume
        self._on_inventory = on_inventory
        self._on_skills = on_skills
        self._on_save = on_save
        self._on_quit = on_quit
        self._on_debug = on_debug

        self._frame = menu_backdrop(parent)
        self._card = menu_card(self._frame, (-1.55, 1.55, -1.12, 1.12))
        self._frame.hide()

        self._nodes = []
        self._buttons = []
        self._build()

    def _build(self):
        title = OnscreenText(
            text="PAUSED",
            pos=(0, 0.42), scale=0.095,
            fg=TITLE_SILVER, align=TextNode.ACenter,
            parent=self._card,
            shadow=(0.02, 0.04, 0.08, 1), shadowOffset=(0.035, -0.035),
        )
        self._nodes.append(title)

        sub = OnscreenText(
            text="—  take a breath  —",
            pos=(0, 0.30), scale=0.038,
            fg=HINT, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(sub)

        y_positions = [0.16, 0.01, -0.14, -0.29, -0.44, -0.59]
        callbacks = [
            self._on_resume,
            self._on_inventory,
            self._on_skills,
            self._on_save,
            self._on_debug,
            self._on_quit,
        ]
        labels = ["Resume", "Inventory", "Skills", "Save", "Debug Menu", "Quit to Title"]

        for y, cb, label in zip(y_positions, callbacks, labels):
            if cb is None:
                continue
            variant = "danger" if label == "Quit to Title" else "default"
            btn = create_menu_button(
                self._card,
                label,
                (0, y),
                cb,
                scale=0.058,
                frame_width=(-1.22, 1.22),
                frame_height=(-0.24, 0.24),
                variant=variant,
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

    def destroy(self):
        self._frame.destroy()
