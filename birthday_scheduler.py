# ==========================================================
# Melanated AZ Bot
# birthday_scheduler.py
# ==========================================================

import asyncio
import logging
from datetime import datetime


from database import (
    get_birthdays_today
)



logger = logging.getLogger(__name__)



# ==========================================================
# BIRTHDAY CHECK LOOP
# ==========================================================

async def birthday_check(
    application
):


    logger.info(
        "Birthday scheduler started"
    )


    while True:

        try:


            today = datetime.now().strftime(
                "%m-%d"
            )



            birthdays = get_birthdays_today(
                today
            )



            for birthday in birthdays:


                try:


                    await application.bot.send_message(

                        chat_id=birthday["chat_id"],

                        text=(

                            "🎂🎉 Happy Birthday "
                            f"{birthday['first_name']}! 🎉🎂\n\n"

                            "Everyone at Melanated AZ "
                            "wishes you an amazing day!\n\n"

                            "👑 Enjoy your day and celebrate!"

                        )

                    )


                except Exception as e:


                    logger.error(
                        f"Birthday message error: {e}"
                    )



            # Wait 24 hours

            await asyncio.sleep(
                86400
            )



        except asyncio.CancelledError:


            logger.info(
                "Birthday scheduler stopped"
            )

            break



        except Exception as e:


            logger.error(
                f"Birthday scheduler error: {e}"
            )


            await asyncio.sleep(
                300
            )
