# ==========================================================
# Melanated AZ Bot
# admin.py
# ==========================================================

import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from config import ADMIN_IDS

from raffle_database import (
    get_active_raffle,
    get_pending_raffle,
    get_pending_entries,
)


logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id: int) -> bool:

    return user_id in ADMIN_IDS


# ==========================================================
# ADMIN MENU KEYBOARD
# ==========================================================

def admin_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_startraffle",
                ),
                InlineKeyboardButton(
                    "📋 Raffle Status",
                    callback_data="admin_rafflestatus",
                ),
            ],
            [
                InlineKeyboardButton(
                    "💰 Pending Payments",
                    callback_data="admin_pending",
                ),
                InlineKeyboardButton(
                    "👥 Entries",
                    callback_data="admin_entries",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎲 Draw Winner",
                    callback_data="admin_draw",
                ),
                InlineKeyboardButton(
                    "🛑 Cancel Raffle",
                    callback_data="admin_cancel",
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
# ADMIN MENU
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_admin(user.id):

        if update.message:

            await update.message.reply_text(
                "❌ Admins only."
            )

        return

    active = get_active_raffle()
    pending = get_pending_raffle()
    pending_entries = get_pending_entries()

    # ------------------------------------------------------
    # Determine raffle status
    # ------------------------------------------------------

    if active:

        raffle_status = (
            "🟢 **ACTIVE RAFFLE**\n\n"
            f"🎁 Prize: {active['prize']}\n"
            f"💵 Entry: {active['entry_price']}\n"
            f"🆔 Raffle #: {active['id']}"
        )

    elif pending:

        raffle_status = (
            "🟡 **RAFFLE AWAITING APPROVAL**\n\n"
            f"🎁 Prize: {pending['prize']}\n"
            f"💵 Entry: {pending['entry_price']}\n"
            f"🆔 Raffle #: {pending['id']}\n\n"
            "Check your admin messages to approve or cancel it."
        )

    else:

        raffle_status = (
            "⚪ **NO ACTIVE RAFFLE**\n\n"
            "Use Start Raffle to create one."
        )

    # ------------------------------------------------------
    # Menu
    # ------------------------------------------------------

    text = (
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        f"{raffle_status}\n\n"
        f"💰 Pending Payments: {len(pending_entries)}"
    )

    if update.message:

        await update.message.reply_text(
            text,
            reply_markup=admin_keyboard(),
            parse_mode="Markdown",
        )


# ==========================================================
# ADMIN BUTTON HANDLER
# ==========================================================

async def admin_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = query.from_user

    if not user or not is_admin(user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    data = query.data

    # ======================================================
    # START RAFFLE
    # ======================================================

    if data == "admin_startraffle":

        await query.message.reply_text(
            "🎟️ **START A NEW RAFFLE**\n\n"
            "Use the following command:\n\n"
            "`/startraffle PRIZE | ENTRY PRICE`\n\n"
            "Example:\n"
            "`/startraffle $100 Cash Prize | $10 Entry`\n\n"
            "The raffle will be sent to the admins "
            "for approval before it is posted.",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # STATUS
    # ======================================================

    if data == "admin_rafflestatus":

        active = get_active_raffle()
        pending = get_pending_raffle()

        if active:

            await query.message.reply_text(
                "🟢 **ACTIVE RAFFLE**\n\n"
                f"🎁 Prize: {active['prize']}\n"
                f"💵 Entry: {active['entry_price']}\n"
                f"🆔 Raffle #: {active['id']}\n"
                f"📌 Status: {active['status']}",
                parse_mode="Markdown",
            )

        elif pending:

            await query.message.reply_text(
                "🟡 **RAFFLE AWAITING APPROVAL**\n\n"
                f"🎁 Prize: {pending['prize']}\n"
                f"💵 Entry: {pending['entry_price']}\n"
                f"🆔 Raffle #: {pending['id']}\n\n"
                "Use the approval buttons sent to the admins.",
                parse_mode="Markdown",
            )

        else:

            await query.message.reply_text(
                "⚪ There is no active raffle."
            )

        return

    # ======================================================
    # PENDING PAYMENTS
    # ======================================================

    if data == "admin_pending":

        entries = get_pending_entries()

        if not entries:

            await query.message.reply_text(
                "✅ There are no pending raffle payments."
            )

            return

        await query.message.reply_text(
            f"💰 **PENDING PAYMENTS**\n\n"
            f"There are **{len(entries)}** pending entries.\n\n"
            "Use `/pending` to view each payment "
            "and approve or deny it.",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # ENTRIES
    # ======================================================

    if data == "admin_entries":

        active = get_active_raffle()

        if not active:

            await query.message.reply_text(
                "❌ There is no active raffle."
            )

            return

        await query.message.reply_text(
            "👥 **RAFFLE ENTRIES**\n\n"
            "Use `/raffleentries` to view all approved entries.",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # DRAW
    # ======================================================

    if data == "admin_draw":

        active = get_active_raffle()

        if not active:

            await query.message.reply_text(
                "❌ There is no active raffle to draw."
            )

            return

        await query.message.reply_text(
            "🎲 **DRAW WINNER**\n\n"
            f"🎁 Prize: {active['prize']}\n"
            f"💵 Entry: {active['entry_price']}\n\n"
            "When you're ready, use:\n"
            "`/draw`",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # CANCEL
    # ======================================================

    if data == "admin_cancel":

        active = get_active_raffle()
        pending = get_pending_raffle()

        raffle = active or pending

        if not raffle:

            await query.message.reply_text(
                "❌ There is no active or pending raffle."
            )

            return

        await query.message.reply_text(
            "🛑 **CANCEL RAFFLE**\n\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry: {raffle['entry_price']}\n"
            f"🆔 Raffle #: {raffle['id']}\n\n"
            "Use:\n"
            "`/cancelraffle`",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # REFRESH
    # ======================================================

    if data == "admin_refresh":

        active = get_active_raffle()
        pending = get_pending_raffle()
        entries = get_pending_entries()

        if active:

            status = (
                "🟢 **ACTIVE RAFFLE**\n\n"
                f"🎁 Prize: {active['prize']}\n"
                f"💵 Entry: {active['entry_price']}\n"
                f"🆔 Raffle #: {active['id']}"
            )

        elif pending:

            status = (
                "🟡 **AWAITING APPROVAL**\n\n"
                f"🎁 Prize: {pending['prize']}\n"
                f"💵 Entry: {pending['entry_price']}\n"
                f"🆔 Raffle #: {pending['id']}"
            )

        else:

            status = (
                "⚪ **NO ACTIVE RAFFLE**"
            )

        await query.message.reply_text(
            "👑 **MELANATED AZ ADMIN PANEL**\n\n"
            f"{status}\n\n"
            f"💰 Pending Payments: {len(entries)}",
            reply_markup=admin_keyboard(),
            parse_mode="Markdown",
        )

        return
