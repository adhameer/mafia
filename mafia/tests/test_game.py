from mafia.views.game import *

## HELPERS
def do_default_night_action(game, player, targets):
    return game.do_night_action(player, player.role.night_action, targets)

### CHECKING ROLEBLOCKS

def test_has_been_blocked_simple_no():
    players = [("hooker", 2), ("detective", 4)]
    game = Game(players, False)

    detective = next(filter(lambda p: p.role.id == 4, game.players))

    assert not game.has_been_blocked(detective)

def test_has_been_blocked_simple_yes():
    players = [("hooker", 2), ("detective", 4)]
    game = Game(players, False)

    hooker = next(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hooker, [detective])

    assert game.has_been_blocked(detective)

def test_has_been_blocked_2_chain():
    players = [("hooker1", 2), ("hooker2", 2), ("detective", 4)]
    game = Game(players, False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hookers[0], [hookers[1]])
    do_default_night_action(game, hookers[1], [detective])

    assert not game.has_been_blocked(detective)

def test_has_been_blocked_3_chain():
    players = [("hooker1", 2), ("hooker2", 2), ("hooker3", 2), ("detective", 4)]
    game = Game(players, False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hookers[0], [hookers[1]])
    do_default_night_action(game, hookers[1], [hookers[2]])
    do_default_night_action(game, hookers[2], [detective])

    assert game.has_been_blocked(detective)

def test_has_been_blocked_multiple():
    players = [("hooker1", 2), ("hooker2", 2), ("hooker3", 2), ("detective", 4)]
    game = Game(players, False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hookers[0], [hookers[1]])
    do_default_night_action(game, hookers[1], [detective])
    do_default_night_action(game, hookers[2], [detective])

    assert game.has_been_blocked(detective)


def test_has_been_blocked_multiple_hookers():
    players = [("hooker1", 2), ("hooker2", 2), ("detective", 4), ("dummy", 3)]
    game = Game(players, False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    dummy = next(filter(lambda p: p.role.id == 3, game.players))

    do_default_night_action(game, hookers[0], [dummy])
    do_default_night_action(game, hookers[1], [detective])

    assert game.has_been_blocked(detective)

### CALCULATING WINNERS

def test_winner_town():
    players = [("villager", 3)]
    game = Game(players, True)

    assert game.winner() == "Town"

def test_winner_mafia_tie():
    players = [("mafia", 0), ("villager", 3)]
    game = Game(players, True)

    assert game.winner() == "Mafia"

def test_winner_just_mafia():
    players = [("mafia", 0)]
    game = Game(players, True)

    assert game.winner() == "Mafia"

def test_winner_no_one():
    players = []
    game = Game(players, True)

    assert game.winner() == "no one"

def test_winner_none_yet():
    players = [("villager", 3), ("doctor", 5), ("mafia", 0)]
    game = Game(players, True)

    assert not game.winner()
