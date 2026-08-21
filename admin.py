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
    get_approved_entries,
)

from raffle import (
    pending_raffle,
)


def is_admin(user_id):

    return user_id in ADMIN_IDS


# ==========================================================
# ADMIN PANEL
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    await send_admin_panel(
        update,
        context
    )


async def send_admin_panel(
    update,
    context
):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎟️ Start Raffle",
                callback_data="admin_startraffle"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Raffle Status",
                callback_data="admin_status"
            ),
            InlineKeyboardButton(
                "👥 Entries",
                callback_data="admin_entries"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Pending Entries",
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

    markup = InlineKeyboardMarkup(
        keyboard
    )

    text = (
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        "🎟️ Raffle Management\n\n"
        "Choose an option below."
    )

    if hasattr(update, "message") and update.message:

        await update.message.reply_text(
            text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif hasattr(update, "callback_query"):

        await update.callback_query.edit_message_text(
            text,
            reply_markup=markup,
            parse_mode="Markdown"
        )


# ==========================================================
# ADMIN BUTTONS
# ==========================================================

async def admin_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )
        return

    action = query.data.replace(
        "admin_",
        ""
    )

    if action == "refresh":

        await send_admin_panel(
            update,
            context
        )
        return

    if action == "startraffle":

        await query.message.reply_text(
            "🎟️ **Start a Raffle**\n\n"
            "Send the command below with the prize "
            "and entry price:\n\n"
            "`/startraffle $100 Cash Prize | 10`\n\n"
            "Example:\n"
            "Prize: $100 Cash Prize\n"
            "Entry: $10",
            parse_mode="Markdown"
        )
        return

    if action == "status":

        raffle = get_active_raffle()

        if not raffle:

            await query.message.reply_text(
                "❌ No active raffle."
            )
            return

        entries = get_approved_entries(
            raffle["id"]
        )

        await query.message.reply_text(
            "📊 **RAFFLE STATUS**\n\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry: ${raffle['entry_price']:.2f}\n"
            f"👥 Approved: {len(entries)}\n"
            f"⏳ Expires: {raffle['expires_at']}",
            parse_mode="Markdown"
        )
        return

    if action == "entries":

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
                "No approved entries yet."
            )
            return

        text = "👥 **APPROVED ENTRIES**\n\n"

        for entry in entries:

            name = (
                entry["display_name"]
                or entry["username"]
                or str(entry["user_id"])
            )

            text += (
                f"#{entry['id']} — {name}\n"
            )

        await query.message.reply_text(
            text,
            parse_mode="Markdown"
        )
        return

    if action == "pending":

        await pending_raffle(
            update,
            context
        )
        return

    if action == "approved":

        raffle = get_active_raffle()

        if not raffle:

            await query.message.reply_text(
                "❌ No active raffle."
            )
            return

        entries = get_approved_entries(
            raffle["id"]
        )

        await query.message.reply_text(
            f"✅ Approved Entries: {len(entries)}"
        )

        for entry in entries:

            name = (
                entry["display_name"]
                or entry["username"]
                or str(entry["user_id"])
            )

            await query.message.reply_text(
                f"#{entry['id']} — {name}"
            )

        return

    if action == "cancel":

        await query.message.reply_text(
            "Use `/cancelraffle` to cancel the "
            "current raffle.",
            parse_mode="Markdown"
        )
        return

    if action == "draw":

        await query.message.reply_text(
            "Use `/draw` to draw the winner.",
            parse_mode="Markdown"
        )
        return
