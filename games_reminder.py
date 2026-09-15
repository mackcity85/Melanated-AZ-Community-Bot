# ==========================================================
# Melanated AZ - Game Center Reminder
# ==========================================================
#
# Keeps the permanent Games-topic launcher, makes sure the
# Introduction launcher is posted on startup, sends the weekly
# Games reminder, starts daily community messages, installs
# centralized chat cleanup/admin notifications, and manages
# the dedicated active-raffle pin.
# ==========================================================

import json
import logging
import os
import re
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

from games.game_center import GAMES_CHAT_ID, GAMES_TOPIC_ID
from daily_messages import start_daily_community_messages
from chat_cleanup import install_chat_cleanup
from raffle_pin_manager import start_raffle_pin_manager

logger = logging.getLogger("melanatedaz.games_reminder")

ARIZONA_TZ = ZoneInfo("America/Phoenix")
WEEKLY_REMINDER_HOUR = int(os.environ.get("GAMES_REMINDER_HOUR", "19") or "19")
WEEKLY_REMINDER_MINUTE = int(os.environ.get("GAMES_REMINDER_MINUTE", "0") or "0")
STATE_FILE = Path(os.environ.get("GAMES_REMINDER_STATE_FILE", "/var/data/games_reminder.json"))
LAUNCHER_STATE_FILE = Path("/var/data/games_topic_launcher.json")
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
    """Expose game systems and the active raffle from the Games topic."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎮 OPEN GAME CENTER", callback_data="games_home"),
            InlineKeyboardButton("🌐 REAL GAME LIBRARY", url=f"{PUBLIC_BASE_URL}/real-games/"),
        ],
        [
            InlineKeyboardButton("🔥 TRUTH OR DARE", callback_data="games_play_truth_dare"),
            InlineKeyboardButton("🎭 DIRTY MINDS", url=f"{PUBLIC_BASE_URL}/real-games/"),
        ],
        [
            InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data="raffle_enter_active"),
        ],
        [
            InlineKeyboardButton("👤 My Profile", callback_data="games_profile"),
            InlineKeyboardButton("🏆 Leaderboards", callback_data="games_leaderboards"),
        ],
    ])


LAUNCHER_TEXT = (
    "🎮🔥 <b>MELANATED AZ GAME CENTER</b> 🔥🎮\n\n"
    "The Games topic has <b>both game systems</b> in one place!\n\n"
    "🎮 <b>Game Center</b> — Telegram games, XP, AZ Coins & leaderboards\n"
    "🔥 <b>Truth or Dare</b> — jump straight into the party game\n"
    "🌐 <b>Real Game Library</b> — Snake, Pong, Breakout, Tetris, Flappy,\n"
    "Chess, Checkers, Monopoly, Basketball, Target Shooter, card games and more\n"
    "🎭 <b>Dirty Minds</b> — multiplayer party game with rooms\n"
    "🎟️ <b>Raffle</b> — enter the currently active raffle\n\n"
    "👇 <b>PICK A GAME AND START PLAYING!</b>"
)


async def ensure_games_topic_launcher(context):
    """Create/update and pin the combined Games-topic launcher."""
    chat_id = _main_group_id()
    if not chat_id:
        logger.warning("Games launcher skipped: MAIN_GROUP_ID is not configured.")
        return None

    existing_message_id = _load_launcher_id()

    if existing_message_id:
        try:
            message = await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=existing_message_id,
                text=LAUNCHER_TEXT,
                reply_markup=_launcher_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            try:
                await context.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=existing_message_id,
                    disable_notification=True,
                )
            except TelegramError:
                logger.warning("Games-topic launcher exists but could not be pinned.")
            return message.message_id
        except TelegramError:
            logger.info("Saved Games-topic launcher is unavailable; creating a new launcher.")

    try:
        sent = await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=GAMES_TOPIC_ID,
            text=LAUNCHER_TEXT,
            reply_markup=_launcher_keyboard(),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.exception(
            "Could not create Games-topic launcher | chat=%s | topic=%s",
            chat_id,
            GAMES_TOPIC_ID,
        )
        return None

    _save_launcher_id(sent.message_id)

    try:
        await context.bot.pin_chat_message(
            chat_id=chat_id,
            message_id=sent.message_id,
            disable_notification=True,
        )
    except TelegramError:
        logger.warning("Games-topic launcher posted but could not be pinned.")

    logger.info(
        "Combined Games-topic launcher ready | chat=%s | topic=%s | message=%s",
        chat_id,
        GAMES_TOPIC_ID,
        sent.message_id,
    )
    return sent.message_id


async def ensure_introduction_launcher(context):
    """Post the existing Introduction launcher and pin the exact message."""
    try:
        from bot import post_intro_topic_reminder

        ok, detail = await post_intro_topic_reminder(context)

        if ok:
            logger.info("Introduction launcher ready: %s", detail)

            match = re.search(r"message\s+(\d+)", detail or "", flags=re.IGNORECASE)
            if not match:
                logger.error("Introduction launcher posted but message ID was not returned: %s", detail)
                return False

            message_id = int(match.group(1))
            chat_id = _main_group_id()

            try:
                await context.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=message_id,
                    disable_notification=True,
                )
                logger.info(
                    "Introduction launcher pinned | chat=%s | topic=%s | message=%s",
                    chat_id,
                    os.environ.get("INTRO_TOPIC_ID", "11570"),
                    message_id,
                )
            except TelegramError as exc:
                logger.exception(
                    "Introduction launcher posted but could not be pinned | chat=%s | message=%s | error=%s",
                    chat_id,
                    message_id,
                    exc,
                )
                return False

            return True

        logger.error("Introduction launcher FAILED: %s", detail)
        return False

    except Exception:
        logger.exception("Could not launch the Introduction topic button.")
        return False


async def send_weekly_game_center_reminder(context):
    """Send the weekly Games reminder to the main chat."""
    chat_id = _main_group_id()
    if not chat_id:
        return

    launcher_id = _load_launcher_id()
    games_link = _telegram_message_link(chat_id, launcher_id) if launcher_id else _topic_link(chat_id)
    if not games_link:
        logger.warning("Weekly Games reminder skipped: no valid Games-topic link.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 ENTER THE GAME CENTER", url=games_link)],
    ])

    text = (
        "🎮 <b>GAME NIGHT REMINDER!</b> 🎮\n\n"
        "Pull up to the <b>Games topic</b> and pick your game!\n\n"
        "🔥 Truth or Dare\n"
        "🎭 Dirty Minds\n"
        "🐍 Snake • 🏓 Pong • 🧱 Breakout\n"
        "♟️ Chess • Checkers • Monopoly\n"
        "🏀 Basketball • 🎯 Target Shooter\n"
        "🃏 Blackjack • UNO • Solitaire\n\n"
        "👇 <b>TAP BELOW TO PLAY!</b>"
    )

    try:
        sent = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        logger.info("Weekly Games reminder posted | message=%s", sent.message_id)
    except TelegramError:
        logger.exception("Could not send weekly Games reminder.")


def start_weekly_game_center_reminder(application):
    """Register topic launchers, weekly Games reminder, daily messages, chat cleanup, and raffle pin management."""
    if not getattr(application, "job_queue", None):
        logger.warning("Games reminder unavailable: JobQueue not installed.")
        return

    install_chat_cleanup(application)
    start_daily_community_messages(application)
    start_raffle_pin_manager(application)

    for name in (
        "games-topic-launcher",
        "introduction-topic-launcher",
        "weekly-game-center-reminder",
    ):
        for job in application.job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    application.job_queue.run_once(
        ensure_games_topic_launcher,
        when=10,
        name="games-topic-launcher",
    )

    application.job_queue.run_once(
        ensure_introduction_launcher,
        when=12,
        name="introduction-topic-launcher",
    )

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
        "Games + Introduction launchers scheduled | Games topic=%s | Intro topic startup=12s | Friday %02d:%02d Arizona | daily community messages active | raffle pin manager active",
        GAMES_TOPIC_ID,
        WEEKLY_REMINDER_HOUR,
        WEEKLY_REMINDER_MINUTE,
    )
