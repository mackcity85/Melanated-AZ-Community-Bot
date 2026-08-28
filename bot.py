# ==========================================================
# Melanated AZ Bot
# bot.py
#
# COMPLETE PRODUCTION VERSION
#
# Features:
# - Persistent raffle system
# - Persistent birthday system
# - Media spoiler enforcement
# - Non-spoiler photos/videos removed
# - GIFs/animations allowed
# - Group media warning removed after 3 minutes
# - Private media instructions
# - Media repost with Telegram Spoiler enabled
# - Pending media expiration
# - Raffle user messages removed after 1 minute
# - Start Raffle button
# - FREE raffle support
# - Central raffle callback routing
# - Birthday callbacks
# - Birthday daily scheduler
# - Admin callbacks
# - Flask health server
#
# IMPORTANT:
# Raffle business logic remains in raffle.py
# Birthday business logic remains in birthday.py
# Birthday scheduling remains in birthday_scheduler.py
# Admin business logic remains in admin.py
# Database logic remains in raffle_database.py
#
# Existing database:
# /var/data/raffle.db
#
# This file does NOT delete, recreate, reset, or migrate
# the existing database.
# ==========================================================

import logging
import os
import threading
import time
import uuid
from typing import Optional

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from telegram.error import (
    BadRequest,
    Forbidden,
    TelegramError,
)

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
)

from admin import (
    admin_menu,
    admin_button,
)

import raffle

from birthday import (
    birthday,
    birthday_callback,
    birthday_text_handler,
    my_birthday,
    remove_my_birthday,
)

from birthday_scheduler import (
    start_birthday_scheduler,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

PORT = int(
    os.environ.get(
        "PORT",
        "10000",
    )
)

MEDIA_WARNING_SECONDS = 180

MEDIA_EXPIRATION_SECONDS = 600

RAFFLE_COUNTDOWN_INTERVAL = 60

RAFFLE_MESSAGE_DELETE_SECONDS = int(
    os.environ.get(
        "RAFFLE_MESSAGE_DELETE_SECONDS",
        "60",
    )
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

logging.getLogger("httpx").setLevel(
    logging.WARNING
)

logging.getLogger("telegram").setLevel(
    logging.INFO
)


# ==========================================================
# RAFFLE FUNCTION VALIDATION
# ==========================================================

REQUIRED_RAFFLE_FUNCTIONS = [
    "start_raffle",
    "raffle_private_start",
    "raffle_approval_button",
    "raffle_enter_button",
    "payment_button",
    "admin_payment_button",
    "enter_raffle",
    "paid_entry",
    "pending_entries",
    "raffle_status",
    "raffle_entries",
    "cancel_raffle",
    "draw_raffle",
    "reroll_raffle",
    "bonus_entry",
    "remove_raffle_entry",
    "raffle_callback_router",
    "update_raffle_countdown",
]


def load_raffle_functions():
    """
    Verify that raffle.py contains all functions
    required by bot.py.
    """

    missing = []
    loaded = {}

    for function_name in REQUIRED_RAFFLE_FUNCTIONS:

        function = getattr(
            raffle,
            function_name,
            None,
        )

        if not callable(function):

            missing.append(
                function_name
            )

        else:

            loaded[function_name] = function

    if missing:

        raise RuntimeError(
            "raffle.py is missing required functions: "
            + ", ".join(missing)
        )

    logger.info(
        "All required raffle functions loaded."
    )

    return loaded


RAFFLE = load_raffle_functions()


# ==========================================================
# OPTIONAL RAFFLE TEXT SETUP
# ==========================================================

handle_raffle_setup = getattr(
    raffle,
    "handle_raffle_setup",
    None,
)

if callable(handle_raffle_setup):

    logger.info(
        "Raffle text setup handler loaded."
    )

else:

    logger.warning(
        "raffle.handle_raffle_setup is not available."
    )


# ==========================================================
# FLASK HEALTH SERVER
# ==========================================================

health_app = Flask(
    "melanated_az_health"
)


@health_app.route(
    "/",
    methods=["GET"],
)
def health():

    return (
        "Melanated AZ Bot is running",
        200,
    )


@health_app.route(
    "/health",
    methods=["GET"],
)
def health_check():

    return (
        "OK",
        200,
    )


def run_health_server():

    logger.info(
        "Starting Flask health server on "
        "0.0.0.0:%s",
        PORT,
    )

    health_app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


# ==========================================================
# PENDING MEDIA
# ==========================================================

pending_media = {}


# ==========================================================
# GROUP MEDIA WARNING
# ==========================================================

GROUP_MEDIA_WARNING = """👑 Hi! I'm the MelanatedAZ Bot.

Chat: {chat_name}

🚫 Your photo/video was removed from {chat_name} because photos and videos must be posted using Telegram's Spoiler option.

📌 You have TWO options:

OPTION 1 — POST IT YOURSELF

1️⃣ Select the photo or video.
2️⃣ Tap the ⋮ / three dots menu.
3️⃣ Select Hide with Spoiler / Mark as Spoiler.
4️⃣ Send it to the {chat_name} chat.

OPTION 2 — LET MELANATEDAZ POST IT

👑 I saved your media and can repost it for you with Spoiler enabled.

⚠️ If MelanatedAZ reposts it, you cannot delete the MelanatedAZ repost.

⏱️ THIS MESSAGE WILL STAY UP FOR 3 MINUTES.

That gives you time to use the button below and have MelanatedAZ post your media.

👇 Tap the button below to have MelanatedAZ post your media.
"""


# ==========================================================
# PRIVATE MEDIA WARNING
# ==========================================================

PRIVATE_MEDIA_WARNING = """👑 Hi! I'm the MelanatedAZ Bot.

Chat: {chat_name}

🚫 Your photo/video was removed from {chat_name} because photos and videos must be posted using Telegram's Spoiler option.

📌 You have TWO options:

OPTION 1 — POST IT YOURSELF

1️⃣ Select the photo or video.
2️⃣ Tap the ⋮ / three dots menu.
3️⃣ Select Hide with Spoiler / Mark as Spoiler.
4️⃣ Send it to the {chat_name} chat.

OPTION 2 — LET MELANATEDAZ POST IT

👑 I saved your media and can repost it for you with Spoiler enabled.

⚠️ If MelanatedAZ reposts it, you cannot delete the MelanatedAZ repost.

👇 Tap the button below to have MelanatedAZ post your media.
"""


# ==========================================================
# MEDIA DEEP LINK KEYBOARD
# ==========================================================

def media_deep_link_keyboard(
    bot_username: str,
    token: str,
):

    deep_link = (
        f"https://t.me/"
        f"{bot_username}"
        f"?start=media_{token}"
    )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👑 Post with MelanatedAZ Bot",
                    url=deep_link,
                )
            ]
        ]
    )


# ==========================================================
# MEDIA REPOST KEYBOARD
# ==========================================================

def spoiler_keyboard(
    token: str,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👑 Post with MelanatedAZ",
                    callback_data=(
                        f"spoiler_repost:{token}"
                    ),
                )
            ]
        ]
    )


# ==========================================================
# SAFE MESSAGE DELETION
# ==========================================================

async def delete_message_safely(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id,
    message_id,
    description="message",
):

    if chat_id is None or message_id is None:

        logger.warning(
            "Cannot delete %s: missing chat_id/message_id.",
            description,
        )

        return False

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "Deleted %s | chat=%s | message=%s",
            description,
            chat_id,
            message_id,
        )

        return True

    except BadRequest as exc:

        logger.info(
            "Could not delete %s: %s",
            description,
            exc,
        )

    except Forbidden as exc:

        logger.warning(
            "Bot lacks permission to delete %s: %s",
            description,
            exc,
        )

    except TelegramError as exc:

        logger.warning(
            "Telegram error deleting %s: %s",
            description,
            exc,
        )

    except Exception:

        logger.exception(
            "Unexpected error deleting %s.",
            description,
        )

    return False


# ==========================================================
# DELETE GROUP WARNING
# ==========================================================

async def delete_group_warning(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    await delete_message_safely(
        context,
        data.get("chat_id"),
        data.get("message_id"),
        description="media warning",
    )


# ==========================================================
# DELETE RAFFLE USER MESSAGE
# ==========================================================

async def delete_raffle_user_message(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    await delete_message_safely(
        context,
        data.get("chat_id"),
        data.get("message_id"),
        description="raffle user message",
    )


# ==========================================================
# SCHEDULE RAFFLE MESSAGE DELETION
# ==========================================================

def schedule_raffle_message_deletion(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id,
    message_id,
):

    if not context.job_queue:

        logger.warning(
            "JobQueue unavailable. "
            "Could not schedule raffle message deletion."
        )

        return

    context.job_queue.run_once(
        delete_raffle_user_message,
        when=RAFFLE_MESSAGE_DELETE_SECONDS,
        data={
            "chat_id": chat_id,
            "message_id": message_id,
        },
        name=(
            f"delete_raffle_message_"
            f"{chat_id}_"
            f"{message_id}"
        ),
    )


# ==========================================================
# CLEAN EXPIRED MEDIA
# ==========================================================

async def cleanup_pending_media(
    context: ContextTypes.DEFAULT_TYPE,
):

    now = time.time()

    expired = []

    for token, media_info in list(
        pending_media.items()
    ):

        created_at = media_info.get(
            "created_at",
            now,
        )

        if (
            now - created_at
            > MEDIA_EXPIRATION_SECONDS
        ):

            expired.append(
                token
            )

    for token in expired:

        pending_media.pop(
            token,
            None,
        )

    if expired:

        logger.info(
            "Removed %s expired pending media item(s).",
            len(expired),
        )


# ==========================================================
# SEND MEDIA WITH SPOILER
# ==========================================================

async def send_media_with_spoiler(
    context: ContextTypes.DEFAULT_TYPE,
    media_info: dict,
):

    media_type = media_info.get("type")
    file_id = media_info.get("file_id")
    caption = media_info.get("caption")
    caption_entities = media_info.get("caption_entities")
    chat_id = media_info.get("chat_id")

    if not media_type:
        raise ValueError("Missing media type.")

    if not file_id:
        raise ValueError("Missing Telegram file ID.")

    if chat_id is None:
        raise ValueError("Missing original chat ID.")

    if media_type == "photo":

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=file_id,
            caption=caption,
            caption_entities=caption_entities,
            has_spoiler=True,
        )

        return

    if media_type == "video":

        await context.bot.send_video(
            chat_id=chat_id,
            video=file_id,
            caption=caption,
            caption_entities=caption_entities,
            has_spoiler=True,
        )

        return

    raise ValueError(
        f"Unsupported media type: {media_type}"
    )


# ==========================================================
# /START AND DEEP LINKS
# ==========================================================

async def media_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    args = context.args or []

    if not args:

        await message.reply_text(
            "👑 Hi! I'm the MelanatedAZ Bot.\n\n"
            "I help manage MelanatedAZ raffles, "
            "birthday announcements, and media moderation.\n\n"
            "Use the appropriate button or command "
            "from the Melanated AZ chat."
        )

        return

    payload = args[0].strip()

    if payload.startswith("media_"):

        token = payload[len("media_"):]

        media_info = pending_media.get(token)

        if not media_info:

            await message.reply_text(
                "⚠️ This media is no longer available.\n\n"
                "Please upload the photo/video again "
                "using Telegram's Spoiler option."
            )

            return

        if media_info.get("user_id") != user.id:

            await message.reply_text(
                "⚠️ This media belongs to another "
                "MelanatedAZ member."
            )

            return

        await message.reply_text(
            "👑 MelanatedAZ Bot\n\n"
            "I have your media ready.\n\n"
            "Tap the button below and I will repost "
            "your photo/video to the original "
            "Melanated AZ chat with Telegram's "
            "Spoiler option enabled.\n\n"
            "⚠️ If MelanatedAZ reposts your media, "
            "you cannot delete the MelanatedAZ repost.",
            reply_markup=spoiler_keyboard(token),
        )

        return

    if payload.startswith("raffle_"):

        await RAFFLE["raffle_private_start"](
            update,
            context,
        )

        return

    await RAFFLE["raffle_private_start"](
        update,
        context,
    )


# ==========================================================
# MEDIA REPOST CALLBACK
# ==========================================================

async def spoiler_repost_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:

        await query.answer()
        return

    data = query.data or ""

    if not data.startswith("spoiler_repost:"):

        await query.answer()
        return

    token = data.split(":", 1)[1]

    media_info = pending_media.get(token)

    if not media_info:

        await query.answer(
            "This media is no longer available.",
            show_alert=True,
        )

        return

    if media_info.get("user_id") != user.id:

        await query.answer(
            "This media belongs to another member.",
            show_alert=True,
        )

        return

    await query.answer(
        "MelanatedAZ is posting your media..."
    )

    try:

        await send_media_with_spoiler(
            context,
            media_info,
        )

        pending_media.pop(
            token,
            None,
        )

        try:

            await query.edit_message_text(
                "✅ MelanatedAZ posted your media.\n\n"
                "Your photo/video was reposted with "
                "Spoiler enabled.\n\n"
                "⚠️ Remember: you cannot delete the "
                "MelanatedAZ repost.\n\n"
                "👑 Thank you for following the "
                "MelanatedAZ media rules."
            )

        except TelegramError:
            pass

    except Exception:

        logger.exception(
            "Failed to repost media."
        )

        try:

            await query.edit_message_text(
                "⚠️ MelanatedAZ could not repost "
                "your media.\n\n"
                "Please try the button again."
            )

        except TelegramError:
            pass


# ==========================================================
# HANDLE NON-SPOILER MEDIA
# ==========================================================

async def handle_non_spoiler_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    media_type: str,
    file_id: str,
    caption: Optional[str] = None,
    caption_entities=None,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    chat_name = (
        message.chat.title
        or "MelanatedAZ"
    )

    token = uuid.uuid4().hex

    pending_media[token] = {
        "type": media_type,
        "file_id": file_id,
        "caption": caption,
        "caption_entities": caption_entities,
        "user_id": user.id,
        "username": user.username,
        "display_name": user.full_name,
        "chat_id": message.chat_id,
        "chat_name": chat_name,
        "created_at": time.time(),
    }

    try:

        await message.delete()

    except TelegramError:

        pending_media.pop(token, None)

        logger.warning(
            "Could not delete non-spoiler media."
        )

        return

    try:

        bot_user = await context.bot.get_me()

        bot_username = bot_user.username

        if not bot_username:
            raise RuntimeError(
                "Bot username unavailable."
            )

    except Exception:

        pending_media.pop(token, None)

        logger.exception(
            "Could not determine bot username."
        )

        return

    media_button = media_deep_link_keyboard(
        bot_username,
        token,
    )

    warning_message = None

    try:

        warning_message = await context.bot.send_message(
            chat_id=message.chat_id,
            text=GROUP_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
            reply_markup=media_button,
        )

    except TelegramError:

        logger.exception(
            "Could not send group media warning."
        )

    if warning_message and context.job_queue:

        context.job_queue.run_once(
            delete_group_warning,
            when=MEDIA_WARNING_SECONDS,
            data={
                "chat_id": warning_message.chat_id,
                "message_id": warning_message.message_id,
            },
            name=(
                f"delete_media_warning_"
                f"{warning_message.chat_id}_"
                f"{warning_message.message_id}"
            ),
        )

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=PRIVATE_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
            reply_markup=media_button,
        )

    except Forbidden:

        logger.info(
            "Could not privately message user=%s.",
            user.id,
        )

    except TelegramError as exc:

        logger.warning(
            "Could not send private media instructions: %s",
            exc,
        )


# ==========================================================
# MEDIA MODERATION
# ==========================================================

async def media_spoiler_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    user = update.effective_user

    if not user:
        return

    # GIFs / animations are allowed

    if message.animation:

        logger.info(
            "Allowed animation/GIF | user=%s | chat=%s",
            user.id,
            message.chat_id,
        )

        return

    # PHOTO

    if message.photo:

        if message.has_media_spoiler:

            logger.info(
                "Allowed spoiler photo | user=%s | chat=%s",
                user.id,
                message.chat_id,
            )

            return

        photo = message.photo[-1]

        await handle_non_spoiler_media(
            update,
            context,
            "photo",
            photo.file_id,
            message.caption,
            message.caption_entities,
        )

        return

    # VIDEO

    if message.video:

        if message.has_media_spoiler:

            logger.info(
                "Allowed spoiler video | user=%s | chat=%s",
                user.id,
                message.chat_id,
            )

            return

        video = message.video

        await handle_non_spoiler_media(
            update,
            context,
            "video",
            video.file_id,
            message.caption,
            message.caption_entities,
        )

        return


# ==========================================================
# TEXT HANDLER
# ==========================================================

async def text_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    try:

        birthday_handled = await birthday_text_handler(
            update,
            context,
        )

        if birthday_handled:
            return

    except Exception:

        logger.exception(
            "Birthday text handler failed."
        )

    if callable(handle_raffle_setup):

        try:

            handled = await handle_raffle_setup(
                update,
                context,
            )

            if handled:

                schedule_raffle_message_deletion(
                    context,
                    message.chat_id,
                    message.message_id,
                )

                return

        except Exception:

            logger.exception(
                "Raffle text setup handler failed."
            )


# ==========================================================
# START RAFFLE BUTTON
#
# THIS HANDLER IS INTENTIONALLY SEPARATE FROM THE
# GENERAL RAFFLE CALLBACK ROUTER.
#
# This guarantees that the Start Raffle button
# actually starts the raffle setup flow.
# ==========================================================

async def start_raffle_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:

        await query.answer()
        return

    # ------------------------------------------------------
    # ADMIN CHECK
    # ------------------------------------------------------

    admin_ids = set()

    for admin_id in ADMIN_IDS or []:

        try:

            admin_ids.add(
                int(admin_id)
            )

        except (TypeError, ValueError):

            continue

    if admin_ids and user.id not in admin_ids:

        await query.answer(
            "You are not authorized to start a raffle.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # START RAFFLE SETUP
    # ------------------------------------------------------

    context.user_data[
        "awaiting_raffle_setup"
    ] = True

    context.user_data.pop(
        "raffle_setup",
        None,
    )

    context.user_data.pop(
        "pending_raffle",
        None,
    )

    await query.answer(
        "Raffle setup started."
    )

    prompt = (
        "🎟️ START RAFFLE\n\n"
        "Enter the raffle information in this format:\n\n"
        "$100 Cash Prize | $5\n\n"
        "FREE raffles are also supported:\n\n"
        "$100 Cash Prize | FREE\n\n"
        "Example:\n"
        "$250 Cash Prize | $10\n\n"
        "The first part is the prize.\n"
        "The second part is the entry price.\n\n"
        "Type the information now."
    )

    try:

        if query.message:

            await query.message.reply_text(
                prompt
            )

        else:

            await context.bot.send_message(
                chat_id=user.id,
                text=prompt,
            )

        logger.info(
            "Start Raffle button activated | user=%s",
            user.id,
        )

    except TelegramError as exc:

        logger.warning(
            "Could not send raffle setup prompt: %s",
            exc,
        )


# ==========================================================
# CENTRAL RAFFLE CALLBACK ROUTER
# ==========================================================

async def raffle_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    normalized = (
        data
        .strip()
        .lower()
        .replace("-", "_")
    )

    logger.info(
        "Raffle callback received | user=%s | data=%s",
        update.effective_user.id
        if update.effective_user
        else "unknown",
        data,
    )

    # ------------------------------------------------------
    # ALL KNOWN START RAFFLE CALLBACK VALUES
    # ------------------------------------------------------

    start_raffle_callbacks = {
        "start_raffle",
        "raffle_start",
        "raffle_start_raffle",
        "startraffle",
        "raffle_start_button",
        "start_raffle_button",
        "startraffle",
        "raffle:start",
        "raffle_start_now",
    }

    if normalized in start_raffle_callbacks:

        await start_raffle_button(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # CATCH START RAFFLE VARIATIONS
    # ------------------------------------------------------

    if (
        "start" in normalized
        and "raffle" in normalized
    ):

        await start_raffle_button(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # SEND ALL OTHER RAFFLE CALLBACKS TO raffle.py
    # ------------------------------------------------------

    try:

        await RAFFLE[
            "raffle_callback_router"
        ](
            update,
            context,
        )

    except Exception as exc:

        logger.exception(
            "Raffle callback router failed | "
            "data=%s | error=%s",
            data,
            exc,
        )

        try:

            await query.answer(
                "Something went wrong. Please try again.",
                show_alert=True,
            )

        except Exception:
            pass


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
        (BadRequest, Forbidden),
    ):

        logger.warning(
            "Telegram request error: %s",
            error,
        )

        return

    logger.error(
        "Unhandled Telegram exception: %r",
        error,
        exc_info=True,
    )


# ==========================================================
# REGISTER HANDLERS
# ==========================================================

def register_handlers(
    application: Application,
):

    # ------------------------------------------------------
    # START
    # ------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            media_start,
        )
    )

    # ------------------------------------------------------
    # ADMIN
    # ------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "admin",
            admin_menu,
        )
    )

    # ------------------------------------------------------
    # RAFFLE COMMANDS
    # ------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "startraffle",
            RAFFLE["start_raffle"],
        )
    )

    application.add_handler(
        CommandHandler(
            [
                "raffle",
                "enterraffle",
            ],
            RAFFLE["enter_raffle"],
        )
    )

    application.add_handler(
        CommandHandler(
            "paid",
            RAFFLE["paid_entry"],
        )
    )

    application.add_handler(
        CommandHandler(
            [
                "status",
                "rafflestatus",
            ],
            RAFFLE["raffle_status"],
        )
    )

    application.add_handler(
        CommandHandler(
            "entries",
            RAFFLE["raffle_entries"],
        )
    )

    application.add_handler(
        CommandHandler(
            "pending",
            RAFFLE["pending_entries"],
        )
    )

    application.add_handler(
        CommandHandler(
            "cancelraffle",
            RAFFLE["cancel_raffle"],
        )
    )

    application.add_handler(
        CommandHandler(
            "draw",
            RAFFLE["draw_raffle"],
        )
    )

    application.add_handler(
        CommandHandler(
            "reroll",
            RAFFLE["reroll_raffle"],
        )
    )

    application.add_handler(
        CommandHandler(
            "bonusentry",
            RAFFLE["bonus_entry"],
        )
    )

    application.add_handler(
        CommandHandler(
            "removeentry",
            RAFFLE["remove_raffle_entry"],
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
    # RAFFLE CALLBACKS
    #
    # IMPORTANT:
    # This handler MUST NOT capture birthday,
    # admin, or spoiler callbacks.
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            raffle_callback_handler,
            pattern=(
                r"^(?!birthday_)"
                r"(?!admin_)"
                r"(?!spoiler_repost:)"
                r".+"
            ),
        ),
        group=0,
    )

    # ------------------------------------------------------
    # BIRTHDAY CALLBACKS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            birthday_callback,
            pattern=r"^birthday_(enter|view|remove)$",
        ),
        group=1,
    )

    # ------------------------------------------------------
    # ADMIN CALLBACKS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            admin_button,
            pattern=r"^admin_",
        ),
        group=1,
    )

    # ------------------------------------------------------
    # MEDIA REPOST CALLBACKS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            spoiler_repost_button,
            pattern=r"^spoiler_repost:",
        ),
        group=1,
    )

    # ------------------------------------------------------
    # MEDIA
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.PHOTO
            | filters.VIDEO
            | filters.ANIMATION,
            media_spoiler_handler,
        )
    )

    # ------------------------------------------------------
    # TEXT
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message_handler,
        )
    )

    # ------------------------------------------------------
    # ERROR HANDLER
    # ------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "All Telegram handlers registered."
    )

    logger.info(
        "Start Raffle button handler enabled."
    )

    logger.info(
        "Central raffle callback router registered."
    )

    logger.info(
        "Birthday handlers registered."
    )


# ==========================================================
# POST INITIALIZATION
# ==========================================================

async def post_init(
    application: Application,
):

    logger.info(
        "Telegram application initialization complete."
    )

    # ------------------------------------------------------
    # VERIFY BOT
    # ------------------------------------------------------

    try:

        bot_user = await application.bot.get_me()

        logger.info(
            "Connected to Telegram as @%s",
            bot_user.username,
        )

    except Exception:

        logger.exception(
            "Unable to verify Telegram bot identity."
        )

        raise

    # ------------------------------------------------------
    # MEDIA CLEANUP
    # ------------------------------------------------------

    if application.job_queue:

        application.job_queue.run_repeating(
            cleanup_pending_media,
            interval=300,
            first=300,
            name="pending_media_cleanup",
        )

        logger.info(
            "Pending media cleanup scheduler started."
        )

    else:

        logger.warning(
            "JobQueue unavailable. "
            "Media cleanup scheduler disabled."
        )

    # ------------------------------------------------------
    # RAFFLE COUNTDOWN
    # ------------------------------------------------------

    if application.job_queue:

        application.job_queue.run_repeating(
            RAFFLE[
                "update_raffle_countdown"
            ],
            interval=RAFFLE_COUNTDOWN_INTERVAL,
            first=10,
            name="raffle_countdown",
        )

        logger.info(
            "Raffle countdown scheduler started."
        )

    else:

        logger.warning(
            "JobQueue unavailable. "
            "Raffle countdown scheduler disabled."
        )


# ==========================================================
# MAIN
# ==========================================================

def main():

    logger.info(
        "=================================================="
    )

    logger.info(
        "🔥 Starting Melanated AZ Bot"
    )

    logger.info(
        "=================================================="
    )

    # ------------------------------------------------------
    # CONFIG VALIDATION
    # ------------------------------------------------------

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN is missing."
        )

    logger.info(
        "Admin IDs loaded: %s",
        ADMIN_IDS,
    )

    logger.info(
        "Raffle Chat ID: %s",
        RAFFLE_CHAT_ID,
    )

    logger.info(
        "Health server port: %s",
        PORT,
    )

    logger.info(
        "Media warning deletion: %s seconds",
        MEDIA_WARNING_SECONDS,
    )

    logger.info(
        "Raffle message deletion: %s seconds",
        RAFFLE_MESSAGE_DELETE_SECONDS,
    )

    # ------------------------------------------------------
    # HEALTH SERVER
    # ------------------------------------------------------

    health_thread = threading.Thread(
        target=run_health_server,
        name="FlaskHealthServer",
        daemon=True,
    )

    health_thread.start()

    logger.info(
        "🌐 Flask health server started."
    )

    # ------------------------------------------------------
    # TELEGRAM APPLICATION
    # ------------------------------------------------------

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ------------------------------------------------------
    # REGISTER HANDLERS
    # ------------------------------------------------------

    register_handlers(
        application
    )

    # ------------------------------------------------------
    # BIRTHDAY SCHEDULER
    # ------------------------------------------------------

    try:

        start_birthday_scheduler(
            application
        )

        logger.info(
            "🎂 Birthday scheduler started."
        )

    except Exception:

        logger.exception(
            "Birthday scheduler failed to start."
        )

        raise

    # ------------------------------------------------------
    # START POLLING
    # ------------------------------------------------------

    logger.info(
        "📡 Starting Telegram polling..."
    )

    logger.info(
        "Bot is now online."
    )

    application.run_polling(
        drop_pending_updates=False,
        allowed_updates=Update.ALL_TYPES,
        close_loop=True,
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        logger.info(
            "Bot stopped by keyboard interrupt."
        )

    except Exception:

        logger.exception(
            "Fatal bot startup/runtime error."
        )

        raise
