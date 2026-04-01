"""
Phase 12 - Ranch Screen.
UI for managing captured monsters, renaming, deploying, and evolving.
"""
from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from ui.menu_theme import (
    BODY,
    HINT,
    ROW_NORMAL,
    ROW_SELECTED,
    TITLE_MINT,
    menu_backdrop,
    menu_card,
)


class RanchScreen:
    def __init__(self, parent, on_deploy=None, on_evolve=None, on_close=None):
        self._parent = parent
        self._on_deploy = on_deploy
        self._on_evolve = on_evolve
        self._on_close = on_close

        self._frame = menu_backdrop(parent)
        self._card = menu_card(self._frame, (-1.72, 1.72, -1.28, 1.05))
        self._frame.hide()

        self._nodes = []
        self._selected_idx = 0
        self._monsters = []
        self._inventory = []
        self._build()

    def _build(self):
        title = OnscreenText(
            text="MONSTER RANCH",
            pos=(0, 0.52), scale=0.085,
            fg=TITLE_MINT, align=TextNode.ACenter,
            parent=self._card,
            shadow=(0.02, 0.06, 0.04, 1), shadowOffset=(0.03, -0.03),
        )
        self._nodes.append(title)

        self._item_texts = []
        for i in range(10):
            t = OnscreenText(
                text="",
                pos=(0, 0.38 - i * 0.09), scale=0.048,
                fg=ROW_NORMAL, align=TextNode.ACenter,
                parent=self._card,
            )
            self._item_texts.append(t)
            self._nodes.append(t)

        detail = OnscreenText(
            text="",
            pos=(0, -0.62), scale=0.042,
            fg=BODY, align=TextNode.ACenter,
            parent=self._card,
        )
        self._detail_text = detail
        self._nodes.append(detail)

        hint = OnscreenText(
            text="↑↓:Select  Enter:Toggle Deploy  E:Evolve  Esc:Close",
            pos=(0, -0.78), scale=0.032,
            fg=HINT, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(hint)

    def show(self, monsters, inventory_items):
        self._monsters = monsters or []
        self._inventory = inventory_items or []
        self._selected_idx = 0
        self._frame.show()
        self._card.show()

        for i, t in enumerate(self._item_texts):
            if i < len(self._monsters):
                m = self._monsters[i]
                tag = "[Deployed]" if m.is_deployed else ""
                t.setText(f"  {m.name} (Lv{m.level} {m.monster_type}) {tag}")
                t.setFg(ROW_NORMAL)
            else:
                t.setText("")

        self._update_selection()
        for n in self._nodes:
            n.show()

    def _update_selection(self):
        for i, t in enumerate(self._item_texts):
            if i == self._selected_idx:
                t.setFg(ROW_SELECTED)
            elif i < len(self._monsters):
                t.setFg(ROW_NORMAL)

        if self._selected_idx < len(self._monsters):
            m = self._monsters[self._selected_idx]
            desc = f"HP: {m.max_hp} | ATK: {m.attack_power} | XP: {m.xp}"

            ev = m.check_evolution(self._inventory)
            if ev:
                item_req = ev.get('item_req')
                req_str = f" + {item_req}" if item_req else ""
                desc += f"\nCan Evolve into {ev['evolved_type']}! (Requires Lv{ev['level_req']}{req_str})"

            self._detail_text.setText(desc)
        else:
            self._detail_text.setText("")

    def navigate(self, direction):
        if not self._monsters:
            return
        self._selected_idx = (self._selected_idx + direction) % len(self._monsters)
        self._update_selection()

    def deploy_selected(self):
        if self._selected_idx < len(self._monsters) and self._on_deploy:
            self._on_deploy(self._selected_idx)

    def evolve_selected(self):
        if self._selected_idx < len(self._monsters) and self._on_evolve:
            self._on_evolve(self._selected_idx)

    def hide(self):
        self._frame.hide()
        self._card.hide()
        for n in self._nodes:
            n.hide()

    def destroy(self):
        self._frame.destroy()
