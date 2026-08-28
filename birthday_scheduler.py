# ==========================================================
# Melanated AZ Bot
# birthday_scheduler.py
#
# Birthday announcements:
#   - Checked daily at 9:00 AM
#   - Posted into the saved chat
#   - Remain posted for 24 HOURS
#   - Automatically deleted after 24 HOURS
# ==========================================================

import logging
from datetime import datetime, time

from telegram.ext import ContextTypes

from config import RAFFLE_CHAT_ID

from raffle_database import get_birthdays_for_date


logger = logging.getLogger(__name__)

BIRTHDAY_JOB_NAME = "melanated_birthday_scheduler"
BIRTHDAY_DELETE_JOB_NAME = "melanated_birthday_delete"

BIRTHDAY_ANNOUNCEMENT_SECONDS = 24 * 60 * 60


# ==========================================================
# BIRTHDAY MESSAGE
# ==========================================================

def birthday_message(birthday):

    name = (
        birthday.get("display_name")
        or birthday.get("username")
        or "Melanated AZ member"
    )

    return (
        "🎉🎂 **HAPPY BIRTHDAY!** 🎂🎉\n\n"
        f"Help us wish **{name}** a very Happy Birthday! 🥳\n\n"
        "👑 From everyone at **Melanated AZ** — "
        "we hope your day is filled with good vibes, "
        "good people, love, laughter, and plenty of fun! 💜\n\n"
        "🎁 **HAPPY BIRTHDAY!** 🎉"
    )


# ==========================================================
# DELETE BIRTHDAY ANNOUNCEMENT
# ==========================================================

async def delete_birthday_announcement(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    chat_id = data.get("chat_id")
    message_id = data.get("message_id")

    if chat_id is None or message_id is None:

        logger.warning(
            "Birthday deletion job missing chat/message ID."
        )

        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "🎂 Birthday announcement deleted after 24 hours | "
            "chat=%s | message=%s",
            chat_id,
            message_id,
        )

    except Exception as exc:

        logger.info(
            "Birthday announcement already deleted/unavailable | "
            "chat=%s | message=%s | error=%s",
            chat_id,
            message_id,
            exc,
        )


# ==========================================================
# SEND BIRTHDAY MESSAGES
# ==========================================================

async def birthday_scheduler(
    context: ContextTypes.DEFAULT_TYPE,
):

    today = datetime.now()
    month_day = today.strftime("%m/%d")

    logger.info(
        "🎂 Birthday scheduler checking %s",
        month_day,
    )

    try:

        birthdays = get_birthdays_for_date(
            month_day
        )

    except Exception:

        logger.exception(
            "Unable to retrieve birthdays for %s",
            month_day,
        )

        return

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

    for birthday in birthdays:

        chat_id = birthday.get(
            "chat_id"
        )

        if not chat_id:

            chat_id = RAFFLE_CHAT_ID

        if not chat_id:

            logger.warning(
                "No chat ID available for birthday user %s",
                birthday.get("user_id"),
            )

            continue

        try:

            sent_message = await context.bot.send_message(
                chat_id=chat_id,
                text=birthday_message(birthday),
                parse_mode="Markdown",
            )

            logger.info(
                "🎂 Birthday message sent | "
                "user=%s | chat=%s | message=%s",
                birthday.get("user_id"),
                chat_id,
                sent_message.message_id,
            )

            # --------------------------------------------------
            # DELETE AFTER 24 HOURS
            # --------------------------------------------------

            if context.job_queue:

                context.job_queue.run_once(
                    delete_birthday_announcement,
                    when=BIRTHDAY_ANNOUNCEMENT_SECONDS,
                    data={
                        "chat_id": chat_id,
                        "message_id": sent_message.message_id,
                    },
                    name=BIRTHDAY_DELETE_JOB_NAME,
                )

                logger.info(
                    "Scheduled birthday announcement deletion "
                    "for 24 hours later | chat=%s | message=%s",
                    chat_id,
                    sent_message.message_id,
                )

            else:

                logger.warning(
                    "JobQueue unavailable. "
                    "Birthday announcement will not "
                    "be automatically deleted."
                )

        except Exception:

            logger.exception(
                "Unable to send birthday message for user %s",
                birthday.get("user_id"),
            )


# ==========================================================
# START BIRTHDAY SCHEDULER
# ==========================================================

def start_birthday_scheduler(application):

    if not application.job_queue:

        logger.error(
            "JobQueue is not available. "
            "Install python-telegram-bot[job-queue]."
        )

        return

    # ------------------------------------------------------
    # PREVENT DUPLICATE DAILY JOB
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
    # RUN EVERY DAY AT 9:00 AM
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
        "🎂 Birthday scheduler started — daily at 9:00 AM."
    )
