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
# BIRTHDAY BUTTON MENU
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

    # ======================================================
    # DIRECT DATE
    # ======================================================

    if context.args:

        birthday_value = context.args[0].strip()

        await save_birthday_from_value(
            update,
            context,
            birthday_value,
        )

        return

    # ======================================================
    # BIRTHDAY MENU
    # ======================================================

    await message.reply_text(
        "🎂 **MELANATED AZ BIRTHDAY** 🎂\n\n"
        "We love celebrating our members! 💜\n\n"
        "Enter your birthday and Melanated AZ "
        "will give you a birthday shout-out "
        "in the chat on your special day. 🎉\n\n"
        "Your birthday is stored in our database "
        "so it remains saved when the bot restarts.\n\n"
        "Choose an option below:",
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# VALIDATE BIRTHDAY
# ==========================================================

def validate_birthday(
    birthday_value,
):

    if not birthday_value:
        return None

    birthday_value = birthday_value.strip()

    # Allow common formats but save consistently as MM/DD.
    formats = [
        "%m/%d",
        "%m-%d",
        "%m.%d",
    ]

    for date_format in formats:

        try:

            parsed = datetime.strptime(
                birthday_value,
                date_format,
            )

            return parsed.strftime("%m/%d")

        except ValueError:
            continue

    return None


# ==========================================================
# SAVE BIRTHDAY FROM VALUE
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

    normalized_birthday = validate_birthday(
        birthday_value
    )

    if not normalized_birthday:

        await message.reply_text(
            "❌ **Invalid birthday.**\n\n"
            "Please enter your birthday using:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return False

    # ======================================================
    # SAVE TO DATABASE
    # ======================================================

    try:

        saved = save_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
            birthday=normalized_birthday,
            username=user.username,
            display_name=user.full_name,
        )

    except Exception:

        logger.exception(
            "DATABASE ERROR saving birthday "
            "for user %s in chat %s",
            user.id,
            message.chat_id,
        )

        await message.reply_text(
            "⚠️ I couldn't save your birthday right now.\n\n"
            "Please try again in a moment."
        )

        return False

    if not saved:

        await message.reply_text(
            "⚠️ Your birthday could not be saved.\n\n"
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
    # VERIFY DATABASE SAVE
    # ======================================================

    try:

        verification = get_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception:

        logger.exception(
            "Could not verify birthday save "
            "for user %s in chat %s",
            user.id,
            message.chat_id,
        )

        verification = None

    if not verification:

        logger.error(
            "Birthday save verification FAILED "
            "for user %s in chat %s",
            user.id,
            message.chat_id,
        )

        await message.reply_text(
            "⚠️ Your birthday could not be verified "
            "in the database.\n\n"
            "Please try again."
        )

        return False

    # ======================================================
    # SUCCESS
    # ======================================================

    await message.reply_text(
        "🎂 **Birthday Saved!** 🎂\n\n"
        f"📅 Your birthday: **{normalized_birthday}**\n\n"
        "🎉 Melanated AZ will recognize your birthday "
        "in the chat and give you a shout-out! 💜\n\n"
        "Your birthday has been successfully stored "
        "in the database.",
        parse_mode="Markdown",
    )

    logger.info(
        "🎂 Birthday saved and verified — "
        "user=%s chat=%s birthday=%s",
        user.id,
        message.chat_id,
        normalized_birthday,
    )

    return True


# ==========================================================
# BIRTHDAY BUTTON HANDLER
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

    try:
        await query.answer()
    except Exception:
        pass

    # ======================================================
    # ENTER BIRTHDAY
    # ======================================================

    if data == "birthday_enter":

        context.user_data["awaiting_birthday"] = True

        await query.message.reply_text(
            "🎂 **Let's add your birthday!**\n\n"
            "Please send your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`\n\n"
            "Your birthday will be saved to the "
            "Melanated AZ database.",
            parse_mode="Markdown",
        )

        logger.info(
            "Birthday input started for user %s in chat %s",
            user.id,
            query.message.chat_id,
        )

        return

    # ======================================================
    # VIEW BIRTHDAY
    # ======================================================

    if data == "birthday_view":

        try:

            record = get_birthday(
                user_id=user.id,
                chat_id=query.message.chat_id,
            )

        except Exception:

            logger.exception(
                "Database error retrieving birthday "
                "for user %s",
                user.id,
            )

            await query.message.reply_text(
                "⚠️ I couldn't retrieve your birthday "
                "right now. Please try again."
            )

            return

        if not record:

            await query.message.reply_text(
                "🎂 **No Birthday Saved**\n\n"
                "You don't have a birthday saved yet.\n\n"
                "Use the button below to enter yours.",
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
    # REMOVE BIRTHDAY
    # ======================================================

    if data == "birthday_remove":

        try:

            removed = remove_birthday(
                user_id=user.id,
                chat_id=query.message.chat_id,
            )

        except Exception:

            logger.exception(
                "Database error removing birthday "
                "for user %s",
                user.id,
            )

            await query.message.reply_text(
                "⚠️ I couldn't remove your birthday "
                "right now. Please try again."
            )

            return

        if removed:

            await query.message.reply_text(
                "🗑️ **Birthday Removed**\n\n"
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

    logger.info(
        "Birthday text received from user %s: %s",
        update.effective_user.id
        if update.effective_user
        else "unknown",
        birthday_value,
    )

    await save_birthday_from_value(
        update,
        context,
        birthday_value,
    )

    return True


# ==========================================================
# VIEW BIRTHDAY COMMAND
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

    try:

        record = get_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception:

        logger.exception(
            "Database error retrieving birthday "
            "for user %s",
            user.id,
        )

        await message.reply_text(
            "⚠️ I couldn't retrieve your birthday "
            "right now. Please try again."
        )

        return

    if not record:

        await message.reply_text(
            "🎂 **No Birthday Saved**\n\n"
            "You don't have a birthday saved yet.\n\n"
            "Use:\n"
            "`/birthday`\n\n"
            "or use the birthday button.",
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
# REMOVE BIRTHDAY COMMAND
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

    try:

        removed = remove_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception:

        logger.exception(
            "Database error removing birthday "
            "for user %s",
            user.id,
        )

        await message.reply_text(
            "⚠️ I couldn't remove your birthday "
            "right now. Please try again."
        )

        return

    if removed:

        await message.reply_text(
            "🗑️ **Birthday Removed**\n\n"
            "Your birthday has been removed "
            "from the Melanated AZ database.",
            parse_mode="Markdown",
        )

    else:

        await message.reply_text(
            "ℹ️ You don't currently have a birthday saved."
        )
