# ==========================================================
# Melanated AZ Bot
# birthday_scheduler.py
#
# Persistent Birthday Announcement Scheduler
#
# Birthday announcements:
#   - Run every day at 9:00 AM
#   - Only announce birthdays matching today's MM/DD
#   - Multiple birthdays are combined into ONE message
#   - Announcement remains for 24 hours
#   - Automatically deleted after 24 hours
#
# Uses the existing raffle_database.py database.
#
# IMPORTANT:
# This file does NOT modify or reset the database.
#
# ==========================================================

import logging
from datetime import datetime, time

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


# ==========================================================
# BIRTHDAY MESSAGE
# ==========================================================

def birthday_message(
    birthdays,
):

    if not birthdays:
        return None

    lines = [
        "🎉🎂 HAPPY BIRTHDAY! 🎂🎉",
        "",
    ]

    if len(birthdays) == 1:

        birthday = birthdays[0]

        name = (
            birthday.get("display_name")
            or birthday.get("username")
            or "Melanated AZ member"
        )

        lines.extend(
            [
                f"Help us wish {name} a very Happy Birthday! 🥳",
                "",
                "👑 From everyone at Melanated AZ — "
                "we hope your day is filled with good vibes, "
                "good people, love, laughter, and plenty of fun! 💜",
                "",
                "🎁 HAPPY BIRTHDAY! 🎉",
                "",
                "💜 Enjoy YOUR day!",
            ]
        )

        return "\n".join(lines)

    # ------------------------------------------------------
    # Multiple birthdays
    # ------------------------------------------------------

    lines.extend(
        [
            "Help us wish our birthday members a "
            "VERY HAPPY BIRTHDAY! 🥳💜",
            "",
        ]
    )

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
            "👑 From everyone at Melanated AZ — "
            "we hope your day is filled with good vibes, "
            "good people, love, laughter, and plenty of fun! 💜",
            "",
            "🎁 HAPPY BIRTHDAY TO ALL OF YOU! 🎉",
            "",
            "💜 Enjoy YOUR day!",
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

    today = datetime.now()

    month_day = today.strftime(
        "%m/%d"
    )

    logger.info(
        "🎂 Birthday scheduler checking %s",
        month_day,
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
    # Determine chat
    #
    # The configured Melanated AZ raffle chat is preferred.
    # This prevents the same birthday from being posted into
    # multiple chats when users have records in different
    # chats.
    # ------------------------------------------------------

    chat_id = RAFFLE_CHAT_ID

    if not chat_id:

        # Fall back to the first birthday's original chat.
        chat_id = birthdays[0].get(
            "chat_id"
        )

    if not chat_id:

        logger.warning(
            "No chat ID available for birthday announcements."
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
            "for %s birthday(s) in chat %s | "
            "message=%s",
            len(birthdays),
            chat_id,
            sent_message.message_id,
        )

        # --------------------------------------------------
        # DELETE AFTER 24 HOURS
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
    # Run every day at 9:00 AM.
    # ------------------------------------------------------

    application.job_queue.run_daily(
        birthday_scheduler,
        time=time(
            hour=9,
            minute=0,
        ),
        name=BIRTHDAY_JOB_NAME,
    )

    logger.info(
        "🎂 Birthday scheduler started — "
        "daily at 9:00 AM."
    )


# ==========================================================
# END birthday_scheduler.py
# ==========================================================
