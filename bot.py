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
# PENDING MEDIA STORAGE
#
# Stores media temporarily after it is removed so the bot
# can repost it with Telegram's Spoiler setting.
#
# This is intentionally kept in memory.
# ==========================================================

pending_media = {}


# ==========================================================
# MEDIA WARNING
# ==========================================================

MEDIA_WARNING = """🚫 MelanatedAZ Media Reminder

Your photo/video was removed because photos and videos must be posted using Telegram's Spoiler option.

How to post it correctly:

1️⃣ Select the photo or video you want to send.
2️⃣ Tap the ⋮ / three dots menu before sending.
3️⃣ Select Hide with Spoiler / Mark as Spoiler.
4️⃣ Send the photo or video.

🎞️ GIFs are allowed without a spoiler.

You can also let me repost your media for you by pressing the button below.

Thank you for helping keep MelanatedAZ comfortable for everyone. 👑
"""


# ==========================================================
# SPOILER BUTTON
# ==========================================================

def spoiler_keyboard(token):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔒 Post With Spoiler",
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
            "Deleted media warning message %s from chat %s",
            message_id,
            chat_id,
        )

    except Exception:

        logger.exception(
            "Unable to delete media warning message"
        )


# ==========================================================
# SEND MEDIA WITH SPOILER
# ==========================================================

async def send_media_with_spoiler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    media_info: dict,
):

    user = update.effective_user

    if not user:
        return

    media_type = media_info.get("type")
    file_id = media_info.get("file_id")
    caption = media_info.get("caption")

    if not media_type or not file_id:
        return

    # ------------------------------------------------------
    # PHOTO
    # ------------------------------------------------------

    if media_type == "photo":

        await context.bot.send_photo(
            chat_id=RAFFLE_CHAT_ID,
            photo=file_id,
            caption=caption,
            has_spoiler=True,
        )

        return

    # ------------------------------------------------------
    # VIDEO
    # ------------------------------------------------------

    if media_type == "video":

        await context.bot.send_video(
            chat_id=RAFFLE_CHAT_ID,
            video=file_id,
            caption=caption,
            has_spoiler=True,
        )

        return


# ==========================================================
# SPOILER REPOST BUTTON
# ==========================================================

async def spoiler_repost_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = update.effective_user

    if not user:
        return

    data = query.data or ""

    if not data.startswith("spoiler_repost:"):
        return

    token = data.split(
        ":",
        1,
    )[1]

    media_info = pending_media.get(token)

    # ------------------------------------------------------
    # MEDIA NO LONGER AVAILABLE
    # ------------------------------------------------------

    if not media_info:

        try:

            await query.edit_message_text(
                "⚠️ This media is no longer available for reposting.\n\n"
                "Please upload it again using Telegram's "
                "Spoiler option."
            )

        except Exception:

            pass

        return

    # ------------------------------------------------------
    # VERIFY ORIGINAL USER
    # ------------------------------------------------------

    original_user_id = media_info.get(
        "user_id"
    )

    if original_user_id != user.id:

        await query.answer(
            "This media belongs to another member.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # REPOST MEDIA
    # ------------------------------------------------------

    try:

        await send_media_with_spoiler(
            update,
            context,
            media_info,
        )

        # --------------------------------------------------
        # REMOVE FROM TEMPORARY STORAGE
        # --------------------------------------------------

        pending_media.pop(
            token,
            None,
        )

        # --------------------------------------------------
        # UPDATE PRIVATE MESSAGE
        # --------------------------------------------------

        try:

            await query.edit_message_text(
                "✅ Your media has been reposted to "
                "MelanatedAZ with Spoiler enabled.\n\n"
                "🔒 Your media is now protected by the "
                "group's spoiler rule."
            )

        except Exception:

            pass

        logger.info(
            "Reposted media %s with spoiler for user %s",
            token,
            user.id,
        )

    except Exception:

        logger.exception(
            "Failed to repost media with spoiler"
        )

        try:

            await query.edit_message_text(
                "⚠️ I couldn't repost that media right now.\n\n"
                "Please upload it again and select "
                "Hide with Spoiler / Mark as Spoiler."
            )

        except Exception:

            pass


# ==========================================================
# MEDIA SPOILER MODERATION
#
# GIFS / ANIMATIONS
#     ALWAYS ALLOWED
#
# PHOTOS
#     SPOILER     = ALLOWED
#     NO SPOILER  = DELETE
#
# VIDEOS
#     SPOILER     = ALLOWED
#     NO SPOILER  = DELETE
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

    # ======================================================
    # GIF / ANIMATION
    # ======================================================

    if message.animation:

        logger.info(
            "GIF/animation allowed from user %s",
            user.id,
        )

        return

    # ======================================================
    # PHOTO
    # ======================================================

    if message.photo:

        # --------------------------------------------------
        # SPOILER PHOTO = ALLOWED
        # --------------------------------------------------

        if message.has_media_spoiler:

            logger.info(
                "Spoiler photo allowed from user %s",
                user.id,
            )

            return

        # --------------------------------------------------
        # SAVE PHOTO BEFORE DELETING
        #
        # Telegram photo sizes are ordered from smallest
        # to largest, so [-1] gives us the highest quality.
        # --------------------------------------------------

        photo = message.photo[-1]

        token = uuid.uuid4().hex

        pending_media[token] = {
            "type": "photo",
            "file_id": photo.file_id,
            "caption": message.caption,
            "user_id": user.id,
            "username": user.username,
            "chat_id": message.chat_id,
        }

        # --------------------------------------------------
        # DELETE ORIGINAL PHOTO
        # --------------------------------------------------

        try:

            await message.delete()

            logger.info(
                "Deleted non-spoiler photo from user %s",
                user.id,
            )

        except Exception:

            logger.exception(
                "Failed to delete non-spoiler photo"
            )

            pending_media.pop(
                token,
                None,
            )

            return

        # --------------------------------------------------
        # SEND GROUP WARNING
        # --------------------------------------------------

        warning_message = None

        try:

            warning_message = await context.bot.send_message(
                chat_id=message.chat_id,
                text=MEDIA_WARNING,
                reply_markup=spoiler_keyboard(token),
            )

        except Exception:

            logger.exception(
                "Failed to send group media warning"
            )

        # --------------------------------------------------
        # DELETE GROUP WARNING AFTER 30 SECONDS
        # --------------------------------------------------

        if warning_message:

            context.job_queue.run_once(
                delete_group_warning,
                when=30,
                data={
                    "chat_id": warning_message.chat_id,
                    "message_id": warning_message.message_id,
                },
            )

        # --------------------------------------------------
        # SEND PRIVATE WARNING
        # --------------------------------------------------

        try:

            await context.bot.send_message(
                chat_id=user.id,
                text=MEDIA_WARNING,
                reply_markup=spoiler_keyboard(token),
            )

            logger.info(
                "Sent private media warning to user %s",
                user.id,
            )

        except Exception:

            logger.warning(
                "Could not send private warning to user %s. "
                "User may not have started the bot privately.",
                user.id,
            )

        return

    # ======================================================
    # VIDEO
    # ======================================================

    if message.video:

        # --------------------------------------------------
        # SPOILER VIDEO = ALLOWED
        # --------------------------------------------------

        if message.has_media_spoiler:

            logger.info(
                "Spoiler video allowed from user %s",
                user.id,
            )

            return

        # --------------------------------------------------
        # SAVE VIDEO BEFORE DELETING
        # --------------------------------------------------

        video = message.video

        token = uuid.uuid4().hex

        pending_media[token] = {
            "type": "video",
            "file_id": video.file_id,
            "caption": message.caption,
            "user_id": user.id,
            "username": user.username,
            "chat_id": message.chat_id,
        }

        # --------------------------------------------------
        # DELETE ORIGINAL VIDEO
        # --------------------------------------------------

        try:

            await message.delete()

            logger.info(
                "Deleted non-spoiler video from user %s",
                user.id,
            )

        except Exception:

            logger.exception(
                "Failed to delete non-spoiler video"
            )

            pending_media.pop(
                token,
                None,
            )

            return

        # --------------------------------------------------
        # SEND GROUP WARNING
        # --------------------------------------------------

        warning_message = None

        try:

            warning_message = await context.bot.send_message(
                chat_id=message.chat_id,
                text=MEDIA_WARNING,
                reply_markup=spoiler_keyboard(token),
            )

        except Exception:

            logger.exception(
                "Failed to send group media warning"
            )

        # --------------------------------------------------
        # DELETE GROUP WARNING AFTER 30 SECONDS
        # --------------------------------------------------

        if warning_message:

            context.job_queue.run_once(
                delete_group_warning,
                when=30,
                data={
                    "chat_id": warning_message.chat_id,
                    "message_id": warning_message.message_id,
                },
            )

        # --------------------------------------------------
        # SEND PRIVATE WARNING
        # --------------------------------------------------

        try:

            await context.bot.send_message(
                chat_id=user.id,
                text=MEDIA_WARNING,
                reply_markup=spoiler_keyboard(token),
            )

            logger.info(
                "Sent private media warning to user %s",
                user.id,
            )

        except Exception:

            logger.warning(
                "Could not send private warning to user %s. "
                "User may not have started the bot privately.",
                user.id,
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
    # ADMIN COMMAND
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
    # PRIVATE ENTER RAFFLE BUTTON
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
    # MEDIA SPOILER REPOST BUTTON
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            spoiler_repost_button,
            pattern=r"^spoiler_repost:",
        )
    )

    # ======================================================
    # MEDIA SPOILER MODERATION
    #
    # GIFS      = ALLOWED
    # SPOILER   = ALLOWED
    # NO SPOILER = DELETED
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
