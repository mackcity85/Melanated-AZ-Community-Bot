from real_games.nes_games import get_nes_games


def test_nes_catalog_has_playable_games():
    games = get_nes_games()
    assert len(games) == 3
    assert {g["game_id"] for g in games} == {
        "nes_block_buster",
        "nes_star_defender",
        "nes_coin_runner",
    }
    for game in games:
        assert game["name"]
        assert game["description"]
        assert game["game_id"].startswith("nes_")


def test_nes_game_ids_are_unique():
    ids = [g["game_id"] for g in get_nes_games()]
    assert len(ids) == len(set(ids))
