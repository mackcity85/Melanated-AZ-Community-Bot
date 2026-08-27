# ==========================================================
# Melanated AZ Bot
# birthday_scheduler.py
# ==========================================================

import logging
from datetime import datetime, time

from telegram.ext import ContextTypes

from config import RAFFLE_CHAT_ID

from raffle_database import (
    get_birthdays_for_date,
)

logger = logging.getLogger(__name__)


# ==========================================================
# BIRTHDAY MESSAGE
# ==========================================================

def birthday_message(birthday):

    name = (
        birthday.get("display_name")
        or birthday.get("username")
        or "Melanated AZ member"
    )

    if birthday.get("username") and not birthday.get("display_name"):
        name = f"@{birthday['username']}"

    return (
        "🎉🎂 **HAPPY BIRTHDAY!** 🎂🎉\n\n"
        f"Help us wish **{name}** a very Happy Birthday! 🥳\n\n"
        "👑 From everyone at **Melanated AZ** — "
        "we hope your day is filled with good vibes, "
        "good people, love, laughter, and plenty of fun! 💜\n\n"
        "🎁 **HAPPY BIRTHDAY!** 🎉"
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

        # --------------------------------------------------
        # Use the chat where the birthday was registered.
        # Fall back to RAFFLE_CHAT_ID if necessary.
        # --------------------------------------------------

        chat_id = birthday.get("chat_id")

        if not chat_id:
            chat_id = RAFFLE_CHAT_ID

        if not chat_id:

            logger.warning(
                "No chat ID available for birthday user %s",
                birthday.get("user_id"),
            )

            continue

        try:

            await context.bot.send_message(
                chat_id=chat_id,
                text=birthday_message(
                    birthday
                ),
                parse_mode="Markdown",
            )

            logger.info(
                "🎂 Birthday message sent for user %s "
                "in chat %s",
                birthday.get("user_id"),
                chat_id,
            )

        except Exception:

            logger.exception(
                "Unable to send birthday message "
                "for user %s in chat %s",
                birthday.get("user_id"),
                chat_id,
            )


# ==========================================================
# START BIRTHDAY SCHEDULER
# ==========================================================

def start_birthday_scheduler(
    application,
):

    # ------------------------------------------------------
    # Make sure JobQueue is available.
    # ------------------------------------------------------

    if not application.job_queue:

        logger.error(
            "❌ JobQueue is not available.\n"
            "Install python-telegram-bot[job-queue]."
        )

        return

    # ------------------------------------------------------
    # Check for an existing birthday scheduler.
    #
    # IMPORTANT:
    # python-telegram-bot uses:
    #
    # get_jobs_by_name()
    #
    # NOT:
    #
    # jobs(name=...)
    # ------------------------------------------------------

    try:

        existing_jobs = (
            application.job_queue
            .get_jobs_by_name(
                "melanated_birthday_scheduler"
            )
        )

    except Exception:

        logger.exception(
            "Unable to check for existing birthday scheduler."
        )

        existing_jobs = ()

    if existing_jobs:

        logger.info(
            "🎂 Birthday scheduler is already running."
        )

        return

    # ------------------------------------------------------
    # Schedule birthday check every day at 9:00 AM.
    #
    # The scheduler itself is recreated whenever the bot
    # restarts.
    #
    # Birthday records remain permanently stored in the
    # SQLite database.
    # ------------------------------------------------------

    application.job_queue.run_daily(
        birthday_scheduler,
        time=time(
            hour=9,
            minute=0,
        ),
        name="melanated_birthday_scheduler",
    )

    logger.info(
        "🎂 Birthday scheduler started — "
        "daily at 9:00 AM."
    )
