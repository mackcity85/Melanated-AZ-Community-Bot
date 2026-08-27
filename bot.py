# ==========================================================
# Melanated AZ Bot
# bot.py
#
# COMPLETE PRODUCTION REPLACEMENT
#
# Responsibilities:
#   - Start Telegram bot
#   - Start Flask health endpoint
#   - Media spoiler enforcement
#   - Birthday commands/scheduler
#   - Raffle command/callback routing
#   - Admin command/callback routing
#   - Safe Telegram application lifecycle
#   - Centralized logging/error handling
#
# IMPORTANT:
#   - Raffle business logic remains in raffle.py
#   - Birthday business logic remains in birthday.py
#   - Admin business logic remains in admin.py
#
# MEDIA:
#   - Photos MUST use Telegram Spoiler
#   - Videos MUST use Telegram Spoiler
#   - Non-spoiler photos/videos are deleted
#   - User receives instructions
#   - User receives a button to repost through the bot
#   - Bot reposts with Spoiler enabled
#   - GIFs/animations are allowed
#   - Image documents are NOT treated as spoiler media
#
# ==========================================================

import logging
import os
import threading
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

# Maximum amount of time an unsent media item stays in memory.
MEDIA_EXPIRATION_SECONDS = 600


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
]


def load_raffle_functions():
    """
    Validate all raffle functions before Telegram polling starts.
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
        "raffle.handle_raffle_setup is not available. "
        "Raffle text setup handler is disabled."
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
        "Starting Flask health server on 0.0.0.0:%s",
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
#
# IMPORTANT:
# This dictionary is process memory only.
#
# Telegram file IDs are used, so media does not need to be
# downloaded to disk.
#
# This is intentionally temporary. Raffle/birthday data is
# handled by their respective database modules.
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
# DELETE GROUP WARNING
# ==========================================================

async def delete_group_warning(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    chat_id = data.get(
        "chat_id"
    )

    message_id = data.get(
        "message_id"
    )

    if chat_id is None or message_id is None:

        logger.warning(
            "Warning deletion job missing IDs."
        )

        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "Deleted media warning | "
            "chat=%s | message=%s",
            chat_id,
            message_id,
        )

    except BadRequest as exc:

        logger.info(
            "Media warning already deleted or unavailable | "
            "chat=%s | message=%s | %s",
            chat_id,
            message_id,
            exc,
        )

    except Forbidden as exc:

        logger.warning(
            "Bot lacks permission to delete warning | "
            "chat=%s | message=%s | %s",
            chat_id,
            message_id,
            exc,
        )

    except TelegramError as exc:

        logger.warning(
            "Telegram error deleting warning | "
            "chat=%s | message=%s | %s",
            chat_id,
            message_id,
            exc,
        )

    except Exception as exc:

        logger.exception(
            "Unexpected error deleting media warning | "
            "chat=%s | message=%s | %s",
            chat_id,
            message_id,
            exc,
        )


# ==========================================================
# CLEAN EXPIRED MEDIA
# ==========================================================

async def cleanup_pending_media(
    context: ContextTypes.DEFAULT_TYPE,
):

    import time

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

    media_type = media_info.get(
        "type"
    )

    file_id = media_info.get(
        "file_id"
    )

    caption = media_info.get(
        "caption"
    )

    caption_entities = media_info.get(
        "caption_entities"
    )

    chat_id = media_info.get(
        "chat_id"
    )

    if not media_type:

        raise ValueError(
            "Missing media type."
        )

    if not file_id:

        raise ValueError(
            "Missing Telegram file ID."
        )

    if chat_id is None:

        raise ValueError(
            "Missing original chat ID."
        )

    # ------------------------------------------------------
    # PHOTO
    # ------------------------------------------------------

    if media_type == "photo":

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=file_id,
            caption=caption,
            caption_entities=caption_entities,
            has_spoiler=True,
        )

        return

    # ------------------------------------------------------
    # VIDEO
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # NORMAL /START
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # MEDIA DEEP LINK
    # ------------------------------------------------------

    if payload.startswith(
        "media_"
    ):

        token = payload[
            len("media_"):
        ]

        media_info = pending_media.get(
            token
        )

        if not media_info:

            await message.reply_text(
                "⚠️ This media is no longer available.\n\n"
                "Please upload the photo/video again "
                "using Telegram's Spoiler option."
            )

            return

        if media_info.get(
            "user_id"
        ) != user.id:

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
            reply_markup=spoiler_keyboard(
                token
            ),
        )

        return

    # ------------------------------------------------------
    # RAFFLE DEEP LINK
    # ------------------------------------------------------

    if payload.startswith(
        "raffle_"
    ):

        await RAFFLE[
            "raffle_private_start"
        ](
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # FALLBACK
    # ------------------------------------------------------

    await RAFFLE[
        "raffle_private_start"
    ](
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

    if not data.startswith(
        "spoiler_repost:"
    ):

        await query.answer()

        return

    token = data.split(
        ":",
        1,
    )[1]

    media_info = pending_media.get(
        token
    )

    if not media_info:

        await query.answer(
            "This media is no longer available.",
            show_alert=True,
        )

        return

    if media_info.get(
        "user_id"
    ) != user.id:

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

        # Only remove from memory AFTER the
        # Telegram repost succeeds.

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

        except TelegramError as exc:

            logger.warning(
                "Media posted successfully but "
                "confirmation message could not be edited: %s",
                exc,
            )

    except Exception as exc:

        logger.exception(
            "Failed to repost media with spoiler | "
            "user=%s | token=%s | error=%s",
            user.id,
            token,
            exc,
        )

        try:

            await query.edit_message_text(
                "⚠️ MelanatedAZ could not repost "
                "your media.\n\n"
                "Your saved media has not been removed "
                "from the pending queue.\n\n"
                "Please try the button again. If it "
                "continues to fail, upload the media "
                "again using Telegram's Spoiler option."
            )

        except TelegramError:

            logger.warning(
                "Could not update media repost error message."
            )


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

    import time

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

    logger.info(
        "Saved non-spoiler media | "
        "type=%s | user=%s | chat=%s | token=%s",
        media_type,
        user.id,
        message.chat_id,
        token,
    )

    # ------------------------------------------------------
    # DELETE ORIGINAL
    # ------------------------------------------------------

    try:

        await message.delete()

        logger.info(
            "Deleted non-spoiler media | "
            "chat=%s | message=%s",
            message.chat_id,
            message.message_id,
        )

    except Forbidden as exc:

        logger.warning(
            "Bot does not have permission to delete "
            "non-spoiler media | chat=%s | error=%s",
            message.chat_id,
            exc,
        )

        pending_media.pop(
            token,
            None,
        )

        return

    except TelegramError as exc:

        logger.warning(
            "Could not delete non-spoiler media | "
            "chat=%s | message=%s | error=%s",
            message.chat_id,
            message.message_id,
            exc,
        )

        pending_media.pop(
            token,
            None,
        )

        return

    # ------------------------------------------------------
    # GET BOT USERNAME
    # ------------------------------------------------------

    try:

        bot_user = await context.bot.get_me()

        bot_username = bot_user.username

        if not bot_username:

            raise RuntimeError(
                "Bot username unavailable."
            )

    except Exception as exc:

        logger.exception(
            "Could not determine bot username: %s",
            exc,
        )

        pending_media.pop(
            token,
            None,
        )

        return

    media_button = (
        media_deep_link_keyboard(
            bot_username,
            token,
        )
    )

    # ------------------------------------------------------
    # GROUP WARNING
    # ------------------------------------------------------

    warning_message = None

    try:

        warning_message = (
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=GROUP_MEDIA_WARNING.format(
                    chat_name=chat_name,
                ),
                reply_markup=media_button,
            )
        )

        logger.info(
            "Sent media warning | "
            "chat=%s | message=%s",
            message.chat_id,
            warning_message.message_id,
        )

    except TelegramError as exc:

        logger.warning(
            "Could not send group media warning | "
            "error=%s",
            exc,
        )

    # ------------------------------------------------------
    # SCHEDULE WARNING DELETION
    # ------------------------------------------------------

    if (
        warning_message
        and context.job_queue
    ):

        context.job_queue.run_once(
            delete_group_warning,
            when=MEDIA_WARNING_SECONDS,
            data={
                "chat_id": warning_message.chat_id,
                "message_id": warning_message.message_id,
            },
        )

    # ------------------------------------------------------
    # PRIVATE MESSAGE
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=PRIVATE_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
            reply_markup=media_button,
        )

        logger.info(
            "Sent private media instructions | "
            "user=%s",
            user.id,
        )

    except Forbidden:

        logger.info(
            "Could not privately message user=%s. "
            "User may not have started the bot.",
            user.id,
        )

    except TelegramError as exc:

        logger.warning(
            "Could not send private media instructions | "
            "user=%s | error=%s",
            user.id,
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

    # ------------------------------------------------------
    # GIFS / ANIMATIONS
    #
    # GIFs are explicitly allowed.
    # ------------------------------------------------------

    if message.animation:

        logger.info(
            "Allowed animation/GIF | user=%s | chat=%s",
            user.id,
            message.chat_id,
        )

        return

    # ------------------------------------------------------
    # PHOTO
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # VIDEO
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # BIRTHDAY TEXT HANDLER
    # ------------------------------------------------------

    try:

        birthday_handled = (
            await birthday_text_handler(
                update,
                context,
            )
        )

        if birthday_handled:
            return

    except Exception:

        logger.exception(
            "Birthday text handler failed."
        )

    # ------------------------------------------------------
    # RAFFLE TEXT SETUP
    # ------------------------------------------------------

    if callable(
        handle_raffle_setup
    ):

        try:

            handled = (
                await handle_raffle_setup(
                    update,
                    context,
                )
            )

            if handled:
                return

        except Exception:

            logger.exception(
                "Raffle text setup handler failed."
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
        exc_info=(
            type(error),
            error,
            error.__traceback__
            if error
            else None,
        ),
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
    # BIRTHDAY CALLBACKS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            birthday_callback,
            pattern=r"^birthday_(enter|view|remove)$",
        )
    )

    # ------------------------------------------------------
    # ADMIN CALLBACKS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            admin_button,
            pattern=r"^admin_",
        )
    )

    # ------------------------------------------------------
    # RAFFLE APPROVAL
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            RAFFLE["raffle_approval_button"],
            pattern=r"^raffle_(?:approve|cancel)_\d+$",
        )
    )

    # ------------------------------------------------------
    # RAFFLE ENTER
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            RAFFLE["raffle_enter_button"],
            pattern=r"^raffle_enter_\d+$",
        )
    )

    # ------------------------------------------------------
    # ADMIN PAYMENT
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            RAFFLE["admin_payment_button"],
            pattern=r"^(approve|deny)_\d+$",
        )
    )

    # ------------------------------------------------------
    # PAYMENT
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            RAFFLE["payment_button"],
            pattern=r"^raffle_(cashapp|zelle)_\d+$",
        )
    )

    # ------------------------------------------------------
    # MEDIA REPOST
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            spoiler_repost_button,
            pattern=r"^spoiler_repost:",
        )
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
    # PENDING MEDIA CLEANUP
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
    # STARTUP CONFIG VALIDATION
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
    #
    # IMPORTANT:
    # Do NOT use drop_pending_updates=True.
    #
    # This prevents legitimate updates waiting while
    # Render restarts/deploys from being silently discarded.
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
