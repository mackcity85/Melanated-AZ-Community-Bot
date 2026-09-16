from __future__ import annotations

# Original browser games with NES-era arcade/platform action.
# No ROMs, copyrighted game code, or proprietary assets are used.

NES_GAMES = [
    {
        "game_id": "nes_block_buster",
        "name": "Block Buster",
        "icon": "🧱",
        "category": "NES",
        "description": "Break every block, catch the ball, and clear the stage.",
    },
    {
        "game_id": "nes_star_defender",
        "name": "Star Defender",
        "icon": "🚀",
        "category": "NES",
        "description": "Blast incoming enemies, dodge fire, and survive the wave.",
    },
    {
        "game_id": "nes_coin_runner",
        "name": "Coin Runner",
        "icon": "🪙",
        "category": "NES",
        "description": "Run, jump, collect coins, and reach the flag.",
    },
]


def get_nes_games():
    return list(NES_GAMES)
