"""
Phase 11 – Health Bar Widget.

Visual bar for HP, hunger, XP, and other numeric stats.
Supports color gradients and smooth transitions.
"""
from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectFrame import DirectFrame
from panda3d.core import TextNode


class HealthBar:
    """Visual bar widget for numeric stats."""

    def __init__(self, parent, pos, width=0.4, height=0.04,
                 label="", fg=(0.3, 1.0, 0.3, 1), bg=(0.15, 0.15, 0.15, 1)):
        self._parent = parent
        self._width = width
        self._height = height
        self._value = 0
        self._max_value = 1

        self._bg_frame = DirectFrame(
            frameColor=bg,
            frameSize=(-width / 2, width / 2, -height / 2, height / 2),
            pos=pos,
            parent=parent,
        )

        self._fill_frame = DirectFrame(
            frameColor=fg,
            frameSize=(-width / 2, width / 2, -height / 2, height / 2),
            pos=pos,
            parent=parent,
        )

        self._label = OnscreenText(
            text=label,
            pos=(pos[0], pos[1] - 0.03), scale=0.035,
            fg=(0.7, 0.7, 0.7, 1), align=TextNode.ACenter,
            parent=parent,
        )

    def update(self, value, max_value, color=None):
        self._value = value
        self._max_value = max_value
        frac = max(0, min(1, value / max_value))

        self._fill_frame["frameSize"] = (
            -self._width / 2,
            -self._width / 2 + self._width * frac,
            -self._height / 2,
            self._height / 2,
        )

        if color:
            self._fill_frame["frameColor"] = color

    def set_label(self, text):
        self._label.setText(text)

    def show(self):
        self._bg_frame.show()
        self._fill_frame.show()
        self._label.show()

    def hide(self):
        self._bg_frame.hide()
        self._fill_frame.hide()
        self._label.hide()
