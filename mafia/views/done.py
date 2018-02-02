from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther

@view_config(route_name="done", renderer="done.mako")
def game_over(context, request):

    game = request.session.setdefault("game", None)

    if not game:
        request.session.flash("You don't have a game in progress.")
        return HTTPSeeOther("/")

    if not game.winner:
        request.session.flash("This game isn't over yet.")
        return HTTPSeeOther("/play")

    return {"game": game, "messages": game.pop_messages()}
