from flask import render_template, session, redirect
from mafia import app

from ..models import roles
from .game import Game
from ..views import add_game, get_game

from flask_wtf import FlaskForm
import wtforms
from multidict import MultiDict

role_choices = [(role.id, role.name) for role in roles]

class GameForm(FlaskForm):
    """A form for entering info to start a game."""

    num_players = wtforms.IntegerField("How many players?")
    set_num_players = wtforms.SubmitField("Go")

    roles = wtforms.FieldList(wtforms.SelectField(
        choices=role_choices, coerce=int, default=3))

    start_phase = wtforms.SelectField("Start phase",
        choices=[(0, "Day"), (1, "Night")], coerce=int, default=0)
    submit = wtforms.SubmitField("Start Game")

    def validate_num_players(form, field):
        """Make sure num_players contains an integer that is at least 3.
        wtforms.validators.NumberRange isn't good enough because it raises
        an error if num_players contains an invalid integer."""

        # field.data is None if a proper integer wasn't passed in
        if field.data is not None and field.data < 3:
            raise wtforms.validators.ValidationError(
                "Mafia isn't fun with fewer than 3 players")


    def add_role_fields(self, n):
        """Add or remove role fields from this form so that there are
        fields for exactly n roles."""

        num_players = len(self.roles)
        append_or_pop = (self.roles.append_entry if num_players < n
            else self.roles.pop_entry)

        for i in range(abs(n - num_players)):
            append_or_pop()

@app.route("/", methods=["GET"])
def create_game():
    """The page to enter a number of players and player information."""

    form = session.setdefault("game_form", {})
    game_id = session.setdefault("game_id", None)
    game = get_game(game_id)

    return render_template("start.html", form=GameForm(data=form), game=game)

@app.route("/", methods=["POST"])
def create_game_process():
    """Set the number of players in a game, or start a game if ready."""

    # Delete leftover information from previous game, if present
    session["game_id"] = None

    form = GameForm()
    session["game_form"] = form.data

    response = {"form": form, "game": None}

    if not form.validate():
        return render_template("start.html", **response)

    # Change the number of players
    if form.set_num_players.data:
        form.add_role_fields(form.num_players.data)
        session["game_form"] = form.data
        return render_template("start.html", **response)

    # Start a game
    if form.submit.data:
        game = Game([e.data for e in form.roles.entries],
            not form.start_phase.data)
        session["game_id"] = add_game(game)

        return redirect("/play")

    return render_template("start.html", **response)
