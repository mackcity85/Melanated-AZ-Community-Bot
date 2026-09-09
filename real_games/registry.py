from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class GameDefinition:
    game_id: str
    name: str
    icon: str
    category: str
    description: str
    mode: str = "solo"
    min_players: int = 1
    max_players: int = 1
    uses_rooms: bool = False


GAMES: List[GameDefinition] = [

    # ==========================================================
    # ARCADE
    # ==========================================================

    GameDefinition(
        "snake",
        "Snake",
        "🐍",
        "Arcade",
        "Eat the food, grow longer, and don't hit yourself."
    ),

    GameDefinition(
        "pong",
        "Pong",
        "🏓",
        "Arcade",
        "Classic paddle battle against the computer."
    ),

    GameDefinition(
        "breakout",
        "Breakout",
        "🧱",
        "Arcade",
        "Break the blocks and keep the ball alive."
    ),

    GameDefinition(
        "tetris",
        "Tetris",
        "🧩",
        "Arcade",
        "Clear lines by fitting falling blocks together."
    ),

    GameDefinition(
        "flappy",
        "Flappy",
        "🐦",
        "Arcade",
        "Tap to fly through the pipes."
    ),

    GameDefinition(
        "space_invaders",
        "Space Invaders",
        "👾",
        "Arcade",
        "Defeat the invading aliens."
    ),

    GameDefinition(
        "asteroids",
        "Asteroids",
        "☄️",
        "Arcade",
        "Destroy asteroids and survive."
    ),

    GameDefinition(
        "pac_man",
        "Pac-Man",
        "🟡",
        "Arcade",
        "Collect dots and avoid the ghosts."
    ),

    GameDefinition(
        "2048",
        "2048",
        "🔢",
        "Arcade",
        "Combine matching tiles and reach 2048."
    ),

    GameDefinition(
        "memory_match",
        "Memory Match",
        "🧠",
        "Arcade",
        "Find every matching pair."
    ),


    # ==========================================================
    # BOARD GAMES
    # ==========================================================

    GameDefinition(
        "monopoly",
        "Monopoly",
        "💰",
        "Board Games",
        "Roll, move, buy properties, and build your fortune."
    ),

    GameDefinition(
        "chess",
        "Chess",
        "♟️",
        "Board Games",
        "Classic chess against the computer."
    ),

    GameDefinition(
        "checkers",
        "Checkers",
        "🔴",
        "Board Games",
        "Jump opposing pieces and capture them."
    ),

    GameDefinition(
        "connect_four",
        "Connect Four",
        "🟠",
        "Board Games",
        "Connect four pieces before the computer does."
    ),

    GameDefinition(
        "tic_tac_toe",
        "Tic-Tac-Toe",
        "❌",
        "Board Games",
        "Get three in a row."
    ),

    GameDefinition(
        "battleship",
        "Battleship",
        "🚢",
        "Board Games",
        "Find and sink the hidden fleet."
    ),

    GameDefinition(
        "yahtzee",
        "Yahtzee",
        "🎲",
        "Board Games",
        "Roll dice and chase the best score."
    ),

    GameDefinition(
        "ludo",
        "Ludo",
        "🎯",
        "Board Games",
        "Race your pieces around the board."
    ),


    # ==========================================================
    # SPORTS
    # ==========================================================

    GameDefinition(
        "basketball",
        "Basketball",
        "🏀",
        "Sports",
        "Shoot baskets and score points."
    ),

    GameDefinition(
        "football",
        "Football",
        "🏈",
        "Sports",
        "Run the play and score touchdowns."
    ),

    GameDefinition(
        "soccer",
        "Soccer",
        "⚽",
        "Sports",
        "Shoot past the keeper and score."
    ),

    GameDefinition(
        "bowling",
        "Bowling",
        "🎳",
        "Sports",
        "Roll the ball and knock down pins."
    ),

    GameDefinition(
        "cricket",
        "Cricket",
        "🏏",
        "Sports",
        "Time your shot and score runs."
    ),


    # ==========================================================
    # SHOOTING
    # ==========================================================

    GameDefinition(
        "alien_blaster",
        "Alien Blaster",
        "👽",
        "Shooting",
        "Blast incoming aliens."
    ),

    GameDefinition(
        "space_fighter",
        "Space Fighter",
        "🚀",
        "Shooting",
        "Pilot your fighter and destroy enemies."
    ),

    GameDefinition(
        "target_shooter",
        "Target Shooter",
        "🎯",
        "Shooting",
        "Hit targets before time runs out."
    ),

    GameDefinition(
        "zombie_blaster",
        "Zombie Blaster",
        "🧟",
        "Shooting",
        "Stop the approaching zombies."
    ),


    # ==========================================================
    # SOLO CARD GAMES
    # ==========================================================

    GameDefinition(
        "blackjack",
        "Blackjack",
        "🃏",
        "Solo Games",
        "Play Blackjack against the computer dealer.",
        mode="solo",
        min_players=1,
        max_players=1,
        uses_rooms=False
    ),

    GameDefinition(
        "war",
        "War",
        "⚔️",
        "Solo Games",
        "Battle the computer by playing higher cards.",
        mode="solo",
        min_players=1,
        max_players=1,
        uses_rooms=False
    ),

    GameDefinition(
        "high_card",
        "High Card",
        "🎴",
        "Solo Games",
        "Draw a card and see if you can beat the computer.",
        mode="solo",
        min_players=1,
        max_players=1,
        uses_rooms=False
    ),

    GameDefinition(
        "go_fish",
        "Go Fish",
        "🐟",
        "Solo Games",
        "Ask the computer for cards and collect matching sets.",
        mode="solo",
        min_players=1,
        max_players=1,
        uses_rooms=False
    ),

    GameDefinition(
        "crazy_eights",
        "Crazy Eights",
        "8️⃣",
        "Solo Games",
        "Play matching cards and use eights as wild cards.",
        mode="solo",
        min_players=1,
        max_players=1,
        uses_rooms=False
    ),

    GameDefinition(
        "uno",
        "UNO",
        "🌈",
        "Solo Games",
        "Play an UNO-style card game against the computer.",
        mode="solo",
        min_players=1,
        max_players=1,
        uses_rooms=False
    ),

    GameDefinition(
        "solitaire",
        "Solitaire",
        "♠️",
        "Solo Games",
        "Play a mobile-friendly game of Solitaire.",
        mode="solo",
        min_players=1,
        max_players=1,
        uses_rooms=False
    ),
]


# ==========================================================
# CATEGORY ORDER
# ==========================================================

CATEGORY_ORDER = [
    "Arcade",
    "Board Games",
    "Sports",
    "Shooting",
    "Solo Games",
]


# ==========================================================
# INTERNAL LOOKUP
# ==========================================================

_BY_ID: Dict[str, GameDefinition] = {
    game.game_id: game
    for game in GAMES
}


# ==========================================================
# PUBLIC HELPERS
# ==========================================================

def all_games() -> List[GameDefinition]:
    return list(GAMES)


def get_game(game_id: str) -> Optional[GameDefinition]:
    if not game_id:
        return None

    gid = str(game_id).strip().lower()

    if gid.startswith("rg_"):
        gid = gid[3:]

    return _BY_ID.get(gid)


def get_games_by_category(category: str) -> List[GameDefinition]:
    return [
        game
        for game in GAMES
        if game.category == category
    ]


def get_categories() -> List[str]:
    return list(CATEGORY_ORDER)


def get_games_grouped() -> Dict[str, List[GameDefinition]]:
    return {
        category: get_games_by_category(category)
        for category in CATEGORY_ORDER
    }


def get_game_ids() -> List[str]:
    return [
        game.game_id
        for game in GAMES
    ]


def game_exists(game_id: str) -> bool:
    return get_game(game_id) is not None


# ==========================================================
# VALIDATION
# ==========================================================

def validate_registry() -> None:

    ids = get_game_ids()

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Duplicate game IDs in Real Games registry"
        )

    for game in GAMES:

        if game.category not in CATEGORY_ORDER:
            raise ValueError(
                f"Unknown game category: {game.category}"
            )


validate_registry()
