# ==========================================================
# Melanated AZ Bot
# admin.py
#
# FLAT ADMIN PANEL
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
                    "🎂 View Birthdays",
                    callback_data="admin_birthdays",
                ),
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
        "Welcome, Admin.\n\n"
        "🎟️ **RAFFLES**\n"
        "Start, monitor, review, and manage raffles.\n\n"
        "🎂 **BIRTHDAYS**\n"
        "View and manage member birthdays.\n\n"
        "Select an option below."
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

            await query.message.reply_text(
                text=admin_menu_text(),
                reply_markup=admin_main_keyboard(),
                parse_mode="Markdown",
            )

        return

    await update.effective_message.reply_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# RUN RAFFLE HANDLER
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
# START RAFFLE
# ==========================================================

async def admin_start_raffle(
    update,
    context,
):

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


# ==========================================================
# RAFFLE STATUS
# ==========================================================

async def admin_status(
    update,
    context,
):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Raffle Status",
    )


# ==========================================================
# RAFFLE ENTRIES
# ==========================================================

async def admin_entries(
    update,
    context,
):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        raffle_entries,
        update,
        context,
        "Raffle Entries",
    )


# ==========================================================
# PENDING PAYMENTS
# ==========================================================

async def admin_pending(
    update,
    context,
):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        pending_entries,
        update,
        context,
        "Pending Payments",
    )


# ==========================================================
# COMPLETED PAYMENTS
# ==========================================================

async def admin_completed(
    update,
    context,
):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        paid_entry,
        update,
        context,
        "Completed Payments",
    )


# ==========================================================
# DRAW WINNER
# ==========================================================

async def admin_draw(
    update,
    context,
):

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
# CANCEL CONFIRMATION
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
                    "⬅️ NO — GO BACK",
                    callback_data="admin_back",
                )
            ],
        ]
    )


async def admin_cancel(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "⚠️ **Cancel Active Raffle?**\n\n"
        "This will cancel the currently active raffle.\n\n"
        "Are you sure you want to continue?",
        reply_markup=cancel_confirmation_keyboard(),
        parse_mode="Markdown",
    )


async def admin_confirm_cancel(
    update,
    context,
):

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
# BIRTHDAY LIST
# ==========================================================

def birthday_list_keyboard():

    birthdays = get_all_birthdays()

    buttons = []

    for birthday in birthdays:

        birthday_id = birthday.get("id")

        display_name = (
            birthday.get("display_name")
            or birthday.get("username")
            or str(
                birthday.get("user_id")
            )
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


def birthday_list_text():

    birthdays = get_all_birthdays()

    if not birthdays:

        return (
            "🎂 **Birthday Management**\n\n"
            "There are currently no birthdays "
            "saved in the database."
        )

    lines = [
        "🎂 **Birthday Management**\n",
        f"Total birthdays: **{len(birthdays)}**\n",
    ]

    for birthday in birthdays:

        display_name = (
            birthday.get("display_name")
            or birthday.get("username")
            or str(
                birthday.get("user_id")
            )
        )

        birthday_value = (
            birthday.get("birthday")
            or "Unknown"
        )

        lines.append(
            f"🎂 **{display_name}** — "
            f"{birthday_value}"
        )

    return "\n".join(lines)


# ==========================================================
# VIEW BIRTHDAYS
# ==========================================================

async def admin_birthdays(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    birthdays = get_all_birthdays()

    if not birthdays:

        await query.edit_message_text(
            text=(
                "🎂 **Birthday Management**\n\n"
                "No birthdays are currently saved.\n\n"
                "Members can use `/birthday` "
                "to save their birthday."
            ),
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
        "🎂 **Saved Member Birthdays**\n",
        f"Total: **{len(birthdays)}**\n",
    ]

    for birthday in birthdays:

        display_name = (
            birthday.get("display_name")
            or birthday.get("username")
            or str(
                birthday.get("user_id")
            )
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
                        "🗑️ Manage / Remove",
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
# BIRTHDAY REMOVE LIST
# ==========================================================

async def admin_birthday_remove(
    update,
    context,
):

    query = update.callback_query

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
        "Select the birthday you want to remove:",
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

async def admin_refresh(
    update,
    context,
):

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

async def admin_back(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

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
    # MAIN
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
