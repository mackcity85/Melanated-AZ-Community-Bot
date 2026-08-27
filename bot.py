# ==========================================================
# Melanated AZ Bot
# bot.py
# ==========================================================

import logging
import threading
import os
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ==========================================================
# FLASK
# ==========================================================

app = Flask(__name__)


@app.route("/")
def health():

    return "Melanated AZ Bot is running", 200


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
# ==========================================================

pending_media = {}


# ==========================================================
# MEDIA MESSAGES
# ==========================================================

GROUP_MEDIA_WARNING = """👑 MelanatedAZ Bot — Media Reminder
Chat: {chat_name}

🚫 A photo/video was removed because photos and videos must be posted using Telegram's Spoiler option.

📌 How to post it manually:

1️⃣ Select your photo or video.
2️⃣ Tap the ⋮ / three dots menu before sending.
3️⃣ Select Hide with Spoiler / Mark as Spoiler.
4️⃣ Send it to the Melanated AZ chat.

🎞️ GIFs are allowed without a spoiler.

📩 The MelanatedAZ Bot has also sent instructions privately.

If you want MelanatedAZ to post the media for you, open the bot using the private link sent in your message.

⚠️ If MelanatedAZ reposts your media, you cannot delete the MelanatedAZ post.

👑 Thank you for following the MelanatedAZ media rules.
"""


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

👇 Tap the button below to open MelanatedAZ Bot and continue.
"""


# ==========================================================
# MEDIA DEEP LINK
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
                    "👑 Open MelanatedAZ Bot to post media",
                    url=deep_link,
                )
            ]
        ]
    )


def spoiler_keyboard(token):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👑 MelanatedAZ Post It",
                    callback_data=f"spoiler_repost:{token}",
                )
            ]
        ]
    )


# ==========================================================
# DELETE GROUP WARNING
# ==========================================================

async def delete_group_warning(context):

    job = context.job

    if not job:
        return

    chat_id = job.data.get("chat_id")
    message_id = job.data.get("message_id")

    if chat_id is None or message_id is None:
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

    except Exception:

        logger.exception(
            "Unable to delete group media warning"
        )


# ==========================================================
# SEND MEDIA WITH SPOILER
# ==========================================================

async def send_media_with_spoiler(
    context,
    media_info,
):

    media_type = media_info.get("type")
    file_id = media_info.get("file_id")
    caption = media_info.get("caption")
    caption_entities = media_info.get("caption_entities")
    chat_id = media_info.get("chat_id")

    if not media_type:
        raise ValueError("Missing media type")

    if not file_id:
        raise ValueError("Missing Telegram file ID")

    if not chat_id:
        raise ValueError("Missing original chat ID")

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
# START / DEEP LINK
# ==========================================================

async def media_start(
    update,
    context,
):

    user = update.effective_user

    if not user:
        return

    args = context.args or []

    if not args:

        await update.effective_message.reply_text(
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
    # MEDIA
    # ======================================================

    if payload.startswith("media_"):

        token = payload[len("media_"):]

        media_info = pending_media.get(token)

        if not media_info:

            await update.effective_message.reply_text(
                "⚠️ This media is no longer available.\n\n"
                "Please upload the photo/video again "
                "using Telegram's Spoiler option."
            )

            return

        if media_info.get("user_id") != user.id:

            await update.effective_message.reply_text(
                "⚠️ This media belongs to another "
                "MelanatedAZ member."
            )

            return

        await update.effective_message.reply_text(
            "👑 **MelanatedAZ Bot**\n\n"
            "I have your media ready.\n\n"
            "You can let MelanatedAZ repost it to "
            "the original chat with Telegram's "
            "Spoiler option enabled.\n\n"
            "⚠️ If MelanatedAZ reposts your media, "
            "you cannot delete the MelanatedAZ repost.",
            reply_markup=spoiler_keyboard(token),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RAFFLE
    # ======================================================

    if payload.startswith("raffle_"):

        await raffle_private_start(
            update,
            context,
        )

        return

    await raffle_private_start(
        update,
        context,
    )


# ==========================================================
# MEDIA REPOST BUTTON
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

        await query.edit_message_text(
            "✅ MelanatedAZ posted your media.\n\n"
            "Your photo/video was reposted with "
            "Spoiler enabled.\n\n"
            "⚠️ Remember: you cannot delete the "
            "MelanatedAZ repost.\n\n"
            "👑 Thank you for following the "
            "MelanatedAZ media rules."
        )

    except Exception:

        logger.exception(
            "Failed to repost media with spoiler"
        )

        await query.edit_message_text(
            "⚠️ MelanatedAZ could not repost "
            "your media.\n\n"
            "Please upload it again and select "
            "Hide with Spoiler / Mark as Spoiler."
        )


# ==========================================================
# NON-SPOILER MEDIA
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
    }

    try:

        await message.delete()

    except Exception:

        logger.exception(
            "Failed to delete non-spoiler media"
        )

        pending_media.pop(token, None)

        return

    try:

        bot_user = await context.bot.get_me()

        bot_username = bot_user.username

        if not bot_username:
            raise ValueError(
                "Bot username unavailable"
            )

    except Exception:

        pending_media.pop(token, None)

        return

    warning_message = None

    try:

        warning_message = await context.bot.send_message(
            chat_id=message.chat_id,
            text=GROUP_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
        )

    except Exception:

        logger.exception(
            "Failed to send group media warning"
        )

    if warning_message and context.job_queue:

        context.job_queue.run_once(
            delete_group_warning,
            when=60,
            data={
                "chat_id": warning_message.chat_id,
                "message_id": warning_message.message_id,
            },
        )

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=PRIVATE_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
            reply_markup=media_deep_link_keyboard(
                bot_username,
                token,
            ),
        )

    except Exception as exc:

        logger.warning(
            "Could not DM user %s: %s",
            user.id,
            exc,
        )


# ==========================================================
# MEDIA HANDLER
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

    if message.animation:
        return

    if message.photo:

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

    if message.video:

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


# ==========================================================
# TEXT HANDLER
# ==========================================================

async def text_message_handler(
    update,
    context,
):

    handled = await handle_raffle_setup(
        update,
        context,
    )

    if handled:
        return


# ==========================================================
# ERROR
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

    # ======================================================
    # APPLICATION
    # ======================================================

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ======================================================
    # START / DEEP LINKS
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
    # RAFFLE
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            ["raffle", "enterraffle"],
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
            ["status", "rafflestatus"],
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
    # ADMIN BUTTONS
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
    # LEGACY RAFFLE ENTER
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
    # RAFFLE SETUP
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
    # START BIRTHDAY SCHEDULER
    # ======================================================

    start_birthday_scheduler(
        application
    )

    # ======================================================
    # START TELEGRAM
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
