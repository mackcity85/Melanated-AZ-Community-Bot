# ==========================================================
# Melanated AZ Real Games
# real_games.py
#
# PC + MOBILE COMPATIBLE
# Only games with real playable engines are listed.
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
    template_folder="templates"
)


# ==========================================================
# GAME REGISTRY
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
        "description": "Eat the food, grow longer, and don't hit yourself."
    },

    {
        "game_id": "pong",
        "name": "Pong",
        "icon": "🏓",
        "category": "Arcade",
        "description": "Classic paddle battle against the computer."
    },

    {
        "game_id": "breakout",
        "name": "Breakout",
        "icon": "🧱",
        "category": "Arcade",
        "description": "Break the blocks and keep the ball alive."
    },

    {
        "game_id": "dodge",
        "name": "Dodge",
        "icon": "💥",
        "category": "Arcade",
        "description": "Move around and survive as long as possible."
    },

    {
        "game_id": "2048",
        "name": "2048",
        "icon": "🔢",
        "category": "Arcade",
        "description": "Combine matching numbers and reach 2048."
    },

    {
        "game_id": "memory_match",
        "name": "Memory Match",
        "icon": "🧠",
        "category": "Arcade",
        "description": "Find every matching pair."
    },

    {
        "game_id": "reaction",
        "name": "Reaction Test",
        "icon": "⚡",
        "category": "Arcade",
        "description": "Wait for the signal and react as quickly as possible."
    },

    {
        "game_id": "whack_a_mole",
        "name": "Whack-a-Mole",
        "icon": "🔨",
        "category": "Arcade",
        "description": "Tap the mole before it disappears."
    },


    # ======================================================
    # SPORTS
    # ======================================================

    {
        "game_id": "basketball",
        "name": "Basketball",
        "icon": "🏀",
        "category": "Sports",
        "description": "Shoot the ball and score as many baskets as possible."
    },


    # ======================================================
    # SHOOTING
    # ======================================================

    {
        "game_id": "target_shooter",
        "name": "Target Shooter",
        "icon": "🎯",
        "category": "Shooting",
        "description": "Hit as many targets as possible before time runs out."
    },
]


# ==========================================================
# ROOM STORAGE
# ==========================================================

rooms = {}


# ==========================================================
# GAME HELPERS
# ==========================================================

def get_game(game_id):
    """Return a game from the registry."""

    if not game_id:
        return None

    game_id = str(game_id).lower().strip()

    for game in GAMES:
        if game["game_id"].lower() == game_id:
            return game

    return None


def games_by_category():
    """Group games by category."""

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

    return render_template(
        "real_games.html",
        games=GAMES,
        categories=games_by_category()
    )


# ==========================================================
# PLAY GAME
# ==========================================================

@real_games_bp.route("/play/<game_id>")
def play_game(game_id):

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
                    "description": "This game is not available."
                }
            ),
            404
        )

    return render_template(
        "game.html",
        game=game
    )


# ==========================================================
# GAME API
# ==========================================================

@real_games_bp.route("/api/games")
def api_games():

    return jsonify({
        "success": True,
        "games": GAMES,
        "categories": games_by_category()
    })


# ==========================================================
# CREATE ROOM
# ==========================================================

@real_games_bp.route("/create-room", methods=["POST"])
def create_room():

    data = request.get_json(silent=True) or {}

    game_id = str(data.get("game_id", "")).lower().strip()

    game = get_game(game_id)

    if game is None:
        return jsonify({
            "success": False,
            "error": "Game not found"
        }), 404

    room_id = uuid.uuid4().hex[:8].upper()

    rooms[room_id] = {
        "room_id": room_id,
        "game_id": game["game_id"],
        "players": []
    }

    return jsonify({
        "success": True,
        "room_id": room_id,
        "game_id": game["game_id"]
    })


# ==========================================================
# ROOM INFO
# ==========================================================

@real_games_bp.route("/room/<room_id>")
def room_info(room_id):

    room_id = str(room_id).upper().strip()

    room = rooms.get(room_id)

    if room is None:
        return jsonify({
            "success": False,
            "error": "Room not found"
        }), 404

    return jsonify({
        "success": True,
        "room": room
    })


# ==========================================================
# EXPORTS
# ==========================================================

__all__ = [
    "real_games_bp",
    "GAMES",
    "get_game",
    "games_by_category"
]
