# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Private paid raffle
# Admin approval + 7 day expiration
# ==========================================================

import logging
import random
from datetime import datetime, timedelta

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
    deny_raffle,
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
# ADMIN
# ==========================================================

def is_admin(
    user_id: int,
) -> bool:

    return user_id in ADMIN_IDS


def admin_only(
    update: Update,
) -> bool:

    user = update.effective_user

    if not user:
        return False

    return is_admin(user.id)


# ==========================================================
# DISPLAY NAME
# ==========================================================

def get_display_name(
    user,
) -> str:

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


# ==========================================================
# RAFFLE BUTTONS
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


def payment_keyboard():

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


def admin_raffle_approval_keyboard(
    raffle_id,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve & Post",
                    callback_data=f"raffleapprove_{raffle_id}",
                ),
                InlineKeyboardButton(
                    "❌ Deny",
                    callback_data=f"raffaldeny_{raffle_id}",
                ),
            ]
        ]
    )


def admin_entry_keyboard(
    entry_id,
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
# FORMAT TIME
# ==========================================================

def format_remaining(
    expires_at,
):

    try:

        expiration = datetime.fromisoformat(
            expires_at
        )

        now = datetime.utcnow()

        remaining = expiration - now

        if remaining.total_seconds() <= 0:
            return "EXPIRED"

        days = remaining.days

        hours = (
            remaining.seconds // 3600
        )

        minutes = (
            remaining.seconds % 3600
        ) // 60

        return (
            f"{days}d "
            f"{hours}h "
            f"{minutes}m"
        )

    except Exception:

        return "7 days"


# ==========================================================
# RAFFLE MESSAGE
# ==========================================================

def raffle_text(
    raffle,
):

    countdown = format_remaining(
        raffle["expires_at"]
    )

    return (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {raffle['entry_price']}\n"
        f"🆔 **Raffle #:** {raffle['id']}\n\n"
        "🔒 **Private raffle for Melanated AZ friends.**\n\n"
        "Click the button below to enter.\n"
        "Payment is required for an entry.\n"
        "All payments must be approved by an admin.\n\n"
        f"⏳ **Time Remaining:** {countdown}\n\n"
        "🍀 Good luck!"
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
            "❌ This command is for raffle admins only."
        )
        return

    if not update.message:
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n\n"
            "/startraffle PRIZE | ENTRY PRICE\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | $10 Entry"
        )

        return

    existing = get_active_raffle()

    if existing:

        await update.message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"💵 Entry: {existing['entry_price']}\n"
            f"🆔 Raffle #: {existing['id']}"
        )

        return

    text = " ".join(
        context.args
    ).strip()

    if "|" not in text:

        await update.message.reply_text(
            "❌ Please include the entry price.\n\n"
            "Use:\n"
            "/startraffle PRIZE | ENTRY PRICE\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | $10 Entry"
        )

        return

    prize, entry_price = text.split(
        "|",
        1,
    )

    prize = prize.strip()
    entry_price = entry_price.strip()

    if not prize or not entry_price:

        await update.message.reply_text(
            "❌ Both the prize and entry price are required."
        )

        return

    raffle_id = create_raffle(
        prize=prize,
        entry_price=entry_price,
        chat_id=update.effective_chat.id,
    )

    approval_text = (
        "🎟️ **RAFFLE APPROVAL REQUIRED**\n\n"
        f"🆔 Raffle #: {raffle_id}\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry Price: {entry_price}\n\n"
        "🔒 Private Melanated AZ Friends Raffle\n\n"
        "This raffle has NOT been posted yet.\n\n"
        "Approve it to post the raffle and start "
        "the 7-day countdown."
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=approval_text,
                reply_markup=admin_raffle_approval_keyboard(
                    raffle_id
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin %s",
                admin_id,
            )

    await update.message.reply_text(
        "✅ **Raffle Created**\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry Price: {entry_price}\n"
        f"🆔 Raffle #: {raffle_id}\n\n"
        "⏳ Waiting for admin approval.\n"
        "The 7-day countdown will begin after approval.",
        parse_mode="Markdown",
    )


# ==========================================================
# APPROVE / DENY RAFFLE
# ==========================================================

async def raffle_approval_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    data = query.data

    if data.startswith(
        "raffleapprove_"
    ):

        raffle_id = int(
            data.split("_", 1)[1]
        )

        raffle = get_raffle(
            raffle_id
        )

        if not raffle:

            await query.edit_message_text(
                "❌ Raffle not found."
            )

            return

        if raffle["status"] != "pending":

            await query.edit_message_text(
                "⚠️ This raffle has already been processed."
            )

            return

        expires_at = (
            datetime.utcnow()
            + timedelta(days=7)
        ).isoformat()

        chat_id = raffle["chat_id"]

        if not chat_id:

            await query.edit_message_text(
                "❌ I don't know which group this raffle "
                "belongs to."
            )

            return

        # --------------------------------------------------
        # Send raffle to group
        # --------------------------------------------------

        raffle_copy = dict(raffle)

        raffle_copy["expires_at"] = expires_at

        posted = await context.bot.send_message(
            chat_id=chat_id,
            text=raffle_text(
                raffle_copy
            ),
            reply_markup=public_raffle_keyboard(),
            parse_mode="Markdown",
        )

        # --------------------------------------------------
        # Save approval
        # --------------------------------------------------

        approve_raffle(
            raffle_id=raffle_id,
            admin_id=query.from_user.id,
            chat_id=chat_id,
            message_id=posted.message_id,
            expires_at=expires_at,
        )

        await query.edit_message_text(
            "✅ **RAFFLE APPROVED & POSTED**\n\n"
            f"🆔 Raffle #: {raffle_id}\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry: {raffle['entry_price']}\n\n"
            "⏳ The 7-day countdown has started.",
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # DENY
    # ------------------------------------------------------

    if data.startswith(
        "raffaldeny_"
    ):

        raffle_id = int(
            data.split("_", 1)[1]
        )

        success = deny_raffle(
            raffle_id,
            query.from_user.id,
        )

        if success:

            await query.edit_message_text(
                f"❌ **RAFFLE #{raffle_id} DENIED**",
                parse_mode="Markdown",
            )

        else:

            await query.edit_message_text(
                "⚠️ This raffle could not be denied."
            )


# ==========================================================
# ENTER BUTTON
# ==========================================================

async def enter_button(
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

    if raffle["expires_at"]:

        expiration = datetime.fromisoformat(
            raffle["expires_at"]
        )

        if datetime.utcnow() >= expiration:

            close_raffle(
                raffle["id"]
            )

            await query.message.reply_text(
                "⏰ This raffle has expired."
            )

            return

    await query.message.reply_text(
        "🎟️ **ENTER MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['entry_price']}\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# COMMAND ENTER
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
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['entry_price']}\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# PAID COMMAND
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await enter_raffle(
        update,
        context,
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

    # ------------------------------------------------------
    # Check expiration
    # ------------------------------------------------------

    if raffle["expires_at"]:

        expiration = datetime.fromisoformat(
            raffle["expires_at"]
        )

        if datetime.utcnow() >= expiration:

            close_raffle(
                raffle["id"]
            )

            await query.message.reply_text(
                "⏰ This raffle has expired."
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

    # ------------------------------------------------------
    # PAYMENT INFORMATION
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
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['entry_price']}\n"
        f"🆔 Entry #: {entry_id}\n"
        f"💳 Method: {payment_method}\n\n"
        f"{payment_text}\n"
        "Once payment is sent, an admin will verify it.\n\n"
        "⚠️ Your entry is NOT active until approved.",
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # NOTIFY ADMINS
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **RAFFLE PAYMENT PENDING**\n\n"
                    f"🎁 Prize: {raffle['prize']}\n"
                    f"💵 Entry Price: {raffle['entry_price']}\n"
                    f"🆔 Raffle #: {raffle['id']}\n"
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
                admin_id,
            )


# ==========================================================
# ENTRY APPROVAL BUTTON
# ==========================================================

async def admin_payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    try:

        action, entry_text = (
            query.data.split(
                "_",
                1,
            )
        )

        entry_id = int(
            entry_text
        )

    except Exception:

        await query.message.reply_text(
            "❌ Invalid entry."
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

    if action == "approve":

        success = approve_entry(
            entry_id,
            query.from_user.id,
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry has already been processed."
            )

            return

        await query.edit_message_text(
            f"✅ **Entry #{entry_id} APPROVED**\n\n"
            f"👤 {entry['display_name'] or entry['user_id']}\n"
            f"💳 {entry['payment_method']}",
            parse_mode="Markdown",
        )

        raffle = get_raffle(
            entry["raffle_id"]
        )

        prize = (
            raffle["prize"]
            if raffle
            else "raffle prize"
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!**\n\n"
                    f"🎁 Prize: **{prize}**\n"
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
            query.from_user.id,
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry has already been processed."
            )

            return

        await query.edit_message_text(
            f"❌ **Entry #{entry_id} DENIED**",
            parse_mode="Markdown",
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
            "✅ No pending raffle payments."
        )

        return

    for entry in entries:

        await update.message.reply_text(
            "💰 **PENDING PAYMENT**\n\n"
            f"🎟️ Raffle #: {entry['raffle_id']}\n"
            f"🎁 Prize: {entry['prize']}\n"
            f"💵 Entry Price: {entry['entry_price']}\n"
            f"🆔 Entry #: {entry['id']}\n"
            f"👤 User ID: {entry['user_id']}\n"
            f"💳 Payment: {entry['payment_method']}",
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
        update.effective_user.id,
    )

    await update.message.reply_text(
        f"✅ Entry #{entry_id} approved."
        if success
        else "❌ Entry could not be approved."
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
        update.effective_user.id,
    )

    await update.message.reply_text(
        f"❌ Entry #{entry_id} denied."
        if success
        else "❌ Entry could not be denied."
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
        f"💵 Entry: {raffle['entry_price']}\n"
        f"📌 Status: {raffle['status']}\n"
        f"👥 Approved Entries: {len(entries)}\n"
        f"⏳ Time Remaining: "
        f"{format_remaining(raffle['expires_at'])}",
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
        "⚠️ Reroll is available after a raffle has been closed."
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
