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
    RAFFLE_CHAT_ID,
)

from raffle_database import (
    create_raffle,
    get_raffle,
    get_active_raffle,
    get_pending_raffle,
    approve_raffle,
    set_posted_message,
    close_raffle,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
)


logger = logging.getLogger(__name__)


# ==========================================================
# HELPERS
# ==========================================================

def is_admin(user_id):
    return user_id in ADMIN_IDS


def admin_only(update):

    user = update.effective_user

    return bool(
        user and is_admin(user.id)
    )


def name_of(user):

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


def format_price(price):

    return f"${price:,.2f}"


def time_remaining(expires_at):

    try:

        expires = datetime.fromisoformat(
            expires_at
        )

        remaining = expires - datetime.utcnow()

        seconds = max(
            0,
            int(remaining.total_seconds())
        )

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return (
            f"{days}d {hours}h {minutes}m"
        )

    except Exception:

        return "7 days"


# ==========================================================
# GROUP RAFFLE KEYBOARD
# ==========================================================

def group_raffle_keyboard():

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


# ==========================================================
# PAYMENT KEYBOARD
# ==========================================================

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


# ==========================================================
# ADMIN RAFFLE APPROVAL
# ==========================================================

def raffle_approval_keyboard(
    raffle_id
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve & Post",
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


# ==========================================================
# PAYMENT APPROVAL
# ==========================================================

def payment_approval_keyboard(
    entry_id
):

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


# ==========================================================
# START RAFFLE
#
# /startraffle $100 Cash Prize | 10
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
            "/startraffle Prize | Entry Price\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )
        return

    existing = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if existing:

        await update.message.reply_text(
            "⚠️ There is already a raffle "
            "waiting for approval or currently active."
        )
        return

    raw = " ".join(
        context.args
    )

    if "|" not in raw:

        await update.message.reply_text(
            "❌ Please include the entry price.\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )
        return

    prize, price_text = raw.split(
        "|",
        1
    )

    prize = prize.strip()

    try:

        entry_price = float(
            price_text.strip()
            .replace("$", "")
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Entry price must be a number.\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )
        return

    if entry_price <= 0:

        await update.message.reply_text(
            "❌ Entry price must be greater than $0."
        )
        return

    raffle_id = create_raffle(
        prize,
        entry_price
    )

    await update.message.reply_text(
        "🎟️ **RAFFLE CREATED**\n\n"
        f"🎁 Prize: **{prize}**\n"
        f"💵 Entry Price: **{format_price(entry_price)}**\n"
        f"🆔 Raffle #: **{raffle_id}**\n\n"
        "The raffle is waiting for admin approval.",
        reply_markup=raffle_approval_keyboard(
            raffle_id
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# APPROVE + POST RAFFLE
# ==========================================================

async def approve_raffle_button(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )
        return

    try:

        raffle_id = int(
            query.data.split("_")[1]
        )

    except Exception:

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

    if RAFFLE_CHAT_ID == 0:

        await query.message.reply_text(
            "❌ RAFFLE_CHAT_ID is not configured."
        )
        return

    success = approve_raffle(
        raffle_id
    )

    if not success:

        await query.message.reply_text(
            "❌ Raffle could not be approved."
        )
        return

    raffle = get_raffle(
        raffle_id
    )

    text = (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {format_price(raffle['entry_price'])}\n\n"
        "🔐 Private raffle for Melanated AZ friends.\n\n"
        f"⏳ **Time Remaining:** "
        f"{time_remaining(raffle['expires_at'])}\n\n"
        "Tap the button below to enter.\n"
        "Payment is required and all entries "
        "must be approved by an admin.\n\n"
        "🍀 Good luck!"
    )

    try:

        message = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=text,
            reply_markup=group_raffle_keyboard(),
            parse_mode="Markdown",
        )

        set_posted_message(
            raffle_id,
            message.message_id
        )

        await query.message.reply_text(
            "✅ Raffle approved and posted "
            "to the Melanated AZ group."
        )

    except Exception:

        logger.exception(
            "Unable to post raffle."
        )

        await query.message.reply_text(
            "⚠️ Raffle was approved, but I could "
            "not post it to the raffle group."
        )


# ==========================================================
# ENTER BUTTON
# ==========================================================

async def enter_button(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    await query.message.reply_text(
        "🎟️ **ENTER MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry: **{format_price(raffle['entry_price'])}**\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ This raffle is no longer active."
        )
        return

    user = query.from_user

    payment_method = (
        "Zelle"
        if query.data == "raffle_zelle"
        else "Cash App"
    )

    entry_id = add_raffle_entry(
        raffle["id"],
        user.id,
        user.username,
        name_of(user),
        payment_method
    )

    if entry_id is None:

        await query.message.reply_text(
            "⚠️ You already have a pending "
            "or approved entry."
        )
        return

    if payment_method == "Cash App":

        payment = (
            "💵 **Cash App**\n\n"
            f"Send **{format_price(raffle['entry_price'])}** "
            f"to `{CASHAPP_TAG}`"
        )

        if CASHAPP_URL:

            payment += (
                f"\n\n🔗 {CASHAPP_URL}"
            )

    else:

        payment = (
            "💳 **Zelle**\n\n"
            f"Send **{format_price(raffle['entry_price'])}** "
            f"to `{ZELLE_PHONE}`"
        )

    await query.message.reply_text(
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {format_price(raffle['entry_price'])}\n"
        f"🆔 Entry #: {entry_id}\n\n"
        f"{payment}\n\n"
        "After payment, an admin will verify it.\n\n"
        "⚠️ Your entry is not active until approved.",
        parse_mode="Markdown",
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **PENDING RAFFLE PAYMENT**\n\n"
                    f"🎁 Prize: {raffle['prize']}\n"
                    f"💵 Amount: {format_price(raffle['entry_price'])}\n"
                    f"🆔 Entry #: {entry_id}\n"
                    f"👤 Name: {name_of(user)}\n"
                    f"🆔 User ID: `{user.id}`\n"
                    f"💳 Payment: {payment_method}"
                ),
                reply_markup=payment_approval_keyboard(
                    entry_id
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin."
            )


# ==========================================================
# ADMIN PAYMENT APPROVAL
# ==========================================================

async def admin_payment_button(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )
        return

    action, value = query.data.split(
        "_",
        1
    )

    entry_id = int(value)

    entry = get_entry(
        entry_id
    )

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

        if success:

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
                        "🎉 **RAFFLE ENTRY APPROVED!**\n\n"
                        f"🎁 Prize: **{raffle['prize']}**\n"
                        f"💵 Entry: **{format_price(raffle['entry_price'])}**\n"
                        f"🆔 Entry #: **{entry_id}**\n\n"
                        "Good luck! 🍀"
                    ),
                    parse_mode="Markdown",
                )

            except Exception:

                logger.exception(
                    "Unable to notify participant."
                )

        else:

            await query.message.reply_text(
                "⚠️ Entry was already processed."
            )

    elif action == "deny":

        success = deny_entry(
            entry_id,
            query.from_user.id
        )

        if success:

            await query.message.reply_text(
                f"❌ Entry #{entry_id} denied."
            )

            try:

                await context.bot.send_message(
                    chat_id=entry["user_id"],
                    text=(
                        "❌ Your raffle payment "
                        "was not approved.\n\n"
                        f"Entry #: {entry_id}\n"
                        "Please contact an admin."
                    )
                )

            except Exception:

                logger.exception(
                    "Unable to notify participant."
                )


# ==========================================================
# ADMIN PENDING RAFFLE
# ==========================================================

async def pending_raffle(
    update,
    context
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    raffle = get_pending_raffle()

    if not raffle:

        await update.message.reply_text(
            "✅ No raffle waiting for approval."
        )
        return

    await update.message.reply_text(
        "🎟️ **RAFFLE WAITING FOR APPROVAL**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry: **{format_price(raffle['entry_price'])}**\n"
        f"🆔 Raffle #: **{raffle['id']}**",
        reply_markup=raffle_approval_keyboard(
            raffle["id"]
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(
    update,
    context
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
        f"💵 Entry: {format_price(raffle['entry_price'])}\n"
        f"👥 Approved Entries: {len(entries)}\n"
        f"⏳ Time Remaining: "
        f"{time_remaining(raffle['expires_at'])}",
        parse_mode="Markdown",
    )


# ==========================================================
# ENTRIES
# ==========================================================

async def raffle_entries(
    update,
    context
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
        "🎟️ APPROVED ENTRIES",
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
        "\n".join(lines)
    )


# ==========================================================
# PENDING PAYMENTS
# ==========================================================

async def pending_entries(
    update,
    context
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
            "💰 PENDING PAYMENT\n\n"
            f"Entry #: {entry['id']}\n"
            f"User: {entry['display_name']}\n"
            f"Payment: {entry['payment_method']}",
            reply_markup=payment_approval_keyboard(
                entry["id"]
            )
        )


# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(
    update,
    context
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

    if (
        raffle["expires_at"]
        and datetime.utcnow()
        < datetime.fromisoformat(
            raffle["expires_at"]
        )
    ):

        await update.message.reply_text(
            "⏳ The raffle has not expired yet.\n\n"
            f"Time remaining: "
            f"{time_remaining(raffle['expires_at'])}"
        )
        return

    entries = get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await update.message.reply_text(
            "❌ No approved paid entries."
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
        f"🆔 Entry #: **{winner['id']}**\n\n"
        "Congratulations! 🍀",
        parse_mode="Markdown",
    )


# ==========================================================
# CANCEL
# ==========================================================

async def cancel_raffle(
    update,
    context
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    raffle = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if not raffle:

        await update.message.reply_text(
            "❌ No raffle to cancel."
        )
        return

    close_raffle(
        raffle["id"]
    )

    await update.message.reply_text(
        f"🛑 Raffle #{raffle['id']} cancelled."
    )


# ==========================================================
# APPROVE ENTRY COMMAND
# ==========================================================

async def approve_raffle_entry(
    update,
    context
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
            "❌ Invalid entry ID."
        )
        return

    success = approve_entry(
        entry_id,
        update.effective_user.id
    )

    await update.message.reply_text(
        "✅ Entry approved."
        if success
        else "❌ Entry could not be approved."
    )


# ==========================================================
# DENY ENTRY COMMAND
# ==========================================================

async def deny_raffle_entry(
    update,
    context
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
            "❌ Invalid entry ID."
        )
        return

    success = deny_entry(
        entry_id,
        update.effective_user.id
    )

    await update.message.reply_text(
        "❌ Entry denied."
        if success
        else "❌ Entry could not be denied."
    )


# ==========================================================
# REMOVE
# ==========================================================

async def remove_raffle_entry(
    update,
    context
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
            "❌ Invalid entry ID."
        )
        return

    success = remove_entry(
        entry_id
    )

    await update.message.reply_text(
        "🗑️ Entry removed."
        if success
        else "❌ Entry not found."
    )
