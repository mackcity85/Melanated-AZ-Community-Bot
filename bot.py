# ==========================================================
# Melanated AZ Bot
# bot.py
#
# COMPLETE CLEAN DROP-IN LAUNCHER
#
# Includes:
#   - Existing raffle system
#   - Existing birthday system
#   - Existing Game Center
#   - Existing Truth or Dare
#   - Existing media moderation
#   - NEW separate Real Games system
#   - NEW Monopoly web game
#   - NEW Telegram deep-links for Real Games
#
# IMPORTANT:
#   - Existing games/ package is NOT replaced.
#   - Existing raffle database is NOT replaced.
#   - Existing raffle callbacks remain owned by raffle.py.
#   - Real Games lives separately in real_games/.
# ==========================================================

import logging
import os
import threading

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ParseMode

from telegram.error import (
    TelegramError,
    BadRequest,
)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
)

from admin import (
    admin_menu,
    admin_button,
    admin_birthday_text_handler,
    is_admin,
)

from birthday import (
    birthday,
    my_birthday,
    remove_my_birthday,
    birthday_callback,
    birthday_text_handler,
)

from raffle import (
    start_raffle,
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
    raffle_callback,
)

from raffle_database import (
    get_database_stats,
    check_database_integrity,
)

from truth_dare import (
    truth,
    dare,
    truth_dare_menu,
    truth_dare_callback,
)

# ----------------------------------------------------------
# EXISTING GAME CENTER
# ----------------------------------------------------------

from games.game_center import (
    games_command,
    game_center_callback_router,
    initialize_game_database,
)

# ----------------------------------------------------------
# NEW REAL GAMES
#
# This is completely separate from games/
# ----------------------------------------------------------

from real_games import (
    real_games_bp,
    handle_real_game_deep_link,
)

from real_games.monopoly import (
    monopoly_bp,
)


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(
    "melanated_az_bot"
)


# ==========================================================
# STARTUP INFORMATION
# ==========================================================

logger.info(
    "=========================================================="
)

logger.info(
    "Starting Melanated AZ Bot"
)

logger.info(
    "Loaded Admin IDs: %s",
    list(ADMIN_IDS),
)

logger.info(
    "Raffle Chat ID: %s",
    RAFFLE_CHAT_ID,
)

logger.info(
    "=========================================================="
)


# ==========================================================
# FLASK HEALTH SERVER
# ==========================================================

app = Flask(__name__)


# ----------------------------------------------------------
# EXISTING HEALTH ROUTES
# ----------------------------------------------------------

@app.route("/")
def health_check():

    return (
        "Melanated AZ Bot is running.",
        200,
    )


@app.route("/health")
def health():

    return (
        "OK",
        200,
    )


# ----------------------------------------------------------
# NEW REAL GAMES ROUTES
#
# These do NOT interfere with the existing health routes.
# ----------------------------------------------------------

app.register_blueprint(
    real_games_bp
)

app.register_blueprint(
    monopoly_bp
)

logger.info(
    "Real Games web routes registered."
)

logger.info(
    "Real Games URL: /real-games/"
)

logger.info(
    "Monopoly URL: /real-games/monopoly/"
)


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
    )

    logger.info(
        "Starting Flask on port %s",
        port,
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ==========================================================
# MESSAGE DELETION
# ==========================================================

async def delete_message_later(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    if (
        data.get("chat_id") is None
        or data.get("message_id") is None
    ):
        return

    try:

        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )

    except TelegramError:

        pass


async def delete_after(
    context: ContextTypes.DEFAULT_TYPE,
    message,
    seconds=30,
):

    if message and context.job_queue:

        context.job_queue.run_once(
            delete_message_later,
            when=seconds,
            data={
                "chat_id": message.chat_id,
                "message_id": message.message_id,
            },
        )


# ==========================================================
# BOT USERNAME
# ==========================================================

async def get_bot_username(
    context: ContextTypes.DEFAULT_TYPE,
):

    username = (
        context.application.bot_data.get(
            "bot_username"
        )
    )

    if username:
        return username

    try:

        me = await context.bot.get_me()

        username = me.username

        if username:

            context.application.bot_data[
                "bot_username"
            ] = username

        return username

    except Exception:

        logger.exception(
            "Could not retrieve bot username."
        )

        return None


# ==========================================================
# MEDIA MODERATION
# ==========================================================

MEDIA_WARNING_SECONDS = 30


async def send_media_warning(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    username = await get_bot_username(
        context
    )

    keyboard = (
        InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "🤖 Post with Melanated AZ Bot",
                    url=f"https://t.me/{username}",
                )
            ]]
        )
        if username
        else None
    )

    text = (
        "⚠️ <b>Media Spoiler Required</b>\n\n"
        f"{user.mention_html()}, your photo/video "
        "was removed because it was not marked "
        "as a spoiler.\n\n"
        "Please resend the media using Telegram's "
        "🚫 <b>Spoiler</b> option."
    )

    try:

        warning = await context.bot.send_message(
            chat_id=message.chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        await delete_after(
            context,
            warning,
            MEDIA_WARNING_SECONDS,
        )

    except TelegramError:

        logger.exception(
            "Could not send media warning."
        )


async def send_private_media_warning(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    username = await get_bot_username(
        context
    )

    keyboard = (
        InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "🤖 Open Melanated AZ Bot",
                    url=f"https://t.me/{username}",
                )
            ]]
        )
        if username
        else None
    )

    text = (
        "👋 Hey! This is the Melanated AZ Bot "
        "from the Melanated AZ group.\n\n"
        "Your photo/video was removed because "
        "Telegram's Spoiler option was not enabled.\n\n"
        "📸 <b>How to post it correctly:</b>\n\n"
        "1️⃣ Select your photo or video.\n"
        "2️⃣ Tap the ⋮ menu/options.\n"
        "3️⃣ Select <b>Hide with Spoiler</b>.\n"
        "4️⃣ Send the media."
    )

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.info(
            "Could not send private media warning "
            "to %s.",
            user.id,
        )


async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if message.has_media_spoiler:
        return

    try:

        await message.delete()

    except TelegramError:

        pass

    await send_media_warning(
        update,
        context,
    )

    await send_private_media_warning(
        update,
        context,
    )


async def handle_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if message.has_media_spoiler:
        return

    try:

        await message.delete()

    except TelegramError:

        pass

    await send_media_warning(
        update,
        context,
    )

    await send_private_media_warning(
        update,
        context,
    )


async def handle_animation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    return


async def handle_image_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    return


# ==========================================================
# TEXT ROUTER
# ==========================================================

async def text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if await admin_birthday_text_handler(
        update,
        context,
    ):
        return

    if await birthday_text_handler(
        update,
        context,
    ):
        return


# ==========================================================
# /START
#
# IMPORTANT:
# Telegram deep-links also arrive through /start.
#
# Examples:
#
# /start rg_monopoly
# /start rg_join_AB12CD34
#
# We check Real Games FIRST.
# If it is not a Real Games payload,
# normal /start continues.
# ==========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    # ------------------------------------------------------
    # REAL GAMES DEEP-LINK
    # ------------------------------------------------------

    try:

        handled = await handle_real_game_deep_link(
            update,
            context,
        )

        if handled:

            logger.info(
                "Real Games deep-link handled for user %s",
                user.id,
            )

            return

    except Exception:

        logger.exception(
            "Real Games deep-link processing failed."
        )

        await message.reply_text(
            "⚠️ I couldn't open that game link. "
            "Please try again."
        )

        return

    # ------------------------------------------------------
    # NORMAL /START
    # ------------------------------------------------------

    text = (
        "👋 <b>Welcome to Melanated AZ Bot!</b>\n\n"
        "I'm the bot for the Melanated AZ community.\n\n"
        "🎂 Birthdays\n"
        "🎟️ Raffles\n"
        "🔥 Truth or Dare\n"
        "🎮 Game Center\n"
        "🎲 Real Games\n"
        "🛡️ Media protection\n\n"
        "Birthday: <code>/birthday</code>\n"
        "Truth or Dare: <code>/truthdare</code>\n"
        "Game Center: <code>/games</code>\n"
        "Real Games: <code>/realgames</code>"
    )

    if is_admin(user.id):

        text += (
            "\n\n👑 <b>Admin:</b>\n"
            "Use <code>/admin</code> to open "
            "the admin panel."
        )

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "🎮 REAL GAMES",
                callback_data="real_games_menu",
            )
        ]]
    )

    await message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# /REALGAMES
# ==========================================================

async def real_games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    base_url = (
        context.application.bot_data.get(
            "public_base_url"
        )
        or os.environ.get(
            "PUBLIC_BASE_URL",
            "",
        )
    ).rstrip("/")

    if base_url:

        games_url = (
            f"{base_url}/real-games/"
        )

        monopoly_url = (
            f"{base_url}/real-games/monopoly/"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎮 REAL GAMES",
                        url=games_url,
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🎲 MONOPOLY",
                        url=monopoly_url,
                    )
                ],
            ]
        )

        text = (
            "🎮 <b>Melanated AZ Real Games</b>\n\n"
            "These are the interactive browser games.\n\n"
            "Choose a game below:"
        )

    else:

        keyboard = None

        text = (
            "🎮 <b>Melanated AZ Real Games</b>\n\n"
            "The game server URL has not been configured yet.\n\n"
            "Set the Render environment variable:\n\n"
            "<code>PUBLIC_BASE_URL</code>"
        )

    await message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# /ADMIN
# ==========================================================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    if not is_admin(user.id):

        await update.effective_message.reply_text(
            "⛔ You are not authorized to use "
            "the admin panel."
        )

        return

    await admin_menu(
        update,
        context,
    )


# ==========================================================
# ADMIN CALLBACK ROUTER
# ==========================================================

async def admin_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):

        await query.answer(
            "⛔ You are not authorized.",
            show_alert=True,
        )

        return

    try:

        await admin_button(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Admin callback failed."
        )

        try:

            await query.answer(
                "⚠️ Something went wrong.",
                show_alert=True,
            )

        except Exception:

            pass


# ==========================================================
# BIRTHDAY CALLBACK ROUTER
# ==========================================================

async def birthday_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        await birthday_callback(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Birthday callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.answer(
                    "⚠️ Something went wrong.",
                    show_alert=True,
                )

            except Exception:

                pass


# ==========================================================
# GAME CENTER CALLBACK ROUTER
# ==========================================================

async def game_center_callback_router_wrapper(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        await game_center_callback_router(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Game Center callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.answer(
                    "⚠️ Game Center action failed.",
                    show_alert=True,
                )

            except Exception:

                pass


# ==========================================================
# REAL GAMES CALLBACK ROUTER
#
# This is intentionally separate from games/.
# ==========================================================

async def real_games_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    try:

        await query.answer()

    except Exception:

        pass

    base_url = (
        context.application.bot_data.get(
            "public_base_url"
        )
        or os.environ.get(
            "PUBLIC_BASE_URL",
            "",
        )
    ).rstrip("/")

    if not base_url:

        await query.message.reply_text(
            "⚠️ Real Games are not configured yet.\n\n"
            "The Render PUBLIC_BASE_URL environment "
            "variable needs to be set."
        )

        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎲 MONOPOLY",
                    url=(
                        f"{base_url}"
                        "/real-games/monopoly/"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 ALL REAL GAMES",
                    url=(
                        f"{base_url}"
                        "/real-games/"
                    ),
                )
            ],
        ]
    )

    await query.message.reply_text(
        "🎮 <b>REAL GAMES</b>\n\n"
        "Choose a game:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# TRUTH OR DARE CALLBACK ROUTER
# ==========================================================

async def truth_dare_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        await truth_dare_callback(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Truth or Dare callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.answer(
                    "⚠️ Something went wrong.",
                    show_alert=True,
                )

            except Exception:

                pass


# ==========================================================
# RAFFLE CALLBACK ROUTER
# ==========================================================

async def raffle_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    logger.info(
        "=========================================================="
    )

    logger.info(
        "RAFFLE CALLBACK HANDLER TRIGGERED"
    )

    logger.info(
        "Callback query exists: %s",
        bool(query),
    )

    if query:

        logger.info(
            "Callback data: %s",
            query.data,
        )

        logger.info(
            "Callback user: %s",
            getattr(
                update.effective_user,
                "id",
                None,
            ),
        )

        logger.info(
            "Callback username: %s",
            getattr(
                update.effective_user,
                "username",
                None,
            ),
        )

        callback_message = getattr(
            query,
            "message",
            None,
        )

        logger.info(
            "Callback chat ID: %s",
            getattr(
                callback_message,
                "chat_id",
                None,
            ),
        )

        logger.info(
            "Callback message ID: %s",
            getattr(
                callback_message,
                "message_id",
                None,
            ),
        )

    else:

        logger.warning(
            "RAFFLE CALLBACK HANDLER RECEIVED "
            "WITHOUT callback_query!"
        )

    logger.info(
        "Calling raffle.raffle_callback()..."
    )

    try:

        await raffle_callback(
            update,
            context,
        )

        logger.info(
            "raffle.raffle_callback() completed successfully."
        )

    except Exception:

        logger.exception(
            "Raffle callback failed."
        )

        if query:

            try:

                await query.answer(
                    "⚠️ Raffle action failed.",
                    show_alert=True,
                )

            except Exception:

                logger.exception(
                    "Could not answer failed "
                    "raffle callback."
                )

    logger.info(
        "=========================================================="
    )


# ==========================================================
# DATABASE STARTUP CHECK
# ==========================================================

def database_startup_check():

    try:

        stats = get_database_stats()

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Melanated AZ Bot - Persistent Database"
        )

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Database path       : %s",
            stats.get("database"),
        )

        logger.info(
            "Database directory  : %s",
            stats.get("database_directory"),
        )

        logger.info(
            "Database exists     : %s",
            stats.get("exists"),
        )

        logger.info(
            "Database size       : %s",
            stats.get("size"),
        )

        logger.info(
            "Persistent directory: %s",
            stats.get("persistent"),
        )

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Melanated AZ Bot - Database Statistics"
        )

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Database       : %s",
            stats.get("database"),
        )

        logger.info(
            "Raffles        : %s",
            stats.get("raffles"),
        )

        logger.info(
            "Raffle Entries : %s",
            stats.get("raffle_entries"),
        )

        logger.info(
            "Birthdays      : %s",
            stats.get("birthdays"),
        )

        logger.info(
            "Known Members  : %s",
            stats.get("members"),
        )

        logger.info(
            "Integrity      : %s",
            "OK"
            if check_database_integrity()
            else "FAILED",
        )

        logger.info(
            "=========================================================="
        )

    except Exception:

        logger.exception(
            "Database startup check failed."
        )


# ==========================================================
# GAME DATABASE
# ==========================================================

def game_database_startup_check():

    try:

        initialize_game_database()

        logger.info(
            "Game Center database: READY"
        )

    except Exception:

        logger.exception(
            "Game Center database initialization failed."
        )


# ==========================================================
# REAL GAMES STARTUP CHECK
# ==========================================================

def real_games_startup_check():

    public_url = os.environ.get(
        "PUBLIC_BASE_URL",
        "",
    ).strip().rstrip("/")

    if public_url:

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Real Games: READY"
        )

        logger.info(
            "Public URL: %s",
            public_url,
        )

        logger.info(
            "Real Games: %s/real-games/",
            public_url,
        )

        logger.info(
            "Monopoly: %s/real-games/monopoly/",
            public_url,
        )

        logger.info(
            "=========================================================="
        )

    else:

        logger.warning(
            "=========================================================="
        )

        logger.warning(
            "PUBLIC_BASE_URL is NOT configured."
        )

        logger.warning(
            "Real Games can still run locally, but "
            "Telegram game links will not have a "
            "public Render URL."
        )

        logger.warning(
            "Set PUBLIC_BASE_URL in Render."
        )

        logger.warning(
            "=========================================================="
        )


# ==========================================================
# POST INIT
# ==========================================================

async def post_init(
    application: Application,
):

    # ------------------------------------------------------
    # BOT INFORMATION
    # ------------------------------------------------------

    try:

        me = await application.bot.get_me()

        application.bot_data[
            "bot_username"
        ] = me.username

        logger.info(
            "Bot username: @%s",
            me.username,
        )

    except Exception:

        logger.exception(
            "Could not retrieve bot information."
        )

    # ------------------------------------------------------
    # PUBLIC URL
    # ------------------------------------------------------

    public_url = os.environ.get(
        "PUBLIC_BASE_URL",
        "",
    ).strip().rstrip("/")

    if public_url:

        application.bot_data[
            "public_base_url"
        ] = public_url

        logger.info(
            "Public Base URL loaded: %s",
            public_url,
        )

    else:

        application.bot_data[
            "public_base_url"
        ] = ""

        logger.warning(
            "PUBLIC_BASE_URL is not configured."
        )


# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    error = context.error

    if isinstance(
        error,
        BadRequest,
    ):

        logger.warning(
            "Telegram BadRequest: %s",
            error,
        )

        return

    logger.exception(
        "Unhandled bot exception:",
        exc_info=error,
    )


# ==========================================================
# BUILD APPLICATION
# ==========================================================

def build_application():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN is not configured."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ======================================================
    # COMMANDS
    # ======================================================

    for command, callback in [

        (
            "start",
            start_command,
        ),

        (
            "realgames",
            real_games_command,
        ),

        (
            "admin",
            admin_command,
        ),

        (
            "startraffle",
            start_raffle,
        ),

        (
            "rafflestatus",
            raffle_status,
        ),

        (
            "entries",
            raffle_entries,
        ),

        (
            "pending",
            pending_entries,
        ),

        (
            "paid",
            paid_entry,
        ),

        (
            "cancelraffle",
            cancel_raffle,
        ),

        (
            "draw",
            draw_raffle,
        ),

        (
            "games",
            games_command,
        ),

        (
            "birthday",
            birthday,
        ),

        (
            "mybirthday",
            my_birthday,
        ),

        (
            "removebirthday",
            remove_my_birthday,
        ),

        (
            "truthdare",
            truth_dare_menu,
        ),

        (
            "truth",
            truth,
        ),

        (
            "dare",
            dare,
        ),

    ]:

        application.add_handler(
            CommandHandler(
                command,
                callback,
            )
        )

    # ======================================================
    # RAFFLE CALLBACKS
    #
    # raffle.py remains the ONLY owner of raffle
    # callback processing.
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_callback_router,
            pattern=(
                r"^(raffle_|"
                r"approve_|"
                r"deny_|"
                r"enter_|"
                r"pay_|"
                r"payment_|"
                r"paid_|"
                r"draw_|"
                r"reroll_|"
                r"bonus_|"
                r"remove_)"
            ),
        )
    )

    # ======================================================
    # ADMIN CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_callback_router,
            pattern=r"^admin_",
        )
    )

    # ======================================================
    # BIRTHDAY CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            birthday_callback_router,
            pattern=r"^birthday_",
        )
    )

    # ======================================================
    # EXISTING GAME CENTER CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            game_center_callback_router_wrapper,
            pattern=r"^games_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            game_center_callback_router_wrapper,
            pattern=r"^game_",
        )
    )

    # ======================================================
    # NEW REAL GAMES CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            real_games_callback_router,
            pattern=r"^real_games_",
        )
    )

    # ======================================================
    # TRUTH OR DARE CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            truth_dare_callback_router,
            pattern=r"^truthdare_",
        )
    )

    # ======================================================
    # MEDIA
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo,
        ),
        group=5,
    )

    application.add_handler(
        MessageHandler(
            filters.VIDEO,
            handle_video,
        ),
        group=5,
    )

    application.add_handler(
        MessageHandler(
            filters.ANIMATION,
            handle_animation,
        ),
        group=5,
    )

    application.add_handler(
        MessageHandler(
            filters.Document.IMAGE,
            handle_image_document,
        ),
        group=5,
    )

    # ======================================================
    # TEXT
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_router,
        ),
        group=10,
    )

    # ======================================================
    # ERROR HANDLER
    # ======================================================

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "All Telegram handlers registered."
    )

    logger.info(
        "Raffle callback handler registered."
    )

    logger.info(
        "Existing Game Center callbacks registered."
    )

    logger.info(
        "Real Games callback handler registered."
    )

    logger.info(
        "Real Games deep-link handler registered."
    )

    return application


# ==========================================================
# MAIN
# ==========================================================

def main():

    logger.info(
        "=========================================================="
    )

    logger.info(
        "Starting Melanated AZ Bot"
    )

    logger.info(
        "=========================================================="
    )

    logger.info(
        "Loaded Admin IDs: %s",
        list(ADMIN_IDS),
    )

    logger.info(
        "Raffle Chat ID: %s",
        RAFFLE_CHAT_ID,
    )

    # ------------------------------------------------------
    # DATABASE
    # ------------------------------------------------------

    database_startup_check()

    # ------------------------------------------------------
    # EXISTING GAME CENTER DATABASE
    # ------------------------------------------------------

    game_database_startup_check()

    # ------------------------------------------------------
    # NEW REAL GAMES
    # ------------------------------------------------------

    real_games_startup_check()

    # ------------------------------------------------------
    # START FLASK
    # ------------------------------------------------------

    threading.Thread(
        target=run_flask,
        daemon=True,
        name="flask-health-server",
    ).start()

    logger.info(
        "Flask health server started."
    )

    # ------------------------------------------------------
    # BUILD TELEGRAM APPLICATION
    # ------------------------------------------------------

    application = build_application()

    logger.info(
        "Telegram application created."
    )

    # ------------------------------------------------------
    # START POLLING
    # ------------------------------------------------------

    logger.info(
        "Starting Telegram polling..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
        close_loop=False,
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    main()


# ==========================================================
# END bot.py
# ==========================================================
