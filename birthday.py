# ==========================================================
# Melanated AZ Bot
# birthday.py
# ==========================================================

import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
# /birthday
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

        birthday_value = context.args[0].strip()

        await save_birthday_from_value(
            update,
            context,
            birthday_value,
        )

        return

    # ------------------------------------------------------
    # Normal /birthday command
    # ------------------------------------------------------

    await message.reply_text(
        "🎂 *MELANATED AZ BIRTHDAY* 🎂\n\n"
        "We love celebrating our members! 💜\n\n"
        "Enter your birthday and Melanated AZ "
        "will recognize your birthday in the chat. 🎉\n\n"
        "Your birthday is saved in the database "
        "so it remains available when the bot restarts.\n\n"
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

    birthday_value = birthday_value.strip()

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
            "❌ *Invalid birthday.*\n\n"
            "Please enter your birthday using:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return False

    # ------------------------------------------------------
    # Save to database
    # ------------------------------------------------------

    try:

        save_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
            birthday=birthday_value,
            username=user.username,
            display_name=user.full_name,
        )

    except Exception as exc:

        logger.exception(
            "Failed to save birthday for user %s: %s",
            user.id,
            exc,
        )

        await message.reply_text(
            "❌ *I couldn't save your birthday.*\n\n"
            "Please try again.",
            parse_mode="Markdown",
        )

        return False

    # ------------------------------------------------------
    # Clear waiting state
    # ------------------------------------------------------

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    # ------------------------------------------------------
    # Confirm
    # ------------------------------------------------------

    await message.reply_text(
        "🎂 *Birthday Saved!* 🎂\n\n"
        f"📅 Your birthday: *{birthday_value}*\n\n"
        "🎉 Melanated AZ will recognize your birthday "
        "and give you a shout-out in the chat! 💜\n\n"
        "Your birthday has been saved to the database.",
        parse_mode="Markdown",
    )

    logger.info(
        "Birthday successfully saved: "
        "user=%s chat=%s birthday=%s",
        user.id,
        message.chat_id,
        birthday_value,
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
        return

    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    # ======================================================
    # ENTER
    # ======================================================

    if data == "birthday_enter":

        context.user_data["awaiting_birthday"] = True

        await query.message.reply_text(
            "🎂 *Let's add your birthday!*\n\n"
            "Please send your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`\n\n"
            "Your birthday will be saved to "
            "the Melanated AZ database.",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # VIEW
    # ======================================================

    if data == "birthday_view":

        try:

            record = get_birthday(
                user_id=user.id,
                chat_id=query.message.chat_id,
            )

        except Exception as exc:

            logger.exception(
                "Error retrieving birthday: %s",
                exc,
            )

            await query.message.reply_text(
                "❌ Unable to retrieve your birthday right now."
            )

            return

        if not record:

            await query.message.reply_text(
                "🎂 *No Birthday Saved*\n\n"
                "You don't have a birthday saved yet.\n\n"
                "Click *Enter / Update My Birthday* below.",
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

            return

        birthday_value = record["birthday"]

        await query.message.reply_text(
            "🎂 *Your Birthday*\n\n"
            f"📅 *{birthday_value}*\n\n"
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

        try:

            removed = remove_birthday(
                user_id=user.id,
                chat_id=query.message.chat_id,
            )

        except Exception as exc:

            logger.exception(
                "Error removing birthday: %s",
                exc,
            )

            await query.message.reply_text(
                "❌ Unable to remove your birthday right now."
            )

            return

        if removed:

            await query.message.reply_text(
                "🗑️ *Birthday Removed*\n\n"
                "Your birthday has been removed "
                "from the Melanated AZ database.",
                parse_mode="Markdown",
            )

        else:

            await query.message.reply_text(
                "ℹ️ You don't currently have a birthday saved."
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

    try:

        record = get_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception as exc:

        logger.exception(
            "Error retrieving birthday: %s",
            exc,
        )

        await message.reply_text(
            "❌ Unable to retrieve your birthday right now."
        )

        return

    if not record:

        await message.reply_text(
            "🎂 *No Birthday Saved*\n\n"
            "You don't have a birthday saved yet.\n\n"
            "Use:\n"
            "`/birthday`",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

        return

    await message.reply_text(
        "🎂 *Your Birthday*\n\n"
        f"📅 *{record['birthday']}*\n\n"
        "Your birthday is saved in the "
        "Melanated AZ database. 💜",
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
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

    try:

        removed = remove_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception as exc:

        logger.exception(
            "Error removing birthday: %s",
            exc,
        )

        await message.reply_text(
            "❌ Unable to remove your birthday right now."
        )

        return

    if removed:

        await message.reply_text(
            "🗑️ *Birthday Removed*\n\n"
            "Your birthday has been removed "
            "from the Melanated AZ database.",
            parse_mode="Markdown",
        )

    else:

        await message.reply_text(
            "ℹ️ You don't currently have a birthday saved."
        )
