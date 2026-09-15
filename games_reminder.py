# ==========================================================
# Melanated AZ - Game Center Reminder
# ==========================================================
#
# Keeps the permanent Games-topic launcher and sends the
# weekly reminder. The launcher exposes BOTH game systems:
#
#   1. Telegram Game Center games (games/game_center.py)
#   2. Real Games web library (real_games/)
#
# Truth or Dare is a Telegram Game Center game and is exposed
# directly from the Games-topic launcher.
# Dirty Minds is a multiplayer Real Game and is exposed through
# the Real Games library because it requires a room/player key.
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
from games.game_center import games_home_keyboard
from games.game_center import games_play_callback

logger = logging.getLogger("melanated_az.games_reminder")

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
    """Expose the Telegram Game Center AND the Real Games library."""
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
            InlineKeyboardButton("👤 My Profile", callback_data="games_profile"),
            InlineKeyboardButton("🏆 Leaderboards", callback_data="games_leaderboards"),
        ],
    ])


LAUNCHER_TEXT = (
    "🎮🔥 <b>MELANATED AZ GAME CENTER</b> 🔥🎮\n\n"
    "The Games topic now has <b>both game systems</b> in one place!\n\n"
    "🎮 <b>Game Center</b> — Telegram games, XP, AZ Coins & leaderboards\n"
    "🔥 <b>Truth or Dare</b> — jump straight into the party game\n"
    "🌐 <b>Real Game Library</b> — Snake, Pong, Breakout, Tetris, Flappy,\n"
    "Chess, Checkers, Monopoly, Basketball, Target Shooter, card games and more\n"
    "🎭 <b>Dirty Minds</b> — multiplayer party game with rooms\n\n"
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
    """Register the combined Games launcher and weekly reminder."""
    if not getattr(application, "job_queue", None):
        logger.warning("Games reminder unavailable: JobQueue not installed.")
        return

    for name in ("games-topic-launcher", "weekly-game-center-reminder"):
        for job in application.job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    application.job_queue.run_once(
        ensure_games_topic_launcher,
        when=10,
        name="games-topic-launcher",
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
        "Games reminder scheduled | Friday %02d:%02d Arizona | chat=%s | topic=%s",
        WEEKLY_REMINDER_HOUR,
        WEEKLY_REMINDER_MINUTE,
        _main_group_id(),
        GAMES_TOPIC_ID,
    )
