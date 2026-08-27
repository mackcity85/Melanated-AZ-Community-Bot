# ==========================================================
# Melanated AZ Bot
# bot.py
#
# COMPLETE REPLACEMENT
#
# Media:
#   - Photos/videos MUST use Telegram Spoiler
#   - Non-spoiler media is deleted immediately
#   - Group warning remains for 3 minutes
#   - Group warning includes Post with MelanatedAZ Bot button
#   - Private message includes the same button when possible
#   - GIFs/animations are allowed
#
# Birthday:
#   - /birthday
#   - /mybirthday
#   - /removebirthday
#
# Raffle:
#   - Existing raffle system preserved
# ==========================================================

import logging
import os
import threading
import uuid

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

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
)

from admin import (
    admin_menu,
    admin_button,
)

from raffle import (
    start_raffle,
    handle_raffle_setup,
    raffle_private_start,
    raffle_approval_button,
    raffle_enter_button,
    payment_button,
    admin_payment_button,
    enter_raffle,
    paid_entry,
    pending_entries,
    raffle_status,
    raffle_entries,
    cancel_raffle,
    draw_raffle,
    reroll_raffle,
    bonus_entry,
    remove_raffle_entry,
)

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
# LOGGING
# ==========================================================

logging.basicConfig(
    format=(
        "%(asctime)s - %(name)s - "
        "%(levelname)s - %(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ==========================================================
# FLASK HEALTH SERVER
# ==========================================================

app = Flask(__name__)


@app.route("/")
def health():
    return (
        "Melanated AZ Bot is running",
        200,
    )


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            10000,
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ==========================================================
# PENDING MEDIA
#
# Media is temporarily stored here while the member decides
# whether MelanatedAZ should repost it.
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
# MEDIA DEEP LINK
#
# The group button opens the bot with:
#
# /start media_TOKEN
#
# The member does NOT have to enter a username or user ID.
# ==========================================================

def media_deep_link_keyboard(
    bot_username,
    token,
):

    deep_link = (
        f"https://t.me/{bot_username}"
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
# PRIVATE REPOST BUTTON
# ==========================================================

def spoiler_keyboard(token):

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
#
# Runs 180 seconds after the warning is created.
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
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "Deleted group media warning after 3 minutes | "
            "chat=%s | message=%s",
            chat_id,
            message_id,
        )

    except Exception as exc:

        logger.warning(
            "Unable to delete group media warning | "
            "chat=%s | message=%s | error=%s",
            chat_id,
            message_id,
            exc,
        )


# ==========================================================
# SEND MEDIA WITH SPOILER
# ==========================================================

async def send_media_with_spoiler(
    context,
    media_info,
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
            "Missing media type"
        )

    if not file_id:
        raise ValueError(
            "Missing Telegram file ID"
        )

    if chat_id is None:
        raise ValueError(
            "Missing original chat ID"
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
# START / DEEP LINKS
# ==========================================================

async def media_start(
    update,
    context,
):

    user = update.effective_user

    if not user:
        return

    message = update.effective_message

    if not message:
        return

    args = context.args or []

    # ======================================================
    # NORMAL /START
    # ======================================================

    if not args:

        await message.reply_text(
            "👑 **Hi! I'm the MelanatedAZ Bot.**\n\n"
            "I help manage MelanatedAZ raffles, "
            "birthday announcements, and media moderation.\n\n"
            "Use the appropriate button or command "
            "from the Melanated AZ chat.",
            parse_mode="Markdown",
        )

        return

    payload = args[0]

    # ======================================================
    # MEDIA DEEP LINK
    # ======================================================

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

        # --------------------------------------------------
        # Verify the person opening the link owns the media
        # --------------------------------------------------

        if media_info.get(
            "user_id"
        ) != user.id:

            await message.reply_text(
                "⚠️ This media belongs to another "
                "MelanatedAZ member."
            )

            return

        # --------------------------------------------------
        # Give member repost option
        # --------------------------------------------------

        await message.reply_text(
            "👑 **MelanatedAZ Bot**\n\n"
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
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RAFFLE DEEP LINK
    # ======================================================

    if payload.startswith(
        "raffle_"
    ):

        await raffle_private_start(
            update,
            context,
        )

        return

    # ======================================================
    # FALLBACK
    # ======================================================

    await raffle_private_start(
        update,
        context,
    )


# ==========================================================
# MEDIA REPOST CALLBACK
# ==========================================================

async def spoiler_repost_button(
    update,
    context,
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

    # ======================================================
    # SECURITY
    # ======================================================

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

        # --------------------------------------------------
        # Remove saved media after successful repost
        # --------------------------------------------------

        pending_media.pop(
            token,
            None,
        )

        await query.edit_message_text(
            "✅ **MelanatedAZ posted your media.**\n\n"
            "Your photo/video was reposted with "
            "Spoiler enabled.\n\n"
            "⚠️ Remember: you cannot delete the "
            "MelanatedAZ repost.\n\n"
            "👑 Thank you for following the "
            "MelanatedAZ media rules.",
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Failed to repost media with spoiler"
        )

        await query.edit_message_text(
            "⚠️ **MelanatedAZ could not repost "
            "your media.**\n\n"
            "Please upload it again and select "
            "Hide with Spoiler / Mark as Spoiler.",
            parse_mode="Markdown",
        )


# ==========================================================
# HANDLE NON-SPOILER MEDIA
# ==========================================================

async def handle_non_spoiler_media(
    update,
    context,
    media_type,
    file_id,
    caption=None,
    caption_entities=None,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    # ======================================================
    # CHAT NAME
    # ======================================================

    chat_name = (
        message.chat.title
        or "MelanatedAZ"
    )

    # ======================================================
    # UNIQUE TOKEN
    # ======================================================

    token = uuid.uuid4().hex

    # ======================================================
    # SAVE MEDIA
    # ======================================================

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
    }

    logger.info(
        "Saved non-spoiler media | "
        "user=%s | chat=%s | token=%s",
        user.id,
        message.chat_id,
        token,
    )

    # ======================================================
    # DELETE ORIGINAL MEDIA
    # ======================================================

    try:

        await message.delete()

        logger.info(
            "Deleted non-spoiler media | "
            "chat=%s | message=%s",
            message.chat_id,
            message.message_id,
        )

    except Exception as exc:

        logger.warning(
            "Failed to delete non-spoiler media | "
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

    # ======================================================
    # GET BOT USERNAME
    # ======================================================

    try:

        bot_user = await context.bot.get_me()

        bot_username = bot_user.username

        if not bot_username:

            raise ValueError(
                "Bot username unavailable"
            )

    except Exception:

        logger.exception(
            "Unable to determine bot username"
        )

        pending_media.pop(
            token,
            None,
        )

        return

    # ======================================================
    # CREATE THE SAME BUTTON FOR BOTH PLACES
    # ======================================================

    media_button = (
        media_deep_link_keyboard(
            bot_username,
            token,
        )
    )

    # ======================================================
    # SEND GROUP WARNING
    #
    # IMPORTANT:
    # The button is attached directly to the GROUP message.
    # ======================================================

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
            "Sent group media warning with button | "
            "chat=%s | message=%s",
            message.chat_id,
            warning_message.message_id,
        )

    except Exception as exc:

        logger.warning(
            "Failed to send group media warning | "
            "error=%s",
            exc,
        )

    # ======================================================
    # KEEP GROUP WARNING FOR 3 MINUTES
    #
    # 180 seconds = 3 minutes
    # ======================================================

    if (
        warning_message
        and context.job_queue
    ):

        context.job_queue.run_once(
            delete_group_warning,
            when=180,
            data={
                "chat_id": (
                    warning_message.chat_id
                ),
                "message_id": (
                    warning_message.message_id
                ),
            },
        )

        logger.info(
            "Group warning scheduled for deletion "
            "in 180 seconds | chat=%s | message=%s",
            warning_message.chat_id,
            warning_message.message_id,
        )

    # ======================================================
    # SEND PRIVATE MESSAGE
    #
    # This is attempted, but it is NOT required for the
    # workflow because the group button is also available.
    # ======================================================

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

    except Exception as exc:

        logger.info(
            "Could not send private media instructions "
            "to user %s. Group button remains available. "
            "Reason: %s",
            user.id,
            exc,
        )


# ==========================================================
# MEDIA SPOILER HANDLER
# ==========================================================

async def media_spoiler_handler(
    update,
    context,
):

    message = update.effective_message

    if not message:
        return

    user = update.effective_user

    if not user:
        return

    # ======================================================
    # GIFS / ANIMATIONS ARE ALLOWED
    # ======================================================

    if message.animation:
        return

    # ======================================================
    # PHOTO
    # ======================================================

    if message.photo:

        # Already spoilered = ALLOW
        if message.has_media_spoiler:
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

    # ======================================================
    # VIDEO
    # ======================================================

    if message.video:

        # Already spoilered = ALLOW
        if message.has_media_spoiler:
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
    update,
    context,
):

    # ======================================================
    # BIRTHDAY HAS PRIORITY
    # ======================================================

    birthday_handled = (
        await birthday_text_handler(
            update,
            context,
        )
    )

    if birthday_handled:
        return

    # ======================================================
    # RAFFLE SETUP
    # ======================================================

    handled = await handle_raffle_setup(
        update,
        context,
    )

    if handled:
        return


# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update,
    context,
):

    logger.error(
        "Exception while processing update",
        exc_info=context.error,
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    logger.info(
        "🔥 Melanated AZ Bot Started"
    )

    logger.info(
        "Loaded Admin IDs: %s",
        ADMIN_IDS,
    )

    logger.info(
        "Raffle Chat ID: %s",
        RAFFLE_CHAT_ID,
    )

    # ======================================================
    # FLASK
    # ======================================================

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )

    flask_thread.start()

    logger.info(
        "🌐 Flask health server started"
    )

    # ======================================================
    # TELEGRAM APPLICATION
    # ======================================================

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ======================================================
    # /START
    # ======================================================

    application.add_handler(
        CommandHandler(
            "start",
            media_start,
        )
    )

    # ======================================================
    # ADMIN
    # ======================================================

    application.add_handler(
        CommandHandler(
            "admin",
            admin_menu,
        )
    )

    # ======================================================
    # RAFFLE COMMANDS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            [
                "raffle",
                "enterraffle",
            ],
            enter_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "paid",
            paid_entry,
        )
    )

    application.add_handler(
        CommandHandler(
            [
                "status",
                "rafflestatus",
            ],
            raffle_status,
        )
    )

    application.add_handler(
        CommandHandler(
            "entries",
            raffle_entries,
        )
    )

    application.add_handler(
        CommandHandler(
            "pending",
            pending_entries,
        )
    )

    application.add_handler(
        CommandHandler(
            "cancelraffle",
            cancel_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "draw",
            draw_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "reroll",
            reroll_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "bonusentry",
            bonus_entry,
        )
    )

    application.add_handler(
        CommandHandler(
            "removeentry",
            remove_raffle_entry,
        )
    )

    # ======================================================
    # BIRTHDAY COMMANDS
    # ======================================================

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

    # ======================================================
    # BIRTHDAY CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            birthday_callback,
            pattern=r"^birthday_(enter|view|remove)$",
        )
    )

    # ======================================================
    # ADMIN CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_button,
            pattern=r"^admin_",
        )
    )

    # ======================================================
    # RAFFLE APPROVAL
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_approval_button,
            pattern=r"^raffle(?:approve|cancel)_\d+$",
        )
    )

    # ======================================================
    # RAFFLE ENTER
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_enter_button,
            pattern=r"^raffle_enter_\d+$",
        )
    )

    # ======================================================
    # ADMIN PAYMENT
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_payment_button,
            pattern=r"^(approve|deny)_\d+$",
        )
    )

    # ======================================================
    # PAYMENT
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            payment_button,
            pattern=r"^raffle_(cashapp|zelle)_\d+$",
        )
    )

    # ======================================================
    # MEDIA REPOST
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            spoiler_repost_button,
            pattern=r"^spoiler_repost:",
        )
    )

    # ======================================================
    # MEDIA MODERATION
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.PHOTO
            | filters.VIDEO
            | filters.ANIMATION,
            media_spoiler_handler,
        )
    )

    # ======================================================
    # TEXT
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message_handler,
        )
    )

    # ======================================================
    # ERROR HANDLER
    # ======================================================

    application.add_error_handler(
        error_handler
    )

    # ======================================================
    # BIRTHDAY SCHEDULER
    # ======================================================

    start_birthday_scheduler(
        application
    )

    # ======================================================
    # START POLLING
    # ======================================================

    logger.info(
        "Starting Telegram polling..."
    )

    application.run_polling(
        drop_pending_updates=False,
        allowed_updates=Update.ALL_TYPES,
    )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":
    main()
