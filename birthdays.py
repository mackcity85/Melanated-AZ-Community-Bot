# ==========================================================
# Melanated AZ Bot
# birthdays.py
# Birthday System - MM/DD
# ==========================================================

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    initialize_database,
    save_birthday,
    get_todays_birthdays
)


# ==========================================================
# DATABASE INIT
# ==========================================================

def init_birthdays():

    initialize_database()



# ==========================================================
# /birthday MM/DD
# ==========================================================

async def birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return


    if not context.args:

        await update.message.reply_text(
            "🎂 Birthday Setup\n\n"
            "Use:\n"
            "/birthday MM/DD\n\n"
            "Example:\n"
            "/birthday 08/25"
        )

        return



    birthday = context.args[0]


    try:

        datetime.strptime(
            birthday,
            "%m/%d"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid birthday format.\n\n"
            "Use MM/DD\n"
            "Example: 08/25"
        )

        return



    save_birthday(
        user.id,
        birthday
    )


    await update.message.reply_text(
        f"🎉 Birthday saved!\n"
        f"🎂 {birthday}"
    )



# ==========================================================
# /birthdaycheck
# ==========================================================

async def birthday_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    birthdays = get_todays_birthdays()


    if not birthdays:

        await update.message.reply_text(
            "🎂 No birthdays today."
        )

        return



    text = "🎉 Today's Birthdays 🎉\n\n"


    for person in birthdays:

        text += (
            f"🎂 {person['first_name']}\n"
        )


    await update.message.reply_text(
        text
    )
