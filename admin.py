# ==========================================================
# Melanated AZ Bot
# admin.py
#
# FLAT ADMIN PANEL
#
# Admin command:
#   /admin
#
# Includes:
#   - Raffle management
#   - Birthday management
#   - Persistent birthday storage
# ==========================================================

import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config import ADMIN_IDS

from raffle import (
    start_raffle,
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
)

from raffle_database import (
    get_all_birthdays,
    remove_birthday_by_id,
    save_birthday,
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
# MAIN ADMIN KEYBOARD
# ==========================================================

def admin_main_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle",
                ),
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_status",
                ),
            ],
            [
                InlineKeyboardButton(
                    "👥 Raffle Entries",
                    callback_data="admin_entries",
                ),
                InlineKeyboardButton(
                    "⏳ Pending Payments",
                    callback_data="admin_pending",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ Completed Payments",
                    callback_data="admin_completed",
                ),
                InlineKeyboardButton(
                    "🏆 Draw Winner",
                    callback_data="admin_draw",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel Raffle",
                    callback_data="admin_cancel",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎂 Add Birthday",
                    callback_data="admin_birthday_add",
                ),
                InlineKeyboardButton(
                    "📅 View Birthdays",
                    callback_data="admin_birthdays",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Remove Birthday",
                    callback_data="admin_birthday_remove",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_refresh",
                ),
            ],
        ]
    )


# ==========================================================
# ADMIN MENU TEXT
# ==========================================================

def admin_menu_text():

    return (
        "👑 **Melanated AZ Admin Panel**\n\n"
        "Select an option below.\n\n"
        "🎟️ **RAFFLE**\n"
        "Start, review, monitor, and draw raffles.\n\n"
        "🎂 **BIRTHDAYS**\n"
        "Add, view, and remove member birthdays."
    )


# ==========================================================
# ADMIN MENU
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_admin(user.id):

        if update.effective_message:
            await update.effective_message.reply_text(
                "⛔ You are not authorized to use "
                "the admin panel."
            )

        return

    # ------------------------------------------------------
    # CALLBACK
    # ------------------------------------------------------

    if update.callback_query:

        query = update.callback_query

        try:
            await query.answer()
        except Exception:
            pass

        try:

            await query.edit_message_text(
                text=admin_menu_text(),
                reply_markup=admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception:

            try:

                await query.message.reply_text(
                    text=admin_menu_text(),
                    reply_markup=admin_main_keyboard(),
                    parse_mode="Markdown",
                )

            except Exception:
                logger.exception(
                    "Could not display admin menu."
                )

        return

    # ------------------------------------------------------
    # /admin COMMAND
    # ------------------------------------------------------

    await update.effective_message.reply_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# RAFFLE HANDLER WRAPPER
# ==========================================================

async def run_raffle_handler(
    handler,
    update,
    context,
    action_name,
):

    try:

        await handler(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Error running admin action: %s",
            action_name,
        )

        query = update.callback_query

        if query:

            try:

                await query.message.reply_text(
                    "⚠️ An error occurred while "
                    f"processing **{action_name}**.\n\n"
                    "Please try again.",
                    parse_mode="Markdown",
                )

            except Exception:
                pass


# ==========================================================
# RAFFLE ACTIONS
# ==========================================================

async def admin_start_raffle(update, context):

    query = update.callback_query

    if query:

        await query.answer(
            "Starting raffle setup..."
        )

    await run_raffle_handler(
        start_raffle,
        update,
        context,
        "Start Raffle",
    )


async def admin_status(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Raffle Status",
    )


async def admin_entries(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        raffle_entries,
        update,
        context,
        "Raffle Entries",
    )


async def admin_pending(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        pending_entries,
        update,
        context,
        "Pending Payments",
    )


async def admin_completed(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        paid_entry,
        update,
        context,
        "Completed Payments",
    )


async def admin_draw(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        draw_raffle,
        update,
        context,
        "Draw Winner",
    )


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

def cancel_confirmation_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⚠️ YES — CANCEL RAFFLE",
                    callback_data="admin_confirm_cancel",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ BACK",
                    callback_data="admin_back",
                )
            ],
        ]
    )


async def admin_cancel(update, context):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "⚠️ **Cancel Active Raffle?**\n\n"
        "This will cancel the currently active raffle.\n\n"
        "Are you sure?",
        reply_markup=cancel_confirmation_keyboard(),
        parse_mode="Markdown",
    )


async def admin_confirm_cancel(update, context):

    query = update.callback_query

    await query.answer(
        "Cancelling raffle..."
    )

    await run_raffle_handler(
        cancel_raffle,
        update,
        context,
        "Cancel Raffle",
    )


# ==========================================================
# NORMALIZE ADMIN BIRTHDAY
# ==========================================================

def normalize_admin_birthday(value):

    if not value:
        return None

    value = value.strip()
    value = value.replace("-", "/")

    parts = value.split("/")

    if len(parts) != 2:
        return None

    try:

        month = int(parts[0])
        day = int(parts[1])

    except (TypeError, ValueError):

        return None

    if month < 1 or month > 12:
        return None

    if day < 1 or day > 31:
        return None

    return f"{month:02d}/{day:02d}"


# ==========================================================
# ADD BIRTHDAY
# ==========================================================

async def admin_birthday_add(update, context):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):

        await query.answer(
            "⛔ You are not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    # ------------------------------------------------------
    # REMEMBER THE CHAT WHERE ADMIN STARTED THIS
    # ------------------------------------------------------

    context.user_data[
        "admin_birthday_chat_id"
    ] = query.message.chat_id

    # ------------------------------------------------------
    # WAIT FOR ADMIN TEXT
    # ------------------------------------------------------

    context.user_data[
        "awaiting_admin_birthday"
    ] = True

    await query.message.reply_text(
        "🎂 **Add Member Birthday**\n\n"
        "Send the member's Telegram User ID "
        "followed by their birthday.\n\n"
        "**Format:**\n"
        "`USER_ID MM/DD`\n\n"
        "**Example:**\n"
        "`123456789 08/27`\n\n"
        "The birthday will be saved for this "
        "Melanated AZ chat.",
        parse_mode="Markdown",
    )


# ==========================================================
# ADMIN BIRTHDAY TEXT HANDLER
# ==========================================================

async def admin_birthday_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return False

    # ------------------------------------------------------
    # ONLY HANDLE TEXT IF ADMIN BIRTHDAY MODE IS ACTIVE
    # ------------------------------------------------------

    if not context.user_data.get(
        "awaiting_admin_birthday"
    ):
        return False

    # ------------------------------------------------------
    # SECURITY
    # ------------------------------------------------------

    if not is_admin(user.id):

        context.user_data.pop(
            "awaiting_admin_birthday",
            None,
        )

        context.user_data.pop(
            "admin_birthday_chat_id",
            None,
        )

        await message.reply_text(
            "⛔ You are not authorized to add birthdays."
        )

        return True

    # ------------------------------------------------------
    # GET ORIGINAL CHAT
    # ------------------------------------------------------

    birthday_chat_id = context.user_data.get(
        "admin_birthday_chat_id"
    )

    if birthday_chat_id is None:

        context.user_data.pop(
            "awaiting_admin_birthday",
            None,
        )

        await message.reply_text(
            "⚠️ I lost track of the Melanated AZ chat.\n\n"
            "Please open `/admin` again and select "
            "🎂 Add Birthday.",
            parse_mode="Markdown",
        )

        return True

    # ------------------------------------------------------
    # PARSE:
    #
    # USER_ID MM/DD
    # ------------------------------------------------------

    text = (message.text or "").strip()

    parts = text.split()

    if len(parts) != 2:

        await message.reply_text(
            "⚠️ **Invalid format.**\n\n"
            "Please enter:\n"
            "`USER_ID MM/DD`\n\n"
            "Example:\n"
            "`123456789 08/27`",
            parse_mode="Markdown",
        )

        return True

    user_id_text = parts[0]
    birthday_text = parts[1]

    # ------------------------------------------------------
    # USER ID
    # ------------------------------------------------------

    try:

        member_user_id = int(
            user_id_text
        )

    except (TypeError, ValueError):

        await message.reply_text(
            "⚠️ Invalid Telegram User ID.\n\n"
            "Example:\n"
            "`123456789 08/27`",
            parse_mode="Markdown",
        )

        return True

    if member_user_id <= 0:

        await message.reply_text(
            "⚠️ The Telegram User ID must be a "
            "positive number."
        )

        return True

    # ------------------------------------------------------
    # BIRTHDAY
    # ------------------------------------------------------

    birthday_value = normalize_admin_birthday(
        birthday_text
    )

    if not birthday_value:

        await message.reply_text(
            "🎂 Invalid birthday.\n\n"
            "Please use MM/DD.\n\n"
            "Example:\n"
            "`08/27`",
            parse_mode="Markdown",
        )

        return True

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------

    try:

        success = save_birthday(
            user_id=member_user_id,
            chat_id=birthday_chat_id,
            birthday=birthday_value,
        )

    except Exception:

        logger.exception(
            "Failed to save admin birthday | "
            "admin=%s | member=%s | chat=%s",
            user.id,
            member_user_id,
            birthday_chat_id,
        )

        await message.reply_text(
            "❌ I couldn't save that birthday.\n\n"
            "Please check the Render logs."
        )

        return True

    if not success:

        await message.reply_text(
            "❌ The birthday could not be saved.\n\n"
            "Please try again."
        )

        return True

    # ------------------------------------------------------
    # CLEAR ADMIN INPUT MODE
    # ------------------------------------------------------

    context.user_data.pop(
        "awaiting_admin_birthday",
        None,
    )

    context.user_data.pop(
        "admin_birthday_chat_id",
        None,
    )

    # ------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------

    await message.reply_text(
        "✅ **Birthday Saved!**\n\n"
        f"👤 Telegram User ID: `{member_user_id}`\n"
        f"🎂 Birthday: **{birthday_value}**\n\n"
        "The birthday has been added to the "
        "Melanated AZ birthday list.",
        parse_mode="Markdown",
    )

    logger.info(
        "Admin added birthday | "
        "admin=%s | member=%s | birthday=%s | chat=%s",
        user.id,
        member_user_id,
        birthday_value,
        birthday_chat_id,
    )

    return True


# ==========================================================
# VIEW BIRTHDAYS
# ==========================================================

async def admin_birthdays(update, context):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    birthdays = get_all_birthdays()

    if not birthdays:

        await query.edit_message_text(
            "📅 **Saved Birthdays**\n\n"
            "No birthdays are currently saved.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin_back",
                        )
                    ]
                ]
            ),
            parse_mode="Markdown",
        )

        return

    lines = [
        "📅 **Saved Birthdays**",
        "",
        f"Total: **{len(birthdays)}**",
        "",
    ]

    for birthday in birthdays:

        display_name = (
            birthday.get("display_name")
            or birthday.get("username")
            or str(birthday.get("user_id"))
        )

        birthday_value = (
            birthday.get("birthday")
            or "Unknown"
        )

        lines.append(
            f"🎂 {display_name} — "
            f"**{birthday_value}**"
        )

    await query.edit_message_text(
        text="\n".join(lines),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🗑️ Remove Birthday",
                        callback_data=(
                            "admin_birthday_remove"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_back",
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# REMOVE BIRTHDAY LIST
# ==========================================================

def birthday_list_keyboard():

    birthdays = get_all_birthdays()

    buttons = []

    for birthday in birthdays:

        birthday_id = birthday.get("id")

        display_name = (
            birthday.get("display_name")
            or birthday.get("username")
            or str(birthday.get("user_id"))
        )

        birthday_value = (
            birthday.get("birthday")
            or "Unknown"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"🎂 {display_name} — "
                    f"{birthday_value}",
                    callback_data=(
                        f"admin_bday_remove_{birthday_id}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_back",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


# ==========================================================
# REMOVE BIRTHDAY
# ==========================================================

async def admin_birthday_remove(update, context):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    birthdays = get_all_birthdays()

    if not birthdays:

        await query.edit_message_text(
            "🗑️ **Remove Birthday**\n\n"
            "There are no saved birthdays to remove.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin_back",
                        )
                    ]
                ]
            ),
            parse_mode="Markdown",
        )

        return

    await query.edit_message_text(
        "🗑️ **Remove Birthday**\n\n"
        "Select the birthday to remove:",
        reply_markup=birthday_list_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# REMOVE ONE BIRTHDAY
# ==========================================================

async def admin_remove_birthday(
    update,
    context,
    birthday_id,
):

    query = update.callback_query

    try:

        birthday_id = int(
            birthday_id
        )

    except (TypeError, ValueError):

        await query.answer(
            "Invalid birthday.",
            show_alert=True,
        )

        return

    removed = remove_birthday_by_id(
        birthday_id
    )

    if removed:

        await query.answer(
            "Birthday removed."
        )

        await admin_birthday_remove(
            update,
            context,
        )

    else:

        await query.answer(
            "Birthday was not found.",
            show_alert=True,
        )


# ==========================================================
# REFRESH
# ==========================================================

async def admin_refresh(update, context):

    query = update.callback_query

    await query.answer(
        "Admin panel refreshed."
    )

    await query.edit_message_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# BACK
# ==========================================================

async def admin_back(update, context):

    query = update.callback_query

    await query.answer()

    # Clear any unfinished admin birthday operation.
    context.user_data.pop(
        "awaiting_admin_birthday",
        None,
    )

    context.user_data.pop(
        "admin_birthday_chat_id",
        None,
    )

    await query.edit_message_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# ADMIN BUTTON ROUTER
# ==========================================================

async def admin_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):

        await query.answer(
            "⛔ You are not authorized.",
            show_alert=True,
        )

        return

    data = query.data or ""

    logger.info(
        "Admin button pressed: %s by %s",
        data,
        user.id,
    )

    # ------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------

    if data == "admin_back":

        await admin_back(
            update,
            context,
        )

        return

    if data == "admin_refresh":

        await admin_refresh(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # RAFFLE
    # ------------------------------------------------------

    if data == "admin_start_raffle":

        await admin_start_raffle(
            update,
            context,
        )

        return

    if data == "admin_status":

        await admin_status(
            update,
            context,
        )

        return

    if data == "admin_entries":

        await admin_entries(
            update,
            context,
        )

        return

    if data == "admin_pending":

        await admin_pending(
            update,
            context,
        )

        return

    if data == "admin_completed":

        await admin_completed(
            update,
            context,
        )

        return

    if data == "admin_draw":

        await admin_draw(
            update,
            context,
        )

        return

    if data == "admin_cancel":

        await admin_cancel(
            update,
            context,
        )

        return

    if data == "admin_confirm_cancel":

        await admin_confirm_cancel(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # BIRTHDAYS
    # ------------------------------------------------------

    if data == "admin_birthday_add":

        await admin_birthday_add(
            update,
            context,
        )

        return

    if data == "admin_birthdays":

        await admin_birthdays(
            update,
            context,
        )

        return

    if data == "admin_birthday_remove":

        await admin_birthday_remove(
            update,
            context,
        )

        return

    if data.startswith(
        "admin_bday_remove_"
    ):

        birthday_id = data[
            len("admin_bday_remove_"):
        ]

        await admin_remove_birthday(
            update,
            context,
            birthday_id,
        )

        return

    # ------------------------------------------------------
    # UNKNOWN
    # ------------------------------------------------------

    logger.warning(
        "Unknown admin callback: %s",
        data,
    )

    await query.answer(
        "⚠️ This option is unavailable.",
        show_alert=True,
    )
