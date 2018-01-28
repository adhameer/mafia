from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther

@view_config(route_name="done", renderer="done.mako")
def game_over(context, request):

    if "game" not in request.session:
        request.session.flash("You don't have a game in progress.")
        return HTTPSeeOther("/")

    if "winner" not in request.session:
        request.session.flash("This game isn't over yet.")
        return HTTPSeeOther("/play")

    game = request.session["game"]
    winner = request.session["winner"]

    return {"game": game, "winner": winner, "messages": game.pop_messages()}
