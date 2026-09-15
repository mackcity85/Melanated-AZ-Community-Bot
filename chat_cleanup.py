# ==========================================================
# Melanated AZ Bot - chat_cleanup.py
# Automatic cleanup for bot messages in the main/admin groups.
#
# Default: delete temporary bot messages after 3 minutes.
# Daily community messages are intentionally preserved.
# User/member messages are never targeted by this module.
# ==========================================================

import html
import logging
import os

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, MessageHandler, filters

logger = logging.getLogger(__name__)

CLEANUP_SECONDS = int(os.environ.get("CHAT_CLEANUP_SECONDS", "180") or "180")
DAILY_MESSAGE_MARKERS = (
    "DAILY COMMUNITY",
    "GOOD MORNING",
    "GOOD AFTERNOON",
    "GOOD EVENING",
    "COMMUNITY CHECK-IN",
)


def _main_group_id():
    try:
        return int(os.environ.get("MAIN_GROUP_ID", "-1002697105809"))
    except (TypeError, ValueError):
        return -1002697105809


def _admin_group_id():
    try:
        value = os.environ.get("ADMIN_GROUP_ID")
        return int(value) if value else -5241371581
    except (TypeError, ValueError):
        return -5241371581


def _cleanup_group_ids():
    return {_main_group_id(), _admin_group_id()}


def _is_daily_community_message(text: str) -> bool:
    upper = str(text or "").upper()
    return any(marker in upper for marker in DAILY_MESSAGE_MARKERS)


def _is_permanent_launcher(chat_id, thread_id, message_id, text) -> bool:
    """Only daily community messages remain permanent."""
    return _is_daily_community_message(text)


async def _delete_after(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    if not job or not job.data:
        return

    chat_id = job.data.get("chat_id")
    message_id = job.data.get("message_id")
    if chat_id is None or message_id is None:
        return

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError as exc:
        logger.debug(
            "Cleanup could not delete %s/%s: %s",
            chat_id,
            message_id,
            exc,
        )


def schedule_cleanup(application, message, delay=None):
    if not application or not message:
        return

    if _is_permanent_launcher(
        message.chat_id,
        getattr(message, "message_thread_id", None),
        message.message_id,
        getattr(message, "text", ""),
    ):
        return

    seconds = CLEANUP_SECONDS if delay is None else delay
    application.job_queue.run_once(
        _delete_after,
        when=seconds,
        data={
            "chat_id": message.chat_id,
            "message_id": message.message_id,
        },
        name=f"cleanup:{message.chat_id}:{message.message_id}",
    )


async def cleanup_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    main_id = _main_group_id()
    if message.chat_id != main_id:
        return

    # Telegram service messages are removed immediately from the main group.
    try:
        await message.delete()
    except TelegramError as exc:
        logger.debug("Could not delete service message: %s", exc)



def install_chat_cleanup(application):
    """Install automatic 3-minute cleanup for bot text messages.

    Daily community messages are exempt. The main group and admin group
    (including the configured ADMIN_GROUP_ID, currently -5241371581) are
    covered. Member/user messages are not intercepted.
    """
    bot_class = application.bot.__class__

    if getattr(bot_class, "_melanated_chat_cleanup_installed", False):
        return

    original_send_message = bot_class.send_message

    async def wrapped_send_message(self, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        if chat_id is None and args:
            chat_id = args[0]

        thread_id = kwargs.get("message_thread_id")
        text = kwargs.get("text")
        if text is None and len(args) > 1:
            text = args[1]
        text = str(text or "")

        result = await original_send_message(self, *args, **kwargs)

        cleanup_ids = _cleanup_group_ids()
        if result and chat_id in cleanup_ids:
            schedule_cleanup(application, result)

        # Keep the existing admin notification mirror for messages sent to
        # the main group, but make the mirrored notification temporary too.
        main_id = _main_group_id()
        admin_id = _admin_group_id()
        if (
            result
            and main_id is not None
            and chat_id == main_id
            and admin_id
            and admin_id != main_id
            and not _is_daily_community_message(text)
        ):
            try:
                topic_note = f"\n📍 Topic ID: {thread_id}" if thread_id else ""
                admin_text = (
                    "<b>🔔 BOT NOTIFICATION</b>"
                    f"{html.escape(topic_note)}\n\n"
                    f"{html.escape(text[:3800])}"
                )
                admin_result = await original_send_message(
                    self,
                    chat_id=admin_id,
                    text=admin_text,
                    parse_mode="HTML",
                )
                if admin_result:
                    schedule_cleanup(application, admin_result)
            except TelegramError as exc:
                logger.warning(
                    "Could not mirror bot notification to admin group: %s", exc
                )

        return result

    bot_class.send_message = wrapped_send_message
    bot_class._melanated_chat_cleanup_installed = True
    logger.info(
        "Chat cleanup installed: temporary bot messages expire after %s seconds; daily community messages are preserved.",
        CLEANUP_SECONDS,
    )
