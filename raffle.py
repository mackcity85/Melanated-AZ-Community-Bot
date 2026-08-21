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
    approve_raffle,
    set_posted_message,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle,
    expire_raffle,
)


logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


def admin_only(update):

    user = update.effective_user

    if not user:
        return False

    return is_admin(user.id)


# ==========================================================
# COUNTDOWN
# ==========================================================

def countdown_text(raffle):

    if not raffle["expires_at"]:
        return "⏳ Expiration: 7 days"

    try:

        expires = datetime.fromisoformat(
            raffle["expires_at"]
        )

        remaining = expires - datetime.utcnow()

        seconds = int(
            remaining.total_seconds()
        )

        if seconds <= 0:

            return "⏰ **RAFFLE EXPIRED**"

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return (
            f"⏳ **Time Remaining:** "
            f"{days}d {hours}h {minutes}m"
        )

    except Exception:

        return "⏳ **Time Remaining:** 7 days"


# ==========================================================
# RAFFLE POST BUTTON
# ==========================================================

def public_raffle_keyboard():

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
# PAYMENT BUTTONS
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
            ]
        ]
    )


# ==========================================================
# ADMIN ENTRY BUTTONS
# ==========================================================

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
                )
            ]
        ]
    )


# ==========================================================
# ADMIN RAFFLE APPROVAL
# ==========================================================

def admin_raffle_approval_keyboard(raffle_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve & Post",
                    callback_data=f"approve_raffle_{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f"cancel_raffle_{raffle_id}",
                )
            ]
        ]
    )


# ==========================================================
# DISPLAY NAME
# ==========================================================

def get_display_name(user):

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


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
            "/startraffle PRIZE | ENTRY PRICE\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )

        return

    existing = get_active_raffle()

    if existing:

        await update.message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"💵 Entry: ${existing['entry_price']}"
        )

        return

    raw = " ".join(context.args)

    if "|" not in raw:

        await update.message.reply_text(
            "❌ Please include the entry price.\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | 10"
        )

        return

    prize, price = raw.split("|", 1)

    prize = prize.strip()
    price = price.strip()

    if not prize or not price:

        await update.message.reply_text(
            "❌ Prize and entry price are required."
        )

        return

    raffle_id = create_raffle(
        prize,
        price
    )

    text = (
        "🎟️ **RAFFLE AWAITING APPROVAL**\n\n"
        f"🎁 **Prize:** {prize}\n"
        f"💵 **Entry Price:** ${price}\n"
        f"🆔 **Raffle #:** {raffle_id}\n\n"
        "⏳ Once approved, the raffle will be posted "
        "to the group for 7 days.\n\n"
        "Approve this raffle?"
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=admin_raffle_approval_keyboard(
                    raffle_id
                ),
                parse_mode="Markdown"
            )

        except Exception:

            logger.exception(
                "Unable to notify admin."
            )

    await update.message.reply_text(
        f"✅ Raffle #{raffle_id} created and sent for admin approval."
    )


# ==========================================================
# POST APPROVED RAFFLE
# ==========================================================

async def post_approved_raffle(
    query,
    context,
    raffle_id
):

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

    chat_id = query.message.chat_id

    message = (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** ${raffle['entry_price']}\n\n"
        "🔒 **Private raffle for Melanated AZ friends.**\n\n"
        f"{countdown_text(raffle)}\n\n"
        "Click below to enter."
    )

    sent = await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=public_raffle_keyboard(),
        parse_mode="Markdown"
    )

    set_posted_message(
        raffle_id,
        sent.message_id,
        chat_id
    )

    await query.message.reply_text(
        f"✅ Raffle #{raffle_id} approved and posted."
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
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: ${raffle['entry_price']}\n\n"
        f"{countdown_text(raffle)}\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown"
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
            "❌ There is no active raffle."
        )

        return

    user = query.from_user

    if query.data == "raffle_cashapp":

        method = "Cash App"

    else:

        method = "Zelle"

    entry_id = add_raffle_entry(
        raffle["id"],
        user.id,
        user.username,
        get_display_name(user),
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
            f"Send **${raffle['entry_price']}** to:\n"
            f"`{CASHAPP_TAG}`"
        )

        if CASHAPP_URL:

            payment += f"\n\n🔗 {CASHAPP_URL}"

    else:

        payment = (
            "💳 **Zelle**\n\n"
            f"Send **${raffle['entry_price']}** to:\n"
            f"`{ZELLE_PHONE}`"
        )

    await query.message.reply_text(
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Amount: ${raffle['entry_price']}\n"
        f"🆔 Entry #: {entry_id}\n\n"
        f"{payment}\n\n"
        "After payment, an admin will verify it.\n\n"
        "⚠️ Your entry is not active until approved.",
        parse_mode="Markdown"
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **PENDING RAFFLE PAYMENT**\n\n"
                    f"🎁 Prize: {raffle['prize']}\n"
                    f"💵 Amount: ${raffle['entry_price']}\n"
                    f"🆔 Entry #: {entry_id}\n"
                    f"👤 {get_display_name(user)}\n"
                    f"💳 Method: {method}\n\n"
                    "Verify payment before approving."
                ),
                reply_markup=admin_entry_keyboard(entry_id),
                parse_mode="Markdown"
            )

        except Exception:

            logger.exception(
                "Unable to notify admin."
            )


# ==========================================================
# ADMIN ENTRY APPROVAL
# ==========================================================

async def admin_payment_button(
    update,
    context
):

    query = update.callback_query

    admin = query.from_user

    if not is_admin(admin.id):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    action, entry_id_text = query.data.split("_", 1)

    entry_id = int(entry_id_text)

    entry = get_entry(entry_id)

    if not entry:

        await query.message.reply_text(
            "❌ Entry not found."
        )

        return

    if action == "approve":

        success = approve_entry(
            entry_id,
            admin.id
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry was already processed."
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
                    f"🆔 Entry #: {entry_id}\n\n"
                    "Good luck! 🍀"
                ),
                parse_mode="Markdown"
            )

        except Exception:

            logger.exception(
                "Unable to notify participant."
            )

    else:

        success = deny_entry(
            entry_id,
            admin.id
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry was already processed."
            )

            return

        await query.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )


# ==========================================================
# ADMIN APPROVE RAFFLE BUTTON
# ==========================================================

async def admin_raffle_button(
    update,
    context
):

    query = update.callback_query

    admin = query.from_user

    if not is_admin(admin.id):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )

        return

    await query.answer()

    data = query.data

    if data.startswith("approve_raffle_"):

        raffle_id = int(
            data.replace(
                "approve_raffle_",
                ""
            )
        )

        await post_approved_raffle(
            query,
            context,
            raffle_id
        )

    elif data.startswith("cancel_raffle_"):

        raffle_id = int(
            data.replace(
                "cancel_raffle_",
                ""
            )
        )

        close_raffle(raffle_id)

        await query.message.reply_text(
            f"🛑 Raffle #{raffle_id} cancelled."
        )


# ==========================================================
# /ENTER
# ==========================================================

async def enter_raffle(update, context):

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ There is no active raffle."
        )

        return

    await update.message.reply_text(
        "🎟️ **MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: ${raffle['entry_price']}\n\n"
        f"{countdown_text(raffle)}",
        reply_markup=public_raffle_keyboard(),
        parse_mode="Markdown"
    )


# ==========================================================
# PENDING
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
            f"💵 Amount: ${entry['entry_price']}\n"
            f"💳 {entry['payment_method']}",
            reply_markup=admin_entry_keyboard(
                entry["id"]
            ),
            parse_mode="Markdown"
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
        f"💵 Entry: ${raffle['entry_price']}\n"
        f"📌 Status: {raffle['status']}\n"
        f"👥 Approved Entries: {len(entries)}\n\n"
        f"{countdown_text(raffle)}",
        parse_mode="Markdown"
    )


# ==========================================================
# ENTRIES
# ==========================================================

async def raffle_entries(update, context):

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
            "❌ No approved paid entries."
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
        parse_mode="Markdown"
    )


# ==========================================================
# CANCEL
# ==========================================================

async def cancel_raffle(update, context):

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
# BONUS
# ==========================================================

async def bonus_entry(update, context):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    await update.message.reply_text(
        "ℹ️ Bonus entries are not enabled."
    )


# ==========================================================
# REMOVE
# ==========================================================

async def remove_raffle_entry(update, context):

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

    if remove_entry(entry_id):

        await update.message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )


# ==========================================================
# REFRESH RAFFLE COUNTDOWN
# ==========================================================

async def refresh_raffle(update, context):

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

    await update.message.reply_text(
        "🔄 **RAFFLE REFRESH**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: ${raffle['entry_price']}\n\n"
        f"{countdown_text(raffle)}",
        parse_mode="Markdown"
    )
