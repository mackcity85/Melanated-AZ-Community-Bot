# ==========================================================
# Melanated AZ Bot - chat_cleanup.py
# Persistent cleanup for bot messages in the main/admin groups.
#
# Default: delete temporary bot messages after 3 minutes.
# Daily community messages and active raffle topic posts are preserved.
# User/member messages are never targeted by this module.
# Bot ID: 8810138488
#
# IMPORTANT: This module does NOT mirror notifications to the admin group.
# ==========================================================

import json
import logging
import os
from pathlib import Path

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

CLEANUP_SECONDS = int(os.environ.get("CHAT_CLEANUP_SECONDS", "180") or "180")
BOT_ID = 8810138488
RAFFLE_TOPIC_ID = 11883
MESSAGE_STORE = Path(os.environ.get("CHAT_CLEANUP_STORE", "/var/data/bot_cleanup_messages.json"))
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
    # Cleanup is intentionally limited to the main community group.
    # The admin group is never used as a notification mirror.
    return {_main_group_id()}


def _is_daily_community_message(text: str) -> bool:
    upper = str(text or "").upper()
    return any(marker in upper for marker in DAILY_MESSAGE_MARKERS)


def _is_raffle_topic_message(message) -> bool:
    """Raffle posts are permanent until the raffle manager closes/removes them."""
    if not message:
        return False
    try:
        return (
            int(message.chat_id) == _main_group_id()
            and int(getattr(message, "message_thread_id", 0) or 0) == RAFFLE_TOPIC_ID
        )
    except (TypeError, ValueError):
        return False


def _record_is_raffle_topic(record) -> bool:
    try:
        return (
            int(record.get("chat_id")) == _main_group_id()
            and int(record.get("thread_id", 0) or 0) == RAFFLE_TOPIC_ID
        )
    except (TypeError, ValueError, AttributeError):
        return False


def _load_store():
    try:
        if not MESSAGE_STORE.exists():
            return []
        data = json.loads(MESSAGE_STORE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("Could not load bot cleanup store: %s", exc)
        return []


def _save_store(records):
    try:
        MESSAGE_STORE.parent.mkdir(parents=True, exist_ok=True)
        tmp = MESSAGE_STORE.with_suffix(".tmp")
        tmp.write_text(json.dumps(records, separators=(",", ":")), encoding="utf-8")
        tmp.replace(MESSAGE_STORE)
    except OSError as exc:
        logger.warning("Could not save bot cleanup store: %s", exc)


def _remember_message(message):
    if not message or message.chat_id not in _cleanup_group_ids():
        return
    text = getattr(message, "text", "") or getattr(message, "caption", "") or ""
    if _is_daily_community_message(text) or _is_raffle_topic_message(message):
        return

    records = _load_store()
    record = {"chat_id": int(message.chat_id), "message_id": int(message.message_id)}
    if record not in records:
        records.append(record)
    _save_store(records[-5000:])


def _forget_message(chat_id, message_id):
    records = _load_store()
    records = [r for r in records if not (r.get("chat_id") == chat_id and r.get("message_id") == message_id)]
    _save_store(records)


async def _delete_record(context, record):
    chat_id = record.get("chat_id")
    message_id = record.get("message_id")
    if chat_id is None or message_id is None or _record_is_raffle_topic(record):
        return
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        _forget_message(chat_id, message_id)
    except TelegramError as exc:
        logger.debug("Cleanup could not delete %s/%s: %s", chat_id, message_id, exc)


async def _delete_after(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    if not job or not job.data:
        return
    record = job.data
    await _delete_record(context, record)


def schedule_cleanup(application, message, delay=None):
    if not application or not message:
        return

    text = getattr(message, "text", "") or getattr(message, "caption", "") or ""
    if _is_daily_community_message(text) or _is_raffle_topic_message(message):
        return

    if message.chat_id not in _cleanup_group_ids():
        return

    _remember_message(message)
    seconds = CLEANUP_SECONDS if delay is None else delay
    application.job_queue.run_once(
        _delete_after,
        when=seconds,
        data={"chat_id": message.chat_id, "message_id": message.message_id},
        name=f"cleanup:{message.chat_id}:{message.message_id}",
    )


async def startup_cleanup(application):
    """Delete previously recorded temporary bot messages after a Render restart."""
    records = _load_store()
    if not records:
        logger.info("Bot cleanup startup sweep: no stored bot messages.")
        return

    logger.info("Bot cleanup startup sweep: checking %s stored bot messages.", len(records))
    remaining = []
    for record in records:
        chat_id = record.get("chat_id")
        message_id = record.get("message_id")
        if _record_is_raffle_topic(record):
            remaining.append(record)
            continue
        if chat_id not in _cleanup_group_ids() or not isinstance(message_id, int):
            continue
        try:
            await application.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info("Startup cleanup deleted bot message %s/%s.", chat_id, message_id)
        except TelegramError as exc:
            remaining.append(record)
            logger.debug("Startup cleanup could not delete %s/%s: %s", chat_id, message_id, exc)
    _save_store(remaining[-5000:])


async def cleanup_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    main_id = _main_group_id()
    if message.chat_id != main_id:
        return

    try:
        await message.delete()
    except TelegramError as exc:
        logger.debug("Could not delete service message: %s", exc)


def install_chat_cleanup(application):
    """Install persistent 3-minute cleanup for temporary bot text messages."""
    bot_class = application.bot.__class__

    if getattr(bot_class, "_melanated_chat_cleanup_installed", False):
        return

    original_send_message = bot_class.send_message

    async def wrapped_send_message(self, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        if chat_id is None and args:
            chat_id = args[0]
        text = kwargs.get("text")
        if text is None and len(args) > 1:
            text = args[1]
        text = str(text or "")

        result = await original_send_message(self, *args, **kwargs)

        if result and chat_id in _cleanup_group_ids():
            schedule_cleanup(application, result)

        return result

    bot_class.send_message = wrapped_send_message
    bot_class._melanated_chat_cleanup_installed = True
    logger.info(
        "Chat cleanup installed: temporary bot messages expire after %s seconds; daily community messages and raffle topic posts are preserved; admin-group notification mirroring DISABLED; persistent store=%s.",
        CLEANUP_SECONDS,
        MESSAGE_STORE,
    )
