# ==========================================================
# Melanated AZ - Game Center Reminder
# COMPLETE DROP-IN MODULE
#
# Purpose:
#   - Keeps a permanent Game Center launcher in the Games topic.
#   - Pins the launcher in the Games topic.
#   - Sends a weekly reminder in the MAIN chat.
#   - Main-chat reminder links directly to the Games topic.
#
# Schedule:
#   Friday at 7:00 PM Arizona time.
#
# Existing games are not changed.
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

logger = logging.getLogger("melanated_az.games_reminder")

ARIZONA_TZ = ZoneInfo("America/Phoenix")
GAMES_TOPIC_ID = int(os.environ.get("GAMES_TOPIC_ID", "8809") or "8809")
WEEKLY_REMINDER_HOUR = int(os.environ.get("GAMES_REMINDER_HOUR", "19") or "19")
WEEKLY_REMINDER_MINUTE = int(os.environ.get("GAMES_REMINDER_MINUTE", "0") or "0")
STATE_FILE = Path(os.environ.get("GAMES_REMINDER_STATE_FILE", "/var/data/games_reminder.json"))

# Friday = 4 in Python's Monday=0 weekday numbering.
REMINDER_WEEKDAY = 4


def _main_group_id():
    try:
        return int(os.environ.get("MAIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        return 0


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
    """Build the direct Telegram link for the configured Games topic."""
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


async def ensure_games_topic_launcher(context):
    """Create/update and pin the Game Center launcher in the Games topic.

    IMPORTANT: A previously saved message ID is only reusable when this state
    record explicitly belongs to the current Games topic. Older state files did
    not store the topic ID, so those message IDs are treated as stale instead of
    risking an edit of the Introduction launcher.
    """
    main_group_id = _main_group_id()
    if not main_group_id:
        logger.warning("Game Center launcher skipped: MAIN_GROUP_ID is not configured.")
        return None

    state = _load_state()
    launcher_message_id = state.get("games_topic_launcher_message_id")
    saved_topic_id = state.get("games_topic_launcher_topic_id")
    reusable_launcher = False

    try:
        reusable_launcher = (
            int(saved_topic_id) == int(GAMES_TOPIC_ID)
            and int(launcher_message_id) > 0
        )
    except (TypeError, ValueError):
        reusable_launcher = False

    # A legacy/incorrect state entry may point at the Introduction topic. Never
    # edit it as the Game Center launcher. Remove the stale state and, when
    # possible, remove that bot-owned message so the bad Game Center post does
    # not remain in the Introduction topic.
    if launcher_message_id and not reusable_launcher:
        logger.warning(
            "Ignoring stale Game Center launcher state: message=%s saved_topic=%s expected_topic=%s",
            launcher_message_id,
            saved_topic_id,
            GAMES_TOPIC_ID,
        )
        try:
            await context.bot.delete_message(
                chat_id=main_group_id,
                message_id=int(launcher_message_id),
            )
            logger.info(
                "Removed stale Game Center launcher message %s from chat %s.",
                launcher_message_id,
                main_group_id,
            )
        except (TelegramError, TypeError, ValueError):
            logger.info(
                "Could not remove stale Game Center launcher message %s; continuing with a new Games-topic launcher.",
                launcher_message_id,
            )
        state.pop("games_topic_launcher_message_id", None)
        state.pop("games_topic_launcher_topic_id", None)
        _save_state(state)
        launcher_message_id = None

    text = (
        "🎮 <b>MELANATED AZ GAME CENTER</b> 🎮\n\n"
        "Welcome to the Games topic! 🔥\n\n"
        "🎮 <b>GAMEE</b> — Pick a game and play\n"
        "😈 <b>DIRTY MINDS</b> — See how dirty your mind really is 👀\n\n"
        "🔥 Challenge somebody\n"
        "🏆 Compete for bragging rights\n"
        "😂 Have some fun with the crew\n\n"
        "👇 <b>ENTER THE GAME CENTER & START PLAYING!</b>"
    )

    # GAMEE opens Telegram's GAMEE bot. Dirty Minds remains in the existing
    # Melanated AZ system and can be reached from the existing Games controls.
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 GAMEE — PLAY NOW", url="https://t.me/gamee")],
    ])

    if launcher_message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=main_group_id,
                message_id=int(launcher_message_id),
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            try:
                await context.bot.pin_chat_message(
                    chat_id=main_group_id,
                    message_id=int(launcher_message_id),
                    disable_notification=True,
                )
            except TelegramError:
                logger.warning("Game Center launcher exists but could not be pinned.")
            return int(launcher_message_id)
        except TelegramError:
            logger.info("Saved Game Center launcher message is no longer available; creating a new one.")

    try:
        sent = await context.bot.send_message(
            chat_id=main_group_id,
            message_thread_id=GAMES_TOPIC_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.exception(
            "Could not create Game Center launcher in Games topic | chat=%s | topic=%s",
            main_group_id,
            GAMES_TOPIC_ID,
        )
        return None

    state["games_topic_launcher_message_id"] = sent.message_id
    state["games_topic_launcher_topic_id"] = GAMES_TOPIC_ID
    _save_state(state)

    try:
        await context.bot.pin_chat_message(
            chat_id=main_group_id,
            message_id=sent.message_id,
            disable_notification=True,
        )
    except TelegramError:
        logger.warning(
            "Game Center launcher posted but could not be pinned | message=%s",
            sent.message_id,
        )

    logger.info(
        "Game Center launcher ready | chat=%s | topic=%s | message=%s",
        main_group_id,
        GAMES_TOPIC_ID,
        sent.message_id,
    )
    return sent.message_id


async def send_weekly_game_center_reminder(context):
    """Send the weekly Game Center reminder to the main chat."""
    main_group_id = _main_group_id()
    if not main_group_id:
        logger.warning("Weekly Game Center reminder skipped: MAIN_GROUP_ID is not configured.")
        return

    state = _load_state()
    launcher_message_id = state.get("games_topic_launcher_message_id")
    saved_topic_id = state.get("games_topic_launcher_topic_id")

    try:
        launcher_message_id = (
            int(launcher_message_id)
            if int(saved_topic_id) == int(GAMES_TOPIC_ID)
            else None
        )
    except (TypeError, ValueError):
        launcher_message_id = None

    if launcher_message_id:
        games_link = _telegram_message_link(main_group_id, launcher_message_id)
    else:
        games_link = _topic_link(main_group_id)

    if not games_link:
        logger.warning("Weekly Game Center reminder skipped: could not build Games topic link.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 ENTER THE GAME CENTER", url=games_link)],
    ])

    text = (
        "🎮 <b>GAME CENTER REMINDER!</b> 🎮\n\n"
        "Don’t forget to pull up to the <b>🎮 Games topic</b> and get your game on!\n\n"
        "🎮 <b>GAMEE</b> — Pick a game and play\n"
        "😈 <b>DIRTY MINDS</b> — See how dirty your mind really is 👀\n\n"
        "🔥 Challenge somebody\n"
        "🏆 Compete for bragging rights\n"
        "😂 Have some fun with the crew\n\n"
        "👇 <b>TAP BELOW TO ENTER THE GAME CENTER & START PLAYING!</b> 🎮"
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
    """Register the weekly Game Center launcher/reminder jobs."""
    if not getattr(application, "job_queue", None):
        logger.warning("Weekly Game Center reminder unavailable: JobQueue not installed.")
        return

    # Remove duplicates after bot restarts/deploys.
    for name in ("games-topic-launcher", "weekly-game-center-reminder"):
        for job in application.job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    # Ensure the pinned Games-topic launcher shortly after startup.
    application.job_queue.run_once(
        ensure_games_topic_launcher,
        when=10,
        name="games-topic-launcher",
    )

    # Weekly reminder every Friday at 7:00 PM Arizona time.
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
        "Weekly Game Center reminder scheduled | Friday %02d:%02d | timezone=%s | main_chat=%s | games_topic=%s",
        WEEKLY_REMINDER_HOUR,
        WEEKLY_REMINDER_MINUTE,
        ARIZONA_TZ.key,
        _main_group_id(),
        GAMES_TOPIC_ID,
    )
