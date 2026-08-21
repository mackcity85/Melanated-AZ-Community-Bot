# ==========================================================
# Melanated AZ Bot
# raffle.py
# ==========================================================

import logging
import random
from datetime import datetime

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
    get_pending_raffle,
    get_raffle,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle,
    expire_raffle,
    approve_raffle,
)

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN
# ==========================================================

def is_admin(user_id):
    return user_id in ADMIN_IDS


def admin_only(update):

    user = update.effective_user

    if not user:
        return False

    return is_admin(user.id)


# ==========================================================
# FORMATTING
# ==========================================================

def money(value):

    try:
        value = float(value)

        if value.is_integer():
            return f"${int(value)}"

        return f"${value:.2f}"

    except Exception:
        return str(value)


def countdown(expires_at):

    if not expires_at:
        return "Expiration not set"

    try:
        expiration = datetime.fromisoformat(expires_at)
        now = datetime.utcnow()

        remaining = expiration - now

        if remaining.total_seconds() <= 0:
            return "EXPIRED"

        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60

        return f"{days}d {hours}h {minutes}m"

    except Exception:
        return "Expiration unavailable"


def display_name(user):

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


# ==========================================================
# MEMBER KEYBOARD
# ==========================================================

def raffle_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎟️ Enter Raffle",
                callback_data="raffle_enter"
            )
        ]
    ])


def payment_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💵 Pay with Cash App",
                callback_data="raffle_paid"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Pay with Zelle",
                callback_data="raffle_zelle"
            )
        ]
    ])


# ==========================================================
# ADMIN ENTRY KEYBOARD
# ==========================================================

def admin_entry_keyboard(entry_id):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve_{entry_id}"
            ),
            InlineKeyboardButton(
                "❌ Deny",
                callback_data=f"deny_{entry_id}"
            )
        ]
    ])


# ==========================================================
# RAFFLE POST
# ==========================================================

def raffle_post(raffle):

    return (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        "🔒 **PRIVATE RAFFLE — FRIENDS ONLY**\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {money(raffle['price'])}\n\n"
        "⏳ **Time Remaining:**\n"
        f"**{countdown(raffle['expires_at'])}**\n\n"
        "Click **🎟️ Enter Raffle** below to enter.\n\n"
        "Payment is required for an entry to be approved.\n"
        "Your entry is not active until an admin verifies "
        "your payment."
    )


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(update, context):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n\n"
            "/startraffle PRICE PRIZE\n\n"
            "Example:\n"
            "/startraffle 10 $100 Cash Prize"
        )

        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ You must provide both the entry price "
            "and the prize.\n\n"
            "Example:\n"
            "/startraffle 10 $100 Cash Prize"
        )

        return

    existing = get_active_raffle()

    if existing:

        await update.message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"💵 Entry: {money(existing['price'])}\n"
            f"🆔 Raffle #: {existing['id']}\n"
            f"⏳ Remaining: {countdown(existing['expires_at'])}"
        )

        return

    try:
        price = float(context.args[0])
    except ValueError:

        await update.message.reply_text(
            "❌ Price must be a number.\n\n"
            "Example:\n"
            "/startraffle 10 $100 Cash Prize"
        )

        return

    prize = " ".join(context.args[1:])

    raffle_id = create_raffle(
        prize,
        price
    )

    raffle = get_raffle(raffle_id)

    # ------------------------------------------------------
    # Admin approval message
    # ------------------------------------------------------

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Approve & Post Raffle",
                callback_data=f"raffleapprove_{raffle_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"raffalecancel_{raffle_id}"
            )
        ]
    ])

    await update.message.reply_text(
        "🎟️ **RAFFLE CREATED — AWAITING APPROVAL**\n\n"
        f"🆔 Raffle #: {raffle_id}\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry Price: {money(price)}\n\n"
        "The raffle has NOT been posted yet.\n"
        "An admin must approve it first.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

async def approve_raffle_button(update, context):

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

    try:
        raffle_id = int(
            query.data.split("_")[1]
        )
    except Exception:

        await query.message.reply_text(
            "❌ Invalid raffle."
        )

        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await query.message.reply_text(
            "❌ Raffle not found."
        )

        return

    if raffle["status"] != "pending":

        await query.message.reply_text(
            "⚠️ This raffle has already been processed."
        )

        return

    approve_raffle(raffle_id)

    raffle = get_raffle(raffle_id)

    await query.message.reply_text(
        "✅ Raffle approved.\n\n"
        "Posting the raffle now."
    )

    # ------------------------------------------------------
    # Post into the same group where admin approved it
    # ------------------------------------------------------

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=raffle_post(raffle),
        reply_markup=raffle_keyboard(),
        parse_mode="Markdown"
    )


# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(update, context):

    if not update.message:
        return

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ There is no active raffle right now."
        )

        return

    await update.message.reply_text(
        "🎟️ **Enter the Melanated AZ Friends Raffle**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry: **{money(raffle['price'])}**\n\n"
        f"⏳ Time Remaining: **{countdown(raffle['expires_at'])}**\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown"
    )


# ==========================================================
# BUTTON ENTRY
# ==========================================================

async def raffle_enter_button(update, context):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ This raffle is no longer active."
        )

        return

    await query.message.reply_text(
        "🎟️ **RAFFLE ENTRY**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry Price: **{money(raffle['price'])}**\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown"
    )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(update, context):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )

        return

    user = query.from_user

    method = (
        "Zelle"
        if query.data == "raffle_zelle"
        else "Cash App"
    )

    entry_id = add_raffle_entry(
        raffle["id"],
        user.id,
        user.username,
        display_name(user),
        method
    )

    if entry_id is None:

        await query.message.reply_text(
            "⚠️ You already have a pending or approved "
            "entry for this raffle."
        )

        return

    if method == "Cash App":

        payment = (
            "💵 **Cash App**\n\n"
            f"Send **{money(raffle['price'])}** to:\n"
            f"`{CASHAPP_TAG}`"
        )

        if CASHAPP_URL:
            payment += f"\n\n🔗 {CASHAPP_URL}"

    else:

        payment = (
            "💳 **Zelle**\n\n"
            f"Send **{money(raffle['price'])}** to:\n"
            f"`{ZELLE_PHONE}`"
        )

    await query.message.reply_text(
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry Price: **{money(raffle['price'])}**\n"
        f"🆔 Entry #: **{entry_id}**\n\n"
        f"{payment}\n\n"
        "After payment is sent, an admin will verify it.\n\n"
        "⚠️ Your entry is NOT active until approved.",
        parse_mode="Markdown"
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
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Amount: **{money(raffle['price'])}**\n"
                    f"🆔 Entry #: **{entry_id}**\n"
                    f"👤 Name: {display_name(user)}\n"
                    f"🆔 User ID: `{user.id}`\n"
                    f"💳 Payment: **{method}**\n\n"
                    "Verify payment before approving."
                ),
                reply_markup=admin_entry_keyboard(entry_id),
                parse_mode="Markdown"
            )

        except Exception:

            logger.exception(
                "Unable to notify admin %s",
                admin_id
            )


# ==========================================================
# ADMIN ENTRY APPROVAL
# ==========================================================

async def admin_payment_button(update, context):

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

    try:

        action, entry_text = query.data.split("_", 1)
        entry_id = int(entry_text)

    except Exception:

        await query.message.reply_text(
            "❌ Invalid entry."
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
            query.from_user.id
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry has already been processed."
            )

            return

        await query.message.reply_text(
            f"✅ Entry #{entry_id} approved."
        )

        try:

            raffle = get_raffle(
                entry["raffle_id"]
            )

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!** 🎉\n\n"
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Entry: **{money(raffle['price'])}**\n"
                    f"🆔 Entry #: **{entry_id}**\n\n"
                    "Good luck! 🍀"
                ),
                parse_mode="Markdown"
            )

        except Exception:

            logger.exception(
                "Unable to notify participant."
            )

    elif action == "deny":

        success = deny_entry(
            entry_id,
            query.from_user.id
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry has already been processed."
            )

            return

        await query.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )


# ==========================================================
# PENDING PAYMENTS
# ==========================================================

async def pending_entries(update, context):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    entries = get_pending_entries()

    if not entries:

        await update.message.reply_text(
            "✅ No pending payments."
        )

        return

    for entry in entries:

        await update.message.reply_text(
            "💰 **PENDING PAYMENT**\n\n"
            f"🆔 Entry #: {entry['id']}\n"
            f"👤 {entry['display_name']}\n"
            f"💳 {entry['payment_method']}\n"
            f"🕐 {entry['created_at']}",
            reply_markup=admin_entry_keyboard(entry["id"]),
            parse_mode="Markdown"
        )


# ==========================================================
# APPROVE ENTRY COMMAND
# ==========================================================

async def approve_raffle_entry(update, context):

    if not admin_only(update):
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
            "❌ Invalid entry ID."
        )

        return

    if approve_entry(
        entry_id,
        update.effective_user.id
    ):

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

async def deny_raffle_entry(update, context):

    if not admin_only(update):
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
            "❌ Invalid entry ID."
        )

        return

    if deny_entry(
        entry_id,
        update.effective_user.id
    ):

        await update.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )

    else:

        await update.message.reply_text(
            "❌ Entry could not be denied."
        )


# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(update, context):

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
        f"💵 Entry: {money(raffle['price'])}\n"
        f"📌 Status: {raffle['status']}\n"
        f"⏳ Remaining: {countdown(raffle['expires_at'])}\n"
        f"👥 Approved Entries: {len(entries)}",
        parse_mode="Markdown"
    )


# ==========================================================
# ENTRIES
# ==========================================================

async def raffle_entries(update, context):

    if not admin_only(update):
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
        ""
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
        parse_mode="Markdown"
    )


# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(update, context):

    if not admin_only(update):
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
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry: **{money(raffle['price'])}**\n\n"
        f"🏆 Winner: **{name}**\n"
        f"🆔 Entry #: **{winner['id']}**\n\n"
        "Congratulations! 🍀",
        parse_mode="Markdown"
    )


# ==========================================================
# CANCEL
# ==========================================================

async def cancel_raffle(update, context):

    if not admin_only(update):
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
# BONUS
# ==========================================================

async def bonus_entry(update, context):

    if not admin_only(update):
        return

    await update.message.reply_text(
        "ℹ️ Bonus entries are not enabled."
    )


# ==========================================================
# REMOVE
# ==========================================================

async def remove_raffle_entry(update, context):

    if not admin_only(update):
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
            "❌ Invalid entry ID."
        )

        return

    if remove_entry(entry_id):

        await update.message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(update, context):

    if not admin_only(update):
        return

    await update.message.reply_text(
        "⚠️ Reroll requires a new active raffle."
    )


# ==========================================================
# EXPIRATION CHECK
# ==========================================================

async def check_raffle_expiration(context):

    raffle = get_active_raffle()

    if not raffle:
        return

    if not raffle["expires_at"]:
        return

    try:

        expiration = datetime.fromisoformat(
            raffle["expires_at"]
        )

        if datetime.utcnow() >= expiration:

            expire_raffle(
                raffle["id"]
            )

            for admin_id in ADMIN_IDS:

                try:

                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            "⏰ **RAFFLE EXPIRED**\n\n"
                            f"🎁 Prize: {raffle['prize']}\n"
                            f"🆔 Raffle #: {raffle['id']}\n\n"
                            "The one-week raffle period has ended."
                        ),
                        parse_mode="Markdown"
                    )

                except Exception:

                    logger.exception(
                        "Unable to notify admin of expiration."
                    )

    except Exception:

        logger.exception(
            "Error checking raffle expiration."
        )
