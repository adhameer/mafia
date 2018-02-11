# Main-memory table of running games
games = {}
next_game_id = 1

def add_game(game):
    global games
    global next_game_id
    games[next_game_id] = game
    next_game_id += 1
    return next_game_id - 1
