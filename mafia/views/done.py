from mafia import app
from flask import session, redirect, url_for, render_template, flash

from ..views import get_game

@app.route("/done")
def game_over():

    game_id = session.setdefault("game_id", None)
    game = get_game(game_id)

    if not game:
        flash("You don't have a game in progress.")
        return redirect("/", code=303)

    if not game.winner:
        flash("This game isn't over yet.")
        return redirect(url_for("play_game"), code=303)

    return render_template("done.html", game=game, messages=game.pop_messages())
