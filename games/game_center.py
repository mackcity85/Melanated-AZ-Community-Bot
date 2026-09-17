# ==========================================================
# Melanated AZ Bot - Console Game Center
# ==========================================================
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from .games import initialize_game_database, games_callback_router as engine_games_callback_router
from .console_catalog import CONSOLE_ORDER, CONSOLE_BUTTONS, get_console, get_system
from real_games.nes_games import get_nes_games
from real_games.snes_games import get_snes_games
from real_games.retro_system_games import get_retro_games
from real_games.genre_games import get_genre_games

logger = logging.getLogger("melanated_az_bot.games")
GAMES_CHAT_ID = -1002697105809
GAMES_TOPIC_ID = 8809
GAME_CENTER_PIN_FILE = "/var/data/game_center_pin.txt"
GAME_CENTER_PIN_TEXT = ("🎮🔥 <b>MELANATED AZ RETRO CONSOLE ARCADE</b> 🔥🎮\n\n🟥 <b>Nintendo</b>\n🔵 <b>Sega</b>\n🟦 <b>PlayStation</b>\n🟩 <b>Xbox</b>\n\nEvery title added here will be an actual playable retro-inspired console game.\n\n🥊 <b>Fighting</b> and 🏀 <b>Sports</b> now have dedicated gameplay too.\n\n👇🏾 <b>Choose your console.</b>")


def _load_pinned_game_center_id():
    try:
        with open(GAME_CENTER_PIN_FILE, "r", encoding="utf-8") as f: return int(f.read().strip())
    except (FileNotFoundError, ValueError, OSError): return None


def _save_pinned_game_center_id(message_id):
    try:
        with open(GAME_CENTER_PIN_FILE, "w", encoding="utf-8") as f: f.write(str(message_id))
    except OSError: logger.exception("Could not save Game Center launcher ID.")


def console_home_keyboard():
    rows=[]
    for i in range(0,len(CONSOLE_ORDER),2):
        row=[InlineKeyboardButton(CONSOLE_BUTTONS[CONSOLE_ORDER[i]],callback_data=f"games_console_{CONSOLE_ORDER[i]}")]
        if i+1<len(CONSOLE_ORDER): row.append(InlineKeyboardButton(CONSOLE_BUTTONS[CONSOLE_ORDER[i+1]],callback_data=f"games_console_{CONSOLE_ORDER[i+1]}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def pinned_game_center_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("🎮 OPEN GAME CENTER",callback_data="games_home")]])


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


async def games_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    message=update.effective_message
    if not message:return
    initialize_game_database()
    await message.reply_text("🎮 <b>MELANATED AZ RETRO CONSOLE ARCADE</b>\n\nChoose a console family below.\n\nOnly actual playable retro-inspired games will appear in the library.",reply_markup=console_home_keyboard(),parse_mode=ParseMode.HTML)


async def games_home_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    await q.answer(); await q.edit_message_text("🎮 <b>MELANATED AZ RETRO CONSOLE ARCADE</b>\n\nChoose a console family.\n\nEvery game added to this center is genuinely playable.",reply_markup=console_home_keyboard(),parse_mode=ParseMode.HTML)


async def console_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    cid=(q.data or "").removeprefix("games_console_"); console=get_console(cid)
    if not console: await q.answer("Console not found.",show_alert=True); return
    await q.answer(); rows=[]
    system_ids={sid for sid,_ in console["systems"]}
    for sid,name in console["systems"]:
        games=get_retro_games(sid) if sid not in ("nes","snes") else (get_nes_games() if sid=="nes" else get_snes_games())
        if games: rows.append([InlineKeyboardButton(f"🕹️ {name} — {len(games)} PLAYABLE",callback_data=f"games_system_{cid}_{sid}")])
        else: rows.append([InlineKeyboardButton(f"🎮 {name}",callback_data=f"games_system_{cid}_{sid}")])
    genre_games=[g for g in get_genre_games() if g["system_id"] in system_ids]
    if genre_games:
        rows.append([InlineKeyboardButton(f"🥊🏀 Fighting & Sports — {len(genre_games)} PLAYABLE",callback_data=f"games_genre_{cid}")])
    rows.append([InlineKeyboardButton("⬅️ Consoles",callback_data="games_home")])
    await q.edit_message_text(f"{console['title']}\n\nChoose a console system or a genre-specific game.",reply_markup=InlineKeyboardMarkup(rows),parse_mode=ParseMode.HTML)


def _system_games(sid):
    if sid=="nes": return get_nes_games()
    if sid=="snes": return get_snes_games()
    return get_retro_games(sid)


async def nes_callback(update:Update,context:ContextTypes.DEFAULT_TYPE): return await _playable_system_callback(update,context,"nes","NES","games_console_nintendo")
async def snes_callback(update:Update,context:ContextTypes.DEFAULT_TYPE): return await _playable_system_callback(update,context,"snes","SNES","games_console_nintendo")


async def _playable_system_callback(update,context,sid,name,back):
    q=update.callback_query
    if not q:return
    await q.answer(); games=_system_games(sid)
    rows=[[InlineKeyboardButton(f"{g['icon']} {g['name']}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in games]
    genre_games=[g for g in get_genre_games() if g["system_id"]==sid]
    rows += [[InlineKeyboardButton(f"{g['icon']} {g['name']} — {g['genre'].capitalize()}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in genre_games]
    rows.append([InlineKeyboardButton("⬅️ Back",callback_data=back)])
    await q.edit_message_text(f"🎮 <b>{name}</b>\n\nOriginal console-inspired games. No ROMs. Pick a game to play:",reply_markup=InlineKeyboardMarkup(rows),parse_mode=ParseMode.HTML)


async def genre_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    cid=(q.data or "").removeprefix("games_genre_"); console=get_console(cid)
    if not console: await q.answer("Console not found.",show_alert=True); return
    system_ids={sid for sid,_ in console["systems"]}; games=[g for g in get_genre_games() if g["system_id"] in system_ids]
    await q.answer()
    rows=[[InlineKeyboardButton(f"{g['icon']} {g['name']} — {g['genre'].capitalize()}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in games]
    rows.append([InlineKeyboardButton("⬅️ Back to Console",callback_data=f"games_console_{cid}")])
    await q.edit_message_text(f"🥊🏀 <b>{console['title']} — FIGHTING & SPORTS</b>\n\nThese titles use dedicated fighting or sports gameplay—not the generic arcade template.",reply_markup=InlineKeyboardMarkup(rows),parse_mode=ParseMode.HTML)


async def system_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    payload=(q.data or "").removeprefix("games_system_"); parts=payload.split("_",1)
    if len(parts)!=2: await q.answer("System not found.",show_alert=True); return
    cid,sid=parts; system=get_system(cid,sid)
    if not system: await q.answer("System not found.",show_alert=True); return
    games=_system_games(sid); genre_games=[g for g in get_genre_games() if g["system_id"]==sid]
    await q.answer()
    if games or genre_games:
        rows=[[InlineKeyboardButton(f"{g['icon']} {g['name']}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in games]
        rows += [[InlineKeyboardButton(f"{g['icon']} {g['name']} — {g['genre'].capitalize()}",url=f"https://melanatedaz.onrender.com/real-games/play/{g['game_id']}")] for g in genre_games]
        rows += [[InlineKeyboardButton("⬅️ Back to Console",callback_data=f"games_console_{cid}")],[InlineKeyboardButton("🎮 All Consoles",callback_data="games_home")]]
        text=f"🎮 <b>{system['name']}</b>\n\n{len(games)+len(genre_games)} playable games are installed. Pick one to play:"
    else:
        rows=[[InlineKeyboardButton("⬅️ Back to Console",callback_data=f"games_console_{cid}")],[InlineKeyboardButton("🎮 All Consoles",callback_data="games_home")]]
        text=f"🎮 <b>{system['name']}</b>\n\nNo playable titles are installed in this system yet."
    await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup(rows),parse_mode=ParseMode.HTML)


async def games_admin_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    user=update.effective_user;q=update.callback_query
    if not user:return
    try:
        from admin import is_admin; authorized=await is_admin(user.id,context)
    except Exception:
        if q: await q.answer("⚠️ Unable to verify admin access.",show_alert=True)
        return
    if not authorized:
        if q: await q.answer("⛔ You are not authorized.",show_alert=True)
        return
    if q:
        await q.answer(); await q.edit_message_text("🎮 <b>RETRO CONSOLE GAME CENTER</b>\n\n🟥 Nintendo\n🔵 Sega\n🟦 PlayStation\n🟩 Xbox\n\n🥊 Fighting and 🏀 Sports use dedicated gameplay.\n\nPlayable titles are added one system at a time.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Open Game Center",callback_data="games_home")],[InlineKeyboardButton("⬅️ Back to Admin Panel",callback_data="admin_back")]]),parse_mode=ParseMode.HTML)


async def game_center_callback_router(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if not q:return
    data=q.data or ""
    if data=="games_home": return await games_home_callback(update,context)
    if data=="games_nes": return await nes_callback(update,context)
    if data=="games_snes": return await snes_callback(update,context)
    if data.startswith("games_console_"): return await console_callback(update,context)
    if data.startswith("games_genre_"): return await genre_callback(update,context)
    if data.startswith("games_system_"): return await system_callback(update,context)
    if data.startswith("game_"): return await engine_games_callback_router(update,context)
    await q.answer("That Game Center option is no longer available.",show_alert=True)


games_callback=game_center_callback_router
games_home_keyboard=console_home_keyboard
