# ==========================================================
# Melanated AZ Real Games
# real_games.py
#
# Main Flask blueprint for Real Games.
#
# Uses registry.py as the SINGLE source of truth for the
# 27 launcher games.
#
# Dirty Minds remains supported separately as a multiplayer
# Telegram game.
# ==========================================================

from __future__ import annotations

import os

from dataclasses import asdict

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from .game_manager import GAME_MANAGER

from .dirty_minds import (
    create_dirty_minds_state,
    finish_game,
    next_round,
    public_room_state,
    reveal_round,
    start_game,
    submit_answer,
)

from .registry import (
    CATEGORY_ORDER,
    all_games,
    get_game as registry_get_game,
)


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
#
# registry.py contains the 27 public games.
#
# Dirty Minds is intentionally kept separate because it is
# a multiplayer Telegram game and is not part of the four
# launcher categories.
# ==========================================================

def _game_dict(game):
    """
    Convert a GameDefinition dataclass into the dictionary
    format expected by the existing templates and APIs.
    """

    if game is None:
        return None

    return asdict(game)


# Public launcher games
GAMES = [
    _game_dict(game)
    for game in all_games()
]


# ==========================================================
# DIRTY MINDS
#
# Keep Dirty Minds available to the existing Telegram
# deep-link / multiplayer system without displaying it in
# the four-section launcher.
# ==========================================================

DIRTY_MINDS_GAME = {
    "game_id": "dirty_minds",
    "name": "Dirty Minds",
    "icon": "🎭",
    "category": "Party",
    "description": (
        "A multiplayer guessing game where the clues "
        "sound dirty but the answers are clean."
    ),
    "multiplayer": True,
    "max_players": 20,
    "min_players": 2,
    "mode": "multiplayer",
    "uses_rooms": True,
}


# ==========================================================
# GAME LOOKUP
# ==========================================================

def get_game(game_id: str):
    """
    Find a Real Game by ID.

    Supports:
        snake
        pong
        tetris
        flappy
        space_invaders
        asteroids
        pac_man
        2048
        memory_match
        monopoly
        chess
        checkers
        connect_four
        tic_tac_toe
        battleship
        yahtzee
        ludo
        basketball
        football
        soccer
        bowling
        cricket
        alien_blaster
        space_fighter
        target_shooter
        zombie_blaster
        dirty_minds
    """

    if not game_id:
        return None

    game_id = str(game_id).strip().lower()

    # Support old/deep-link style rg_ IDs.
    if game_id.startswith("rg_"):
        game_id = game_id[3:]

    # Dirty Minds is intentionally outside the public
    # four-category registry.
    if game_id == "dirty_minds":
        return DIRTY_MINDS_GAME

    game = registry_get_game(game_id)

    if not game:
        return None

    return _game_dict(game)


# ==========================================================
# VALID GAME IDS
# ==========================================================

VALID_GAME_IDS = {
    game["game_id"]
    for game in GAMES
}

VALID_GAME_IDS.add("dirty_minds")


# ==========================================================
# LAUNCHER
# ==========================================================

@real_games_bp.route("/")
def real_games_home():
    """
    Main Real Games launcher.

    Only the four configured categories are supplied:
        Arcade
        Board Games
        Sports
        Shooting
    """

    return render_template(
        "real_games.html",
        games=GAMES,
        categories=CATEGORY_ORDER,
    )


# ==========================================================
# PLAY GAME
# ==========================================================

@real_games_bp.route("/play/<game_id>")
def play_game(game_id):
    """
    Open a game.

    Examples:

        /real-games/play/snake
        /real-games/play/tetris
        /real-games/play/chess
        /real-games/play/basketball

    Dirty Minds:

        /real-games/play/dirty_minds
            ?room=ABC123
            &player_key=...
    """

    normalized_id = str(
        game_id or ""
    ).strip().lower()

    if normalized_id.startswith("rg_"):
        normalized_id = normalized_id[3:]

    game = get_game(normalized_id)

    if not game:
        return (
            render_template(
                "real_games.html",
                games=GAMES,
                categories=CATEGORY_ORDER,
            ),
            404,
        )

    # ------------------------------------------------------
    # Dirty Minds requires a room and player key.
    # ------------------------------------------------------

    if normalized_id == "dirty_minds":

        room_id = request.args.get(
            "room",
            "",
        ).strip().upper()

        player_key = request.args.get(
            "player_key",
            "",
        ).strip()

        if not room_id or not player_key:
            return (
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta name="viewport"
                          content="width=device-width,
                                   initial-scale=1">
                    <title>Dirty Minds</title>
                </head>
                <body style="
                    background:#080808;
                    color:#fff;
                    font-family:Arial;
                    text-align:center;
                    padding:40px 20px;
                ">
                    <h2>🎭 Dirty Minds</h2>
                    <p>
                        This game must be opened from
                        the Telegram JOIN button.
                    </p>
                </body>
                </html>
                """,
                400,
            )

        room = GAME_MANAGER.get(room_id)

        if not room:
            return (
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta name="viewport"
                          content="width=device-width,
                                   initial-scale=1">
                    <title>Game Room Not Found</title>
                </head>
                <body style="
                    background:#080808;
                    color:#fff;
                    font-family:Arial;
                    text-align:center;
                    padding:40px 20px;
                ">
                    <h2>🎭 Game Room Not Found</h2>
                    <p>
                        This Dirty Minds room has expired
                        or no longer exists.
                    </p>
                </body>
                </html>
                """,
                404,
            )

        player = room.get_player_by_key(
            player_key
        )

        if not player:
            return (
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta name="viewport"
                          content="width=device-width,
                                   initial-scale=1">
                    <title>Player Not Found</title>
                </head>
                <body style="
                    background:#080808;
                    color:#fff;
                    font-family:Arial;
                    text-align:center;
                    padding:40px 20px;
                ">
                    <h2>🎭 Player Not Found</h2>
                    <p>
                        Your game session is invalid.
                        Please use the Telegram JOIN
                        button again.
                    </p>
                </body>
                </html>
                """,
                403,
            )

        return render_template(
            "dirty_minds.html",
            game=game,
            room_id=room.room_id,
            player_key=player_key,
            player_name=player.get(
                "name",
                "Player",
            ),
        )

    # ------------------------------------------------------
    # All public single-player games.
    # ------------------------------------------------------

    return render_template(
        "game.html",
        game=game,
    )


# ==========================================================
# CREATE ROOM
# ==========================================================

@real_games_bp.route(
    "/create-room",
    methods=["POST"],
)
def create_room():
    """
    Create a multiplayer room.

    Dirty Minds currently uses this endpoint.

    Expected JSON:

        {
            "game_id": "dirty_minds",
            "user_id": "123",
            "name": "Dexter"
        }
    """

    data = request.get_json(
        silent=True
    ) or {}

    game_id = str(
        data.get(
            "game_id",
            "",
        )
    ).strip().lower()

    user_id = str(
        data.get(
            "user_id",
            "",
        )
    ).strip()

    display_name = str(
        data.get(
            "name",
            "Player",
        )
    ).strip()

    game = get_game(game_id)

    if not game:
        return jsonify(
            {
                "success": False,
                "error": "Game not found.",
            }
        ), 404

    if not game.get(
        "multiplayer",
        False,
    ):
        return jsonify(
            {
                "success": False,
                "error": (
                    "This game does not use "
                    "multiplayer rooms."
                ),
            }
        ), 400

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "user_id is required.",
            }
        ), 400

    # Prevent duplicate rooms for the same player.
    existing = GAME_MANAGER.find_player_room(
        user_id,
        game_id=game_id,
    )

    if existing:

        player = existing.get_player(
            user_id
        )

        return jsonify(
            {
                "success": True,
                "existing": True,
                "room_id": existing.room_id,
                "player_key": (
                    player.get("player_key")
                    if player
                    else None
                ),
                "game_url": _build_game_url(
                    existing.room_id,
                    (
                        player.get("player_key")
                        if player
                        else ""
                    ),
                ),
            }
        )

    room = GAME_MANAGER.create(
        game_id=game_id,
        game_name=game["name"],
        max_players=int(
            game.get(
                "max_players",
                20,
            )
        ),
        min_players=int(
            game.get(
                "min_players",
                2,
            )
        ),
        state=(
            create_dirty_minds_state()
            if game_id == "dirty_minds"
            else {}
        ),
    )

    player = room.add_player(
        user_id=user_id,
        display_name=display_name,
    )

    return jsonify(
        {
            "success": True,
            "existing": False,
            "room_id": room.room_id,
            "player_key": player[
                "player_key"
            ],
            "game_url": _build_game_url(
                room.room_id,
                player["player_key"],
            ),
        }
    )


# ==========================================================
# ROOM INFORMATION
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>",
    methods=["GET"],
)
def room_info(room_id):
    """
    Return public information about a room.
    """

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

    player_key = request.args.get(
        "player_key",
        "",
    ).strip()

    if room.game_id == "dirty_minds":

        return jsonify(
            {
                "success": True,
                "room": public_room_state(
                    room,
                    player_key=player_key,
                ),
            }
        )

    return jsonify(
        {
            "success": True,
            "room": room.public_data(),
        }
    )


# ==========================================================
# DIRTY MINDS HELPER
# ==========================================================

def _get_dirty_minds_player():
    """
    Validate the room and player key supplied
    in a Dirty Minds API request.

    Returns:
        (room, player)
    """

    room_id = request.args.get(
        "room",
        "",
    ).strip().upper()

    player_key = request.args.get(
        "player_key",
        "",
    ).strip()

    # Also accept JSON values.
    if not room_id or not player_key:

        data = request.get_json(
            silent=True
        ) or {}

        room_id = (
            room_id
            or str(
                data.get(
                    "room_id",
                    "",
                )
            ).strip().upper()
        )

        player_key = (
            player_key
            or str(
                data.get(
                    "player_key",
                    "",
                )
            ).strip()
        )

    if not room_id:
        raise ValueError(
            "Room ID is required."
        )

    if not player_key:
        raise ValueError(
            "Player key is required."
        )

    room = GAME_MANAGER.get(
        room_id
    )

    if not room:
        raise ValueError(
            "Game room not found."
        )

    if room.game_id != "dirty_minds":
        raise ValueError(
            "This is not a Dirty Minds room."
        )

    player = room.get_player_by_key(
        player_key
    )

    if not player:
        raise ValueError(
            "Player is not in this room."
        )

    return room, player


# ==========================================================
# DIRTY MINDS STATE
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/state",
    methods=["GET"],
)
def dirty_minds_state():

    try:

        room, player = (
            _get_dirty_minds_player()
        )

        player_key = player[
            "player_key"
        ]

        return jsonify(
            {
                "success": True,
                "state": public_room_state(
                    room,
                    player_key=player_key,
                ),
            }
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400


# ==========================================================
# DIRTY MINDS START
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/start",
    methods=["POST"],
)
def dirty_minds_start():

    try:

        room, player = (
            _get_dirty_minds_player()
        )

        if not room.is_host_key(
            player["player_key"]
        ):
            raise ValueError(
                "Only the host can start the game."
            )

        state = start_game(
            room
        )

        return jsonify(
            {
                "success": True,
                "state": state,
            }
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400


# ==========================================================
# DIRTY MINDS ANSWER
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/answer",
    methods=["POST"],
)
def dirty_minds_answer():

    try:

        room, player = (
            _get_dirty_minds_player()
        )

        data = request.get_json(
            silent=True
        ) or {}

        answer = str(
            data.get(
                "answer",
                "",
            )
        ).strip()

        result = submit_answer(
            room=room,
            player_key=player[
                "player_key"
            ],
            answer=answer,
        )

        return jsonify(
            result
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400


# ==========================================================
# DIRTY MINDS REVEAL
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/reveal",
    methods=["POST"],
)
def dirty_minds_reveal():

    try:

        room, player = (
            _get_dirty_minds_player()
        )

        if not room.is_host_key(
            player["player_key"]
        ):
            raise ValueError(
                "Only the host can reveal the answer."
            )

        state = reveal_round(
            room
        )

        return jsonify(
            {
                "success": True,
                "state": state,
            }
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400


# ==========================================================
# DIRTY MINDS NEXT ROUND
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/next",
    methods=["POST"],
)
def dirty_minds_next():

    try:

        room, player = (
            _get_dirty_minds_player()
        )

        if not room.is_host_key(
            player["player_key"]
        ):
            raise ValueError(
                "Only the host can advance the round."
            )

        state = next_round(
            room
        )

        return jsonify(
            {
                "success": True,
                "state": state,
            }
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400


# ==========================================================
# DIRTY MINDS FINISH
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/finish",
    methods=["POST"],
)
def dirty_minds_finish():

    try:

        room, player = (
            _get_dirty_minds_player()
        )

        if not room.is_host_key(
            player["player_key"]
        ):
            raise ValueError(
                "Only the host can finish the game."
            )

        state = finish_game(
            room
        )

        return jsonify(
            {
                "success": True,
                "state": state,
            }
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400


# ==========================================================
# LIVEKIT SETTINGS
# ==========================================================

def _get_livekit_settings():

    url = os.getenv(
        "LIVEKIT_URL",
        "",
    ).strip()

    api_key = os.getenv(
        "LIVEKIT_API_KEY",
        "",
    ).strip()

    api_secret = os.getenv(
        "LIVEKIT_API_SECRET",
        "",
    ).strip()

    return (
        url,
        api_key,
        api_secret,
    )


# ==========================================================
# LIVEKIT TOKEN
# ==========================================================

@real_games_bp.route(
    "/api/dirty-minds/livekit-token",
    methods=["GET", "POST"],
)
def dirty_minds_livekit_token():

    try:

        room, player = (
            _get_dirty_minds_player()
        )

        (
            livekit_url,
            api_key,
            api_secret,
        ) = _get_livekit_settings()

        if not livekit_url:
            raise ValueError(
                "LIVEKIT_URL is not configured."
            )

        if not api_key:
            raise ValueError(
                "LIVEKIT_API_KEY is not configured."
            )

        if not api_secret:
            raise ValueError(
                "LIVEKIT_API_SECRET is not configured."
            )

        # Import only when needed.
        from livekit import api

        livekit_room_name = (
            f"dirty-minds-{room.room_id}"
        )

        player_identity = str(
            player["player_key"]
        )

        player_name = str(
            player.get(
                "name",
                "Player",
            )
        )

        token = (
            api.AccessToken(
                api_key,
                api_secret,
            )
            .with_identity(
                player_identity
            )
            .with_name(
                player_name
            )
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=livekit_room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .to_jwt()
        )

        return jsonify(
            {
                "success": True,
                "url": livekit_url,
                "token": token,
                "room": livekit_room_name,
            }
        )

    except ValueError as exc:

        return jsonify(
            {
                "success": False,
                "error": str(exc),
            }
        ), 400

    except Exception:

        return jsonify(
            {
                "success": False,
                "error": (
                    "Unable to create the LiveKit "
                    "connection token."
                ),
            }
        ), 500


# ==========================================================
# GAME URL
# ==========================================================

def _build_game_url(
    room_id: str,
    player_key: str,
) -> str:
    """
    Build the browser URL for a multiplayer player.
    """

    base_url = os.getenv(
        "PUBLIC_BASE_URL",
        "",
    ).strip().rstrip("/")

    if not base_url:
        base_url = (
            "https://melanatedaz.onrender.com"
        )

    return (
        f"{base_url}"
        f"/real-games/play/dirty_minds"
        f"?room={room_id}"
        f"&player_key={player_key}"
    )


# ==========================================================
# STATUS
# ==========================================================

@real_games_bp.route(
    "/api/status",
    methods=["GET"],
)
def real_games_status():

    GAME_MANAGER.cleanup()

    return jsonify(
        {
            "success": True,
            "service": "Melanated AZ Real Games",

            # 27 public games
            "games": len(GAMES),

            "game_ids": [
                game["game_id"]
                for game in GAMES
            ],

            "categories": CATEGORY_ORDER,

            "active_rooms": (
                GAME_MANAGER.count()
            ),

            "dirty_minds_rooms": (
                GAME_MANAGER.count(
                    "dirty_minds"
                )
            ),
        }
    )
