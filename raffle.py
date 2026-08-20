# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Private paid raffle between friends
# ==========================================================

import logging
import random

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS,
    CASHAPP_TAG,
    CASHAPP_URL,
    ZELLE_PHONE,
)

from raffle_database import (
    create_raffle,
    get_active_raffle,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle,
)


logger = logging.getLogger(__name__)


# ==========================================================
# HELPERS
# ==========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_only(update: Update) -> bool:
    user = update.effective_user

    if not user:
        return False

    return is_admin(user.id)


def raffle_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 Pay with Cash App",
                    callback_data="raffle_paid",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 Pay with Zelle",
                    callback_data="raffle_zelle",
                )
            ],
        ]
    )


def admin_entry_keyboard(entry_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"approve_{entry_id}",
                ),
                InlineKeyboardButton(
                    "❌ Deny",
                    callback_data=f"deny_{entry_id}",
                ),
            ]
        ]
    )


def get_display_name(user) -> str:
    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):
        await update.message.reply_text(
            "❌ This command is for raffle admins only."
        )
        return

    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/startraffle Prize description\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize"
        )
        return

    existing = get_active_raffle()

    if existing:
        await update.message.reply_text(
            f"⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"🆔 Raffle #: {existing['id']}"
        )
        return

    prize = " ".join(context.args).strip()

    raffle_id = create_raffle(prize)

    message = (
        "🎟️ **PRIVATE FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {prize}\n"
        f"🆔 **Raffle #:** {raffle_id}\n\n"
        "This is a private raffle between friends.\n"
        "Entries require payment.\n\n"
        "Choose your payment method below.\n"
        "After payment, your entry will be sent to the admins "
        "for approval."
    )

    await update.message.reply_text(
        message,
        reply_markup=raffle_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.message.reply_text(
            "❌ There is no active raffle right now."
        )
        return

    await update.message.reply_text(
        "🎟️ **Enter the raffle**\n\n"
        f"🎁 Prize: {raffle['prize']}\n\n"
        "Entries are paid. Choose your payment method:",
        reply_markup=raffle_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# PAID ENTRY COMMAND
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    await update.message.reply_text(
        "💳 **Paid raffle entry**\n\n"
        f"🎁 Prize: {raffle['prize']}\n\n"
        "Select a payment method below:",
        reply_markup=raffle_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    raffle = get_active_raffle()

    if not raffle:
        await query.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    payment_method = (
        "Zelle"
        if query.data == "raffle_zelle"
        else "Cash App"
    )

    entry_id = add_raffle_entry(
        raffle_id=raffle["id"],
        user_id=user.id,
        username=user.username,
        display_name=get_display_name(user),
        payment_method=payment_method,
    )

    if entry_id is None:
        await query.message.reply_text(
            "⚠️ You already have a pending or approved entry "
            "for this raffle."
        )
        return

    # ------------------------------------------------------
    # Payment instructions
    # ------------------------------------------------------

    if payment_method == "Cash App":

        payment_text = (
            "💵 **Cash App**\n\n"
            f"Send payment to: `{CASHAPP_TAG}`\n"
        )

        if CASHAPP_URL:
            payment_text += (
                f"\n🔗 {CASHAPP_URL}\n"
            )

    else:

        payment_text = (
            "💳 **Zelle**\n\n"
            f"Send payment to: `{ZELLE_PHONE}`\n"
        )

    await query.message.reply_text(
        "🎟️ **Entry Created**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"🆔 Entry #: {entry_id}\n"
        f"💳 Method: {payment_method}\n\n"
        f"{payment_text}\n"
        "Once payment is sent, an admin will verify it "
        "and approve your entry.\n\n"
        "⚠️ Your entry is NOT active until approved.",
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # Notify admins
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **RAFFLE PAYMENT PENDING**\n\n"
                    f"🎁 Prize: {raffle['prize']}\n"
                    f"🆔 Entry #: {entry_id}\n"
                    f"👤 Name: {get_display_name(user)}\n"
                    f"🔹 User ID: `{user.id}`\n"
                    f"💳 Payment: {payment_method}\n\n"
                    "Verify the payment before approving."
                ),
                reply_markup=admin_entry_keyboard(entry_id),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin %s",
                admin_id,
            )


# ==========================================================
# ADMIN PAYMENT BUTTON
# ==========================================================

async def admin_payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    admin = query.from_user

    if not is_admin(admin.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )
        return

    data = query.data

    try:
        action, entry_text = data.split("_", 1)
        entry_id = int(entry_text)
    except (ValueError, AttributeError):

        await query.message.reply_text(
            "❌ Invalid raffle entry."
        )
        return

    entry = get_entry(entry_id)

    if not entry:

        await query.message.reply_text(
            "❌ Entry not found."
        )
        return

    if action == "approve":

        success = approve_entry(
            entry_id,
            admin.id,
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry could not be approved. "
                "It may already have been processed."
            )
            return

        await query.message.reply_text(
            f"✅ Entry #{entry_id} approved."
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!**\n\n"
                    f"🎁 Your entry for **{get_active_prize(entry['raffle_id'])}** "
                    "has been approved.\n\n"
                    f"🆔 Entry #: {entry_id}\n"
                    "Good luck! 🍀"
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify raffle participant."
            )

    elif action == "deny":

        success = deny_entry(
            entry_id,
            admin.id,
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry could not be denied. "
                "It may already have been processed."
            )
            return

        await query.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "❌ Your raffle entry was not approved.\n\n"
                    f"🆔 Entry #: {entry_id}\n"
                    "Please contact an admin if you believe this "
                    "was an error."
                ),
            )

        except Exception:

            logger.exception(
                "Unable to notify participant."
            )


# ==========================================================
# HELPER: ACTIVE PRIZE BY RAFFLE ID
# ==========================================================

def get_active_prize(raffle_id):

    raffle = get_active_raffle()

    if raffle and raffle["id"] == raffle_id:
        return raffle["prize"]

    return "raffle prize"


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    entries = get_pending_entries()

    if not entries:

        await update.message.reply_text(
            "✅ No pending raffle entries."
        )
        return

    for entry in entries:

        text = (
            "💰 **PENDING RAFFLE ENTRY**\n\n"
            f"🆔 Entry #: {entry['id']}\n"
            f"👤 User ID: {entry['user_id']}\n"
            f"💳 Payment: {entry['payment_method']}\n"
            f"🕐 Created: {entry['created_at']}"
        )

        await update.message.reply_text(
            text,
            reply_markup=admin_entry_keyboard(
                entry["id"]
            ),
            parse_mode="Markdown",
        )


# ==========================================================
# APPROVE ENTRY COMMAND
# ==========================================================

async def approve_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage: /approveentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(context.args[0])
    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )
        return

    success = approve_entry(
        entry_id,
        update.effective_user.id,
    )

    if success:

        await update.message.reply_text(
            f"✅ Entry #{entry_id} approved."
        )

    else:

        await update.message.reply_text(
            "❌ Entry could not be approved."
        )


# ==========================================================
# DENY ENTRY COMMAND
# ==========================================================

async def deny_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage: /denyentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(context.args[0])
    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )
        return

    success = deny_entry(
        entry_id,
        update.effective_user.id,
    )

    if success:

        await update.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )

    else:

        await update.message.reply_text(
            "❌ Entry could not be denied."
        )


# ==========================================================
# RAFFLE STATUS
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    entries = get_approved_entries(
        raffle["id"]
    )

    await update.message.reply_text(
        "🎟️ **RAFFLE STATUS**\n\n"
        f"🆔 Raffle #: {raffle['id']}\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"📌 Status: {raffle['status']}\n"
        f"👥 Approved Entries: {len(entries)}",
        parse_mode="Markdown",
    )


# ==========================================================
# RAFFLE ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    entries = get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await update.message.reply_text(
            "No approved entries yet."
        )
        return

    lines = [
        "🎟️ **APPROVED ENTRIES**",
        "",
    ]

    for entry in entries:

        name = (
            entry["display_name"]
            or entry["username"]
            or str(entry["user_id"])
        )

        lines.append(
            f"#{entry['id']} — {name}"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ==========================================================
# DRAW RAFFLE
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    entries = get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await update.message.reply_text(
            "❌ There are no approved paid entries."
        )
        return

    winner = random.choice(entries)

    close_raffle(
        raffle["id"]
    )

    name = (
        winner["display_name"]
        or winner["username"]
        or str(winner["user_id"])
    )

    await update.message.reply_text(
        "🎉🎉 **RAFFLE WINNER!** 🎉🎉\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n\n"
        f"🏆 Winner: **{name}**\n"
        f"🆔 Entry #: {winner['id']}\n\n"
        "Congratulations! 🍀",
        parse_mode="Markdown",
    )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    await update.message.reply_text(
        "⚠️ The previous raffle has already been closed.\n"
        "Use /startraffle to create a new raffle before rerolling."
    )


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    close_raffle(
        raffle["id"]
    )

    await update.message.reply_text(
        f"🛑 Raffle #{raffle['id']} cancelled."
    )


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    await update.message.reply_text(
        "ℹ️ Bonus entries are not enabled in this database version."
    )


# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage: /removeentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(context.args[0])
    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )
        return

    success = remove_entry(
        entry_id
    )

    if success:

        await update.message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )
