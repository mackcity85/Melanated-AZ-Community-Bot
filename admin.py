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


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):
    """Return True when the Telegram user is an authorized admin."""

    try:
        return int(user_id) in [
            int(admin_id)
            for admin_id in ADMIN_IDS
        ]
    except (TypeError, ValueError):
        return False


# ==========================================================
# MAIN ADMIN MENU
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
        "👑 **Melanated AZ Admin Panel**\n\n"
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
# RAFFLE MANAGEMENT MENU
# ==========================================================

def raffle_management_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle",
                )
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


async def show_raffle_management(
    query,
    context,
):

    if not query:
        return

    text = (
        "🎟️ **Raffle Management**\n\n"
        "Use the buttons below to manage the "
        "Melanated AZ raffle.\n\n"
        "🎟️ **Start Raffle** — Create a new raffle\n"
        "📊 **Status** — View raffle status\n"
        "👥 **Entries** — View approved entries\n"
        "⏳ **Pending Payments** — Review pending entries\n"
        "✅ **Completed Payments** — View completed entries\n"
        "🏆 **Draw Winner** — Select a winner\n"
        "❌ **Cancel Raffle** — Cancel the active raffle"
    )

    try:

        await query.edit_message_text(
            text=text,
            reply_markup=raffle_management_keyboard(),
            parse_mode="Markdown",
        )

    except Exception as exc:

        logger.warning(
            "Could not edit raffle management message: %s",
            exc,
        )

        if query.message:

            await query.message.reply_text(
                text=text,
                reply_markup=raffle_management_keyboard(),
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
            "Error running admin raffle action: %s",
            action_name,
        )

        query = update.callback_query

        if query and query.message:

            try:

                await query.message.reply_text(
                    "⚠️ An error occurred while processing "
                    f"the **{action_name}** request.\n\n"
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
# STATUS
# ==========================================================

async def admin_status(
    update,
    context,
):

    query = update.callback_query

    if query:

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

    if query:

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
# PENDING PAYMENTS
# ==========================================================

async def admin_pending(
    update,
    context,
):

    query = update.callback_query

    if query:

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
# COMPLETED PAYMENTS
# ==========================================================

async def admin_completed(
    update,
    context,
):

    query = update.callback_query

    if query:

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
# DRAW WINNER
# ==========================================================

async def admin_draw(
    update,
    context,
):

    query = update.callback_query

    if query:

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
                    callback_data="admin_raffle",
                )
            ],
        ]
    )


async def admin_cancel(
    update,
    context,
):

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

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

    if query:

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
# REFRESH MAIN ADMIN MENU
# ==========================================================

async def admin_refresh(
    update,
    context,
):

    query = update.callback_query

    if query:

        try:
            await query.answer(
                "Admin panel refreshed."
            )
        except Exception:
            pass

        await query.edit_message_text(
            "👑 **Melanated AZ Admin Panel**\n\n"
            "Select a management area below.",
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown",
        )


# ==========================================================
# REFRESH RAFFLE MENU
# ==========================================================

async def admin_raffle_refresh(
    update,
    context,
):

    query = update.callback_query

    if query:

        try:
            await query.answer(
                "Raffle management refreshed."
            )
        except Exception:
            pass

        await show_raffle_management(
            query,
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

    if query:

        try:
            await query.answer()
        except Exception:
            pass

        await query.edit_message_text(
            "👑 **Melanated AZ Admin Panel**\n\n"
            "Welcome, Admin.\n\n"
            "Select a management area below.",
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
            "⛔ You are not authorized to use the admin panel.",
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
    #
    # IMPORTANT:
    # Do NOT call enter_raffle() here.
    # This button is only for opening the admin menu.
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

    if data == "admin_raffle_refresh":

        await admin_raffle_refresh(
            update,
            context,
        )

        return

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

    # ======================================================
    # BIRTHDAY MANAGEMENT
    # ======================================================

    if data == "admin_birthday":

        try:
            await query.answer()
        except Exception:
            pass

        await query.edit_message_text(
            "🎂 **Birthday Management**\n\n"
            "Members can manage their birthdays using:\n\n"
            "`/birthday`\n"
            "`/birthday MM/DD`\n"
            "`/mybirthday`\n"
            "`/removebirthday`\n\n"
            "The birthday is saved separately for each "
            "member and chat.",
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

    # ======================================================
    # UNKNOWN ADMIN BUTTON
    # ======================================================

    logger.warning(
        "Unknown admin callback: %s",
        data,
    )

    await query.answer(
        "⚠️ This admin option is unavailable.",
        show_alert=True,
    )
