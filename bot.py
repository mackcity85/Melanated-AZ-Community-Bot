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
)

# ==========================================================
# RAFFLE
# ==========================================================

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

# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ==========================================================
# FLASK HEALTH SERVER
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
# GROUP MEDIA WARNING
# ==========================================================

GROUP_MEDIA_WARNING = """👑 MelanatedAZ Bot — Media Reminder
Chat: {chat_name}

🚫 Your photo/video was removed because photos and videos must be posted using Telegram's Spoiler option.

How to post it correctly:

1️⃣ Select the photo or video.
2️⃣ Tap the ⋮ / three dots menu before sending.
3️⃣ Select Hide with Spoiler / Mark as Spoiler.
4️⃣ Send it to the MelanatedAZ chat.

🎞️ GIFs are allowed without a spoiler.

📩 Check your private messages from the MelanatedAZ Bot. You will also have the option to let MelanatedAZ repost your media for you with Spoiler enabled.

⚠️ If MelanatedAZ reposts your media, you cannot delete the MelanatedAZ repost.

👑 Thank you for following the MelanatedAZ media rules.
"""


# ==========================================================
# PRIVATE MEDIA WARNING
# ==========================================================

PRIVATE_MEDIA_WARNING = """👑 Hi! I'm the MelanatedAZ Bot.
Chat: {chat_name}

🚫 Your photo/video was removed from {chat_name} because photos and videos must be posted using Telegram's Spoiler option.

How to post it correctly:

1️⃣ Select the photo or video.
2️⃣ Tap the ⋮ / three dots menu before sending.
3️⃣ Select Hide with Spoiler / Mark as Spoiler.
4️⃣ Send it to the {chat_name} chat.

🎞️ GIFs are allowed without a spoiler.

If you don't want to do it manually, MelanatedAZ Bot can repost your media for you with Spoiler enabled.

⚠️ If MelanatedAZ reposts your media, you cannot delete the MelanatedAZ repost.

👑 Thank you for following the MelanatedAZ media rules.
"""


# ==========================================================
# PRIVATE REPOST BUTTON
# ==========================================================

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

async def delete_group_warning(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    chat_id = job.data.get("chat_id")
    message_id = job.data.get("message_id")

    if not chat_id or not message_id:
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "Deleted media warning %s from chat %s",
            message_id,
            chat_id,
        )

    except Exception:

        logger.exception(
            "Unable to delete group media warning"
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
# MELANATEDAZ POST IT BUTTON
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

        try:

            await query.edit_message_text(
                "⚠️ This media is no longer available "
                "for reposting.\n\n"
                "Please upload it again using Telegram's "
                "Spoiler option."
            )

        except Exception:
            pass

        return

    original_user_id = media_info.get("user_id")

    if original_user_id != user.id:

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

        except Exception:
            pass

        logger.info(
            "Reposted %s with spoiler for user %s",
            media_info.get("type"),
            user.id,
        )

    except Exception:

        logger.exception(
            "Failed to repost media with spoiler"
        )

        try:

            await query.edit_message_text(
                "⚠️ MelanatedAZ could not repost "
                "your media.\n\n"
                "Please upload it again and select "
                "Hide with Spoiler / Mark as Spoiler."
            )

        except Exception:
            pass


# ==========================================================
# HANDLE NON-SPOILER MEDIA
# ==========================================================

async def handle_non_spoiler_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    media_type: str,
    file_id: str,
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
        "chat_id": message.chat_id,
        "chat_name": chat_name,
    }

    try:

        await message.delete()

        logger.info(
            "Deleted non-spoiler %s from user %s in %s",
            media_type,
            user.id,
            chat_name,
        )

    except Exception:

        logger.exception(
            "Failed to delete non-spoiler %s",
            media_type,
        )

        pending_media.pop(
            token,
            None,
        )

        return

    warning_message = None

    try:

        warning_message = await context.bot.send_message(
            chat_id=message.chat_id,
            text=GROUP_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
        )

        logger.info(
            "Sent media warning to %s",
            chat_name,
        )

    except Exception:

        logger.exception(
            "Failed to send group media warning"
        )

    if warning_message:

        try:

            context.job_queue.run_once(
                delete_group_warning,
                when=30,
                data={
                    "chat_id": warning_message.chat_id,
                    "message_id": warning_message.message_id,
                },
            )

        except Exception:

            logger.exception(
                "Failed to schedule warning deletion"
            )

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=PRIVATE_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
            reply_markup=spoiler_keyboard(token),
        )

        logger.info(
            "Sent private media warning to user %s",
            user.id,
        )

    except Exception as exc:

        logger.warning(
            "Could not send private media warning "
            "to user %s. User may not have started "
            "the bot privately. Error: %s",
            user.id,
            exc,
        )


# ==========================================================
# MEDIA SPOILER MODERATION
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

    if message.animation:

        logger.info(
            "GIF/animation allowed from user %s",
            user.id,
        )

        return

    if message.photo:

        if message.has_media_spoiler:

            logger.info(
                "Spoiler photo allowed from user %s",
                user.id,
            )

            return

        photo = message.photo[-1]

        await handle_non_spoiler_media(
            update=update,
            context=context,
            media_type="photo",
            file_id=photo.file_id,
            caption=message.caption,
            caption_entities=message.caption_entities,
        )

        return

    if message.video:

        if message.has_media_spoiler:

            logger.info(
                "Spoiler video allowed from user %s",
                user.id,
            )

            return

        video = message.video

        await handle_non_spoiler_media(
            update=update,
            context=context,
            media_type="video",
            file_id=video.file_id,
            caption=message.caption,
            caption_entities=message.caption_entities,
        )

        return


# ==========================================================
# TEXT MESSAGE HANDLER
# ==========================================================

async def text_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

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
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.exception(
        "Exception while processing update:",
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

    logger.info(
        "Cash App: Loaded"
    )

    logger.info(
        "Zelle: Loaded"
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
    # PRIVATE RAFFLE DEEP LINK
    #
    # /start raffle_123
    # ======================================================

    application.add_handler(
        CommandHandler(
            "start",
            raffle_private_start,
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
    # START RAFFLE
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle,
        )
    )

    # ======================================================
    # ENTER RAFFLE
    # ======================================================

    application.add_handler(
        CommandHandler(
            ["raffle", "enterraffle"],
            enter_raffle,
        )
    )

    # ======================================================
    # PAID ENTRY
    # ======================================================

    application.add_handler(
        CommandHandler(
            "paid",
            paid_entry,
        )
    )

    # ======================================================
    # STATUS
    # ======================================================

    application.add_handler(
        CommandHandler(
            ["status", "rafflestatus"],
            raffle_status,
        )
    )

    # ======================================================
    # ENTRIES
    # ======================================================

    application.add_handler(
        CommandHandler(
            "entries",
            raffle_entries,
        )
    )

    # ======================================================
    # PENDING PAYMENTS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "pending",
            pending_entries,
        )
    )

    # ======================================================
    # CANCEL RAFFLE
    # ======================================================

    application.add_handler(
        CommandHandler(
            "cancelraffle",
            cancel_raffle,
        )
    )

    # ======================================================
    # DRAW
    # ======================================================

    application.add_handler(
        CommandHandler(
            "draw",
            draw_raffle,
        )
    )

    # ======================================================
    # REROLL
    # ======================================================

    application.add_handler(
        CommandHandler(
            "reroll",
            reroll_raffle,
        )
    )

    # ======================================================
    # BONUS ENTRY
    # ======================================================

    application.add_handler(
        CommandHandler(
            "bonusentry",
            bonus_entry,
        )
    )

    # ======================================================
    # REMOVE ENTRY
    # ======================================================

    application.add_handler(
        CommandHandler(
            "removeentry",
            remove_raffle_entry,
        )
    )

    # ======================================================
    # ADMIN PANEL BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_button,
            pattern=r"^admin_",
        )
    )

    # ======================================================
    # RAFFLE APPROVAL / CANCELLATION
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_approval_button,
            pattern=r"^raffle(?:approve|cancel)_\d+$",
        )
    )

    # ======================================================
    # LEGACY ENTER RAFFLE CALLBACK
    #
    # Handles older raffle posts that still contain
    # callback_data instead of the new deep-link URL.
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_enter_button,
            pattern=r"^raffle_enter_\d+$",
        )
    )

    # ======================================================
    # ADMIN PAYMENT BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_payment_button,
            pattern=r"^(approve|deny)_\d+$",
        )
    )

    # ======================================================
    # PAYMENT BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            payment_button,
            pattern=r"^raffle_(cashapp|zelle)_\d+$",
        )
    )

    # ======================================================
    # MEDIA REPOST BUTTON
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            spoiler_repost_button,
            pattern=r"^spoiler_repost:",
        )
    )

    # ======================================================
    # MEDIA SPOILER MODERATION
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
    # RAFFLE SETUP TEXT
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
