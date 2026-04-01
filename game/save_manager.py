import json
import os
from entities.items import Item
from entities.skills import Skill


class SaveManager:
    def __init__(self, filename="save_data.json"):
        self.filename = filename

    def save_progress(self, player):
        """Persists meta-progression stats, inventory, skills, and Phase 7 data."""
        inv_data = [item.to_dict() for item in player.inventory]
        equipped = player.equipped_weapon.to_dict() if player.equipped_weapon else None
        skill_data = [{"key": s.key, "pp": s.pp} for s in player.skills]

        data = {
            "gold": player.gold,
            "level": player.level,
            "xp": player.xp,
            "xp_to_next": player.xp_to_next,
            "max_hp": player.max_hp,
            "attack_power": player.attack_power,
            "inventory": inv_data,
            "equipped_weapon": equipped,
            "skills": skill_data,
            "selected_skill_idx": player.selected_skill_idx,
            # Phase 7
            "identified_items": sorted(player.identified_items),
            "materials": player.materials,
            # Phase 8 – town construction
            "completed_buildings": sorted(getattr(player, "completed_buildings", set())),
            # Phase 8 – building services
            "active_bounty": getattr(player, "active_bounty", None),
            "inn_buff_hp": getattr(player, "inn_buff_hp", 0),
            # Phase 9 – life sim
            "calendar": getattr(player, "calendar", None),
            "garden_plots": [
                {"crop_id": p.crop_id, "growth_days_needed": p.growth_days_needed,
                 "growth_days_current": p.growth_days_current, "is_watered": p.is_watered,
                 "yield_item": p.yield_item, "yield_count": p.yield_count,
                 "season_bonus": p.season_bonus}
                for p in getattr(player, "garden_plots", [])
            ],
            # Phase 10 – companions
            "companions": [c.to_dict() for c in getattr(player, "companions", [])],
            "active_companions": sorted(getattr(player, "active_companions", set())),
            # Phase 12 – monster roster
            "monster_roster": getattr(player, "monster_roster", None).to_dict() if getattr(player, "monster_roster", None) else None,
            # Phase 13 – endless dungeon & NG+
            "endless_dungeon": getattr(player, "endless_dungeon", None).to_dict() if getattr(player, "endless_dungeon", None) else None,
            "ngp_state": getattr(player, "ngp_state", None).to_dict() if getattr(player, "ngp_state", None) else None,
            # Phase 14 – core integrations
            "progression": getattr(player, "progression", None).to_dict() if getattr(player, "progression", None) else None,
            # Phase 15 – life sim
            "home": getattr(player, "home", None).to_dict() if getattr(player, "home", None) else None,
            "festivals": getattr(player, "festivals", None).to_dict() if getattr(player, "festivals", None) else None,
            "npc_affection": {n.npc_id: n.affection for n in getattr(player, "_npcs", [])},
        }
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Save failed: {e}")

    def load_progress(self, player):
        """Loads meta-progression into the player object."""
        if not os.path.exists(self.filename):
            return False

        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)

            player.gold = data.get("gold", 0)
            player.level = data.get("level", 1)
            player.xp = data.get("xp", 0)
            player.xp_to_next = data.get("xp_to_next", 20)
            player.max_hp = data.get("max_hp", 30)
            player.attack_power = data.get("attack_power", 5)
            player.hp = player.max_hp

            # Phase 7: identification knowledge and materials
            player.identified_items = set(data.get("identified_items", []))
            player.materials = data.get("materials", {})
            # Phase 8
            cb = data.get("completed_buildings", [])
            player.completed_buildings = set(cb) if isinstance(cb, list) else set()
            player.active_bounty = data.get("active_bounty", None)
            player.inn_buff_hp = data.get("inn_buff_hp", 0)

            # Phase 9 – calendar and garden
            from game.calendar import Calendar
            from world.garden import CropPlot
            cal_data = data.get("calendar")
            player.calendar = Calendar.from_dict(cal_data) if cal_data else Calendar(1)
            player.garden_plots = []
            for pd in data.get("garden_plots", []):
                player.garden_plots.append(CropPlot(
                    crop_id=pd["crop_id"],
                    growth_days_needed=pd["growth_days_needed"],
                    growth_days_current=pd.get("growth_days_current", 0),
                    is_watered=pd.get("is_watered", False),
                    yield_item=pd.get("yield_item", ""),
                    yield_count=pd.get("yield_count", 1),
                    season_bonus=pd.get("season_bonus", ""),
                ))

            # Phase 10 – companions
            from entities.companion import Companion
            player.companions = []
            for cd in data.get("companions", []):
                player.companions.append(Companion.from_dict(cd))
            player.active_companions = set(data.get("active_companions", []))

            # Phase 12 – monster roster
            from entities.monster_roster import MonsterRoster
            roster_data = data.get("monster_roster")
            player.monster_roster = MonsterRoster.from_dict(roster_data) if roster_data else MonsterRoster()

            # Phase 13 – endless dungeon & NG+
            from systems.endless_dungeon import EndlessDungeon
            ed_data = data.get("endless_dungeon")
            player.endless_dungeon = EndlessDungeon.from_dict(ed_data) if ed_data else EndlessDungeon()
            from systems.new_game_plus import NGPlusState
            ngp_data = data.get("ngp_state")
            player.ngp_state = NGPlusState.from_dict(ngp_data) if ngp_data else None

            # Phase 14 – progression tracker
            from systems.progression_tracker import ProgressionTracker
            prog_data = data.get("progression")
            player.progression = ProgressionTracker.from_dict(prog_data) if prog_data else ProgressionTracker()

            # Phase 15 – life sim
            from systems.home_system import HomeSystem
            home_data = data.get("home")
            player.home = HomeSystem.from_dict(home_data) if home_data else HomeSystem()
            from systems.festivals import FestivalSystem
            fest_data = data.get("festivals")
            player.festivals = FestivalSystem.from_dict(fest_data) if fest_data else FestivalSystem()
            player._npc_affection = data.get("npc_affection", {})

            # Restore inventory (Phase 7: full dict round-trip)
            player.inventory = []
            for item_data in data.get("inventory", []):
                try:
                    if isinstance(item_data, dict):
                        item = Item.from_dict(item_data)
                    else:
                        item = Item(item_data)   # legacy: plain key string
                    # Auto-identify if type has been seen before
                    if item.key in player.identified_items:
                        item.is_identified = True
                    player.inventory.append(item)
                except Exception:
                    pass

            # Restore equipped weapon
            eq_data = data.get("equipped_weapon")
            if eq_data:
                try:
                    if isinstance(eq_data, dict):
                        wpn = Item.from_dict(eq_data)
                    else:
                        wpn = Item(eq_data)   # legacy
                    if wpn.key in player.identified_items:
                        wpn.is_identified = True
                    player.equipped_weapon = wpn
                    player._weapon_bonus = wpn.attack_bonus  # noqa: SLF001
                    player._apply_weapon_affixes(wpn)  # noqa: SLF001
                except Exception:
                    pass

            # Restore skills
            skill_data = data.get("skills", [])
            if skill_data:
                player.skills = []
                for sd in skill_data:
                    try:
                        sk = Skill(sd["key"])
                        sk.pp = sd.get("pp", sk.max_pp)
                        player.skills.append(sk)
                    except Exception:
                        pass
            player.selected_skill_idx = data.get("selected_skill_idx", 0)

            return True
        except Exception as e:
            print(f"Load failed: {e}")
            return False
