from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther

from ..models import roles
from .actions import ActionError
from .game import GameOver
from .day import *
from .night import *

import wtforms


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

    players = [(i, player.name) for (i, player) in enumerate(game.players)
                if player.is_alive]

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

    if game.phase == "day":
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
