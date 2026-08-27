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

from config import ADMIN_IDS

from raffle_database import (
    save_birthday,
    get_birthday,
    remove_birthday,
)

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    try:
        return int(user_id) in [
            int(admin_id)
            for admin_id in ADMIN_IDS
        ]
    except (TypeError, ValueError):
        return False


# ==========================================================
# MEMBER BIRTHDAY KEYBOARD
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
# SAVE ADMIN BIRTHDAY
# ==========================================================

async def save_admin_birthday(
    update,
    context,
    value,
):

    message = update.effective_message
    admin = update.effective_user

    if not message or not admin:
        return True

    if not is_admin(admin.id):
        return False

    parts = value.strip().split()

    if len(parts) != 2:

        await message.reply_text(
            "❌ Invalid format.\n\n"
            "Use:\n"
            "`USER_ID MM/DD`\n\n"
            "Example:\n"
            "`123456789 08/26`",
            parse_mode="Markdown",
        )

        return True

    user_id_text = parts[0]
    birthday_value = parts[1]

    try:

        user_id = int(user_id_text)

    except ValueError:

        await message.reply_text(
            "❌ Invalid Telegram User ID.\n\n"
            "The first value must be a number.",
        )

        return True

    birthday_value = validate_birthday(
        birthday_value
    )

    if not birthday_value:

        await message.reply_text(
            "❌ Invalid birthday.\n\n"
            "Use `MM/DD`.\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return True

    try:

        save_birthday(
            user_id=user_id,
            chat_id=message.chat_id,
            birthday=birthday_value,
            username=None,
            display_name=f"User {user_id}",
        )

    except Exception:

        logger.exception(
            "Admin failed to save birthday"
        )

        await message.reply_text(
            "⚠️ Database error while saving "
            "the birthday."
        )

        return True

    context.user_data.pop(
        "awaiting_admin_birthday",
        None,
    )

    await message.reply_text(
        "🎂 **Birthday Added**\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"📅 Birthday: **{birthday_value}**\n\n"
        "✅ The birthday has been saved.",
        parse_mode="Markdown",
    )

    logger.info(
        "Admin added birthday | admin=%s | user=%s | birthday=%s",
        admin.id,
        user_id,
        birthday_value,
    )

    return True


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

    if context.args:

        birthday_value = context.args[0].strip()

        await save_birthday_from_value(
            update,
            context,
            birthday_value,
        )

        return

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
            "Choose an option below:"
        )

    await message.reply_text(
        text,
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# SAVE MEMBER BIRTHDAY
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
            "Please enter:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        return False

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
            "because of a database error."
        )

        return False

    if not saved:

        await message.reply_text(
            "⚠️ Your birthday could not be saved."
        )

        return False

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    await message.reply_text(
        "🎂 **BIRTHDAY SAVED!** 🎂\n\n"
        f"📅 Your birthday: **{birthday_value}**\n\n"
        "✅ Your birthday has been saved.\n\n"
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

    # ------------------------------------------------------
    # ENTER
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # VIEW
    # ------------------------------------------------------

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
            "✅ Your birthday is saved. 💜",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # REMOVE
    # ------------------------------------------------------

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
                "Your birthday has been removed.",
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

    # ------------------------------------------------------
    # ADMIN ADD BIRTHDAY
    # ------------------------------------------------------

    if context.user_data.get(
        "awaiting_admin_birthday"
    ):

        return await save_admin_birthday(
            update,
            context,
            update.effective_message.text
            if update.effective_message
            else "",
        )

    # ------------------------------------------------------
    # MEMBER BIRTHDAY
    # ------------------------------------------------------

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
            "Use `/birthday` to add your birthday.",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

        return

    await message.reply_text(
        "🎂 **Your Birthday**\n\n"
        f"📅 **{record['birthday']}**\n\n"
        "✅ Your birthday is saved. 💜",
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
            "Your birthday has been removed.",
            parse_mode="Markdown",
        )

    else:

        await message.reply_text(
            "ℹ️ You don't currently have "
            "a birthday saved."
        )
