"""
Phase 7 - Item Inspection Overlay.

Shows an item's full details: rarity, display name, description,
affix list, flavor text, and identification status.

Toggle with the I key from app.py when the player presses I while
having items in their inventory.
"""

from direct.gui.OnscreenText import OnscreenText
from entities.items import RARITY_TIERS
from panda3d.core import TextNode

from ui.menu_theme import BODY, HINT, MUTED, TITLE_MINT


class ItemScreen:
    """
    Overlay panel that displays details for a selected inventory item.
    The panel is hidden by default; call show(item) to display it and
    hide() to dismiss.
    """

    def __init__(self):
        self._lines = []
        self._build_panel()
        self.hide()

    def _build_panel(self):
        self._bg = OnscreenText(
            text="",
            pos=(0, 0.15), scale=0.07,
            fg=(1, 1, 1, 1), align=TextNode.ACenter,
            mayChange=True, font=None
        )
        self._name_text = OnscreenText(
            text="",
            pos=(0, 0.35), scale=0.08,
            fg=(1.0, 0.9, 0.2, 1), align=TextNode.ACenter,
            mayChange=True
        )
        self._rarity_text = OnscreenText(
            text="",
            pos=(0, 0.22), scale=0.065,
            fg=(0.7, 0.7, 0.7, 1), align=TextNode.ACenter,
            mayChange=True
        )
        self._desc_text = OnscreenText(
            text="",
            pos=(0, 0.08), scale=0.055,
            fg=BODY, align=TextNode.ACenter,
            mayChange=True
        )
        self._affixes_text = OnscreenText(
            text="",
            pos=(0, -0.10), scale=0.055,
            fg=TITLE_MINT, align=TextNode.ACenter,
            mayChange=True
        )
        self._flavor_text = OnscreenText(
            text="",
            pos=(0, -0.28), scale=0.048,
            fg=MUTED, align=TextNode.ACenter,
            mayChange=True
        )
        self._hint_text = OnscreenText(
            text="[I] Close",
            pos=(0, -0.42), scale=0.045,
            fg=HINT, align=TextNode.ACenter,
            mayChange=False
        )
        self._lines = [
            self._bg, self._name_text, self._rarity_text,
            self._desc_text, self._affixes_text, self._flavor_text,
            self._hint_text,
        ]

    def show(self, item):
        """Populate the overlay with item details and make it visible."""
        rarity = getattr(item, 'rarity', 'common')
        rarity_info = RARITY_TIERS.get(rarity, RARITY_TIERS["common"])
        rarity_color = rarity_info["color"]

        display = item.display_name if hasattr(item, 'display_name') else item.display
        self._name_text.setText(display)
        self._name_text.setFg(rarity_color)

        cursed_tag = "  !! CURSED !!" if getattr(item, 'cursed', False) else ""
        rarity_label = rarity_info["display"] + cursed_tag
        self._rarity_text.setText(rarity_label)
        self._rarity_text.setFg(rarity_color)

        desc = getattr(item, 'description', '')
        if not item.is_identified:
            desc = "(Unidentified - use or bring to town to reveal)"
        self._desc_text.setText(desc)

        affixes = getattr(item, 'affixes', [])
        if affixes and item.is_identified:
            affix_lines = "\n".join(f"  • {a.desc}" for a in affixes)
        else:
            affix_lines = ""
        self._affixes_text.setText(affix_lines)

        flavor = getattr(item, 'flavor', '')
        self._flavor_text.setText(f'"{flavor}"' if flavor else "")

        for node in self._lines:
            node.show()

    def hide(self):
        for node in self._lines:
            node.hide()

    @property
    def is_visible(self):
        return not self._name_text.isHidden()
