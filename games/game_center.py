# ==========================================================
# Melanated AZ Bot - Console Game Center
# ==========================================================
# Console-first Game Center. Only actual playable games will
# be exposed. Retro-inspired titles are added one system at a time.
# ==========================================================

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .games import initialize_game_database, games_callback_router as engine_games_callback_router
from .console_catalog import CONSOLE_ORDER, CONSOLE_BUTTONS, get_console, get_system

logger = logging.getLogger("melanated_az_bot.games")

GAMES_CHAT_ID = -1002697105809
GAMES_TOPIC_ID = 8809
GAME_CENTER_PIN_FILE = "/var/data/game_center_pin.txt"

GAME_CENTER_PIN_TEXT = (
    "🎮🔥 <b>MELANATED AZ RETRO CONSOLE ARCADE</b> 🔥🎮\n\n"
    "🟥 <b>Nintendo</b>\n"
    "🔵 <b>Sega</b>\n"
    "🟦 <b>PlayStation</b>\n"
    "🟩 <b>Xbox</b>\n\n"
    "Every title added here will be an actual playable "
    "retro-inspired console game.\n\n"
    "👇🏾 <b>Choose your console.</b>"
)


def _load_pinned_game_center_id():
    try:
        with open(GAME_CENTER_PIN_FILE, "r", encoding="utf-8") as file:
            value = file.read().strip()
        return int(value) if value else None
    except (FileNotFoundError, ValueError, OSError):
        return None


def _save_pinned_game_center_id(message_id):
    try:
        with open(GAME_CENTER_PIN_FILE, "w", encoding="utf-8") as file:
            file.write(str(message_id))
    except OSError:
        logger.exception("Could not save Game Center launcher ID.")


def console_home_keyboard():
    rows = []
    for index in range(0, len(CONSOLE_ORDER), 2):
        row = []
        first = CONSOLE_ORDER[index]
        row.append(InlineKeyboardButton(CONSOLE_BUTTONS[first], callback_data=f"games_console_{first}"))
        if index + 1 < len(CONSOLE_ORDER):
            second = CONSOLE_ORDER[index + 1]
            row.append(InlineKeyboardButton(CONSOLE_BUTTONS[second], callback_data=f"games_console_{second}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def pinned_game_center_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 OPEN GAME CENTER", callback_data="games_home")],
    ])


async def ensure_pinned_game_center(bot):
    existing_message_id = _load_pinned_game_center_id()

    if existing_message_id:
        try:
            message = await bot.edit_message_text(
                chat_id=GAMES_CHAT_ID,
                message_id=existing_message_id,
                text=GAME_CENTER_PIN_TEXT,
                reply_markup=pinned_game_center_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            try:
                await bot.pin_chat_message(
                    chat_id=GAMES_CHAT_ID,
                    message_id=existing_message_id,
                    disable_notification=True,
                )
            except Exception:
                logger.debug("Could not re-pin Game Center launcher.", exc_info=True)
            return message
        except Exception:
            logger.info("Existing Game Center launcher unavailable; creating replacement.")

    message = await bot.send_message(
        chat_id=GAMES_CHAT_ID,
        message_thread_id=GAMES_TOPIC_ID,
        text=GAME_CENTER_PIN_TEXT,
        reply_markup=pinned_game_center_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    _save_pinned_game_center_id(message.message_id)

    try:
        await bot.pin_chat_message(
            chat_id=GAMES_CHAT_ID,
            message_id=message.message_id,
            disable_notification=True,
        )
    except Exception:
        logger.debug("Could not pin new Game Center launcher.", exc_info=True)

    logger.info("Created console Game Center launcher | chat=%s topic=%s message=%s", GAMES_CHAT_ID, GAMES_TOPIC_ID, message.message_id)
    return message


async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return
    initialize_game_database()
    await message.reply_text(
        "🎮 <b>MELANATED AZ RETRO CONSOLE ARCADE</b>\n\n"
        "Choose a console family below.\n\n"
        "🟥 Nintendo  •  🔵 Sega\n"
        "🟦 PlayStation  •  🟩 Xbox\n\n"
        "Only actual playable retro-inspired games will appear in the library.",
        reply_markup=console_home_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def games_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    await query.edit_message_text(
        "🎮 <b>MELANATED AZ RETRO CONSOLE ARCADE</b>\n\n"
        "Choose a console family.\n\n"
        "Every game added to this center must be genuinely playable.",
        reply_markup=console_home_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def console_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    console_id = (query.data or "").removeprefix("games_console_")
    console = get_console(console_id)
    if not console:
        await query.answer("Console not found.", show_alert=True)
        return

    await query.answer()
    rows = [
        [InlineKeyboardButton(f"🎮 {name}", callback_data=f"games_system_{console_id}_{system_id}")]
        for system_id, name in console["systems"]
    ]
    rows.append([InlineKeyboardButton("⬅️ Consoles", callback_data="games_home")])
    await query.edit_message_text(
        f"{console['title']}\n\nChoose a console system.\n\n"
        "Only installed, playable titles will be shown inside a system.",
        reply_markup=InlineKeyboardMarkup(rows),
        parse_mode=ParseMode.HTML,
    )


async def system_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    payload = (query.data or "").removeprefix("games_system_")
    parts = payload.split("_", 1)
    if len(parts) != 2:
        await query.answer("System not found.", show_alert=True)
        return

    console_id, system_id = parts
    system = get_system(console_id, system_id)
    if not system:
        await query.answer("System not found.", show_alert=True)
        return

    await query.answer()
    await query.edit_message_text(
        f"🎮 <b>{system['name']}</b>\n\n"
        "No playable titles are installed in this system yet.\n\n"
        "We are adding the library one console at a time. "
        "This screen will only show games after the game itself is playable.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Console", callback_data=f"games_console_{console_id}")],
            [InlineKeyboardButton("🎮 All Consoles", callback_data="games_home")],
        ]),
        parse_mode=ParseMode.HTML,
    )


async def games_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    query = update.callback_query
    if not user:
        return
    try:
        from admin import is_admin
        authorized = await is_admin(user.id, context)
    except Exception:
        logger.exception("Unable to verify Game Center admin access.")
        if query:
            await query.answer("⚠️ Unable to verify admin access.", show_alert=True)
        return
    if not authorized:
        if query:
            await query.answer("⛔ You are not authorized.", show_alert=True)
        return
    if query:
        await query.answer()
        await query.edit_message_text(
            "🎮 <b>RETRO CONSOLE GAME CENTER</b>\n\n"
            "The Game Center is organized by console family.\n\n"
            "🟥 Nintendo\n🔵 Sega\n🟦 PlayStation\n🟩 Xbox\n\n"
            "Playable titles will be added one console/system at a time.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Open Game Center", callback_data="games_home")],
                [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode=ParseMode.HTML,
        )


async def game_center_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data or ""

    if data == "games_home":
        await games_home_callback(update, context)
        return
    if data.startswith("games_console_"):
        await console_callback(update, context)
        return
    if data.startswith("games_system_"):
        await system_callback(update, context)
        return
    if data.startswith("game_"):
        await engine_games_callback_router(update, context)
        return

    await query.answer("That Game Center option is no longer available.", show_alert=True)


games_callback = game_center_callback_router
games_home_keyboard = console_home_keyboard
