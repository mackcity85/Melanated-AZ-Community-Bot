from __future__ import annotations
import os
from dataclasses import asdict
from flask import Blueprint, jsonify, render_template, request
from .game_manager import GAME_MANAGER
from .dirty_minds import create_dirty_minds_state, finish_game, next_round, public_room_state, reveal_round, start_game, submit_answer
from .registry import CATEGORY_ORDER, all_games, get_game as registry_get_game

real_games_bp = Blueprint("real_games", __name__, url_prefix="/real-games", template_folder="templates")

def _game_dict(game): return asdict(game)

GAMES = [_game_dict(g) for g in all_games()]
DIRTY_MINDS_GAME = {"game_id":"dirty_minds","name":"Dirty Minds","icon":"🎭","category":"Party","description":"A multiplayer guessing game where the clues sound dirty but the answers are clean.","multiplayer":True,"max_players":20,"min_players":2,"uses_rooms":True}

def get_game(game_id):
    if not game_id: return None
    gid = str(game_id).strip().lower()
    if gid.startswith("rg_"): gid = gid[3:]
    if gid == "dirty_minds": return DIRTY_MINDS_GAME
    game = registry_get_game(gid)
    return _game_dict(game) if game else None

@real_games_bp.route("/")
def real_games_home():
    return render_template("real_games.html", games=GAMES, categories=CATEGORY_ORDER)

@real_games_bp.route("/play/<game_id>")
def play_game(game_id):
    game = get_game(game_id)
    if not game:
        return render_template("real_games.html", games=GAMES, categories=CATEGORY_ORDER), 404
    if game_id.lower() == "dirty_minds":
        room_id=request.args.get("room","").strip().upper(); player_key=request.args.get("player_key","").strip()
        if not room_id or not player_key: return "<h2>Dirty Minds</h2><p>This game must be opened from the Telegram JOIN button.</p>",400
        room=GAME_MANAGER.get(room_id)
        if not room: return "<h2>Game Room Not Found</h2>",404
        player=room.get_player_by_key(player_key)
        if not player: return "<h2>Player Not Found</h2>",403
        return render_template("dirty_minds.html",game=game,room_id=room.room_id,player_key=player_key,player_name=player.get("name","Player"))
    return render_template("game.html", game=game)

@real_games_bp.route("/create-room",methods=["POST"])
def create_room():
    data=request.get_json(silent=True) or {}; game_id=str(data.get("game_id","")).strip().lower(); user_id=str(data.get("user_id","")).strip(); name=str(data.get("name","Player")).strip()
    game=get_game(game_id)
    if not game: return jsonify(success=False,error="Game not found."),404
    if not game.get("multiplayer",False): return jsonify(success=False,error="This game does not use multiplayer rooms."),400
    if not user_id: return jsonify(success=False,error="user_id is required."),400
    existing=GAME_MANAGER.find_player_room(user_id,game_id=game_id)
    if existing:
        p=existing.get_player(user_id)
        return jsonify(success=True,existing=True,room_id=existing.room_id,player_key=p.get("player_key") if p else None,game_url=_build_game_url(existing.room_id,p.get("player_key") if p else ""))
    room=GAME_MANAGER.create(game_id=game_id,game_name=game["name"],max_players=int(game.get("max_players",20)),min_players=int(game.get("min_players",2)),state=create_dirty_minds_state() if game_id=="dirty_minds" else {})
    player=room.add_player(user_id=user_id,display_name=name)
    return jsonify(success=True,existing=False,room_id=room.room_id,player_key=player["player_key"],game_url=_build_game_url(room.room_id,player["player_key"]))

@real_games_bp.route("/room/<room_id>")
def room_info(room_id):
    room=GAME_MANAGER.get(room_id)
    if not room: return jsonify(success=False,error="Room not found."),404
    key=request.args.get("player_key","").strip()
    return jsonify(success=True,room=public_room_state(room,player_key=key) if room.game_id=="dirty_minds" else room.public_data())

def _get_dirty_minds_player():
    room_id=request.args.get("room","").strip().upper(); key=request.args.get("player_key","").strip(); data=request.get_json(silent=True) or {}
    room_id=room_id or str(data.get("room_id","")).strip().upper(); key=key or str(data.get("player_key","")).strip()
    if not room_id or not key: raise ValueError("Room ID and player key are required.")
    room=GAME_MANAGER.get(room_id)
    if not room or room.game_id!="dirty_minds": raise ValueError("Game room not found.")
    player=room.get_player_by_key(key)
    if not player: raise ValueError("Player is not in this room.")
    return room,player

def _dm_call(fn, *args, host=False, **kwargs):
    try:
        room,player=_get_dirty_minds_player()
        if host and not room.is_host_key(player["player_key"]): raise ValueError("Only the host can perform this action.")
        result=fn(*args,**kwargs)
        return jsonify(success=True,state=result) if not isinstance(result,dict) or "success" not in result else jsonify(result)
    except ValueError as e: return jsonify(success=False,error=str(e)),400

@real_games_bp.route("/api/dirty-minds/state")
def dirty_minds_state():
    try:
        room,p=_get_dirty_minds_player(); return jsonify(success=True,state=public_room_state(room,player_key=p["player_key"]))
    except ValueError as e: return jsonify(success=False,error=str(e)),400

@real_games_bp.route("/api/dirty-minds/start",methods=["POST"])
def dirty_minds_start():
    try:
        room,p=_get_dirty_minds_player()
        if not room.is_host_key(p["player_key"]): raise ValueError("Only the host can start the game.")
        return jsonify(success=True,state=start_game(room))
    except ValueError as e: return jsonify(success=False,error=str(e)),400

@real_games_bp.route("/api/dirty-minds/answer",methods=["POST"])
def dirty_minds_answer():
    try:
        room,p=_get_dirty_minds_player(); data=request.get_json(silent=True) or {}; answer=str(data.get("answer","")).strip()
        return jsonify(submit_answer(room=room,player_key=p["player_key"],answer=answer))
    except ValueError as e: return jsonify(success=False,error=str(e)),400

@real_games_bp.route("/api/dirty-minds/reveal",methods=["POST"])
def dirty_minds_reveal():
    try:
        room,p=_get_dirty_minds_player()
        if not room.is_host_key(p["player_key"]): raise ValueError("Only the host can reveal the answer.")
        return jsonify(success=True,state=reveal_round(room))
    except ValueError as e: return jsonify(success=False,error=str(e)),400

@real_games_bp.route("/api/dirty-minds/next",methods=["POST"])
def dirty_minds_next():
    try:
        room,p=_get_dirty_minds_player()
        if not room.is_host_key(p["player_key"]): raise ValueError("Only the host can advance the round.")
        return jsonify(success=True,state=next_round(room))
    except ValueError as e: return jsonify(success=False,error=str(e)),400

@real_games_bp.route("/api/dirty-minds/finish",methods=["POST"])
def dirty_minds_finish():
    try:
        room,p=_get_dirty_minds_player()
        if not room.is_host_key(p["player_key"]): raise ValueError("Only the host can finish the game.")
        return jsonify(success=True,state=finish_game(room))
    except ValueError as e: return jsonify(success=False,error=str(e)),400

def _get_livekit_settings(): return tuple(os.getenv(k,"").strip() for k in ("LIVEKIT_URL","LIVEKIT_API_KEY","LIVEKIT_API_SECRET"))

@real_games_bp.route("/api/dirty-minds/livekit-token",methods=["GET","POST"])
def dirty_minds_livekit_token():
    try:
        room,p=_get_dirty_minds_player(); url,key,secret=_get_livekit_settings()
        if not url or not key or not secret: raise ValueError("LiveKit is not fully configured.")
        from livekit import api
        token=(api.AccessToken(key,secret).with_identity(str(p["player_key"])).with_name(str(p.get("name","Player"))).with_grants(api.VideoGrants(room_join=True,room=f"dirty-minds-{room.room_id}",can_publish=True,can_subscribe=True,can_publish_data=True)).to_jwt())
        return jsonify(success=True,url=url,token=token,room=f"dirty-minds-{room.room_id}")
    except ValueError as e: return jsonify(success=False,error=str(e)),400
    except Exception: return jsonify(success=False,error="Unable to create the LiveKit connection token."),500

def _build_game_url(room_id,player_key):
    base=os.getenv("PUBLIC_BASE_URL","").strip().rstrip("/") or "https://melanatedaz.onrender.com"
    return f"{base}/real-games/play/dirty_minds?room={room_id}&player_key={player_key}"

@real_games_bp.route("/api/status")
def real_games_status():
    GAME_MANAGER.cleanup()
    return jsonify(success=True,service="Melanated AZ Real Games",games=len(GAMES),game_ids=[g["game_id"] for g in GAMES],categories=CATEGORY_ORDER,active_rooms=GAME_MANAGER.count(),dirty_minds_rooms=GAME_MANAGER.count("dirty_minds"))
