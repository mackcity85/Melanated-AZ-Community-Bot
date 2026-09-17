"""Melanated AZ weekday Grand Rising greetings.

Runs at 6:00 AM America/Phoenix from 2026-09-16 through 2036-12-31.
Each weekday has its own theme while keeping the recurring "Grand Rising"
opener and community-focused tone.
"""

import json
import logging
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

logger = logging.getLogger("melanatedaz.grand_rising")

CHAT_ID = -1002697105809
TOPIC_ID = 11999
ARIZONA_TZ = ZoneInfo("America/Phoenix")
START_DATE = date(2026, 9, 16)
END_DATE = date(2036, 12, 31)
GREETING_TIME = time(hour=6, minute=0, tzinfo=ARIZONA_TZ)
JOB_NAME = "melanated-grand-rising"
RECOVERY_JOB_NAME = "melanated-grand-rising-recovery"
STATE_FILE = Path("/var/data/grand_rising_state.json")

WEEKDAY_GREETINGS = {
    0: (
        "👑 <b>Grand Rising, Melanated AZ! 🖤</b>\n\n"
        "🌅 <b>Mindset Monday</b>\n"
        "New week, new energy, same beautiful community. Start the week with intention, "
        "protect your peace, and make room for good conversations.\n\n"
        "🖤 Check in, meet somebody new, support somebody else, and leave a little positive energy behind.\n\n"
        "What is one thing you want to make happen this week?\n\n"
        "— King 👑"
    ),
    1: (
        "👑 <b>Grand Rising, Melanated AZ! 🖤</b>\n\n"
        "😏 <b>Tease Tuesday</b>\n"
        "Bring a little playful energy into the room today. A good smile, a good conversation, "
        "and a little harmless teasing can go a long way.\n\n"
        "🔥 Talk to somebody you have not talked to before and let the vibe develop naturally.\n\n"
        "What kind of personality always gets your attention?\n\n"
        "— King 👑"
    ),
    2: (
        "👑 <b>Grand Rising, Melanated AZ! 🖤</b>\n\n"
        "🌿 <b>Wellness Wednesday</b>\n"
        "Take care of yourself today—mind, body, energy, and boundaries. We build community by "
        "showing up for ourselves and for each other.\n\n"
        "🖤 Drink some water, take a breath, check on somebody, and keep the energy respectful.\n\n"
        "What is one thing you are doing for yourself today?\n\n"
        "— King 👑"
    ),
    3: (
        "👑 <b>Grand Rising, Melanated AZ! 🖤</b>\n\n"
        "🔥 <b>Thirsty Thursday</b>\n"
        "The weekend is getting close, so bring your personality with you. Flirt, laugh, meet people, "
        "and have some fun—but keep communication clear and respect everybody's boundaries.\n\n"
        "👀 Who in this community has a vibe you would like to get to know better?\n\n"
        "— King 👑"
    ),
    4: (
        "👑 <b>Grand Rising, Melanated AZ! 🖤</b>\n\n"
        "💋 <b>Flirty Friday</b>\n"
        "Friday is for good energy, good looks, good laughs, and conversations that make you smile.\n\n"
        "🔥 Shoot your shot respectfully, compliment somebody, and remember that confidence and consent "
        "can exist in the same conversation.\n\n"
        "What is your favorite kind of Friday-night vibe?\n\n"
        "— King 👑"
    ),
    5: (
        "👑 <b>Grand Rising, Melanated AZ! 🖤</b>\n\n"
        "✨ <b>Sensual Saturday</b>\n"
        "Slow down and enjoy the day. Dress how you feel, move how you want, and spend time around "
        "people who make you feel comfortable being yourself.\n\n"
        "🖤 Make a connection, start a conversation, or simply enjoy your own energy.\n\n"
        "What would make today a perfect Saturday for you?\n\n"
        "— King 👑"
    ),
    6: (
        "👑 <b>Grand Rising, Melanated AZ! 🖤</b>\n\n"
        "❤️ <b>Self-Love Sunday</b>\n"
        "Before you pour into anybody else, pour something into yourself. Rest, reset, laugh, connect, "
        "and appreciate how far you have come.\n\n"
        "🖤 This community is about meeting people, building friendships, creating connections, and "
        "making Arizona feel a little more like home.\n\n"
        "What are you grateful for today?\n\n"
        "— King 👑"
    ),
}


def _load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return {}


def _save_state(day: date):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"last_posted_date": day.isoformat()}), encoding="utf-8")
    except OSError:
        logger.exception("Could not save Grand Rising state.")


def _today():
    return datetime.now(ARIZONA_TZ).date()


async def send_grand_rising(context: ContextTypes.DEFAULT_TYPE, target_date: date | None = None):
    day = target_date or _today()
    if day < START_DATE or day > END_DATE:
        return False
    state = _load_state()
    if state.get("last_posted_date") == day.isoformat():
        logger.info("Grand Rising already posted | date=%s", day.isoformat())
        return False
    message = await context.bot.send_message(
        chat_id=CHAT_ID,
        message_thread_id=TOPIC_ID,
        text=WEEKDAY_GREETINGS[day.weekday()],
        parse_mode="HTML",
    )
    _save_state(day)
    logger.info(
        "Grand Rising posted | date=%s | weekday=%s | message=%s | time=06:00 Arizona",
        day.isoformat(), day.strftime("%A"), message.message_id,
    )
    return True


async def _daily_job(context: ContextTypes.DEFAULT_TYPE):
    await send_grand_rising(context)


async def _startup_recovery(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(ARIZONA_TZ)
    today = now.date()
    if today < START_DATE or today > END_DATE or now.hour != 6:
        return
    await send_grand_rising(context)


def start(application):
    job_queue = application.job_queue
    if not job_queue:
        logger.error("Grand Rising scheduler NOT started: JobQueue unavailable.")
        return
    for job_name in (JOB_NAME, RECOVERY_JOB_NAME):
        for job in job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
    job_queue.run_daily(_daily_job, time=GREETING_TIME, name=JOB_NAME)
    job_queue.run_once(_startup_recovery, when=8, name=RECOVERY_JOB_NAME)
    logger.info(
        "Grand Rising scheduler enabled | schedule=06:00 Arizona | start=%s | end=%s | topic=%s",
        START_DATE.isoformat(), END_DATE.isoformat(), TOPIC_ID,
    )
