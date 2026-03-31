import json
import os
from entities.items import Item
from entities.skills import Skill


class SaveManager:
    def __init__(self, filename="save_data.json"):
        self.filename = filename

    def save_progress(self, player):
        """Persists meta-progression stats, inventory, and skills to disk."""
        inv_data = [item.key for item in player.inventory]
        equipped = player.equipped_weapon.key if player.equipped_weapon else None
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

            # Restore inventory
            player.inventory = []
            for key in data.get("inventory", []):
                try:
                    player.inventory.append(Item(key))
                except Exception:
                    pass

            # Restore equipped weapon
            eq_key = data.get("equipped_weapon")
            if eq_key:
                try:
                    wpn = Item(eq_key)
                    player.equipped_weapon = wpn
                    player._weapon_bonus = wpn.attack_bonus
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
