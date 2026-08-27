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
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
)

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):
    try:
        return int(user_id) in [int(admin_id) for admin_id in ADMIN_IDS]
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
                    "🎟️ Raffle Management",
                    callback_data="admin_raffle",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎂 Birthday Management",
                    callback_data="admin_birthday",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_refresh",
                )
            ],
        ]
    )


# ==========================================================
# MAIN ADMIN MENU
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_admin(user.id):

        if update.effective_message:
            await update.effective_message.reply_text(
                "⛔ You are not authorized to use the admin panel."
            )

        return

    text = (
        "👑 *Melanated AZ Admin Panel*\n\n"
        "Welcome, Admin.\n\n"
        "Select a management area below."
    )

    keyboard = admin_main_keyboard()

    if update.callback_query:

        query = update.callback_query

        try:
            await query.answer()
        except Exception:
            pass

        try:
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        except Exception:
            if query.message:
                await query.message.reply_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )

        return

    if update.effective_message:

        await update.effective_message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


# ==========================================================
# RAFFLE MANAGEMENT KEYBOARD
# ==========================================================

def raffle_management_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle",
                ),
                InlineKeyboardButton(
                    "🎫 Active Raffle",
                    callback_data="admin_active_raffle",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Status",
                    callback_data="admin_status",
                ),
                InlineKeyboardButton(
                    "👥 Entries",
                    callback_data="admin_entries",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⏳ Pending Payments",
                    callback_data="admin_pending",
                ),
                InlineKeyboardButton(
                    "✅ Completed Payments",
                    callback_data="admin_completed",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏆 Draw Winner",
                    callback_data="admin_draw",
                ),
                InlineKeyboardButton(
                    "❌ Cancel Raffle",
                    callback_data="admin_cancel",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_raffle_refresh",
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


# ==========================================================
# SHOW RAFFLE MANAGEMENT
# ==========================================================

async def show_raffle_management(
    query,
    context,
):

    text = (
        "🎟️ *Raffle Management*\n\n"
        "Manage the Melanated AZ raffle from this menu.\n\n"
        "🎟️ *Start Raffle*\n"
        "Create and configure a new raffle.\n\n"
        "🎫 *Active Raffle*\n"
        "View the current raffle.\n\n"
        "📊 *Status*\n"
        "View the current raffle status.\n\n"
        "👥 *Entries*\n"
        "View approved raffle entries.\n\n"
        "⏳ *Pending Payments*\n"
        "Review entries waiting for payment verification.\n\n"
        "✅ *Completed Payments*\n"
        "View completed/approved payments.\n\n"
        "🏆 *Draw Winner*\n"
        "Draw the winner of the active raffle.\n\n"
        "❌ *Cancel Raffle*\n"
        "Cancel the active raffle."
    )

    try:

        await query.edit_message_text(
            text=text,
            reply_markup=raffle_management_keyboard(),
            parse_mode="Markdown",
        )

    except Exception as exc:

        logger.exception(
            "Unable to display raffle management menu: %s",
            exc,
        )

        if query.message:

            await query.message.reply_text(
                text=text,
                reply_markup=raffle_management_keyboard(),
                parse_mode="Markdown",
            )


# ==========================================================
# RUN RAFFLE FUNCTION
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

    except Exception as exc:

        logger.exception(
            "Error running raffle action %s: %s",
            action_name,
            exc,
        )

        query = update.callback_query

        if query and query.message:

            try:

                await query.message.reply_text(
                    f"⚠️ An error occurred while processing "
                    f"*{action_name}*.\n\n"
                    f"Please try again.\n\n"
                    f"Error: `{exc}`",
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

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        start_raffle,
        update,
        context,
        "Start Raffle",
    )


# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

async def admin_active_raffle(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Active Raffle",
    )


# ==========================================================
# STATUS
# ==========================================================

async def admin_status(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Status",
    )


# ==========================================================
# ENTRIES
# ==========================================================

async def admin_entries(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        raffle_entries,
        update,
        context,
        "Entries",
    )


# ==========================================================
# PENDING
# ==========================================================

async def admin_pending(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        pending_entries,
        update,
        context,
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

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        paid_entry,
        update,
        context,
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

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        draw_raffle,
        update,
        context,
        "Draw Winner",
    )


# ==========================================================
# CANCEL KEYBOARD
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
                    callback_data="admin_raffle",
                )
            ],
        ]
    )


# ==========================================================
# CANCEL
# ==========================================================

async def admin_cancel(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    await query.edit_message_text(
        "⚠️ *Cancel Active Raffle?*\n\n"
        "This will cancel the currently active raffle.\n\n"
        "Are you sure you want to continue?",
        reply_markup=cancel_confirmation_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# CONFIRM CANCEL
# ==========================================================

async def admin_confirm_cancel(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    await run_raffle_handler(
        cancel_raffle,
        update,
        context,
        "Cancel Raffle",
    )


# ==========================================================
# RAFFLE REFRESH
# ==========================================================

async def admin_raffle_refresh(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer("Raffle menu refreshed.")
    except Exception:
        pass

    await show_raffle_management(
        query,
        context,
    )


# ==========================================================
# MAIN REFRESH
# ==========================================================

async def admin_refresh(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer("Admin panel refreshed.")
    except Exception:
        pass

    await query.edit_message_text(
        "👑 *Melanated AZ Admin Panel*\n\n"
        "Welcome, Admin.\n\n"
        "Select a management area below.",
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

    try:
        await query.answer()
    except Exception:
        pass

    await query.edit_message_text(
        "👑 *Melanated AZ Admin Panel*\n\n"
        "Welcome, Admin.\n\n"
        "Select a management area below.",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# BIRTHDAY ADMIN MENU
# ==========================================================

async def admin_birthday(
    update,
    context,
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_back",
                )
            ]
        ]
    )

    await query.edit_message_text(
        "🎂 *Birthday Management*\n\n"
        "Birthday commands:\n\n"
        "🎂 `/birthday`\n"
        "Enter or update your birthday.\n\n"
        "📅 `/mybirthday`\n"
        "View your saved birthday.\n\n"
        "🗑️ `/removebirthday`\n"
        "Remove your saved birthday.",
        reply_markup=keyboard,
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

        try:
            await query.answer(
                "⛔ You are not authorized to use the admin panel.",
                show_alert=True,
            )
        except Exception:
            pass

        return

    data = query.data or ""

    logger.info(
        "Admin button pressed: %s by %s",
        data,
        user.id,
    )

    # ======================================================
    # MAIN MENU
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
    # RAFFLE MANAGEMENT
    # ======================================================

    if data == "admin_raffle":

        try:
            await query.answer()
        except Exception:
            pass

        await show_raffle_management(
            query,
            context,
        )

        return

    if data == "admin_start_raffle":

        await admin_start_raffle(
            update,
            context,
        )

        return

    if data == "admin_active_raffle":

        await admin_active_raffle(
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

    if data == "admin_raffle_refresh":

        await admin_raffle_refresh(
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

    # ======================================================
    # UNKNOWN
    # ======================================================

    logger.warning(
        "Unknown admin callback: %s",
        data,
    )

    try:

        await query.answer(
            "⚠️ This admin option is unavailable.",
            show_alert=True,
        )

    except Exception:
        pass
