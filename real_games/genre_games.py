from __future__ import annotations

# Original genre games with dedicated mechanics. No ROMs, ports, or copied assets.
GENRE_GAMES = [
    {"game_id":"nes_ring_rumble","name":"Ring Rumble","icon":"🥊","system_id":"nes","system_name":"NES","genre":"fighting","description":"One-on-one arcade boxing. Move, block, jab and knock down the CPU."},
    {"game_id":"snes_court_kings","name":"Court Kings","icon":"🏀","system_id":"snes","system_name":"SNES","genre":"sports","sport":"basketball","description":"Arcade basketball. Dribble, shoot and score before the clock expires."},
    {"game_id":"n64_slam_duel","name":"Slam Duel 64","icon":"🏀","system_id":"n64","system_name":"Nintendo 64","genre":"sports","sport":"basketball","description":"Fast two-lane basketball challenge with steals, shots and a score target."},
    {"game_id":"genesis_street_clash","name":"Street Clash","icon":"🥊","system_id":"genesis","system_name":"Genesis / Mega Drive","genre":"fighting","description":"Side-view arcade fighter. Advance, retreat, punch and kick through a best-of-three bout."},
    {"game_id":"ps1_knockout_circuit","name":"Knockout Circuit","icon":"🥊","system_id":"ps1","system_name":"PlayStation","genre":"fighting","description":"Timing-based boxing with stamina, guard and knockout rounds."},
    {"game_id":"ps2_pro_hoops","name":"Pro Hoops","icon":"🏀","system_id":"ps2","system_name":"PlayStation 2","genre":"sports","sport":"basketball","description":"Arcade basketball with moving defenders, shot timing and a 60-second score chase."},
    {"game_id":"xbox_gridiron_rush","name":"Gridiron Rush","icon":"🏈","system_id":"xbox","system_name":"Original Xbox","genre":"sports","sport":"football","description":"Arcade football drive. Dodge defenders, hit the holes and reach the end zone."},
    {"game_id":"xbox360_boxing_league","name":"Boxing League","icon":"🥊","system_id":"xbox360","system_name":"Xbox 360","genre":"fighting","description":"Arcade boxing league with stamina, guard, combos and three-round bouts."},
]

def get_genre_games():
    return list(GENRE_GAMES)

def get_genre_game(game_id):
    return next((g for g in GENRE_GAMES if g["game_id"] == str(game_id).lower()), None)
