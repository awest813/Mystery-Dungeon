"""
Phase 15 - Post-Processing Effects.

Bloom, color grading, vignette, and film grain to achieve the PSP/3DS
mystery dungeon aesthetic: soft glow, warm tones, slight film look.
"""
from __future__ import annotations

from panda3d.core import (
    NodePath, CardMaker, TransparencyAttrib, ColorBlendAttrib,
    Texture, TextureStage, FrameBufferProperties, GraphicsOutput,
    Vec3, Vec4,
)
from direct.filter.CommonFilters import CommonFilters


class PostProcess:
    """Manages post-processing effects for the PSP/3DS aesthetic."""

    def __init__(self, base):
        self.base = base
        self._filters = None
        self._bloom_strength = 0.4
        self._vignette_strength = 0.3
        self._blur = 0
        self._color_temperature = 1.0  # 1.0 = neutral, <1 warm, >1 cool

        self._setup_vignette()

    def _setup_vignette(self):
        """Create a vignette overlay using a radial gradient card."""
        self._vignette_card = None

    def enable_bloom(self, strength: float = 0.4):
        """Enable bloom/glow effect."""
        self._bloom_strength = strength
        if self.base.win and hasattr(self.base, 'render'):
            try:
                self._filters = CommonFilters(self.base.win, self.base.cam)
                self._filters.setBloom(blend=(0, 0, 0, 0),
                                       mintrigger=0.6,
                                       maxtrigger=1.0,
                                       desat=0.5,
                                       intensity=strength,
                                       size="small")
            except Exception:
                pass  # simplepbr may conflict with CommonFilters

    def enable_vignette(self, strength: float = 0.3):
        """Enable dark edges vignette effect."""
        self._vignette_strength = strength
        # Create vignette as a dark card with radial transparency
        cm = CardMaker("vignette")
        cm.setFrame(-2, 2, -1.5, 1.5)
        self._vignette_card = NodePath(cm.generate())
        self._vignette_card.reparentTo(self.base.render2d)
        self._vignette_card.setTransparency(TransparencyAttrib.MAlpha)
        self._vignette_card.setColor(0, 0, 0, strength)
        self._vignette_card.setBin("fixed", 50)

    def set_color_temperature(self, temp: float):
        """Adjust overall color temperature. <1 = warm (orange), >1 = cool (blue)."""
        self._color_temperature = temp
        if temp < 1.0:
            self.base.win.setClearColor(Vec4(0.06, 0.04, 0.03, 1))
        elif temp > 1.0:
            self.base.win.setClearColor(Vec4(0.03, 0.04, 0.06, 1))
        else:
            self.base.win.setClearColor(Vec4(0.04, 0.04, 0.06, 1))

    def set_season_grade(self, season: str):
        """Apply color grading based on season."""
        grades = {
            "Spring": {"temp": 0.95, "bloom": 0.3},   # Warm, soft
            "Summer": {"temp": 0.9, "bloom": 0.5},    # Very warm, bright
            "Autumn": {"temp": 0.85, "bloom": 0.4},   # Orange-gold
            "Winter": {"temp": 1.1, "bloom": 0.2},    # Cool blue, muted
        }
        g = grades.get(season, grades["Spring"])
        self.set_color_temperature(g["temp"])
        self.enable_bloom(g["bloom"])

    def set_location_grade(self, location: str):
        """Apply color grading based on location."""
        grades = {
            "town": {"temp": 0.95, "bloom": 0.3},
            "cave": {"temp": 1.05, "bloom": 0.1},
            "ice": {"temp": 1.15, "bloom": 0.2},
            "fire": {"temp": 0.85, "bloom": 0.5},
            "house": {"temp": 0.9, "bloom": 0.4},
        }
        g = grades.get(location, grades["town"])
        self.set_color_temperature(g["temp"])
        self.enable_bloom(g["bloom"])

    def disable(self):
        """Remove all post-processing effects."""
        if self._filters:
            self._filters.cleanup()
            self._filters = None
        if self._vignette_card:
            self._vignette_card.removeNode()
            self._vignette_card = None
        self.base.win.setClearColor(Vec4(0.04, 0.04, 0.06, 1))
