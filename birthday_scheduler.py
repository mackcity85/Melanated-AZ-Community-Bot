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
from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import RAFFLE_CHAT_ID

from raffle_database import (
    get_birthdays_for_date,
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
# BUILD BIRTHDAY MESSAGE
# ==========================================================

def birthday_message(
    birthdays,
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
            "👑 From ALL of us at Melanated AZ — we are celebrating YOU! "
            "May your day be filled with BIG energy, real love, good people, "
            "laughter, unforgettable memories, and plenty of reasons to smile! 💜🔥",
            "",
            "🎊🎊 EVERYBODY DROP SOME BIRTHDAY LOVE! 🎊🎊",
            "",
            "🥳 HAPPY BIRTHDAY TO OUR BIRTHDAY STARS! 👑🎂",
            "💜 WE CELEBRATE YOU TODAY — ENJOY YOUR DAY! 🎉",
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

    message_text = birthday_message(
        birthdays
    )

    if not message_text:
        return

    try:

        sent_message = (
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
            )
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

        logger.exception(
            "Unable to send birthday announcement."
        )

    except Exception:

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

    # ------------------------------------------------------
    # Prevent duplicate scheduler jobs.
    # ------------------------------------------------------

    existing_jobs = [
        job
        for job in application.job_queue.jobs()
        if job.name == BIRTHDAY_JOB_NAME
    ]

    if existing_jobs:

        logger.info(
            "🎂 Birthday scheduler is already running."
        )

        return

    # ------------------------------------------------------
    # Run every day at exactly 9:00 AM Arizona/MST.
    # ------------------------------------------------------
    # The timezone is attached directly to the scheduled time,
    # so the job does not depend on Render's operating-system
    # timezone or UTC configuration.
    # ------------------------------------------------------

    application.job_queue.run_daily(
        birthday_scheduler,
        time=time(
            hour=9,
            minute=0,
            tzinfo=ARIZONA_TZ,
        ),
        name=BIRTHDAY_JOB_NAME,
    )

    logger.info(
        "🎂 Birthday scheduler started — "
        "daily at exactly 9:00 AM Arizona/MST "
        "(America/Phoenix, UTC-7)."
    )


# ==========================================================
# END birthday_scheduler.py
# ==========================================================
