# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Private paid raffle
# Variable entry price
# Admin approval
# 7-day expiration
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
    approve_raffle,
    save_raffle_message,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle,
    get_entry_counts,
)


logger = logging.getLogger(__name__)


# ==========================================================
# HELPERS
# ==========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_only(update: Update) -> bool:

    user = update.effective_user

    return bool(
        user and is_admin(user.id)
    )


def money(value):

    try:

        value = float(value)

        if value.is_integer():
            return f"${int(value)}"

        return f"${value:.2f}"

    except (ValueError, TypeError):

        return "$0"


def get_display_name(user):

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


def raffle_entry_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Enter Raffle",
                    callback_data="raffle_enter",
                )
            ]
        ]
    )


def payment_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 Cash App",
                    callback_data="raffle_cashapp",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 Zelle",
                    callback_data="raffle_zelle",
                )
            ],
        ]
    )


def raffle_approval_keyboard(raffle_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve & Post Raffle",
                    callback_data=f"raffleapprove_{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f"rafflecancel_{raffle_id}",
                )
            ],
        ]
    )


def admin_entry_keyboard(entry_id):

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


def get_countdown(expires_at):

    if not expires_at:
        return "Expired"

    try:

        expiration = datetime.fromisoformat(
            expires_at
        )

        remaining = expiration - datetime.utcnow()

        seconds = int(
            remaining.total_seconds()
        )

        if seconds <= 0:
            return "EXPIRED"

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return (
            f"{days}d {hours}h {minutes}m"
        )

    except Exception:

        return "Unknown"


def raffle_post_text(raffle):

    return (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {money(raffle['entry_price'])}\n"
        f"🆔 **Raffle #:** {raffle['id']}\n\n"
        "🔒 **Private raffle between friends.**\n\n"
        f"⏳ **Time Remaining:** "
        f"{get_countdown(raffle['expires_at'])}\n\n"
        "Click **Enter Raffle** below to participate.\n\n"
        "Payment is required and every entry must be "
        "approved by an admin."
    )


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
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
            "Usage:\n\n"
            "/startraffle $100 Cash Prize | 10\n\n"
            "The number after | is the entry price.\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )

        return

    existing = get_active_raffle()

    if existing:

        await update.message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"💵 Entry: {money(existing['entry_price'])}\n"
            f"🆔 Raffle #: {existing['id']}"
        )

        return

    existing_pending = get_pending_raffle()

    if existing_pending:

        await update.message.reply_text(
            "⚠️ There is already a raffle waiting "
            "for admin approval.\n\n"
            f"🎁 Prize: {existing_pending['prize']}\n"
            f"💵 Entry: "
            f"{money(existing_pending['entry_price'])}\n"
            f"🆔 Raffle #: {existing_pending['id']}"
        )

        return

    raw = " ".join(context.args)

    if "|" not in raw:

        await update.message.reply_text(
            "❌ You must include the entry price.\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )

        return

    prize_part, price_part = raw.rsplit(
        "|",
        1
    )

    prize = prize_part.strip()

    try:

        entry_price = float(
            price_part.strip().replace("$", "")
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid entry price.\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )

        return

    if entry_price <= 0:

        await update.message.reply_text(
            "❌ Entry price must be greater than $0."
        )

        return

    chat_id = (
        update.effective_chat.id
        if update.effective_chat
        else None
    )

    raffle_id = create_raffle(
        prize,
        entry_price,
        chat_id
    )

    raffle = get_raffle(
        raffle_id
    )

    await update.message.reply_text(
        "🎟️ **RAFFLE CREATED — WAITING FOR APPROVAL**\n\n"
        f"🎁 Prize: **{prize}**\n"
        f"💵 Entry Price: **{money(entry_price)}**\n"
        f"🆔 Raffle #: **{raffle_id}**\n\n"
        "An admin must approve this raffle before "
        "it is posted to the group.",
        reply_markup=raffle_approval_keyboard(
            raffle_id
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# APPROVE AND POST RAFFLE
# ==========================================================

async def approve_and_post_raffle(
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

    try:

        raffle_id = int(
            query.data.split("_", 1)[1]
        )

    except ValueError:

        await query.message.reply_text(
            "❌ Invalid raffle."
        )

        return

    raffle = get_raffle(
        raffle_id
    )

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

    chat_id = raffle["chat_id"]

    if not chat_id:

        chat_id = query.message.chat_id

    success = approve_raffle(
        raffle_id,
        chat_id
    )

    if not success:

        await query.message.reply_text(
            "❌ Raffle could not be approved."
        )

        return

    raffle = get_raffle(
        raffle_id
    )

    posted = await context.bot.send_message(
        chat_id=chat_id,
        text=raffle_post_text(raffle),
        reply_markup=raffle_entry_keyboard(),
        parse_mode="Markdown",
    )

    save_raffle_message(
        raffle_id,
        posted.message_id
    )

    await query.edit_message_text(
        "✅ **RAFFLE APPROVED AND POSTED**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {money(raffle['entry_price'])}\n"
        f"🆔 Raffle #: {raffle['id']}\n"
        "⏳ Duration: 7 days",
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
            "❌ There is no active raffle."
        )

        return

    await update.message.reply_text(
        "🎟️ **ENTER MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry: **{money(raffle['entry_price'])}**\n\n"
        "Choose a payment method:",
        reply_markup=payment_keyboard(),
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

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )

        return

    if query.data == "raffle_enter":

        await query.message.reply_text(
            "🎟️ **Choose Payment Method**\n\n"
            f"💵 Entry Price: "
            f"**{money(raffle['entry_price'])}**",
            reply_markup=payment_keyboard(),
            parse_mode="Markdown",
        )

        return

    user = query.from_user

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
            "⚠️ You already have a pending or approved "
            "entry for this raffle."
        )

        return

    if payment_method == "Cash App":

        payment_text = (
            "💵 **Cash App**\n\n"
            f"Send **{money(raffle['entry_price'])}** to:\n"
            f"`{CASHAPP_TAG}`\n"
        )

        if CASHAPP_URL:

            payment_text += (
                f"\n🔗 {CASHAPP_URL}\n"
            )

    else:

        payment_text = (
            "💳 **Zelle**\n\n"
            f"Send **{money(raffle['entry_price'])}** to:\n"
            f"`{ZELLE_PHONE}`\n"
        )

    await query.message.reply_text(
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: "
        f"{money(raffle['entry_price'])}\n"
        f"🆔 Entry #: {entry_id}\n"
        f"💳 Payment: {payment_method}\n\n"
        f"{payment_text}\n"
        "Once payment is sent, an admin will verify it.\n\n"
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
                    f"💵 Amount: "
                    f"{money(raffle['entry_price'])}\n"
                    f"🆔 Entry #: {entry_id}\n"
                    f"👤 Name: {get_display_name(user)}\n"
                    f"🔹 User ID: `{user.id}`\n"
                    f"💳 Payment: {payment_method}\n\n"
                    "Verify the payment before approving."
                ),
                reply_markup=admin_entry_keyboard(
                    entry_id
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin %s",
                admin_id
            )


# ==========================================================
# ADMIN ENTRY APPROVAL
# ==========================================================

async def admin_payment_button(
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

    try:

        action, entry_text = query.data.split(
            "_",
            1
        )

        entry_id = int(entry_text)

    except (ValueError, AttributeError):

        await query.message.reply_text(
            "❌ Invalid raffle entry."
        )

        return

    entry = get_entry(
        entry_id
    )

    if not entry:

        await query.message.reply_text(
            "❌ Entry not found."
        )

        return

    raffle = get_raffle(
        entry["raffle_id"]
    )

    if action == "approve":

        success = approve_entry(
            entry_id,
            query.from_user.id
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry could not be approved. "
                "It may already be processed."
            )

            return

        await query.edit_message_text(
            f"✅ **Payment Approved**\n\n"
            f"Entry #: {entry_id}\n"
            f"Amount: {money(raffle['entry_price'])}",
            parse_mode="Markdown",
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!**\n\n"
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Entry: **{money(raffle['entry_price'])}**\n"
                    f"🆔 Entry #: {entry_id}\n\n"
                    "Your payment has been verified.\n"
                    "Good luck! 🍀"
                ),
                parse_mode="Markdown",
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
                "⚠️ Entry could not be denied."
            )

            return

        await query.edit_message_text(
            f"❌ **Payment Denied**\n\n"
            f"Entry #: {entry_id}",
            parse_mode="Markdown",
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "❌ Your raffle payment was not approved.\n\n"
                    f"🆔 Entry #: {entry_id}\n\n"
                    "Please contact an admin if you believe "
                    "this was an error."
                ),
            )

        except Exception:

            logger.exception(
                "Unable to notify participant."
            )


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
            "✅ No pending payments."
        )

        return

    for entry in entries:

        await update.message.reply_text(
            "💰 **PENDING PAYMENT**\n\n"
            f"🆔 Entry #: {entry['id']}\n"
            f"👤 {entry['display_name']}\n"
            f"🎁 Prize: {entry['prize']}\n"
            f"💵 Amount: {money(entry['entry_price'])}\n"
            f"💳 Payment: {entry['payment_method']}",
            reply_markup=admin_entry_keyboard(
                entry["id"]
            ),
            parse_mode="Markdown",
        )


# ==========================================================
# APPROVED ENTRIES
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
# STATUS
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

    counts = get_entry_counts(
        raffle["id"]
    )

    await update.message.reply_text(
        "🎟️ **RAFFLE STATUS**\n\n"
        f"🆔 Raffle #: {raffle['id']}\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {money(raffle['entry_price'])}\n"
        f"📌 Status: {raffle['status']}\n"
        f"⏳ Time Remaining: "
        f"{get_countdown(raffle['expires_at'])}\n\n"
        f"⏳ Pending Payments: {counts['pending']}\n"
        f"✅ Approved Entries: {counts['approved']}",
        parse_mode="Markdown",
    )


# ==========================================================
# DRAW
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

    winner = random.choice(
        entries
    )

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
# CANCEL
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
# COMMAND APPROVE ENTRY
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

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )

        return

    success = approve_entry(
        entry_id,
        update.effective_user.id
    )

    await update.message.reply_text(
        f"✅ Entry #{entry_id} approved."
        if success
        else "❌ Entry could not be approved."
    )


# ==========================================================
# COMMAND DENY ENTRY
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

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )

        return

    success = deny_entry(
        entry_id,
        update.effective_user.id
    )

    await update.message.reply_text(
        f"❌ Entry #{entry_id} denied."
        if success
        else "❌ Entry could not be denied."
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

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )

        return

    success = remove_entry(
        entry_id
    )

    await update.message.reply_text(
        f"🗑️ Entry #{entry_id} removed."
        if success
        else "❌ Entry not found."
    )


# ==========================================================
# BONUS
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
        "ℹ️ Bonus entries are not enabled."
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
        "⚠️ Reroll requires a new active raffle."
    )
