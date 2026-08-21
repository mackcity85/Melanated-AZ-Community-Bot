# ==========================================================
# Melanated AZ Bot
# admin.py
#
# Full Admin Control Panel
# ==========================================================

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from config import ADMIN_IDS


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ==========================================================
# MAIN ADMIN MENU
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    await send_admin_menu(
        update,
        context,
    )


# ==========================================================
# ADMIN MENU DISPLAY
# ==========================================================

async def send_admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    edit=False,
):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle",
                ),
                InlineKeyboardButton(
                    "🎟️ Raffle",
                    callback_data="admin_raffle",
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
                    "💰 Pending Payments",
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
                    callback_data="admin_refresh",
                ),
            ],
        ]
    )

    text = (
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        "🎟️ Raffle Management\n"
        "💰 Payment Management\n"
        "🏆 Winner Management\n\n"
        "Select an option:"
    )

    if edit:

        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=keyboard,
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

    if not is_admin(query.from_user.id):

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

    if data == "admin_start_raffle":

        await query.edit_message_text(
            "🎟️ **START A RAFFLE**\n\n"
            "Use:\n\n"
            "`/startraffle PRIZE | ENTRY PRICE`\n\n"
            "Example:\n"
            "`/startraffle $100 Cash Prize | $10 Entry`\n\n"
            "The raffle will be created as **pending approval**.\n\n"
            "Once an admin approves it, the bot will post "
            "the private Melanated AZ Friends Raffle and "
            "start the 7-day countdown.",
            parse_mode="Markdown",
        )
        return

    # ======================================================
    # RAFFLE
    # ======================================================

    if data == "admin_raffle":

        from raffle_database import get_active_raffle

        raffle = get_active_raffle()

        if not raffle:

            await query.edit_message_text(
                "🎟️ **RAFFLE**\n\n"
                "❌ There is no active raffle.",
                reply_markup=back_keyboard(),
                parse_mode="Markdown",
            )
            return

        await query.edit_message_text(
            "🎟️ **ACTIVE RAFFLE**\n\n"
            f"🆔 Raffle #: {raffle['id']}\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"📌 Status: {raffle['status']}\n\n"
            "Use the buttons below to manage it.",
            reply_markup=raffle_controls_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # STATUS
    # ======================================================

    if data == "admin_status":

        from raffle import raffle_status

        await query.message.reply_text(
            "📊 Checking raffle status..."
        )

        await raffle_status(
            update,
            context,
        )

        return

    # ======================================================
    # ENTRIES
    # ======================================================

    if data == "admin_entries":

        from raffle import raffle_entries

        await query.message.reply_text(
            "👥 Loading approved entries..."
        )

        await raffle_entries(
            update,
            context,
        )

        return

    # ======================================================
    # PENDING PAYMENTS
    # ======================================================

    if data == "admin_pending":

        from raffle import pending_entries

        await query.message.reply_text(
            "💰 **PENDING PAYMENTS**\n\n"
            "Loading pending entries...",
            parse_mode="Markdown",
        )

        await pending_entries(
            update,
            context,
        )

        return

    # ======================================================
    # COMPLETED PAYMENTS
    # ======================================================

    if data == "admin_completed":

        from raffle_database import (
            get_active_raffle,
            get_approved_entries,
        )

        raffle = get_active_raffle()

        if not raffle:

            await query.message.reply_text(
                "❌ No active raffle."
            )
            return

        entries = get_approved_entries(
            raffle["id"]
        )

        if not entries:

            await query.message.reply_text(
                "✅ No completed payments yet."
            )
            return

        lines = [
            "✅ **COMPLETED PAYMENTS**",
            "",
        ]

        for entry in entries:

            name = (
                entry["display_name"]
                or entry["username"]
                or str(entry["user_id"])
            )

            lines.append(
                f"#{entry['id']} — {name} — "
                f"{entry['payment_method']}"
            )

        await query.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # DRAW WINNER
    # ======================================================

    if data == "admin_draw":

        from raffle_database import get_active_raffle

        raffle = get_active_raffle()

        if not raffle:

            await query.message.reply_text(
                "❌ There is no active raffle to draw."
            )
            return

        await query.message.reply_text(
            "🏆 **DRAW WINNER**\n\n"
            f"🎁 Prize: {raffle['prize']}\n\n"
            "Use `/draw` to select the winner.",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # CANCEL
    # ======================================================

    if data == "admin_cancel":

        from raffle_database import get_active_raffle

        raffle = get_active_raffle()

        if not raffle:

            await query.message.reply_text(
                "❌ No active raffle to cancel."
            )
            return

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⚠️ YES, CANCEL",
                        callback_data="admin_confirm_cancel",
                    ),
                    InlineKeyboardButton(
                        "🔙 NO",
                        callback_data="admin_refresh",
                    ),
                ]
            ]
        )

        await query.edit_message_text(
            "⚠️ **CANCEL RAFFLE?**\n\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"🆔 Raffle #: {raffle['id']}\n\n"
            "This will close the active raffle.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # CONFIRM CANCEL
    # ======================================================

    if data == "admin_confirm_cancel":

        from raffle_database import (
            get_active_raffle,
            close_raffle,
        )

        raffle = get_active_raffle()

        if not raffle:

            await query.edit_message_text(
                "❌ No active raffle.",
                reply_markup=back_keyboard(),
            )
            return

        close_raffle(
            raffle["id"]
        )

        await query.edit_message_text(
            f"🛑 **RAFFLE CANCELLED**\n\n"
            f"Raffle #: {raffle['id']}\n"
            f"Prize: {raffle['prize']}",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # REFRESH
    # ======================================================

    if data == "admin_refresh":

        await send_admin_menu(
            update,
            context,
            edit=True,
        )

        return


# ==========================================================
# RAFFLE CONTROLS
# ==========================================================

def raffle_controls_keyboard():

    return InlineKeyboardMarkup(
        [
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
                    "💰 Pending",
                    callback_data="admin_pending",
                ),
                InlineKeyboardButton(
                    "✅ Completed",
                    callback_data="admin_completed",
                ),
            ],
            [
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
                    "🔄 Refresh",
                    callback_data="admin_refresh",
                ),
            ],
        ]
    )


# ==========================================================
# BACK BUTTON
# ==========================================================

def back_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 Admin Menu",
                    callback_data="admin_refresh",
                )
            ]
        ]
    )
