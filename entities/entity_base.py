import math
from panda3d.core import NodePath, CardMaker
from .status_effects import StatusEffectsMixin


class Entity(StatusEffectsMixin):
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.node = NodePath(name)

        # Simple placeholder: a Billboard card
        cm = CardMaker(name)
        cm.setFrame(-0.35, 0.35, 0, 0.7)
        self.visual = self.node.attachNewNode(cm.generate())
        self.visual.setBillboardPointEye()

        self.max_hp = 10
        self.hp = 10
        self.attack_power = 2
        self.is_dead = False

        # Smooth movement variables
        self.target_pos = (x, y, 0.05)
        self.node.setPos(x, y, 0.05)

        # Status effects
        self.init_status()

    def update(self, dt):
        """Linearly interpolates toward target position for smooth visuals."""
        curr = self.node.getPos()
        dest = self.target_pos

        speed = 10.0
        new_pos = curr + (dest - curr) * min(1.0, speed * dt)

        # "Hop" effect: Z-offset based on distance to target
        dist = (dest - curr).length()
        hop = 0
        if dist > 0.05:
            hop = math.sin(dist * math.pi) * 0.4

        self.node.setPos(new_pos.x, new_pos.y, new_pos.z + hop)

    def move_to(self, tx, ty):
        self.x = tx
        self.y = ty
        self.target_pos = (tx, ty, 0.05)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.on_death()
        return amount

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def on_death(self):
        self.visual.setColor(0.3, 0.1, 0.1, 0.5)

    def reparent_to(self, parent):
        self.node.reparentTo(parent)
