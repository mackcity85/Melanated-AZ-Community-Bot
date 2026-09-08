# ==========================================================
# Melanated AZ Real Games
# real_games/registry.py
#
# SINGLE SOURCE OF TRUTH FOR REAL GAMES
# PC + MOBILE COMPATIBLE
# ==========================================================

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
    endpoint: str = "real_games.play_game"
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
    "Board Games",
    "Sports",
    "Shooting",
]


# ==========================================================
# PLAYABLE GAME REGISTRY
#
# IMPORTANT:
# A game should only be added here when game.html contains
# a matching playable JavaScript game engine.
# ==========================================================

GAMES: dict[str, GameDefinition] = {

    # ======================================================
    # 🎮 ARCADE
    # ======================================================

    "snake": GameDefinition(
        game_id="snake",
        name="Snake",
        category="Arcade",
        description="Eat the food, grow longer, and avoid hitting yourself.",
        icon="🐍",
    ),

    "pong": GameDefinition(
        game_id="pong",
        name="Pong",
        category="Arcade",
        description="Classic paddle action against the computer.",
        icon="🏓",
    ),

    "breakout": GameDefinition(
        game_id="breakout",
        name="Breakout",
        category="Arcade",
        description="Break the blocks and keep the ball alive.",
        icon="🧱",
    ),

    "tetris": GameDefinition(
        game_id="tetris",
        name="Tetris",
        category="Arcade",
        description="Clear lines by fitting falling blocks together.",
        icon="🟦",
    ),

    "flappy": GameDefinition(
        game_id="flappy",
        name="Flappy",
        category="Arcade",
        description="Fly through the pipes without hitting them.",
        icon="🐦",
    ),

    "space_invaders": GameDefinition(
        game_id="space_invaders",
        name="Space Invaders",
        category="Arcade",
        description="Destroy the invading aliens before they reach you.",
        icon="👾",
    ),

    "asteroids": GameDefinition(
        game_id="asteroids",
        name="Asteroids",
        category="Arcade",
        description="Pilot your ship and destroy incoming asteroids.",
        icon="☄️",
    ),

    "pac_man": GameDefinition(
        game_id="pac_man",
        name="Pac-Man",
        category="Arcade",
        description="Eat the pellets and avoid the ghosts.",
        icon="🟡",
    ),

    "2048": GameDefinition(
        game_id="2048",
        name="2048",
        category="Arcade",
        description="Combine matching tiles and reach 2048.",
        icon="🔢",
    ),

    "memory_match": GameDefinition(
        game_id="memory_match",
        name="Memory Match",
        category="Arcade",
        description="Flip cards and match all the hidden pairs.",
        icon="🧠",
    ),


    # ======================================================
    # 🎲 BOARD GAMES
    # ======================================================

    "monopoly": GameDefinition(
        game_id="monopoly",
        name="Monopoly",
        category="Board Games",
        description="Roll, move, buy properties, and collect rent.",
        icon="🎩",
    ),

    "chess": GameDefinition(
        game_id="chess",
        name="Chess",
        category="Board Games",
        description="Classic strategy chess.",
        icon="♟️",
    ),

    "checkers": GameDefinition(
        game_id="checkers",
        name="Checkers",
        category="Board Games",
        description="Jump your opponent's pieces and capture them.",
        icon="🔴",
    ),

    "connect_four": GameDefinition(
        game_id="connect_four",
        name="Connect Four",
        category="Board Games",
        description="Connect four pieces in a row before your opponent.",
        icon="🔵",
    ),

    "tic_tac_toe": GameDefinition(
        game_id="tic_tac_toe",
        name="Tic-Tac-Toe",
        category="Board Games",
        description="Get three symbols in a row.",
        icon="❌",
    ),

    "battleship": GameDefinition(
        game_id="battleship",
        name="Battleship",
        category="Board Games",
        description="Find and sink the opponent's ships.",
        icon="🚢",
    ),

    "yahtzee": GameDefinition(
        game_id="yahtzee",
        name="Yahtzee",
        category="Board Games",
        description="Roll the dice and build the highest score.",
        icon="🎲",
    ),

    "ludo": GameDefinition(
        game_id="ludo",
        name="Ludo",
        category="Board Games",
        description="Race your pieces around the board and reach home.",
        icon="🎯",
    ),


    # ======================================================
    # 🏀 SPORTS
    # ======================================================

    "basketball": GameDefinition(
        game_id="basketball",
        name="Basketball",
        category="Sports",
        description="Shoot hoops and build your score.",
        icon="🏀",
    ),

    "football": GameDefinition(
        game_id="football",
        name="Football",
        category="Sports",
        description="Play a quick football challenge.",
        icon="🏈",
    ),

    "soccer": GameDefinition(
        game_id="soccer",
        name="Soccer",
        category="Sports",
        description="Score goals and beat the goalkeeper.",
        icon="⚽",
    ),

    "bowling": GameDefinition(
        game_id="bowling",
        name="Bowling",
        category="Sports",
        description="Roll the ball and knock down the pins.",
        icon="🎳",
    ),

    "cricket": GameDefinition(
        game_id="cricket",
        name="Cricket",
        category="Sports",
        description="Bat, score runs, and test your timing.",
        icon="🏏",
    ),


    # ======================================================
    # 🔫 SHOOTING
    # ======================================================

    "alien_blaster": GameDefinition(
        game_id="alien_blaster",
        name="Alien Blaster",
        category="Shooting",
        description="Blast incoming aliens and survive the attack.",
        icon="👽",
    ),

    "space_fighter": GameDefinition(
        game_id="space_fighter",
        name="Space Fighter",
        category="Shooting",
        description="Pilot your fighter and destroy enemy ships.",
        icon="🚀",
    ),

    "target_shooter": GameDefinition(
        game_id="target_shooter",
        name="Target Shooter",
        category="Shooting",
        description="Hit the targets and test your accuracy.",
        icon="🎯",
    ),

    "zombie_blaster": GameDefinition(
        game_id="zombie_blaster",
        name="Zombie Blaster",
        category="Shooting",
        description="Stop the zombies before they reach you.",
        icon="🧟",
    ),
}


# ==========================================================
# LOOKUPS
# ==========================================================

def get_game(game_id: str) -> Optional[GameDefinition]:
    """
    Return a game definition by ID.

    Accepts IDs such as:
        snake
        2048
        rg_snake
    """

    if not game_id:
        return None

    game_id = str(game_id).strip().lower()

    if game_id.startswith("rg_"):
        game_id = game_id[3:]

    return GAMES.get(game_id)


def get_games_by_category(
    category: str,
) -> list[GameDefinition]:

    if not category:
        return []

    category = category.strip()

    return [
        game
        for game in GAMES.values()
        if game.category == category
    ]


def get_categories() -> list[str]:
    """
    Return categories in the desired display order.
    """

    return [
        category
        for category in CATEGORY_ORDER
        if any(
            game.category == category
            for game in GAMES.values()
        )
    ]


def get_games_grouped() -> dict[str, list[GameDefinition]]:
    """
    Return games grouped by category.
    """

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
    """
    Return every registered game.
    """

    return list(GAMES.values())


def get_game_ids() -> list[str]:
    """
    Return all registered game IDs.
    """

    return list(GAMES.keys())


def game_exists(game_id: str) -> bool:
    """
    Check whether a game exists.
    """

    return get_game(game_id) is not None


# ==========================================================
# REGISTRY VALIDATION
# ==========================================================

def validate_registry() -> list[str]:

    errors: list[str] = []

    for game_id, game in GAMES.items():

        # Dictionary key must match internal ID
        if game_id != game.game_id:
            errors.append(
                f"Dictionary key '{game_id}' does not match "
                f"game_id '{game.game_id}'."
            )

        # Required fields
        if not game.name:
            errors.append(
                f"{game_id}: missing name."
            )

        if not game.category:
            errors.append(
                f"{game_id}: missing category."
            )

        if not game.description:
            errors.append(
                f"{game_id}: missing description."
            )

        # Category
        if game.category not in CATEGORY_ORDER:
            errors.append(
                f"{game_id}: invalid category "
                f"'{game.category}'."
            )

        # Mode
        if game.mode not in {
            "solo",
            "multiplayer",
            "both",
        }:
            errors.append(
                f"{game_id}: invalid mode."
            )

        # Player counts
        if game.min_players < 1:
            errors.append(
                f"{game_id}: min_players must be >= 1."
            )

        if game.max_players < 1:
            errors.append(
                f"{game_id}: max_players must be >= 1."
            )

        if game.min_players > game.max_players:
            errors.append(
                f"{game_id}: min_players cannot exceed "
                f"max_players."
            )

    return errors


# ==========================================================
# RUN VALIDATION WHEN IMPORTED
# ==========================================================

REGISTRY_ERRORS = validate_registry()

if REGISTRY_ERRORS:
    raise RuntimeError(
        "Real Games registry validation failed:\n"
        + "\n".join(
            f" - {error}"
            for error in REGISTRY_ERRORS
        )
    )
