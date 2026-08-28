# ==========================================================
# Melanated AZ Bot
# birthday.py
#
# Persistent Birthday System
#
# Uses the existing raffle_database.py birthdays table.
#
# Database fields:
#   user_id
#   chat_id
#   birthday
#   username
#   display_name
#   created_at
#   updated_at
#
# Commands:
#   /birthday
#   /mybirthday
#   /removebirthday
#
# Birthday format:
#   MM/DD
#
# Examples:
#   /birthday 08/27
#   /birthday 12/25
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

from raffle_database import (
    save_birthday,
    get_birthday,
    get_all_birthdays,
    remove_birthday,
    remove_birthday_by_id,
)

from admin import is_admin


logger = logging.getLogger(__name__)


# ==========================================================
# BIRTHDAY FORMAT
# ==========================================================

BIRTHDAY_PATTERN = re.compile(
    r"^(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])$"
)


# ==========================================================
# VALIDATE BIRTHDAY
# ==========================================================

def normalize_birthday(value):

    if not value:
        return None

    value = value.strip()

    # Allow 8/27 as well as 08/27
    value = value.replace("-", "/")

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

    birthday = f"{month:02d}/{day:02d}"

    if not BIRTHDAY_PATTERN.match(birthday):
        return None

    return birthday


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
    # If a date was supplied
    # ------------------------------------------------------

    if context.args:

        birthday_value = normalize_birthday(
            context.args[0]
        )

        if not birthday_value:

            await message.reply_text(
                "🎂 I couldn't understand that birthday.\n\n"
                "Please use:\n"
                "/birthday MM/DD\n\n"
                "Example:\n"
                "/birthday 08/27"
            )

            return

        chat_id = message.chat_id

        success = save_birthday(
            user_id=user.id,
            chat_id=chat_id,
            birthday=birthday_value,
            username=user.username,
            display_name=user.full_name,
        )

        if success:

            await message.reply_text(
                "🎉 Your birthday has been saved!\n\n"
                f"🎂 Birthday: {birthday_value}\n\n"
                "We'll celebrate you in Melanated AZ "
                "on your birthday! 🥳💜"
            )

        return

    # ------------------------------------------------------
    # Show birthday menu
    # ------------------------------------------------------

    await message.reply_text(
        "🎂 **Melanated AZ Birthday System**\n\n"
        "Let's celebrate each other! 🥳\n\n"
        "To add or update your birthday, use:\n\n"
        "🎂 `/birthday MM/DD`\n\n"
        "Example:\n"
        "`/birthday 08/27`\n\n"
        "Your birthday is saved permanently in the "
        "Melanated AZ database until you change or "
        "remove it.",
        parse_mode="Markdown",
        reply_markup=birthday_keyboard(),
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

        await message.reply_text(
            "🎂 You don't have a birthday saved yet.\n\n"
            "Use:\n"
            "/birthday MM/DD\n\n"
            "Example:\n"
            "/birthday 08/27"
        )

        return

    birthday_value = birthday_record.get(
        "birthday"
    )

    await message.reply_text(
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

        await message.reply_text(
            "🗑️ Your birthday has been removed "
            "from the Melanated AZ birthday list."
        )

    else:

        await message.reply_text(
            "🎂 You don't currently have a birthday "
            "saved in this chat."
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

        await message.reply_text(
            "🎂 Please enter your birthday using MM/DD.\n\n"
            "Example: 08/27"
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

    await message.reply_text(
        "🎉 Birthday saved!\n\n"
        f"🎂 {birthday_value}\n\n"
        "We'll celebrate you on your birthday! 🥳💜"
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

        await query.message.reply_text(
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

            await query.message.reply_text(
                "🎂 No birthdays have been added yet."
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

        await query.message.reply_text(
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

            await query.message.reply_text(
                "🗑️ Your birthday has been removed."
            )

        else:

            await query.message.reply_text(
                "🎂 You don't have a birthday saved "
                "in this chat."
            )

        return


# ==========================================================
# ADMIN BIRTHDAY LIST
# ==========================================================

async def birthday_admin_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await is_admin(update, context):
        return

    birthdays = get_all_birthdays()

    if not birthdays:

        await update.effective_message.reply_text(
            "🎂 There are no birthdays saved."
        )

        return

    lines = [
        "🎂 **Melanated AZ Birthday List**",
        "",
    ]

    for record in birthdays:

        birthday_id = record.get("id")

        name = (
            record.get("display_name")
            or record.get("username")
            or "Unknown"
        )

        birthday_value = record.get(
            "birthday",
            "Unknown",
        )

        chat_id = record.get(
            "chat_id"
        )

        lines.append(
            f"#{birthday_id} — "
            f"{birthday_value} — "
            f"{name} — "
            f"{chat_id}"
        )

    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ==========================================================
# END birthday.py
# ==========================================================
