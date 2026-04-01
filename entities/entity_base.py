import math
from panda3d.core import NodePath, CardMaker
from .status_effects import StatusEffectsMixin

try:
    from direct.interval.IntervalGlobal import Sequence
    _HAS_INTERVALS = True
except ImportError:
    _HAS_INTERVALS = False


def _build_default_model():
    from render import make_player_model
    return make_player_model()


def _build_default_shadow():
    from render import make_blob_shadow
    return make_blob_shadow(0.20)


class Entity(StatusEffectsMixin):
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.node = NodePath(name)

        self._build_visual(name)

        self.max_hp = 10
        self.hp = 10
        self.attack_power = 2
        self.is_dead = False

        self.target_pos = (x, y, 0.05)
        self.node.setPos(x, y, 0.05)

        self.init_status()

        self._flash_seq = None

    def _build_visual(self, name):
        self.shadow = _build_default_shadow()
        self.visual = _build_default_model()

    def update(self, dt):
        curr = self.node.getPos()
        dest = self.target_pos

        speed = 10.0
        new_pos = curr + (dest - curr) * min(1.0, speed * dt)

        dist = (dest - curr).length()
        hop = 0
        if dist > 0.05:
            hop = math.sin(dist * math.pi) * 0.3

        self.node.setPos(new_pos.x, new_pos.y, new_pos.z + hop)

        if self.shadow:
            self.shadow.setPos(new_pos.x, new_pos.y, 0.02)

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
        else:
            self._flash_damage()
        return amount

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
        self._flash_heal()

    def _flash_damage(self):
        if not self.visual or not _HAS_INTERVALS:
            return
        orig_color = self.visual.getColor()
        flash = self.visual.colorInterval(0.08, (1.0, 0.2, 0.2, 1.0))
        restore = self.visual.colorInterval(0.12, orig_color)
        seq = Sequence(flash, restore)
        seq.start()

    def _flash_heal(self):
        if not self.visual or not _HAS_INTERVALS:
            return
        orig_color = self.visual.getColor()
        flash = self.visual.colorInterval(0.08, (0.3, 1.0, 0.3, 1.0))
        restore = self.visual.colorInterval(0.12, orig_color)
        seq = Sequence(flash, restore)
        seq.start()

    def on_death(self):
        if self.visual:
            fade = self.visual.colorInterval(0.8, (0.3, 0.1, 0.1, 0.3))
            fade.start()
        if self.shadow:
            self.shadow.setColor(0, 0, 0, 0.05)

    def reparent_to(self, parent):
        self.shadow.reparentTo(parent)
        self.visual.reparentTo(parent)
