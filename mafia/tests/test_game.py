from mafia.views.game import *

## HELPERS
def do_default_night_action(game, player, targets):
    return game.do_night_action(player, player.role.night_action, targets)

### CHECKING ROLEBLOCKS

def test_has_been_blocked_simple_no():
    game = Game([2, 4], False)

    detective = next(filter(lambda p: p.role.id == 4, game.players))

    assert not game.has_been_blocked(detective)

def test_has_been_blocked_simple_yes():
    game = Game([2, 4], False)

    hooker = next(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hooker, [detective])

    assert game.has_been_blocked(detective)

def test_has_been_blocked_2_chain():
    game = Game([2, 2, 4], False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hookers[0], [hookers[1]])
    do_default_night_action(game, hookers[1], [detective])

    assert not game.has_been_blocked(detective)

def test_has_been_blocked_3_chain():
    game = Game([2, 2, 2, 4], False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hookers[0], [hookers[1]])
    do_default_night_action(game, hookers[1], [hookers[2]])
    do_default_night_action(game, hookers[2], [detective])

    assert game.has_been_blocked(detective)

def test_has_been_blocked_multiple():
    game = Game([2, 2, 2, 4], False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    do_default_night_action(game, hookers[0], [hookers[1]])
    do_default_night_action(game, hookers[1], [detective])
    do_default_night_action(game, hookers[2], [detective])

    assert game.has_been_blocked(detective)


def test_has_been_blocked_multiple_hookers():
    game = Game([2, 2, 4, 3], False)

    hookers = list(filter(lambda p: p.role.id == 2, game.players))
    detective = next(filter(lambda p: p.role.id == 4, game.players))
    dummy = next(filter(lambda p: p.role.id == 3, game.players))

    do_default_night_action(game, hookers[0], [dummy])
    do_default_night_action(game, hookers[1], [detective])

    assert game.has_been_blocked(detective)

### CALCULATING WINNERS

def test_winner_town():
    game = Game([3], True)

    assert game.winner() == "Town"

def test_winner_mafia_tie():
    game = Game([0, 3], True)

    assert game.winner() == "Mafia"

def test_winner_just_mafia():
    game = Game([0], True)

    assert game.winner() == "Mafia"

def test_winner_no_one():
    game = Game([], True)

    assert game.winner() == "no one"

def test_winner_none_yet():
    game = Game([3, 5, 0], True)

    assert not game.winner()
