# ==========================================================
# Melanated AZ Bot
# birthday.py
# ==========================================================

import logging
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from raffle_database import (
    save_birthday,
    get_birthday,
    remove_birthday,
)

logger = logging.getLogger(__name__)


# ==========================================================
# BIRTHDAY KEYBOARD
# ==========================================================

def birthday_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎂 Enter / Update My Birthday",
                    callback_data="birthday_enter",
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 View My Birthday",
                    callback_data="birthday_view",
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Remove My Birthday",
                    callback_data="birthday_remove",
                )
            ],
        ]
    )


# ==========================================================
# VALIDATE BIRTHDAY
# ==========================================================

def validate_birthday(value):

    if not value:
        return None

    value = value.strip()

    try:

        parsed = datetime.strptime(
            value,
            "%m/%d",
        )

        return parsed.strftime(
            "%m/%d"
        )

    except ValueError:

        return None


# ==========================================================
# BIRTHDAY COMMAND
#
# /birthday
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

    if context.args:

        birthday_value = context.args[0]

        await save_birthday_from_value(
            update,
            context,
            birthday_value,
        )

        return

    await message.reply_text(
        "🎂 **MELANATED AZ BIRTHDAY** 🎂\n\n"
        "We love celebrating our members! 💜\n\n"
        "Enter your birthday and Melanated AZ "
        "will recognize your special day.\n\n"
        "Choose an option below:",
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# SAVE BIRTHDAY
# ==========================================================

async def save_birthday_from_value(
    update,
    context,
    birthday_value,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return False

    birthday_value = validate_birthday(
        birthday_value
    )

    if not birthday_value:

        await message.reply_text(
            "❌ **Invalid birthday.**\n\n"
            "Please use:\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return False

    # ======================================================
    # SAVE TO DATABASE
    # ======================================================

    saved = save_birthday(
        user_id=user.id,
        chat_id=message.chat_id,
        birthday=birthday_value,
        username=user.username,
        display_name=user.full_name,
    )

    if not saved:

        await message.reply_text(
            "⚠️ I could not save your birthday.\n\n"
            "Please try again."
        )

        return False

    # ======================================================
    # CLEAR WAITING STATE
    # ======================================================

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    # ======================================================
    # CONFIRM
    # ======================================================

    await message.reply_text(
        "🎂 **Birthday Saved!** 🎂\n\n"
        f"📅 Your birthday: **{birthday_value}**\n\n"
        "🎉 Melanated AZ will recognize your "
        "birthday and give you a shout-out! 💜\n\n"
        "Your birthday has been permanently "
        "saved in the database.",
        parse_mode="Markdown",
    )

    logger.info(
        "Birthday saved: user=%s chat=%s birthday=%s",
        user.id,
        message.chat_id,
        birthday_value,
    )

    return True


# ==========================================================
# BIRTHDAY BUTTON CALLBACK
# ==========================================================

async def birthday_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = query.from_user

    if not user:
        await query.answer()
        return

    data = query.data or ""

    await query.answer()

    # ======================================================
    # ENTER
    # ======================================================

    if data == "birthday_enter":

        context.user_data[
            "awaiting_birthday"
        ] = True

        await query.message.reply_text(
            "🎂 **Let's add your birthday!**\n\n"
            "Send your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # VIEW
    # ======================================================

    if data == "birthday_view":

        record = get_birthday(
            user_id=user.id,
            chat_id=query.message.chat_id,
        )

        if not record:

            await query.message.reply_text(
                "🎂 **No Birthday Saved**\n\n"
                "You don't have a birthday saved yet.",
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

            return

        await query.message.reply_text(
            "🎂 **Your Birthday**\n\n"
            f"📅 **{record['birthday']}**\n\n"
            "Your birthday is saved in the "
            "Melanated AZ database. 💜",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # REMOVE
    # ======================================================

    if data == "birthday_remove":

        removed = remove_birthday(
            user_id=user.id,
            chat_id=query.message.chat_id,
        )

        if removed:

            await query.message.reply_text(
                "🗑️ **Birthday Removed**\n\n"
                "Your birthday has been removed "
                "from the Melanated AZ database.",
                parse_mode="Markdown",
            )

        else:

            await query.message.reply_text(
                "ℹ️ You don't currently have "
                "a birthday saved."
            )

        return


# ==========================================================
# TEXT BIRTHDAY INPUT
# ==========================================================

async def birthday_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not context.user_data.get(
        "awaiting_birthday"
    ):

        return False

    message = update.effective_message

    if not message or not message.text:

        return False

    birthday_value = message.text.strip()

    await save_birthday_from_value(
        update,
        context,
        birthday_value,
    )

    return True


# ==========================================================
# MY BIRTHDAY
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
            "🎂 **No Birthday Saved**\n\n"
            "You don't have a birthday saved yet.",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

        return

    await message.reply_text(
        "🎂 **Your Birthday**\n\n"
        f"📅 **{record['birthday']}**\n\n"
        "Your birthday is saved in the "
        "Melanated AZ database. 💜",
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# REMOVE
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
            "🗑️ **Birthday Removed**\n\n"
            "Your birthday has been removed "
            "from the Melanated AZ database.",
            parse_mode="Markdown",
        )

    else:

        await message.reply_text(
            "ℹ️ You don't currently have "
            "a birthday saved."
        )
