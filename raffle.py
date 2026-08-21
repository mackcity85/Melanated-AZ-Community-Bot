# ==========================================================
# Melanated AZ Bot
# raffle.py
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
    RAFFLE_CHAT_ID,
    RAFFLE_DURATION_DAYS,
)

from raffle_database import (
    create_raffle,
    get_active_raffle,
    get_pending_raffle,
    get_raffle,
    approve_raffle,
    cancel_pending_raffle,
    set_raffle_post,
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
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


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
# ADMIN RAFFLE APPROVAL
# ==========================================================

def raffle_approval_keyboard(raffle_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE RAFFLE",
                    callback_data=f"raffleapprove_{raffle_id}",
                ),
                InlineKeyboardButton(
                    "❌ CANCEL",
                    callback_data=f"rafflecancel_{raffle_id}",
                ),
            ]
        ]
    )


# ==========================================================
# MEMBER RAFFLE BUTTONS
# ==========================================================

def raffle_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER RAFFLE",
                    callback_data="raffle_enter",
                )
            ],
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data="raffle_cashapp",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data="raffle_zelle",
                )
            ],
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
                    "✅ APPROVE",
                    callback_data=f"approve_{entry_id}",
                ),
                InlineKeyboardButton(
                    "❌ DENY",
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

        return "Expiration unavailable"

    remaining = expiration - datetime.utcnow()

    if remaining.total_seconds() <= 0:

        return "⏰ EXPIRED"

    days = remaining.days

    hours = remaining.seconds // 3600

    minutes = (
        remaining.seconds % 3600
    ) // 60

    if days > 0:

        return (
            f"{days}d "
            f"{hours}h "
            f"{minutes}m remaining"
        )

    return (
        f"{hours}h "
        f"{minutes}m remaining"
    )


# ==========================================================
# RAFFLE MESSAGE
# ==========================================================

def raffle_message(raffle):

    countdown = format_countdown(
        raffle["expires_at"]
    )

    return (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry Price:** {raffle['price']}\n"
        f"🆔 **Raffle #:** {raffle['id']}\n\n"
        "🔒 **PRIVATE RAFFLE**\n"
        "This raffle is for friends and members of "
        "the Melanated AZ community.\n\n"
        f"⏳ **Time Remaining:** {countdown}\n\n"
        "Tap **ENTER RAFFLE** to create your entry.\n"
        "Then send your payment using Cash App or Zelle.\n\n"
        "⚠️ Entries are not active until payment is "
        "verified and approved by an admin."
    )


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:

        return

    if not is_admin(
        update.effective_user.id
    ):

        if update.message:

            await update.message.reply_text(
                "❌ Admins only."
            )

        return

    if not update.message:

        return

    # ------------------------------------------------------
    # If called from command
    # ------------------------------------------------------

    if context.args:

        text = " ".join(
            context.args
        )

        if "|" not in text:

            await update.message.reply_text(
                "Use this format:\n\n"
                "/startraffle Prize | Entry Price\n\n"
                "Example:\n"
                "/startraffle $100 Cash Prize | $5"
            )

            return

        prize, price = text.split(
            "|",
            1
        )

        prize = prize.strip()
        price = price.strip()

        await create_pending_raffle(
            update,
            context,
            prize,
            price,
        )

        return

    # ------------------------------------------------------
    # Admin panel flow
    # ------------------------------------------------------

    context.user_data[
        "awaiting_raffle_setup"
    ] = True

    await update.message.reply_text(
        "🎟️ **START A NEW RAFFLE**\n\n"
        "Send the raffle information in this format:\n\n"
        "**Prize | Entry Price**\n\n"
        "Example:\n"
        "`$100 Cash Prize | $5`",
        parse_mode="Markdown",
    )


# ==========================================================
# CREATE PENDING RAFFLE
# ==========================================================

async def create_pending_raffle(
    update,
    context,
    prize,
    price,
):

    if not prize or not price:

        await update.message.reply_text(
            "❌ Both the prize and entry price are required."
        )

        return

    existing = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if existing:

        await update.message.reply_text(
            "⚠️ There is already an active or pending raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"💵 Entry Price: {existing['price']}\n"
            f"🆔 Raffle #: {existing['id']}"
        )

        return

    expiration = (
        datetime.utcnow()
        + timedelta(
            days=RAFFLE_DURATION_DAYS
        )
    ).isoformat()

    raffle_id = create_raffle(
        prize,
        price,
        expiration,
    )

    raffle = get_raffle(
        raffle_id
    )

    await update.message.reply_text(
        "📋 **RAFFLE CREATED — AWAITING ADMIN APPROVAL**\n\n"
        f"🎁 Prize: **{prize}**\n"
        f"💵 Entry Price: **{price}**\n"
        f"🆔 Raffle #: **{raffle_id}**\n\n"
        "The raffle has NOT been posted to the group yet.\n"
        "An admin must approve it first.",
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # Prompt all admins
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "🚨 **RAFFLE APPROVAL REQUIRED** 🚨\n\n"
                    "A new raffle is waiting for approval.\n\n"
                    f"🎁 Prize: **{prize}**\n"
                    f"💵 Entry Price: **{price}**\n"
                    f"🆔 Raffle #: **{raffle_id}**\n\n"
                    "Approve it to automatically post "
                    "the raffle in the Melanated AZ group."
                ),
                reply_markup=raffle_approval_keyboard(
                    raffle_id
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Could not notify admin %s",
                admin_id
            )


# ==========================================================
# PROCESS ADMIN RAFFLE APPROVAL
# ==========================================================

async def raffle_approval_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    user = query.from_user

    if not is_admin(user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    try:

        action, raffle_id_text = (
            query.data.split("_", 1)
        )

        raffle_id = int(
            raffle_id_text
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

    if action == "rafflecancel":

        if cancel_pending_raffle(
            raffle_id
        ):

            await query.edit_message_text(
                "❌ Raffle cancelled."
            )

        else:

            await query.message.reply_text(
                "⚠️ This raffle has already been processed."
            )

        return

    if action != "raffleapprove":

        return

    if not approve_raffle(
        raffle_id
    ):

        await query.message.reply_text(
            "⚠️ This raffle has already been approved or cancelled."
        )

        return

    raffle = get_raffle(
        raffle_id
    )

    # ------------------------------------------------------
    # Post to group
    # ------------------------------------------------------

    if not RAFFLE_CHAT_ID:

        await query.message.reply_text(
            "❌ RAFFLE_CHAT_ID is not configured in Render."
        )

        return

    try:

        posted = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=raffle_message(
                raffle
            ),
            reply_markup=raffle_keyboard(),
            parse_mode="Markdown",
        )

        set_raffle_post(
            raffle_id,
            RAFFLE_CHAT_ID,
            posted.message_id,
        )

        await query.edit_message_text(
            "✅ **RAFFLE APPROVED AND POSTED**\n\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry Price: {raffle['price']}\n"
            f"🆔 Raffle #: {raffle_id}",
            parse_mode="Markdown",
        )

        # Start countdown updater
        context.job_queue.run_repeating(
            update_raffle_countdown,
            interval=60,
            first=5,
            data={
                "raffle_id": raffle_id
            },
            name=f"raffle_{raffle_id}",
        )

    except Exception:

        logger.exception(
            "Failed to post raffle to group."
        )

        await query.message.reply_text(
            "❌ Raffle was approved, but I could not post it "
            "to RAFFLE_CHAT_ID.\n\n"
            "Check that the bot is a member/admin of the group "
            "and that RAFFLE_CHAT_ID is correct."
        )


# ==========================================================
# COUNTDOWN UPDATER
# ==========================================================

async def update_raffle_countdown(
    context: ContextTypes.DEFAULT_TYPE
):

    raffle_id = context.job.data[
        "raffle_id"
    ]

    raffle = get_raffle(
        raffle_id
    )

    if not raffle:

        return

    if raffle["status"] != "active":

        context.job.schedule_removal()

        return

    try:

        expiration = datetime.fromisoformat(
            raffle["expires_at"]
        )

        if datetime.utcnow() >= expiration:

            close_raffle(
                raffle_id
            )

            await context.bot.edit_message_text(
                chat_id=raffle["chat_id"],
                message_id=raffle["message_id"],
                text=(
                    "⏰ **MELANATED AZ FRIENDS RAFFLE CLOSED**\n\n"
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Entry Price: **{raffle['price']}**\n"
                    f"🆔 Raffle #: **{raffle_id}**\n\n"
                    "Entries are no longer being accepted."
                ),
                parse_mode="Markdown",
            )

            context.job.schedule_removal()

            return

        await context.bot.edit_message_text(
            chat_id=raffle["chat_id"],
            message_id=raffle["message_id"],
            text=raffle_message(
                raffle
            ),
            reply_markup=raffle_keyboard(),
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Unable to update raffle countdown."
        )


# ==========================================================
# MEMBER ENTER BUTTON
# ==========================================================

async def raffle_enter_button(
    update,
    context
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

    await query.message.reply_text(
        "🎟️ **RAFFLE ENTRY**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry Price: **{raffle['price']}**\n\n"
        "Choose your payment method below.\n\n"
        "Your entry will remain pending until an admin "
        "verifies your payment.",
        reply_markup=raffle_keyboard(),
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

    if query.data == "raffle_zelle":

        payment_method = "Zelle"

    elif query.data == "raffle_cashapp":

        payment_method = "Cash App"

    else:

        payment_method = "Cash App"

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
            f"Send **{raffle['price']}** to:\n"
            f"`{CASHAPP_TAG}`\n"
        )

        if CASHAPP_URL:

            payment_text += (
                f"\n🔗 {CASHAPP_URL}\n"
            )

    else:

        payment_text = (
            "💳 **Zelle**\n\n"
            f"Send **{raffle['price']}** to:\n"
            f"`{ZELLE_PHONE}`\n"
        )

    await query.message.reply_text(
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry Price: **{raffle['price']}**\n"
        f"🆔 Entry #: **{entry_id}**\n"
        f"💳 Method: **{payment_method}**\n\n"
        f"{payment_text}\n"
        "⚠️ Your entry is NOT active until an admin "
        "verifies and approves your payment.",
        parse_mode="Markdown",
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **RAFFLE PAYMENT PENDING**\n\n"
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Amount: **{raffle['price']}**\n"
                    f"🆔 Entry #: **{entry_id}**\n"
                    f"👤 Name: **{get_display_name(user)}**\n"
                    f"🆔 User ID: `{user.id}`\n"
                    f"💳 Payment: **{payment_method}**\n\n"
                    "Verify the payment before approving."
                ),
                reply_markup=admin_entry_keyboard(
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
            query.data.split("_", 1)
        )

        entry_id = int(entry_text)

    except Exception:

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
            query.from_user.id
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry has already been processed."
            )

            return

        await query.edit_message_text(
            f"✅ Entry #{entry_id} approved."
        )

        raffle = get_raffle(
            entry["raffle_id"]
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!** 🎉\n\n"
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Entry Price: **{raffle['price']}**\n"
                    f"🆔 Entry #: **{entry_id}**\n\n"
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
                "⚠️ Entry has already been processed."
            )

            return

        await query.edit_message_text(
            f"❌ Entry #{entry_id} denied."
        )


# ==========================================================
# ADMIN COMMANDS
# ==========================================================

async def enter_raffle(update, context):

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ There is no active raffle."
        )

        return

    await update.message.reply_text(
        raffle_message(raffle),
        reply_markup=raffle_keyboard(),
        parse_mode="Markdown",
    )


async def paid_entry(update, context):

    await enter_raffle(
        update,
        context
    )


async def pending_entries(update, context):

    if not is_admin(
        update.effective_user.id
    ):

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
            f"💳 {entry['payment_method']}",
            reply_markup=admin_entry_keyboard(
                entry["id"]
            ),
            parse_mode="Markdown",
        )


async def raffle_status(update, context):

    raffle = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if not raffle:

        await update.message.reply_text(
            "❌ No active or pending raffle."
        )

        return

    entries = get_approved_entries(
        raffle["id"]
    )

    await update.message.reply_text(
        "🎟️ **RAFFLE STATUS**\n\n"
        f"🆔 Raffle #: **{raffle['id']}**\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry Price: **{raffle['price']}**\n"
        f"📌 Status: **{raffle['status']}**\n"
        f"👥 Approved Entries: **{len(entries)}**\n"
        f"⏳ {format_countdown(raffle['expires_at'])}",
        parse_mode="Markdown",
    )


async def raffle_entries(update, context):

    if not is_admin(
        update.effective_user.id
    ):

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

        lines.append(
            f"#{entry['id']} — "
            f"{entry['display_name']}"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


async def cancel_raffle(update, context):

    if not is_admin(
        update.effective_user.id
    ):

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
        f"🛑 Raffle #{raffle['id']} cancelled/closed."
    )


async def draw_raffle(update, context):

    if not is_admin(
        update.effective_user.id
    ):

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

    await update.message.reply_text(
        "🎉 **RAFFLE WINNER!** 🎉\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"💵 Entry Price: **{raffle['price']}**\n\n"
        f"🏆 Winner: **{winner['display_name']}**\n"
        f"🆔 Entry #: **{winner['id']}**\n\n"
        "Congratulations! 🍀",
        parse_mode="Markdown",
    )


async def reroll_raffle(update, context):

    await update.message.reply_text(
        "Use a new raffle for another drawing."
    )


async def bonus_entry(update, context):

    await update.message.reply_text(
        "ℹ️ Bonus entries are not enabled."
    )


async def remove_raffle_entry(update, context):

    if not is_admin(
        update.effective_user.id
    ):

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
