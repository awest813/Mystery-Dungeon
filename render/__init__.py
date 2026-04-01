"""
Procedural 3D geometry builders for PSP-style dungeon rendering.

Creates extruded tiles, wall blocks, character models, and environmental
objects using Panda3D CardMaker — no external model files needed.
"""


def _core():
    from panda3d.core import (
        NodePath, CardMaker, TransparencyAttrib,
    )
    return NodePath, CardMaker, TransparencyAttrib


def _make_floor_tile(tile_size=0.96, thickness=0.12):
    NodePath, CardMaker, _ = _core()
    root = NodePath("floor_tile")
    hs = tile_size / 2
    th = thickness

    top = CardMaker("top")
    top.setFrame(-hs, hs, -hs, hs)
    tn = root.attachNewNode(top.generate())
    tn.setP(-90)
    tn.setZ(th / 2)

    bottom = CardMaker("bottom")
    bottom.setFrame(-hs, hs, -hs, hs)
    bn = root.attachNewNode(bottom.generate())
    bn.setP(90)
    bn.setZ(-th / 2)

    side = CardMaker("side")
    side.setFrame(-hs, hs, 0, th)
    for heading, pos_x, pos_y in [
        (0, 0, hs), (180, 0, -hs), (90, hs, 0), (270, -hs, 0)
    ]:
        sn = root.attachNewNode(side.generate())
        sn.setH(heading)
        sn.setPos(pos_x, pos_y, 0)

    return root


def _make_wall_block(tile_size=1.0, height=1.6):
    NodePath, CardMaker, _ = _core()
    root = NodePath("wall_block")
    hs = tile_size / 2
    h = height

    top = CardMaker("top")
    top.setFrame(-hs, hs, -hs, hs)
    tn = root.attachNewNode(top.generate())
    tn.setP(-90)
    tn.setZ(h)

    front = CardMaker("front")
    front.setFrame(-hs, hs, 0, h)

    for heading, px, py in [
        (0, 0, hs), (180, 0, -hs), (90, hs, 0), (270, -hs, 0)
    ]:
        fn = root.attachNewNode(front.generate())
        fn.setH(heading)
        fn.setPos(px, py, 0)

    return root


def _make_wall_cap(tile_size=1.0, height=1.6):
    NodePath, CardMaker, _ = _core()
    root = NodePath("wall_cap")
    hs = tile_size / 2 + 0.04

    cap = CardMaker("cap")
    cap.setFrame(-hs, hs, -hs, hs)
    cn = root.attachNewNode(cap.generate())
    cn.setP(-90)
    cn.setZ(height + 0.04)

    return root


def make_floor_tile(tile_size=0.96, thickness=0.12):
    return _make_floor_tile(tile_size, thickness)


def make_wall_block(tile_size=1.0, height=1.6):
    return _make_wall_block(tile_size, height)


def make_wall_cap(tile_size=1.0, height=1.6):
    return _make_wall_cap(tile_size, height)


def make_player_model(color=(0.3, 0.7, 1.0, 1.0)):
    NodePath, CardMaker, _ = _core()
    root = NodePath("player_model")

    body = CardMaker("body")
    body.setFrame(-0.22, 0.22, 0, 0.50)
    bn = root.attachNewNode(body.generate())
    bn.setP(-90)
    bn.setZ(0.05)
    bn.setColor(*color)

    head = CardMaker("head")
    head.setFrame(-0.16, 0.16, -0.16, 0.16)
    hn = root.attachNewNode(head.generate())
    hn.setP(-90)
    hn.setZ(0.55)
    hn.setColor(0.95, 0.80, 0.65, 1)

    helm = CardMaker("helm")
    helm.setFrame(-0.18, 0.18, -0.14, 0.14)
    hlmn = root.attachNewNode(helm.generate())
    hlmn.setP(-90)
    hlmn.setZ(0.62)
    hlmn.setColor(0.6, 0.65, 0.75, 1)

    visor = CardMaker("visor")
    visor.setFrame(-0.12, 0.12, -0.03, 0.03)
    vn = root.attachNewNode(visor.generate())
    vn.setP(-90)
    vn.setZ(0.58)
    vn.setY(0.12)
    vn.setColor(0.4, 0.6, 1.0, 0.9)

    weapon = CardMaker("weapon")
    weapon.setFrame(-0.03, 0.03, -0.35, 0.15)
    wn = root.attachNewNode(weapon.generate())
    wn.setX(0.30)
    wn.setZ(0.25)
    wn.setColor(0.8, 0.8, 0.9, 1)

    return root


def make_enemy_model(enemy_type, color):
    NodePath, CardMaker, TransparencyAttrib = _core()
    root = NodePath(f"enemy_{enemy_type}")

    if enemy_type == "slime":
        body = CardMaker("body")
        body.setFrame(-0.30, 0.30, -0.30, 0.15)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.08)
        bn.setColor(*color)
        shine = CardMaker("shine")
        shine.setFrame(-0.06, 0.06, -0.06, 0.06)
        sn = root.attachNewNode(shine.generate())
        sn.setP(-90)
        sn.setZ(0.18)
        sn.setPos(-0.10, 0.08, 0)
        sn.setColor(1, 1, 1, 0.5)
        eye = CardMaker("eye")
        eye.setFrame(-0.04, 0.04, -0.04, 0.04)
        for ex, ey in [(-0.08, 0.15), (0.08, 0.15)]:
            en = root.attachNewNode(eye.generate())
            en.setP(-90)
            en.setZ(0.20)
            en.setPos(ex, ey, 0)
            en.setColor(1, 1, 1, 1)

    elif enemy_type == "bat":
        body = CardMaker("body")
        body.setFrame(-0.12, 0.12, -0.18, 0.12)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.35)
        bn.setColor(*color)
        wing = CardMaker("wing")
        wing.setFrame(-0.30, 0.30, -0.05, 0.08)
        for side_x in [-0.22, 0.22]:
            wn = root.attachNewNode(wing.generate())
            wn.setP(-90)
            wn.setZ(0.40)
            wn.setX(side_x)

    elif enemy_type == "goblin":
        body = CardMaker("body")
        body.setFrame(-0.18, 0.18, 0, 0.40)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.05)
        bn.setColor(*color)
        head = CardMaker("head")
        head.setFrame(-0.13, 0.13, -0.13, 0.13)
        hn = root.attachNewNode(head.generate())
        hn.setP(-90)
        hn.setZ(0.45)
        hn.setColor(0.5, 0.75, 0.3, 1)
        ear = CardMaker("ear")
        ear.setFrame(-0.04, 0.04, -0.10, 0.0)
        for ear_x in [-0.12, 0.12]:
            en = root.attachNewNode(ear.generate())
            en.setP(-90)
            en.setZ(0.50)
            en.setPos(ear_x, -0.08, 0)

    elif enemy_type == "ghost":
        body = CardMaker("body")
        body.setFrame(-0.22, 0.22, -0.28, 0.22)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.20)
        bn.setColor(*color)
        bn.setTransparency(TransparencyAttrib.MAlpha)
        eye = CardMaker("eye")
        eye.setFrame(-0.04, 0.04, -0.04, 0.04)
        for ex in [-0.06, 0.06]:
            en = root.attachNewNode(eye.generate())
            en.setP(-90)
            en.setZ(0.32)
            en.setPos(ex, 0.10, 0)
            en.setColor(0.2, 0.8, 1.0, 1)

    elif enemy_type == "orc":
        body = CardMaker("body")
        body.setFrame(-0.26, 0.26, 0, 0.50)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.05)
        bn.setColor(*color)
        head = CardMaker("head")
        head.setFrame(-0.15, 0.15, -0.15, 0.15)
        hn = root.attachNewNode(head.generate())
        hn.setP(-90)
        hn.setZ(0.55)
        hn.setColor(0.4, 0.55, 0.15, 1)
        club = CardMaker("club")
        club.setFrame(-0.04, 0.04, -0.35, 0.05)
        cn = root.attachNewNode(club.generate())
        cn.setX(0.35)
        cn.setZ(0.30)
        cn.setColor(0.45, 0.30, 0.15, 1)

    elif enemy_type == "fire_imp":
        body = CardMaker("body")
        body.setFrame(-0.18, 0.18, 0, 0.38)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.08)
        bn.setColor(*color)
        head = CardMaker("head")
        head.setFrame(-0.14, 0.14, -0.14, 0.14)
        hn = root.attachNewNode(head.generate())
        hn.setP(-90)
        hn.setZ(0.42)
        hn.setColor(1.0, 0.5, 0.1, 1)
        horn = CardMaker("horn")
        horn.setFrame(-0.03, 0.03, -0.12, 0.0)
        for hx in [-0.10, 0.10]:
            hn2 = root.attachNewNode(horn.generate())
            hn2.setP(-90)
            hn2.setZ(0.48)
            hn2.setPos(hx, -0.08, 0)
            hn2.setColor(0.3, 0.1, 0.0, 1)
        glow = CardMaker("glow")
        glow.setFrame(-0.30, 0.30, -0.30, 0.30)
        gn = root.attachNewNode(glow.generate())
        gn.setP(-90)
        gn.setZ(0.02)
        gn.setColor(1.0, 0.3, 0.0, 0.15)
        gn.setTransparency(TransparencyAttrib.MAlpha)

    elif enemy_type == "ice_wisp":
        body = CardMaker("body")
        body.setFrame(-0.20, 0.20, -0.20, 0.20)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.25)
        bn.setColor(*color)
        bn.setTransparency(TransparencyAttrib.MAlpha)
        crystal = CardMaker("crystal")
        crystal.setFrame(-0.06, 0.06, -0.25, 0.10)
        cn = root.attachNewNode(crystal.generate())
        cn.setZ(0.30)
        cn.setColor(0.7, 0.9, 1.0, 0.8)

    elif enemy_type == "dark_knight":
        body = CardMaker("body")
        body.setFrame(-0.28, 0.28, 0, 0.55)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.05)
        bn.setColor(*color)
        head = CardMaker("head")
        head.setFrame(-0.16, 0.16, -0.16, 0.16)
        hn = root.attachNewNode(head.generate())
        hn.setP(-90)
        hn.setZ(0.60)
        hn.setColor(0.2, 0.1, 0.3, 1)
        visor = CardMaker("visor")
        visor.setFrame(-0.14, 0.14, -0.03, 0.03)
        vn = root.attachNewNode(visor.generate())
        vn.setP(-90)
        vn.setZ(0.62)
        vn.setY(0.13)
        vn.setColor(1.0, 0.1, 0.3, 0.8)
        weapon = CardMaker("weapon")
        weapon.setFrame(-0.04, 0.04, -0.45, 0.15)
        wn = root.attachNewNode(weapon.generate())
        wn.setX(0.38)
        wn.setZ(0.30)
        wn.setColor(0.3, 0.05, 0.4, 1)
        cape = CardMaker("cape")
        cape.setFrame(-0.24, 0.24, -0.30, 0.0)
        cn = root.attachNewNode(cape.generate())
        cn.setZ(0.20)
        cn.setY(-0.20)
        cn.setColor(0.15, 0.0, 0.25, 0.8)

    else:
        body = CardMaker("body")
        body.setFrame(-0.20, 0.20, 0, 0.40)
        bn = root.attachNewNode(body.generate())
        bn.setP(-90)
        bn.setZ(0.05)
        bn.setColor(*color)

    return root


def make_item_pickup(color=(1.0, 0.8, 0.2, 1.0)):
    NodePath, CardMaker, TransparencyAttrib = _core()
    root = NodePath("item_pickup")

    gem = CardMaker("gem")
    gem.setFrame(-0.10, 0.10, -0.10, 0.10)
    top = root.attachNewNode(gem.generate())
    top.setP(-90)
    top.setZ(0.35)
    top.setColor(*color)

    glow = CardMaker("glow")
    glow.setFrame(-0.15, 0.15, -0.15, 0.15)
    gn = root.attachNewNode(glow.generate())
    gn.setP(-90)
    gn.setZ(0.20)
    gn.setColor(color[0], color[1], color[2], 0.25)
    gn.setTransparency(TransparencyAttrib.MAlpha)

    return root


def make_stairs_model(color=(0.3, 0.9, 0.9, 1.0)):
    NodePath, CardMaker, _ = _core()
    root = NodePath("stairs")

    step = CardMaker("step")
    for i in range(3):
        w = 0.7 - i * 0.10
        sn = root.attachNewNode(step.generate())
        sn.setFrame(-w / 2, w / 2, -w / 2, w / 2)
        sn.setP(-90)
        sn.setZ(0.05 + i * 0.12)
        sn.setColor(
            min(1, color[0] + i * 0.15),
            min(1, color[1] + i * 0.05),
            min(1, color[2] + i * 0.05),
            1,
        )

    arrow = CardMaker("arrow")
    arrow.setFrame(-0.06, 0.06, -0.20, 0.20)
    an = root.attachNewNode(arrow.generate())
    an.setP(-90)
    an.setZ(0.45)
    an.setColor(1, 1, 1, 0.7)

    return root


def make_material_node_model():
    NodePath, CardMaker, TransparencyAttrib = _core()
    root = NodePath("material_node")

    base = CardMaker("base")
    base.setFrame(-0.25, 0.25, -0.25, 0.25)
    bn = root.attachNewNode(base.generate())
    bn.setP(-90)
    bn.setZ(0.05)
    bn.setColor(0.35, 0.25, 0.40, 1)

    crystal1 = CardMaker("crystal1")
    crystal1.setFrame(-0.08, 0.08, -0.30, 0.10)
    c1 = root.attachNewNode(crystal1.generate())
    c1.setZ(0.15)
    c1.setR(15)
    c1.setColor(0.55, 0.35, 0.70, 0.9)
    c1.setTransparency(TransparencyAttrib.MAlpha)

    crystal2 = CardMaker("crystal2")
    crystal2.setFrame(-0.06, 0.06, -0.22, 0.08)
    c2 = root.attachNewNode(crystal2.generate())
    c2.setPos(0.15, -0.10, 0.15)
    c2.setR(-20)
    c2.setColor(0.65, 0.40, 0.80, 0.85)
    c2.setTransparency(TransparencyAttrib.MAlpha)

    crystal3 = CardMaker("crystal3")
    crystal3.setFrame(-0.05, 0.05, -0.18, 0.06)
    c3 = root.attachNewNode(crystal3.generate())
    c3.setPos(-0.12, 0.12, 0.15)
    c3.setR(30)
    c3.setColor(0.50, 0.30, 0.65, 0.8)
    c3.setTransparency(TransparencyAttrib.MAlpha)

    return root


def make_blob_shadow(radius=0.22):
    NodePath, CardMaker, TransparencyAttrib = _core()
    shadow = CardMaker("shadow")
    shadow.setFrame(-radius, radius, -radius, radius)
    node = NodePath(shadow.generate())
    node.setP(-90)
    node.setZ(0.02)
    node.setColor(0, 0, 0, 0.3)
    node.setTransparency(TransparencyAttrib.MAlpha)
    return node
