# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Private paid raffle between friends
# 7-day automatic expiration
# Admin approval required before posting
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
    approve_raffle,
    set_raffle_posted_message,
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


def get_display_name(user) -> str:

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


# ==========================================================
# RAFFLE ENTRY KEYBOARD
# ==========================================================

def raffle_keyboard():

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


# ==========================================================
# ADMIN RAFFLE APPROVAL KEYBOARD
# ==========================================================

def raffle_approval_keyboard(raffle_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve & Post",
                    callback_data=f"raffleapprove_{raffle_id}",
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f"raffaldeny_{raffle_id}",
                ),
            ]
        ]
    )


# ==========================================================
# ADMIN ENTRY KEYBOARD
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
                ),
            ]
        ]
    )


# ==========================================================
# FORMAT COUNTDOWN
# ==========================================================

def format_countdown(expires_at):

    try:

        expiration = datetime.fromisoformat(
            expires_at
        )

    except Exception:

        return "Unknown"

    remaining = (
        expiration -
        datetime.utcnow()
    )

    if remaining.total_seconds() <= 0:
        return "EXPIRED"

    total_seconds = int(
        remaining.total_seconds()
    )

    days = total_seconds // 86400

    hours = (
        total_seconds % 86400
    ) // 3600

    minutes = (
        total_seconds % 3600
    ) // 60

    return (
        f"{days}d "
        f"{hours}h "
        f"{minutes}m"
    )


# ==========================================================
# RAFFLE POST TEXT
# ==========================================================

def raffle_post_text(raffle):

    countdown = format_countdown(
        raffle["expires_at"]
    )

    return (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {raffle['entry_price']}\n\n"
        f"⏳ **Ends in:** {countdown}\n\n"
        "🖤 Private raffle between friends.\n"
        "💰 Payment is required for entry.\n\n"
        "Click **Enter Raffle** below to participate."
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

    # ------------------------------------------------------
    # Parse raffle
    # ------------------------------------------------------

    raw = " ".join(
        context.args
    ).strip()

    parts = [
        part.strip()
        for part in raw.split("|")
    ]

    if len(parts) != 2:

        await update.message.reply_text(
            "❌ Invalid raffle format.\n\n"
            "Use:\n"
            "/startraffle PRIZE | ENTRY PRICE\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | $10 Entry"
        )

        return

    prize = parts[0]
    entry_price = parts[1]

    # ------------------------------------------------------
    # Check existing raffle
    # ------------------------------------------------------

    active = get_active_raffle()

    if active:

        await update.message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {active['prize']}\n"
            f"💵 Entry: {active['entry_price']}\n"
            f"🆔 Raffle #: {active['id']}"
        )

        return

    pending = get_pending_raffle()

    if pending:

        await update.message.reply_text(
            "⚠️ There is already a raffle waiting "
            "for admin approval.\n\n"
            f"🎁 Prize: {pending['prize']}\n"
            f"💵 Entry: {pending['entry_price']}\n"
            f"🆔 Raffle #: {pending['id']}"
        )

        return

    # ------------------------------------------------------
    # Create raffle
    # ------------------------------------------------------

    raffle_id = create_raffle(
        prize=prize,
        entry_price=entry_price,
        chat_id=update.effective_chat.id,
    )

    # ------------------------------------------------------
    # Admin approval request
    # ------------------------------------------------------

    await update.message.reply_text(
        "🎟️ **RAFFLE CREATED — APPROVAL REQUIRED**\n\n"
        f"🎁 **Prize:** {prize}\n"
        f"💵 **Entry:** {entry_price}\n"
        f"🆔 **Raffle #:** {raffle_id}\n\n"
        "This raffle has NOT been posted yet.\n\n"
        "An admin must approve it before it is posted "
        "to the group.\n\n"
        "⏳ The 7-day countdown will begin when approved.",
        reply_markup=raffle_approval_keyboard(
            raffle_id
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# ADMIN RAFFLE APPROVAL BUTTON
# ==========================================================

async def raffle_approval_button(
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

        if data.startswith("raffleapprove_"):

            raffle_id = int(
                data.split("_", 1)[1]
            )

            action = "approve"

        elif data.startswith("raffaldeny_"):

            raffle_id = int(
                data.split("_", 1)[1]
            )

            action = "deny"

        else:

            return

    except (ValueError, AttributeError):

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

    # ======================================================
    # DENY
    # ======================================================

    if action == "deny":

        success = close_raffle(
            raffle_id
        )

        if success:

            await query.edit_message_text(
                "❌ **RAFFLE CANCELLED**\n\n"
                f"🆔 Raffle #: {raffle_id}",
                parse_mode="Markdown",
            )

        else:

            await query.message.reply_text(
                "⚠️ Raffle could not be cancelled."
            )

        return

    # ======================================================
    # APPROVE
    # ======================================================

    success = approve_raffle(
        raffle_id,
        admin.id,
    )

    if not success:

        await query.message.reply_text(
            "⚠️ Raffle could not be approved.\n"
            "It may already have been processed."
        )

        return

    raffle = get_raffle(
        raffle_id
    )

    # ------------------------------------------------------
    # Post raffle to group
    # ------------------------------------------------------

    try:

        posted = await context.bot.send_message(
            chat_id=raffle["chat_id"],
            text=raffle_post_text(
                raffle
            ),
            reply_markup=raffle_keyboard(),
            parse_mode="Markdown",
        )

        set_raffle_posted_message(
            raffle_id,
            posted.message_id
        )

        await query.edit_message_text(
            "✅ **RAFFLE APPROVED & POSTED**\n\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry: {raffle['entry_price']}\n"
            f"🆔 Raffle #: {raffle_id}\n\n"
            "⏳ The 7-day countdown has started.",
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Unable to post approved raffle."
        )

        await query.message.reply_text(
            "⚠️ Raffle was approved, but I could not "
            "post it to the group."
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
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {raffle['entry_price']}\n"
        f"⏳ Ends in: "
        f"{format_countdown(raffle['expires_at'])}\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown",
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
            "⏰ This raffle has expired or is no longer active."
        )

        return

    await query.message.reply_text(
        "🎟️ **Enter the raffle**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {raffle['entry_price']}\n"
        f"⏳ Ends in: "
        f"{format_countdown(raffle['expires_at'])}\n\n"
        "Choose your payment method:",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# PAID ENTRY COMMAND
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await enter_raffle(
        update,
        context
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
            "⏰ This raffle has expired or is no longer active."
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
            "⚠️ You already have a pending or approved "
            "entry for this raffle, or the raffle has expired."
        )

        return

    # ======================================================
    # PAYMENT INSTRUCTIONS
    # ======================================================

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
        f"💵 Entry: {raffle['entry_price']}\n"
        f"🆔 Entry #: {entry_id}\n"
        f"💳 Method: {payment_method}\n\n"
        f"{payment_text}\n"
        "Once payment is sent, an admin will verify it "
        "and approve your entry.\n\n"
        "⚠️ Your entry is NOT active until approved.",
        parse_mode="Markdown",
    )

    # ======================================================
    # NOTIFY ADMINS
    # ======================================================

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **RAFFLE PAYMENT PENDING**\n\n"
                    f"🎁 Prize: {raffle['prize']}\n"
                    f"💵 Entry: {raffle['entry_price']}\n"
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

        action, entry_text = data.split(
            "_",
            1
        )

        entry_id = int(
            entry_text
        )

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

    if action == "approve":

        success = approve_entry(
            entry_id,
            admin.id,
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry could not be approved."
            )

            return

        raffle = get_raffle(
            entry["raffle_id"]
        )

        await query.message.reply_text(
            f"✅ Entry #{entry_id} approved."
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!**\n\n"
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Entry: **{raffle['entry_price']}**\n\n"
                    f"🆔 Entry #: {entry_id}\n"
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
            admin.id
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry could not be denied."
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
                    "Please contact an admin if you believe "
                    "this was an error."
                )
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
            "✅ No pending raffle entries."
        )

        return

    for entry in entries:

        text = (
            "💰 **PENDING RAFFLE ENTRY**\n\n"
            f"🆔 Entry #: {entry['id']}\n"
            f"👤 Name: {entry['display_name']}\n"
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

    raffle = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return

    entries = get_approved_entries(
        raffle["id"]
    )

    status_text = (
        "🎟️ **RAFFLE STATUS**\n\n"
        f"🆔 Raffle #: {raffle['id']}\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {raffle['entry_price']}\n"
        f"📌 Status: {raffle['status']}\n"
        f"👥 Approved Entries: {len(entries)}"
    )

    if raffle["expires_at"]:

        status_text += (
            f"\n⏳ Ends in: "
            f"{format_countdown(raffle['expires_at'])}"
        )

    await update.message.reply_text(
        status_text,
        parse_mode="Markdown"
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
        parse_mode="Markdown"
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
        parse_mode="Markdown"
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
        "⚠️ Reroll is not available until a new raffle "
        "has been created."
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
        "ℹ️ Bonus entries are not enabled in this "
        "database version."
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

    if success:

        await update.message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )
