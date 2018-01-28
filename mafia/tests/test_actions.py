from mafia.views.game import *
from mafia.views.actions import InvalidTargetError

import pytest

### HELPERS
def players_with_role_id(game, id):
    return filter(lambda p: p.role.id == id, game.players)

### NIGHT ACTIONS

## HEALING
def test_heal():
    players = [("doctor", 5)]
    game = Game(players, False)

    doctor = game.players[0]
    game.do_night_action(doctor, [doctor])

    assert doctor.last_target == doctor

def test_heal_twice():
    players = [("doctor", 5)]
    game = Game(players, False)

    doctor = game.players[0]
    game.do_night_action(doctor, [doctor])

    with pytest.raises(InvalidTargetError):
        game.do_night_action(doctor, [doctor])

## BLOCKING
def test_block():
    players = [("hooker", 2), ("detective", 4)]
    game = Game(players, False)

    hooker = next(players_with_role_id(game, 2))
    detective = next(players_with_role_id(game, 4))

    assert not game.has_been_blocked(detective)
    game.do_night_action(hooker, [detective])
    assert game.has_been_blocked(detective)

## INSPECTING
def test_detective_town():
    players = [("villager", 3), ("detective", 4)]
    game = Game(players, False)

    detective = next(players_with_role_id(game, 4))
    villager = next(players_with_role_id(game, 3))

    assert game.do_night_action(detective, [villager]) == "town"

def test_detective_mafia():
    players = [("mafia", 0), ("detective", 4)]
    game = Game(players, False)

    detective = next(players_with_role_id(game, 4))
    mafia = next(players_with_role_id(game, 0))

    assert game.do_night_action(detective, [mafia]) == "mafia"

def test_detective_godfather():
    players = [("godfather", 1), ("detective", 4)]
    game = Game(players, False)

    detective = next(players_with_role_id(game, 4))
    godfather = next(players_with_role_id(game, 1))

    assert game.do_night_action(detective, [godfather]) == "town"

def test_detective_self():
    players = [("detective", 4)]
    game = Game(players, False)

    detective = game.players[0]

    with pytest.raises(InvalidTargetError):
        game.do_night_action(detective, [detective])

def test_blocked_detective():
    players = [("hooker", 2), ("detective", 4)]
    game = Game(players, False)

    hooker = next(players_with_role_id(game, 2))
    detective = next(players_with_role_id(game, 4))

    game.do_night_action(hooker, [detective])
    assert game.do_night_action(detective, [hooker]) == "X"

def test_parity_same():
    players = [("parity detective", 9), ("villager 1", 3), ("villager 2", 3)]
    game = Game(players, False)

    parity_detective = next(players_with_role_id(game, 9))
    villagers = players_with_role_id(game, 3)

    assert game.do_night_action(parity_detective, list(villagers)) == "same"

def test_parity_different():
    players = [("parity detective", 9), ("villager", 3), ("mafia", 0)]
    game = Game(players, False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))
    mafia = next(players_with_role_id(game, 0))

    assert (game.do_night_action(parity_detective, [villager, mafia])
        == "different")

def test_parity_godfather():
    players = [("parity detective", 9), ("villager", 3), ("godfather", 1)]
    game = Game(players, False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))
    godfather = next(players_with_role_id(game, 1))

    assert (game.do_night_action(parity_detective, [villager, godfather])
        == "same")

def test_parity_self():
    players = [("parity detective", 9), ("villager", 3)]
    game = Game(players, False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))

    with pytest.raises(InvalidTargetError):
        game.do_night_action(parity_detective, [parity_detective, villager])

    with pytest.raises(InvalidTargetError):
        game.do_night_action(parity_detective, [villager, parity_detective])

def test_parity_same_target():
    players = [("parity detective", 9), ("villager", 3), ("dummy", 3)]
    game = Game(players, False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))

    with pytest.raises(InvalidTargetError):
        game.do_night_action(parity_detective, [villager, villager])

## KILLING
def test_mafia_kill():
    players = [("mafia", 0), ("villager", 3), ("dummy", 3), ("dummy", 3)]
    game = Game(players, False)

    mafia = next(players_with_role_id(game, 0))
    villager = next(players_with_role_id(game, 3))

    game.mafia_kill = villager
    game.process_night_actions()
    game.end_night()

    assert not villager.is_alive

def test_mafia_kill_heal():
    players = [("mafia", 0), ("doctor", 5), ("dummy", 3)]
    game = Game(players, False)

    mafia = next(players_with_role_id(game, 0))
    doctor = next(players_with_role_id(game, 5))

    game.mafia_kill = doctor
    game.do_night_action(doctor, [doctor])
    game.process_night_actions()
    game.end_night()

    assert doctor.is_alive

def test_vig():
    players = [("vigilante", 6), ("mafia", 0), ("dummy", 0), ("dummy", 3)]
    game = Game(players, False)

    vigilante = next(players_with_role_id(game, 6))
    mafia = next(players_with_role_id(game, 0))

    game.do_night_action(vigilante, [mafia])
    game.process_night_actions()
    game.end_night()

    assert not mafia.is_alive

def test_vig_heal():
    players = [("vigilante", 6), ("doctor", 5), ("mafia", 0)]
    game = Game(players, False)

    vigilante = next(players_with_role_id(game, 6))
    doctor = next(players_with_role_id(game, 5))

    game.do_night_action(vigilante, [doctor])
    game.do_night_action(doctor, [doctor])
    game.process_night_actions()
    game.end_night()

    assert doctor.is_alive

def test_two_kills_heal():
    players = [("vigilante", 6), ("doctor", 5), ("mafia", 0)]
    game = Game(players, False)

    vigilante = next(players_with_role_id(game, 6))
    doctor = next(players_with_role_id(game, 5))
    mafia = next(players_with_role_id(game, 0))

    game.mafia_kill = doctor
    game.do_night_action(vigilante, [doctor])
    game.do_night_action(doctor, [doctor])
    game.process_night_actions()
    game.end_night()

    assert doctor.is_alive

### DAY ACTIONS

## KILLING
def test_sniper():
    players = [("sniper", 7), ("villager", 3), ("dummy", 3), ("dummy", 3)]
    game = Game(players, True)

    sniper = next(players_with_role_id(game, 7))
    villager = next(players_with_role_id(game, 3))

    game.do_day_action(sniper, [villager])
    assert not villager.is_alive

def test_sniper_self():
    players = [("sniper", 7)]
    game = Game(players, True)

    sniper = game.players[0]

    with pytest.raises(InvalidTargetError):
        game.do_day_action(sniper, [sniper])

### PASSIVE ACTIONS

## BLEEDER
def test_bleed():
    players = [("bleeder", 8), ("mafia", 0), ("dummy", 3)]
    game = Game(players, False)

    bleeder = next(players_with_role_id(game, 8))
    mafia = next(players_with_role_id(game, 0))

    assert not bleeder.is_bleeding

    game.mafia_kill = bleeder
    game.process_night_actions()

    assert bleeder.is_bleeding

    game.end_night()
    assert bleeder.is_alive

def test_bleeder_healed():
    players = [("bleeder", 8), ("mafia", 0), ("doctor", 5)]
    game = Game(players, False)

    bleeder = next(players_with_role_id(game, 8))
    mafia = next(players_with_role_id(game, 0))
    doctor = next(players_with_role_id(game, 5))

    game.do_night_action(doctor, [bleeder])
    game.mafia_kill = bleeder
    game.process_night_actions()

    assert not bleeder.is_bleeding

def test_bleeder_death():
    players = [("bleeder", 8), ("mafia", 0), ("dummy", 3), ("dummy", 3)]
    game = Game(players, False)

    bleeder = next(players_with_role_id(game, 8))
    bleeder.is_bleeding = True
    game.process_night_actions()
    game.end_night()

    assert not bleeder.is_alive

def test_bleeder_healed_after():
    players = [("bleeder", 8), ("doctor", 5), ("mafia", 0), ("dummy", 3)]
    game = Game(players, False)

    bleeder = next(players_with_role_id(game, 8))
    doctor = next(players_with_role_id(game, 5))

    bleeder.is_bleeding = True
    game.do_night_action(doctor, [bleeder])
    game.process_night_actions()
    game.end_night()

    assert not bleeder.is_alive
