import wtforms

class NoTargetForm(wtforms.Form):
    """A form for a player to choose a yes/no action."""

    choice = wtforms.BooleanField("Use action?")
    submit = wtforms.SubmitField("Decide")

class TargetForm(wtforms.Form):
    """A form for a player to choose night action targets."""

    targets = wtforms.FieldList(wtforms.SelectField(choices=[], coerce=int))
    submit = wtforms.SubmitField("Submit")

class SkipForm(wtforms.Form):
    """A form for skipping a dead player's action after pretending to ask
    them for it."""

    submit = wtforms.SubmitField("Skip")

def fix_target_form(form, player, action, targets):
    """Dynamically set the proper attributes in a TargetForm."""

    if action.optional:
        targets = [(-1, "Don't use")] + targets

    for entry in form.targets:
        entry.choices = targets

def build_night_form(game, next_player, players):
    """Depending on the next player to take their action, return the proper
    action form."""

    player, action = next_player

    if not (action.name == "mafia kill" or player.has_night_action()):
        return SkipForm()

    num_targets = action.targets

    if not num_targets:
        return NoTargetForm()

    else:
        form = TargetForm()
        for i in range(num_targets):
            form.targets.append_entry()
        fix_target_form(form, player, action, players)
        return form

def process_night_click(request, game):
    """Process a submitted night action and prompt for the next one.
    If the target was invalid, raise an error.
    Return True if the action was successfully processed, False otherwise."""

    # Figure out what kind of form this was
    # There must be a better way to do this
    submit = request.POST["submit"]
    if submit == "Decide":
        formclass = NoTargetForm
    elif submit == "Submit":
        formclass = TargetForm
    elif submit == "Skip":
        # Skipping a dead player; no further processing necessary
        return True
    else: # this shouldn't happen
        return False

    form = formclass(request.POST)
    player, action = game.next_action()

    if isinstance(form, NoTargetForm) and not form.choice.data:
        # Chose not to use an optional action
        return True

    targets = []
    if isinstance(form, TargetForm):
        for target in form.targets:
            if target.data == -1: # no target chosen
                # Return without performing action
                return True
            targets.append(game.players[target.data])

    game.do_night_action(player, action, targets)
    return True

