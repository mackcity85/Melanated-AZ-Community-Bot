from __future__ import annotations

import os

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from .game_manager import GAME_MANAGER
from .dirty_minds import (
    next_round,
    public_room_state,
    reveal_round,
    start_game,
    submit_answer,
)

real_games_bp = Blueprint(
    "real_games",
    __name__,
    url_prefix="/real-games",
    template_folder="templates",
)


GAMES = [

    # ---------------------------------------------------------
    # ARCADE
    # ---------------------------------------------------------

    {
        "game_id": "snake",
        "name": "Snake",
        "icon": "🐍",
        "category": "Arcade",
        "description": "Eat the food, grow longer, and don't hit yourself.",
    },

    {
        "game_id": "pong",
        "name": "Pong",
        "icon": "🏓",
        "category": "Arcade",
        "description": "Classic paddle battle against the computer.",
    },

    {
        "game_id": "breakout",
        "name": "Breakout",
        "icon": "🧱",
        "category": "Arcade",
        "description": "Break the blocks and keep the ball alive.",
    },

    {
        "game_id": "dodge",
        "name": "Dodge",
        "icon": "💥",
        "category": "Arcade",
        "description": "Move around and survive as long as possible.",
    },

    {
        "game_id": "2048",
        "name": "2048",
        "icon": "🔢",
        "category": "Arcade",
        "description": "Combine matching numbers and reach 2048.",
    },

    {
        "game_id": "memory_match",
        "name": "Memory Match",
        "icon": "🧠",
        "category": "Arcade",
        "description": "Find every matching pair.",
    },

    {
        "game_id": "reaction",
        "name": "Reaction Test",
        "icon": "⚡",
        "category": "Arcade",
        "description": "Wait for the signal and react as quickly as possible.",
    },

    {
        "game_id": "whack_a_mole",
        "name": "Whack-a-Mole",
        "icon": "🔨",
        "category": "Arcade",
        "description": "Tap the mole before it disappears.",
    },

    # ---------------------------------------------------------
    # BOARD
    # ---------------------------------------------------------

    {
        "game_id": "chess",
        "name": "Chess",
        "icon": "♟️",
        "category": "Board Games",
        "description": "Classic two-player chess.",
    },

    {
        "game_id": "checkers",
        "name": "Checkers",
        "icon": "🔴",
        "category": "Board Games",
        "description": "Classic checkers.",
    },

    {
        "game_id": "monopoly",
        "name": "Monopoly",
        "icon": "🏦",
        "category": "Board Games",
        "description": "Buy property, collect rent, and build your fortune.",
    },

    # ---------------------------------------------------------
    # SPORTS
    # ---------------------------------------------------------

    {
        "game_id": "basketball",
        "name": "Basketball",
        "icon": "🏀",
        "category": "Sports",
        "description": "Shoot the ball and score.",
    },

    # ---------------------------------------------------------
    # SHOOTING
    # ---------------------------------------------------------

    {
        "game_id": "target_shooter",
        "name": "Target Shooter",
        "icon": "🎯",
        "category": "Shooting",
        "description": "Hit as many targets as possible.",
    },

    # ---------------------------------------------------------
    # PARTY
    # ---------------------------------------------------------

    {
        "game_id": "dirty_minds",
        "name": "Dirty Minds",
        "icon": "🎭",
        "category": "Party",
        "description": "A multiplayer guessing game where the clues sound dirty but the answers are clean.",
        "multiplayer": True,
        "max_players": 20,
        "min_players": 2,
    },

    # ---------------------------------------------------------
    # RACING
    # ---------------------------------------------------------

    {
        "game_id": "race_car",
        "name": "Race Car Racing",
        "icon": "🏎️",
        "category": "Racing",
        "description": "Dodge traffic and survive the race.",
    },
]


VALID_GAME_IDS = {
    game["game_id"]
    for game in GAMES
}


def get_game(game_id):

    if not game_id:
        return None

    game_id = str(game_id).strip().lower()

    for game in GAMES:

        if game["game_id"].lower() == game_id:
            return game

    return None


def games_by_category():

    categories = {}

    for game in GAMES:

        category = game["category"]

        categories.setdefault(
            category,
            [],
        ).append(game)

    return categories


@real_games_bp.route("/")
def real_games_home():

    return render_template(
        "real_games.html",
        games=GAMES,
        categories=games_by_category(),
    )


@real_games_bp.route("/play/<game_id>")
def play_game(game_id):

    game = get_game(game_id)

    if game is None:

        return render_template(
            "game.html",
            game={
                "game_id": "unknown",
                "name": "Game Not Found",
                "icon": "❌",
                "category": "Unknown",
                "description": "This game is not available.",
            },
        ), 404

    # Dirty Minds gets its own multiplayer interface.
    if game_id == "dirty_minds":

        room_id = request.args.get(
            "room",
            "",
        ).strip().upper()

        player_key = request.args.get(
            "player_key",
            "",
        ).strip()

        return render_template(
            "dirty_minds.html",
            game=game,
            room_id=room_id,
            player_key=player_key,
        )

    return render_template(
        "game.html",
        game=game,
    )


@real_games_bp.route("/api/games")
def api_games():

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

@real_games_bp.route(
    "/create-room",
    methods=["POST"],
)
def create_room():

    data = request.get_json(
        silent=True
    ) or {}

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

    room = GAME_MANAGER.create(
        game_id=game["game_id"],
        game_name=game["name"],
        max_players=game.get(
            "max_players",
            2,
        ),
        min_players=game.get(
            "min_players",
            1,
        ),
    )

    return jsonify(
        {
            "success": True,
            "room_id": room.room_id,
            "game_id": game["game_id"],
            "game": game,
        }
    )


# ==========================================================
# ROOM INFORMATION
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>"
)
def room_info(room_id):

    room = GAME_MANAGER.get(
        room_id
    )

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found",
            }
        ), 404

    if room.game_id == "dirty_minds":

        return jsonify(
            {
                "success": True,
                "room": public_room_state(room),
            }
        )

    return jsonify(
        {
            "success": True,
            "room": {
                "room_id": room.room_id,
                "game_id": room.game_id,
                "game_name": room.game_name,
                "players": list(
                    room.players.values()
                ),
                "started": room.started,
                "finished": room.finished,
            },
        }
    )


# ==========================================================
# DIRTY MINDS PLAYER VALIDATION
# ==========================================================

def dirty_room_and_player():

    room_id = (
        request.args.get(
            "room",
            "",
        )
        or request.form.get(
            "room",
            "",
        )
    ).strip().upper()

    player_key = (
        request.args.get(
            "player_key",
            "",
        )
        or request.form.get(
            "player_key",
            "",
        )
    ).strip()

    room = GAME_MANAGER.get(room_id)

    if not room:
        return None, None

    if room.game_id != "dirty_minds":
        return None, None

    player = room.get_player_by_key(
        player_key
    )

    if not player:
        return None, None

    return room, player


# ==========================================================
# DIRTY MINDS STATE
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/state"
)
def dirty_minds_state():

    room, player = dirty_room_and_player()

    if not room:

        return jsonify(
            {
                "success": False,
                "error": "Invalid room or player.",
            }
        ), 403

    result = public_room_state(room)

    result["success"] = True

    result["you"] = {
        "user_id": player["user_id"],
        "name": player["name"],
        "score": player.get(
            "score",
            0,
        ),
        "is_host": (
            player["user_id"]
            == room.host_id
        ),
        "answered": (
            player["user_id"]
            in room.state.get(
                "answers",
                {},
            )
        ),
    }

    return jsonify(result)


# ==========================================================
# START GAME
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/start",
    methods=["POST"],
)
def dirty_minds_start():

    room, player = dirty_room_and_player()

    if not room:

        return jsonify(
            {
                "success": False,
                "error": "Invalid room or player.",
            }
        ), 403

    if player["user_id"] != room.host_id:

        return jsonify(
            {
                "success": False,
                "error": "Only the host can start the game.",
            }
        ), 403

    try:

        start_game(room)

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400

    return jsonify(
        {
            "success": True,
            "room": public_room_state(room),
        }
    )


# ==========================================================
# SUBMIT ANSWER
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/answer",
    methods=["POST"],
)
def dirty_minds_answer():

    data = request.get_json(
        silent=True
    ) or {}

    room_id = str(
        data.get(
            "room",
            "",
        )
    ).strip().upper()

    player_key = str(
        data.get(
            "player_key",
            "",
        )
    ).strip()

    answer = str(
        data.get(
            "answer",
            "",
        )
    ).strip()

    room = GAME_MANAGER.get(
        room_id
    )

    if not room:

        return jsonify(
            {
                "success": False,
                "error": "Room not found.",
            }
        ), 404

    player = room.get_player_by_key(
        player_key
    )

    if not player:

        return jsonify(
            {
                "success": False,
                "error": "Player not found.",
            }
        ), 403

    try:

        submit_answer(
            room,
            player_key,
            answer,
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400

    return jsonify(
        {
            "success": True,
        }
    )


# ==========================================================
# REVEAL
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/reveal",
    methods=["POST"],
)
def dirty_minds_reveal():

    room, player = dirty_room_and_player()

    if not room:

        return jsonify(
            {
                "success": False,
                "error": "Invalid room or player.",
            }
        ), 403

    if player["user_id"] != room.host_id:

        return jsonify(
            {
                "success": False,
                "error": "Only the host can reveal.",
            }
        ), 403

    reveal_round(room)

    return jsonify(
        {
            "success": True,
            "room": public_room_state(room),
        }
    )


# ==========================================================
# NEXT ROUND
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/next",
    methods=["POST"],
)
def dirty_minds_next():

    room, player = dirty_room_and_player()

    if not room:

        return jsonify(
            {
                "success": False,
                "error": "Invalid room or player.",
            }
        ), 403

    if player["user_id"] != room.host_id:

        return jsonify(
            {
                "success": False,
                "error": "Only the host can start the next round.",
            }
        ), 403

    try:

        next_round(room)

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400

    return jsonify(
        {
            "success": True,
            "room": public_room_state(room),
        }
    )


# ==========================================================
# LIVEKIT TOKEN
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/livekit-token",
    methods=["POST"],
)
def dirty_minds_livekit_token():

    room, player = dirty_room_and_player()

    if not room:

        return jsonify(
            {
                "success": False,
                "error": "Invalid room or player.",
            }
        ), 403

    livekit_url = os.getenv(
        "LIVEKIT_URL"
    )

    livekit_api_key = os.getenv(
        "LIVEKIT_API_KEY"
    )

    livekit_api_secret = os.getenv(
        "LIVEKIT_API_SECRET"
    )

    if not all(
        [
            livekit_url,
            livekit_api_key,
            livekit_api_secret,
        ]
    ):

        return jsonify(
            {
                "success": False,
                "error": (
                    "LiveKit is not configured. "
                    "Add LIVEKIT_URL, LIVEKIT_API_KEY "
                    "and LIVEKIT_API_SECRET to Render."
                ),
            }
        ), 503

    try:

        from livekit import api

        # IMPORTANT:
        # Never use Telegram user IDs as the LiveKit identity.
        # The random player_key is used instead.

        token = (
            api.AccessToken(
                livekit_api_key,
                livekit_api_secret,
            )
            .with_identity(
                player["player_key"]
            )
            .with_name(
                player["name"]
            )
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=(
                        f"dirty-minds-{room.room_id}"
                    ),
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .to_jwt()
        )

    except Exception as exc:

        return jsonify(
            {
                "success": False,
                "error": (
                    f"Unable to create LiveKit token: {exc}"
                ),
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "url": livekit_url,
            "token": token,
            "room": (
                f"dirty-minds-{room.room_id}"
            ),
            "name": player["name"],
        }
    )


@real_games_bp.route(
    "/api/status"
)
def api_status():

    return jsonify(
        {
            "success": True,
            "service": "Melanated AZ Real Games",
            "status": "online",
            "games": len(GAMES),
            "game_ids": sorted(
                VALID_GAME_IDS
            ),
        }
    )


__all__ = [
    "real_games_bp",
    "GAMES",
    "VALID_GAME_IDS",
    "get_game",
    "games_by_category",
]
