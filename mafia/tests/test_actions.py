from mafia.models.roles import actions
from mafia.views.game import *
from mafia.views.actions import InvalidTargetError

import pytest

### HELPERS
def players_with_role_id(game, id):
    return filter(lambda p: p.role.id == id, game.players)

def do_default_night_action(game, player, targets):
    return game.do_night_action(player, player.role.night_action, targets)

### NIGHT ACTIONS

## HEALING
def test_heal():
    game = Game([5], False)

    doctor = game.players[0]
    do_default_night_action(game, doctor, [doctor])

    assert doctor.last_target == doctor

def test_heal_twice():
    game = Game([5], False)

    doctor = game.players[0]
    do_default_night_action(game, doctor, [doctor])

    with pytest.raises(InvalidTargetError):
        do_default_night_action(game, doctor, [doctor])

## BLOCKING
def test_block():
    game = Game([2, 4], False)

    hooker = next(players_with_role_id(game, 2))
    detective = next(players_with_role_id(game, 4))

    assert not game.has_been_blocked(detective)
    do_default_night_action(game, hooker, [detective])
    assert game.has_been_blocked(detective)

## INSPECTING
def test_detective_town():
    game = Game([3, 4], False)

    detective = next(players_with_role_id(game, 4))
    villager = next(players_with_role_id(game, 3))

    assert do_default_night_action(game, detective, [villager]) == "town"

def test_detective_mafia():
    game = Game([0, 4], False)

    detective = next(players_with_role_id(game, 4))
    mafia = next(players_with_role_id(game, 0))

    assert do_default_night_action(game, detective, [mafia]) == "mafia"

def test_detective_godfather():
    game = Game([1, 4], False)

    detective = next(players_with_role_id(game, 4))
    godfather = next(players_with_role_id(game, 1))

    assert do_default_night_action(game, detective, [godfather]) == "town"

def test_detective_self():
    game = Game([4], False)

    detective = game.players[0]

    with pytest.raises(InvalidTargetError):
        do_default_night_action(game, detective, [detective])

def test_blocked_detective():
    game = Game([2, 4], False)

    hooker = next(players_with_role_id(game, 2))
    detective = next(players_with_role_id(game, 4))

    do_default_night_action(game, hooker, [detective])
    assert do_default_night_action(game, detective, [hooker]) == "X"

def test_parity_same():
    game = Game([9, 3, 3], False)

    parity_detective = next(players_with_role_id(game, 9))
    villagers = players_with_role_id(game, 3)

    assert do_default_night_action(
        game, parity_detective, list(villagers)) == "same"

def test_parity_different():
    game = Game([9, 3, 0], False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))
    mafia = next(players_with_role_id(game, 0))

    assert (do_default_night_action(game, parity_detective, [villager, mafia])
        == "different")

def test_parity_godfather():
    game = Game([9, 3, 1], False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))
    godfather = next(players_with_role_id(game, 1))

    assert (do_default_night_action(
        game, parity_detective, [villager, godfather]) == "same")

def test_parity_self():
    game = Game([9, 3], False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))

    with pytest.raises(InvalidTargetError):
        do_default_night_action(
            game, parity_detective, [parity_detective, villager])

    with pytest.raises(InvalidTargetError):
        do_default_night_action(
            game, parity_detective, [villager, parity_detective])

def test_parity_same_target():
    game = Game([9, 3, 3], False)

    parity_detective = next(players_with_role_id(game, 9))
    villager = next(players_with_role_id(game, 3))

    with pytest.raises(InvalidTargetError):
        do_default_night_action(game, parity_detective, [villager, villager])

## KILLING
def test_mafia_kill():
    game = Game([0, 3, 3, 3], False)

    mafia = next(players_with_role_id(game, 0))
    villager = next(players_with_role_id(game, 3))

    game.do_night_action(mafia, actions["mafia kill"], [villager])
    game.process_night_actions()
    game.end_night()

    assert not villager.is_alive

def test_mafia_kill_heal():
    game = Game([0, 5, 3], False)

    mafia = next(players_with_role_id(game, 0))
    doctor = next(players_with_role_id(game, 5))

    game.do_night_action(mafia, actions["mafia kill"], [doctor])
    do_default_night_action(game, doctor, [doctor])
    game.process_night_actions()
    game.end_night()

    assert doctor.is_alive

def test_vig():
    game = Game([6, 0, 0, 3], False)

    vigilante = next(players_with_role_id(game, 6))
    mafia = next(players_with_role_id(game, 0))

    do_default_night_action(game, vigilante, [mafia])
    game.process_night_actions()
    game.end_night()

    assert not mafia.is_alive

def test_vig_heal():
    game = Game([6, 5, 0], False)

    vigilante = next(players_with_role_id(game, 6))
    doctor = next(players_with_role_id(game, 5))

    do_default_night_action(game, vigilante, [doctor])
    do_default_night_action(game, doctor, [doctor])
    game.process_night_actions()
    game.end_night()

    assert doctor.is_alive

def test_two_kills_heal():
    game = Game([6, 5, 0], False)

    vigilante = next(players_with_role_id(game, 6))
    doctor = next(players_with_role_id(game, 5))
    mafia = next(players_with_role_id(game, 0))

    game.do_night_action(mafia, actions["mafia kill"], [doctor])
    do_default_night_action(game, vigilante, [doctor])
    do_default_night_action(game, doctor, [doctor])
    game.process_night_actions()
    game.end_night()

    assert doctor.is_alive

### DAY ACTIONS

## KILLING
def test_sniper():
    game = Game([7, 3, 3, 3], True)

    sniper = next(players_with_role_id(game, 7))
    villager = next(players_with_role_id(game, 3))

    game.do_day_action(sniper, [villager])
    assert not villager.is_alive

def test_sniper_self():
    game = Game([7], True)

    sniper = game.players[0]

    with pytest.raises(InvalidTargetError):
        game.do_day_action(sniper, [sniper])

### PASSIVE ACTIONS

## BLEEDER
def test_bleed():
    game = Game([8, 0, 3], False)

    bleeder = next(players_with_role_id(game, 8))
    mafia = next(players_with_role_id(game, 0))

    assert not bleeder.is_bleeding

    game.do_night_action(mafia, actions["mafia kill"], [bleeder])
    game.process_night_actions()

    assert bleeder.is_bleeding

    game.end_night()
    assert bleeder.is_alive

def test_bleeder_healed():
    game = Game([8, 0, 5], False)

    bleeder = next(players_with_role_id(game, 8))
    mafia = next(players_with_role_id(game, 0))
    doctor = next(players_with_role_id(game, 5))

    game.do_night_action(mafia, actions["mafia kill"], [bleeder])
    do_default_night_action(game, doctor, [bleeder])
    game.process_night_actions()

    assert not bleeder.is_bleeding

def test_bleeder_death():
    game = Game([8, 0, 3, 3], False)

    bleeder = next(players_with_role_id(game, 8))
    bleeder.is_bleeding = True
    game.process_night_actions()
    game.end_night()

    assert not bleeder.is_alive

def test_bleeder_healed_after():
    game = Game([8, 5, 0, 3], False)

    bleeder = next(players_with_role_id(game, 8))
    doctor = next(players_with_role_id(game, 5))

    bleeder.is_bleeding = True
    do_default_night_action(game, doctor, [bleeder])
    game.process_night_actions()
    game.end_night()

    assert not bleeder.is_alive
