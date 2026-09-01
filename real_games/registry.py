"""
Melanated AZ Bot
Real Games - Game Registry

Central registry for every Real Game.

IMPORTANT:
    The registry contains game metadata only.
    Actual game implementations are loaded by routes.py.

Deep-link format:

    /start rg_<game_id>

Examples:

    /start rg_snake
    /start rg_monopoly
    /start rg_chess

Multiplayer room:

    /start rg_join_<ROOM_ID>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GameDefinition:
    game_id: str
    name: str
    category: str
    description: str

    # URL endpoint used by Flask.
    endpoint: str

    # solo / multiplayer / both
    mode: str = "solo"

    # Maximum number of players when multiplayer.
    max_players: int = 1

    # Minimum players required to start.
    min_players: int = 1

    # Whether the game uses GameManager rooms.
    uses_rooms: bool = False

    # Optional emoji.
    icon: str = "🎮"


# ==========================================================
# CATEGORY ORDER
# ==========================================================

CATEGORY_ORDER = [
    "Arcade",
    "Outdoor",
    "Solo",
    "Shooting",
    "Board Games",
    "Party Games",
    "Trivia",
    "Sports",
    "Racing",
    "Fighting",
]


# ==========================================================
# GAME REGISTRY
# ==========================================================

GAMES: dict[str, GameDefinition] = {

    # ======================================================
    # ARCADE
    # ======================================================

    "snake": GameDefinition(
        "snake",
        "Snake",
        "Arcade",
        "Classic snake action.",
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
        "Classic paddle action.",
        "real_games.play_game",
        "both",
        2,
        1,
        True,
        "🏓",
    ),

    "breakout": GameDefinition(
        "breakout",
        "Breakout",
        "Arcade",
        "Break the blocks and chase the high score.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🧱",
    ),

    "tetris": GameDefinition(
        "tetris",
        "Tetris",
        "Arcade",
        "Stack the blocks and clear lines.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🟦",
    ),

    "flappy": GameDefinition(
        "flappy",
        "Flappy",
        "Arcade",
        "Navigate through the pipes.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🐦",
    ),

    "space_invaders": GameDefinition(
        "space_invaders",
        "Space Invaders",
        "Arcade",
        "Defend Earth from the invading fleet.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "👾",
    ),

    "asteroids": GameDefinition(
        "asteroids",
        "Asteroids",
        "Arcade",
        "Destroy asteroids and survive.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "☄️",
    ),

    "pacman": GameDefinition(
        "pacman",
        "Pac-Man",
        "Arcade",
        "Eat pellets and avoid the ghosts.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🟡",
    ),

    "2048": GameDefinition(
        "2048",
        "2048",
        "Arcade",
        "Combine tiles to reach 2048.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🔢",
    ),

    "memory": GameDefinition(
        "memory",
        "Memory Match",
        "Arcade",
        "Match the hidden pairs.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🧠",
    ),


    # ======================================================
    # OUTDOOR
    # ======================================================

    "archery": GameDefinition(
        "archery",
        "Archery Challenge",
        "Outdoor",
        "Hit the target and score points.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🏹",
    ),

    "fishing": GameDefinition(
        "fishing",
        "Fishing",
        "Outdoor",
        "Catch fish and build your score.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🎣",
    ),

    "camping": GameDefinition(
        "camping",
        "Camping Adventure",
        "Outdoor",
        "Survive your outdoor adventure.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🏕️",
    ),

    "disc_golf": GameDefinition(
        "disc_golf",
        "Disc Golf",
        "Outdoor",
        "Complete the course in as few throws as possible.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🥏",
    ),

    "trail_explorer": GameDefinition(
        "trail_explorer",
        "Trail Explorer",
        "Outdoor",
        "Explore the trail and find your way through.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🥾",
    ),


    # ======================================================
    # SOLO
    # ======================================================

    "solitaire": GameDefinition(
        "solitaire",
        "Solitaire",
        "Solo",
        "Classic card solitaire.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🃏",
    ),

    "sudoku": GameDefinition(
        "sudoku",
        "Sudoku",
        "Solo",
        "Complete the number puzzle.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🔢",
    ),

    "minesweeper": GameDefinition(
        "minesweeper",
        "Minesweeper",
        "Solo",
        "Clear the board without hitting mines.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "💣",
    ),

    "wordle": GameDefinition(
        "wordle",
        "Word Challenge",
        "Solo",
        "Guess the hidden word.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🔤",
    ),

    "maze": GameDefinition(
        "maze",
        "Maze Runner",
        "Solo",
        "Find your way out of the maze.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🌀",
    ),


    # ======================================================
    # SHOOTING
    # ======================================================

    "alien_blaster": GameDefinition(
        "alien_blaster",
        "Alien Blaster",
        "Shooting",
        "Blast the alien invasion.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "👽",
    ),

    "space_fighter": GameDefinition(
        "space_fighter",
        "Space Fighter",
        "Shooting",
        "Pilot your fighter and destroy enemies.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🚀",
    ),

    "target_shooter": GameDefinition(
        "target_shooter",
        "Target Shooter",
        "Shooting",
        "Test your accuracy.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🎯",
    ),

    "zombie_blaster": GameDefinition(
        "zombie_blaster",
        "Zombie Blaster",
        "Shooting",
        "Survive waves of enemies.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🧟",
    ),


    # ======================================================
    # BOARD GAMES
    # ======================================================

    "monopoly": GameDefinition(
        "monopoly",
        "Monopoly",
        "Board Games",
        "Buy properties, collect rent and bankrupt your opponents.",
        "real_games.play_game",
        "multiplayer",
        8,
        2,
        True,
        "🎩",
    ),

    "chess": GameDefinition(
        "chess",
        "Chess",
        "Board Games",
        "Classic chess.",
        "real_games.play_game",
        "multiplayer",
        2,
        2,
        True,
        "♟️",
    ),

    "checkers": GameDefinition(
        "checkers",
        "Checkers",
        "Board Games",
        "Classic checkers.",
        "real_games.play_game",
        "multiplayer",
        2,
        2,
        True,
        "🔴",
    ),

    "connect_four": GameDefinition(
        "connect_four",
        "Connect Four",
        "Board Games",
        "Connect four pieces before your opponent.",
        "real_games.play_game",
        "multiplayer",
        2,
        2,
        True,
        "🟡",
    ),

    "tic_tac_toe": GameDefinition(
        "tic_tac_toe",
        "Tic-Tac-Toe",
        "Board Games",
        "Three in a row wins.",
        "real_games.play_game",
        "multiplayer",
        2,
        2,
        True,
        "⭕",
    ),

    "battleship": GameDefinition(
        "battleship",
        "Battleship",
        "Board Games",
        "Find and sink your opponent's fleet.",
        "real_games.play_game",
        "multiplayer",
        2,
        2,
        True,
        "🚢",
    ),

    "risk": GameDefinition(
        "risk",
        "Risk",
        "Board Games",
        "Conquer territories and defeat your opponents.",
        "real_games.play_game",
        "multiplayer",
        6,
        2,
        True,
        "🌎",
    ),

    "yahtzee": GameDefinition(
        "yahtzee",
        "Yahtzee",
        "Board Games",
        "Roll the dice and chase the best score.",
        "real_games.play_game",
        "multiplayer",
        6,
        1,
        True,
        "🎲",
    ),

    "ludo": GameDefinition(
        "ludo",
        "Ludo",
        "Board Games",
        "Race your pieces around the board.",
        "real_games.play_game",
        "multiplayer",
        4,
        2,
        True,
        "🎲",
    ),


    # ======================================================
    # PARTY
    # ======================================================

    "truth_or_dare": GameDefinition(
        "truth_or_dare",
        "Truth or Dare",
        "Party Games",
        "Party game for groups.",
        "real_games.play_game",
        "multiplayer",
        20,
        2,
        True,
        "🎉",
    ),

    "would_you_rather": GameDefinition(
        "would_you_rather",
        "Would You Rather?",
        "Party Games",
        "Pick your answer and compare with everyone.",
        "real_games.play_game",
        "multiplayer",
        20,
        2,
        True,
        "🤔",
    ),

    "two_truths": GameDefinition(
        "two_truths",
        "Two Truths & A Lie",
        "Party Games",
        "Can everyone spot the lie?",
        "real_games.play_game",
        "multiplayer",
        20,
        3,
        True,
        "😈",
    ),

    "most_likely": GameDefinition(
        "most_likely",
        "Most Likely To",
        "Party Games",
        "Vote for who is most likely.",
        "real_games.play_game",
        "multiplayer",
        20,
        3,
        True,
        "😂",
    ),


    # ======================================================
    # TRIVIA
    # ======================================================

    "trivia": GameDefinition(
        "trivia",
        "Trivia Challenge",
        "Trivia",
        "Answer questions and earn points.",
        "real_games.play_game",
        "multiplayer",
        20,
        1,
        True,
        "🧠",
    ),

    "quick_quiz": GameDefinition(
        "quick_quiz",
        "Quick Quiz",
        "Trivia",
        "Fast questions. Fast answers.",
        "real_games.play_game",
        "multiplayer",
        20,
        1,
        True,
        "❓",
    ),

    "word_challenge": GameDefinition(
        "word_challenge",
        "Word Challenge",
        "Trivia",
        "Test your vocabulary.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🔤",
    ),


    # ======================================================
    # SPORTS
    # ======================================================

    "basketball": GameDefinition(
        "basketball",
        "Basketball",
        "Sports",
        "Shoot hoops and chase a high score.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🏀",
    ),

    "football": GameDefinition(
        "football",
        "Football",
        "Sports",
        "Play football and score.",
        "real_games.play_game",
        "both",
        2,
        1,
        True,
        "🏈",
    ),

    "soccer": GameDefinition(
        "soccer",
        "Soccer",
        "Sports",
        "Score goals against your opponent.",
        "real_games.play_game",
        "both",
        2,
        1,
        True,
        "⚽",
    ),

    "bowling": GameDefinition(
        "bowling",
        "Bowling",
        "Sports",
        "Knock down the pins.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🎳",
    ),

    "cricket": GameDefinition(
        "cricket",
        "Cricket",
        "Sports",
        "Score runs and beat the opposition.",
        "real_games.play_game",
        "both",
        2,
        1,
        True,
        "🏏",
    ),


    # ======================================================
    # RACING
    # ======================================================

    "car_race": GameDefinition(
        "car_race",
        "Car Race",
        "Racing",
        "Race to the finish.",
        "real_games.play_game",
        "both",
        4,
        1,
        True,
        "🏎️",
    ),

    "traffic_racer": GameDefinition(
        "traffic_racer",
        "Traffic Racer",
        "Racing",
        "Avoid traffic and survive as long as possible.",
        "real_games.play_game",
        "solo",
        1,
        1,
        False,
        "🚗",
    ),

    "drag_race": GameDefinition(
        "drag_race",
        "Drag Race",
        "Racing",
        "Beat the other driver to the finish.",
        "real_games.play_game",
        "multiplayer",
        2,
        2,
        True,
        "🏁",
    ),

    "space_race": GameDefinition(
        "space_race",
        "Space Race",
        "Racing",
        "Race through space.",
        "real_games.play_game",
        "both",
        4,
        1,
        True,
        "🚀",
    ),


    # ======================================================
    # FIGHTING
    # ======================================================

    "tank_battle": GameDefinition(
        "tank_battle",
        "Tank Battle",
        "Fighting",
        "Destroy the opposing tank.",
        "real_games.play_game",
        "multiplayer",
        2,
        2,
        True,
        "🛡️",
    ),

    "snake_arena": GameDefinition(
        "snake_arena",
        "Snake Arena",
        "Fighting",
        "Battle other snakes for territory.",
        "real_games.play_game",
        "multiplayer",
        8,
        2,
        True,
        "🐍",
    ),

    "dodge_battle": GameDefinition(
        "dodge_battle",
        "Dodge Battle",
        "Fighting",
        "Dodge attacks and survive.",
        "real_games.play_game",
        "multiplayer",
        4,
        2,
        True,
        "🥊",
    ),
}


# ==========================================================
# LOOKUP FUNCTIONS
# ==========================================================

def get_game(game_id: str) -> Optional[GameDefinition]:
    """
    Return a game definition by ID.
    """

    if not game_id:
        return None

    return GAMES.get(game_id.lower().strip())


def get_games_by_category(category: str) -> list[GameDefinition]:
    """
    Return all games belonging to a category.
    """

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

    grouped = {
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
