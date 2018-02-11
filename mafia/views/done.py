from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther

from ..views import games

@view_config(route_name="done", renderer="done.mako")
def game_over(context, request):

    game_id = request.session.setdefault("game_id", None)

    if not game_id:
        request.session.flash("You don't have a game in progress.")
        return HTTPSeeOther("/")

    game = games[game_id]

    if not game.winner:
        request.session.flash("This game isn't over yet.")
        return HTTPSeeOther("/play")

    return {"game": game, "messages": game.pop_messages()}
