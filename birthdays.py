# ==========================================================
# Melanated AZ Bot
# birthdays.py
# Birthday Commands
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    save_birthday
)



# ==========================================================
# /setbirthday
# ==========================================================

async def set_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):


    user = update.effective_user


    if not context.args:

        await update.message.reply_text(

            "Usage:\n"
            "/setbirthday MM-DD-YYYY\n\n"
            "Example:\n"
            "/setbirthday 07-25-1985"

        )

        return



    birthday = context.args[0]



    # Basic format check

    try:

        month, day, year = birthday.split("-")


        if len(month) != 2 or len(day) != 2:

            raise ValueError



    except:

        await update.message.reply_text(

            "❌ Invalid format.\n\n"
            "Use:\n"
            "/setbirthday MM-DD-YYYY"

        )

        return



    save_birthday(

        user.id,
        birthday

    )



    await update.message.reply_text(

f"""
🎂 Birthday saved!

{user.first_name}, your birthday has been added.

We will celebrate with the community when your day arrives! 🎉
"""

    )
