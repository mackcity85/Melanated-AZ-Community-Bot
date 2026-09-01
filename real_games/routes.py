"""
Melanated AZ Bot
Real Games - Flask Routes

Real Games launcher and multiplayer room routes.
"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from .game_manager import GAME_MANAGER
from .registry import (
    CATEGORY_ORDER,
    all_games,
    get_game,
    get_games_grouped,
)

logger = logging.getLogger(__name__)


real_games_bp = Blueprint(
    "real_games",
    __name__,
    url_prefix="/real-games",
    template_folder="templates",
)


# ==========================================================
# REAL GAMES HOME
# ==========================================================

@real_games_bp.get("/")
def real_games_home():

    grouped_games = get_games_grouped()

    return render_template(
        "real_games.html",
        games=all_games(),
        grouped_games=grouped_games,
        categories=CATEGORY_ORDER,
    )


# ==========================================================
# GAME LAUNCHER
# ==========================================================

@real_games_bp.get("/game/<game_id>")
def game_launcher(game_id):

    game = get_game(game_id)

    if not game:
        abort(
            404,
            description="Game not found."
        )

    logger.info(
        "Launching Real Game: %s (%s)",
        game.name,
        game.game_id,
    )

    return render_template(
        "game.html",
        game=game,
        room=None,
        multiplayer=game.uses_rooms,
    )


# ==========================================================
# REAL GAME PLAY ENDPOINT
#
# registry.py points every game at:
#
#     real_games.play_game
#
# This route makes that endpoint actually exist.
# ==========================================================

@real_games_bp.get("/play/<game_id>")
def play_game(game_id):

    game = get_game(game_id)

    if not game:
        abort(
            404,
            description="Game not found."
        )

    logger.info(
        "Starting game: %s (%s)",
        game.name,
        game.game_id,
    )

    return render_template(
        "game.html",
        game=game,
        room=None,
        multiplayer=game.uses_rooms,
    )


# ==========================================================
# CREATE MULTIPLAYER ROOM
# ==========================================================

@real_games_bp.post("/create/<game_id>")
def create_game_room(game_id):

    game = get_game(game_id)

    if not game:
        abort(
            404,
            description="Game not found."
        )

    if not game.uses_rooms:

        return redirect(
            url_for(
                "real_games.game_launcher",
                game_id=game.game_id,
            )
        )

    room = GAME_MANAGER.create(
        game_id=game.game_id,
        game_name=game.name,
        max_players=game.max_players,
        min_players=game.min_players,
        state={
            "game_id": game.game_id,
            "turn": None,
            "status": "waiting",
        },
    )

    return redirect(
        url_for(
            "real_games.game_room",
            game_id=game.game_id,
            room_id=room.room_id,
        )
    )


# ==========================================================
# GAME ROOM
# ==========================================================

@real_games_bp.get("/<game_id>/<room_id>")
def game_room(game_id, room_id):

    game = get_game(game_id)

    if not game:
        abort(
            404,
            description="Game not found."
        )

    room = GAME_MANAGER.get(room_id)

    if not room:
        abort(
            404,
            description="That game room no longer exists."
        )

    if room.game_id != game.game_id:

        abort(
            400,
            description="This room belongs to a different game."
        )

    return render_template(
        "game.html",
        game=game,
        room=room,
        multiplayer=game.uses_rooms,
    )


# ==========================================================
# ROOM INFORMATION API
# ==========================================================

@real_games_bp.get("/api/room/<room_id>")
def room_information(room_id):

    room = GAME_MANAGER.get(room_id)

    if not room:

        return jsonify(
            {
                "ok": False,
                "error": "Room not found.",
            }
        ), 404

    return jsonify(
        {
            "ok": True,
            "room": {
                "room_id": room.room_id,
                "game_id": room.game_id,
                "game_name": room.game_name,
                "players": list(
                    room.players.values()
                ),
                "player_count": room.player_count(),
                "max_players": room.max_players,
                "min_players": room.min_players,
                "started": room.started,
                "finished": room.finished,
                "winner_id": room.winner_id,
                "state": room.state,
            },
        }
    )


# ==========================================================
# JOIN ROOM FROM WEB
# ==========================================================

@real_games_bp.post("/api/room/<room_id>/join")
def join_room(room_id):

    room = GAME_MANAGER.get(room_id)

    if not room:

        return jsonify(
            {
                "ok": False,
                "error": "Room not found.",
            }
        ), 404

    data = request.get_json(
        silent=True
    ) or {}

    user_id = str(
        data.get("user_id", "")
    ).strip()

    display_name = str(
        data.get("display_name")
        or "Player"
    ).strip()

    if not user_id:

        return jsonify(
            {
                "ok": False,
                "error": "user_id is required.",
            }
        ), 400

    try:

        room.add_player(
            user_id=user_id,
            display_name=display_name,
        )

    except ValueError as exc:

        return jsonify(
            {
                "ok": False,
                "error": str(exc),
            }
        ), 400

    return jsonify(
        {
            "ok": True,
            "room_id": room.room_id,
            "player_count": room.player_count(),
            "players": list(
                room.players.values()
            ),
        }
    )


# ==========================================================
# START ROOM
# ==========================================================

@real_games_bp.post("/api/room/<room_id>/start")
def start_room(room_id):

    room = GAME_MANAGER.get(room_id)

    if not room:

        return jsonify(
            {
                "ok": False,
                "error": "Room not found.",
            }
        ), 404

    try:

        room.start()

    except ValueError as exc:

        return jsonify(
            {
                "ok": False,
                "error": str(exc),
            }
        ), 400

    return jsonify(
        {
            "ok": True,
            "started": room.started,
            "room_id": room.room_id,
        }
    )


# ==========================================================
# GAME INFORMATION API
# ==========================================================

@real_games_bp.get("/api/game/<game_id>")
def game_information(game_id):

    game = get_game(game_id)

    if not game:

        return jsonify(
            {
                "ok": False,
                "error": "Game not found.",
            }
        ), 404

    return jsonify(
        {
            "ok": True,
            "game": {
                "id": game.game_id,
                "name": game.name,
                "category": game.category,
                "description": game.description,
                "mode": game.mode,
                "max_players": game.max_players,
                "min_players": game.min_players,
                "uses_rooms": game.uses_rooms,
                "icon": game.icon,
                "endpoint": game.endpoint,
            },
        }
    )


# ==========================================================
# CLEANUP
# ==========================================================

@real_games_bp.post("/api/cleanup")
def cleanup_rooms():

    removed = GAME_MANAGER.cleanup()

    return jsonify(
        {
            "ok": True,
            "removed": removed,
            "count": len(removed),
        }
    )
