from __future__ import annotations

SNES_GAMES = [
    {"game_id": "snes_drift_racer", "name": "Drift Racer", "icon": "🏎️", "description": "Top-down turbo racing with boost and track hazards."},
    {"game_id": "snes_power_blaster", "name": "Power Blaster", "icon": "⚡", "description": "Run, jump and blast through an original action stage."},
    {"game_id": "snes_crystal_catch", "name": "Crystal Catch", "icon": "💎", "description": "Collect crystals, dodge enemies and survive the arena."},
]


def get_snes_games():
    return list(SNES_GAMES)
