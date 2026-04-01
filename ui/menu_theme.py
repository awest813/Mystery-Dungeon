"""
Shared DirectGUI styling for fullscreen menus and modal overlays.

Cohesive “handheld RPG” look: deep blue-gray panels, teal highlights, gold accents.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Tuple

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui import DirectGuiGlobals as DGG

# --- Colors (RGBA, 0–1) ---

OVERLAY_BG = (0.02, 0.04, 0.09, 0.91)

CARD_FACE = (0.05, 0.08, 0.14, 0.96)

TITLE_CYAN = (0.48, 0.86, 0.96, 1.0)
TITLE_SILVER = (0.82, 0.86, 0.93, 1.0)
TITLE_DANGER = (0.98, 0.42, 0.38, 1.0)
TITLE_GOLD = (0.93, 0.76, 0.32, 1.0)
TITLE_DEBUG = (0.98, 0.52, 0.32, 1.0)
TITLE_MINT = (0.5, 0.86, 0.62, 1.0)

SUBTITLE = (0.52, 0.6, 0.72, 1.0)
BODY = (0.76, 0.79, 0.85, 1.0)
MUTED = (0.4, 0.44, 0.52, 1.0)
HINT = (0.36, 0.4, 0.48, 1.0)

TEXT_ON_BTN = (0.93, 0.94, 0.97, 1.0)

BTN_IDLE = (0.09, 0.13, 0.22, 0.94)
BTN_HOVER = (0.14, 0.38, 0.55, 0.99)

BTN_DANGER_IDLE = (0.2, 0.1, 0.12, 0.94)
BTN_DANGER_HOVER = (0.48, 0.16, 0.2, 0.99)

BTN_DEBUG_IDLE = (0.14, 0.11, 0.13, 0.96)
BTN_DEBUG_HOVER = (0.32, 0.18, 0.2, 0.99)

DISABLED_LABEL = (0.38, 0.4, 0.45, 1.0)

ROW_SELECTED = (0.94, 0.8, 0.34, 1.0)
ROW_NORMAL = (0.72, 0.75, 0.8, 1.0)

DEFAULT_OVERLAY_SIZE = (-2.0, 2.0, -1.5, 1.5)


def menu_backdrop(
    parent,
    *,
    frame_size: Tuple[float, float, float, float] = DEFAULT_OVERLAY_SIZE,
    rgba: Tuple[float, float, float, float] | None = None,
) -> DirectFrame:
    return DirectFrame(
        frameColor=rgba or OVERLAY_BG,
        frameSize=frame_size,
        parent=parent,
    )


def menu_card(
    parent,
    frame_size: Tuple[float, float, float, float],
    *,
    pos: Tuple[float, float, float] = (0, 0, 0.02),
) -> DirectFrame:
    """Inset panel with a subtle raised border."""
    return DirectFrame(
        parent=parent,
        pos=pos,
        frameSize=frame_size,
        frameColor=CARD_FACE,
        relief=DGG.RIDGE,
        borderWidth=(0.014, 0.014),
    )


def create_menu_button(
    parent,
    text: str,
    pos: Tuple[float, float],
    command: Callable,
    *,
    scale: float = 0.06,
    frame_width: Tuple[float, float] = (-1.28, 1.28),
    frame_height: Tuple[float, float] = (-0.27, 0.27),
    variant: str = "default",
) -> DirectButton:
    if variant == "danger":
        idle, hover = BTN_DANGER_IDLE, BTN_DANGER_HOVER
    elif variant == "debug":
        idle, hover = BTN_DEBUG_IDLE, BTN_DEBUG_HOVER
    else:
        idle, hover = BTN_IDLE, BTN_HOVER

    btn = DirectButton(
        text=text,
        pos=(pos[0], pos[1]),
        command=command,
        scale=scale,
        text_fg=TEXT_ON_BTN,
        frameColor=idle,
        frameSize=(*frame_width, *frame_height),
        relief=DGG.RIDGE,
        borderWidth=(0.008, 0.008),
        parent=parent,
    )

    btn.bind("enter", lambda _e, b=btn, h=hover: b.setFrameColor(h))
    btn.bind("exit", lambda _e, b=btn, i=idle: b.setFrameColor(i))
    return btn
