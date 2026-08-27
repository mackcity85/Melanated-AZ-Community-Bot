# ==========================================================
# Melanated AZ Bot
# birthday_scheduler.py
# ==========================================================

import asyncio
import logging
from datetime import datetime

from birthdays import get_todays_birthdays

logger = logging.getLogger(__name__)


# ==========================================================
# BIRTHDAY MESSAGE
# ==========================================================

def birthday_message(birthday):

    name = (
        birthday.get("first_name")
        or birthday.get("name")
        or birthday.get("display_name")
        or "our member"
    )

    return (
        "🎂🎉 HAPPY BIRTHDAY 🎉🎂\n\n"
        f"👑 {name}\n\n"
        "Everyone at Melanated AZ wishes you "
        "an amazing birthday!\n\n"
        "🔥 We hope your day is filled with "
        "good vibes, good people, and plenty "
        "of reasons to smile.\n\n"
        "👑 Enjoy your day and celebrate! 🎉"
    )


# ==========================================================
# DAILY BIRTHDAY CHECK
# ==========================================================

async def birthday_check(application):

    logger.info(
        "🎂 Birthday scheduler started."
    )

    last_checked_date = None

    while True:

        try:

            now = datetime.now()
            today = now.strftime("%m-%d")

            # ------------------------------------------------
            # Only run once per calendar day
            # ------------------------------------------------

            if last_checked_date != today:

                logger.info(
                    "🎂 Checking birthdays for %s",
                    today,
                )

                birthdays = get_todays_birthdays()

                if birthdays:

                    logger.info(
                        "Found %s birthday(s) for today.",
                        len(birthdays),
                    )

                    for birthday in birthdays:

                        chat_id = birthday.get(
                            "chat_id"
                        )

                        if not chat_id:

                            logger.warning(
                                "Birthday record has no chat_id: %s",
                                birthday,
                            )

                            continue

                        try:

                            await application.bot.send_message(
                                chat_id=chat_id,
                                text=birthday_message(
                                    birthday
                                ),
                            )

                            logger.info(
                                "Birthday message sent for %s",
                                birthday.get(
                                    "first_name"
                                )
                                or birthday.get(
                                    "name"
                                ),
                            )

                        except Exception:

                            logger.exception(
                                "Unable to send birthday "
                                "message for %s",
                                birthday,
                            )

                else:

                    logger.info(
                        "No birthdays found for today."
                    )

                last_checked_date = today

            # ------------------------------------------------
            # Check every minute
            #
            # This lets the scheduler notice a new day
            # without needing a long sleep.
            # ------------------------------------------------

            await asyncio.sleep(60)

        except asyncio.CancelledError:

            logger.info(
                "🎂 Birthday scheduler stopped."
            )

            raise

        except Exception:

            logger.exception(
                "Birthday scheduler error."
            )

            await asyncio.sleep(60)
