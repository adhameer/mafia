from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from ..models import roles
from .game import Game

import wtforms
from multidict import MultiDict

role_choices = [(role.id, role.name) for role in roles]

def strip_whitespace(str):
    return str.strip() if str else None

class SinglePlayerForm(wtforms.Form):
    """A form with information about a single player (name and role)."""

    # The name attribute is being used for something else
    player_name = wtforms.StringField(filters=[strip_whitespace])
    role = wtforms.SelectField(choices=role_choices, coerce=int, default=0)

class PlayerForm(wtforms.Form):
    """A form for entering player info for a game."""

    num_players = wtforms.IntegerField("How many players?")
    set_num_players = wtforms.SubmitField("Go")

    players = wtforms.FieldList(wtforms.FormField(SinglePlayerForm))
    # Players that were previously removed by add_player_fields
    # It would be nice to do this as a list of hidden fields, but I couldn't
    # get that to work.
    old_players = wtforms.FieldList(wtforms.FormField(SinglePlayerForm))

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


    def add_player_fields(self, n):
        """Add or remove player fields from this form so that there are
        fields for exactly n players. Keep track of removed players to
        automatically repopulate the fields if they are removed and re-added."""

        num_players = len(self.players)

        if num_players > n:
            for i in range(num_players - n):
                self.old_players.append_entry(self.players.pop_entry().data)

        else:
            for i in range(n - num_players):
                if self.old_players:
                    self.players.append_entry(self.old_players.pop_entry().data)
                else:
                    self.players.append_entry()

    def validate(self):
        """Along with normal form validation, do some extra validation if
        the submit button has been clicked to make sure that the expected
        number of player names has been entered."""

        if not super(PlayerForm, self).validate():
            return False

        # Submit was clicked - do extra validation
        if self.submit.data:
            num_players = self.num_players.data
            entered_players = len([player for player in self.players
                                   if player.player_name.data])
            if num_players != entered_players:
                self.players.errors.append(
                    "Expected {} players, but got {}".format(
                        num_players, entered_players))
                return False

        return True

@view_config(route_name="start", request_method="GET", renderer="start.mako")
def create_game(context, request):
    """The page to enter a number of players and player information."""

    form = request.session.setdefault("player_form", {})
    game = request.session.setdefault("game", None)

    return {"form": PlayerForm(data=form), "game": game}

@view_config(route_name="start", request_method="POST", renderer="start.mako")
def create_game_process(context, request):
    """Set the number of players in a game, or start a game if ready."""

    # Delete leftover information from previous game, if present
    if "winner" in request.session:
        del request.session["winner"]
    request.session["game"] = None

    form = PlayerForm(request.POST)
    request.session["player_form"] = form.data

    response = {"form": form, "game": request.session["game"]}

    if not form.validate():
        return response

    # Change the number of players
    if form.set_num_players.data:
        form.add_player_fields(form.num_players.data)
        request.session["player_form"] = form.data
        return response

    # Start a game
    if form.submit.data:
        game = Game([(e.data["player_name"], e.data["role"])
                    for e in form.players.entries],
            not form.start_phase.data)
        request.session["game"] = game

        return HTTPFound("/play")

    return response
