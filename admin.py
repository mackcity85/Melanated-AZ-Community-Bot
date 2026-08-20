# ==========================================================
# Melanated AZ Bot
# admin.py
#
# Admin Control Panel
# ==========================================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_IDS


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ==========================================================
# ADMIN MENU
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ You are not authorized to access the Admin Control Panel."
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_startraffle",
                ),
                InlineKeyboardButton(
                    "📋 Pending",
                    callback_data="admin_pending",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_status",
                ),
                InlineKeyboardButton(
                    "👥 Entries",
                    callback_data="admin_entries",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎲 Draw Raffle",
                    callback_data="admin_draw",
                ),
                InlineKeyboardButton(
                    "🔄 Reroll",
                    callback_data="admin_reroll",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🛑 Cancel Raffle",
                    callback_data="admin_cancel",
                ),
                InlineKeyboardButton(
                    "🎁 Bonus Entry",
                    callback_data="admin_bonus",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Remove Entry",
                    callback_data="admin_remove",
                ),
            ],
        ]
    )

    await update.message.reply_text(
        "👑 **MELANATED AZ ADMIN CONTROL PANEL**\n\n"
        "Select an option below:",
        reply_markup=keyboard,
        parse_mode="Markdown",
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

    if not query.from_user:
        return

    if not is_admin(query.from_user.id):
        await query.answer(
            "❌ Not authorized.",
            show_alert=True,
        )
        return

    commands = {
        "admin_startraffle": (
            "🎟️ **Start Raffle**\n\n"
            "Use:\n"
            "`/startraffle Prize description`\n\n"
            "Example:\n"
            "`/startraffle $100 Cash Prize`"
        ),

        "admin_pending": (
            "📋 **Pending Entries**\n\n"
            "Use:\n"
            "`/pending`"
        ),

        "admin_status": (
            "📊 **Raffle Status**\n\n"
            "Use:\n"
            "`/rafflestatus`"
        ),

        "admin_entries": (
            "👥 **Approved Entries**\n\n"
            "Use:\n"
            "`/raffleentries`"
        ),

        "admin_draw": (
            "🎲 **Draw Raffle**\n\n"
            "Use:\n"
            "`/draw`\n\n"
            "⚠️ This closes the active raffle."
        ),

        "admin_reroll": (
            "🔄 **Reroll**\n\n"
            "Use:\n"
            "`/reroll`"
        ),

        "admin_cancel": (
            "🛑 **Cancel Raffle**\n\n"
            "Use:\n"
            "`/cancelraffle`"
        ),

        "admin_bonus": (
            "🎁 **Bonus Entry**\n\n"
            "Use:\n"
            "`/bonusentry`\n\n"
            "⚠️ Bonus entries are not currently implemented "
            "in the database."
        ),

        "admin_remove": (
            "🗑️ **Remove Entry**\n\n"
            "Use:\n"
            "`/removeentry ENTRY_ID`\n\n"
            "Example:\n"
            "`/removeentry 3`"
        ),
    }

    text = commands.get(query.data)

    if not text:
        text = "❌ Unknown admin option."

    await query.message.reply_text(
        text,
        parse_mode="Markdown",
    )
