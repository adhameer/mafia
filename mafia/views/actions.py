class ActionError(Exception):
    """Exception raised when something goes wrong while performing an action."""

    pass


class InvalidTargetError(ActionError):
    """Exception raised when an action is attempted with an invalid target."""

    pass

# Actions that can't attempt to target the same person two nights in a row
non_consecutive_target_actions = ("heal", "ghoul")

# Actions that need to trigger immediately, as opposed to at the end of
# the night when processing
immediate_actions = ("inspect", "parity")

def validate_night_action(user, action, targets, game):
    """Check that the targets of a user's attempted night action are valid.
    If they are not, raise an exception."""

    if user in targets and not action.can_target_self:
        raise InvalidTargetError("This role can't target itself")

    # Note: if actions are added to this category that can't target themselves,
    # this will need to be revised to only raise an error if consecutive
    # targets can be avoided.
    if action.name in non_consecutive_target_actions:
        if user.last_target == targets[0]:
            raise InvalidTargetError(
                "Can't target the same person two nights in a row")
        user.last_target = targets[0]

    # Check for duplicates - but only raise an error if there are enough
    # living players that duplicates can be avoided
    living_players = len(game.living_players())
    if (len(targets) > len(set(targets)) and
        ((action.can_target_self and living_players >= len(targets)) or
        len(game.living_players()) > len(targets))):
        raise InvalidTargetError("All targets must be different")

### NIGHT ACTIONS

def mafia_kill(user, game, target):
    # Need to check here if the user was blocked, because the mafia kill action
    # has a really high priority so the game can ask for it first.
    if not game.has_been_blocked(user):
        kill(user, game, target)

def kill(user, game, target):
    game.death_queue.enqueue(target)

def heal(user, game, target):
    user.last_target = target

    # Use this if a heal should invalidate all kills
    game.death_queue.remove_all(target)

    # Use this instead if heals and kills should cancel out
    # game.death_queue.remove(target)

def block(user, game, target):
    game.action_log = [entry for entry in game.action_log
                       if entry[0] != target]

def inspect(user, game, target):
    if game.has_been_blocked(user):
        return "X" # blocked; no result

    return target.perceived_alignment

def parity(user, game, target1, target2):
    if game.has_been_blocked(user):
        return "X" # blocked; no result

    return ("same" if target1.perceived_alignment == target2.perceived_alignment
        else "different")

### DAY ACTIONS

def shoot(user, game, target):
    game.kill(target)

## PASSIVE ACTIONS
# Passive actions return True if they were used, False otherwise.
# Relevant for limited-use roles.

def bulletproof(user, game, performed_actions):
    if user in game.death_queue:
        # Remove ONE instance of user from the death queue
        game.death_queue.remove(user)
        return True

    return False

def alien(user, game, performed_actions):
    if not user.is_activated and user in game.death_queue:
        # Remove ONE instance of user from the death queue
        game.death_queue.remove(user)
        user.is_activated = True
        return True

    return False

def bleed(user, game, performed_actions):
    if user.is_bleeding:
        game.death_queue.enqueue(user)

    elif user in game.death_queue:
        # Remove ONE instance of user from the death queue.
        # Should bleeder survive all kill attempts in one night?
        game.death_queue.remove(user)
        user.is_bleeding = True
        game.message_queue.append("{} is bleeding".format(user.name))
        return True

    return False

night_actions = {
    "mafia kill": mafia_kill,
    "kill": kill,
    "heal": heal,
    "block": block,
    "inspect": inspect,
    "parity": parity,
}

day_actions = {
    "shoot": shoot,
}

passive_actions = {
    "bulletproof": bulletproof,
    "alien": alien,
    "bleed": bleed,
}

def perform_night_action(player, action, game, targets):
    """Dispatch to the appropriate night action function."""

    return night_actions[action.name](player, game, *targets)

def perform_day_action(player, game, targets):
    """Dispatch to the appropriate day action function."""

    return day_actions[player.role.day_action.name](player, game, *targets)

def perform_passive_action(player, action, game, performed_actions):
    """Dispatch to the approriate passive action function."""

    return passive_actions[action.name](player, game, performed_actions)
