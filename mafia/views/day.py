import wtforms

class DayPlayerForm(wtforms.Form):
    """A form to record a player's day actions."""

    lynch = wtforms.SubmitField("Lynch")

    # It would be much nicer and more flexible to have other actions in a
    # FieldList, but we can't easily have submit buttons within FieldLists.
    action_target = wtforms.SelectField(choices=[], coerce=int)
    action_submit = wtforms.SubmitField()
    gun_target = wtforms.SelectField(choices=[], coerce=int)
    gun_submit = wtforms.SubmitField("Use Gun")

    # Fix for rows not showing up in POST data because they have no actions.
    # There must be a better way to do this.
    hidden = wtforms.HiddenField("")

class DayForm(wtforms.Form):
    """A form for recording day actions."""

    actions = wtforms.FieldList(wtforms.FormField(DayPlayerForm))
    start_night = wtforms.SubmitField("Night Phase ->")

def fix_day_player_form(form, player, targets):
    """Dynamically set the proper attributes in a DayPlayerForm."""

    if player.has_day_action():
        form.action_target.choices = targets
        form.action_submit.label = wtforms.fields.Label(
            "action_submit", player.role.day_action.title())

    if player.can_use_gun():
        form.gun_target.choices = targets

def build_day_form(game, players):
    form = DayForm()
    for i, player in enumerate(game.players):
        form.actions.append_entry()
        # There has got to be a better way to do this.
        fix_day_player_form(form.actions[i], player, players)

    return form

def process_day_click(form, game):
    """Figure out what button in form was clicked and act accordingly."""

    for (i, subform) in enumerate(form.actions):
        player = game.players[i]
        if subform.lynch.data:
            game.lynch(player)
            return

        if subform.action_submit.data:
            target = subform.action_target.data
            game.do_day_action(player, [game.players[target]])
            return

        if subform.gun_submit.data:
            target = subform.gun_target.data
            game.do_gunshot(player, game.players[target])
            return
