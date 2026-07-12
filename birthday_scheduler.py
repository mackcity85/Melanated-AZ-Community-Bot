import asyncio
import logging
from datetime import datetime

from database import get_birthdays_today


logging.basicConfig(level=logging.INFO)


async def birthday_check(application):

    logging.info("Birthday scheduler started")

    try:

        while True:

            today = datetime.now().strftime("%m/%d")


            birthdays = get_birthdays_today(
                today
            )


            for chat_id, user_id, name in birthdays:

                try:

                    await application.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"🎂 Happy Birthday {name}! 🎉\n\n"
                            "Wishing you an amazing day from everyone at Melanated AZ!"
                        )
                    )

                except Exception as e:

                    logging.error(
                        f"Birthday message error: {e}"
                    )


            await asyncio.sleep(
                86400
            )


    except asyncio.CancelledError:

        logging.info(
            "Birthday scheduler stopped cleanly"
        )

        raise
