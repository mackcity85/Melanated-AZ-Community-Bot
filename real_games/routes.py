"""Melanated AZ Bot - Real Games Flask routes."""
from __future__ import annotations
import logging
import time
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for
from .game_manager import GAME_MANAGER
from .registry import CATEGORY_ORDER, all_games, get_game, get_games_grouped
from .dirty_minds import create_dirty_minds_state, finish_game, grade_answer, next_round, public_room_state, reveal_round, start_game, submit_answer

logger = logging.getLogger(__name__)
real_games_bp = Blueprint("real_games", __name__, url_prefix="/real-games", template_folder="templates")
DIRTY_MINDS_ID = "dirty_minds"

def _normalize_game_id(game_id):
    gid = str(game_id or "").strip().lower()
    return gid[3:] if gid.startswith("rg_") else gid

def _is_dirty_minds(game_id): return _normalize_game_id(game_id) == DIRTY_MINDS_ID

def _dirty_minds_game():
    return {"game_id": DIRTY_MINDS_ID, "id": DIRTY_MINDS_ID, "name": "Dirty Minds", "icon": "🎭", "category": "Party", "description": "A multiplayer guessing game where the clues sound dirty but the answers are clean.", "mode": "multiplayer", "multiplayer": True, "uses_rooms": True, "min_players": 2, "max_players": 20, "endpoint": "/real-games/play/dirty_minds"}

def _get_game_for_route(game_id):
    gid = _normalize_game_id(game_id)
    return _dirty_minds_game() if gid == DIRTY_MINDS_ID else get_game(gid)

def _game_value(game, key, default=None): return game.get(key, default) if isinstance(game, dict) else getattr(game, key, default)
def _game_name(game): return _game_value(game, "name", "Real Game")
def _game_id(game): return _game_value(game, "game_id", "")
def _game_uses_rooms(game): return bool(_game_value(game, "uses_rooms", False))
def _game_min_players(game): return int(_game_value(game, "min_players", 2))
def _game_max_players(game): return int(_game_value(game, "max_players", 20))
def _build_dirty_minds_url(room_id, player_key): return url_for("real_games.play_game", game_id=DIRTY_MINDS_ID, room=room_id, player_key=player_key, _external=True)

def _room_and_player(data):
    room_id = str(data.get("room_id", data.get("room", "")) or "").strip().upper()
    player_key = str(data.get("player_key", "") or "").strip()
    return room_id, player_key

@real_games_bp.get("/")
def real_games_home():
    return render_template("real_games.html", games=all_games(), grouped_games=get_games_grouped(), categories=CATEGORY_ORDER)

@real_games_bp.get("/game/<game_id>")
def game_launcher(game_id):
    game = _get_game_for_route(game_id)
    if not game: abort(404, description="Game not found.")
    if _is_dirty_minds(game_id):
        room_id = request.args.get("room", "").strip().upper(); player_key = request.args.get("player_key", "").strip()
        if room_id and player_key:
            room = GAME_MANAGER.get(room_id)
            if not room: abort(404, description="Dirty Minds room not found.")
            player = room.get_player_by_key(player_key)
            if not player: abort(403, description="You are not a player in this room.")
            return render_template("dirty_minds.html", game=game, room_id=room.room_id, player_key=player_key, player_name=player.get("name", "Player"))
    return render_template("game.html", game=game, room=None, multiplayer=True if _is_dirty_minds(game_id) else _game_uses_rooms(game))

@real_games_bp.get("/play/<game_id>")
def play_game(game_id):
    game = _get_game_for_route(game_id)
    if not game: abort(404, description="Game not found.")
    if _is_dirty_minds(game_id):
        room_id = request.args.get("room", "").strip().upper(); player_key = request.args.get("player_key", "").strip()
        if not room_id or not player_key: return ("<h2>🎭 Dirty Minds</h2><p>A player-specific room link is required.</p>", 400)
        room = GAME_MANAGER.get(room_id)
        if not room: abort(404, description="That Dirty Minds room no longer exists.")
        player = room.get_player_by_key(player_key)
        if not player: abort(403, description="You are not a player in this room.")
        return render_template("dirty_minds.html", game=game, room_id=room.room_id, player_key=player_key, player_name=player.get("name", "Player"))
    return render_template("game.html", game=game, room=None, multiplayer=_game_uses_rooms(game))

@real_games_bp.post("/create/<game_id>")
def create_game_room(game_id):
    game = _get_game_for_route(game_id)
    if not game: abort(404, description="Game not found.")
    if not _game_uses_rooms(game): return redirect(url_for("real_games.game_launcher", game_id=_game_id(game)))
    state = create_dirty_minds_state() if _is_dirty_minds(game_id) else {"game_id": _game_id(game), "turn": None, "status": "waiting"}
    room = GAME_MANAGER.create(game_id=_game_id(game), game_name=_game_name(game), max_players=_game_max_players(game), min_players=_game_min_players(game), state=state)
    return redirect(url_for("real_games.game_launcher", game_id=DIRTY_MINDS_ID, room=room.room_id)) if _is_dirty_minds(game_id) else redirect(url_for("real_games.game_room", game_id=_game_id(game), room_id=room.room_id))

@real_games_bp.post("/create-room")
def create_room_api():
    data = request.get_json(silent=True) or {}; game_id = _normalize_game_id(data.get("game_id", "")); user_id = str(data.get("user_id", "") or "").strip(); name = str(data.get("name", data.get("display_name", "Player")) or "Player").strip()
    game = _get_game_for_route(game_id)
    if not game: return jsonify(success=False, ok=False, error="Game not found."), 404
    if not _game_uses_rooms(game): return jsonify(success=False, ok=False, error="This game does not use multiplayer rooms."), 400
    if not user_id: return jsonify(success=False, ok=False, error="user_id is required."), 400
    existing = GAME_MANAGER.find_player_room(user_id, game_id=game_id)
    if existing:
        player = existing.get_player(user_id)
        if player:
            key = player.get("player_key"); game_url = _build_dirty_minds_url(existing.room_id, key) if _is_dirty_minds(game_id) else url_for("real_games.game_room", game_id=game_id, room_id=existing.room_id, _external=True)
            return jsonify(success=True, ok=True, existing=True, room_id=existing.room_id, player_key=key, game_url=game_url)
    state = create_dirty_minds_state() if _is_dirty_minds(game_id) else {"game_id": game_id, "turn": None, "status": "waiting"}
    room = GAME_MANAGER.create(game_id=game_id, game_name=_game_name(game), max_players=_game_max_players(game), min_players=_game_min_players(game), state=state)
    try: player = room.add_player(user_id=user_id, display_name=name)
    except ValueError as exc: return jsonify(success=False, ok=False, error=str(exc)), 400
    key = player.get("player_key"); game_url = _build_dirty_minds_url(room.room_id, key) if _is_dirty_minds(game_id) else url_for("real_games.game_room", game_id=game_id, room_id=room.room_id, _external=True)
    return jsonify(success=True, ok=True, existing=False, room_id=room.room_id, player_key=key, player_count=room.player_count(), game_url=game_url)

@real_games_bp.get("/<game_id>/<room_id>")
def game_room(game_id, room_id):
    game = _get_game_for_route(game_id); room = GAME_MANAGER.get(room_id)
    if not game: abort(404, description="Game not found.")
    if not room: abort(404, description="That game room no longer exists.")
    if room.game_id != _game_id(game): abort(400, description="This room belongs to a different game.")
    if _is_dirty_minds(game_id): return ("<h2>🎭 Dirty Minds</h2><p>This room requires a player-specific JOIN link.</p>", 400)
    return render_template("game.html", game=game, room=room, multiplayer=_game_uses_rooms(game))

@real_games_bp.get("/api/room/<room_id>")
def room_information(room_id):
    room = GAME_MANAGER.get(room_id)
    if not room: return jsonify(ok=False, success=False, error="Room not found."), 404
    if room.game_id == DIRTY_MINDS_ID:
        return jsonify(ok=True, success=True, room=public_room_state(room, request.args.get("player_key", "").strip()))
    return jsonify(ok=True, success=True, room={"room_id":room.room_id,"game_id":room.game_id,"game_name":room.game_name,"players":list(room.players.values()),"player_count":room.player_count(),"max_players":room.max_players,"min_players":room.min_players,"started":room.started,"finished":room.finished,"winner_id":room.winner_id,"state":room.state})

@real_games_bp.post("/api/room/<room_id>/join")
def join_room(room_id):
    room=GAME_MANAGER.get(room_id)
    if not room: return jsonify(ok=False,success=False,error="Room not found."),404
    data=request.get_json(silent=True) or {}; user_id=str(data.get("user_id","") or "").strip(); name=str(data.get("display_name",data.get("name","Player")) or "Player").strip()
    if not user_id: return jsonify(ok=False,success=False,error="user_id is required."),400
    try: player=room.add_player(user_id=user_id,display_name=name)
    except ValueError as exc: return jsonify(ok=False,success=False,error=str(exc)),400
    out={"ok":True,"success":True,"room_id":room.room_id,"player_count":room.player_count(),"players":list(room.players.values())}
    if room.game_id==DIRTY_MINDS_ID:
        out["player_key"]=player.get("player_key"); out["game_url"]=_build_dirty_minds_url(room.room_id,player.get("player_key"))
    return jsonify(out)

@real_games_bp.post("/api/room/<room_id>/start")
def start_room(room_id):
    room=GAME_MANAGER.get(room_id)
    if not room: return jsonify(ok=False,success=False,error="Room not found."),404
    if room.game_id==DIRTY_MINDS_ID:
        data=request.get_json(silent=True) or {}; key=str(data.get("player_key",request.args.get("player_key","")) or "").strip(); player=room.get_player_by_key(key)
        if not player: return jsonify(ok=False,success=False,error="Player is not in this room."),403
        if not player.get("host",False): return jsonify(ok=False,success=False,error="Only the host can start Dirty Minds."),403
        try: start_game(room)
        except ValueError as exc: return jsonify(ok=False,success=False,error=str(exc)),400
        return jsonify(ok=True,success=True,started=True,room_id=room.room_id,state=public_room_state(room,key))
    try: room.start()
    except ValueError as exc: return jsonify(ok=False,success=False,error=str(exc)),400
    return jsonify(ok=True,success=True,started=room.started,room_id=room.room_id)

def _dirty_request():
    data=request.get_json(silent=True) or {}; room_id,key=_room_and_player(data)
    if not room_id or not key: return None,None,None,(jsonify(success=False,ok=False,error="Room ID and player key are required."),400)
    room=GAME_MANAGER.get(room_id)
    if not room: return None,None,None,(jsonify(success=False,ok=False,error="Game room not found."),404)
    if room.game_id!=DIRTY_MINDS_ID: return None,None,None,(jsonify(success=False,ok=False,error="This is not a Dirty Minds room."),400)
    player=room.get_player_by_key(key)
    if not player: return None,None,None,(jsonify(success=False,ok=False,error="Player is not in this room."),403)
    return data,room,key,None

@real_games_bp.get("/api/dirty-minds/state")
def dirty_minds_state():
    room_id=str(request.args.get("room",request.args.get("room_id","")) or "").strip().upper(); key=request.args.get("player_key","").strip()
    if not room_id:return jsonify(success=False,ok=False,error="Room ID is required."),400
    room=GAME_MANAGER.get(room_id)
    if not room:return jsonify(success=False,ok=False,error="Game room not found."),404
    if key and not room.get_player_by_key(key):return jsonify(success=False,ok=False,error="Player is not in this room."),403
    return jsonify(success=True,ok=True,state=public_room_state(room,key))

@real_games_bp.post("/api/dirty-minds/start")
def dirty_minds_start():
    data,room,key,error=_dirty_request()
    if error:return error
    player=room.get_player_by_key(key)
    if not player.get("host",False):return jsonify(success=False,ok=False,error="Only the host can start the game."),403
    try:start_game(room)
    except ValueError as exc:return jsonify(success=False,ok=False,error=str(exc)),400
    return jsonify(success=True,ok=True,state=public_room_state(room,key))

@real_games_bp.post("/api/dirty-minds/answer")
def dirty_minds_answer():
    data,room,key,error=_dirty_request()
    if error:return error
    try:result=submit_answer(room,key,str(data.get("answer","") or "").strip())
    except ValueError as exc:return jsonify(success=False,ok=False,error=str(exc)),400
    return jsonify(success=True,ok=True,**result)

@real_games_bp.post("/api/dirty-minds/reveal")
def dirty_minds_reveal():
    data,room,key,error=_dirty_request()
    if error:return error
    if not room.get_player_by_key(key).get("host",False):return jsonify(success=False,ok=False,error="Only the host can reveal the answer."),403
    try:reveal_round(room)
    except ValueError as exc:return jsonify(success=False,ok=False,error=str(exc)),400
    return jsonify(success=True,ok=True,state=public_room_state(room,key))

@real_games_bp.post("/api/dirty-minds/grade")
def dirty_minds_grade():
    data,room,key,error=_dirty_request()
    if error:return error
    target=str(data.get("target_player_key","") or "").strip(); grade=str(data.get("grade","") or "").strip().lower()
    try:result=grade_answer(room,key,target,grade)
    except ValueError as exc:return jsonify(success=False,ok=False,error=str(exc)),400
    return jsonify(success=True,ok=True,**result)

@real_games_bp.post("/api/dirty-minds/next")
def dirty_minds_next():
    data,room,key,error=_dirty_request()
    if error:return error
    if not room.get_player_by_key(key).get("host",False):return jsonify(success=False,ok=False,error="Only the host can advance the round."),403
    try:next_round(room)
    except ValueError as exc:return jsonify(success=False,ok=False,error=str(exc)),400
    return jsonify(success=True,ok=True,state=public_room_state(room,key))

@real_games_bp.post("/api/dirty-minds/finish")
def dirty_minds_finish():
    data,room,key,error=_dirty_request()
    if error:return error
    if not room.get_player_by_key(key).get("host",False):return jsonify(success=False,ok=False,error="Only the host can end the game."),403
    try:finish_game(room)
    except ValueError as exc:return jsonify(success=False,ok=False,error=str(exc)),400
    return jsonify(success=True,ok=True,state=public_room_state(room,key))


# ==========================================================
# DIRTY MINDS WEBRTC VOICE SIGNALING
# ==========================================================

@real_games_bp.get("/api/dirty-minds/voice/peers")
def dirty_minds_voice_peers():
    """Return the other players in the room for WebRTC peer discovery."""
    room_id = str(request.args.get("room", request.args.get("room_id", "")) or "").strip().upper()
    key = str(request.args.get("player_key", "") or "").strip()
    if not room_id or not key:
        return jsonify(success=False, ok=False, error="Room ID and player key are required."), 400
    room = GAME_MANAGER.get(room_id)
    if not room:
        return jsonify(success=False, ok=False, error="Game room not found."), 404
    if room.game_id != DIRTY_MINDS_ID:
        return jsonify(success=False, ok=False, error="This is not a Dirty Minds room."), 400
    if not room.get_player_by_key(key):
        return jsonify(success=False, ok=False, error="Player is not in this room."), 403
    peers = []
    for peer_key, player in room.players.items():
        if peer_key == key:
            continue
        peers.append({
            "player_key": peer_key,
            "name": player.get("name", "Player"),
        })
    return jsonify(success=True, ok=True, peers=peers)


@real_games_bp.post("/api/dirty-minds/voice/signal")
def dirty_minds_voice_signal():
    """Store one WebRTC signaling message for its target player."""
    data, room, key, error = _dirty_request()
    if error:
        return error
    target = str(data.get("target_player_key", "") or "").strip()
    signal_type = str(data.get("type", "") or "").strip().lower()
    payload = data.get("data")
    if not target or target == key:
        return jsonify(success=False, ok=False, error="A different target player is required."), 400
    if not room.get_player_by_key(target):
        return jsonify(success=False, ok=False, error="Target player is not in this room."), 404
    if signal_type not in {"offer", "answer", "candidate", "leave"}:
        return jsonify(success=False, ok=False, error="Invalid signaling message type."), 400

    signals = room.state.setdefault("voice_signals", {})
    signals.setdefault(target, []).append({
        "from_player_key": key,
        "type": signal_type,
        "data": payload,
        "created_at": time.time(),
    })
    # Keep the queue bounded in case a browser disappears without consuming it.
    signals[target] = signals[target][-50:]
    room.touch()
    return jsonify(success=True, ok=True, queued=True)


@real_games_bp.get("/api/dirty-minds/voice/signals")
def dirty_minds_voice_signals():
    """Return and consume pending WebRTC signaling messages for this player."""
    room_id = str(request.args.get("room", request.args.get("room_id", "")) or "").strip().upper()
    key = str(request.args.get("player_key", "") or "").strip()
    if not room_id or not key:
        return jsonify(success=False, ok=False, error="Room ID and player key are required."), 400
    room = GAME_MANAGER.get(room_id)
    if not room:
        return jsonify(success=False, ok=False, error="Game room not found."), 404
    if room.game_id != DIRTY_MINDS_ID:
        return jsonify(success=False, ok=False, error="This is not a Dirty Minds room."), 400
    if not room.get_player_by_key(key):
        return jsonify(success=False, ok=False, error="Player is not in this room."), 403
    signals = room.state.setdefault("voice_signals", {})
    messages = signals.pop(key, [])
    # Drop anything older than 5 minutes.
    cutoff = time.time() - 300
    messages = [m for m in messages if float(m.get("created_at", 0)) >= cutoff]
    if messages:
        room.touch()
    return jsonify(success=True, ok=True, signals=messages)


@real_games_bp.post("/api/dirty-minds/voice/leave")
def dirty_minds_voice_leave():
    """Tell a peer that this browser closed its WebRTC connection."""
    data, room, key, error = _dirty_request()
    if error:
        return error
    target = str(data.get("target_player_key", "") or "").strip()
    if target and room.get_player_by_key(target):
        signals = room.state.setdefault("voice_signals", {})
        signals.setdefault(target, []).append({
            "from_player_key": key,
            "type": "leave",
            "data": None,
            "created_at": time.time(),
        })
        signals[target] = signals[target][-50:]
        room.touch()
    return jsonify(success=True, ok=True)

@real_games_bp.get("/api/game/<game_id>")
def game_information(game_id):
    game=_get_game_for_route(game_id)
    if not game:return jsonify(ok=False,success=False,error="Game not found."),404
    return jsonify(ok=True,success=True,game={"id":_game_id(game),"name":_game_name(game),"category":_game_value(game,"category","Arcade"),"description":_game_value(game,"description",""),"mode":_game_value(game,"mode","single"),"max_players":_game_max_players(game),"min_players":_game_min_players(game),"uses_rooms":_game_uses_rooms(game),"icon":_game_value(game,"icon","🎮"),"endpoint":_game_value(game,"endpoint",None)})

@real_games_bp.post("/api/cleanup")
def cleanup_rooms():
    removed=GAME_MANAGER.cleanup(); return jsonify(ok=True,success=True,removed=removed,count=len(removed))
