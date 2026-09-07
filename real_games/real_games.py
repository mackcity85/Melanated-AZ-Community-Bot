# ==========================================================
# Melanated AZ Real Games
# real_games.py
#
# PC + MOBILE COMPATIBLE
#
# This is the SINGLE SOURCE OF TRUTH for the Real Games
# registry and Flask routes.
#
# Only games with a real playable engine in game.html
# are included.
# ==========================================================

from flask import Blueprint, render_template, jsonify, request
import uuid


# ==========================================================
# BLUEPRINT
# ==========================================================

real_games_bp = Blueprint(
    "real_games",
    __name__,
    url_prefix="/real-games",
    template_folder="templates",
)


# ==========================================================
# GAME REGISTRY
# ==========================================================
#
# IMPORTANT:
# Every game listed here MUST have a matching playable
# engine in:
#
#     real_games/templates/game.html
#
# Do NOT add games here until the game engine exists.
# ==========================================================

GAMES = [

    # ======================================================
    # ARCADE
    # ======================================================

    {
        "game_id": "snake",
        "name": "Snake",
        "icon": "🐍",
        "category": "Arcade",
        "description": (
            "Eat the food, grow longer, "
            "and don't hit yourself."
        ),
    },

    {
        "game_id": "pong",
        "name": "Pong",
        "icon": "🏓",
        "category": "Arcade",
        "description": (
            "Classic paddle battle against "
            "the computer."
        ),
    },

    {
        "game_id": "breakout",
        "name": "Breakout",
        "icon": "🧱",
        "category": "Arcade",
        "description": (
            "Break the blocks and keep "
            "the ball alive."
        ),
    },

    {
        "game_id": "dodge",
        "name": "Dodge",
        "icon": "💥",
        "category": "Arcade",
        "description": (
            "Move around and survive "
            "as long as possible."
        ),
    },

    {
        "game_id": "2048",
        "name": "2048",
        "icon": "🔢",
        "category": "Arcade",
        "description": (
            "Combine matching numbers "
            "and reach 2048."
        ),
    },

    {
        "game_id": "memory_match",
        "name": "Memory Match",
        "icon": "🧠",
        "category": "Arcade",
        "description": (
            "Find every matching pair."
        ),
    },

    {
        "game_id": "reaction",
        "name": "Reaction Test",
        "icon": "⚡",
        "category": "Arcade",
        "description": (
            "Wait for the signal and react "
            "as quickly as possible."
        ),
    },

    {
        "game_id": "whack_a_mole",
        "name": "Whack-a-Mole",
        "icon": "🔨",
        "category": "Arcade",
        "description": (
            "Tap the mole before "
            "it disappears."
        ),
    },


    # ======================================================
    # SPORTS
    # ======================================================

    {
        "game_id": "basketball",
        "name": "Basketball",
        "icon": "🏀",
        "category": "Sports",
        "description": (
            "Shoot the ball and score "
            "as many baskets as possible."
        ),
    },


    # ======================================================
    # SHOOTING
    # ======================================================

    {
        "game_id": "target_shooter",
        "name": "Target Shooter",
        "icon": "🎯",
        "category": "Shooting",
        "description": (
            "Hit as many targets as possible "
            "before time runs out."
        ),
    },
]


# ==========================================================
# VALID GAME IDS
# ==========================================================
#
# Used for fast validation and prevents random/unknown
# games from being exposed through the API.
# ==========================================================

VALID_GAME_IDS = {
    game["game_id"]
    for game in GAMES
}


# ==========================================================
# ROOM STORAGE
# ==========================================================
#
# This is lightweight in-memory room storage.
#
# NOTE:
# Render instances do not share in-memory dictionaries.
# Therefore this is suitable for basic room creation/testing,
# but persistent multiplayer rooms should eventually use
# SQLite/Redis/etc.
# ==========================================================

rooms = {}


# ==========================================================
# GAME HELPERS
# ==========================================================

def get_game(game_id):
    """
    Return a game from the registry.

    Returns:
        dict | None
    """

    if not game_id:
        return None

    game_id = str(game_id).strip().lower()

    for game in GAMES:
        if game["game_id"].lower() == game_id:
            return game

    return None


def games_by_category():
    """
    Group registered games by category.

    Returns:
        dict
    """

    categories = {}

    for game in GAMES:

        category = game["category"]

        if category not in categories:
            categories[category] = []

        categories[category].append(game)

    return categories


# ==========================================================
# REAL GAMES HOME
# ==========================================================

@real_games_bp.route("/")
def real_games_home():
    """
    Main Real Games launcher.
    """

    return render_template(
        "real_games.html",
        games=GAMES,
        categories=games_by_category(),
    )


# ==========================================================
# PLAY GAME
# ==========================================================

@real_games_bp.route("/play/<game_id>")
def play_game(game_id):
    """
    Open a specific playable game.
    """

    game = get_game(game_id)

    if game is None:

        return (
            render_template(
                "game.html",
                game={
                    "game_id": "unknown",
                    "name": "Game Not Found",
                    "icon": "❌",
                    "category": "Unknown",
                    "description": (
                        "This game is not available."
                    ),
                },
            ),
            404,
        )

    return render_template(
        "game.html",
        game=game,
    )


# ==========================================================
# GAME API
# ==========================================================

@real_games_bp.route("/api/games")
def api_games():
    """
    Return the complete Real Games registry.
    """

    return jsonify(
        {
            "success": True,
            "count": len(GAMES),
            "games": GAMES,
            "categories": games_by_category(),
        }
    )


# ==========================================================
# CREATE ROOM
# ==========================================================

@real_games_bp.route("/create-room", methods=["POST"])
def create_room():
    """
    Create a basic game room.

    Expected JSON:

        {
            "game_id": "snake"
        }
    """

    data = request.get_json(silent=True) or {}

    game_id = str(
        data.get("game_id", "")
    ).strip().lower()

    game = get_game(game_id)

    if game is None:

        return jsonify(
            {
                "success": False,
                "error": "Game not found",
            }
        ), 404

    room_id = uuid.uuid4().hex[:8].upper()

    rooms[room_id] = {
        "room_id": room_id,
        "game_id": game["game_id"],
        "game_name": game["name"],
        "players": [],
    }

    return jsonify(
        {
            "success": True,
            "room_id": room_id,
            "game_id": game["game_id"],
            "game": game,
        }
    )


# ==========================================================
# ROOM INFO
# ==========================================================

@real_games_bp.route("/room/<room_id>")
def room_info(room_id):
    """
    Return information about a game room.
    """

    room_id = str(
        room_id
    ).strip().upper()

    room = rooms.get(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "room": room,
        }
    )


# ==========================================================
# HEALTH / STATUS
# ==========================================================

@real_games_bp.route("/api/status")
def api_status():
    """
    Simple Real Games status endpoint.
    Useful for Render testing.
    """

    return jsonify(
        {
            "success": True,
            "service": "Melanated AZ Real Games",
            "status": "online",
            "games": len(GAMES),
            "game_ids": sorted(VALID_GAME_IDS),
        }
    )


# ==========================================================
# EXPORTS
# ==========================================================

__all__ = [
    "real_games_bp",
    "GAMES",
    "VALID_GAME_IDS",
    "rooms",
    "get_game",
    "games_by_category",
]
