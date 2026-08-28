# ==========================================================
# Melanated AZ Bot
# bot.py
#
# COMPLETE MAIN BOT LAUNCHER
#
# Features:
#   - /admin admin panel
#   - Raffle button routing
#   - Birthday system
#   - Persistent SQLite database
#   - Media spoiler enforcement
#   - GIF / animation support
#   - Image document support
#   - Private media instructions
#   - Group warning
#   - Truth or Dare
#   - Flask health server
#   - Telegram polling
#
# Database:
#   /var/data/raffle.db
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


# ==========================================================
# CONFIG
# ==========================================================

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
)


# ==========================================================
# ADMIN
# ==========================================================

from admin import (
    admin_menu,
    admin_button,
    admin_birthday_text_handler,
    cancel_birthday_input,
    is_admin,
)


# ==========================================================
# BIRTHDAY
# ==========================================================

from birthday import (
    birthday,
    my_birthday,
    remove_my_birthday,
    birthday_callback,
    birthday_text_handler,
)


# ==========================================================
# DATABASE
# ==========================================================

from raffle_database import (
    get_database_stats,
    check_database_integrity,
)


# ==========================================================
# RAFFLE
# ==========================================================

from raffle import (
    start_raffle,
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
)


# ==========================================================
# TRUTH OR DARE
# ==========================================================

from truth_dare import (
    truth,
    dare,
    truth_dare_menu,
    truth_dare_callback,
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

    return "OK", 200


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
    )

    logger.info(
        "Starting health server on port %s",
        port,
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ==========================================================
# TEMPORARY MESSAGE DELETE
# ==========================================================

async def delete_message_later(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    chat_id = data.get("chat_id")
    message_id = data.get("message_id")

    if chat_id is None or message_id is None:
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

    except TelegramError as exc:

        logger.debug(
            "Could not delete temporary message: %s",
            exc,
        )

    except Exception:

        logger.exception(
            "Unexpected temporary message "
            "deletion error."
        )


async def delete_after(
    context,
    message,
    seconds=30,
):

    if not message:
        return

    if not context.job_queue:
        return

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
# MEDIA WARNING
# ==========================================================

MEDIA_WARNING_SECONDS = 30


async def send_media_warning(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    user = update.effective_user

    if not user:
        return

    username = await get_bot_username(
        context
    )

    keyboard = None

    if username:

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🤖 Post with Melanated AZ Bot",
                        url=f"https://t.me/{username}",
                    )
                ]
            ]
        )

    warning_text = (
        "⚠️ Media Spoiler Required\n\n"
        f"{user.mention_html()}, your photo/video "
        "was removed because it was not marked as "
        "a spoiler.\n\n"
        "Please resend the media using Telegram's "
        "🚫 Spoiler option.\n\n"
        "You can also send it to the "
        "Melanated AZ Bot and let the bot "
        "handle the posting for you."
    )

    try:

        warning = await context.bot.send_message(
            chat_id=message.chat_id,
            text=warning_text,
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


# ==========================================================
# PRIVATE MEDIA WARNING
# ==========================================================

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

    keyboard = None

    if username:

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🤖 Open Melanated AZ Bot",
                        url=f"https://t.me/{username}",
                    )
                ]
            ]
        )

    text = (
        "👋 Hey! This is the Melanated AZ Bot "
        "from the Melanated AZ group.\n\n"
        "Your photo/video was removed from the group "
        "because Telegram's Spoiler option was not "
        "enabled.\n\n"
        "📸 How to post it correctly:\n\n"
        "1️⃣ Select your photo or video.\n"
        "2️⃣ Tap the ⋮ menu/options.\n"
        "3️⃣ Select Hide with Spoiler.\n"
        "4️⃣ Send the media.\n\n"
        "You can also send the media directly to me "
        "and use the bot to post it for you.\n\n"
        "⚠️ Media posted without the required spoiler "
        "may be removed automatically."
    )

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=text,
            reply_markup=keyboard,
        )

    except TelegramError as exc:

        logger.info(
            "Could not send private media warning "
            "to %s: %s",
            user.id,
            exc,
        )


# ==========================================================
# PHOTO
# ==========================================================

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if message.has_media_spoiler:

        logger.info(
            "Allowed spoilered photo | chat=%s | user=%s",
            message.chat_id,
            update.effective_user.id
            if update.effective_user
            else "unknown",
        )

        return

    logger.info(
        "Deleting non-spoiler photo | chat=%s | user=%s",
        message.chat_id,
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )

    try:

        await message.delete()

    except TelegramError:

        logger.exception(
            "Could not delete non-spoiler photo."
        )

    await send_media_warning(
        update,
        context,
    )

    await send_private_media_warning(
        update,
        context,
    )


# ==========================================================
# VIDEO
# ==========================================================

async def handle_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if message.has_media_spoiler:

        logger.info(
            "Allowed spoilered video | chat=%s | user=%s",
            message.chat_id,
            update.effective_user.id
            if update.effective_user
            else "unknown",
        )

        return

    logger.info(
        "Deleting non-spoiler video | chat=%s | user=%s",
        message.chat_id,
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )

    try:

        await message.delete()

    except TelegramError:

        logger.exception(
            "Could not delete non-spoiler video."
        )

    await send_media_warning(
        update,
        context,
    )

    await send_private_media_warning(
        update,
        context,
    )


# ==========================================================
# GIF / ANIMATION
# ==========================================================

async def handle_animation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    logger.info(
        "Allowed animation/GIF | chat=%s | user=%s",
        message.chat_id,
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )


# ==========================================================
# IMAGE DOCUMENT
# ==========================================================

async def handle_image_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message or not message.document:
        return

    mime_type = (
        message.document.mime_type or ""
    ).lower()

    if mime_type.startswith("image/"):

        logger.info(
            "Allowed image document | chat=%s | user=%s",
            message.chat_id,
            update.effective_user.id
            if update.effective_user
            else "unknown",
        )


# ==========================================================
# TEXT ROUTER
# ==========================================================

async def text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    # ------------------------------------------------------
    # ADMIN BIRTHDAY INPUT
    #
    # MUST COME FIRST.
    # ------------------------------------------------------

    handled = await admin_birthday_text_handler(
        update,
        context,
    )

    if handled:
        return

    # ------------------------------------------------------
    # USER BIRTHDAY INPUT
    # ------------------------------------------------------

    handled = await birthday_text_handler(
        update,
        context,
    )

    if handled:
        return


# ==========================================================
# START
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
        "👋 Welcome to Melanated AZ Bot!\n\n"
        "I'm the bot for the Melanated AZ community.\n\n"
        "I can help with:\n\n"
        "🎂 Birthdays\n"
        "🎟️ Raffles\n"
        "🔥 Truth or Dare\n"
        "🛡️ Media protection\n\n"
        "Birthday:\n"
        "/birthday\n\n"
        "Truth or Dare:\n"
        "/truthdare\n\n"
        "Truth:\n"
        "/truth\n\n"
        "Dare:\n"
        "/dare"
    )

    if is_admin(user.id):

        text += (
            "\n\n👑 ADMIN\n"
            "/admin"
        )

    await message.reply_text(
        text
    )


# ==========================================================
# ADMIN
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
# CANCEL COMMAND
# ==========================================================

async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if context.user_data.get(
        "awaiting_admin_birthday"
    ):

        await cancel_birthday_input(
            update,
            context,
        )

        return

    await update.effective_message.reply_text(
        "Nothing is currently waiting for input."
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
# BIRTHDAY CALLBACK
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
# TRUTH / DARE CALLBACK
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
# RAFFLE CALLBACK
# ==========================================================

async def raffle_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Raffle callback received: %s",
        data,
    )

    if data == "admin_start_raffle":

        await start_raffle(
            update,
            context,
        )

        return

    if data == "admin_status":

        await raffle_status(
            update,
            context,
        )

        return

    if data == "admin_entries":

        await raffle_entries(
            update,
            context,
        )

        return

    if data == "admin_pending":

        await pending_entries(
            update,
            context,
        )

        return

    if data == "admin_completed":

        await paid_entry(
            update,
            context,
        )

        return

    if data == "admin_draw":

        await draw_raffle(
            update,
            context,
        )

        return

    logger.debug(
        "Unclaimed raffle callback: %s",
        data,
    )


# ==========================================================
# DATABASE STARTUP
# ==========================================================

def database_startup_check():

    logger.info(
        "=========================================================="
    )

    logger.info(
        "Melanated AZ Bot - Database Startup Check"
    )

    try:

        stats = get_database_stats()

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

        integrity = check_database_integrity()

        logger.info(
            "Integrity      : %s",
            "OK" if integrity else "FAILED",
        )

        if not integrity:

            raise RuntimeError(
                "Database integrity check failed."
            )

    except Exception:

        logger.exception(
            "Database startup check failed."
        )

    logger.info(
        "=========================================================="
    )


# ==========================================================
# POST INIT
# ==========================================================

async def post_init(
    application: Application,
):

    logger.info(
        "Telegram application initialized."
    )

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

    if isinstance(error, BadRequest):

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

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "cancel",
            cancel_command,
        )
    )

    # ------------------------------------------------------
    # ADMIN
    # ------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "admin",
            admin_command,
        )
    )

    # ------------------------------------------------------
    # BIRTHDAY
    # ------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "birthday",
            birthday,
        )
    )

    application.add_handler(
        CommandHandler(
            "mybirthday",
            my_birthday,
        )
    )

    application.add_handler(
        CommandHandler(
            "removebirthday",
            remove_my_birthday,
        )
    )

    # ------------------------------------------------------
    # TRUTH OR DARE
    # ------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "truthdare",
            truth_dare_menu,
        )
    )

    application.add_handler(
        CommandHandler(
            "truth",
            truth,
        )
    )

    application.add_handler(
        CommandHandler(
            "dare",
            dare,
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
    # TRUTH / DARE CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            truth_dare_callback_router,
            pattern=r"^truthdare_",
        )
    )

    # ======================================================
    # RAFFLE CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_callback_router,
            pattern=(
                r"^(raffle_|enter_|pay_|payment_|"
                r"approve_|deny_|paid_|draw_|"
                r"reroll_|bonus_|remove_)"
            ),
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
    # TEXT INPUT
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_router,
        ),
        group=10,
    )

    # ======================================================
    # ERRORS
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

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
        name="flask-health-server",
    )

    flask_thread.start()

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
