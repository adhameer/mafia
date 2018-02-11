from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther

from ..models import roles
from .actions import ActionError
from .game import GameOver
from .day import *
from .night import *
from ..views import games

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

    game_id = request.session.setdefault("game_id", None)

    if not game_id:
        request.session.flash("You don't have a game in progress.")
        return HTTPSeeOther("/")

    game = games[game_id]

    if game.winner:
        # Current game is already over
        return HTTPSeeOther("/done")

    # Check if not all players have entered their names
    unnamed_player = game.next_unnamed_player()
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
        form = build_day_form(game, players)

        return {"game": game, "form": form, "messages": game.pop_messages()}

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
            return {"game": game, "form": form, "messages": messages,
                    "player": player, "action": action}

        else:
            # All night actions taken
            game.process_night_actions()

            try:
                game.end_night()
            except GameOver:
                return HTTPFound("/done")

            game.start_day()

            # Refresh
            return HTTPFound("/play")


    return {"game": game, "messages": game.pop_messages()}

@view_config(route_name="play", request_method="POST", renderer="game.mako")
def play_game_process(context, request):
    """Process clicks on the gameplay page."""

    game_id = request.session.setdefault("game_id", None)

    if not game_id:
        request.session.flash("You don't have a game in progress.")
        return HTTPSeeOther("/")

    game = games[game_id]

    if game.winner:
        # Current game is already over
        return HTTPSeeOther("/done")

    # Check for entered player names
    unnamed_player = game.next_unnamed_player()
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
            game.pop_next_unnamed_player()
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
        except GameOver:
            return HTTPFound("/done")

        # Night phase button clicked
        if form.start_night.data:
            game.end_day()
            game.start_night()

    else:
        success = False
        try:
            success = process_night_click(request, game)
        except ActionError as e:
            request.session.flash(str(e))

        if success:
            game.pop_next_action()

    # Refresh the page to invoke play_game again.
    # This also prevents accidental double requests.
    return HTTPFound("/play")
