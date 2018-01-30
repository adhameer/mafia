from ..models import roles

class Player():
    """A single player in a specific game."""

    def __init__(self, name, role_id):

        self.name = name
        self.role = roles[role_id]
        self.role_name = self.role.name

        self.is_alive = True

        # Data initially taken from role, but can be changed
        self.alignment = self.role.alignment
        self.perceived_alignment = self.role.perceived_alignment

        # Data for limited-use actions. -1 means no limit.
        self.night_action_uses_left = self.role.night_action_uses
        self.day_action_uses_left = self.role.day_action_uses
        self.passive_action_uses_left = self.role.passive_action_uses

        # Flags for special roles
        self.is_bleeding = False # bleeder
        self.is_activated = False # alien
        self.has_lost_action = False # psychic
        self.has_gun = False # gunsmith targets

        self.last_target = None # protective roles

        # Nightly flags
        # none currently

    def has_night_action(self):
        """Return True if this player has a night action that it can currently
        use, False otherwise."""

        return self.is_alive and self.role.night_action and \
            self.night_action_uses_left and not self.has_lost_action

    def has_day_action(self):
        """Return True if this player has a day action that it can currently
        use, False otherwise."""

        return self.is_alive and self.role.day_action and \
            self.day_action_uses_left

    def has_passive_action(self):
        """Return True if this player has a day action that is can currently
        use, False otherwise."""

        return self.is_alive and self.role.passive_action and \
            self.passive_action_uses_left

    def can_use_gun(self):
        """Return True if this player has a gun and can use it, False
        otherwise."""

        return self.is_alive and self.has_gun

    def reset_nightly_flags(self):
        """Reset all nightly flags to their default state."""

        pass

    def secret_role_name(self):
        """Return this player's role name, excluding any secret info.
        e.g. for Bleeder, return Villager."""

        if self.role.name == "Bleeder":
            return "Villager"

        return self.role_name
