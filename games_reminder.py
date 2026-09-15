# ==========================================================
# Melanated AZ - Game Center Reminder
#
# Purpose:
#   - Uses the REAL Game Center launcher from games/game_center.py.
#   - Keeps the launcher in the Games topic.
#   - Pins the launcher in the Games topic.
#   - Sends a weekly reminder in the MAIN chat.
#
# IMPORTANT:
#   This module does NOT create a separate GAMEE launcher.
#   The actual Game Center buttons are owned by game_center.py.
# ==========================================================

import json
import logging
import os
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

from games.game_center import (
    GAMES_CHAT_ID,
    GAMES_TOPIC_ID,
    ensure_pinned_game_center,
)

logger = logging.getLogger("melanated_az.games_reminder")

ARIZONA_TZ = ZoneInfo("America/Phoenix")
WEEKLY_REMINDER_HOUR = int(os.environ.get("GAMES_REMINDER_HOUR", "19") or "19")
WEEKLY_REMINDER_MINUTE = int(os.environ.get("GAMES_REMINDER_MINUTE", "0") or "0")
STATE_FILE = Path(os.environ.get("GAMES_REMINDER_STATE_FILE", "/var/data/games_reminder.json"))
LEGACY_MIGRATION_FILE = Path("/var/data/game_center_launcher_v2_migrated")
GAME_CENTER_PIN_FILE = Path("/var/data/game_center_pin.txt")

# Friday = 4 in Python's Monday=0 weekday numbering.
REMINDER_WEEKDAY = 4


def _main_group_id():
    try:
        return int(os.environ.get("MAIN_GROUP_ID", str(GAMES_CHAT_ID)) or str(GAMES_CHAT_ID))
    except (TypeError, ValueError):
        return int(GAMES_CHAT_ID)


def _telegram_message_link(chat_id, message_id):
    """Build a private-supergroup message link."""
    try:
        chat_id = int(chat_id)
        message_id = int(message_id)
    except (TypeError, ValueError):
        return None

    if chat_id >= 0:
        return None

    internal_id = str(abs(chat_id))
    if internal_id.startswith("100"):
        internal_id = internal_id[3:]
    return f"https://t.me/c/{internal_id}/{message_id}"


def _topic_link(chat_id):
    """Build the direct Telegram link for the Games topic."""
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return None

    if chat_id >= 0:
        return None

    internal_id = str(abs(chat_id))
    if internal_id.startswith("100"):
        internal_id = internal_id[3:]
    return f"https://t.me/c/{internal_id}/{GAMES_TOPIC_ID}"


def _load_state():
    try:
        if STATE_FILE.exists():
            with STATE_FILE.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                return data if isinstance(data, dict) else {}
    except Exception:
        logger.exception("Could not read Game Center reminder state file.")
    return {}


def _save_state(data):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = STATE_FILE.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        temp.replace(STATE_FILE)
    except Exception:
        logger.exception("Could not save Game Center reminder state file.")


async def _migrate_legacy_game_center_pin(context):
    """Reset the old launcher state once so the real Game Center owns it."""
    if LEGACY_MIGRATION_FILE.exists():
        return

    old_message_id = None
    try:
        if GAME_CENTER_PIN_FILE.exists():
            old_message_id = GAME_CENTER_PIN_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        logger.exception("Could not inspect legacy Game Center pin state.")

    if old_message_id:
        try:
            await context.bot.delete_message(
                chat_id=GAMES_CHAT_ID,
                message_id=int(old_message_id),
            )
            logger.info("Removed legacy Game Center launcher message %s during migration.", old_message_id)
        except (TelegramError, TypeError, ValueError):
            logger.info("Legacy Game Center launcher %s could not be deleted; continuing.", old_message_id)

    try:
        GAME_CENTER_PIN_FILE.unlink(missing_ok=True)
    except Exception:
        logger.exception("Could not reset legacy Game Center pin file.")

    try:
        LEGACY_MIGRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        LEGACY_MIGRATION_FILE.write_text("migrated\n", encoding="utf-8")
    except Exception:
        logger.exception("Could not write Game Center migration marker.")


async def ensure_games_topic_launcher(context):
    """Delegate launcher creation to the actual Game Center module."""
    await _migrate_legacy_game_center_pin(context)
    return await ensure_pinned_game_center(context.bot)


async def send_weekly_game_center_reminder(context):
    """Send the weekly reminder to the main chat and link to the real launcher."""
    main_group_id = _main_group_id()
    if not main_group_id:
        logger.warning("Weekly Game Center reminder skipped: MAIN_GROUP_ID is not configured.")
        return

    state = _load_state()
    launcher_message_id = state.get("games_topic_launcher_message_id")
    saved_topic_id = state.get("games_topic_launcher_topic_id")

    # Prefer the authoritative Game Center pin file created by game_center.py.
    if GAME_CENTER_PIN_FILE.exists():
        try:
            launcher_message_id = int(GAME_CENTER_PIN_FILE.read_text(encoding="utf-8").strip())
        except (OSError, TypeError, ValueError):
            pass

    try:
        if saved_topic_id is not None and int(saved_topic_id) != int(GAMES_TOPIC_ID):
            launcher_message_id = None
    except (TypeError, ValueError):
        pass

    games_link = _telegram_message_link(GAMES_CHAT_ID, launcher_message_id) if launcher_message_id else _topic_link(GAMES_CHAT_ID)
    if not games_link:
        logger.warning("Weekly Game Center reminder skipped: could not build Games topic link.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 ENTER THE GAME CENTER", url=games_link)],
    ])

    text = (
        "🎮 <b>GAME CENTER REMINDER!</b> 🎮\n\n"
        "The real <b>Melanated AZ Game Center</b> is ready in the <b>Games</b> topic.\n\n"
        "🎮 Play the available games\n"
        "😈 Play <b>Dirty Minds</b>\n"
        "🏆 Check your profile and leaderboards\n"
        "🔥 Challenge the crew\n\n"
        "👇 <b>TAP BELOW TO ENTER THE GAME CENTER!</b>"
    )

    try:
        sent = await context.bot.send_message(
            chat_id=main_group_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        logger.info(
            "Weekly Game Center reminder posted | chat=%s | message=%s",
            main_group_id,
            sent.message_id,
        )
    except TelegramError:
        logger.exception("Could not send weekly Game Center reminder.")


def start_weekly_game_center_reminder(application):
    """Register the real Game Center launcher and weekly reminder jobs."""
    if not getattr(application, "job_queue", None):
        logger.warning("Game Center scheduler unavailable: JobQueue not installed.")
        return

    for name in ("games-topic-launcher", "weekly-game-center-reminder"):
        for job in application.job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    # Startup launcher: this calls games/game_center.py, which owns the
    # OPEN GAME CENTER / My Profile / Leaderboards buttons.
    application.job_queue.run_once(
        ensure_games_topic_launcher,
        when=10,
        name="games-topic-launcher",
    )

    # Weekly Friday reminder at 7:00 PM Arizona time.
    application.job_queue.run_daily(
        send_weekly_game_center_reminder,
        time(
            hour=WEEKLY_REMINDER_HOUR,
            minute=WEEKLY_REMINDER_MINUTE,
            tzinfo=ARIZONA_TZ,
        ),
        days=(REMINDER_WEEKDAY,),
        name="weekly-game-center-reminder",
    )

    logger.info(
        "Game Center scheduler registered | Friday %02d:%02d | timezone=%s | chat=%s | topic=%s",
        WEEKLY_REMINDER_HOUR,
        WEEKLY_REMINDER_MINUTE,
        ARIZONA_TZ.key,
        GAMES_CHAT_ID,
        GAMES_TOPIC_ID,
    )
