from direct.gui.OnscreenText import OnscreenText
from entities.items import RARITY_TIERS
from panda3d.core import TextNode
from ui.health_bar import HealthBar


class GameHUD:
    def __init__(self):
        # --- Left panel: HP, Hunger, Level, XP, Status ---
        self.hp_bar = HealthBar(
            parent=None, pos=(-1.0, 0, 0.90),
            width=0.4, height=0.04, label="HP",
            fg=(0.3, 1.0, 0.3, 1)
        )
        self.hunger_bar = HealthBar(
            parent=None, pos=(-1.0, 0, 0.80),
            width=0.4, height=0.04, label="Hunger",
            fg=(1.0, 0.8, 0.3, 1)
        )
        
        self.level_text = OnscreenText(
            text="Lv.1  XP: 0/20",
            pos=(-1.3, 0.70), scale=0.060,
            fg=(0.7, 0.7, 1.0, 1), align=TextNode.ALeft, mayChange=True
        )
        self.status_text = OnscreenText(
            text="",
            pos=(-1.3, 0.63), scale=0.055,
            fg=(1.0, 0.5, 1.0, 1), align=TextNode.ALeft, mayChange=True
        )

        # --- Right panel: Gold, Weapon, Inventory count ---
        self.gold_text = OnscreenText(
            text="GOLD: 0",
            pos=(1.3, 0.93), scale=0.065,
            fg=(1.0, 1.0, 0.3, 1), align=TextNode.ARight, mayChange=True
        )
        self.weapon_text = OnscreenText(
            text="Weapon: none",
            pos=(1.3, 0.83), scale=0.055,
            fg=(0.9, 0.7, 0.4, 1), align=TextNode.ARight, mayChange=True
        )
        self.inv_text = OnscreenText(
            text="Bag: 0/10",
            pos=(1.3, 0.73), scale=0.055,
            fg=(0.7, 0.9, 0.7, 1), align=TextNode.ARight, mayChange=True
        )
        self.materials_text = OnscreenText(
            text="",
            pos=(1.3, 0.63), scale=0.042,
            fg=(0.75, 0.85, 0.95, 1), align=TextNode.ARight, mayChange=True
        )
        self.day_text = OnscreenText(
            text="",
            pos=(1.3, 0.53), scale=0.042,
            fg=(0.6, 0.9, 0.6, 1), align=TextNode.ARight, mayChange=True
        )
        self.meals_text = OnscreenText(
            text="",
            pos=(-1.3, 0.53), scale=0.042,
            fg=(0.9, 0.7, 0.4, 1), align=TextNode.ALeft, mayChange=True
        )

        # --- Bottom center: Floor status ---
        self.floor_text = OnscreenText(
            text="Oasis Town",
            pos=(0, -0.75), scale=0.08,
            fg=(1, 1, 1, 1), align=TextNode.ACenter, mayChange=True
        )

        # --- Skill bar: 4 skills (PMD style) ---
        self.skill_labels = []
        for i in range(4):
            t = OnscreenText(
                text="",
                pos=(-0.45 + i * 0.30, -0.87), scale=0.048,
                fg=(0.8, 1.0, 0.8, 1), align=TextNode.ACenter, mayChange=True
            )
            self.skill_labels.append(t)

        # --- Message Log ---
        self.messages = []
        self.log_text = OnscreenText(
            text="",
            pos=(-1.3, -0.93), scale=0.048,
            fg=(0.8, 0.8, 1.0, 1), align=TextNode.ALeft, mayChange=True
        )

        # --- Controls hint ---
        OnscreenText(
            text="WASD:Move  Space:Wait  1-4:Skill  F:Use  Z:Drop  I:Inspect  E:Action",
            pos=(0, -0.997), scale=0.038,
            fg=(0.5, 0.5, 0.5, 1), align=TextNode.ACenter
        )

    # ------------------------------------------------------------------ #
    #  Messaging                                                           #
    # ------------------------------------------------------------------ #

    def add_message(self, msg):
        self.messages.append(msg)
        if len(self.messages) > 4:
            self.messages.pop(0)
        self.log_text.setText("\n".join(self.messages))

    # ------------------------------------------------------------------ #
    #  Full update                                                         #
    # ------------------------------------------------------------------ #

    def update(self, player, floor_level=0, in_town=False):
        # HP with color coding
        hp_frac = player.hp / max(1, player.max_hp)
        if hp_frac > 0.5:
            hp_color = (0.3, 1.0, 0.3, 1)
        elif hp_frac > 0.25:
            hp_color = (1.0, 0.8, 0.0, 1)
        else:
            hp_color = (1.0, 0.2, 0.2, 1)
        
        self.hp_bar.update(player.hp, max(1, player.max_hp), color=hp_color)
        self.hp_bar.set_label(f"HP: {int(player.hp)} / {int(player.max_hp)}")

        # Hunger with color coding
        hung_frac = player.hunger / max(1, player.max_hunger)
        hung_color = (1.0, 0.8, 0.3, 1) if hung_frac > 0.3 else (1.0, 0.3, 0.1, 1)
        self.hunger_bar.update(player.hunger, max(1, player.max_hunger), color=hung_color)
        self.hunger_bar.set_label(f"HUNGER: {int(player.hunger)}")

        # Level / XP
        xp_to = getattr(player, 'xp_to_next', 20)
        self.level_text.setText(f"Lv.{player.level}  XP:{player.xp}/{xp_to}")

        # Status effects
        status_str = player.status_display_str() if hasattr(player, 'status_display_str') else ""
        self.status_text.setText(status_str)

        # Gold
        self.gold_text.setText(f"GOLD: {int(player.gold)}")

        # Equipped weapon – Phase 7: show rarity colour and affix count
        wpn = getattr(player, 'equipped_weapon', None)
        if wpn:
            wpn_str = wpn.display_name if hasattr(wpn, 'display_name') else wpn.display
            affix_count = len(getattr(wpn, 'affixes', []))
            affix_tag = f" +{affix_count}" if affix_count else ""
            cursed_tag = " !" if getattr(wpn, 'cursed', False) else ""
            wpn_display = f"{wpn_str}{affix_tag}{cursed_tag}"
            # Rarity colour (Phase 7)
            rarity = getattr(wpn, 'rarity', 'common')
            wpn_color = RARITY_TIERS.get(rarity, RARITY_TIERS["common"])["color"]
        else:
            wpn_display = "none"
            wpn_color = (0.9, 0.7, 0.4, 1)
        atk_total = getattr(player, 'effective_attack', player.attack_power)
        self.weapon_text.setText(f"ATK:{atk_total} [{wpn_display}]")
        self.weapon_text.setFg(wpn_color)

        # Inventory count
        inv_count = len(player.inventory)
        self.inv_text.setText(f"Bag: {inv_count}/{player.max_inventory}")

        # Phase 8 – compact material line (town + dungeon)
        mats = getattr(player, "materials", {}) or {}
        nz = [(k, v) for k, v in sorted(mats.items()) if v > 0]
        if nz:
            short = ", ".join(f"{v}×{k.replace('_', ' ')[:4]}" for k, v in nz[:5])
            if len(nz) > 5:
                short += "…"
            self.materials_text.setText(f"Mats: {short}")
        else:
            self.materials_text.setText("Mats: —")

        # Phase 9 – calendar day/season
        cal = getattr(player, 'calendar', None)
        if cal:
            self.day_text.setText(f"Day {cal.day} ({cal.season})")
        else:
            self.day_text.setText("")

        # Phase 9 – active meal buffs
        meals = getattr(player, 'active_meals', [])
        if meals:
            meal_str = " | ".join(m["name"] for m in meals)
            self.meals_text.setText(f"Meals: {meal_str}")
        else:
            self.meals_text.setText("")

        # Skill bar (PMD 4-slot style)
        sel_idx = getattr(player, 'selected_skill_idx', 0)
        skills = getattr(player, 'skills', [])
        for i, label in enumerate(self.skill_labels):
            if i < len(skills):
                sk = skills[i]
                txt = f"[{i+1}]{sk.display}\nPP:{sk.pp}"
                label.setText(txt)
                if i == sel_idx:
                    label.setFg((1.0, 1.0, 0.3, 1))
                else:
                    label.setFg((0.7, 0.9, 0.7, 1))
            else:
                label.setText("")

        # Floor / town label
        if in_town:
            self.floor_text.setText("OASIS TOWN (Safe)")
            self.floor_text.setFg((0.3, 1.0, 1.0, 1))
            self.messages = ["--- Progress Saved ---"]
            self.log_text.setText("\n".join(self.messages))
        else:
            boss = (floor_level % 5 == 0 and floor_level > 0)
            label = f"B{floor_level} !! BOSS FLOOR !!" if boss else f"Floor {floor_level}"
            self.floor_text.setText(label)
            self.floor_text.setFg((1.0, 0.3, 0.3, 1) if boss else (1.0, 1.0, 1.0, 1))

    # ------------------------------------------------------------------ #
    #  Show / hide                                                         #
    # ------------------------------------------------------------------ #

    def hide(self):
        self.hp_bar.hide()
        self.hunger_bar.hide()
        for t in [self.level_text, self.status_text,
                  self.gold_text, self.weapon_text, self.inv_text, self.materials_text,
                  self.day_text, self.meals_text, self.floor_text, self.log_text]:
            t.hide()
        for sl in self.skill_labels:
            sl.hide()

    def show(self):
        self.hp_bar.show()
        self.hunger_bar.show()
        for t in [self.level_text, self.status_text,
                  self.gold_text, self.weapon_text, self.inv_text, self.materials_text,
                  self.day_text, self.meals_text, self.floor_text, self.log_text]:
            t.show()
        for sl in self.skill_labels:
            sl.show()
