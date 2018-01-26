from .actions import (
    validate_night_action,
    perform_night_action,
    perform_day_action,
    perform_passive_action,
    ActionError, InvalidTargetError
)
from .player import Player

from collections import deque
from copy import copy
from random import shuffle, randint

def priority_key(k, reverse=True):
    """Use for sorting players by night or passive action priority."""

    if k is not None:
        return -k if reverse else k
    return float("inf") if reverse else float("-inf")

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

    # Actions that need to trigger immediately, as opposed to at the end of
    # the night when processing
    immediate_actions = ("inspect")

    def __init__(self, players, day_start):

        # Players in the game, sorted by alignment and then decreasing
        # night action priority
        self.players = sorted([Player(*data) for data in players],
            key=lambda p: (p.role.alignment_id,
            priority_key(p.role.night_action_priority)))

        # Queue of messages to be accessed by the UI
        self.message_queue = deque()

        # Data for night phase
        self.action_queue = deque()
        self.death_queue = DeathQueue()
        self.mafia_kill = None
        self.action_log = []

        # Used to figure out which mafia member carries out the kill
        # This relies on the fact that the plain Mafia role has the lowest id.
        # Note: self.players is already sorted by alignment, so this could be
        # made more efficient, but not really worth it.
        # The random number is to stop plain mafia members from always being
        # ranked in the order they were initially entered.
        mafia_members = filter(lambda p: p.role.alignment == "mafia",
            self.players)
        self.mafia_hierarchy = sorted(mafia_members,
            key=lambda p: (p.role.id, randint(0, 5)))

        # Game log
        self.action_logs = []

        if day_start:
            self.turn = 1
            self.phase = "day"
        else:
            self.turn = 0
            self.phase = "night"

    def lynch(self, player):
        """Lynch a player. Triggers win condition for active alien and fool."""

        if player.role.name == "fool" or (player.role.name == "alien" and \
            player.is_activated):
            # TODO: End the game
            return

        self.kill(player)
        self.message_queue.append("{} was lynched".format(player.name))

        self.start_night()

    def kill(self, player):
        """Kill a player immediately. Used for gunshots, etc."""

        player.is_alive = False

        maybe_winner = self.winner()
        if maybe_winner:
            # TODO: End the game
            return

    def start_day(self):
        """Prepare game state for the day phase."""

        self.phase = "day"
        self.message_queue.append("Tell everyone to wake up")

    def do_gunshot(self, player, target):
        """Should only be called during the day phase. Kill the target
        immediately and take away player's gun."""

        if player == target:
            raise InvalidTargetError("You can't shoot yourself with a gun")

        self.kill(target)
        player.has_gun = False

    def do_day_action(self, player, targets):
        """Should only be called during the day phase.
        Perform the player's day action on the given target(s).
        Return the result of the action, or None if the action does not
        give a result."""

        if player in targets and not player.role.can_target_self:
            raise InvalidTargetError("This role can't target itself")

        result = perform_day_action(player, self, targets)

        # Decrement uses remaining if applicable
        if player.day_action_uses_left > 0:
            player.day_action_uses_left -= 1

        return result

    def start_night(self):
        """Prepare game state for the night phase."""

        self.phase = "night"
        self.action_queue.extend(p for p in self.players
                                 if p.role.night_action)
        self.message_queue.append("Tell everyone to go to bed")

    def next_action(self):
        """Should only be called during the night phase.
        Return the player who should next perform a night action.
        If the mafia should next decide a kill, return "mafia".
        If every player has taken their night action, return None."""

        if not self.mafia_kill and self.killing_mafia():
            self.message_queue.append("Ask the mafia to choose a target")
            return "mafia"

        if self.action_queue:
            # NOTE: To add Nurse and Deputy, the best way to arrange it is
            # probably to return them here instead of the doc/cop if the
            # original role is dead.
            player = self.action_queue.popleft()
            self.message_queue.append(
                "Ask the {} for their action".format(player.role.name))
            return player

        self.message_queue.append("All actions in")

    def killing_mafia(self):
        """Return the player that carries out the mafia kill tonight.
        If all the mafia are dead, return None."""

        return next(filter(lambda p: p.is_alive, self.mafia_hierarchy), None)

    def has_been_blocked(self, player):
        """Return True if player has been blocked tonight, False otherwise."""

        return any(player in targets and user.role.night_action == "block"
                   and not self.has_been_blocked(user)
                   for (user, targets) in self.action_log)

    def do_night_action(self, player, targets):
        """Should only be called during the night phase.
        Add player's night action to the action log.
        If the night action is one that needs to be performed immediately
        (e.g. inspection), perform it and all results (if any) to the
        message queue.
        Return the result of the night action if it was performed immediately,
        otherwise return None."""

        validate_night_action(player, targets)

        if player.has_night_action():
            self.action_log.append((player, targets))

            # Decrement remaining uses, if applicable
            # Note: limited uses are based on night action attempts, i.e.
            # if a role is blocked, it still loses a use if it tries to use
            # its action.
            if player.night_action_uses_left > 0:
                player.night_action_uses_left -= 1

            # Actions that need to be performed immediately
            if player.role.night_action in Game.immediate_actions:
                result = perform_night_action(player, self, targets)
                self.message_queue.append("Inspection result: {}".format(
                    result))
                return result

    def do_passive_action(self, player, performed_actions):
        """Perform a player's passive action, if applicable."""

        if (perform_passive_action(player, self, performed_actions) and
            player.passive_action_uses_left > 0):
            player.passive_action_uses_left -= 1

    def process_night_actions(self):
        """Should be called once all night actions have been submitted.
        Resolve the night actions and change the game state accordingly."""

        self.action_logs.append(copy(self.action_log))

        # Sort the action log by increasing night action priority
        # (We'll go through this list in reverse.)
        self.action_log.sort(
            key=lambda entry: entry[0].role.night_action_priority)

        # Need to keep record of actions actually performed for passive roles
        performed_actions = []

        # NOTE: Currently the mafia kill can't be roleblocked, etc.
        if self.mafia_kill:
            self.death_queue.enqueue(self.mafia_kill)

        # Pop each entry from the log and perform its action.
        # Note that performing actions may modify the action log (e.g.
        # roleblocking), which is why we can't just iterate through it.
        while self.action_log:
            player, targets = self.action_log.pop()
            performed_actions.append((player, targets))
            if not player.role.night_action in Game.immediate_actions:
                perform_night_action(player, self, targets)


        # Perform passive actions, if applicable.
        # Currently passive actions don't add anything to the action log.
        passive_actors = sorted(
            filter(lambda p: p.has_passive_action(), self.players),
            key=lambda p: priority_key(p.role.passive_action_priority))
        for player in passive_actors:
                self.do_passive_action(player, performed_actions)


    def end_night(self):
        """End the night phase and process all deaths."""

        self.turn += 1
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
        self.mafia_kill = None
        for player in self.players:
            player.reset_nightly_flags()

        # Read all death announcements in a random order
        shuffle(announcements)
        self.message_queue.extend(announcements)

    def winner(self):
        """If a win condition has been met, return the name of the winning
        faction.
        If everybody loses, return "no one".
        Otherwise, return False."""

        living_players = [p for p in self.players if p.is_alive]
        num_living = len(living_players)
        living_mafia = 0
        living_town = 0
        living_cult = 0
        living_third_party = []

        for player in living_players:
            if player.role.alignment == "mafia":
                living_mafia += 1
            elif player.role.alignment == "town":
                living_town += 1
            elif player.role.alignment == "cult":
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

        # No win conditions met yet
        return False

    def pop_messages(self):
        """Clear the message queue and return a list of the messages that
        were on it, in the same order."""

        temp = self.message_queue
        self.message_queue = deque()
        return temp
