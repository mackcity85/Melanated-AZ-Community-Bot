# ==========================================================
# Melanated AZ Bot
# birthday.py
# ==========================================================

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from raffle_database import (
    save_birthday,
    get_birthday,
    remove_birthday,
)

logger = logging.getLogger(__name__)


# ==========================================================
# SAVE BIRTHDAY
#
# /birthday 08/26
# ==========================================================

async def birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not context.args:

        await message.reply_text(
            "🎂 **Birthday Setup**\n\n"
            "Use:\n"
            "`/birthday MM/DD`\n\n"
            "Example:\n"
            "`/birthday 08/26`",
            parse_mode="Markdown",
        )

        return

    birthday_value = context.args[0].strip()

    # ------------------------------------------------------
    # Validate MM/DD
    # ------------------------------------------------------

    try:

        parsed = datetime.strptime(
            birthday_value,
            "%m/%d",
        )

        birthday_value = parsed.strftime(
            "%m/%d"
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid birthday.\n\n"
            "Please use:\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return

    chat_id = message.chat_id

    save_birthday(
        user_id=user.id,
        chat_id=chat_id,
        birthday=birthday_value,
        username=user.username,
        display_name=user.full_name,
    )

    await message.reply_text(
        "🎂 **Birthday Saved!**\n\n"
        f"Your birthday is saved as **{birthday_value}**.\n\n"
        "🎉 Melanated AZ will recognize your birthday "
        "in the chat on your special day.",
        parse_mode="Markdown",
    )


# ==========================================================
# VIEW BIRTHDAY
#
# /mybirthday
# ==========================================================

async def my_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    record = get_birthday(
        user_id=user.id,
        chat_id=message.chat_id,
    )

    if not record:

        await message.reply_text(
            "🎂 You don't have a birthday saved yet.\n\n"
            "Use:\n"
            "`/birthday MM/DD`",
            parse_mode="Markdown",
        )

        return

    await message.reply_text(
        "🎂 **Your Birthday**\n\n"
        f"📅 **{record['birthday']}**\n\n"
        "Your birthday is saved in the Melanated AZ database.",
        parse_mode="Markdown",
    )


# ==========================================================
# REMOVE BIRTHDAY
#
# /removebirthday
# ==========================================================

async def remove_my_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    removed = remove_birthday(
        user_id=user.id,
        chat_id=message.chat_id,
    )

    if removed:

        await message.reply_text(
            "🗑️ Your birthday has been removed."
        )

    else:

        await message.reply_text(
            "ℹ️ You don't have a birthday saved."
        )
