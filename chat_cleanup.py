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
QOTD_TOPIC_ID = 11999
INTRO_TOPIC_ID = 11570
GAMES_TOPIC_ID = 8809
SOCIAL_MEDIA_TOPIC_ID = 9513
MEDIA_TOPIC_ID = 10286
EVENT_TOPIC_ID = 12214
PERMANENT_TOPIC_IDS = {RAFFLE_TOPIC_ID, QOTD_TOPIC_ID, INTRO_TOPIC_ID, GAMES_TOPIC_ID, SOCIAL_MEDIA_TOPIC_ID, MEDIA_TOPIC_ID, EVENT_TOPIC_ID}
MESSAGE_STORE = Path(os.environ.get("CHAT_CLEANUP_STORE", "/var/data/bot_cleanup_messages.json"))
DAILY_MESSAGE_MARKERS = ("DAILY COMMUNITY", "GOOD MORNING", "GOOD AFTERNOON", "GOOD EVENING", "COMMUNITY CHECK-IN", "CONFESSION TIME", "FLIRTY CONFESSION", "SPICY CONFESSION")

def _main_group_id():
    try:return int(os.environ.get("MAIN_GROUP_ID", "-1002697105809"))
    except (TypeError, ValueError):return -1002697105809

def _cleanup_group_ids():return {_main_group_id()}

def _is_daily_community_message(text: str) -> bool:
    upper = str(text or "").upper()
    return any(marker in upper for marker in DAILY_MESSAGE_MARKERS)

def _message_thread_id(message) -> int:
    try:return int(getattr(message, "message_thread_id", 0) or 0)
    except (TypeError, ValueError):return 0

def _is_permanent_topic_id(chat_id, thread_id) -> bool:
    try:return int(chat_id) == _main_group_id() and int(thread_id or 0) in PERMANENT_TOPIC_IDS
    except (TypeError, ValueError):return False

def _is_permanent_topic_message(message) -> bool:
    if not message:return False
    return _is_permanent_topic_id(getattr(message, "chat_id", None), _message_thread_id(message))

def _record_is_permanent_topic(record) -> bool:
    try:return _is_permanent_topic_id(record.get("chat_id"), record.get("thread_id", 0))
    except (TypeError, ValueError, AttributeError):return False

def _send_targets_permanent_topic(chat_id, kwargs) -> bool:
    if chat_id is None:return False
    return _is_permanent_topic_id(chat_id, kwargs.get("message_thread_id"))

def _load_store():
    try:
        if not MESSAGE_STORE.exists():return []
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
    except OSError as exc:logger.warning("Could not save bot cleanup store: %s", exc)

def _remember_message(message):
    if not message or message.chat_id not in _cleanup_group_ids():return
    text = getattr(message, "text", "") or getattr(message, "caption", "") or ""
    if _is_daily_community_message(text) or _is_permanent_topic_message(message):return
    records = _load_store()
    record = {"chat_id": int(message.chat_id), "message_id": int(message.message_id), "thread_id": _message_thread_id(message)}
    if record not in records:records.append(record)
    _save_store(records[-5000:])

def _forget_message(chat_id, message_id):
    records = _load_store()
    records = [r for r in records if not (r.get("chat_id") == chat_id and r.get("message_id") == message_id)]
    _save_store(records)

async def _delete_record(context, record):
    chat_id = record.get("chat_id")
    message_id = record.get("message_id")
    if chat_id is None or message_id is None or _record_is_permanent_topic(record):return
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        _forget_message(chat_id, message_id)
    except TelegramError as exc:
        text_error = str(exc).lower()
        if any(phrase in text_error for phrase in ("message to delete not found", "message not found", "message identifier is not valid", "message_id_invalid")):
            _forget_message(chat_id, message_id)
            return
        logger.warning("Cleanup delete failed %s/%s: %s", chat_id, message_id, exc)

async def _delete_after(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    if not job or not job.data:return
    await _delete_record(context, job.data)

def schedule_cleanup(application, message, delay=None):
    if not application or not message:return
    text = getattr(message, "text", "") or getattr(message, "caption", "") or ""
    if _is_daily_community_message(text) or _is_permanent_topic_message(message):return
    if message.chat_id not in _cleanup_group_ids():return
    _remember_message(message)
    seconds = CLEANUP_SECONDS if delay is None else delay
    record = {"chat_id": int(message.chat_id), "message_id": int(message.message_id), "thread_id": _message_thread_id(message)}
    application.job_queue.run_once(_delete_after, when=seconds, data=record, name=f"cleanup:{message.chat_id}:{message.message_id}")

async def startup_cleanup(application):
    records = _load_store()
    if not records:
        logger.info("Bot cleanup startup sweep: no stored bot messages.")
        return
    logger.info("Bot cleanup startup sweep: checking %s stored bot messages.", len(records))
    remaining = []
    for record in records:
        if _record_is_permanent_topic(record):
            remaining.append(record)
            continue
        if "thread_id" not in record:
            remaining.append(record)
            continue
        chat_id = record.get("chat_id")
        message_id = record.get("message_id")
        if chat_id not in _cleanup_group_ids() or not isinstance(message_id, int):continue
        try:
            await application.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info("Startup cleanup deleted bot message %s/%s.", chat_id, message_id)
        except TelegramError as exc:
            text_error = str(exc).lower()
            if any(phrase in text_error for phrase in ("message to delete not found", "message not found", "message identifier is not valid", "message_id_invalid")):
                continue
            remaining.append(record)
            logger.warning("Startup cleanup delete failed %s/%s: %s", chat_id, message_id, exc)
    _save_store(remaining[-5000:])

async def cleanup_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or message.chat_id != _main_group_id():return
    if _is_permanent_topic_message(message):return
    try:await message.delete()
    except TelegramError as exc:
        text_error = str(exc).lower()
        if any(phrase in text_error for phrase in ("message to delete not found", "message not found", "message identifier is not valid", "message_id_invalid")):
            return
        logger.warning("Could not delete service message: %s", exc)

def install_chat_cleanup(application):
    bot_class = application.bot.__class__
    if getattr(bot_class, "_melanated_chat_cleanup_installed", False):return
    original_send_message = bot_class.send_message
    async def wrapped_send_message(self, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        if chat_id is None and args:chat_id = args[0]
        permanent_target = _send_targets_permanent_topic(chat_id, kwargs)
        result = await original_send_message(self, *args, **kwargs)
        if result and chat_id in _cleanup_group_ids() and not permanent_target:schedule_cleanup(application, result)
        return result
    bot_class.send_message = wrapped_send_message
    bot_class._melanated_chat_cleanup_installed = True
