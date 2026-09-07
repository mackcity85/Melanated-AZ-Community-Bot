"""
Melanated AZ Bot
Real Games - Game Registry

PC + MOBILE COMPATIBLE GAME REGISTRY

IMPORTANT:
    This file contains GAME METADATA ONLY.

    The actual game engines are implemented by game.html.

    ONLY games with a real playable engine in game.html should
    be registered here.

Deep-link format:

    /start rg_<game_id>

Examples:

    /start rg_snake
    /start rg_pong
    /start rg_2048

Multiplayer rooms are intentionally disabled for this registry.
The current Real Games package is focused on reliable
PC + mobile browser gameplay.
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

    # Flask endpoint used by the Real Games blueprint.
    endpoint: str

    # solo / multiplayer / both
    mode: str = "solo"

    # Maximum players.
    max_players: int = 1

    # Minimum players.
    min_players: int = 1

    # GameManager rooms are disabled for this mobile/PC set.
    uses_rooms: bool = False

    # Display emoji.
    icon: str = "🎮"


# ==========================================================
# CATEGORY ORDER
# ==========================================================

CATEGORY_ORDER = [
    "Arcade",
    "Sports",
    "Shooting",
]


# ==========================================================
# GAME REGISTRY
#
# IMPORTANT:
# Keep this list synchronized with the playable engines
# inside game.html.
# ==========================================================

GAMES: dict[str, GameDefinition] = {

    # ======================================================
    # 🎮 ARCADE
    # ======================================================

    "snake": GameDefinition(
        game_id="snake",
        name="Snake",
        category="Arcade",
        description="Eat the food, grow longer, and don't hit yourself.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🐍",
    ),

    "pong": GameDefinition(
        game_id="pong",
        name="Pong",
        category="Arcade",
        description="Classic paddle action. Play against the computer.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🏓",
    ),

    "breakout": GameDefinition(
        game_id="breakout",
        name="Breakout",
        category="Arcade",
        description="Break the blocks and keep the ball alive.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🧱",
    ),

    "dodge": GameDefinition(
        game_id="dodge",
        name="Dodge",
        category="Arcade",
        description="Move around the arena and avoid the falling obstacles.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="💨",
    ),

    "2048": GameDefinition(
        game_id="2048",
        name="2048",
        category="Arcade",
        description="Combine matching tiles and reach 2048.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🔢",
    ),

    "memory_match": GameDefinition(
        game_id="memory_match",
        name="Memory Match",
        category="Arcade",
        description="Flip the cards and match all the hidden pairs.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🧠",
    ),

    "reaction": GameDefinition(
        game_id="reaction",
        name="Reaction Test",
        category="Arcade",
        description="Wait for the signal and tap as quickly as possible.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="⚡",
    ),

    "whack_a_mole": GameDefinition(
        game_id="whack_a_mole",
        name="Whack-a-Mole",
        category="Arcade",
        description="Tap the targets before they disappear.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🔨",
    ),


    # ======================================================
    # 🏀 SPORTS
    # ======================================================

    "basketball": GameDefinition(
        game_id="basketball",
        name="Basketball",
        category="Sports",
        description="Shoot the basketball and build your high score.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🏀",
    ),


    # ======================================================
    # 🎯 SHOOTING
    # ======================================================

    "target_shooter": GameDefinition(
        game_id="target_shooter",
        name="Target Shooter",
        category="Shooting",
        description="Tap the targets as quickly and accurately as possible.",
        endpoint="real_games.play_game",
        mode="solo",
        max_players=1,
        min_players=1,
        uses_rooms=False,
        icon="🎯",
    ),
}


# ==========================================================
# LOOKUP FUNCTIONS
# ==========================================================

def get_game(game_id: str) -> Optional[GameDefinition]:
    """
    Return a game definition by ID.

    Handles:
        rg_snake
        snake
        SNAKE
        snake
    """

    if not game_id:
        return None

    game_id = game_id.strip().lower()

    # Allow callers to accidentally pass the deep-link prefix.
    if game_id.startswith("rg_"):
        game_id = game_id[3:]

    return GAMES.get(game_id)


def get_games_by_category(category: str) -> list[GameDefinition]:
    """
    Return all games belonging to a category.
    """

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
    Return categories in display order.
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
    Return True if a game exists in the registry.
    """

    return get_game(game_id) is not None


# ==========================================================
# REGISTRY VALIDATION
# ==========================================================

def validate_registry() -> list[str]:
    """
    Validate the registry.

    Returns a list of problems instead of raising an exception.

    This makes it easier for routes.py or startup code to check
    the registry safely.
    """

    errors: list[str] = []

    seen_ids: set[str] = set()

    for game in GAMES.values():

        # ----------------------------------------------
        # Game ID
        # ----------------------------------------------

        if not game.game_id:
            errors.append("Game has an empty game_id.")

        if game.game_id in seen_ids:
            errors.append(
                f"Duplicate game_id: {game.game_id}"
            )

        seen_ids.add(game.game_id)

        # ----------------------------------------------
        # Name
        # ----------------------------------------------

        if not game.name.strip():
            errors.append(
                f"{game.game_id}: missing game name."
            )

        # ----------------------------------------------
        # Category
        # ----------------------------------------------

        if game.category not in CATEGORY_ORDER:
            errors.append(
                f"{game.game_id}: unknown category "
                f"'{game.category}'."
            )

        # ----------------------------------------------
        # Endpoint
        # ----------------------------------------------

        if not game.endpoint:
            errors.append(
                f"{game.game_id}: missing Flask endpoint."
            )

        # ----------------------------------------------
        # Mode
        # ----------------------------------------------

        if game.mode not in {
            "solo",
            "multiplayer",
            "both",
        }:
            errors.append(
                f"{game.game_id}: invalid mode "
                f"'{game.mode}'."
            )

        # ----------------------------------------------
        # Player counts
        # ----------------------------------------------

        if game.max_players < 1:
            errors.append(
                f"{game.game_id}: max_players must be >= 1."
            )

        if game.min_players < 1:
            errors.append(
                f"{game.game_id}: min_players must be >= 1."
            )

        if game.min_players > game.max_players:
            errors.append(
                f"{game.game_id}: min_players cannot exceed "
                f"max_players."
            )

        # ----------------------------------------------
        # Current Real Games requirement
        # ----------------------------------------------

        if game.uses_rooms:
            errors.append(
                f"{game.game_id}: room-based games are not "
                f"allowed in the PC/mobile registry."
            )

    return errors


# ==========================================================
# STARTUP CHECK
# ==========================================================

REGISTRY_ERRORS = validate_registry()


if REGISTRY_ERRORS:
    raise RuntimeError(
        "Real Games registry validation failed:\n"
        + "\n".join(
            f"  - {error}"
            for error in REGISTRY_ERRORS
        )
    )
