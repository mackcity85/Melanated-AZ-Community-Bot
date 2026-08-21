# ==========================================================
# Melanated AZ Bot
# admin.py
#
# Admin menu and raffle controls
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
            "❌ Admins only."
        )

        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Raffle",
                    callback_data="admin_raffle",
                )
            ],
            [
                InlineKeyboardButton(
                    "💰 Pending Entries",
                    callback_data="admin_pending",
                ),
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_status",
                ),
            ],
            [
                InlineKeyboardButton(
                    "👥 Approved Entries",
                    callback_data="admin_entries",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel Raffle",
                    callback_data="admin_cancel",
                ),
            ],
        ]
    )

    await update.message.reply_text(
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
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

    if not is_admin(query.from_user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    data = query.data

    # ------------------------------------------------------
    # RAFFLE MENU
    # ------------------------------------------------------

    if data == "admin_raffle":

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎟️ Start Raffle",
                        callback_data="admin_start_raffle",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "💰 Pending Entries",
                        callback_data="admin_pending",
                    ),
                    InlineKeyboardButton(
                        "📊 Status",
                        callback_data="admin_status",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "👥 Entries",
                        callback_data="admin_entries",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="admin_back",
                    )
                ],
            ]
        )

        await query.edit_message_text(
            "🎟️ **RAFFLE ADMIN**\n\n"
            "Raffles are private and require admin approval "
            "before they are posted.\n\n"
            "Each approved raffle automatically runs for "
            "**7 days**.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # START RAFFLE
    # ------------------------------------------------------

    if data == "admin_start_raffle":

        await query.edit_message_text(
            "🎟️ **START A RAFFLE**\n\n"
            "Use the command:\n\n"
            "`/startraffle PRIZE | ENTRY PRICE`\n\n"
            "Example:\n"
            "`/startraffle $100 Cash Prize | $10 Entry`\n\n"
            "An admin must approve the raffle before it "
            "is posted.\n\n"
            "⏳ The 7-day countdown starts when approved.",
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # PENDING ENTRIES
    # ------------------------------------------------------

    if data == "admin_pending":

        from raffle import pending_entries

        await query.message.reply_text(
            "💰 Checking pending raffle entries..."
        )

        await pending_entries(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # APPROVED ENTRIES
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    if data == "admin_cancel":

        from raffle import cancel_raffle

        await query.message.reply_text(
            "🛑 Cancelling raffle..."
        )

        await cancel_raffle(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # BACK
    # ------------------------------------------------------

    if data == "admin_back":

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎟️ Raffle",
                        callback_data="admin_raffle",
                    )
                ],
            ]
        )

        await query.edit_message_text(
            "👑 **MELANATED AZ ADMIN PANEL**\n\n"
            "Select an option below:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return
