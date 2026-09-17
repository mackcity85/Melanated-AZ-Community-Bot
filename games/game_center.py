# ==========================================================
# Melanated AZ Bot - Console Game Center
# ==========================================================
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from . import truth_dare_pin  # noqa: F401
from .games import initialize_game_database, games_callback_router as engine_games_callback_router
from .console_catalog import CONSOLE_ORDER, CONSOLE_BUTTONS, get_console, get_system
from real_games.nes_games import get_nes_games
from real_games.snes_games import get_snes_games
from real_games.retro_system_games import get_retro_games
from real_games.genre_games import get_genre_games
from real_games.game_manager import GAME_MANAGER
from real_games.dirty_minds import create_dirty_minds_state

logger = logging.getLogger("melanated_az_bot.games")
GAMES_CHAT_ID = -1002697105809
GAMES_TOPIC_ID = 8809
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "0") or "0")
GAME_CENTER_PIN_FILE = "/var/data/game_center_pin.txt"
GAME_CENTER_PIN_TEXT = ("🎮🔥 <b>MELANATED AZ GAME CENTER</b> 🔥🎮\n\n🥊 <b>Fighting</b>\n🏆 <b>Sports</b>\n🎭 <b>Dirty Minds</b>\n\n🟥 <b>Nintendo</b>\n🔵 <b>Sega</b>\n🟦 <b>PlayStation</b>\n🟩 <b>Xbox</b>\n\n👇🏾 <b>Choose a game or start Dirty Minds.</b>")

GAME_CATEGORIES = {"fighting": {"title":"🥊 FIGHTING", "games":[]}, "sports": {"title":"🏆 SPORTS", "games":[]}}

def _load_pinned_game_center_id():
    try:
        with open(GAME_CENTER_PIN_FILE, "r", encoding="utf-8") as f: return int(f.read().strip())
    except (FileNotFoundError, ValueError, OSError): return None

def _save_pinned_game_center_id(message_id):
    try:
        with open(GAME_CENTER_PIN_FILE, "w", encoding="utf-8") as f: f.write(str(message_id))
    except OSError: logger.exception("Could not save Game Center launcher ID.")

def console_home_keyboard():
    rows=[[InlineKeyboardButton("🥊 FIGHTING",callback_data="games_genre_all_fighting"),InlineKeyboardButton("🏆 SPORTS",callback_data="games_genre_all_sports")],[InlineKeyboardButton("🎭 DIRTY MINDS",callback_data="games_dirty_minds_start")]]
    for i in range(0,len(CONSOLE_ORDER),2):
        row=[InlineKeyboardButton(CONSOLE_BUTTONS[CONSOLE_ORDER[i]],callback_data=f"games_console_{CONSOLE_ORDER[i]}")]
        if i+1<len(CONSOLE_ORDER): row.append(InlineKeyboardButton(CONSOLE_BUTTONS[CONSOLE_ORDER[i+1]],callback_data=f"games_console_{CONSOLE_ORDER[i+1]}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def pinned_game_center_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("🎮 OPEN GAME CENTER",callback_data="games_home")],[InlineKeyboardButton("🎭 START DIRTY MINDS",callback_data="games_dirty_minds_start")]])

async def ensure_pinned_game_center(bot):
    mid=_load_pinned_game_center_id()
    if mid:
        try:
            msg=await bot.edit_message_text(chat_id=GAMES_CHAT_ID,message_id=mid,text=GAME_CENTER_PIN_TEXT,reply_markup=pinned_game_center_keyboard(),parse_mode=ParseMode.HTML)
            try: await bot.pin_chat_message(chat_id=GAMES_CHAT_ID,message_id=mid,disable_notification=True)
            except Exception: pass
            return msg
        except Exception: pass
    msg=await bot.send_message(chat_id=GAMES_CHAT_ID,message_thread_id=GAMES_TOPIC_ID,text=GAME_CENTER_PIN_TEXT,reply_markup=pinned_game_center_keyboard(),parse_mode=ParseMode.HTML)
    _save_pinned_game_center_id(msg.message_id)
    try: await bot.pin_chat_message(chat_id=GAMES_CHAT_ID,message_id=msg.message_id,disable_notification=True)
    except Exception: pass
    return msg

async def _send_dm_link(bot,user_id,room):
    p=room.get_player(str(user_id))
    if not p:return
    base=os.getenv("PUBLIC_BASE_URL","").strip().rstrip("/") or "https://melanatedaz.onrender.com"
    url=f"{base}/real-games/play/dirty_minds?room={room.room_id}&player_key={p['player_key']}"
    try:
        await bot.send_message(chat_id=int(user_id),text=f"🎭 <b>DIRTY MINDS</b>\n\nRoom: <b>{room.room_id}</b>\nYou are {'the host' if p.get('host') else 'a player'}.\n\nTap below to enter the game.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎭 ENTER DIRTY MINDS",url=url)]]),parse_mode=ParseMode.HTML)
    except Exception: logger.exception("Could not send Dirty Minds private game link | user=%s",user_id)

async def _post_dirty_minds_request(bot,room,host_name):
    text=(f"🎭 <b>DIRTY MINDS GAME REQUEST</b>\n\n<b>Host:</b> {host_name}\n<b>Room:</b> {room.room_id}\n<b>Players:</b> {room.player_count()}/20\n<b>Status:</b> ⏳ Awaiting admin approval\n\nAn admin must approve this game before it can start.")
    return await bot.send_message(chat_id=GAMES_CHAT_ID,message_thread_id=GAMES_TOPIC_ID,text=text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎭 JOIN DIRTY MINDS",callback_data=f"games_dirty_minds_join_{room.room_id}")]]),parse_mode=ParseMode.HTML)

async def _post_admin_request(bot,room,host_name,topic_message_id):
    if not ADMIN_GROUP_ID:return
    text=(f"🎭 <b>DIRTY MINDS APPROVAL REQUEST</b>\n\n<b>Host:</b> {host_name}\n<b>Room:</b> {room.room_id}\n<b>Players:</b> {room.player_count()}/20\n\nApprove this game before the host can start it.")
    await bot.send_message(chat_id=ADMIN_GROUP_ID,text=text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ APPROVE",callback_data=f"games_dirty_minds_approve_{room.room_id}"),InlineKeyboardButton("❌ DENY",callback_data=f"games_dirty_minds_deny_{room.room_id}")]]),parse_mode=ParseMode.HTML)

def _room_topic_text(room,status):
    host=room.get_player(room.host_id) or {}; name=host.get("name","Host")
    return f"🎭 <b>DIRTY MINDS</b>\n\n<b>Host:</b> {name}\n<b>Room:</b> {room.room_id}\n<b>Players:</b> {room.player_count()}/20\n<b>Status:</b> {status}"

async def dirty_minds_start_request(update,context):
    q=update.callback_query; user=update.effective_user
    if not q or not user:return
    await q.answer("Creating Dirty Minds room...")
    existing=GAME_MANAGER.find_player_room(user.id,game_id="dirty_minds")
    if existing:
        await _send_dm_link(context.bot,user.id,existing)
        await q.answer("You already have a Dirty Minds room. Check your private messages.",show_alert=True)
        return
    room=GAME_MANAGER.create(game_id="dirty_minds",game_name="Dirty Minds",max_players=20,min_players=2,state=create_dirty_minds_state())
    room.state["approval_status"]="pending"
    room.state["approval_requested_by"]=str(user.id)
    room.state["topic_chat_id"]=GAMES_CHAT_ID
    player=room.add_player(user_id=str(user.id),display_name=user.full_name or user.first_name or "Host")
    msg=await _post_dirty_minds_request(context.bot,room,player["name"])
    room.state["topic_message_id"]=msg.message_id
    await _post_admin_request(context.bot,room,player["name"],msg.message_id)
    await _send_dm_link(context.bot,user.id,room)

async def dirty_minds_join(update,context):
    q=update.callback_query; user=update.effective_user
    if not q or not user:return
    room_id=(q.data or "").removeprefix("games_dirty_minds_join_")
    room=GAME_MANAGER.get(room_id)
    if not room or room.game_id!="dirty_minds": await q.answer("That Dirty Minds room is no longer available.",show_alert=True); return
    if room.finished: await q.answer("That game has finished.",show_alert=True); return
    existing=room.get_player(user.id)
    if not existing:
        try: existing=room.add_player(user_id=str(user.id),display_name=user.full_name or user.first_name or "Player")
        except ValueError as exc: await q.answer(str(exc),show_alert=True); return
    await q.answer("You joined Dirty Minds. Check your private messages for your game link.",show_alert=True)
    await _send_dm_link(context.bot,user.id,room)
    topic_id=room.state.get("topic_message_id")
    if topic_id:
        try: await context.bot.edit_message_text(chat_id=GAMES_CHAT_ID,message_id=topic_id,text=_room_topic_text(room,"⏳ Awaiting admin approval"),reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎭 JOIN DIRTY MINDS",callback_data=f"games_dirty_minds_join_{room.room_id}")]]),parse_mode=ParseMode.HTML)
        except Exception: pass

async def dirty_minds_admin_decision(update,context):
    q=update.callback_query; user=update.effective_user
    if not q or not user:return
    from admin import is_admin
    if not await is_admin(user.id,context): await q.answer("⛔ Admin access required.",show_alert=True); return
    data=q.data or ""; approve=data.startswith("games_dirty_minds_approve_"); room_id=data.rsplit("_",1)[-1]; room=GAME_MANAGER.get(room_id)
    if not room: await q.answer("Room no longer exists.",show_alert=True); return
    if room.state.get("approval_status") not in ("pending",None): await q.answer("This request was already processed.",show_alert=True); return
    room.state["approval_status"]="approved" if approve else "denied"; room.state["approved_by"]=str(user.id) if approve else None
    status="✅ Approved — host may start the game" if approve else "❌ Denied by an admin"
    topic_id=room.state.get("topic_message_id")
    if topic_id:
        try:
            buttons=[] if not approve else [[InlineKeyboardButton("🎭 JOIN DIRTY MINDS",callback_data=f"games_dirty_minds_join_{room.room_id}")]]
            await context.bot.edit_message_text(chat_id=GAMES_CHAT_ID,message_id=topic_id,text=_room_topic_text(room,status),reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,parse_mode=ParseMode.HTML)
        except Exception: pass
    await q.answer("Dirty Minds approved." if approve else "Dirty Minds denied.")
    try: await q.edit_message_text(q.message.text + f"\n\n<b>Status:</b> {status}",parse_mode=ParseMode.HTML)
    except Exception: pass
    host_id=room.host_id
    if host_id: await _send_dm_link(context.bot,host_id,room)

async def games_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    message=update.effective_message
    if not message:return
    initialize_game_database()
    await message.reply_text("🎮 <b>MELANATED AZ GAME CENTER</b>\n\nChoose a genre or console family below.\n\n🥊 Fighting and 🏆 Sports use dedicated gameplay.\n\n🎭 Dirty Minds requires admin approval before it can start.",reply_markup=console_home_keyboard(),parse_mode=ParseMode.HTML)

async def games_home_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    await q.answer(); await q.edit_message_text("🎮 <b>MELANATED AZ GAME CENTER</b>\n\n🥊 Fighting = actual 1v1 combat\n🏆 Sports = actual sport gameplay\n🎭 Dirty Minds = multiplayer + admin approval\n\nChoose a genre or console family.",reply_markup=console_home_keyboard(),parse_mode=ParseMode.HTML)

async def genre_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    data=q.data or ""
    if data=="games_genre_all_fighting": games=[g for g in get_genre_games() if g["genre"]=="fighting"]; title="🥊 <b>FIGHTING GAMES</b>"
    elif data=="games_genre_all_sports": games=[g for g in get_genre_games() if g["genre"]=="sports"]; title="🏆 <b>SPORTS GAMES</b>"
    elif data.startswith("games_genre_"):
        cid=data.removeprefix("games_genre_"); console=get_console(cid)
        if not console: await q.answer("Console not found.",show_alert=True); return
        ids={sid for sid,_ in console["systems"]}; games=[g for g in get_genre_games() if g["system_id"] in ids]; title=f"🥊🏆 <b>{console['title']} — FIGHTING & SPORTS</b>"
    else: await q.answer("Genre not found.",show_alert=True); return
    await q.answer(); rows=[[InlineKeyboardButton(f"{g['icon']} {g['name']} — {g['system_name']}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in games]; rows.append([InlineKeyboardButton("⬅️ Game Center",callback_data="games_home")]); await q.edit_message_text(f"{title}\n\nDedicated genre gameplay. Pick a game to play:",reply_markup=InlineKeyboardMarkup(rows),parse_mode=ParseMode.HTML)

async def console_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    cid=(q.data or "").removeprefix("games_console_"); console=get_console(cid)
    if not console: await q.answer("Console not found.",show_alert=True); return
    await q.answer(); rows=[]; system_ids={sid for sid,_ in console["systems"]}
    for sid,name in console["systems"]:
        games=get_retro_games(sid) if sid not in ("nes","snes") else (get_nes_games() if sid=="nes" else get_snes_games())
        rows.append([InlineKeyboardButton(f"🕹️ {name} — {len(games)} PLAYABLE" if games else f"🎮 {name}",callback_data=f"games_system_{cid}_{sid}")])
    genre_games=[g for g in get_genre_games() if g["system_id"] in system_ids]
    if genre_games: rows.append([InlineKeyboardButton(f"🥊🏆 Fighting & Sports — {len(genre_games)} PLAYABLE",callback_data=f"games_genre_{cid}")])
    rows.append([InlineKeyboardButton("⬅️ Consoles",callback_data="games_home")]); await q.edit_message_text(f"{console['title']}\n\nChoose a console system or genre-specific game.",reply_markup=InlineKeyboardMarkup(rows),parse_mode=ParseMode.HTML)

def _system_games(sid):
    if sid=="nes": return get_nes_games()
    if sid=="snes": return get_snes_games()
    return get_retro_games(sid)
async def nes_callback(update,context): return await _playable_system_callback(update,context,"nes","NES","games_console_nintendo")
async def snes_callback(update,context): return await _playable_system_callback(update,context,"snes","SNES","games_console_nintendo")
async def _playable_system_callback(update,context,sid,name,back):
    q=update.callback_query
    if not q:return
    await q.answer(); games=_system_games(sid); rows=[[InlineKeyboardButton(f"{g['icon']} {g['name']}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in games]; genre_games=[g for g in get_genre_games() if g["system_id"]==sid]; rows += [[InlineKeyboardButton(f"{g['icon']} {g['name']} — {g['genre'].capitalize()}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in genre_games]; rows.append([InlineKeyboardButton("⬅️ Back",callback_data=back)]); await q.edit_message_text(f"🕹️ <b>{name}</b>\n\nChoose a playable game:",reply_markup=InlineKeyboardMarkup(rows),parse_mode=ParseMode.HTML)

def game_center_callback_router(update,context):
    data=update.callback_query.data if update.callback_query else ""
    if data=="games_home": return games_home_callback(update,context)
    if data.startswith("games_genre_"): return genre_callback(update,context)
    if data.startswith("games_console_"): return console_callback(update,context)
    if data.startswith("games_system_nintendo_nes"): return nes_callback(update,context)
    if data.startswith("games_system_nintendo_snes"): return snes_callback(update,context)
    if data=="games_dirty_minds_start": return dirty_minds_start_request(update,context)
    if data.startswith("games_dirty_minds_join_"): return dirty_minds_join(update,context)
    if data.startswith("games_dirty_minds_approve_") or data.startswith("games_dirty_minds_deny_"): return dirty_minds_admin_decision(update,context)
    return engine_games_callback_router(update,context)
