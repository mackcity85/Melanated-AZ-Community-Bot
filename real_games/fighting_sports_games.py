from __future__ import annotations

# Dedicated original gameplay titles. These are not generic retro skins.

FIGHTING_GAMES = [
    {"game_id":"fight_street_brawl","name":"Street Brawl","icon":"🥊","genre":"Fighting","description":"1v1 side-view arcade fighting with punches, kicks, blocking and knockouts."},
    {"game_id":"fight_knockout_kings","name":"Knockout Kings","icon":"🥊","genre":"Fighting","description":"Arcade boxing with guard, body/head attacks, stamina and three-round fights."},
    {"game_id":"fight_warrior_clash","name":"Warrior Clash","icon":"⚔️","genre":"Fighting","description":"Fast arena combat with attack chains, dash movement and a visible health bar."},
]

SPORTS_GAMES = [
    {"game_id":"sport_hoops_battle","name":"Hoops Battle","icon":"🏀","genre":"Sports","sport":"basketball","description":"Arcade basketball with dribbling, shooting, a hoop, score and shot timing."},
    {"game_id":"sport_street_football","name":"Street Football","icon":"🏈","genre":"Sports","sport":"football","description":"Arcade football with running lanes, defenders, tackling and touchdowns."},
    {"game_id":"sport_turbo_soccer","name":"Turbo Soccer","icon":"⚽","genre":"Sports","sport":"soccer","description":"Top-down soccer with a ball, goals, opponents and a match clock."},
    {"game_id":"sport_home_run_derby","name":"Home Run Derby","icon":"⚾","genre":"Sports","sport":"baseball","description":"Batting timing game with pitches, contact, distance and home runs."},
]

FIGHTING_SPORTS_GAMES = FIGHTING_GAMES + SPORTS_GAMES


def get_fighting_games():
    return list(FIGHTING_GAMES)


def get_sports_games():
    return list(SPORTS_GAMES)


def get_fighting_sports_games():
    return list(FIGHTING_SPORTS_GAMES)


def get_fighting_sports_game(game_id: str):
    gid = str(game_id or "").strip().lower()
    return next((g for g in FIGHTING_SPORTS_GAMES if g["game_id"] == gid), None)
