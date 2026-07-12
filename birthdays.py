# ==========================================================
# Melanated AZ Bot
# birthdays.py
# Birthday System MM/DD
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    save_birthday,
    get_todays_birthdays
)

from datetime import datetime


# ==========================================================
# INITIALIZE
# ==========================================================

def init_birthdays():

    print("Birthday system loaded")



# ==========================================================
# /birthday COMMAND
# ==========================================================

async def birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not context.args:

        await update.message.reply_text(
            """
🎂 Birthday Setup

Use:

/birthday MM/DD

Example:

/birthday 07/25

Your birthday will be saved.
"""
        )

        return



    birthday = context.args[0]


    try:

        datetime.strptime(
            birthday
