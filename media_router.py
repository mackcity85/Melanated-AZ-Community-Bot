# ==========================================================
# Melanated AZ Bot - Photo / Video Topic Router
# ==========================================================

import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes


logger = logging.getLogger("media_router")

MEDIA_CHAT_ID = -1002697105809
MEDIA_TOPIC_ID = 10286
MOVE_NOTICE = "📸 Your photo/video was moved to the Media topic."


async def _move_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    # Only photos and videos are handled here.
    if not message.photo and not message.video:
        return

    # Only route media from the Melanated AZ community.
    if message.chat_id != MEDIA_CHAT_ID:
        return

    # Already in the Media topic.
    if getattr(message, "message_thread_id", None) == MEDIA_TOPIC_ID:
        return

    try:
        # Copy first so the original is preserved until Telegram confirms
        # the Media-topic copy succeeded.
        await context.bot.copy_message(
            chat_id=MEDIA_CHAT_ID,
            from_chat_id=MEDIA_CHAT_ID,
            message_id=message.message_id,
            message_thread_id=MEDIA_TOPIC_ID,
        )

        # Tell the member where their media went, in the topic where they
        # originally posted it.
        try:
            notice = await context.bot.send_message(
                chat_id=MEDIA_CHAT_ID,
                message_thread_id=getattr(message, "message_thread_id", None),
                text=MOVE_NOTICE,
            )
            if context.job_queue:
                context.job_queue.run_once(
                    _delete_notice,
                    when=30,
                    data={"chat_id": notice.chat_id, "message_id": notice.message_id},
                )
        except TelegramError:
            logger.exception("Could not send media move notice.")

        # Remove the original only after the copy succeeded.
        try:
            await message.delete()
        except TelegramError:
            logger.exception("Could not delete original media message after moving it.")

    except TelegramError:
        logger.exception(
            "Could not move media | chat=%s | message=%s | target_topic=%s",
            MEDIA_CHAT_ID,
            message.message_id,
            MEDIA_TOPIC_ID,
        )


async def _delete_notice(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data or {}
    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )
    except TelegramError:
        pass


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _move_media(update, context)


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _move_media(update, context)


def install(bot_module):
    """Replace the existing photo/video handlers before bot.build_application()."""
    bot_module.handle_photo = handle_photo
    bot_module.handle_video = handle_video
    logger.info(
        "Media topic routing enabled | chat=%s | topic=%s",
        MEDIA_CHAT_ID,
        MEDIA_TOPIC_ID,
    )
