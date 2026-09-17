"""Melanated AZ weekday Grand Rising greetings.

Runs at 6:00 AM America/Phoenix from 2026-09-16 through 2036-12-31.
Each weekday has its own urban, playful, kinky/open-minded theme while keeping
"Grand Rising, Melanated Kings & Queens" as the recurring community opener.
"""

import json
import logging
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

logger = logging.getLogger("melanatedaz.grand_rising")

CHAT_ID = -1002697105809
TOPIC_ID = 1
ARIZONA_TZ = ZoneInfo("America/Phoenix")
START_DATE = date(2026, 9, 16)
END_DATE = date(2036, 12, 31)
GREETING_TIME = time(hour=6, minute=0, tzinfo=ARIZONA_TZ)
JOB_NAME = "melanated-grand-rising"
RECOVERY_JOB_NAME = "melanated-grand-rising-recovery"
STATE_FILE = Path("/var/data/grand_rising_state.json")

WEEKDAY_GREETINGS = {
    0: (
        "👑 <b>Grand Rising, Melanated Kings &amp; Queens! 🖤</b>\n\n"
        "😈 <b>Munchie Monday</b>\n"
        "Start the week with a little appetite for something different. Sometimes you gotta feed "
        "your mind before you feed your cravings. Be curious. Be open. Explore what makes you tick.\n\n"
        "🖤 New week. New energy. New things to discover."
    ),
    1: (
        "👑 <b>Grand Rising, Melanated Kings &amp; Queens! 🖤</b>\n\n"
        "😏 <b>Talk That Kink Tuesday</b>\n"
        "Everybody ain't into the same thing—and that's what makes the conversation interesting. "
        "Vanilla, kinky, curious, freaky, or somewhere in between... don't yuck somebody else's yum.\n\n"
        "🔥 Keep an open mind, respect the boundaries, and let grown folks enjoy their flavor."
    ),
    2: (
        "👑 <b>Grand Rising, Melanated Kings &amp; Queens! 🖤</b>\n\n"
        "🔥 <b>Wicked Wednesday</b>\n"
        "That innocent look don't always tell the whole story. 👀 Everybody's got a little freak "
        "hiding somewhere. Maybe it's time to stop pretending yours doesn't exist.\n\n"
        "😈 Be curious. Be playful. Let that wild side breathe."
    ),
    3: (
        "👑 <b>Grand Rising, Melanated Kings &amp; Queens! 🖤</b>\n\n"
        "💦 <b>Thirst Trap Thursday</b>\n"
        "Sometimes it's not what you say... it's the look, the energy, the confidence, the way you "
        "carry yourself. A little attention can turn into a whole lot of temptation.\n\n"
        "👀 Keep 'em guessing. Keep 'em interested. Keep it respectful."
    ),
    4: (
        "👑 <b>Grand Rising, Melanated Kings &amp; Queens! 🖤</b>\n\n"
        "😈 <b>Freaky Friday</b>\n"
        "The weekend is here. Time to loosen up, leave the judgment at the door, and let your "
        "adventurous side out to play. You don't have to explain your flavor to everybody.\n\n"
        "🔥 Know your boundaries, know your worth, and enjoy your freak."
    ),
    5: (
        "👑 <b>Grand Rising, Melanated Kings &amp; Queens! 🖤</b>\n\n"
        "💋 <b>Satin &amp; Spankings Saturday</b>\n"
        "Soft energy or a little more edge? Sweet talk or playful trouble? Everybody's version of "
        "kinky looks a little different.\n\n"
        "🔥 The fun is in discovering what makes the chemistry hit different."
    ),
    6: (
        "👑 <b>Grand Rising, Melanated Kings &amp; Queens! 🖤</b>\n\n"
        "🖤 <b>Submission &amp; Sins Sunday</b>\n"
        "Sometimes giving up control takes more confidence than holding onto it. Sometimes being "
        "in charge is exactly what someone needs. And sometimes you're still figuring out where you fit.\n\n"
        "😈 No boxes. No judgment. Just grown folks discovering themselves."
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
        "Grand Rising posted | date=%s | weekday=%s | message=%s | time=06:00 Arizona | topic=%s",
        day.isoformat(), day.strftime("%A"), message.message_id, TOPIC_ID,
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
