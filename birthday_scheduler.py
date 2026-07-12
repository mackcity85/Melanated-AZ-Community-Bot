# ==========================================================
# Melanated AZ Bot
# birthdays.py
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes

from database import save_birthday


# ==========================================================
# SAVE BIRTHDAY
# ==========================================================

async def birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat


    if not context.args:

        await update.message.reply_text(
            """
🎂 Birthday Setup

Use:

/birthday MM-DD

Example:

/birthday 07-25

Your birthday will be saved for community shoutouts.
"""
        )

        return



    birthday_date = context.args[0]


    # Basic format check

    if len(birthday_date) != 5 or birthday_date[2] != "-":

        await update.message.reply_text(
            "❌ Please use this format:\n\n/birthday MM-DD"
        )

        return



    save_birthday(

        user.id,

        chat.id,

        birthday_date,

        user.username,

        user.first_name

    )



    await update.message.reply_text(
        f"""
🎂 Birthday saved!

{user.first_name}, your birthday has been added.

You will receive a birthday shoutout from Melanated AZ 👑
"""
    )



# ==========================================================
# REMOVE BIRTHDAY
# ==========================================================

async def remove_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
🎂 Birthday removal

Contact an admin if you would like your birthday removed.
"""
    )



# ==========================================================
# BIRTHDAY HELP
# ==========================================================

async def birthday_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
🎂 Birthday Commands

/birthday MM-DD
Save your birthday

Example:
/birthday 12-31

Your birthday will be announced to the group.
"""
    )
