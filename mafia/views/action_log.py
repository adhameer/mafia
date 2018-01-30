from copy import copy

class ActionLog():
    """A log of actions for a particular phase in a game."""

    def __init__(self, phase, actions):
        self.phase = phase
        self.actions = actions

    def __copy__(self):
        return ActionLog(self.phase, copy(self.actions))

    def __iter__(self):
        return self.actions.__iter__()

    def __len__(self):
        return len(self.actions)

    def pop(self):
        return self.actions.pop()

    def sort(self, key=None, reverse=False):
        self.actions.sort(key=key, reverse=reverse)

    def append(self, action):
        self.actions.append(action)

class LogEntry():
    """An entry in a game's action log."""

    pass

class ActionEntry(LogEntry):
    """An action log entry describing an attempted action."""

    def __init__(self, player, action, targets):
        self.player = player
        self.action = action
        self.targets = targets

    def __str__(self):
        return "{} uses action {} on {}".format(
            self.player.name, self.action.name,
            ", ".join(target.name for target in self.targets))

    def data(self):
        return (self.player, self.action, self.targets)

    def html_str(self):
        """Return a string representation of this log entry with span tags
        around the player name, role name, action name, and target names
        (to use for styling)."""

        return ("<span class=\"player-name\">{}</span> "
            "(<span class=\"role\">{}</span>) uses action "
            "<span class=\"action\">{}</span> on {}".format(
                self.player.name, self.player.role.name, self.action.name,
                ", ".join("<span class=\"target\">{}</span>".format(t.name)
                    for t in self.targets)))

class LynchEntry(LogEntry):
    """An action log entry describing a lynch."""

    def __init__(self, player):
        self.player = player

    def __str__(self):
        return "{} ({}) is lynched".format(self.player.name,
            self.player.role.name)

    def html_str(self):
        """Return a string representation of this log entry with span tags
        around the player name (to use for styling)."""

        return ("<span class=\"player-name\">{}</span> "
            "(<span class=\"role\">{}</span>) is lynched").format(
            self.player.name, self.player.role.name)

class NoLynchEntry(LogEntry):
    """An action log entry for days where there is no lynch."""

    def __str__(self):
        return "No one is lynched"

    def html_str(self):
        return str(self)
