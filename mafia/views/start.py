from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from ..models import roles
from .game import Game

import wtforms
from multidict import MultiDict

role_choices = [(role.id, role.name) for role in roles]

class GameForm(wtforms.Form):
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

@view_config(route_name="start", request_method="GET", renderer="start.mako")
def create_game(context, request):
    """The page to enter a number of players and player information."""

    form = request.session.setdefault("game_form", {})
    game = request.session.setdefault("game", None)

    return {"form": GameForm(data=form), "game": game}

@view_config(route_name="start", request_method="POST", renderer="start.mako")
def create_game_process(context, request):
    """Set the number of players in a game, or start a game if ready."""

    # Delete leftover information from previous game, if present
    if "winner" in request.session:
        del request.session["winner"]
    request.session["game"] = None

    form = GameForm(request.POST)
    request.session["game_form"] = form.data

    response = {"form": form, "game": request.session["game"]}

    if not form.validate():
        return response

    # Change the number of players
    if form.set_num_players.data:
        form.add_role_fields(form.num_players.data)
        request.session["game_form"] = form.data
        return response

    # Start a game
    if form.submit.data:
        game = Game([e.data for e in form.roles.entries],
            not form.start_phase.data)
        request.session["game"] = game
        request.session["unnamed_player"] = game.next_unnamed_player()

        return HTTPFound("/play")

    return response
