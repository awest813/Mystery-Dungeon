"""
Status effects system inspired by PMD, Persona Q, and FF Tactics.

Active effects are stored as {name: turns_remaining} on entities.
Each effect has a tick() that applies its per-turn consequence.
"""

STATUS_COLORS = {
    "poisoned":  (0.5, 0.0, 0.7, 1),
    "burn":      (1.0, 0.3, 0.0, 1),
    "confused":  (1.0, 0.8, 0.0, 1),
    "paralyzed": (0.8, 0.8, 0.2, 1),
    "asleep":    (0.3, 0.3, 0.9, 1),
}

# How many turns each status lasts when first applied
STATUS_DURATIONS = {
    "poisoned":  6,
    "burn":      4,
    "confused":  3,
    "paralyzed": 2,
    "asleep":    3,
}

# Damage per turn for damaging statuses (as fraction of max_hp)
STATUS_DAMAGE = {
    "poisoned": 0.05,   # 5% max HP per turn
    "burn":     0.08,   # 8% max HP per turn
}


class StatusEffectsMixin:
    """
    Mixin to add status effect tracking to an entity.
    Call init_status() in __init__, tick_status() each turn.
    """

    def init_status(self):
        self.active_statuses = {}   # {name: turns_remaining}
        self._original_color = None

    def apply_status(self, name, log_callback=None):
        if name not in STATUS_DURATIONS:
            return
        # Paralyzed / asleep don't stack; refresh instead
        self.active_statuses[name] = STATUS_DURATIONS[name]
        if log_callback:
            log_callback(f"{self.name} is now {name}!")

    def cure_status(self, name):
        self.active_statuses.pop(name, None)

    def cure_all_statuses(self):
        self.active_statuses.clear()

    def has_status(self, name):
        return name in self.active_statuses and self.active_statuses[name] > 0

    def is_immobile(self):
        return self.has_status("paralyzed") or self.has_status("asleep")

    def tick_status(self, log_callback=None):
        """
        Called once per turn for the entity.
        Returns True if entity can act this turn, False if immobilised.
        """
        can_act = True
        expired = []

        for name, turns in list(self.active_statuses.items()):
            # Apply effect
            if name in STATUS_DAMAGE:
                dmg = max(1, int(self.max_hp * STATUS_DAMAGE[name]))
                self.take_damage(dmg)
                if log_callback:
                    log_callback(f"{self.name} takes {dmg} {name} damage!")

            if name == "paralyzed":
                can_act = False
                if log_callback:
                    log_callback(f"{self.name} is paralyzed and cannot move!")

            if name == "asleep":
                can_act = False
                if log_callback:
                    log_callback(f"{self.name} is asleep!")

            # Decrement
            self.active_statuses[name] = turns - 1
            if self.active_statuses[name] <= 0:
                expired.append(name)

        for name in expired:
            del self.active_statuses[name]
            if log_callback:
                log_callback(f"{self.name} recovered from {name}.")

        return can_act

    def status_display_str(self):
        if not self.active_statuses:
            return ""
        parts = []
        for name, turns in self.active_statuses.items():
            abbrev = {"poisoned": "PSN", "burn": "BRN", "confused": "CNF",
                      "paralyzed": "PAR", "asleep": "SLP"}.get(name, name[:3].upper())
            parts.append(f"{abbrev}({turns})")
        return " ".join(parts)
