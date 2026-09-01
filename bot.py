# ==========================================================
# Melanated AZ Bot
# bot.py
#
# COMPLETE CLEAN DROP-IN LAUNCHER
#
# Fixes:
#   - Correct Flask(__name__) syntax
#   - Correct python-telegram-bot v21 handler groups
#   - Raffle callbacks routed through raffle.raffle_callback
#   - Existing database is preserved
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

from games.game_center import (
    games_command,
    game_center_callback_router,
    initialize_game_database,
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

logger = logging.getLogger("melanated_az_bot")


# ==========================================================
# FLASK HEALTH SERVER
# ==========================================================

app = Flask(__name__)


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


def run_flask():
    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
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

async def delete_message_later(context: ContextTypes.DEFAULT_TYPE):

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

    username = context.application.bot_data.get(
        "bot_username"
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
# ==========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    text = (
        "👋 <b>Welcome to Melanated AZ Bot!</b>\n\n"
        "I'm the bot for the Melanated AZ community.\n\n"
        "🎂 Birthdays\n"
        "🎟️ Raffles\n"
        "🔥 Truth or Dare\n"
        "🎮 Game Center\n"
        "🛡️ Media protection\n\n"
        "Birthday: <code>/birthday</code>\n"
        "Truth or Dare: <code>/truthdare</code>\n"
        "Game Center: <code>/games</code>"
    )

    if is_admin(user.id):

        text += (
            "\n\n👑 <b>Admin:</b>\n"
            "Use <code>/admin</code> to open "
            "the admin panel."
        )

    await message.reply_text(
        text,
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

    # IMPORTANT:
    #
    # raffle.py owns all raffle callbacks.
    #
    # This includes:
    #
    #   enter_
    #   approve_
    #   deny_
    #   raffle_approve_
    #   raffle_cancel_
    #   pay_cashapp_
    #   pay_zelle_
    #   payment_
    #   paid_
    #   draw_
    #   reroll_
    #   bonus_
    #   remove_
    #
    # Do NOT answer the callback here.
    # raffle.py is responsible for doing so.

    try:

        await raffle_callback(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Raffle callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.answer(
                    "⚠️ Raffle action failed.",
                    show_alert=True,
                )

            except Exception:
                pass


# ==========================================================
# DATABASE STARTUP CHECK
# ==========================================================

def database_startup_check():

    try:

        stats = get_database_stats()

        logger.info(
            "Database: %s",
            stats.get("database"),
        )

        logger.info(
            "Raffles: %s | Entries: %s | "
            "Birthdays: %s | Members: %s",
            stats.get("raffles"),
            stats.get("raffle_entries"),
            stats.get("birthdays"),
            stats.get("members"),
        )

        if not check_database_integrity():

            raise RuntimeError(
                "Database integrity check failed."
            )

        logger.info(
            "Database integrity: OK"
        )

    except Exception:

        logger.exception(
            "Database startup check failed."
        )


# ==========================================================
# GAME DATABASE
# ==========================================================

def game_database_startup_check():

    initialize_game_database()

    logger.info(
        "Game Center database: READY"
    )


# ==========================================================
# POST INIT
# ==========================================================

async def post_init(
    application: Application,
):

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
    # IMPORTANT:
    # This MUST be registered before admin callbacks.
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_callback_router,
            pattern=(
                r"^(raffle_approve_|"
                r"raffle_cancel_|"
                r"approve_|"
                r"deny_|"
                r"enter_|"
                r"pay_cashapp_|"
                r"pay_zelle_|"
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
    # GAME CENTER CALLBACKS
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
    #
    # IMPORTANT:
    # group belongs to add_handler(), NOT MessageHandler().
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

    database_startup_check()

    game_database_startup_check()

    threading.Thread(
        target=run_flask,
        daemon=True,
        name="flask-health-server",
    ).start()

    logger.info(
        "Flask health server started."
    )

    application = build_application()

    logger.info(
        "Telegram application created."
    )

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
