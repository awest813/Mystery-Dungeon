"""
Phase 11 – Inventory Screen.

Full inventory grid showing all items with use/drop/equip actions.
Navigated with arrow keys, actions with Enter/Escape.
"""
from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from ui.menu_theme import (
    BODY,
    HINT,
    ROW_NORMAL,
    ROW_SELECTED,
    TITLE_SILVER,
    menu_backdrop,
    menu_card,
)


class InventoryScreen:
    """Full inventory overlay with item management."""

    def __init__(self, parent, on_use=None, on_drop=None, on_equip=None, on_close=None):
        self._parent = parent
        self._on_use = on_use
        self._on_drop = on_drop
        self._on_equip = on_equip
        self._on_close = on_close

        self._frame = menu_backdrop(parent)
        self._card = menu_card(self._frame, (-1.72, 1.72, -1.28, 1.05))
        self._frame.hide()

        self._nodes = []
        self._selected_idx = 0
        self._items = []
        self._build()

    def _build(self):
        title = OnscreenText(
            text="INVENTORY",
            pos=(0, 0.52), scale=0.085,
            fg=TITLE_SILVER, align=TextNode.ACenter,
            parent=self._card,
            shadow=(0.02, 0.04, 0.08, 1), shadowOffset=(0.03, -0.03),
        )
        self._nodes.append(title)

        self._item_texts = []
        for i in range(12):
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
            text="↑↓:Select  Enter:Use  E:Equip  D:Drop  Esc:Close",
            pos=(0, -0.78), scale=0.032,
            fg=HINT, align=TextNode.ACenter,
            parent=self._card,
        )
        self._nodes.append(hint)

    def show(self, items, player=None):
        self._items = items or []
        self._selected_idx = 0
        self._frame.show()
        self._card.show()

        for i, t in enumerate(self._item_texts):
            if i < len(self._items):
                item = self._items[i]
                name = item.display_name
                cat = item.category
                t.setText(f"  {name}  [{cat}]")
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
            elif i < len(self._items):
                t.setFg(ROW_NORMAL)

        if self._selected_idx < len(self._items):
            item = self._items[self._selected_idx]
            desc = getattr(item, 'description', '')
            affix_str = ""
            if hasattr(item, 'affixes') and item.affixes:
                affix_str = f"\n  Affixes: {', '.join(item.affix_descs())}"
            self._detail_text.setText(f"{desc}{affix_str}")
        else:
            self._detail_text.setText("")

    def navigate(self, direction):
        if not self._items:
            return
        self._selected_idx = (self._selected_idx + direction) % len(self._items)
        self._update_selection()

    def use_selected(self):
        if self._selected_idx < len(self._items) and self._on_use:
            self._on_use(self._selected_idx)

    def drop_selected(self):
        if self._selected_idx < len(self._items) and self._on_drop:
            self._on_drop(self._selected_idx)

    def equip_selected(self):
        if self._selected_idx < len(self._items) and self._on_equip:
            self._on_equip(self._selected_idx)

    def hide(self):
        self._frame.hide()
        self._card.hide()
        for n in self._nodes:
            n.hide()

    def destroy(self):
        self._frame.destroy()
