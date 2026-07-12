# ==========================================================
# Melanated AZ Bot
# Birthday Commands
# ==========================================================

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    save_birthday,
    get_birthdays_today
)


# ==========================================================
# SAVE BIRTHDAY
# ==========================================================

async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "🎂 Birthday Setup\n\n"
            "Use:\n"
            "/birthday MM/DD\n\n"
            "Example:\n"
            "/birthday 08/15"
        )
        return


    birthday_date = context.args[0]


    try:
        datetime.strptime(
            birthday_date,
            "%m/%d"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Please use:\n"
            "/birthday MM/DD"
        )

        return


    user = update.effective_user


    save_birthday(
        user.id,
        user.first_name,
        user.username,
        birthday_date
    )


    await update.message.reply_text(
        "🎂 Birthday saved!\n\n"
        f"Thanks {user.first_name}."
    )



# ==========================================================
# CHECK TODAY'S BIRTHDAYS
# ==========================================================

async def birthday_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    today = datetime.now().strftime("%m/%d")


    birthdays = get_birthdays_today(
        today
    )


    if not birthdays:

        await update.message.reply_text(
            "🎂 No birthdays today."
        )

        return



    message = (
        "🎉 Today's Birthdays 🎉\n\n"
    )


    for person in birthdays:

        message += (
            f"🎂 {person['first_name']}\n"
        )


    await update.message.reply_text(
        message
    )
