"""
Melanated AZ Bot
Real Games - Flask Routes

Real Games launcher, multiplayer rooms,
and Dirty Minds multiplayer routes.
"""

from **future** import annotations

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

# ==========================================================

# DIRTY MINDS ENGINE

# ==========================================================

from .dirty_minds import (
create_dirty_minds_state,
finish_game,
next_round,
public_room_state,
reveal_round,
start_game,
submit_answer,
)

logger = logging.getLogger(**name**)

# ==========================================================

# BLUEPRINT

# ==========================================================

real_games_bp = Blueprint(
"real_games",
**name**,
url_prefix="/real-games",
template_folder="templates",
)

# ==========================================================

# DIRTY MINDS GAME ID

# ==========================================================

DIRTY_MINDS_ID = "dirty_minds"

# ==========================================================

# HELPERS

# ==========================================================

def _normalize_game_id(game_id):
"""
Normalize game IDs.

```
Supports:
    dirty_minds
    Dirty_Minds
    rg_dirty_minds
"""

if not game_id:
    return ""

gid = str(game_id).strip().lower()

if gid.startswith("rg_"):
    gid = gid[3:]

return gid
```

def _is_dirty_minds(game_id):
return (
_normalize_game_id(game_id)
== DIRTY_MINDS_ID
)

def _dirty_minds_game():

```
"""
Build a lightweight game object/dictionary for
Dirty Minds without requiring it to be registered
in registry.py.

The normal registry remains untouched.
"""

return {
    "game_id": DIRTY_MINDS_ID,
    "id": DIRTY_MINDS_ID,
    "name": "Dirty Minds",
    "icon": "🎭",
    "category": "Party",
    "description": (
        "A multiplayer guessing game where "
        "the clues sound dirty but the answers are clean."
    ),
    "mode": "multiplayer",
    "multiplayer": True,
    "uses_rooms": True,
    "min_players": 2,
    "max_players": 20,
    "endpoint": "/real-games/play/dirty_minds",
}
```

def _get_game_for_route(game_id):

```
"""
Get a normal registry game or the special
Dirty Minds game.
"""

normalized = _normalize_game_id(game_id)

if normalized == DIRTY_MINDS_ID:
    return _dirty_minds_game()

return get_game(normalized)
```

def _game_value(game, key, default=None):

```
"""
Safely read either a registry dataclass/object
or a dictionary.
"""

if isinstance(game, dict):
    return game.get(key, default)

return getattr(
    game,
    key,
    default,
)
```

def _game_name(game):

```
return _game_value(
    game,
    "name",
    "Real Game",
)
```

def _game_id(game):

```
return _game_value(
    game,
    "game_id",
    "",
)
```

def _game_uses_rooms(game):

```
return bool(
    _game_value(
        game,
        "uses_rooms",
        False,
    )
)
```

def _game_min_players(game):

```
return int(
    _game_value(
        game,
        "min_players",
        2,
    )
)
```

def _game_max_players(game):

```
return int(
    _game_value(
        game,
        "max_players",
        20,
    )
)
```

def _build_dirty_minds_url(
room_id,
player_key,
):

```
return url_for(
    "real_games.play_game",
    game_id=DIRTY_MINDS_ID,
    room=room_id,
    player_key=player_key,
    _external=True,
)
```

# ==========================================================

# REAL GAMES HOME

# ==========================================================

@real_games_bp.get("/")
def real_games_home():

```
grouped_games = get_games_grouped()

return render_template(
    "real_games.html",
    games=all_games(),
    grouped_games=grouped_games,
    categories=CATEGORY_ORDER,
)
```

# ==========================================================

# GAME LAUNCHER

# ==========================================================

@real_games_bp.get("/game/<game_id>")
def game_launcher(game_id):

```
game = _get_game_for_route(
    game_id
)

if not game:

    abort(
        404,
        description="Game not found.",
    )

# ------------------------------------------------------
# Dirty Minds gets its own multiplayer page.
# ------------------------------------------------------

if _is_dirty_minds(game_id):

    room_id = (
        request.args
        .get(
            "room",
            "",
        )
        .strip()
        .upper()
    )

    player_key = (
        request.args
        .get(
            "player_key",
            "",
        )
        .strip()
    )

    if room_id and player_key:

        room = GAME_MANAGER.get(
            room_id
        )

        if not room:

            abort(
                404,
                description="Dirty Minds room not found.",
            )

        if room.game_id != DIRTY_MINDS_ID:

            abort(
                400,
                description="This room is not a Dirty Minds room.",
            )

        player = (
            room.get_player_by_key(
                player_key
            )
        )

        if not player:

            abort(
                403,
                description="You are not a player in this room.",
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

    # No room/player key yet.
    # Show the normal game launcher.
    return render_template(
        "game.html",
        game=game,
        room=None,
        multiplayer=True,
    )

logger.info(
    "Launching Real Game: %s (%s)",
    _game_name(game),
    _game_id(game),
)

return render_template(
    "game.html",
    game=game,
    room=None,
    multiplayer=_game_uses_rooms(game),
)
```

# ==========================================================

# REAL GAME PLAY ENDPOINT

# ==========================================================

@real_games_bp.get("/play/<game_id>")
def play_game(game_id):

```
game = _get_game_for_route(
    game_id
)

if not game:

    abort(
        404,
        description="Game not found.",
    )

# ======================================================
# DIRTY MINDS
# ======================================================

if _is_dirty_minds(game_id):

    room_id = (
        request.args
        .get(
            "room",
            "",
        )
        .strip()
        .upper()
    )

    player_key = (
        request.args
        .get(
            "player_key",
            "",
        )
        .strip()
    )

    if not room_id:

        return (
            "<h2>🎭 Dirty Minds</h2>"
            "<p>No game room was supplied.</p>"
            "<p>Please open Dirty Minds from the "
            "game-room JOIN button.</p>",
            400,
        )

    if not player_key:

        return (
            "<h2>🎭 Dirty Minds</h2>"
            "<p>No player key was supplied.</p>"
            "<p>Please open the game from the "
            "JOIN button.</p>",
            400,
        )

    room = GAME_MANAGER.get(
        room_id
    )

    if not room:

        abort(
            404,
            description="That Dirty Minds room no longer exists.",
        )

    if room.game_id != DIRTY_MINDS_ID:

        abort(
            400,
            description="This room is not a Dirty Minds room.",
        )

    player = (
        room.get_player_by_key(
            player_key
        )
    )

    if not player:

        abort(
            403,
            description="You are not a player in this Dirty Minds room.",
        )

    logger.info(
        "Opening Dirty Minds room %s for %s",
        room.room_id,
        player.get(
            "name",
            "Player",
        ),
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

# ======================================================
# NORMAL GAMES
# ======================================================

logger.info(
    "Starting game: %s (%s)",
    _game_name(game),
    _game_id(game),
)

return render_template(
    "game.html",
    game=game,
    room=None,
    multiplayer=_game_uses_rooms(game),
)
```

# ==========================================================

# CREATE MULTIPLAYER ROOM

#

# This preserves the original:

#

# POST /real-games/create/<game_id>

#

# and adds special Dirty Minds state creation.

# ==========================================================

@real_games_bp.post("/create/<game_id>")
def create_game_room(game_id):

```
game = _get_game_for_route(
    game_id
)

if not game:

    abort(
        404,
        description="Game not found.",
    )

if not _game_uses_rooms(game):

    return redirect(
        url_for(
            "real_games.game_launcher",
            game_id=_game_id(game),
        )
    )

# ------------------------------------------------------
# Dirty Minds must use its real game state.
# ------------------------------------------------------

if _is_dirty_minds(game_id):

    state = create_dirty_minds_state()

else:

    state = {
        "game_id": _game_id(game),
        "turn": None,
        "status": "waiting",
    }

room = GAME_MANAGER.create(
    game_id=_game_id(game),
    game_name=_game_name(game),
    max_players=_game_max_players(game),
    min_players=_game_min_players(game),
    state=state,
)

# ------------------------------------------------------
# IMPORTANT:
#
# A browser-created room does not automatically know
# the Telegram user.
#
# The normal room page remains available for other
# games.
#
# Dirty Minds should normally be entered using the
# player-specific JOIN URL generated by the API below.
# ------------------------------------------------------

if _is_dirty_minds(game_id):

    return redirect(
        url_for(
            "real_games.game_launcher",
            game_id=DIRTY_MINDS_ID,
            room=room.room_id,
        )
    )

return redirect(
    url_for(
        "real_games.game_room",
        game_id=_game_id(game),
        room_id=room.room_id,
    )
)
```

# ==========================================================

# CREATE ROOM API

#

# Used by Telegram/web clients that already know the

# player's user ID and name.

#

# POST:

#

# /real-games/create-room

#

# JSON:

# {

# "game_id": "dirty_minds",

# "user_id": "123",

# "name": "Dexter"

# }

# ==========================================================

@real_games_bp.post("/create-room")
def create_room_api():

```
data = (
    request.get_json(
        silent=True
    )
    or {}
)

game_id = _normalize_game_id(
    data.get(
        "game_id",
        "",
    )
)

user_id = str(
    data.get(
        "user_id",
        "",
    )
).strip()

display_name = str(
    data.get(
        "name",
        data.get(
            "display_name",
            "Player",
        ),
    )
    or "Player"
).strip()

game = _get_game_for_route(
    game_id
)

if not game:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Game not found.",
        }
    ), 404

if not _game_uses_rooms(game):

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "This game does not use multiplayer rooms.",
        }
    ), 400

if not user_id:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "user_id is required.",
        }
    ), 400

# ------------------------------------------------------
# If the player already has a room for this game,
# return it instead of creating another room.
# ------------------------------------------------------

existing = (
    GAME_MANAGER.find_player_room(
        user_id,
        game_id=game_id,
    )
)

if existing:

    existing_player = (
        existing.get_player(
            user_id
        )
    )

    if existing_player:

        player_key = existing_player.get(
            "player_key"
        )

        game_url = (
            _build_dirty_minds_url(
                existing.room_id,
                player_key,
            )
            if _is_dirty_minds(game_id)
            else url_for(
                "real_games.game_room",
                game_id=game_id,
                room_id=existing.room_id,
                _external=True,
            )
        )

        return jsonify(
            {
                "success": True,
                "ok": True,
                "existing": True,
                "room_id": existing.room_id,
                "player_key": player_key,
                "game_url": game_url,
            }
        )

# ------------------------------------------------------
# Correct initial state.
# ------------------------------------------------------

if _is_dirty_minds(game_id):

    state = create_dirty_minds_state()

else:

    state = {
        "game_id": game_id,
        "turn": None,
        "status": "waiting",
    }

room = GAME_MANAGER.create(
    game_id=game_id,
    game_name=_game_name(game),
    max_players=_game_max_players(game),
    min_players=_game_min_players(game),
    state=state,
)

try:

    player = room.add_player(
        user_id=user_id,
        display_name=display_name,
    )

except ValueError as exc:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": str(exc),
        }
    ), 400

player_key = player.get(
    "player_key"
)

if _is_dirty_minds(game_id):

    game_url = _build_dirty_minds_url(
        room.room_id,
        player_key,
    )

else:

    game_url = url_for(
        "real_games.game_room",
        game_id=game_id,
        room_id=room.room_id,
        _external=True,
    )

return jsonify(
    {
        "success": True,
        "ok": True,
        "existing": False,
        "room_id": room.room_id,
        "player_key": player_key,
        "player_count": room.player_count(),
        "game_url": game_url,
    }
)
```

# ==========================================================

# GAME ROOM

# ==========================================================

@real_games_bp.get("/<game_id>/<room_id>")
def game_room(game_id, room_id):

```
game = _get_game_for_route(
    game_id
)

if not game:

    abort(
        404,
        description="Game not found.",
    )

room = GAME_MANAGER.get(
    room_id
)

if not room:

    abort(
        404,
        description="That game room no longer exists.",
    )

if room.game_id != _game_id(game):

    abort(
        400,
        description="This room belongs to a different game.",
    )

# ------------------------------------------------------
# Dirty Minds uses dirty_minds.html.
#
# This route may not have a player key, so we don't
# pretend to know which player is viewing it.
# ------------------------------------------------------

if _is_dirty_minds(game_id):

    return (
        "<h2>🎭 Dirty Minds</h2>"
        "<p>This room requires a player-specific JOIN link.</p>"
        "<p>Please use the JOIN button provided for your player.</p>",
        400,
    )

return render_template(
    "game.html",
    game=game,
    room=room,
    multiplayer=_game_uses_rooms(game),
)
```

# ==========================================================

# ROOM INFORMATION API

# ==========================================================

@real_games_bp.get("/api/room/<room_id>")
def room_information(room_id):

```
room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "ok": False,
            "success": False,
            "error": "Room not found.",
        }
    ), 404

# ------------------------------------------------------
# Dirty Minds must NEVER expose its hidden answer
# through the generic room endpoint.
# ------------------------------------------------------

if room.game_id == DIRTY_MINDS_ID:

    player_key = (
        request.args
        .get(
            "player_key",
            "",
        )
        .strip()
    )

    return jsonify(
        {
            "ok": True,
            "success": True,
            "room": public_room_state(
                room,
                player_key=player_key,
            ),
        }
    )

return jsonify(
    {
        "ok": True,
        "success": True,
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
```

# ==========================================================

# JOIN ROOM FROM WEB

# ==========================================================

@real_games_bp.post("/api/room/<room_id>/join")
def join_room(room_id):

```
room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "ok": False,
            "success": False,
            "error": "Room not found.",
        }
    ), 404

data = (
    request.get_json(
        silent=True
    )
    or {}
)

user_id = str(
    data.get(
        "user_id",
        "",
    )
).strip()

display_name = str(
    data.get(
        "display_name",
        data.get(
            "name",
            "Player",
        ),
    )
    or "Player"
).strip()

if not user_id:

    return jsonify(
        {
            "ok": False,
            "success": False,
            "error": "user_id is required.",
        }
    ), 400

try:

    player = room.add_player(
        user_id=user_id,
        display_name=display_name,
    )

except ValueError as exc:

    return jsonify(
        {
            "ok": False,
            "success": False,
            "error": str(exc),
        }
    ), 400

response = {
    "ok": True,
    "success": True,
    "room_id": room.room_id,
    "player_count": room.player_count(),
    "players": list(
        room.players.values()
    ),
}

# ------------------------------------------------------
# Give Dirty Minds players their private game URL.
# ------------------------------------------------------

if room.game_id == DIRTY_MINDS_ID:

    response["player_key"] = player.get(
        "player_key"
    )

    response["game_url"] = (
        _build_dirty_minds_url(
            room.room_id,
            player.get(
                "player_key"
            ),
        )
    )

return jsonify(response)
```

# ==========================================================

# START NORMAL ROOM

# ==========================================================

@real_games_bp.post("/api/room/<room_id>/start")
def start_room(room_id):

```
room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "ok": False,
            "success": False,
            "error": "Room not found.",
        }
    ), 404

# ------------------------------------------------------
# Dirty Minds MUST use its own start_game() function.
# ------------------------------------------------------

if room.game_id == DIRTY_MINDS_ID:

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    player_key = str(
        data.get(
            "player_key",
            request.args.get(
                "player_key",
                "",
            ),
        )
        or ""
    ).strip()

    player = (
        room.get_player_by_key(
            player_key
        )
    )

    if not player:

        return jsonify(
            {
                "ok": False,
                "success": False,
                "error": "Player is not in this room.",
            }
        ), 403

    if not player.get(
        "host",
        False,
    ):

        return jsonify(
            {
                "ok": False,
                "success": False,
                "error": "Only the host can start Dirty Minds.",
            }
        ), 403

    try:

        state = start_game(
            room
        )

    except ValueError as exc:

        return jsonify(
            {
                "ok": False,
                "success": False,
                "error": str(exc),
            }
        ), 400

    return jsonify(
        {
            "ok": True,
            "success": True,
            "started": True,
            "room_id": room.room_id,
            "state": public_room_state(
                room,
                player_key=player_key,
            ),
        }
    )

# ------------------------------------------------------
# Normal game.
# ------------------------------------------------------

try:

    room.start()

except ValueError as exc:

    return jsonify(
        {
            "ok": False,
            "success": False,
            "error": str(exc),
        }
    ), 400

return jsonify(
    {
        "ok": True,
        "success": True,
        "started": room.started,
        "room_id": room.room_id,
    }
)
```

# ==========================================================

# DIRTY MINDS

# STATE

# ==========================================================

@real_games_bp.get("/api/dirty-minds/state")
def dirty_minds_state():

```
room_id = (
    request.args
    .get(
        "room",
        request.args.get(
            "room_id",
            "",
        ),
    )
    .strip()
    .upper()
)

player_key = (
    request.args
    .get(
        "player_key",
        "",
    )
    .strip()
)

if not room_id:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Room ID is required.",
        }
    ), 400

room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Game room not found.",
        }
    ), 404

if room.game_id != DIRTY_MINDS_ID:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "This is not a Dirty Minds room.",
        }
    ), 400

if player_key:

    player = (
        room.get_player_by_key(
            player_key
        )
    )

    if not player:

        return jsonify(
            {
                "success": False,
                "ok": False,
                "error": "Player is not in this room.",
            }
        ), 403

state = public_room_state(
    room,
    player_key=player_key,
)

return jsonify(
    {
        "success": True,
        "ok": True,
        "state": state,
    }
)
```

# ==========================================================

# DIRTY MINDS

# START

# ==========================================================

@real_games_bp.post("/api/dirty-minds/start")
def dirty_minds_start():

```
data = (
    request.get_json(
        silent=True
    )
    or {}
)

room_id = str(
    data.get(
        "room_id",
        "",
    )
).strip().upper()

player_key = str(
    data.get(
        "player_key",
        "",
    )
).strip()

if not room_id or not player_key:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Room ID and player key are required.",
        }
    ), 400

room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Game room not found.",
        }
    ), 404

if room.game_id != DIRTY_MINDS_ID:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "This is not a Dirty Minds room.",
        }
    ), 400

player = (
    room.get_player_by_key(
        player_key
    )
)

if not player:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Player is not in this room.",
        }
    ), 403

if not player.get(
    "host",
    False,
):

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Only the host can start the game.",
        }
    ), 403

try:

    state = start_game(
        room
    )

except ValueError as exc:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": str(exc),
        }
    ), 400

return jsonify(
    {
        "success": True,
        "ok": True,
        "state": public_room_state(
            room,
            player_key=player_key,
        ),
    }
)
```

# ==========================================================

# DIRTY MINDS

# SUBMIT ANSWER

# ==========================================================

@real_games_bp.post("/api/dirty-minds/answer")
def dirty_minds_answer():

```
data = (
    request.get_json(
        silent=True
    )
    or {}
)

room_id = str(
    data.get(
        "room_id",
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
    or ""
).strip()

if not room_id or not player_key:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Room ID and player key are required.",
        }
    ), 400

room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Game room not found.",
        }
    ), 404

if room.game_id != DIRTY_MINDS_ID:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "This is not a Dirty Minds room.",
        }
    ), 400

player = (
    room.get_player_by_key(
        player_key
    )
)

if not player:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Player is not in this room.",
        }
    ), 403

try:

    result = submit_answer(
        room,
        player_key,
        answer,
    )

except ValueError as exc:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": str(exc),
        }
    ), 400

return jsonify(
    {
        "success": True,
        "ok": True,
        **result,
    }
)
```

# ==========================================================

# DIRTY MINDS

# REVEAL

# ==========================================================

@real_games_bp.post("/api/dirty-minds/reveal")
def dirty_minds_reveal():

```
data = (
    request.get_json(
        silent=True
    )
    or {}
)

room_id = str(
    data.get(
        "room_id",
        "",
    )
).strip().upper()

player_key = str(
    data.get(
        "player_key",
        "",
    )
).strip()

if not room_id or not player_key:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Room ID and player key are required.",
        }
    ), 400

room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Game room not found.",
        }
    ), 404

if room.game_id != DIRTY_MINDS_ID:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "This is not a Dirty Minds room.",
        }
    ), 400

player = (
    room.get_player_by_key(
        player_key
    )
)

if not player:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Player is not in this room.",
        }
    ), 403

if not player.get(
    "host",
    False,
):

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Only the host can reveal the answer.",
        }
    ), 403

try:

    state = reveal_round(
        room
    )

except ValueError as exc:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": str(exc),
        }
    ), 400

return jsonify(
    {
        "success": True,
        "ok": True,
        "state": public_room_state(
            room,
            player_key=player_key,
        ),
    }
)
```

# ==========================================================

# DIRTY MINDS

# NEXT ROUND

# ==========================================================

@real_games_bp.post("/api/dirty-minds/next")
def dirty_minds_next():

```
data = (
    request.get_json(
        silent=True
    )
    or {}
)

room_id = str(
    data.get(
        "room_id",
        "",
    )
).strip().upper()

player_key = str(
    data.get(
        "player_key",
        "",
    )
).strip()

if not room_id or not player_key:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Room ID and player key are required.",
        }
    ), 400

room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Game room not found.",
        }
    ), 404

if room.game_id != DIRTY_MINDS_ID:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "This is not a Dirty Minds room.",
        }
    ), 400

player = (
    room.get_player_by_key(
        player_key
    )
)

if not player:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Player is not in this room.",
        }
    ), 403

if not player.get(
    "host",
    False,
):

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Only the host can advance the round.",
        }
    ), 403

try:

    state = next_round(
        room
    )

except ValueError as exc:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": str(exc),
        }
    ), 400

return jsonify(
    {
        "success": True,
        "ok": True,
        "state": public_room_state(
            room,
            player_key=player_key,
        ),
    }
)
```

# ==========================================================

# DIRTY MINDS

# FINISH GAME

# ==========================================================

@real_games_bp.post("/api/dirty-minds/finish")
def dirty_minds_finish():

```
data = (
    request.get_json(
        silent=True
    )
    or {}
)

room_id = str(
    data.get(
        "room_id",
        "",
    )
).strip().upper()

player_key = str(
    data.get(
        "player_key",
        "",
    )
).strip()

if not room_id or not player_key:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Room ID and player key are required.",
        }
    ), 400

room = GAME_MANAGER.get(
    room_id
)

if not room:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Game room not found.",
        }
    ), 404

if room.game_id != DIRTY_MINDS_ID:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "This is not a Dirty Minds room.",
        }
    ), 400

player = (
    room.get_player_by_key(
        player_key
    )
)

if not player:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Player is not in this room.",
        }
    ), 403

if not player.get(
    "host",
    False,
):

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": "Only the host can end the game.",
        }
    ), 403

try:

    state = finish_game(
        room
    )

except ValueError as exc:

    return jsonify(
        {
            "success": False,
            "ok": False,
            "error": str(exc),
        }
    ), 400

return jsonify(
    {
        "success": True,
        "ok": True,
        "state": public_room_state(
            room,
            player_key=player_key,
        ),
    }
)
```

# ==========================================================

# GAME INFORMATION API

# ==========================================================

@real_games_bp.get("/api/game/<game_id>")
def game_information(game_id):

```
game = _get_game_for_route(
    game_id
)

if not game:

    return jsonify(
        {
            "ok": False,
            "success": False,
            "error": "Game not found.",
        }
    ), 404

return jsonify(
    {
        "ok": True,
        "success": True,
        "game": {
            "id": _game_id(game),
            "name": _game_name(game),
            "category": _game_value(
                game,
                "category",
                "Arcade",
            ),
            "description": _game_value(
                game,
                "description",
                "",
            ),
            "mode": _game_value(
                game,
                "mode",
                "single",
            ),
            "max_players": _game_max_players(
                game
            ),
            "min_players": _game_min_players(
                game
            ),
            "uses_rooms": _game_uses_rooms(
                game
            ),
            "icon": _game_value(
                game,
                "icon",
                "🎮",
            ),
            "endpoint": _game_value(
                game,
                "endpoint",
                None,
            ),
        },
    }
)
```

# ==========================================================

# CLEANUP

# ==========================================================

@real_games_bp.post("/api/cleanup")
def cleanup_rooms():

```
removed = GAME_MANAGER.cleanup()

return jsonify(
    {
        "ok": True,
        "success": True,
        "removed": removed,
        "count": len(removed),
    }
)
```

"""

# ==========================================================

# END OF ROUTES

# ==========================================================

"""
