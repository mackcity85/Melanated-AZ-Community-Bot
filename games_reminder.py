# ==========================================================
# Melanated AZ - Game Center Reminder
# ==========================================================
#
# Daily community messages and centralized chat cleanup remain
# enabled here. Automatic Games-topic launcher/reminder posts
# are intentionally disabled; the owner will post Games content
# manually when desired.
#
# Raffle auto-sync/pin management is intentionally NOT started
# here. Raffles are managed by raffle.py / bot.py when created.
#
# IMPORTANT:
# This module MUST NOT repost or recreate the Games launcher
# or send recurring Games reminders on bot startup.
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

from games.game_center import GAMES_CHAT_ID, GAMES_TOPIC_ID
from daily_messages import start_daily_community_messages
from chat_cleanup import install_chat_cleanup, startup_cleanup
from raffle_database import get_active_raffle, set_raffle_post
from raffle import publish_raffle

logger = logging.getLogger("melanatedaz.games_reminder")

ARIZONA_TZ = ZoneInfo("America/Phoenix")
WEEKLY_REMINDER_HOUR = int(os.environ.get("GAMES_REMINDER_HOUR", "19") or "19")
WEEKLY_REMINDER_MINUTE = int(os.environ.get("GAMES_REMINDER_MINUTE", "0") or "0")
STATE_FILE = Path(os.environ.get("GAMES_REMINDER_STATE_FILE", "/var/data/games_reminder.json"))
LAUNCHER_STATE_FILE = Path("/var/data/games_topic_launcher.json")
RAFFLE_REPAIR_MARKER = Path("/var/data/raffle_topic_11883_repair_v2.done")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://melanatedaz.onrender.com").strip().rstrip("/")
REMINDER_WEEKDAY = 4  # Friday


def _main_group_id():
    try:
        return int(os.environ.get("MAIN_GROUP_ID", str(GAMES_CHAT_ID)) or str(GAMES_CHAT_ID))
    except (TypeError, ValueError):
        return GAMES_CHAT_ID


def _telegram_message_link(chat_id, message_id):
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


def _load_launcher_id():
    try:
        if LAUNCHER_STATE_FILE.exists():
            with LAUNCHER_STATE_FILE.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict) and int(data.get("topic_id", 0)) == GAMES_TOPIC_ID:
                message_id = int(data.get("message_id", 0))
                return message_id if message_id > 0 else None
    except Exception:
        logger.exception("Could not read Games-topic launcher state.")
    return None


def _save_launcher_id(message_id):
    try:
        LAUNCHER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = LAUNCHER_STATE_FILE.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump({"message_id": int(message_id), "topic_id": GAMES_TOPIC_ID}, handle, indent=2)
        temp.replace(LAUNCHER_STATE_FILE)
    except Exception:
        logger.exception("Could not save Games-topic launcher state.")


def _launcher_keyboard():
    rows = [
        [
            InlineKeyboardButton("🎮 OPEN GAME CENTER", callback_data="games_home"),
            InlineKeyboardButton("🌐 REAL GAME LIBRARY", url=f"{PUBLIC_BASE_URL}/real-games/"),
        ],
        [
            InlineKeyboardButton("🔥 TRUTH OR DARE", callback_data="games_play_truth_dare"),
            InlineKeyboardButton("🎭 DIRTY MINDS", url=f"{PUBLIC_BASE_URL}/real-games/"),
        ],
    ]

    active = get_active_raffle()
    if active:
        rows.append([
            InlineKeyboardButton(
                "🎟️ ENTER ACTIVE RAFFLE",
                callback_data=f"enter_{int(active['id'])}",
            )
        ])

    rows.append([
        InlineKeyboardButton("👤 My Profile", callback_data="games_profile"),
        InlineKeyboardButton("🏆 Leaderboards", callback_data="games_leaderboards"),
    ])
    return InlineKeyboardMarkup(rows)


LAUNCHER_TEXT = (
    "🎮🔥 <b>MELANATED AZ GAME CENTER</b> 🔥🎮\n\n"
    "The Games topic has <b>both game systems</b> in one place!\n\n"
    "🎮 <b>Game Center</b> — Telegram games, XP, AZ Coins & leaderboards\n"
    "🔥 <b>Truth or Dare</b> — jump straight into the party game\n"
    "🌐 <b>Real Game Library</b> — Snake, Pong, Breakout, Tetris, Flappy,\n"
    "Chess, Checkers, Monopoly, Basketball, Target Shooter, card games and more\n"
    "🎭 <b>Dirty Minds</b> — multiplayer party game with rooms\n"
    "🎟️ <b>Raffle</b> — the button appears here whenever a raffle is active\n\n"
    "👇 <b>PICK A GAME AND START PLAYING!</b>"
)


async def ensure_games_topic_launcher(context):
    """Legacy launcher function retained for compatibility; never scheduled automatically."""
    logger.info("Automatic Games-topic launcher is disabled; no post created.")
    return None


async def repair_active_raffle_topic(context):
    """Legacy raffle repair function retained for compatibility; not scheduled here."""
    if RAFFLE_REPAIR_MARKER.exists():
        return

    raffle = get_active_raffle()
    if not raffle:
        logger.info("Raffle topic v2 repair skipped: no active raffle.")
        return

    raffle_id = int(raffle["id"])
    try:
        # Do not write None into raffle post fields.
        published = await publish_raffle(raffle_id, context)
        if published:
            RAFFLE_REPAIR_MARKER.parent.mkdir(parents=True, exist_ok=True)
            RAFFLE_REPAIR_MARKER.write_text(f"raffle={raffle_id}\n", encoding="utf-8")
            logger.info("RAFFLE TOPIC V2 REPAIR COMPLETE | raffle=%s | topic=11883", raffle_id)
        else:
            logger.error("RAFFLE TOPIC V2 REPAIR FAILED | raffle=%s | topic=11883", raffle_id)
    except Exception:
        logger.exception("Raffle topic v2 repair failed | raffle=%s", raffle_id)


async def send_weekly_game_center_reminder(context):
    """Legacy weekly reminder function retained for compatibility; never scheduled automatically."""
    logger.info("Automatic weekly Games reminder is disabled; no post created.")
    return None


async def disable_daily_raffle_status(context):
    """Keep raffle status scheduling disabled even though legacy bot.py registers it."""
    job_queue = getattr(context.application, "job_queue", None)
    if not job_queue:
        return

    removed = 0
    for job in job_queue.get_jobs_by_name("daily-raffle-status"):
        job.schedule_removal()
        removed += 1

    if removed:
        logger.info("Automatic raffle status disabled: removed %s daily-raffle-status job(s).", removed)


def start_weekly_game_center_reminder(application):
    """Keep cleanup/daily community services; disable all automatic Games posts."""
    if not getattr(application, "job_queue", None):
        logger.warning("Games reminder unavailable: JobQueue not installed.")
        return

    install_chat_cleanup(application)

    application.job_queue.run_once(
        startup_cleanup,
        when=5,
        name="persistent-bot-message-cleanup",
    )

    start_daily_community_messages(application)

    # Explicitly remove any legacy Games jobs that may have been registered
    # by an earlier version during the same process lifetime.
    disabled_names = (
        "games-topic-launcher",
        "weekly-game-center-reminder",
        "raffle-topic-v2-repair",
        "disable-daily-raffle-status",
    )
    for name in disabled_names:
        for job in application.job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    logger.info(
        "Automatic Games posts DISABLED | no Games launcher | no weekly Games reminder | no automatic Games pin | daily community messages remain enabled | persistent cleanup enabled"
    )
