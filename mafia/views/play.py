from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther

from ..models import roles
from .actions import ActionError
from .game import GameOver
from .day import *
from .night import *

import wtforms

def strip_whitespace(str):
    return str.strip() if str else None

class PlayerForm(wtforms.Form):
    """A form for entering player info."""

    player_name = wtforms.StringField(filters=[strip_whitespace],
        validators=[wtforms.validators.DataRequired()])
    submit = wtforms.SubmitField("Submit")

class NextPlayerForm(wtforms.Form):
    """A form for moving on to the next player that needs to enter their
    name."""

    submit = wtforms.SubmitField("Next")

@view_config(route_name="play", request_method="GET", renderer="game.mako")
def play_game(context, request):
    """The gameplay page."""

    if "winner" in request.session:
        # Current game is already over
        return HTTPSeeOther("/done")

    game = request.session.setdefault("game", None)

    if not game:
        request.session.flash("You don't have a game in progress.")
        return HTTPSeeOther("/")

    # Check if not all players have entered their names
    unnamed_player = request.session.setdefault("unnamed_player", None)
    if unnamed_player:
        if unnamed_player.name:
            form = NextPlayerForm()
        else:
            form = PlayerForm()
        return {"game": game, "unnamed_player": unnamed_player, "form": form}

    players = [(i, player.name) for (i, player) in enumerate(game.players)
                if player.is_alive]
    players.sort(key=lambda t: t[1])

    # Day phase
    if game.phase == "day":
        # Delete leftover night data
        if "next_action" in request.session:
            del request.session["next_action"]

        form = build_day_form(game, players)

        return {"game": game, "form": form, "messages": game.pop_messages()}

    # Night phase
    else:
        if "next_action" not in request.session:
            request.session["next_action"] = game.next_action()

        next_action = request.session["next_action"]

        if next_action:
            # Ask for a target
            form = build_night_form(game, next_action, players)
            return {"game": game, "form": form, "messages": game.pop_messages(),
                "player": next_action[0], "action": next_action[1]}

        else:
            # All night actions taken
            game.process_night_actions()

            try:
                game.end_night()
            except GameOver as e:
                request.session["winner"] = str(e)
                return HTTPFound("/done")

            game.start_day()

            # Refresh
            return HTTPFound("/play")


    return {"game": game, "messages": game.pop_messages()}

@view_config(route_name="play", request_method="POST", renderer="game.mako")
def play_game_process(context, request):
    """Process clicks on the gameplay page."""

    if "winner" in request.session:
        # Current game is already over
        return HTTPSeeOther("/done")

    game = request.session.setdefault("game", None)

    if not game:
        request.session.flash("You don't have a game in progress.")
        return HTTPSeeOther("/")

    # Check for entered player names
    unnamed_player = request.session["unnamed_player"]
    if unnamed_player:
        # Find out which form was used
        submit = request.POST["submit"]
        if submit == "Submit":
            form = PlayerForm(request.POST)
            if not form.validate():
                return {"game": game, "unnamed_player": unnamed_player,
                        "form": form}

            unnamed_player.name = form.player_name.data
            return {"game": game, "unnamed_player": unnamed_player,
                    "form": NextPlayerForm()}

        else:
            request.session["unnamed_player"] = game.next_unnamed_player()
            return HTTPFound("/play")

    if game.phase == "day":
        if game.is_modless:
            form = ModlessDayForm(request.POST)
        else:
            form = DayForm(request.POST)

        try:
            # Process individual player buttons
            process_day_click(form, game)
        except ActionError as e:
            request.session.flash(str(e))
        except GameOver as e:
            request.session["winner"] = str(e)
            return HTTPFound("/done")

        # Night phase button clicked
        if form.start_night.data:
            game.end_day()

    else:
        success = False
        try:
            success = process_night_click(request, game)
        except ActionError as e:
            request.session.flash(str(e))

        if success:
            request.session["next_action"] = game.next_action()

    # Refresh the page to invoke play_game again.
    # This also prevents accidental double requests.
    return HTTPFound("/play")
