import asyncio
from datetime import datetime

from database import get_birthdays_today


# ==========================================================
# DAILY BIRTHDAY CHECK
# ==========================================================

async def birthday_check(application):

    while True:

        today = datetime.now().strftime(
            "%m/%d"
        )


        birthdays = get_birthdays_today(
            today
        )


        for birthday in birthdays:

            chat_id = birthday[0]
            first_name = birthday[2]
            username = birthday[3]


            if username:

                name = f"@{username}"

            else:

                name = first_name


            try:

                await application.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🎂 Happy Birthday {name}!\n\n"
                        "The Melanated AZ family wishes "
                        "you an amazing birthday! 🎉"
                    )
                )


            except Exception as e:

                print(
                    f"Birthday notification error: {e}"
                )


        # Run once every 24 hours

        await asyncio.sleep(
            86400
        )
