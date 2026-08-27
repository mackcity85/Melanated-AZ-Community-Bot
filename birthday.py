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

    value = value.strip()

    # Accept:
    # 08/26
    # 8/26

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
# /BIRTHDAY
# ==========================================================

async def birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    # ------------------------------------------------------
    # /birthday 08/26
    # ------------------------------------------------------

    if context.args:

        birthday_value = (
            context.args[0].strip()
        )

        await save_birthday_from_value(
            update,
            context,
            birthday_value,
        )

        return

    # ------------------------------------------------------
    # Show menu
    # ------------------------------------------------------

    existing = get_birthday(
        user_id=user.id,
        chat_id=message.chat_id,
    )

    if existing:

        text = (
            "🎂 **Your Melanated AZ Birthday**\n\n"
            f"📅 Current birthday: "
            f"**{existing['birthday']}**\n\n"
            "You can update or remove it below."
        )

    else:

        text = (
            "🎂 **MELANATED AZ BIRTHDAY** 🎂\n\n"
            "We love celebrating our members! 💜\n\n"
            "Enter your birthday and Melanated AZ "
            "will recognize your special day. 🎉\n\n"
            "Your birthday is stored in the database "
            "so it remains saved when the bot restarts.\n\n"
            "Choose an option below:"
        )

    await message.reply_text(
        text,
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
            "Please enter your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return False

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------

    try:

        saved = save_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
            birthday=birthday_value,
            username=user.username,
            display_name=user.full_name,
        )

    except Exception:

        logger.exception(
            "Database error saving birthday "
            "for user %s",
            user.id,
        )

        await message.reply_text(
            "⚠️ I couldn't save your birthday "
            "because of a database error.\n\n"
            "Please try again."
        )

        return False

    if not saved:

        await message.reply_text(
            "⚠️ Your birthday could not be saved.\n\n"
            "Please try again."
        )

        return False

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    logger.info(
        "🎂 Birthday saved | user=%s | chat=%s | birthday=%s",
        user.id,
        message.chat_id,
        birthday_value,
    )

    await message.reply_text(
        "🎂 **BIRTHDAY SAVED!** 🎂\n\n"
        f"📅 Your birthday: **{birthday_value}**\n\n"
        "✅ Your birthday has been permanently "
        "saved in the Melanated AZ database.\n\n"
        "🎉 Melanated AZ will recognize your "
        "birthday on your special day! 💜",
        parse_mode="Markdown",
    )

    return True


# ==========================================================
# BIRTHDAY CALLBACK
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
            "Please send your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`\n\n"
            "I'll save it to the Melanated AZ "
            "database.",
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
                "You don't have a birthday saved "
                "for this chat yet.",
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

            return

        await query.message.reply_text(
            "🎂 **Your Birthday**\n\n"
            f"📅 **{record['birthday']}**\n\n"
            "✅ Your birthday is saved in the "
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

        context.user_data.pop(
            "awaiting_birthday",
            None,
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
# TEXT INPUT
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
# /MYBIRTHDAY
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
            "You don't have a birthday saved "
            "for this chat yet.\n\n"
            "Use:\n"
            "`/birthday`\n\n"
            "to add it.",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

        return

    await message.reply_text(
        "🎂 **Your Birthday**\n\n"
        f"📅 **{record['birthday']}**\n\n"
        "✅ Your birthday is saved in the "
        "Melanated AZ database. 💜",
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# /REMOVEBIRTHDAY
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

    context.user_data.pop(
        "awaiting_birthday",
        None,
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
