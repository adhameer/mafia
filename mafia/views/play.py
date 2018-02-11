from flask import flash, session, redirect, url_for, render_template, request
from mafia import app

from ..models import roles
from .actions import ActionError
from .game import GameOver
from .day import *
from .night import *
from ..views import get_game

from flask_wtf import FlaskForm
import wtforms

def strip_whitespace(str):
    return str.strip() if str else None

class PlayerForm(FlaskForm):
    """A form for entering player info."""

    player_name = wtforms.StringField(filters=[strip_whitespace],
        validators=[wtforms.validators.DataRequired()])
    submit = wtforms.SubmitField("Submit")

class NextPlayerForm(FlaskForm):
    """A form for moving on to the next player that needs to enter their
    name."""

    submit = wtforms.SubmitField("Next")

@app.route("/play", methods=["GET"])
def play_game():
    """The gameplay page."""

    game_id = session.setdefault("game_id", None)
    game = get_game(game_id)

    if not game:
        flash("You don't have a game in progress.")
        return redirect("/", code=303)

    if game.winner:
        # Current game is already over
        return redirect(url_for("game_over"), code=303)

    # Check if not all players have entered their names
    unnamed_player = game.next_unnamed_player()
    if unnamed_player:
        if unnamed_player.name:
            return render_template(
                "game.html", game=game, pregame=True, form=NextPlayerForm(),
                role=unnamed_player.secret_role_name())
        else:
            return render_template(
                "game.html", game=game, pregame=True, form=PlayerForm())


    players = [(i, player.name) for (i, player) in enumerate(game.players)
                if player.is_alive]
    players.sort(key=lambda t: t[1])

    # Day phase
    if game.phase == "day":
        form = build_day_form(game, players)

        return render_template(
            "game.html", game=game, form=form, messages=game.pop_messages())

    # Night phase
    else:
        next_action = game.next_action()

        if next_action:
            # Ask for a target
            player = next_action[0]
            action = next_action[1]
            messages = game.pop_messages()
            messages.append("Ask {} for their {} action".format(
                player.role_name, action.name))
            form = build_night_form(game, next_action, players)
            return render_template(
                "game.html", game=game, form=form,
                form_type=form.__class__.__name__, messages=messages,
                player=player, action=action)

        else:
            # All night actions taken
            game.process_night_actions()

            try:
                game.end_night()
            except GameOver:
                return redirect(url_for("game_over"))

            game.start_day()

            # Refresh
            return redirect(url_for("play_game"))


    return {"game": game, "messages": game.pop_messages()}

@app.route("/play", methods=["POST"])
def play_game_process():
    """Process clicks on the gameplay page."""

    game_id = session.setdefault("game_id", None)
    game = get_game(game_id)

    if not game:
        flash("You don't have a game in progress.")
        return redirect("/", code=303)

    if game.winner:
        # Current game is already over
        return redirect(url_for("game_over"), code=303)

    # Check for entered player names
    unnamed_player = game.next_unnamed_player()
    if unnamed_player:
        # Find out which form was used
        submit = request.form["submit"]
        if submit == "Submit":
            form = PlayerForm()
            if not form.validate():
                return render_template(
                    "game.html", game=game, pregame=True, form=form)

            unnamed_player.name = form.player_name.data
            return render_template(
                "game.html", game=game, pregame=True, form=NextPlayerForm(),
                role=unnamed_player.secret_role_name())

        else:
            game.pop_next_unnamed_player()
            return redirect(url_for("play_game"))

    if game.phase == "day":
        if game.is_modless:
            form = ModlessDayForm()
        else:
            form = DayForm()

        try:
            print(form.validate())
            # Process individual player buttons
            process_day_click(form, game)
        except ActionError as e:
            flash(str(e))
        except GameOver:
            return redirect(url_for("game_over"))

        # Night phase button clicked
        if form.start_night.data:
            game.end_day()
            game.start_night()

    else:
        success = False
        try:
            success = process_night_click(request, game)
        except ActionError as e:
            flash(str(e))

        if success:
            game.pop_next_action()

    # Refresh the page to invoke play_game again.
    # This also prevents accidental double requests.
    return redirect(url_for("play_game"))
