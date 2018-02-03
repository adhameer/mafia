from .actions import (
    validate_night_action,
    perform_night_action,
    perform_day_action,
    perform_passive_action,
    ActionError, InvalidTargetError,
    immediate_actions
)
from .action_log import *
from .player import Player
from mafia.models.roles import roles, actions

from collections import deque
from copy import copy
from math import ceil
from random import shuffle, randint

def priority_key(action, reverse=True):
    """Use for sorting players by action priority."""

    if not action or action.priority is None:
        return float("inf") if reverse else float("-inf")

    return -action.priority if reverse else action.priority


class GameOver(Exception):
    """Raised when the game is over. This is an exception so that it can be
    raised from anywhere in the call stack to stop game processing.
    Should be caught by the UI."""

    pass

class DeathQueue():
    """An ordered collection of players targeted to die on a particular night.
    May be modified by night action effects.
    Currently just a wrapper around a deque, but that might change.
    In particular, I don't think the order we go through the death queue
    ever matters, so maybe we should just use a list."""

    def __init__(self):
        self.queue = deque()

    def enqueue(self, x):
        self.queue.append(x)

    def dequeue(self):
        return self.queue.popleft()

    def remove(self, x):
        """Remove the first instance of x in this DeathQueue.
        Raise ValueError if x is not found."""

        self.queue.remove(x)

    def remove_all(self, x):
        """Remove all instances of x in this DeathQueue."""

        self.queue = deque(e for e in self.queue if e != x)

    def __bool__(self):
        return self.queue.__bool__()

    def __contains__(self, x):
        return x in self.queue

    def __len__(self):
        return len(self.queue)

class Game():
    """A single mafia game."""

    def __init__(self, game_roles, day_start):

        # Players in the game, sorted by alignment and then decreasing
        # night action priority
        self.players = sorted([Player(None, role) for role in game_roles],
            key=lambda p: (p.role.alignment_id,
            priority_key(p.role.night_action)))

        # Set when a winner is determined
        self.winner = None

        # In case of multiple players with the same role, give them
        # distinguishable names (e.g. Vigilante 1 and Vigilante 2)
        # Not very nice-looking, but the simplest way to only number roles that
        # actually need to be numbered.
        players_with_role = {}
        for player in self.players:
            if player.role.id in players_with_role:
                players_with_role[player.role.id].append(player)
            else:
                players_with_role[player.role.id] = [player]
        for _id, players in players_with_role.items():
            if len(players) > 1 and roles[_id].night_action:
                for i, player in enumerate(players):
                    player.role_name += " {}".format(i + 1)

        # Used for the modless functionality.
        self.is_modless = True
        self.unnamed_players = self.players[:]
        shuffle(self.unnamed_players)

        # Queue of messages to be accessed by the UI
        self.message_queue = deque()

        # Data for night phase
        self.action_queue = deque()
        self.death_queue = DeathQueue()
        self.action_log = []
        self.night_end_hooks = []

        # Used to figure out which mafia member carries out the kill
        # This relies on the fact that the plain Mafia role has the lowest id.
        # Note: self.players is already sorted by alignment, so this could be
        # made more efficient, but not really worth it.
        # The random number is to stop plain mafia members from always being
        # ranked in the order they were initially entered.
        mafia_members = filter(lambda p: p.alignment == "mafia",
            self.players)
        self.mafia_hierarchy = sorted(mafia_members,
            key=lambda p: (p.role.id, randint(0, 5)))

        # Game log
        # TODO: Need to create a class for logs, and use them to also record
        # mafia kills and lynches.
        self.action_logs = []

        self._turn = 0

        if day_start:
            self.start_day()
        else:
            self.start_night()

    def next_unnamed_player(self):
        """Return the next player that needs to enter their name.
        If all players have entered their names, return None."""

        if self.unnamed_players:
            return self.unnamed_players.pop()

    def turn(self):
        """Return the phase and turn number this game is currently in, e.g.
        "Day 1"."""

        return "{} {}".format(self.phase.capitalize(), ceil(self._turn / 2))

    def lynch(self, player):
        """Lynch a player. Triggers win condition for active alien and fool."""

        if player.role.name == "Fool" or (player.role.name == "Alien" and \
            player.is_activated):
            # TODO: End the game
            return

        self.message_queue.append("{} was lynched".format(player.name))
        self.action_log.append(LynchEntry(player))
        self.action_logs.append(self.action_log)

        self.kill(player)

    def kill(self, player):
        """Kill a player immediately. Used for lynching, gunshots, etc.
        NOT used for night kills."""

        player.is_alive = False
        self.check_winner()

    def reset_action_log(self):
        """Set this game's current action log to a new empty one corresponding
        to the current phase."""

        self.action_log = ActionLog(self.turn(), [])

    def start_day(self):
        """Prepare game state for the day phase."""

        self._turn += 1
        self.phase = "day"
        self.message_queue.append("Tell everyone to wake up")
        self.reset_action_log()

    def do_gunshot(self, player, target):
        """Should only be called during the day phase. Kill the target
        immediately and take away player's gun."""

        if not player.guns:
            raise ActionError("This player doesn't have a gun")

        if player == target:
            raise InvalidTargetError("You can't shoot yourself with a gun")

        player.guns -= 1
        self.kill(target)

    def do_day_action(self, player, targets):
        """Should only be called during the day phase.
        Perform the player's day action on the given target(s).
        Return the result of the action, or None if the action does not
        give a result."""

        if not player.has_day_action():
            raise ActionError("This player doesn't have a day action "
                              "that they can use")

        if player in targets and not player.role.day_action.can_target_self:
            raise InvalidTargetError("This role can't target itself")

        self.action_log.append(
            ActionEntry(player, player.role.day_action, targets))

        result = perform_day_action(player, self, targets)

        # Decrement uses remaining if applicable
        if player.day_action_uses_left > 0:
            player.day_action_uses_left -= 1

        return result

    def end_day(self):
        """End the day without a lynch."""

        self.action_log.append(NoLynchEntry())
        self.action_logs.append(self.action_log)

    def start_night(self):
        """Prepare game state for the night phase."""

        self._turn += 1
        self.phase = "night"
        self.message_queue.append("Tell everyone to go to bed")
        self.reset_action_log()

        # NOTE: currently the mafia kill can't be blocked because it has a
        # really high priority so that the game will ask for it first.
        # Need to think of a better way to do this.
        killer = self.killing_mafia()
        if killer:
            self.action_queue.append((killer, actions["mafia kill"]))

        self.action_queue.extend((p, p.role.night_action)
                                 for p in self.players
                                 if p.role.night_action)

    def next_action(self):
        """Should only be called during the night phase.
        Return a tuple of (player, action) for the player who should next
        perform a night action.
        If every player has taken their night action, return None."""

        if self.action_queue:
            # NOTE: To add Nurse and Deputy, the best way to arrange it is
            # probably to return them here instead of the doc/cop if the
            # original role is dead.
            player, action = self.action_queue.popleft()
            self.message_queue.append(
                "Ask {} for their {} action".format(
                    player.role_name, action.name))
            return (player, action)

        self.message_queue.append("All actions in")

    def killing_mafia(self):
        """Return the player that carries out the mafia kill tonight.
        If all the mafia are dead, return None."""

        return next(filter(lambda p: p.is_alive, self.mafia_hierarchy), None)

    def living_players(self):
        """Return a list of all the players that are currently alive."""

        return list(filter(lambda p: p.is_alive, self.players))

    def has_been_blocked(self, player):
        """Return True if player has been blocked tonight, False otherwise."""

        return any(player in log.targets and log.action.name == "block"
                   and not self.has_been_blocked(log.player)
                   for log in self.action_log)

    def do_night_action(self, player, action, targets):
        """Should only be called during the night phase.
        Add player's night action to the action log.
        If the night action is one that needs to be performed immediately
        (e.g. inspection), perform it and all results (if any) to the
        message queue.
        Return the result of the night action if it was performed immediately,
        otherwise return None."""

        validate_night_action(player, action, targets, self)

        self.action_log.append(ActionEntry(player, action, targets))

        # Decrement remaining uses, if applicable
        # Note: limited uses are based on night action attempts, i.e.
        # if a role is blocked, it still loses a use if it tries to use
        # its action.
        if (action == player.role.night_action and
            player.night_action_uses_left > 0):
            player.night_action_uses_left -= 1

        # Actions that need to be performed immediately
        if action.immediate:
            result = perform_night_action(player, action, self, targets)
            # TODO: put this in the action function instead
            self.message_queue.append("Inspection result: {}".format(
                result))
            return result

    def do_passive_action(self, player, performed_actions):
        """Perform a player's passive action, if applicable."""

        result = perform_passive_action(player, player.role.passive_action,
            self, performed_actions)

        if result and player.passive_action_uses_left > 0:
            player.passive_action_uses_left -= 1

    def process_night_actions(self):
        """Should be called once all night actions have been submitted.
        Resolve the night actions and change the game state accordingly."""

        self.action_logs.append(copy(self.action_log))

        # Sort the action log by increasing night action priority
        # (We'll go through this list in reverse.)
        self.action_log.sort(
            key=lambda entry: entry.action.priority)

        # Need to keep record of actions actually performed for passive roles
        performed_actions = []

        # Pop each entry from the log and perform its action.
        # Note that performing actions may modify the action log (e.g.
        # roleblocking), which is why we can't just iterate through it.
        while self.action_log:
            player, action, targets = self.action_log.pop().data()
            performed_actions.append((player, action, targets))
            if not action.immediate:
                perform_night_action(player, action, self, targets)


        # Perform passive actions, if applicable.
        # Currently passive actions don't add anything to the action log.
        passive_actors = sorted(
            filter(lambda p: p.has_passive_action(), self.players),
            key=lambda p: priority_key(p.role.passive_action))
        for player in passive_actors:
            self.do_passive_action(player, performed_actions)


    def end_night(self):
        """End the night phase and process all deaths."""

        announcements = []

        if not self.death_queue:
            self.message_queue.append("No one died!")

        # Empty the death queue
        while self.death_queue:
            dead_player = self.death_queue.dequeue()
            announcements.append("{} is dead".format(dead_player.name))
            dead_player.is_alive = False

        # Clean up
        self.action_log = []
        for player in self.players:
            player.reset_nightly_flags()

        # Read all death announcements in a random order
        shuffle(announcements)
        self.message_queue.extend(announcements)

        # Invoke end-of-night hooks
        while self.night_end_hooks:
            self.night_end_hooks.pop()(self)

        self.check_winner()

    def check_winner(self):
        """Check if a win condition has been met. If so, raise GameOver with
        the name of the winning faction."""

        self.winner = self.calculate_winner()
        if self.winner:
            raise GameOver(self.winner)

    def calculate_winner(self):
        """If a win condition has been met, return the name of the winning
        faction.
        If everybody loses, return "no one".
        Otherwise, return None."""

        living_players = [p for p in self.players if p.is_alive]
        num_living = len(living_players)
        living_mafia = 0
        living_town = 0
        living_cult = 0
        living_third_party = []

        for player in living_players:
            if player.alignment == "mafia":
                living_mafia += 1
            elif player.alignment == "town":
                living_town += 1
            elif player.alignment == "cult":
                living_cult += 1
            else:
                living_third_party.append(player)

        # Need to figure out priority of win conditions
        if not living_players:
            return "no one" # everybody loses

        for player in living_third_party:
            # Assumes there can only be one serial killer in a game
            if player.role.name == "Serial Killer" and num_living <= 2:
                return "Serial Killer"
            # Add more third-party roles

        if not living_mafia and not living_cult and not living_third_party:
            return "Town"
        elif living_mafia >= num_living / 2:
            return "Mafia"
        elif living_cult >= num_living / 2:
            return "Cult"

    def pop_messages(self):
        """Clear the message queue and return a list of the messages that
        were on it, in the same order."""

        temp = self.message_queue
        self.message_queue = deque()
        return temp
