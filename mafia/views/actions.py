class ActionError(Exception):
    """Exception raised when something goes wrong while performing an action."""

    pass


class InvalidTargetError(ActionError):
    """Exception raised when an action is attempted with an invalid target."""

    pass

# Roles that can't attempt to target the same person two nights in a row
non_consecutive_target_roles = ("Doctor", "Ghoul")

def validate_night_action(user, targets):
    """Check that the targets of a user's attempted night action are valid.
    If they are not, raise an exception."""
    if user in targets and not user.role.can_target_self:
        raise InvalidTargetError("This role can't target itself")

    if user.role.name in non_consecutive_target_roles:
        if user.last_target == targets[0]:
            raise InvalidTargetError(
                "Can't target the same person two nights in a row")
        user.last_target = targets[0]

### NIGHT ACTIONS

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
    "kill": kill,
    "heal": heal,
    "block": block,
    "inspect": inspect,
}

day_actions = {
    "shoot": shoot,
}

passive_actions = {
    "bulletproof": bulletproof,
    "alien": alien,
    "bleed": bleed,
}

def perform_night_action(player, game, targets):
    """Dispatch to the appropriate night action function."""

    return night_actions[player.role.night_action](player, game, *targets)

def perform_day_action(player, game, targets):
    """Dispatch to the appropriate day action function."""

    return day_actions[player.role.day_action](player, game, *targets)

def perform_passive_action(player, game, performed_actions):
    """Dispatch to the approriate passive action function."""

    return passive_actions[player.role.passive_action](
        player, game, performed_actions)
