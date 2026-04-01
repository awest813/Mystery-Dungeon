"""
Phase 15 - Particle Systems.

Procedural particle effects for ambient atmosphere: fireflies, seasonal leaves,
snow, rain, torch sparks, and dust motes. All built from Panda3D primitives.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

from panda3d.core import (
    NodePath, CardMaker, TransparencyAttrib, ColorBlendAttrib,
    GeomVertexData, GeomVertexFormat, GeomVertexWriter,
    Geom, GeomTriangles, GeomNode, Vec3, Vec4,
)


def _make_particle_card(size: float, color: Tuple[float, float, float, float]) -> NodePath:
    """Create a single billboard particle card."""
    cm = CardMaker("particle")
    cm.setFrame(-size / 2, size / 2, -size / 2, size / 2)
    node = NodePath(cm.generate())
    node.setColor(*color)
    node.setTransparency(TransparencyAttrib.MAlpha)
    node.setBillboardPointEye()
    return node


class Particle:
    """A single particle with position, velocity, lifetime, and fade."""
    __slots__ = ("x", "y", "z", "vx", "vy", "vz", "life", "max_life", "size", "color", "node", "active")

    def __init__(self, x: float, y: float, z: float,
                 vx: float, vy: float, vz: float,
                 life: float, size: float,
                 color: Tuple[float, float, float, float]):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.node: Optional[NodePath] = None
        self.active = True

    def update(self, dt: float):
        if not self.active:
            return
        self.life -= dt
        if self.life <= 0:
            self.active = False
            if self.node:
                self.node.hide()
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        if self.node:
            self.node.setPos(self.x, self.y, self.z)
            alpha = self.color[3] * (self.life / self.max_life)
            self.node.setColor(self.color[0], self.color[1], self.color[2], alpha)

    def recycle(self, x: float, y: float, z: float,
                vx: float, vy: float, vz: float,
                life: float):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.life = life
        self.max_life = life
        self.active = True
        if self.node:
            self.node.show()
            self.node.setPos(x, y, z)


class ParticleSystem:
    """Manages a pool of particles with emission and recycling."""

    def __init__(self, parent: NodePath, max_particles: int = 60):
        self.parent = parent
        self.max_particles = max_particles
        self.particles: List[Particle] = []
        self.emission_rate = 5.0  # particles per second
        self._emit_timer = 0.0
        self._particle_pool: List[Particle] = []

    def _spawn_particle(self, x: float, y: float, z: float,
                        vx: float, vy: float, vz: float,
                        life: float, size: float,
                        color: Tuple[float, float, float, float]):
        # Try to recycle
        for p in self.particles:
            if not p.active:
                p.recycle(x, y, z, vx, vy, vz, life)
                p.size = size
                p.color = color
                if not p.node:
                    p.node = _make_particle_card(size, color)
                    p.node.reparentTo(self.parent)
                else:
                    p.node.setColor(*color)
                return
        # Create new if under limit
        if len(self.particles) < self.max_particles:
            p = Particle(x, y, z, vx, vy, vz, life, size, color)
            p.node = _make_particle_card(size, color)
            p.node.reparentTo(self.parent)
            self.particles.append(p)

    def update(self, dt: float):
        self._emit_timer += dt
        while self._emit_timer >= 1.0 / max(1, self.emission_rate):
            self._emit_timer -= 1.0 / max(1, self.emission_rate)
            self._emit_one()
        for p in self.particles:
            p.update(dt)

    def _emit_one(self):
        raise NotImplementedError

    def clear(self):
        for p in self.particles:
            if p.node:
                p.node.removeNode()
        self.particles = []
        self._emit_timer = 0.0


class FireflySystem(ParticleSystem):
    """Warm glowing fireflies for evening/summer atmosphere."""
    def _emit_one(self):
        x = random.uniform(-8, 8)
        y = random.uniform(-8, 8)
        z = random.uniform(0.5, 2.0)
        vx = random.uniform(-0.3, 0.3)
        vy = random.uniform(-0.3, 0.3)
        vz = random.uniform(-0.1, 0.2)
        life = random.uniform(3.0, 6.0)
        size = random.uniform(0.08, 0.15)
        color = (1.0, 0.9, 0.3, 0.8)
        self._spawn_particle(x, y, z, vx, vy, vz, life, size, color)


class LeafSystem(ParticleSystem):
    """Falling autumn leaves."""
    def _emit_one(self):
        x = random.uniform(-10, 10)
        y = random.uniform(5, 10)
        z = random.uniform(3.0, 5.0)
        vx = random.uniform(-0.5, 0.5)
        vy = random.uniform(-1.0, -0.3)
        vz = random.uniform(-0.3, -0.1)
        life = random.uniform(4.0, 8.0)
        size = random.uniform(0.06, 0.12)
        colors = [(0.9, 0.5, 0.1, 0.7), (0.8, 0.3, 0.1, 0.6), (0.6, 0.4, 0.1, 0.5)]
        color = random.choice(colors)
        self._spawn_particle(x, y, z, vx, vy, vz, life, size, color)


class SnowSystem(ParticleSystem):
    """Gentle falling snowflakes."""
    def _emit_one(self):
        x = random.uniform(-12, 12)
        y = random.uniform(5, 12)
        z = random.uniform(4.0, 6.0)
        vx = random.uniform(-0.3, 0.3)
        vy = random.uniform(-0.8, -0.2)
        vz = random.uniform(-0.2, 0.0)
        life = random.uniform(5.0, 10.0)
        size = random.uniform(0.04, 0.10)
        color = (0.9, 0.9, 1.0, 0.6)
        self._spawn_particle(x, y, z, vx, vy, vz, life, size, color)


class RainSystem(ParticleSystem):
    """Fast falling rain streaks."""
    def _emit_one(self):
        x = random.uniform(-12, 12)
        y = random.uniform(5, 12)
        z = random.uniform(5.0, 7.0)
        vx = random.uniform(-0.5, 0.0)
        vy = random.uniform(-3.0, -2.0)
        vz = random.uniform(-0.5, 0.0)
        life = random.uniform(1.0, 2.0)
        size = random.uniform(0.03, 0.06)
        color = (0.5, 0.6, 0.8, 0.4)
        self._spawn_particle(x, y, z, vx, vy, vz, life, size, color)


class TorchSparkSystem(ParticleSystem):
    """Rising sparks from torches and the forge."""
    def __init__(self, parent: NodePath, origin_x: float = 0, origin_y: float = 0, origin_z: float = 0):
        super().__init__(parent, max_particles=30)
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.origin_z = origin_z

    def _emit_one(self):
        x = self.origin_x + random.uniform(-0.1, 0.1)
        y = self.origin_y + random.uniform(-0.1, 0.1)
        z = self.origin_z + random.uniform(0, 0.2)
        vx = random.uniform(-0.2, 0.2)
        vy = random.uniform(-0.2, 0.2)
        vz = random.uniform(0.5, 1.5)
        life = random.uniform(0.5, 1.5)
        size = random.uniform(0.03, 0.08)
        colors = [(1.0, 0.6, 0.1, 0.8), (1.0, 0.3, 0.0, 0.6), (0.9, 0.8, 0.2, 0.5)]
        color = random.choice(colors)
        self._spawn_particle(x, y, z, vx, vy, vz, life, size, color)


class DustMoteSystem(ParticleSystem):
    """Subtle floating dust motes for indoor/cave atmosphere."""
    def _emit_one(self):
        x = random.uniform(-6, 6)
        y = random.uniform(-6, 6)
        z = random.uniform(0.5, 3.0)
        vx = random.uniform(-0.05, 0.05)
        vy = random.uniform(-0.05, 0.05)
        vz = random.uniform(-0.02, 0.02)
        life = random.uniform(8.0, 15.0)
        size = random.uniform(0.02, 0.05)
        color = (0.7, 0.7, 0.6, 0.3)
        self._spawn_particle(x, y, z, vx, vy, vz, life, size, color)


class AmbientParticles:
    """Container for all ambient particle systems, activated by season/location."""

    def __init__(self, parent: NodePath):
        self.parent = parent
        self.systems = {
            "fireflies": FireflySystem(parent),
            "leaves": LeafSystem(parent),
            "snow": SnowSystem(parent),
            "rain": RainSystem(parent),
            "torch": TorchSparkSystem(parent),
            "dust": DustMoteSystem(parent),
        }
        self.active: List[str] = []

    def set_season(self, season: str):
        """Activate season-appropriate particles."""
        self.clear()
        if season == "Spring":
            self._activate("dust")
        elif season == "Summer":
            self._activate("fireflies")
            self._activate("dust")
        elif season == "Autumn":
            self._activate("leaves")
            self._activate("dust")
        elif season == "Winter":
            self._activate("snow")

    def set_location(self, location: str):
        """Activate location-specific particles."""
        if location == "forge" or location == "inn":
            self._activate("torch")
        elif location == "cave":
            self._activate("dust")

    def _activate(self, name: str):
        if name not in self.active:
            self.active.append(name)

    def clear(self):
        for name, sys in self.systems.items():
            sys.clear()
        self.active = []

    def update(self, dt: float):
        for name in self.active:
            if name in self.systems:
                self.systems[name].update(dt)
