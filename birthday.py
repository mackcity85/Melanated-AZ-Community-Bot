# ==========================================================
# Melanated AZ Bot
# birthday.py
#
# Persistent Birthday System
#
# Uses raffle_database.py
#
# Commands:
#   /birthday
#   /mybirthday
#   /removebirthday
#
# Birthday format:
#   MM/DD
#
# ==========================================================

import logging
import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from telegram.error import TelegramError

from raffle_database import (
    save_birthday,
    get_birthday,
    get_all_birthdays,
    remove_birthday,
)


logger = logging.getLogger(__name__)


# ==========================================================
# CONFIGURATION
# ==========================================================

BIRTHDAY_RESPONSE_DELETE_SECONDS = 60


# ==========================================================
# BIRTHDAY FORMAT
# ==========================================================

BIRTHDAY_PATTERN = re.compile(
    r"^(0[1-9]|1[0-2])/"
    r"(0[1-9]|[12][0-9]|3[01])$"
)


# ==========================================================
# NORMALIZE BIRTHDAY
# ==========================================================

def normalize_birthday(value):

    if not value:
        return None

    value = value.strip()

    value = value.replace(
        "-",
        "/",
    )

    parts = value.split("/")

    if len(parts) != 2:
        return None

    try:

        month = int(parts[0])
        day = int(parts[1])

    except ValueError:

        return None

    if month < 1 or month > 12:
        return None

    if day < 1 or day > 31:
        return None

    birthday_value = (
        f"{month:02d}/{day:02d}"
    )

    if not BIRTHDAY_PATTERN.match(
        birthday_value
    ):
        return None

    return birthday_value


# ==========================================================
# DELETE TEMPORARY BIRTHDAY RESPONSE
# ==========================================================

async def delete_birthday_response(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    chat_id = data.get(
        "chat_id"
    )

    message_id = data.get(
        "message_id"
    )

    if (
        chat_id is None
        or message_id is None
    ):
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "Deleted birthday response | "
            "chat=%s | message=%s",
            chat_id,
            message_id,
        )

    except TelegramError as exc:

        logger.info(
            "Could not delete birthday response | "
            "chat=%s | message=%s | error=%s",
            chat_id,
            message_id,
            exc,
        )

    except Exception:

        logger.exception(
            "Unexpected error deleting birthday response."
        )


# ==========================================================
# SEND TEMPORARY BIRTHDAY RESPONSE
# ==========================================================

async def send_birthday_response(
    context,
    chat_id,
    text,
    reply_markup=None,
    parse_mode=None,
):

    if chat_id is None:
        return None

    try:

        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

        if context.job_queue:

            context.job_queue.run_once(
                delete_birthday_response,
                when=BIRTHDAY_RESPONSE_DELETE_SECONDS,
                data={
                    "chat_id": chat_id,
                    "message_id": (
                        sent_message.message_id
                    ),
                },
                name=(
                    "delete_birthday_response_"
                    f"{chat_id}_"
                    f"{sent_message.message_id}"
                ),
            )

        return sent_message

    except TelegramError:

        logger.exception(
            "Could not send birthday response."
        )

    return None


# ==========================================================
# BIRTHDAY KEYBOARD
# ==========================================================

def birthday_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎂 Set My Birthday",
                    callback_data="birthday_enter",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎉 View Birthdays",
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
    # DATE SUPPLIED
    # ------------------------------------------------------

    if context.args:

        birthday_value = normalize_birthday(
            context.args[0]
        )

        if not birthday_value:

            await send_birthday_response(
                context,
                message.chat_id,
                "🎂 I couldn't understand that birthday.\n\n"
                "Please use:\n"
                "/birthday MM/DD\n\n"
                "Example:\n"
                "/birthday 08/27",
            )

            return

        success = save_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
            birthday=birthday_value,
            username=user.username,
            display_name=user.full_name,
        )

        if success:

            await send_birthday_response(
                context,
                message.chat_id,
                "🎉 Your birthday has been saved!\n\n"
                f"🎂 Birthday: {birthday_value}\n\n"
                "We'll celebrate you in Melanated AZ "
                "on your birthday! 🥳💜",
            )

        return

    # ------------------------------------------------------
    # SHOW BIRTHDAY MENU
    # ------------------------------------------------------

    await send_birthday_response(
        context,
        message.chat_id,
        "🎂 **Melanated AZ Birthday System**\n\n"
        "Let's celebrate each other! 🥳\n\n"
        "To add or update your birthday, use:\n\n"
        "🎂 `/birthday MM/DD`\n\n"
        "Example:\n"
        "`/birthday 08/27`\n\n"
        "Your birthday is saved permanently in the "
        "Melanated AZ database until you change or "
        "remove it.",
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# MY BIRTHDAY
# ==========================================================

async def my_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    birthday_record = get_birthday(
        user.id,
        message.chat_id,
    )

    if not birthday_record:

        await send_birthday_response(
            context,
            message.chat_id,
            "🎂 You don't have a birthday saved yet.\n\n"
            "Use:\n"
            "/birthday MM/DD\n\n"
            "Example:\n"
            "/birthday 08/27",
        )

        return

    birthday_value = birthday_record.get(
        "birthday"
    )

    await send_birthday_response(
        context,
        message.chat_id,
        "🎂 **Your Melanated AZ Birthday**\n\n"
        f"🎉 {birthday_value}\n\n"
        "Use `/birthday MM/DD` to update it.",
        parse_mode="Markdown",
    )


# ==========================================================
# REMOVE MY BIRTHDAY
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
        user.id,
        message.chat_id,
    )

    if removed:

        await send_birthday_response(
            context,
            message.chat_id,
            "🗑️ Your birthday has been removed "
            "from the Melanated AZ birthday list.",
        )

    else:

        await send_birthday_response(
            context,
            message.chat_id,
            "🎂 You don't currently have a birthday "
            "saved in this chat.",
        )


# ==========================================================
# BIRTHDAY TEXT HANDLER
# ==========================================================

async def birthday_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return False

    awaiting = context.user_data.get(
        "awaiting_birthday"
    )

    if not awaiting:
        return False

    birthday_value = normalize_birthday(
        message.text
    )

    if not birthday_value:

        await send_birthday_response(
            context,
            message.chat_id,
            "🎂 Please enter your birthday using MM/DD.\n\n"
            "Example: 08/27",
        )

        return True

    save_birthday(
        user_id=user.id,
        chat_id=message.chat_id,
        birthday=birthday_value,
        username=user.username,
        display_name=user.full_name,
    )

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    await send_birthday_response(
        context,
        message.chat_id,
        "🎉 Birthday saved!\n\n"
        f"🎂 {birthday_value}\n\n"
        "We'll celebrate you on your birthday! 🥳💜",
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

    user = update.effective_user

    if not user:

        await query.answer()

        return

    await query.answer()

    data = query.data or ""

    # ======================================================
    # ENTER BIRTHDAY
    # ======================================================

    if data == "birthday_enter":

        context.user_data[
            "awaiting_birthday"
        ] = True

        await send_birthday_response(
            context,
            query.message.chat_id,
            "🎂 **Set Your Birthday**\n\n"
            "Enter your birthday using:\n\n"
            "MM/DD\n\n"
            "Example:\n"
            "08/27",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # VIEW BIRTHDAYS
    # ======================================================

    if data == "birthday_view":

        birthdays = get_all_birthdays()

        if not birthdays:

            await send_birthday_response(
                context,
                query.message.chat_id,
                "🎂 No birthdays have been added yet.",
            )

            return

        lines = [
            "🎉 **Melanated AZ Birthdays** 🎂",
            "",
        ]

        for record in birthdays:

            name = (
                record.get("display_name")
                or record.get("username")
                or "Melanated AZ Member"
            )

            birthday_value = record.get(
                "birthday",
                "Unknown",
            )

            lines.append(
                f"🎂 {birthday_value} — {name}"
            )

        await send_birthday_response(
            context,
            query.message.chat_id,
            "\n".join(lines),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # REMOVE BIRTHDAY
    # ======================================================

    if data == "birthday_remove":

        removed = remove_birthday(
            user.id,
            query.message.chat_id,
        )

        if removed:

            await send_birthday_response(
                context,
                query.message.chat_id,
                "🗑️ Your birthday has been removed.",
            )

        else:

            await send_birthday_response(
                context,
                query.message.chat_id,
                "🎂 You don't have a birthday saved "
                "in this chat.",
            )

        return


# ==========================================================
# END birthday.py
# ==========================================================
