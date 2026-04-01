"""
Phase 15 - Festival Screen UI.

Displays active festival info, mini-game interface, and reward collection.
"""
from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from ui.menu_theme import (
    BODY,
    HINT,
    MUTED,
    TITLE_GOLD,
    create_menu_button,
    menu_backdrop,
    menu_card,
)


class FestivalScreen:
    """Festival event overlay with info and participation options."""

    def __init__(self, parent, on_participate=None, on_skip=None, on_close=None):
        self._parent = parent
        self._on_participate = on_participate
        self._on_skip = on_skip
        self._on_close = on_close

        self._frame = menu_backdrop(parent)
        self._card = menu_card(self._frame, (-1.62, 1.62, -1.12, 1.12))
        self._frame.hide()

        self._nodes = []
        self._buttons = []
        self._build()

    def _build(self):
        self._title = OnscreenText(
            text="",
            pos=(0, 0.42), scale=0.085,
            fg=TITLE_GOLD, align=TextNode.ACenter,
            parent=self._card,
            shadow=(0.06, 0.04, 0.02, 1), shadowOffset=(0.035, -0.035),
        )
        self._nodes.append(self._title)

        self._desc = OnscreenText(
            text="",
            pos=(0, 0.28), scale=0.048,
            fg=BODY, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(self._desc)

        self._rewards = OnscreenText(
            text="",
            pos=(0, 0.14), scale=0.042,
            fg=MUTED, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(self._rewards)

        if self._on_participate:
            btn = create_menu_button(
                self._card,
                "Participate!",
                (0, -0.08),
                self._on_participate,
                scale=0.058,
                frame_width=(-1.22, 1.22),
                frame_height=(-0.25, 0.25),
            )
            self._buttons.append(btn)

        if self._on_skip:
            btn = create_menu_button(
                self._card,
                "Skip for Now",
                (0, -0.28),
                self._on_skip,
                scale=0.058,
                frame_width=(-1.22, 1.22),
                frame_height=(-0.25, 0.25),
            )
            self._buttons.append(btn)

        hint = OnscreenText(
            text="Press Esc to close",
            pos=(0, -0.48), scale=0.032,
            fg=HINT, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(hint)

    def show(self, festival):
        self._title.setText(f"{festival.name}")
        self._desc.setText(festival.description)
        reward_str = " | ".join(f"+{v} {k}" for k, v in festival.rewards.items())
        self._rewards.setText(f"Rewards: {reward_str}")
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

    @property
    def is_visible(self):
        return not self._frame.isHidden()
