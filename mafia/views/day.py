from .actions import ActionError

from flask_wtf import FlaskForm
import wtforms

class ModlessDayForm(FlaskForm):
    """A form to be used during the day before someone has died and become
    the mod. Hides all information about players' roles, alignments,
    and actions."""

    lynchee = wtforms.SelectField(choices=[], coerce=int)
    lynch_submit = wtforms.SubmitField("Lynch")

    action_user = wtforms.SelectField(choices=[], coerce=int)
    action_target = wtforms.SelectField(choices=[], coerce=int)
    action_submit = wtforms.SubmitField("Submit")

    start_night = wtforms.SubmitField("Night Phase ->")

    switch_to_modded = wtforms.SubmitField("Switch to manual modding")

class DayPlayerForm(FlaskForm):
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

class DayForm(FlaskForm):
    """A form for recording day actions."""

    actions = wtforms.FieldList(wtforms.FormField(DayPlayerForm))
    start_night = wtforms.SubmitField("Night Phase ->")

def fix_modless_form(form, players):
    """Dynamically set the proper attributes in a ModlessDayForm."""

    form.lynchee.choices = players
    form.action_user.choices = players
    form.action_target.choices = players

def fix_day_player_form(form, player, targets):
    """Dynamically set the proper attributes in a DayPlayerForm."""

    if player.has_day_action():
        form.action_target.choices = targets
        form.action_submit.label = wtforms.fields.Label(
            "action_submit", player.role.day_action.name.title())

    if player.can_use_gun():
        form.gun_target.choices = targets

def build_day_form(game, players):
    """Return a form to be displayed for the day phase, depending on whether
    or not the game has a mod yet."""

    if game.is_modless:
        form = ModlessDayForm()
        fix_modless_form(form, players)
        return form

    form = DayForm()
    for i, player in enumerate(game.players):
        form.actions.append_entry()
        # There has got to be a better way to do this.
        fix_day_player_form(form.actions[i], player, players)

    return form

def process_day_click(form, game):
    """Figure out what button in form was clicked and act accordingly."""

    # No mod yet - minimal information form
    if isinstance(form, ModlessDayForm):
        if form.switch_to_modded.data:
            game.is_modless = False

        elif form.lynch_submit.data:
            game.lynch(game.players[form.lynchee.data])
            game.start_night()

        elif form.action_submit.data:
            user = game.players[form.action_user.data]
            target = game.players[form.action_target.data]

            if not user.has_day_action():
                raise ActionError(
                    "This player doesn't have a usable day action")

            game.do_day_action(user, [target])

        return

    # We have a mod - use the regular DayForm
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
