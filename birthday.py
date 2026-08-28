# ==========================================================
# Melanated AZ Bot
# birthday.py
#
# MEMBER SELF-ENTRY ONLY
#
# Birthday system:
#   /birthday
#   -> Add / Update My Birthday
#   -> Type MM/DD
#
# Cleanup:
#   - Successful birthday entry message: 10 seconds
#   - Birthday bot replies: 1 minute
#   - Birthday command messages: 1 minute
#
# Actual birthday announcements are handled by:
#   birthday_scheduler.py
#
# Actual birthday announcement:
#   - Stays in group for 24 hours
#   - Then is automatically deleted
#
# Database:
#   /var/data/raffle.db
# ==========================================================

import logging
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from raffle_database import (
    save_birthday,
    get_birthday,
    remove_birthday,
)

logger = logging.getLogger(__name__)


# ==========================================================
# CLEANUP SETTINGS
# ==========================================================

BIRTHDAY_ENTRY_DELETE_SECONDS = 10
BIRTHDAY_REPLY_DELETE_SECONDS = 60


# ==========================================================
# DELETE MESSAGE JOB
# ==========================================================

async def delete_birthday_message(
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Deletes a birthday-related message.

    Job data must contain:
        chat_id
        message_id
    """

    job = context.job

    if not job:
        return

    data = job.data or {}

    chat_id = data.get("chat_id")
    message_id = data.get("message_id")

    if chat_id is None or message_id is None:
        logger.warning(
            "Birthday cleanup job missing chat/message IDs."
        )
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "Deleted birthday message | chat=%s | message=%s",
            chat_id,
            message_id,
        )

    except TelegramError as exc:

        logger.info(
            "Birthday message already deleted/unavailable | "
            "chat=%s | message=%s | error=%s",
            chat_id,
            message_id,
            exc,
        )

    except Exception:

        logger.exception(
            "Unexpected error deleting birthday message."
        )


# ==========================================================
# SCHEDULE MESSAGE DELETION
# ==========================================================

def schedule_birthday_message_deletion(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id,
    message_id,
    seconds,
    name="birthday_cleanup",
):
    """
    Schedule a birthday-related message for deletion.
    """

    if not context.job_queue:
        logger.warning(
            "JobQueue unavailable. "
            "Birthday message cleanup cannot be scheduled."
        )
        return

    context.job_queue.run_once(
        delete_birthday_message,
        when=seconds,
        data={
            "chat_id": chat_id,
            "message_id": message_id,
        },
        name=name,
    )


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
# SEND TEMPORARY REPLY
# ==========================================================

async def send_temporary_birthday_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text,
    reply_markup=None,
    parse_mode=None,
    seconds=BIRTHDAY_REPLY_DELETE_SECONDS,
):
    """
    Sends a birthday-related reply and schedules it
    for automatic deletion.
    """

    message = update.effective_message

    if not message:
        return None

    try:

        sent = await message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    except TelegramError:

        logger.exception(
            "Could not send temporary birthday reply."
        )

        return None

    schedule_birthday_message_deletion(
        context,
        sent.chat_id,
        sent.message_id,
        seconds,
    )

    return sent


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
    # Automatically delete /birthday command after 1 minute
    # ------------------------------------------------------

    schedule_birthday_message_deletion(
        context,
        message.chat_id,
        message.message_id,
        BIRTHDAY_REPLY_DELETE_SECONDS,
        name="birthday_command_cleanup",
    )

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
    # Cancel previous birthday entry
    # ------------------------------------------------------

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    # ------------------------------------------------------
    # Find existing birthday
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

    sent = await message.reply_text(
        text,
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )

    schedule_birthday_message_deletion(
        context,
        sent.chat_id,
        sent.message_id,
        BIRTHDAY_REPLY_DELETE_SECONDS,
        name="birthday_menu_cleanup",
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

    original_message = message

    birthday_value = validate_birthday(
        birthday_value
    )

    if not birthday_value:

        sent = await message.reply_text(
            "❌ **That doesn't look like a valid birthday.**\n\n"
            "Please enter your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`",
            parse_mode="Markdown",
        )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="birthday_invalid_reply",
        )

        schedule_birthday_message_deletion(
            context,
            original_message.chat_id,
            original_message.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="birthday_invalid_input",
        )

        context.user_data[
            "awaiting_birthday"
        ] = True

        return False

    # ------------------------------------------------------
    # SAVE TO DATABASE
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

        sent = await message.reply_text(
            "⚠️ I couldn't save your birthday "
            "because of a database error.\n\n"
            "Please try again.",
        )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="birthday_database_error",
        )

        return False

    if not saved:

        sent = await message.reply_text(
            "⚠️ Your birthday could not be saved.\n\n"
            "Please try again.",
        )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="birthday_save_error",
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

    # ------------------------------------------------------
    # DELETE MEMBER'S BIRTHDAY ENTRY AFTER 10 SECONDS
    # ------------------------------------------------------

    schedule_birthday_message_deletion(
        context,
        original_message.chat_id,
        original_message.message_id,
        BIRTHDAY_ENTRY_DELETE_SECONDS,
        name="birthday_entry_cleanup",
    )

    # ------------------------------------------------------
    # CONFIRMATION
    # ------------------------------------------------------

    sent = await message.reply_text(
        "🎂 **BIRTHDAY SAVED!** 🎂\n\n"
        f"📅 Your birthday: **{birthday_value}**\n\n"
        "✅ Your birthday has been saved "
        "to the Melanated AZ database.\n\n"
        "🎉 We'll recognize your special day! 💜",
        reply_markup=birthday_keyboard(),
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # DELETE CONFIRMATION AFTER 1 MINUTE
    # ------------------------------------------------------

    schedule_birthday_message_deletion(
        context,
        sent.chat_id,
        sent.message_id,
        BIRTHDAY_REPLY_DELETE_SECONDS,
        name="birthday_saved_cleanup",
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

            sent = await query.message.reply_text(
                text,
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

            schedule_birthday_message_deletion(
                context,
                sent.chat_id,
                sent.message_id,
                BIRTHDAY_REPLY_DELETE_SECONDS,
                name="birthday_menu_callback_cleanup",
            )

        except TelegramError:

            logger.exception(
                "Could not send birthday menu."
            )

        return

    # ======================================================
    # ENTER / UPDATE
    # ======================================================

    if data == "birthday_enter":

        context.user_data[
            "awaiting_birthday"
        ] = True

        sent = await query.message.reply_text(
            "🎂 **Let's add your birthday!**\n\n"
            "Just send me your birthday as:\n\n"
            "`MM/DD`\n\n"
            "Example:\n"
            "`08/26`\n\n"
            "That's it — I already know who you are. 💜",
            parse_mode="Markdown",
        )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="birthday_entry_prompt_cleanup",
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

            sent = await query.message.reply_text(
                "⚠️ I couldn't retrieve your birthday "
                "right now. Please try again.",
            )

            schedule_birthday_message_deletion(
                context,
                sent.chat_id,
                sent.message_id,
                BIRTHDAY_REPLY_DELETE_SECONDS,
                name="birthday_view_error_cleanup",
            )

            return

        if not record:

            sent = await query.message.reply_text(
                "🎂 **No Birthday Saved**\n\n"
                "You don't have a birthday saved "
                "for this chat yet.\n\n"
                "Click below to add it.",
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

        else:

            sent = await query.message.reply_text(
                "🎂 **Your Birthday**\n\n"
                f"📅 **{record['birthday']}**\n\n"
                "✅ Your birthday is saved in the "
                "Melanated AZ database. 💜",
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="birthday_view_cleanup",
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

            sent = await query.message.reply_text(
                "⚠️ I couldn't remove your birthday "
                "right now. Please try again.",
            )

            schedule_birthday_message_deletion(
                context,
                sent.chat_id,
                sent.message_id,
                BIRTHDAY_REPLY_DELETE_SECONDS,
                name="birthday_remove_error_cleanup",
            )

            return

        if removed:

            sent = await query.message.reply_text(
                "🗑️ **Birthday Removed**\n\n"
                "Your birthday has been removed "
                "from the Melanated AZ database.",
                reply_markup=birthday_keyboard(),
                parse_mode="Markdown",
            )

        else:

            sent = await query.message.reply_text(
                "ℹ️ You don't currently have "
                "a birthday saved.",
                reply_markup=birthday_keyboard(),
            )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="birthday_remove_cleanup",
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

    schedule_birthday_message_deletion(
        context,
        message.chat_id,
        message.message_id,
        BIRTHDAY_REPLY_DELETE_SECONDS,
        name="mybirthday_command_cleanup",
    )

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

        sent = await message.reply_text(
            "⚠️ I couldn't retrieve your birthday "
            "right now. Please try again.",
        )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="mybirthday_error_cleanup",
        )

        return

    if not record:

        sent = await message.reply_text(
            "🎂 **No Birthday Saved**\n\n"
            "You don't have a birthday saved "
            "for this chat yet.\n\n"
            "Click below to add it.",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

    else:

        sent = await message.reply_text(
            "🎂 **Your Birthday**\n\n"
            f"📅 **{record['birthday']}**\n\n"
            "✅ Your birthday is saved in the "
            "Melanated AZ database. 💜",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

    schedule_birthday_message_deletion(
        context,
        sent.chat_id,
        sent.message_id,
        BIRTHDAY_REPLY_DELETE_SECONDS,
        name="mybirthday_reply_cleanup",
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

    schedule_birthday_message_deletion(
        context,
        message.chat_id,
        message.message_id,
        BIRTHDAY_REPLY_DELETE_SECONDS,
        name="removebirthday_command_cleanup",
    )

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

        sent = await message.reply_text(
            "⚠️ I couldn't remove your birthday "
            "right now. Please try again.",
        )

        schedule_birthday_message_deletion(
            context,
            sent.chat_id,
            sent.message_id,
            BIRTHDAY_REPLY_DELETE_SECONDS,
            name="removebirthday_error_cleanup",
        )

        return

    context.user_data.pop(
        "awaiting_birthday",
        None,
    )

    if removed:

        sent = await message.reply_text(
            "🗑️ **Birthday Removed**\n\n"
            "Your birthday has been removed "
            "from the Melanated AZ database.",
            reply_markup=birthday_keyboard(),
            parse_mode="Markdown",
        )

    else:

        sent = await message.reply_text(
            "ℹ️ You don't currently have "
            "a birthday saved.",
            reply_markup=birthday_keyboard(),
        )

    schedule_birthday_message_deletion(
        context,
        sent.chat_id,
        sent.message_id,
        BIRTHDAY_REPLY_DELETE_SECONDS,
        name="removebirthday_reply_cleanup",
    )
