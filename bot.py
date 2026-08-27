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
#
# token -> media information
#
# NOTE:
# This is stored in memory. A Render restart clears pending
# media that has not yet been reposted.
# ==========================================================

pending_media = {}


# ==========================================================
# GROUP WARNING
#
# This remains in the group for 60 seconds.
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

⚠️ If MelanatedAZ reposts your media, you cannot delete the MelanatedAZ repost.

👑 Thank you for following the MelanatedAZ media rules.
"""


# ==========================================================
# PRIVATE MEDIA MESSAGE
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

👇 Tap the button below to open MelanatedAZ Bot and continue.
"""


# ==========================================================
# OPEN BOT BUTTON
#
# This sends the member into the bot using a deep link.
# ==========================================================

def media_deep_link_keyboard(bot_username, token):

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


# ==========================================================
# POST MEDIA BUTTON
#
# This button appears INSIDE the bot after the member
# opens the deep link.
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

    chat_id = job.data.get(
        "chat_id"
    )

    message_id = job.data.get(
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

    if not chat_id:
        raise ValueError(
            "Missing original chat ID"
        )

    # ======================================================
    # PHOTO
    # ======================================================

    if media_type == "photo":

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=file_id,
            caption=caption,
            caption_entities=caption_entities,
            has_spoiler=True,
        )

        return

    # ======================================================
    # VIDEO
    # ======================================================

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
# MEDIA START FLOW
#
# Handles:
#
# https://t.me/MelanatedAZ_Bot?start=media_TOKEN
#
# Telegram converts that into:
#
# /start media_TOKEN
# ==========================================================

async def media_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    # ------------------------------------------------------
    # Get deep-link argument
    # ------------------------------------------------------

    args = context.args or []

    if not args:

        await update.effective_message.reply_text(
            "👑 Welcome to the MelanatedAZ Bot.\n\n"
            "This bot helps manage MelanatedAZ community "
            "raffles and media moderation."
        )

        return

    payload = args[0]

    logger.info(
        "START payload received from user %s: %s",
        user.id,
        payload,
    )

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

        # --------------------------------------------------
        # TOKEN NOT FOUND
        # --------------------------------------------------

        if not media_info:

            await update.effective_message.reply_text(
                "⚠️ This media is no longer available.\n\n"
                "Please upload the photo/video again "
                "using Telegram's Spoiler option."
            )

            return

        # --------------------------------------------------
        # VERIFY USER
        # --------------------------------------------------

        original_user_id = media_info.get(
            "user_id"
        )

        if original_user_id != user.id:

            await update.effective_message.reply_text(
                "⚠️ This media belongs to another "
                "MelanatedAZ member."
            )

            return

        # --------------------------------------------------
        # SHOW POST BUTTON
        # --------------------------------------------------

        await update.effective_message.reply_text(
            "👑 MelanatedAZ Bot\n\n"
            "I have your media ready.\n\n"
            "You can let MelanatedAZ repost it to "
            "the original chat with Telegram's "
            "Spoiler option enabled.\n\n"
            "⚠️ If MelanatedAZ reposts your media, "
            "you cannot delete the MelanatedAZ repost.",
            reply_markup=spoiler_keyboard(
                token
            ),
        )

        logger.info(
            "Displayed media repost button to user %s "
            "for token %s",
            user.id,
            token,
        )

        return

    # ======================================================
    # RAFFLE DEEP LINK
    #
    # Anything beginning with raffle_ is sent to the
    # existing raffle /start handler.
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
    # NORMAL /START
    # ======================================================

    await raffle_private_start(
        update,
        context,
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

    if not data.startswith(
        "spoiler_repost:"
    ):
        await query.answer()
        return

    token = data.split(
        ":",
        1,
    )[1]

    logger.info(
        "MEDIA REPOST button clicked by user %s: %s",
        user.id,
        data,
    )

    media_info = pending_media.get(
        token
    )

    # ======================================================
    # MEDIA EXPIRED
    # ======================================================

    if not media_info:

        await query.answer(
            "This media is no longer available.",
            show_alert=True,
        )

        try:

            await query.edit_message_text(
                "⚠️ This media is no longer available.\n\n"
                "Please upload it again using Telegram's "
                "Spoiler option."
            )

        except Exception:
            pass

        return

    # ======================================================
    # VERIFY USER
    # ======================================================

    original_user_id = media_info.get(
        "user_id"
    )

    if original_user_id != user.id:

        await query.answer(
            "This media belongs to another member.",
            show_alert=True,
        )

        return

    # ======================================================
    # ANSWER BUTTON
    # ======================================================

    await query.answer(
        "MelanatedAZ is posting your media..."
    )

    # ======================================================
    # POST MEDIA
    # ======================================================

    try:

        await send_media_with_spoiler(
            context,
            media_info,
        )

        pending_media.pop(
            token,
            None,
        )

        # ==================================================
        # CONFIRMATION
        # ==================================================

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

            logger.exception(
                "Could not edit media confirmation"
            )

        logger.info(
            "Successfully reposted %s with spoiler "
            "for user %s",
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

    # ======================================================
    # CHAT NAME
    # ======================================================

    chat_name = (
        message.chat.title
        or "MelanatedAZ"
    )

    # ======================================================
    # TOKEN
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
        "Saved non-spoiler %s for user %s with token %s",
        media_type,
        user.id,
        token,
    )

    # ======================================================
    # DELETE ORIGINAL
    # ======================================================

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
            "Could not get bot username"
        )

        pending_media.pop(
            token,
            None,
        )

        return

    # ======================================================
    # GROUP WARNING
    #
    # NO BUTTON
    #
    # DELETED AFTER 60 SECONDS
    # ======================================================

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

    # ======================================================
    # DELETE WARNING AFTER 60 SECONDS
    # ======================================================

    if warning_message:

        try:

            context.job_queue.run_once(
                delete_group_warning,
                when=60,
                data={
                    "chat_id": warning_message.chat_id,
                    "message_id": warning_message.message_id,
                },
            )

            logger.info(
                "Scheduled media warning %s for deletion "
                "in 60 seconds",
                warning_message.message_id,
            )

        except Exception:

            logger.exception(
                "Failed to schedule warning deletion"
            )

    # ======================================================
    # PRIVATE MESSAGE
    #
    # IF USER HAS NEVER STARTED BOT:
    #
    # Telegram will reject this with 403.
    #
    # The group warning still explains the rules, but the
    # deep link must be available for the member to open.
    # ======================================================

    deep_link_markup = media_deep_link_keyboard(
        bot_username,
        token,
    )

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=PRIVATE_MEDIA_WARNING.format(
                chat_name=chat_name,
            ),
            reply_markup=deep_link_markup,
        )

        logger.info(
            "Sent private media instructions to user %s",
            user.id,
        )

    except Exception as exc:

        logger.warning(
            "Could not DM user %s. "
            "User must open the bot first. "
            "Deep link generated: "
            "https://t.me/%s?start=media_%s "
            "Error: %s",
            user.id,
            bot_username,
            token,
            exc,
        )


# ==========================================================
# MEDIA SPOILER MODERATION
#
# GIFS
#   ALLOWED
#
# PHOTOS
#   SPOILER     = ALLOWED
#   NO SPOILER  = DELETED
#
# VIDEOS
#   SPOILER     = ALLOWED
#   NO SPOILER  = DELETED
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
        # NON-SPOILER PHOTO
        # --------------------------------------------------

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
        # NON-SPOILER VIDEO
        # --------------------------------------------------

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
    # START
    #
    # IMPORTANT:
    # We now use media_start instead of sending every
    # /start directly to raffle_private_start.
    #
    # media_start decides whether the payload is:
    #
    # media_TOKEN
    #
    # or
    #
    # raffle_ID
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
