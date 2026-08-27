# ==========================================================
# Melanated AZ Bot
# admin.py
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
    enter_raffle,
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
    reroll_raffle,
    bonus_entry,
    remove_raffle_entry,
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
# ADMIN MAIN KEYBOARD
# ==========================================================

def admin_main_keyboard():

    return InlineKeyboardMarkup(
        [

            # ------------------------------------------------
            # RAFFLE
            # ------------------------------------------------

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
                    "🔄 Reroll Winner",
                    callback_data="admin_reroll",
                ),
                InlineKeyboardButton(
                    "❌ Cancel Raffle",
                    callback_data="admin_cancel",
                ),
            ],

            # ------------------------------------------------
            # BIRTHDAYS
            # ------------------------------------------------

            [
                InlineKeyboardButton(
                    "🎂 Birthday",
                    callback_data="admin_birthday",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📅 View All Birthdays",
                    callback_data="admin_birthdays",
                ),
            ],

            # ------------------------------------------------
            # REFRESH
            # ------------------------------------------------

            [
                InlineKeyboardButton(
                    "🔄 Refresh Admin Panel",
                    callback_data="admin_refresh",
                ),
            ],
        ]
    )


# ==========================================================
# ADMIN PANEL TEXT
# ==========================================================

def admin_panel_text():

    return (
        "👑 *Melanated AZ Admin Panel*\n\n"

        "🎟️ *RAFFLE MANAGEMENT*\n"
        "Use the buttons below to manage the raffle.\n\n"

        "🎟️ Start Raffle\n"
        "📊 Raffle Status\n"
        "👥 Raffle Entries\n"
        "⏳ Pending Payments\n"
        "✅ Completed Payments\n"
        "🏆 Draw Winner\n"
        "🔄 Reroll Winner\n"
        "❌ Cancel Raffle\n\n"

        "🎂 *BIRTHDAY MANAGEMENT*\n"
        "Manage member birthdays below."
    )


# ==========================================================
# SHOW ADMIN PANEL
# ==========================================================

async def show_admin_panel(
    update,
    context,
):

    query = update.callback_query

    if query:

        try:

            await query.edit_message_text(
                text=admin_panel_text(),
                reply_markup=admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception:

            await query.message.reply_text(
                text=admin_panel_text(),
                reply_markup=admin_main_keyboard(),
                parse_mode="Markdown",
            )

        return

    message = update.effective_message

    if message:

        await message.reply_text(
            text=admin_panel_text(),
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown",
        )


# ==========================================================
# ADMIN COMMAND
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:

        return

    if not is_admin(user.id):

        if update.effective_message:

            await update.effective_message.reply_text(
                "⛔ You are not authorized to use "
                "the Melanated AZ admin panel."
            )

        return

    await show_admin_panel(
        update,
        context,
    )


# ==========================================================
# SAFE RAFFLE ACTION
# ==========================================================

async def run_raffle_action(
    update,
    context,
    handler,
    action_name,
):

    query = update.callback_query

    try:

        await handler(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Admin raffle action failed: %s",
            action_name,
        )

        if query:

            try:

                await query.message.reply_text(
                    f"⚠️ Unable to process "
                    f"*{action_name}*.\n\n"
                    f"Please check the bot log for details.",
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

    await query.answer()

    await run_raffle_action(
        update,
        context,
        start_raffle,
        "Start Raffle",
    )


# ==========================================================
# STATUS
# ==========================================================

async def admin_status(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_action(
        update,
        context,
        raffle_status,
        "Raffle Status",
    )


# ==========================================================
# ENTRIES
# ==========================================================

async def admin_entries(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_action(
        update,
        context,
        raffle_entries,
        "Raffle Entries",
    )


# ==========================================================
# PENDING
# ==========================================================

async def admin_pending(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_action(
        update,
        context,
        pending_entries,
        "Pending Payments",
    )


# ==========================================================
# COMPLETED
# ==========================================================

async def admin_completed(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_action(
        update,
        context,
        paid_entry,
        "Completed Payments",
    )


# ==========================================================
# DRAW
# ==========================================================

async def admin_draw(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_action(
        update,
        context,
        draw_raffle,
        "Draw Winner",
    )


# ==========================================================
# REROLL
# ==========================================================

async def admin_reroll(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_action(
        update,
        context,
        reroll_raffle,
        "Reroll Winner",
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
                    "⬅️ Back",
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
        "⚠️ *Cancel Active Raffle?*\n\n"
        "This will cancel the currently active raffle.\n\n"
        "Are you sure?",
        reply_markup=cancel_confirmation_keyboard(),
        parse_mode="Markdown",
    )


async def admin_confirm_cancel(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_action(
        update,
        context,
        cancel_raffle,
        "Cancel Raffle",
    )


# ==========================================================
# BIRTHDAY MENU
# ==========================================================

def birthday_admin_keyboard():

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "🎂 Birthday Commands",
                    callback_data="admin_birthday_info",
                )
            ],

            [
                InlineKeyboardButton(
                    "📅 View All Birthdays",
                    callback_data="admin_birthdays",
                )
            ],

            [
                InlineKeyboardButton(
                    "⬅️ Back to Admin Panel",
                    callback_data="admin_back",
                )
            ],

        ]
    )


async def admin_birthday(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "🎂 *Birthday Management*\n\n"
        "Members can use:\n\n"
        "🎂 /birthday — Enter or update birthday\n"
        "📅 /mybirthday — View saved birthday\n"
        "🗑️ /removebirthday — Remove birthday\n\n"
        "Birthdays are permanently stored in "
        "the database.\n\n"
        "Use the button below to view all saved "
        "birthdays.",
        reply_markup=birthday_admin_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# BIRTHDAY INFO
# ==========================================================

async def admin_birthday_info(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "🎂 *Birthday Commands*\n\n"
        "Members can use these commands:\n\n"
        "🎂 `/birthday`\n"
        "Enter or update a birthday.\n\n"
        "📅 `/mybirthday`\n"
        "View your saved birthday.\n\n"
        "🗑️ `/removebirthday`\n"
        "Remove your birthday.\n\n"
        "Birthday format:\n"
        "`MM/DD`\n\n"
        "Example:\n"
        "`08/26`",
        reply_markup=birthday_admin_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# VIEW ALL BIRTHDAYS
# ==========================================================

async def admin_birthdays(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    try:

        from raffle_database import get_all_birthdays

        birthdays = get_all_birthdays()

    except Exception:

        logger.exception(
            "Unable to retrieve birthdays"
        )

        await query.message.reply_text(
            "⚠️ Unable to load birthdays."
        )

        return

    if not birthdays:

        text = (
            "🎂 *Saved Birthdays*\n\n"
            "No birthdays are currently saved."
        )

    else:

        lines = [
            "🎂 *Saved Birthdays*\n"
        ]

        for record in birthdays:

            name = (
                record.get("display_name")
                or record.get("username")
                or str(record.get("user_id"))
            )

            birthday = record.get(
                "birthday",
                "Unknown",
            )

            lines.append(
                f"• {name} — {birthday}"
            )

        text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back to Admin Panel",
                    callback_data="admin_back",
                )
            ]
        ]
    )

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
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

    await show_admin_panel(
        update,
        context,
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

    await show_admin_panel(
        update,
        context,
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

    # ======================================================
    # MAIN
    # ======================================================

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

    # ======================================================
    # RAFFLE
    # ======================================================

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

    if data == "admin_reroll":

        await admin_reroll(
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

    # ======================================================
    # BIRTHDAY
    # ======================================================

    if data == "admin_birthday":

        await admin_birthday(
            update,
            context,
        )

        return

    if data == "admin_birthday_info":

        await admin_birthday_info(
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

    # ======================================================
    # UNKNOWN
    # ======================================================

    logger.warning(
        "Unknown admin callback: %s",
        data,
    )

    await query.answer(
        "⚠️ Unknown admin option.",
        show_alert=True,
    )
