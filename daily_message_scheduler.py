# ==========================================================
# Melanated AZ - Reliable Daily Community Message Scheduler
# ==========================================================

import logging
import os
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram.constants import ParseMode
from telegram.error import TelegramError

from daily_messages import DAILY_MESSAGES
from games.game_center import GAMES_CHAT_ID

logger = logging.getLogger("melanatedaz.daily_message_scheduler")

ARIZONA_TZ = ZoneInfo("America/Phoenix")
DAILY_MESSAGE_HOUR = int(os.environ.get("DAILY_MESSAGE_HOUR", "10") or "10")
DAILY_MESSAGE_MINUTE = int(os.environ.get("DAILY_MESSAGE_MINUTE", "0") or "0")
DAILY_MESSAGE_START = datetime(2026, 9, 15, tzinfo=ARIZONA_TZ).date()
DAILY_MESSAGE_END = datetime(2027, 12, 31, tzinfo=ARIZONA_TZ).date()
DAILY_MESSAGE_JOB_NAME = "melanated-daily-community-message"
DAILY_MESSAGE_RECOVERY_JOB_NAME = "melanated-daily-community-message-recovery"
QOTD_TOPIC_ID = int(os.environ.get("QUESTION_OF_DAY_TOPIC_ID", "11999") or "11999")
STATE_FILE = Path(os.environ.get("DAILY_MESSAGE_STATE_FILE", "/var/data/daily_message_state.json"))


def _main_group_id():
    try:
        return int(os.environ.get("MAIN_GROUP_ID", str(GAMES_CHAT_ID)) or str(GAMES_CHAT_ID))
    except (TypeError, ValueError):
        return GAMES_CHAT_ID


def _today():
    return datetime.now(ARIZONA_TZ).date()


def _load_last_post_date():
    try:
        if STATE_FILE.exists():
            value = STATE_FILE.read_text(encoding="utf-8").strip()
            return datetime.strptime(value, "%Y-%m-%d").date() if value else None
    except Exception:
        logger.exception("Could not read daily message state.")
    return None


def _save_last_post_date(day):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = STATE_FILE.with_suffix(".tmp")
        temp.write_text(day.isoformat(), encoding="utf-8")
        temp.replace(STATE_FILE)
    except Exception:
        logger.exception("Could not save daily message state.")


def _message_for(day):
    index = (day - DAILY_MESSAGE_START).days % len(DAILY_MESSAGES)
    return index, DAILY_MESSAGES[index]


async def send_daily_community_message_reliable(context, day=None):
    """Post the configured day's message to QOTD topic 11999 exactly once."""
    target_day = day or _today()

    if target_day < DAILY_MESSAGE_START or target_day > DAILY_MESSAGE_END:
        logger.info("Daily community message skipped outside configured date range: %s", target_day)
        return False

    if _load_last_post_date() == target_day:
        logger.info("Daily community message already posted for %s; skipping duplicate.", target_day)
        return False

    chat_id = _main_group_id()
    if not chat_id:
        logger.error("Daily community message has no MAIN_GROUP_ID.")
        return False

    index, (title, prompt) = _message_for(target_day)
    text = (
        f"<b>{title}</b>\n\n"
        f"{prompt}\n\n"
        "😈 Keep it grown, keep it respectful, and remember: PASS is always allowed.\n"
        "👇 Drop your answer and see who matches your energy."
    )

    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=QOTD_TOPIC_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
        _save_last_post_date(target_day)
        logger.info(
            "Daily community message posted | date=%s | index=%s | chat=%s | topic=%s | message=%s",
            target_day,
            index,
            chat_id,
            QOTD_TOPIC_ID,
            getattr(message, "message_id", None),
        )
        return True
    except TelegramError:
        logger.exception(
            "Could not send daily community message | chat=%s | topic=%s | date=%s",
            chat_id,
            QOTD_TOPIC_ID,
            target_day,
        )
        return False


async def _startup_recovery(context):
    """Recover the latest missed scheduled day, then leave today's normal run independent."""
    now = datetime.now(ARIZONA_TZ)
    today = now.date()
    scheduled_today = now.replace(
        hour=DAILY_MESSAGE_HOUR,
        minute=DAILY_MESSAGE_MINUTE,
        second=0,
        microsecond=0,
    )

    if today < DAILY_MESSAGE_START or today > DAILY_MESSAGE_END:
        return

    last_posted = _load_last_post_date()

    # If one or more scheduled days were missed, recover the most recent
    # missed day. This handles a Render restart before today's 10 AM run
    # without losing yesterday's message.
    if last_posted is None:
        target_day = today - timedelta(days=1) if today > DAILY_MESSAGE_START else today
    elif last_posted < today - timedelta(days=1):
        target_day = today - timedelta(days=1)
    elif last_posted == today:
        return
    else:
        target_day = today - timedelta(days=1)

    if target_day < DAILY_MESSAGE_START:
        target_day = today

    if target_day == today and now < scheduled_today:
        logger.info("Daily message recovery waiting for today's 10:00 AM Arizona schedule.")
        return

    logger.warning(
        "Daily message recovery running | missed_date=%s | now=%s | scheduled_today=%s",
        target_day,
        now.isoformat(),
        scheduled_today.isoformat(),
    )
    await send_daily_community_message_reliable(context, target_day)


def start_daily_community_messages_reliable(application):
    job_queue = getattr(application, "job_queue", None)
    if not job_queue:
        logger.warning("Reliable daily community messages unavailable: JobQueue not installed.")
        return

    for name in (DAILY_MESSAGE_JOB_NAME, DAILY_MESSAGE_RECOVERY_JOB_NAME):
        for job in job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    job_queue.run_daily(
        send_daily_community_message_reliable,
        time(hour=DAILY_MESSAGE_HOUR, minute=DAILY_MESSAGE_MINUTE, tzinfo=ARIZONA_TZ),
        name=DAILY_MESSAGE_JOB_NAME,
    )

    job_queue.run_once(
        _startup_recovery,
        when=8,
        name=DAILY_MESSAGE_RECOVERY_JOB_NAME,
    )

    logger.info(
        "Reliable daily community messages scheduled | %02d:%02d Arizona | through %s | topic=%s | recovery=8s",
        DAILY_MESSAGE_HOUR,
        DAILY_MESSAGE_MINUTE,
        DAILY_MESSAGE_END.isoformat(),
        QOTD_TOPIC_ID,
    )
