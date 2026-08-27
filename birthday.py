# ==========================================================
# Melanated AZ Bot
# birthday.py
#
# MEMBER SELF-ENTRY ONLY
#
# Members:
#   /birthday
#   -> Add / Update My Birthday
#   -> Type MM/DD
#
# No username required.
# No Telegram user ID required.
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
                    "🎂 Add / Update My Birthday",
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
# SIMPLE BACK BUTTON
# ==========================================================

def birthday_back_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Birthday Menu",
                    callback_data="birthday_menu",
                )
            ]
        ]
    )


# ==========================================================
# VALIDATE BIRTHDAY
# ==========================================================

def validate_birthday(value):

    if not value:
        return None

    value = value.strip()

    # Accept:
    # 08/26
    # 8/26
    # 08-26
    # 8-26

    value = value.replace("-", "/")

    try:

        parsed = datetime.strptime(
            value,
            "%m/%d",
        )

        return parsed.strftime("%m/%d")

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

        birthday_value = " ".join(
            context.args
        ).strip()

        await save_birthday_from_value(
            update,
            context,
            birthday_value,
        )

        return

    # ------------------------------------------------------
    # Cancel any previous birthday entry
    # ------------------------------------------------------

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    # ------------------------------------------------------
    # Find this user's birthday automatically
    # ------------------------------------------------------

    try:

        existing = get_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception:

        logger.exception(
            "Error retrieving birthday for user %s",
            user.id,
        )

        existing = None

    # ------------------------------------------------------
    # Existing birthday
    # ------------------------------------------------------

    if existing:

        text = (
            "🎂 **Your Melanated AZ Birthday** 🎂\n\n"
            f"📅 Current birthday: "
            f"**{existing['birthday']}**\n\n"
            "You can update or remove it below."
        )

    # ------------------------------------------------------
    # No birthday
    # ------------------------------------------------------

    else:

        text = (
            "🎂 **MELANATED AZ BIRTHDAY** 🎂\n\n"
            "We love celebrating our members! 💜\n\n"
            "Add your birthday and Melanated AZ "
            "will recognize your special day. 🎉\n\n"
            "Your birthday is saved to the "
            "Melanated AZ database.\n\n"
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

    # ------------------------------------------------------
    # Validate
    # ------------------------------------------------------

    birthday_value = validate_birthday(
        birthday_value
    )

    if not birthday_value:

        await message.reply_text(
            "❌ **That doesn't look like a valid birthday.**\n\n"
            "Please enter your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        # Keep waiting so the member can correct it.
        context.user_data[
            "awaiting_birthday"
        ] = True

        return False

    # ------------------------------------------------------
    # SAVE USING AUTOMATIC TELEGRAM USER ID
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
            "Please try again.",
        )

        return False

    if not saved:

        await message.reply_text(
            "⚠️ Your birthday could not be saved.\n\n"
            "Please try again.",
        )

        return False

    # ------------------------------------------------------
    # Clear waiting state
    # ------------------------------------------------------

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
        "✅ Your birthday has been saved "
        "to the Melanated AZ database.\n\n"
        "🎉 We'll recognize your special day! 💜",
        reply_markup=birthday_keyboard(),
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
    # BIRTHDAY MENU
    # ======================================================

    if data == "birthday_menu":

        context.user_data.pop(
            "awaiting_birthday",
            None,
        )

        try:

            existing = get_birthday(
                user_id=user.id,
                chat_id=query.message.chat_id,
            )

        except Exception:

            logger.exception(
                "Error retrieving birthday for user %s",
                user.id,
            )

            existing = None

        if existing:

            text = (
                "🎂 **Your Melanated AZ Birthday** 🎂\n\n"
                f"📅 Current birthday: "
                f"**{existing['birthday']}**\n\n"
                "Choose an option below:"
            )

        else:

            text = (
                "🎂 **MELANATED AZ BIRTHDAY** 🎂\n\n"
                "Add your birthday so we can "
                "celebrate with you! 🎉\n\n"
                "Choose an option below:"
            )

        try:

            await query.edit_message_text(
                text,
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

        except Exception:

            await query.message.reply_text(
                text,
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

        return

    # ======================================================
    # ENTER / UPDATE
    # ======================================================

    if data == "birthday_enter":

        context.user_data[
            "awaiting_birthday"
        ] = True

        await query.message.reply_text(
            "🎂 **Let's add your birthday!**\n\n"
            "Just send me your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`\n\n"
            "That's it — I already know who you are. 💜",
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

        except Exception:

            logger.exception(
                "Error retrieving birthday for user %s",
                user.id,
            )

            await query.message.reply_text(
                "⚠️ I couldn't retrieve your birthday "
                "right now. Please try again.",
            )

            return

        if not record:

            await query.message.reply_text(
                "🎂 **No Birthday Saved**\n\n"
                "You don't have a birthday saved "
                "for this chat yet.\n\n"
                "Click below to add it.",
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

        context.user_data.pop(
            "awaiting_birthday",
            None,
        )

        try:

            removed = remove_birthday(
                user_id=user.id,
                chat_id=query.message.chat_id,
            )

        except Exception:

            logger.exception(
                "Error removing birthday for user %s",
                user.id,
            )

            await query.message.reply_text(
                "⚠️ I couldn't remove your birthday "
                "right now. Please try again.",
            )

            return

        if removed:

            await query.message.reply_text(
                "🗑️ **Birthday Removed**\n\n"
                "Your birthday has been removed "
                "from the Melanated AZ database.",
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

        else:

            await query.message.reply_text(
                "ℹ️ You don't currently have "
                "a birthday saved.",
                reply_markup=birthday_keyboard(),
            )

        return


# ==========================================================
# TEXT INPUT
#
# This catches the birthday AFTER the member clicks
# "Add / Update My Birthday".
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

    try:

        record = get_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception:

        logger.exception(
            "Error retrieving birthday for user %s",
            user.id,
        )

        await message.reply_text(
            "⚠️ I couldn't retrieve your birthday "
            "right now. Please try again.",
        )

        return

    if not record:

        await message.reply_text(
            "🎂 **No Birthday Saved**\n\n"
            "You don't have a birthday saved "
            "for this chat yet.\n\n"
            "Click below to add it.",
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

    try:

        removed = remove_birthday(
            user_id=user.id,
            chat_id=message.chat_id,
        )

    except Exception:

        logger.exception(
            "Error removing birthday for user %s",
            user.id,
        )

        await message.reply_text(
            "⚠️ I couldn't remove your birthday "
            "right now. Please try again.",
        )

        return

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    if removed:

        await message.reply_text(
            "🗑️ **Birthday Removed**\n\n"
            "Your birthday has been removed "
            "from the Melanated AZ database.",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

    else:

        await message.reply_text(
            "ℹ️ You don't currently have "
            "a birthday saved.",
            reply_markup=birthday_keyboard(),
        )
