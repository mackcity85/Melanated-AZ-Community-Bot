# ==========================================================
# Melanated AZ Bot
# admin.py
# ==========================================================

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
    get_approved_entries,
)

from raffle import (
    start_raffle,
    cancel_raffle,
    draw_raffle,
)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ==========================================================
# ADMIN PANEL
# ==========================================================

def admin_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_raffle_status"
                ),
                InlineKeyboardButton(
                    "🎟️ Entries",
                    callback_data="admin_entries"
                )
            ],
            [
                InlineKeyboardButton(
                    "💰 Pending Payments",
                    callback_data="admin_pending"
                ),
                InlineKeyboardButton(
                    "✅ Approved Entries",
                    callback_data="admin_approved"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛑 Cancel Raffle",
                    callback_data="admin_cancel"
                ),
                InlineKeyboardButton(
                    "🏆 Draw Winner",
                    callback_data="admin_draw"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_refresh"
                )
            ]
        ]
    )


# ==========================================================
# /ADMIN
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    await show_admin_panel(
        update,
        context
    )


# ==========================================================
# SHOW PANEL
# ==========================================================

async def show_admin_panel(
    update,
    context
):

    text = (
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        "Choose an option below."
    )

    keyboard = admin_keyboard()

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# ==========================================================
# ADMIN BUTTONS
# ==========================================================

async def admin_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    action = query.data

    # ------------------------------------------------------
    # START
    # ------------------------------------------------------

    if action == "admin_start_raffle":

        context.user_data[
            "awaiting_raffle_setup"
        ] = True

        await query.message.reply_text(
            "🎟️ **START A NEW RAFFLE**\n\n"
            "Send:\n\n"
            "`Prize | Entry Price`\n\n"
            "Example:\n"
            "`$100 Cash Prize | $5`",
            parse_mode="Markdown"
        )

        return

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    if action == "admin_raffle_status":

        raffle = (
            get_active_raffle()
            or get_pending_raffle()
        )

        if not raffle:

            await query.edit_message_text(
                "❌ No active or pending raffle.",
                reply_markup=admin_keyboard()
            )

            return

        entries = get_approved_entries(
            raffle["id"]
        )

        await query.edit_message_text(
            "📊 **RAFFLE STATUS**\n\n"
            f"🆔 Raffle #: **{raffle['id']}**\n"
            f"🎁 Prize: **{raffle['prize']}**\n"
            f"💵 Entry Price: **{raffle['price']}**\n"
            f"📌 Status: **{raffle['status']}**\n"
            f"👥 Approved Entries: **{len(entries)}**",
            reply_markup=admin_keyboard(),
            parse_mode="Markdown"
        )

        return

    # ------------------------------------------------------
    # ENTRIES
    # ------------------------------------------------------

    if action == "admin_entries":

        raffle = get_active_raffle()

        if not raffle:

            await query.edit_message_text(
                "❌ No active raffle.",
                reply_markup=admin_keyboard()
            )

            return

        entries = get_approved_entries(
            raffle["id"]
        )

        if not entries:

            await query.edit_message_text(
                "🎟️ No approved entries yet.",
                reply_markup=admin_keyboard()
            )

            return

        lines = [
            "🎟️ **APPROVED ENTRIES**",
            ""
        ]

        for entry in entries:

            lines.append(
                f"#{entry['id']} — "
                f"{entry['display_name']}"
            )

        lines.append("")
        lines.append("Use 🔄 Refresh to return to the panel.")

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=admin_keyboard(),
            parse_mode="Markdown"
        )

        return

    # ------------------------------------------------------
    # PENDING
    # ------------------------------------------------------

    if action == "admin_pending":

        entries = get_pending_entries()

        if not entries:

            await query.edit_message_text(
                "✅ No pending payments.",
                reply_markup=admin_keyboard()
            )

            return

        lines = [
            "💰 **PENDING PAYMENTS**",
            ""
        ]

        for entry in entries:

            lines.append(
                f"#{entry['id']} — "
                f"{entry['display_name']} — "
                f"{entry['payment_method']}"
            )

        lines.append("")
        lines.append(
            "Use /pending for approval buttons."
        )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=admin_keyboard(),
            parse_mode="Markdown"
        )

        return

    # ------------------------------------------------------
    # APPROVED
    # ------------------------------------------------------

    if action == "admin_approved":

        raffle = get_active_raffle()

        if not raffle:

            await query.edit_message_text(
                "❌ No active raffle.",
                reply_markup=admin_keyboard()
            )

            return

        entries = get_approved_entries(
            raffle["id"]
        )

        if not entries:

            await query.edit_message_text(
                "✅ No approved entries yet.",
                reply_markup=admin_keyboard()
            )

            return

        lines = [
            "✅ **APPROVED ENTRIES**",
            ""
        ]

        for entry in entries:

            lines.append(
                f"#{entry['id']} — "
                f"{entry['display_name']}"
            )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=admin_keyboard(),
            parse_mode="Markdown"
        )

        return

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    if action == "admin_cancel":

        await cancel_raffle(
            update,
            context
        )

        await show_admin_panel(
            update,
            context
        )

        return

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

    if action == "admin_draw":

        await draw_raffle(
            update,
            context
        )

        await show_admin_panel(
            update,
            context
        )

        return

    # ------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------

    if action == "admin_refresh":

        await show_admin_panel(
            update,
            context
        )

        return
