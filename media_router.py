# ==========================================================
# Melanated AZ Bot - Photo / Video Topic Router
# ==========================================================

import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, ContextTypes, MessageHandler, filters

logger = logging.getLogger("media_router")

MEDIA_CHAT_ID = -1002697105809
MEDIA_TOPIC_ID = 10286
MOVE_NOTICE = "📸 Your photo/video was moved to the Media topic."


async def _move_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    if message.chat_id != MEDIA_CHAT_ID:
        return

    if not message.photo and not message.video:
        return

    if getattr(message, "message_thread_id", None) == MEDIA_TOPIC_ID:
        return

    logger.info(
        "Media routing received | chat=%s | topic=%s | message=%s | photo=%s | video=%s",
        message.chat_id,
        getattr(message, "message_thread_id", None),
        message.message_id,
        bool(message.photo),
        bool(message.video),
    )

    try:
        await context.bot.copy_message(
            chat_id=MEDIA_CHAT_ID,
            from_chat_id=MEDIA_CHAT_ID,
            message_id=message.message_id,
            message_thread_id=MEDIA_TOPIC_ID,
        )
        logger.info(
            "Media copied successfully | source_message=%s | target_topic=%s",
            message.message_id,
            MEDIA_TOPIC_ID,
        )
    except TelegramError:
        logger.exception(
            "Could not move media | chat=%s | message=%s | source_topic=%s | target_topic=%s",
            MEDIA_CHAT_ID,
            message.message_id,
            getattr(message, "message_thread_id", None),
            MEDIA_TOPIC_ID,
        )
        return

    # The notice is temporary. The Media topic itself is NOT cleaned up.
    try:
        source_topic = getattr(message, "message_thread_id", None)
        if source_topic is not None:
            notice = await context.bot.send_message(
                chat_id=MEDIA_CHAT_ID,
                message_thread_id=source_topic,
                text=MOVE_NOTICE,
            )
        else:
            notice = await context.bot.send_message(
                chat_id=MEDIA_CHAT_ID,
                text=MOVE_NOTICE,
            )

        if context.job_queue:
            context.job_queue.run_once(
                _delete_notice,
                when=60,
                data={"chat_id": notice.chat_id, "message_id": notice.message_id},
                name=f"media-move-notice:{notice.message_id}",
            )
    except TelegramError:
        logger.exception("Could not send media move notice.")

    try:
        await message.delete()
        logger.info(
            "Original media deleted after successful copy | message=%s",
            message.message_id,
        )
    except TelegramError:
        logger.exception(
            "Could not delete original media message after moving it | message=%s",
            message.message_id,
        )

    # Prevent bot.py's older photo/video moderation handler from processing
    # the same update after this router has successfully handled it.
    raise ApplicationHandlerStop


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


def install_application(application):
    """Install direct group-0 media handlers on the finished application."""
    if getattr(application, "_melanated_media_router_installed", False):
        return

    application.add_handler(
        MessageHandler(filters.PHOTO, handle_photo),
        group=0,
    )
    application.add_handler(
        MessageHandler(filters.VIDEO, handle_video),
        group=0,
    )
    application._melanated_media_router_installed = True

    logger.info(
        "Media topic routing enabled | chat=%s | topic=%s | direct_handlers=2",
        MEDIA_CHAT_ID,
        MEDIA_TOPIC_ID,
    )


def install(bot_module):
    """Install media routing when bot.py builds the application."""
    original_build_application = bot_module.build_application

    def wrapped_build_application(*args, **kwargs):
        application = original_build_application(*args, **kwargs)
        install_application(application)
        return application

    bot_module.build_application = wrapped_build_application
