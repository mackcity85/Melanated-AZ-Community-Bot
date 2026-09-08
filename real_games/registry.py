"""
Melanated AZ Bot
Real Games - Game Registry

PC + MOBILE COMPATIBLE GAMES
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ==========================================================
# GAME DEFINITION
# ==========================================================

@dataclass(frozen=True)
class GameDefinition:
    game_id: str
    name: str
    category: str
    description: str
    endpoint: str
    mode: str = "solo"
    max_players: int = 1
    min_players: int = 1
    uses_rooms: bool = False
    icon: str = "🎮"


# ==========================================================
# CATEGORY ORDER
# ==========================================================

CATEGORY_ORDER = [
    "Arcade",
    "Sports",
    "Shooting",
    "Party",
]


# ==========================================================
# PLAYABLE GAME REGISTRY
# ==========================================================

GAMES: dict[str, GameDefinition] = {

    # ======================================================
    # 🎮 ARCADE
    # ======================================================

    "snake": GameDefinition(
        "snake",
        "Snake",
        "Arcade",
        "Eat the food, grow longer, and avoid hitting yourself.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🐍",
    ),

    "pong": GameDefinition(
        "pong",
        "Pong",
        "Arcade",
        "Classic paddle action against the computer.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🏓",
    ),

    "breakout": GameDefinition(
        "breakout",
        "Breakout",
        "Arcade",
        "Break the blocks and keep the ball alive.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🧱",
    ),

    "dodge": GameDefinition(
        "dodge",
        "Dodge",
        "Arcade",
        "Avoid falling obstacles for as long as possible.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "💨",
    ),

    "2048": GameDefinition(
        "2048",
        "2048",
        "Arcade",
        "Combine matching tiles and reach 2048.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🔢",
    ),

    "memory_match": GameDefinition(
        "memory_match",
        "Memory Match",
        "Arcade",
        "Flip cards and match all the hidden pairs.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🧠",
    ),

    "reaction": GameDefinition(
        "reaction",
        "Reaction Test",
        "Arcade",
        "Test how quickly you can react.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "⚡",
    ),

    "whack_a_mole": GameDefinition(
        "whack_a_mole",
        "Whack-a-Mole",
        "Arcade",
        "Tap the mole before it moves.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🔨",
    ),

    "chess": GameDefinition(
        "chess",
        "Chess",
        "Arcade",
        "Two-player local chess match.",
        "real_games.play_game",
        "solo",
        1,
        2,
        False,
        "♟️",
    ),

    "checkers": GameDefinition(
        "checkers",
        "Checkers",
        "Arcade",
        "Two-player local checkers match.",
        "real_games.play_game",
        "solo",
        1,
        2,
        False,
        "🔴",
    ),

    "monopoly": GameDefinition(
        "monopoly",
        "Monopoly",
        "Arcade",
        "Buy properties and collect rent.",
        "real_games.play_game",
        "solo",
        1,
        4,
        False,
        "🎲",
    ),

    "race_car": GameDefinition(
        "race_car",
        "Race Car Racing",
        "Arcade",
        "Dodge traffic and drive as far as possible.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🏎️",
    ),

    # ======================================================
    # 🏀 SPORTS
    # ======================================================

    "basketball": GameDefinition(
        "basketball",
        "Basketball",
        "Sports",
        "Shoot hoops and build your score.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🏀",
    ),

    # ======================================================
    # 🎯 SHOOTING
    # ======================================================

    "target_shooter": GameDefinition(
        "target_shooter",
        "Target Shooter",
        "Shooting",
        "Tap the targets and test your accuracy.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🎯",
    ),

    # ======================================================
    # 🎭 PARTY
    # ======================================================

    "dirty_minds": GameDefinition(
        "dirty_minds",
        "Dirty Minds",
        "Party",
        "Multiplayer clue party game for groups.",
        "real_games.play_game",
        "multiplayer",
        1,
        20,
        True,
        "🧠",
    ),
}


# ==========================================================
# LOOKUPS
# ==========================================================

def get_game(game_id: str) -> Optional[GameDefinition]:
    if not game_id:
        return None

    game_id = game_id.strip().lower()

    if game_id.startswith("rg_"):
        game_id = game_id[3:]

    return GAMES.get(game_id)


def get_games_by_category(category: str) -> list[GameDefinition]:
    if not category:
        return []

    category = category.strip()

    return [
        game
        for game in GAMES.values()
        if game.category == category
    ]


def get_categories() -> list[str]:
    return [
        category
        for category in CATEGORY_ORDER
        if any(
            game.category == category
            for game in GAMES.values()
        )
    ]


def get_games_grouped() -> dict[str, list[GameDefinition]]:
    grouped: dict[str, list[GameDefinition]] = {
        category: []
        for category in CATEGORY_ORDER
    }

    for game in GAMES.values():
        grouped.setdefault(game.category, [])
        grouped[game.category].append(game)

    return {
        category: games
        for category, games in grouped.items()
        if games
    }


def all_games() -> list[GameDefinition]:
    return list(GAMES.values())


def get_game_ids() -> list[str]:
    return list(GAMES.keys())


def game_exists(game_id: str) -> bool:
    return get_game(game_id) is not None


# ==========================================================
# REGISTRY VALIDATION
# ==========================================================

def validate_registry() -> list[str]:
    errors: list[str] = []

    for game_id, game in GAMES.items():

        if game_id != game.game_id:
            errors.append(
                f"Dictionary key '{game_id}' does not match "
                f"game_id '{game.game_id}'."
            )

        if not game.name:
            errors.append(f"{game_id}: missing name.")

        if not game.category:
            errors.append(f"{game_id}: missing category.")

        if game.category not in CATEGORY_ORDER:
            errors.append(
                f"{game_id}: invalid category '{game.category}'."
            )

        if game.mode not in {"solo", "multiplayer", "both"}:
            errors.append(f"{game_id}: invalid mode.")

        if game.min_players < 1:
            errors.append(f"{game_id}: min_players must be >= 1.")

        if game.max_players < 1:
            errors.append(f"{game_id}: max_players must be >= 1.")

        if game.min_players > game.max_players:
            errors.append(
                f"{game_id}: min_players cannot exceed max_players."
            )

    return errors


REGISTRY_ERRORS = validate_registry()

if REGISTRY_ERRORS:
    raise RuntimeError(
        "Real Games registry validation failed:\n"
        + "\n".join(f" - {error}" for error in REGISTRY_ERRORS)
    )
