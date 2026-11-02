# ==========================================================
# Melanated AZ Bot
# birthday_scheduler.py
#
# Persistent Birthday Announcement Scheduler
#
# Birthday announcements:
#   - Run every day at exactly 9:00 AM Arizona/MST
#   - Only announce birthdays matching today's MM/DD
#   - Multiple birthdays are combined into ONE message
#   - Announcement remains for 24 hours
#   - Automatically deleted after 24 hours
#
# Uses the existing raffle_database.py database.
#
# IMPORTANT:
# This file does NOT reset, recreate, or modify the database.
#
# ==========================================================

import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import RAFFLE_CHAT_ID

from raffle_database import (
    get_birthdays_for_date,
    get_connection,
)


logger = logging.getLogger(__name__)


# ==========================================================
# CONFIGURATION
# ==========================================================

BIRTHDAY_JOB_NAME = (
    "melanated_birthday_scheduler"
)

BIRTHDAY_DELETE_JOB_PREFIX = (
    "melanated_birthday_delete"
)

BIRTHDAY_ANNOUNCEMENT_SECONDS = 86400

# Arizona uses Mountain Standard Time (MST / UTC-7) year-round.
# America/Phoenix does not switch to daylight saving time.
ARIZONA_TZ = ZoneInfo("America/Phoenix")



# ==========================================================
# SAME-DAY RECOVERY / DUPLICATE PROTECTION
# ==========================================================

BIRTHDAY_ANNOUNCEMENT_TABLE = "birthday_announcement_log"
BIRTHDAY_RECOVERY_JOB_NAME = "melanated_birthday_recovery"
BIRTHDAY_RECOVERY_INTERVAL_JOB_NAME = "melanated_birthday_recovery_interval"
BIRTHDAY_RECOVERY_INTERVAL_SECONDS = 300


def _claim_announcement(chat_id, now_arizona):
    """Claim today's announcement; prevent repeats across restarts."""
    day_key = now_arizona.strftime("%Y-%m-%d")
    now_text = now_arizona.isoformat()
    stale_before = (now_arizona - timedelta(minutes=15)).isoformat()
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS birthday_announcement_log (
                announcement_date TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_id INTEGER,
                PRIMARY KEY (announcement_date, chat_id)
            )
        """)
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("""
            SELECT status, updated_at
            FROM birthday_announcement_log
            WHERE announcement_date=? AND chat_id=?
        """, (day_key, int(chat_id))).fetchone()

        if row and row["status"] == "sent":
            conn.commit()
            return False

        if (row and row["status"] == "sending"
                and row["updated_at"] >= stale_before):
            conn.commit()
            return False

        conn.execute("""
            INSERT INTO birthday_announcement_log
                (announcement_date, chat_id, status, updated_at, message_id)
            VALUES (?, ?, 'sending', ?, NULL)
            ON CONFLICT(announcement_date, chat_id) DO UPDATE SET
                status='sending', updated_at=excluded.updated_at,
                message_id=NULL
        """, (day_key, int(chat_id), now_text))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        logger.exception("Could not claim birthday announcement recovery.")
        # Fail closed: avoid duplicate posts if the idempotency log is unavailable.
        return False
    finally:
        conn.close()


def _finish_announcement(chat_id, now_arizona, status, message_id=None):
    day_key = now_arizona.strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE birthday_announcement_log
            SET status=?, updated_at=?, message_id=?
            WHERE announcement_date=? AND chat_id=?
        """, (
            status, datetime.now(ARIZONA_TZ).isoformat(), message_id,
            day_key, int(chat_id),
        ))
        conn.commit()
    except Exception:
        logger.exception("Could not update birthday announcement recovery log.")
    finally:
        conn.close()


async def birthday_scheduler_recovery(context: ContextTypes.DEFAULT_TYPE):
    """Catch up today's birthday post after 9 AM if startup missed it."""
    now_arizona = datetime.now(ARIZONA_TZ)
    if (now_arizona.hour, now_arizona.minute) < (9, 0):
        logger.info(
            "Birthday recovery skipped before 9:00 AM Arizona time."
        )
        return

    logger.info(
        "Birthday same-day recovery check started | Arizona time=%s",
        now_arizona.strftime("%Y-%m-%d %H:%M:%S %Z"),
    )
    await birthday_scheduler(context)


# ==========================================================
# BUILD BIRTHDAY MESSAGE
# ==========================================================

def birthday_message(
    birthdays,
    belated=False,
):

    if not birthdays:
        return None

    # ------------------------------------------------------
    # ONE BIRTHDAY
    # ------------------------------------------------------

    if len(birthdays) == 1:

        birthday = birthdays[0]

        name = (
            birthday.get("display_name")
            or birthday.get("username")
            or "Melanated AZ member"
        )

        if belated:
            return (
                "🎉🎂💜 A BELATED BIRTHDAY SHOUTOUT! 💜🎂🎉\n\n"
                f"🚨 MELANATED AZ, LET'S SHOW {name.upper()} SOME LOVE! 🚨\n\n"
                "We may have missed the day, but we haven't forgotten you! "
                "We hope your birthday was filled with love, laughter, and "
                "everything that makes you smile. 💜\n\n"
                f"🥳 HAPPY BELATED BIRTHDAY, {name}! 🎂👑\n"
                "The celebration doesn't stop just because the day has passed! 🎉"
            )

        return (
            "🎉🎂🥳 IT'S YOUR BIRTHDAY! 🥳🎂🎉\n\n"
            f"🚨🎉 MELANATED AZ, LET'S CELEBRATE {name.upper()}! 🎉🚨\n\n"
            "Today is ALL about you! 💜\n"
            "So everybody show some love, drop those birthday vibes, "
            "and help us make sure they feel celebrated! 🥳🎈🙌🏾\n\n"
            "👑 From all of us at Melanated AZ — we are wishing you "
            "a birthday filled with BIG smiles, real love, good people, "
            "great energy, unforgettable moments, and everything that "
            "makes YOU happy! 💜🔥🎁\n\n"
            "🎊🎊 LET'S TURN UP FOR THE BIRTHDAY STAR! 🎊🎊\n\n"
            "🥂 Here's to another year, another chapter, and plenty more "
            "memories to make! 🎉\n\n"
            f"💜 HAPPY BIRTHDAY, {name}! 👑🎂\n"
            "🎉 WE CELEBRATE YOU TODAY! 🎉"
        )

    # ------------------------------------------------------
    # MULTIPLE BIRTHDAYS
    # ------------------------------------------------------

    if belated:
        lines = [
            "🎉🎂💜 A BELATED BIRTHDAY CELEBRATION! 💜🎂🎉",
            "",
            "MELANATED AZ, WE MAY BE A LITTLE LATE, BUT WE'RE NOT",
            "LETTING THESE BIRTHDAYS GO UNCELEBRATED! 🎉",
            "",
            "Let's show our birthday stars some love! 💜🙌🏾",
            "",
        ]
    else:
        lines = [
            "🎉🎂🥳 IT'S A BIRTHDAY CELEBRATION! 🥳🎂🎉",
            "",
            "🚨🎉 MELANATED AZ, LET'S SHOW OUR BIRTHDAY STARS",
            "SOME SERIOUS LOVE TODAY! 🎉🚨",
            "",
            "These are YOUR birthday stars — so let's celebrate THEM! 💜🙌🏾",
            "",
        ]

    for birthday in birthdays:

        name = (
            birthday.get("display_name")
            or birthday.get("username")
            or "Melanated AZ member"
        )

        lines.append(
            f"🎂 {name}"
        )

    lines.extend(
        [
            "",
            (
                "👑 From ALL of us at Melanated AZ — we are celebrating YOU! "
                "We hope your birthday was filled with BIG energy, real love, "
                "good people, laughter, and unforgettable memories! 💜🔥"
                if belated else
                "👑 From ALL of us at Melanated AZ — we are celebrating YOU! "
                "May your day be filled with BIG energy, real love, good people, "
                "laughter, unforgettable memories, and plenty of reasons to smile! 💜🔥"
            ),
            "",
            "🎊🎊 EVERYBODY DROP SOME BIRTHDAY LOVE! 🎊🎊",
            "",
            (
                "🥳 HAPPY BELATED BIRTHDAY TO OUR BIRTHDAY STARS! 👑🎂"
                if belated else
                "🥳 HAPPY BIRTHDAY TO OUR BIRTHDAY STARS! 👑🎂"
            ),
            (
                "💜 WE'RE STILL CELEBRATING YOU — ENJOYED YOUR DAY! 🎉"
                if belated else
                "💜 WE CELEBRATE YOU TODAY — ENJOY YOUR DAY! 🎉"
            ),
        ]
    )

    return "\n".join(lines)


# ==========================================================
# DELETE BIRTHDAY ANNOUNCEMENT
# ==========================================================

async def delete_birthday_message(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    chat_id = data.get(
        "chat_id"
    )

    message_id = data.get(
        "message_id"
    )

    if chat_id is None or message_id is None:
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "🎂 Birthday announcement removed "
            "after 24 hours | chat=%s | message=%s",
            chat_id,
            message_id,
        )

    except TelegramError as exc:

        logger.info(
            "Birthday announcement already removed "
            "or could not be deleted | "
            "chat=%s | message=%s | error=%s",
            chat_id,
            message_id,
            exc,
        )

    except Exception:

        logger.exception(
            "Unexpected error deleting birthday announcement."
        )


# ==========================================================
# SEND BIRTHDAY ANNOUNCEMENT
# ==========================================================

async def birthday_scheduler(
    context: ContextTypes.DEFAULT_TYPE,
):

    # Always calculate today's birthday date in Arizona time.
    # This prevents Render's UTC date from being used.
    now_arizona = datetime.now(ARIZONA_TZ)

    month_day = now_arizona.strftime(
        "%m/%d"
    )

    logger.info(
        "🎂 Birthday scheduler checking %s "
        "(Arizona time: %s)",
        month_day,
        now_arizona.strftime("%Y-%m-%d %H:%M:%S %Z"),
    )

    birthdays = get_birthdays_for_date(
        month_day
    )

    if not birthdays:

        logger.info(
            "No birthdays found for %s",
            month_day,
        )

        return

    logger.info(
        "Found %s birthday(s) for %s",
        len(birthdays),
        month_day,
    )

    # ------------------------------------------------------
    # Use the configured Melanated AZ chat.
    # ------------------------------------------------------

    chat_id = RAFFLE_CHAT_ID

    # ------------------------------------------------------
    # Fallback to the birthday record's chat.
    # ------------------------------------------------------

    if not chat_id:

        chat_id = birthdays[0].get(
            "chat_id"
        )

    if not chat_id:

        logger.warning(
            "No chat ID available for birthday announcement."
        )

        return

    # After 8:00 PM Arizona time, use a belated birthday message.
    # This applies to both the regular run and startup catch-up.
    is_belated = (now_arizona.hour, now_arizona.minute) >= (20, 0)

    message_text = birthday_message(
        birthdays,
        belated=is_belated,
    )

    if is_belated:
        logger.info(
            "Using belated birthday announcement | Arizona time=%s",
            now_arizona.strftime("%Y-%m-%d %H:%M:%S %Z"),
        )

    if not message_text:
        return

    if not _claim_announcement(chat_id, now_arizona):
        logger.info(
            "Birthday announcement already sent or another run is handling it "
            "| date=%s | chat=%s",
            month_day, chat_id,
        )
        return

    try:

        sent_message = (
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
            )
        )

        _finish_announcement(
            chat_id, now_arizona, "sent", sent_message.message_id
        )

        logger.info(
            "🎂 Birthday announcement sent "
            "for %s birthday(s) | "
            "chat=%s | message=%s",
            len(birthdays),
            chat_id,
            sent_message.message_id,
        )

        # --------------------------------------------------
        # Schedule deletion after 24 hours.
        # --------------------------------------------------

        if context.job_queue:

            context.job_queue.run_once(
                delete_birthday_message,
                when=BIRTHDAY_ANNOUNCEMENT_SECONDS,
                data={
                    "chat_id": chat_id,
                    "message_id": (
                        sent_message.message_id
                    ),
                },
                name=(
                    f"{BIRTHDAY_DELETE_JOB_PREFIX}_"
                    f"{chat_id}_"
                    f"{sent_message.message_id}"
                ),
            )

            logger.info(
                "Scheduled birthday announcement "
                "deletion in 24 hours | "
                "chat=%s | message=%s",
                chat_id,
                sent_message.message_id,
            )

        else:

            logger.warning(
                "JobQueue unavailable. "
                "Birthday announcement will NOT "
                "be automatically deleted."
            )

    except TelegramError:
        _finish_announcement(chat_id, now_arizona, "failed")
        logger.exception(
            "Unable to send birthday announcement."
        )

    except Exception:
        _finish_announcement(chat_id, now_arizona, "failed")
        logger.exception(
            "Unexpected birthday scheduler error."
        )


# ==========================================================
# START BIRTHDAY SCHEDULER
# ==========================================================

def start_birthday_scheduler(
    application,
):

    if not application.job_queue:

        logger.error(
            "JobQueue is not available. "
            "Install python-telegram-bot[job-queue]."
        )

        return

    # Register the daily job and startup recovery independently.
    # A partially registered scheduler must not prevent the missing job
    # from being repaired on the next startup.
    daily_jobs = application.job_queue.get_jobs_by_name(BIRTHDAY_JOB_NAME)
    if not daily_jobs:
        application.job_queue.run_daily(
            birthday_scheduler,
            time=time(hour=9, minute=0, tzinfo=ARIZONA_TZ),
            name=BIRTHDAY_JOB_NAME,
        )
        logger.info(
            "Birthday scheduler REGISTERED | daily=09:00 | timezone=America/Phoenix"
        )
    else:
        logger.info(
            "Birthday scheduler already registered | daily_jobs=%s",
            len(daily_jobs),
        )

    # Catch up today's shout-out after startup when 9:00 AM Arizona time
    # has passed. The persistent announcement log prevents duplicate posts.
    recovery_jobs = application.job_queue.get_jobs_by_name(
        BIRTHDAY_RECOVERY_JOB_NAME
    )
    if not recovery_jobs:
        application.job_queue.run_once(
            birthday_scheduler_recovery,
            when=5,
            name=BIRTHDAY_RECOVERY_JOB_NAME,
        )
        logger.info(
            "Same-day birthday recovery REGISTERED | startup_delay=5s"
        )
    else:
        logger.info(
            "Same-day birthday recovery already registered | jobs=%s",
            len(recovery_jobs),
        )

    # Keep checking today's birthday periodically after startup. This is a
    # safety net if the one-time startup callback fires before the bot is
    # fully ready, or a transient Telegram/database error prevents delivery.
    # The persistent announcement log prevents duplicate posts.
    interval_jobs = application.job_queue.get_jobs_by_name(
        BIRTHDAY_RECOVERY_INTERVAL_JOB_NAME
    )
    if not interval_jobs:
        application.job_queue.run_repeating(
            birthday_scheduler_recovery,
            interval=BIRTHDAY_RECOVERY_INTERVAL_SECONDS,
            first=15,
            name=BIRTHDAY_RECOVERY_INTERVAL_JOB_NAME,
        )
        logger.info(
            "Birthday recovery watchdog REGISTERED | first=15s | interval=%ss | timezone=America/Phoenix",
            BIRTHDAY_RECOVERY_INTERVAL_SECONDS,
        )
    else:
        logger.info(
            "Birthday recovery watchdog already registered | jobs=%s",
            len(interval_jobs),
        )

    logger.info(
        "Birthday scheduler registration verified | daily=%s | recovery=%s | watchdog=%s",
        len(application.job_queue.get_jobs_by_name(BIRTHDAY_JOB_NAME)),
        len(application.job_queue.get_jobs_by_name(BIRTHDAY_RECOVERY_JOB_NAME)),
        len(application.job_queue.get_jobs_by_name(BIRTHDAY_RECOVERY_INTERVAL_JOB_NAME)),
    )


# ==========================================================
# END birthday_scheduler.py
# ==========================================================
