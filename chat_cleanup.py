# ==========================================================
# Melanated AZ Bot - Chat Cleanup + Admin Notification Mirror
# ==========================================================

import html
import json
import logging
import os
from pathlib import Path

from telegram import Message
from telegram.error import TelegramError
from telegram.ext import MessageHandler, filters

logger = logging.getLogger("melanatedaz.chat_cleanup")

CLEANUP_SECONDS = int(os.environ.get("CHAT_CLEANUP_SECONDS", "180") or "180")
INTRO_TOPIC_ID = int(os.environ.get("INTRO_TOPIC_ID", "11570") or "11570")
RAFFLE_TOPIC_ID = 11883
GAMES_TOPIC_ID = 8809
INTRO_STATE_FILE = Path("/var/data/introduction_topic_launcher.txt")
GAMES_LAUNCHER_FILE = Path("/var/data/games_topic_launcher.json")
GAME_CENTER_PIN_FILE = Path("/var/data/game_center_pin.txt")


def _main_group_id():
    raw = os.environ.get("MAIN_GROUP_ID", "") or ""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _admin_group_id():
    raw = os.environ.get("ADMIN_GROUP_ID", "") or ""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _read_int_file(path):
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError, OSError):
        return None


def _games_launcher_id():
    try:
        data = json.loads(GAMES_LAUNCHER_FILE.read_text(encoding="utf-8"))
        value = int(data.get("message_id", 0))
        return value if value > 0 else None
    except (FileNotFoundError, ValueError, TypeError, OSError, json.JSONDecodeError):
        return None


def _is_daily_community_message(text):
    value = (text or "").strip()
    return "Keep it grown, keep it respectful" in value and "PASS is always allowed" in value


def _is_active_raffle_post(chat_id, thread_id, text):
    """The official active raffle post is permanent while the raffle is live."""
    if chat_id != _main_group_id() or thread_id != RAFFLE_TOPIC_ID:
        return False
    value = (text or "").strip()
    return value.startswith("🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b>")


def _is_raffle_navigation_message(chat_id, thread_id, text):
    if chat_id != _main_group_id() or thread_id:
        return False
    value = (text or "").strip()
    return value.startswith("📌 <b>RAFFLE NAVIGATION</b>")


def _is_permanent_launcher(chat_id, thread_id, message_id, text):
    if chat_id != _main_group_id():
        return False
    if _is_daily_community_message(text):
        return True
    if _is_active_raffle_post(chat_id, thread_id, text):
        return True
    if _is_raffle_navigation_message(chat_id, thread_id, text):
        return True
    if message_id in {_read_int_file(GAME_CENTER_PIN_FILE), _games_launcher_id()}:
        return True
    if thread_id == INTRO_TOPIC_ID and "Submit My Introduction" in (text or ""):
        stored = _read_int_file(INTRO_STATE_FILE)
        if stored is None:
            try:
                INTRO_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                INTRO_STATE_FILE.write_text(str(message_id), encoding="utf-8")
                return True
            except OSError:
                logger.exception("Could not persist Introduction launcher ID.")
        return stored == message_id
    return False


async def _delete_after(context):
    data = context.job.data or {}
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")
    thread_id = data.get("thread_id")
    text = data.get("text", "")
    if not chat_id or not message_id:
        return
    if _is_permanent_launcher(chat_id, thread_id, message_id, text):
        return
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError as exc:
        logger.debug("Cleanup delete skipped | chat=%s message=%s | %s", chat_id, message_id, exc)


def schedule_cleanup(application, message):
    if not getattr(application, "job_queue", None):
        return
    application.job_queue.run_once(
        _delete_after,
        when=CLEANUP_SECONDS,
        data={
            "chat_id": message.chat_id,
            "message_id": message.message_id,
            "thread_id": getattr(message, "message_thread_id", None),
            "text": message.text or message.caption or "",
        },
        name=f"chat-cleanup-{message.chat_id}-{message.message_id}",
    )


def _is_service_message(message: Message):
    service_fields = (
        "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo",
        "delete_chat_photo", "group_chat_created", "supergroup_chat_created",
        "channel_chat_created", "migrate_to_chat_id", "migrate_from_chat_id",
        "pinned_message", "forum_topic_created", "forum_topic_closed",
        "forum_topic_reopened", "general_forum_topic_hidden",
        "general_forum_topic_unhidden", "write_access_allowed", "video_chat_started",
        "video_chat_ended", "video_chat_participants_invited", "users_shared", "chat_shared",
    )
    return any(getattr(message, field, None) for field in service_fields)


def _service_summary(message):
    if message.new_chat_members:
        names = ", ".join((u.full_name or str(u.id)) for u in message.new_chat_members)
        return f"👋 New member notification: {names}"
    if message.left_chat_member:
        user = message.left_chat_member
        return f"🚪 Member left: {user.full_name or user.id}"
    if message.pinned_message: return "📌 A message was pinned in the community."
    if message.forum_topic_created: return "🧵 A forum topic was created."
    if message.forum_topic_closed: return "🧵 A forum topic was closed."
    if message.forum_topic_reopened: return "🧵 A forum topic was reopened."
    if message.general_forum_topic_hidden: return "🧵 The General topic was hidden."
    if message.general_forum_topic_unhidden: return "🧵 The General topic was unhidden."
    if message.new_chat_title: return f"✏️ Community title changed: {message.new_chat_title}"
    if message.new_chat_photo: return "🖼️ Community photo changed."
    if message.delete_chat_photo: return "🖼️ Community photo removed."
    return "🔔 Telegram community service notification."


async def cleanup_service_messages(update, context):
    message = update.effective_message
    if not message or message.chat_id != _main_group_id() or not _is_service_message(message):
        return
    admin_id = _admin_group_id()
    if admin_id:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=("<b>🔔 COMMUNITY NOTIFICATION</b>\n\n" f"{html.escape(_service_summary(message))}"),
                parse_mode="HTML",
            )
        except TelegramError as exc:
            logger.warning("Could not mirror service notification to admins: %s", exc)
    try:
        await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
    except TelegramError as exc:
        logger.debug("Service-message cleanup skipped: %s", exc)


def install_chat_cleanup(application):
    if getattr(application, "_melanated_chat_cleanup_installed", False):
        return
    application._melanated_chat_cleanup_installed = True
    application.add_handler(MessageHandler(filters.ALL, cleanup_service_messages), group=20)
    bot = application.bot
    bot_class = type(bot)
    if getattr(bot_class, "_melanated_chat_cleanup_patched", False):
        logger.info("Chat cleanup already patched on bot class | main=%s | admin=%s | temporary messages=%ss", _main_group_id(), _admin_group_id(), CLEANUP_SECONDS)
        return
    original_send_message = bot_class.send_message

    async def wrapped_send_message(self, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        if chat_id is None and args: chat_id = args[0]
        thread_id = kwargs.get("message_thread_id")
        text = kwargs.get("text")
        if text is None and len(args) > 1: text = args[1]
        text = str(text or "")
        result = await original_send_message(self, *args, **kwargs)
        main_id = _main_group_id()
        admin_id = _admin_group_id()
        if main_id is not None and chat_id == main_id and result:
            is_daily = _is_daily_community_message(text)
            is_permanent = _is_permanent_launcher(main_id, thread_id, result.message_id, text)
            if not is_permanent:
                schedule_cleanup(application, result)
            if admin_id and (not is_permanent or is_daily):
                try:
                    topic_note = f"\n📍 Topic ID: {thread_id}" if thread_id else ""
                    admin_text = "<b>🔔 BOT NOTIFICATION</b>" f"{html.escape(topic_note)}\n\n" f"{html.escape(text[:3800])}"
                    await original_send_message(self, chat_id=admin_id, text=admin_text, parse_mode="HTML")
                except TelegramError as exc:
                    logger.warning("Could not mirror bot notification to admin group: %s", exc)
        return result

    bot_class.send_message = wrapped_send_message
    bot_class._melanated_chat_cleanup_patched = True
    logger.info("Chat cleanup installed | main=%s | admin=%s | temporary messages=%ss", _main_group_id(), _admin_group_id(), CLEANUP_SECONDS)
