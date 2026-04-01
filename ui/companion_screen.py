"""
Phase 10 – Companion Screen.

Shows companion roster, affection meters, support ranks, and gift/talk options.
"""
from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from entities.companion import SUPPORT_RANKS, COMPANION_COLORS
from ui.menu_theme import HINT, TITLE_GOLD


class CompanionScreen:
    """Overlay panel showing companion info."""

    def __init__(self):
        self._lines = []
        self._build_panel()
        self.hide()

    def _build_panel(self):
        self._title = OnscreenText(
            text="Companions",
            pos=(0, 0.40), scale=0.08,
            fg=TITLE_GOLD, align=TextNode.ACenter, mayChange=True,
            shadow=(0.05, 0.04, 0.02, 1), shadowOffset=(0.03, -0.03),
        )
        self._entries = []
        for i in range(6):
            t = OnscreenText(
                text="",
                pos=(0, 0.28 - i * 0.12), scale=0.055,
                fg=(0.85, 0.85, 0.85, 1), align=TextNode.ACenter, mayChange=True
            )
            self._entries.append(t)
        self._hint = OnscreenText(
            text="[C] Close",
            pos=(0, -0.48), scale=0.045,
            fg=HINT, align=TextNode.ACenter
        )
        self._lines = [self._title] + self._entries + [self._hint]

    def show(self, companions: list, deployed_ids: set = None) -> None:
        if deployed_ids is None:
            deployed_ids = set()

        for i, entry in enumerate(self._entries):
            if i < len(companions):
                c = companions[i]
                rank = c.support_rank
                rank_idx = SUPPORT_RANKS.index(rank)
                bar = "█" * (rank_idx + 1) + "░" * (4 - rank_idx - 1)
                romance_tag = " ♥" if c.is_romance else ""
                deploy_tag = " [Deployed]" if c.companion_id in deployed_ids else ""
                color = COMPANION_COLORS.get(c.companion_id, (0.8, 0.8, 0.8, 1))
                entry.setText(
                    f"{c.name} Lv.{rank}{romance_tag}{deploy_tag}  [{bar}]  "
                    f"Affection: {c.affection}/100"
                )
                entry.setFg(color)
            else:
                entry.setText("")

        for node in self._lines:
            node.show()

    def hide(self) -> None:
        for node in self._lines:
            node.hide()

    @property
    def is_visible(self) -> bool:
        return not self._title.isHidden()
