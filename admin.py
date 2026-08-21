# ==========================================================
# Melanated AZ Bot
# admin.py
# ==========================================================

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config import ADMIN_IDS


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ==========================================================
# ADMIN MENU
# ==========================================================

async def admin_menu(update, context):

    user = update.effective_user

    if not user or not is_admin(user.id):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎟️ Raffle",
                    callback_data="admin_raffle"
                ),
                InlineKeyboardButton(
                    "📊 Status",
                    callback_data="admin_status"
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 Entries",
                    callback_data="admin_entries"
                )
            ],
            [
                InlineKeyboardButton(
                    "💰 Pending Payments",
                    callback_data="admin_pending"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Completed Payments",
                    callback_data="admin_completed"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏆 Draw Winner",
                    callback_data="admin_draw"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛑 Cancel Raffle",
                    callback_data="admin_cancel"
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

    await update.message.reply_text(
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        "🎟️ Raffle Management\n"
        "💰 Payment Management\n"
        "🏆 Winner Management",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ==========================================================
# ADMIN BUTTONS
# ==========================================================

async def admin_button(update, context):

    query = update.callback_query

    if not query:
        return

    user = query.from_user

    if not is_admin(user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    action = query.data.replace(
        "admin_",
        ""
    )

    # ------------------------------------------------------
    # START
    # ------------------------------------------------------

    if action == "start_raffle":

        await query.message.reply_text(
            "🎟️ **START A RAFFLE**\n\n"
            "Use:\n\n"
            "`/startraffle PRIZE | ENTRY PRICE`\n\n"
            "Example:\n"
            "`/startraffle $100 Cash Prize | 10`",
            parse_mode="Markdown"
        )

    # ------------------------------------------------------
    # RAFFLE
    # ------------------------------------------------------

    elif action == "raffle":

        from raffle_database import get_active_raffle

        raffle = get_active_raffle()

        if not raffle:

            await query.message.reply_text(
                "❌ No active raffle."
            )

            return

        await query.message.reply_text(
            "🎟️ **ACTIVE RAFFLE**\n\n"
            f"🆔 Raffle #: {raffle['id']}\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry: ${raffle['entry_price']}\n"
            f"📌 Status: {raffle['status']}",
            parse_mode="Markdown"
        )

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    elif action == "status":

        from raffle import raffle_status

        await raffle_status(
            update,
            context
        )

    # ------------------------------------------------------
    # ENTRIES
    # ------------------------------------------------------

    elif action == "entries":

        from raffle import raffle_entries

        await raffle_entries(
            update,
            context
        )

    # ------------------------------------------------------
    # PENDING
    # ------------------------------------------------------

    elif action == "pending":

        from raffle import pending_entries

        await pending_entries(
            update,
            context
        )

    # ------------------------------------------------------
    # COMPLETED
    # ------------------------------------------------------

    elif action == "completed":

        from raffle_database import (
            get_active_raffle,
            get_approved_entries
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
            ""
        ]

        for entry in entries:

            lines.append(
                f"#{entry['id']} — "
                f"{entry['display_name']} — "
                f"{entry['payment_method']}"
            )

        await query.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown"
        )

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

    elif action == "draw":

        from raffle import draw_raffle

        await draw_raffle(
            update,
            context
        )

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    elif action == "cancel":

        from raffle import cancel_raffle

        await cancel_raffle(
            update,
            context
        )

    # ------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------

    elif action == "refresh":

        from raffle import refresh_raffle

        await refresh_raffle(
            update,
            context
        )
