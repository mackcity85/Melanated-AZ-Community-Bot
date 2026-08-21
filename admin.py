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
    get_entry_counts,
)

from raffle import (
    raffle_status,
    raffle_entries,
    pending_entries,
    start_raffle,
    draw_raffle,
    cancel_raffle,
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
                    callback_data="admin_startraffle",
                ),
                InlineKeyboardButton(
                    "📋 Raffle",
                    callback_data="admin_raffle",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⏳ Pending Entries",
                    callback_data="admin_pending",
                ),
                InlineKeyboardButton(
                    "💰 Payments",
                    callback_data="admin_payments",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_status",
                ),
                InlineKeyboardButton(
                    "✅ Approved Entries",
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

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    raffle = get_active_raffle()

    pending = get_pending_raffle()

    if raffle:

        counts = get_entry_counts(
            raffle["id"]
        )

        status = (
            "🟢 ACTIVE\n\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry: ${raffle['entry_price']:.2f}\n"
            f"⏳ Pending: {counts['pending']}\n"
            f"✅ Approved: {counts['approved']}"
        )

    elif pending:

        status = (
            "🟡 WAITING FOR APPROVAL\n\n"
            f"🎁 Prize: {pending['prize']}\n"
            f"💵 Entry: ${pending['entry_price']:.2f}\n"
            f"🆔 Raffle #: {pending['id']}"
        )

    else:

        status = (
            "⚪ No active raffle."
        )

    await update.message.reply_text(
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        f"{status}\n\n"
        "Choose an option:",
        reply_markup=admin_keyboard(),
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

    if not is_admin(query.from_user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    action = query.data

    # ------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------

    if action == "admin_refresh":

        raffle = get_active_raffle()

        pending = get_pending_raffle()

        if raffle:

            counts = get_entry_counts(
                raffle["id"]
            )

            status = (
                "🟢 ACTIVE\n\n"
                f"🎁 Prize: {raffle['prize']}\n"
                f"💵 Entry: ${raffle['entry_price']:.2f}\n"
                f"⏳ Pending: {counts['pending']}\n"
                f"✅ Approved: {counts['approved']}"
            )

        elif pending:

            status = (
                "🟡 WAITING FOR APPROVAL\n\n"
                f"🎁 Prize: {pending['prize']}\n"
                f"💵 Entry: ${pending['entry_price']:.2f}\n"
                f"🆔 Raffle #: {pending['id']}"
            )

        else:

            status = "⚪ No active raffle."

        await query.edit_message_text(
            "👑 **MELANATED AZ ADMIN PANEL**\n\n"
            f"{status}\n\n"
            "Choose an option:",
            reply_markup=admin_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # START RAFFLE
    # ------------------------------------------------------

    if action == "admin_startraffle":

        await query.message.reply_text(
            "🎟️ **START A RAFFLE**\n\n"
            "Use:\n"
            "`/startraffle PRIZE | PRICE`\n\n"
            "Example:\n"
            "`/startraffle $100 Cash Prize | 10`\n\n"
            "The raffle will be created and sent "
            "for admin approval before it is posted.",
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # RAFFLE
    # ------------------------------------------------------

    if action == "admin_raffle":

        raffle = get_active_raffle()

        pending = get_pending_raffle()

        if raffle:

            await query.message.reply_text(
                "🎟️ **ACTIVE RAFFLE**\n\n"
                f"🎁 Prize: {raffle['prize']}\n"
                f"💵 Entry: ${raffle['entry_price']:.2f}\n"
                f"🆔 Raffle #: {raffle['id']}",
                parse_mode="Markdown",
            )

        elif pending:

            await query.message.reply_text(
                "🟡 **RAFFLE WAITING FOR APPROVAL**\n\n"
                f"🎁 Prize: {pending['prize']}\n"
                f"💵 Entry: ${pending['entry_price']:.2f}\n"
                f"🆔 Raffle #: {pending['id']}",
                parse_mode="Markdown",
            )

        else:

            await query.message.reply_text(
                "⚪ No raffle currently exists."
            )

        return

    # ------------------------------------------------------
    # PENDING ENTRIES
    # ------------------------------------------------------

    if action == "admin_pending":

        await pending_entries(
            update,
            context
        )

        return

    # ------------------------------------------------------
    # PAYMENTS
    # ------------------------------------------------------

    if action == "admin_payments":

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⏳ Pending Payments",
                        callback_data="admin_pending",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✅ Completed Payments",
                        callback_data="admin_completed",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin_refresh",
                    )
                ],
            ]
        )

        await query.message.reply_text(
            "💰 **RAFFLE PAYMENTS**\n\n"
            "Choose an option:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # COMPLETED PAYMENTS
    # ------------------------------------------------------

    if action == "admin_completed":

        raffle = get_active_raffle()

        if not raffle:

            await query.message.reply_text(
                "❌ No active raffle."
            )

            return

        entries = __import__(
            "raffle_database"
        ).get_approved_entries(
            raffle["id"]
        )

        if not entries:

            await query.message.reply_text(
                "No completed payments yet."
            )

            return

        lines = [
            "✅ **COMPLETED PAYMENTS**",
            ""
        ]

        for entry in entries:

            name = (
                entry["display_name"]
                or entry["username"]
                or str(entry["user_id"])
            )

            lines.append(
                f"#{entry['id']} — {name} — "
                f"{entry['payment_method']} — "
                f"${entry['entry_price']:.2f}"
            )

        await query.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    if action == "admin_status":

        await raffle_status(
            update,
            context
        )

        return

    # ------------------------------------------------------
    # APPROVED ENTRIES
    # ------------------------------------------------------

    if action == "admin_entries":

        await raffle_entries(
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

        return

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    if action == "admin_cancel":

        await cancel_raffle(
            update,
            context
        )

        return
