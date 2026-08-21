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


def is_admin(user_id):

    return user_id in ADMIN_IDS


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

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎟️ Start Raffle",
                callback_data="admin_startraffle"
            )
        ],
        [
            InlineKeyboardButton(
                "⏳ Pending Entries",
                callback_data="admin_pending"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Raffle Status",
                callback_data="admin_status"
            )
        ],
        [
            InlineKeyboardButton(
                "👥 Approved Entries",
                callback_data="admin_entries"
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
                "🏆 Draw Winner",
                callback_data="admin_draw"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="admin_refresh"
            )
        ],
    ])

    await update.message.reply_text(
        "👑 **MELANATED AZ ADMIN PANEL**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


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

    if action == "admin_startraffle":

        await query.message.reply_text(
            "🎟️ **Start a Raffle**\n\n"
            "Use:\n"
            "`/startraffle PRICE PRIZE`\n\n"
            "Example:\n"
            "`/startraffle 10 $100 Cash Prize`\n\n"
            "The raffle will NOT be posted immediately.\n"
            "You will receive an approval prompt first.",
            parse_mode="Markdown"
        )

    elif action == "admin_pending":

        from raffle import pending_entries

        await pending_entries(
            update,
            context
        )

    elif action == "admin_status":

        from raffle import raffle_status

        await raffle_status(
            update,
            context
        )

    elif action == "admin_entries":

        from raffle import raffle_entries

        await raffle_entries(
            update,
            context
        )

    elif action == "admin_cancel":

        from raffle import cancel_raffle

        await cancel_raffle(
            update,
            context
        )

    elif action == "admin_draw":

        from raffle import draw_raffle

        await draw_raffle(
            update,
            context
        )

    elif action == "admin_refresh":

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_startraffle"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ Pending Entries",
                    callback_data="admin_pending"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_status"
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 Approved Entries",
                    callback_data="admin_entries"
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
                    "🏆 Draw Winner",
                    callback_data="admin_draw"
                ]
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_refresh"
                )
            ],
        ])

        await query.message.edit_reply_markup(
            reply_markup=keyboard
        )
