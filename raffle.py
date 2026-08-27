# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Private raffle system
#
# Matches:
#     raffle_database.py
#
# Features:
# - Admin raffle creation
# - Admin approval
# - Group raffle post
# - Private entry through Telegram deep link
# - Cash App / Zelle payment instructions
# - Admin payment verification
# - Private approval/denial notification
# - Countdown
# - Automatic expiration
# - Winner selection
# - Winner saved to database
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
    get_pending_raffles,
    approve_raffle,
    cancel_raffle as db_cancel_raffle,
    update_raffle_message,
    update_raffle_expiration,
    close_raffle as db_close_raffle,
    set_winner,
    add_raffle_entry,
    get_user_entry,
    get_entry,
    get_raffle_entries,
    get_pending_entries,
    approve_entry,
    deny_entry,
    remove_entry,
    count_entries,
    get_raffle_history,
)

logger = logging.getLogger(__name__)


# ==========================================================
# HELPERS
# ==========================================================

def is_admin(user_id):
    try:
        return int(user_id) in [int(x) for x in ADMIN_IDS]
    except Exception:
        return False


def get_display_name(user):
    if not user:
        return "Unknown User"

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


def format_money(value):
    if value is None:
        return "$0"

    value = str(value)

    if value.startswith("$"):
        return value

    return f"${value}"


# ==========================================================
# COUNTDOWN
# ==========================================================

def format_countdown(expires_at):
    if not expires_at:
        return "Expiration unavailable"

    try:
        expiration = datetime.fromisoformat(expires_at)

    except Exception:
        return "Expiration unavailable"

    remaining = expiration - datetime.utcnow()

    if remaining.total_seconds() <= 0:
        return "⏰ EXPIRED"

    total_seconds = int(remaining.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m remaining"

    if hours > 0:
        return f"{hours}h {minutes}m remaining"

    return f"{minutes}m remaining"


# ==========================================================
# ADMIN RAFFLE APPROVAL KEYBOARD
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
# MEMBER RAFFLE KEYBOARD
# ==========================================================

async def raffle_keyboard(context, raffle_id):

    bot_info = await context.bot.get_me()

    if not bot_info.username:
        raise ValueError("Bot username unavailable.")

    deep_link = (
        f"https://t.me/"
        f"{bot_info.username}"
        f"?start=raffle_{raffle_id}"
    )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER RAFFLE",
                    url=deep_link,
                )
            ]
        ]
    )


# ==========================================================
# PRIVATE PAYMENT KEYBOARD
# ==========================================================

def private_payment_keyboard(raffle_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data=f"raffle_cashapp_{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data=f"raffle_zelle_{raffle_id}",
                )
            ],
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
# GROUP RAFFLE MESSAGE
# ==========================================================

def raffle_message(raffle):

    countdown = format_countdown(
        raffle.get("expires_at")
    )

    entry_price = format_money(
        raffle.get("entry_price")
    )

    return (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry Price:** {entry_price}\n"
        f"🆔 **Raffle #:** {raffle['id']}\n\n"
        "🔒 **PRIVATE RAFFLE**\n"
        "This raffle is for friends and members of "
        "the Melanated AZ community.\n\n"
        f"⏳ **Time Remaining:** {countdown}\n\n"
        "🎟️ Click **ENTER RAFFLE** below.\n\n"
        "Your entry process will continue privately "
        "with the MelanatedAZ Bot.\n\n"
        "⚠️ **Payment must be verified by MelanatedAZ "
        "before your entry becomes active.**"
    )


# ==========================================================
# PRIVATE RAFFLE MESSAGE
# ==========================================================

def private_raffle_message(raffle):

    entry_price = format_money(
        raffle.get("entry_price")
    )

    return (
        "👑 **Hi! I'm the MelanatedAZ Bot.**\n\n"
        "🎟️ **RAFFLE ENTRY**\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry Price:** {entry_price}\n"
        f"🆔 **Raffle #:** {raffle['id']}\n\n"
        "🔒 **Your raffle entry is being handled privately.**\n\n"
        "Choose your payment method below.\n\n"
        "⚠️ **IMPORTANT:**\n"
        "After you submit your payment, "
        "**MelanatedAZ will verify your payment "
        "before your raffle entry is activated.**\n\n"
        "Your entry is **NOT valid or active** until "
        "payment has been verified and approved."
    )


# ==========================================================
# START RAFFLE COMMAND
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    if not is_admin(user.id):

        if update.message:
            await update.message.reply_text(
                "❌ Admins only."
            )

        return

    if update.message and context.args:

        text = " ".join(context.args).strip()

        if "|" not in text:

            await update.message.reply_text(
                "❌ Invalid format.\n\n"
                "Use:\n"
                "/startraffle Prize | Entry Price\n\n"
                "Example:\n"
                "/startraffle $100 Cash Prize | $5"
            )

            return

        prize, price = text.split("|", 1)

        await create_pending_raffle(
            update,
            context,
            prize.strip(),
            price.strip(),
        )

        return

    context.user_data["awaiting_raffle_setup"] = True

    if update.message:

        await update.message.reply_text(
            "🎟️ **START A NEW RAFFLE**\n\n"
            "Send the raffle information in this format:\n\n"
            "**Prize | Entry Price**\n\n"
            "Example:\n"
            "`$100 Cash Prize | $5`\n\n"
            "Type **cancel** to stop.",
            parse_mode="Markdown",
        )


# ==========================================================
# HANDLE RAFFLE SETUP TEXT
# ==========================================================

async def handle_raffle_setup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.message

    if not user or not message:
        return False

    if not is_admin(user.id):
        return False

    if not context.user_data.get(
        "awaiting_raffle_setup"
    ):
        return False

    text = (message.text or "").strip()

    if text.lower() in (
        "cancel",
        "/cancel",
        "cancel raffle",
    ):

        context.user_data.pop(
            "awaiting_raffle_setup",
            None,
        )

        await message.reply_text(
            "❌ Raffle setup cancelled."
        )

        return True

    if "|" not in text:

        await message.reply_text(
            "❌ I couldn't read that.\n\n"
            "Use:\n"
            "**Prize | Entry Price**\n\n"
            "Example:\n"
            "`$100 Cash Prize | $5`",
            parse_mode="Markdown",
        )

        return True

    prize, price = text.split("|", 1)

    prize = prize.strip()
    price = price.strip()

    if not prize or not price:

        await message.reply_text(
            "❌ Both the prize and entry price are required."
        )

        return True

    context.user_data.pop(
        "awaiting_raffle_setup",
        None,
    )

    await create_pending_raffle(
        update,
        context,
        prize,
        price,
    )

    return True


# ==========================================================
# CREATE PENDING RAFFLE
# ==========================================================

async def create_pending_raffle(
    update,
    context,
    prize,
    price,
):

    message = update.message

    if not message:
        return

    existing = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if existing:

        await message.reply_text(
            "⚠️ There is already an active or pending raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"💵 Entry Price: "
            f"{format_money(existing['entry_price'])}\n"
            f"🆔 Raffle #: {existing['id']}"
        )

        return

    expiration = (
        datetime.utcnow()
        + timedelta(days=RAFFLE_DURATION_DAYS)
    ).isoformat()

    user = update.effective_user

    try:

        entry_price = float(
            price.replace("$", "").replace(",", "").strip()
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid entry price.\n\n"
            "Example:\n"
            "`$5`",
            parse_mode="Markdown",
        )

        return

    raffle_id = create_raffle(
        prize=prize,
        entry_price=entry_price,
        created_by=user.id if user else None,
        created_by_username=(
            user.username
            if user and user.username
            else None
        ),
        status="pending",
        expires_at=expiration,
    )

    await message.reply_text(
        "📋 **RAFFLE CREATED — AWAITING ADMIN APPROVAL**\n\n"
        f"🎁 Prize: **{prize}**\n"
        f"💵 Entry Price: **{format_money(entry_price)}**\n"
        f"🆔 Raffle #: **{raffle_id}**\n\n"
        "The raffle has **NOT** been posted to the group yet.\n\n"
        "An admin must approve it first.",
        parse_mode="Markdown",
    )

    approval_text = (
        "🚨 **RAFFLE APPROVAL REQUIRED** 🚨\n\n"
        "A new raffle is waiting for approval.\n\n"
        f"🎁 Prize: **{prize}**\n"
        f"💵 Entry Price: **{format_money(entry_price)}**\n"
        f"🆔 Raffle #: **{raffle_id}**\n\n"
        "Approve it to automatically post "
        "the raffle in the Melanated AZ group."
    )

    approval_markup = raffle_approval_keyboard(
        raffle_id
    )

    approval_sent = False

    # ------------------------------------------------------
    # SEND TO RAFFLE CHAT
    # ------------------------------------------------------

    if RAFFLE_CHAT_ID:

        try:

            await context.bot.send_message(
                chat_id=RAFFLE_CHAT_ID,
                text=approval_text,
                reply_markup=approval_markup,
                parse_mode="Markdown",
            )

            approval_sent = True

        except Exception:

            logger.exception(
                "Could not send raffle approval to raffle chat."
            )

    # ------------------------------------------------------
    # SEND TO ADMINS
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=approval_text,
                reply_markup=approval_markup,
                parse_mode="Markdown",
            )

            approval_sent = True

        except Exception:

            logger.warning(
                "Could not DM admin %s.",
                admin_id,
                exc_info=True,
            )

    if not approval_sent:

        await message.reply_text(
            "⚠️ The raffle was created, but I could not "
            "send the approval controls.\n\n"
            "Check RAFFLE_CHAT_ID and ADMIN_IDS."
        )


# ==========================================================
# PRIVATE /START
# ==========================================================

async def raffle_private_start(
    update,
    context,
):

    message = update.message

    if not message:
        return

    args = context.args

    # ------------------------------------------------------
    # NORMAL START
    # ------------------------------------------------------

    if not args:

        await message.reply_text(
            "👑 **Hi! I'm the MelanatedAZ Bot.**\n\n"
            "I'm here to handle the Melanated AZ Friends "
            "Raffle privately.\n\n"
            "Go back to the Melanated AZ group and tap "
            "**ENTER RAFFLE** to begin."
        )

        return

    payload = args[0]

    if not payload.startswith("raffle_"):

        await message.reply_text(
            "👑 **Hi! I'm the MelanatedAZ Bot.**\n\n"
            "Use the **ENTER RAFFLE** button in the "
            "Melanated AZ group to enter privately."
        )

        return

    try:

        raffle_id = int(
            payload.split("_", 1)[1]
        )

    except Exception:

        await message.reply_text(
            "❌ Invalid raffle link."
        )

        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await message.reply_text(
            "❌ This raffle no longer exists."
        )

        return

    if raffle["status"] != "active":

        await message.reply_text(
            "❌ This raffle is no longer accepting entries."
        )

        return

    # ------------------------------------------------------
    # CHECK EXISTING ENTRY
    # ------------------------------------------------------

    user = update.effective_user

    existing = get_user_entry(
        raffle_id,
        user.id,
    )

    if existing:

        if existing["entry_status"] == "approved":

            await message.reply_text(
                "✅ **YOU ARE ALREADY ENTERED!**\n\n"
                f"🎁 Prize: **{raffle['prize']}**\n"
                f"🆔 Entry #: **{existing['id']}**\n\n"
                "Your payment has already been verified.\n"
                "Good luck! 🍀",
                parse_mode="Markdown",
            )

            return

        if existing["entry_status"] == "pending":

            await message.reply_text(
                "⏳ **YOUR ENTRY IS ALREADY PENDING.**\n\n"
                f"🆔 Entry #: **{existing['id']}**\n\n"
                "MelanatedAZ is waiting to verify your "
                "payment before activating your entry."
            )

            return

    await message.reply_text(
        private_raffle_message(raffle),
        reply_markup=private_payment_keyboard(
            raffle_id
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# RAFFLE APPROVAL CALLBACK
# ==========================================================

async def raffle_approval_button(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(query.from_user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    try:

        await query.answer()

    except Exception:
        pass

    try:

        action, raffle_id_text = query.data.split(
            "_",
            1,
        )

        raffle_id = int(
            raffle_id_text
        )

    except Exception:

        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await query.message.reply_text(
            "❌ Raffle not found."
        )

        return

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    if action == "rafflecancel":

        if raffle["status"] != "pending":

            await query.message.reply_text(
                f"⚠️ Raffle #{raffle_id} is already "
                f"{raffle['status']}."
            )

            return

        db_cancel_raffle(
            raffle_id
        )

        await query.edit_message_text(
            "❌ **RAFFLE CANCELLED**\n\n"
            f"🆔 Raffle #: **{raffle_id}**\n"
            f"🎁 Prize: **{raffle['prize']}**\n"
            f"💵 Entry Price: "
            f"**{format_money(raffle['entry_price'])}**",
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # APPROVE
    # ------------------------------------------------------

    if action != "raffleapprove":
        return

    if raffle["status"] != "pending":

        await query.message.reply_text(
            f"⚠️ Raffle #{raffle_id} is already "
            f"{raffle['status']}."
        )

        return

    if not RAFFLE_CHAT_ID:

        await query.message.reply_text(
            "❌ RAFFLE_CHAT_ID is not configured."
        )

        return

    try:

        # Make raffle active first.
        approve_raffle(
            raffle_id=raffle_id,
        )

        raffle = get_raffle(
            raffle_id
        )

        member_keyboard = await raffle_keyboard(
            context,
            raffle_id,
        )

        posted = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=raffle_message(raffle),
            reply_markup=member_keyboard,
            parse_mode="Markdown",
        )

        update_raffle_message(
            raffle_id,
            RAFFLE_CHAT_ID,
            posted.message_id,
        )

        await query.edit_message_text(
            "✅ **RAFFLE APPROVED AND POSTED**\n\n"
            f"🎁 Prize: **{raffle['prize']}**\n"
            f"💵 Entry Price: "
            f"**{format_money(raffle['entry_price'])}**\n"
            f"🆔 Raffle #: **{raffle_id}**",
            parse_mode="Markdown",
        )

        # --------------------------------------------------
        # START COUNTDOWN JOB
        # --------------------------------------------------

        if context.job_queue:

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
            "Failed to approve/post raffle."
        )

        # If posting failed after approval, leave the raffle
        # active so it can be diagnosed/reposted.

        await query.message.reply_text(
            "❌ The raffle was approved, but I could not "
            "post it to the group.\n\n"
            "Check RAFFLE_CHAT_ID and bot permissions."
        )


# ==========================================================
# LEGACY ENTER CALLBACK
# ==========================================================

async def raffle_enter_button(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    try:

        raffle_id = int(
            query.data.rsplit("_", 1)[1]
        )

    except Exception:

        await query.answer(
            "Invalid raffle.",
            show_alert=True,
        )

        return

    raffle = get_raffle(
        raffle_id
    )

    if not raffle:

        await query.answer(
            "Raffle not found.",
            show_alert=True,
        )

        return

    if raffle["status"] != "active":

        await query.answer(
            "This raffle is no longer active.",
            show_alert=True,
        )

        return

    try:

        bot_info = await context.bot.get_me()

        deep_link = (
            f"https://t.me/"
            f"{bot_info.username}"
            f"?start=raffle_{raffle_id}"
        )

        await query.answer(
            "Tap OK to continue privately.",
            url=deep_link,
        )

    except Exception:

        await query.answer(
            "Please open the MelanatedAZ Bot and press Start.",
            show_alert=True,
        )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        raffle_id = int(
            query.data.rsplit("_", 1)[1]
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

    if raffle["status"] != "active":

        await query.message.reply_text(
            "❌ This raffle is no longer active."
        )

        return

    user = query.from_user

    # ------------------------------------------------------
    # CHECK EXISTING ENTRY
    # ------------------------------------------------------

    existing = get_user_entry(
        raffle_id,
        user.id,
    )

    if existing:

        if existing["entry_status"] == "approved":

            await query.message.reply_text(
                "✅ You are already entered in this raffle.\n\n"
                f"🆔 Entry #: **{existing['id']}**\n\n"
                "Good luck! 🍀",
                parse_mode="Markdown",
            )

            return

        if existing["entry_status"] == "pending":

            await query.message.reply_text(
                "⏳ You already have a pending entry.\n\n"
                f"🆔 Entry #: **{existing['id']}**\n\n"
                "Please complete your payment and wait "
                "for MelanatedAZ to verify it."
            )

            return

    # ------------------------------------------------------
    # PAYMENT METHOD
    # ------------------------------------------------------

    if query.data.startswith("raffle_zelle_"):

        payment_method = "Zelle"

    else:

        payment_method = "Cash App"

    # ------------------------------------------------------
    # CREATE ENTRY
    # ------------------------------------------------------

    entry_id = add_raffle_entry(
        raffle_id=raffle_id,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        payment_method=payment_method,
        payment_status="pending",
        entry_status="pending",
    )

    entry_price = format_money(
        raffle["entry_price"]
    )

    # ------------------------------------------------------
    # PAYMENT INSTRUCTIONS
    # ------------------------------------------------------

    if payment_method == "Cash App":

        payment_text = (
            "💵 **CASH APP**\n\n"
            f"Send **{entry_price}** to:\n"
            f"`{CASHAPP_TAG}`"
        )

        if CASHAPP_URL:

            payment_text += (
                f"\n\n🔗 {CASHAPP_URL}"
            )

    else:

        payment_text = (
            "💳 **ZELLE**\n\n"
            f"Send **{entry_price}** to:\n"
            f"`{ZELLE_PHONE}`"
        )

    # ------------------------------------------------------
    # USER MESSAGE
    # ------------------------------------------------------

    await query.message.reply_text(
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry Price:** {entry_price}\n"
        f"🆔 **Entry #:** {entry_id}\n"
        f"💳 **Payment Method:** {payment_method}\n\n"
        f"{payment_text}\n\n"
        "⚠️ **IMPORTANT**\n\n"
        "After you send your payment, "
        "**MelanatedAZ will verify the payment.**\n\n"
        "Your raffle entry is **NOT active** until "
        "your payment has been verified and approved.\n\n"
        "Please do not submit another entry while "
        "this one is pending.",
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # ADMIN NOTIFICATION
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=(
                    "💰 **RAFFLE PAYMENT PENDING**\n\n"
                    f"🎁 Prize: **{raffle['prize']}**\n"
                    f"💵 Amount: **{entry_price}**\n"
                    f"🆔 Entry #: **{entry_id}**\n\n"
                    f"👤 Name: **{get_display_name(user)}**\n"
                    f"🆔 User ID: `{user.id}`\n"
                    f"💳 Payment: **{payment_method}**\n\n"
                    "⚠️ **VERIFY PAYMENT BEFORE APPROVING.**"
                ),
                reply_markup=admin_entry_keyboard(
                    entry_id
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin %s.",
                admin_id,
            )


# ==========================================================
# ADMIN PAYMENT APPROVAL
# ==========================================================

async def admin_payment_button(
    update,
    context,
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

    try:
        await query.answer()
    except Exception:
        pass

    try:

        action, entry_text = query.data.split(
            "_",
            1,
        )

        entry_id = int(
            entry_text
        )

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

    # ------------------------------------------------------
    # APPROVE
    # ------------------------------------------------------

    if action == "approve":

        if entry["entry_status"] != "pending":

            await query.message.reply_text(
                f"⚠️ Entry #{entry_id} has already been "
                f"processed."
            )

            return

        approve_entry(
            entry_id,
            query.from_user.id,
        )

        await query.edit_message_text(
            f"✅ **ENTRY #{entry_id} APPROVED**\n\n"
            "Payment verified.",
            parse_mode="Markdown",
        )

        raffle = get_raffle(
            entry["raffle_id"]
        )

        if not raffle:
            return

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!** 🎉\n\n"
                    f"🎁 **Prize:** {raffle['prize']}\n"
                    f"💵 **Entry Price:** "
                    f"{format_money(raffle['entry_price'])}\n"
                    f"🆔 **Entry #:** {entry_id}\n\n"
                    "✅ Your payment has been verified by "
                    "**MelanatedAZ**.\n\n"
                    "🎟️ **Your raffle entry is now ACTIVE.**\n\n"
                    "Good luck! 🍀"
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify participant."
            )

        return

    # ------------------------------------------------------
    # DENY
    # ------------------------------------------------------

    if action == "deny":

        if entry["entry_status"] != "pending":

            await query.message.reply_text(
                f"⚠️ Entry #{entry_id} has already been "
                f"processed."
            )

            return

        deny_entry(
            entry_id,
            query.from_user.id,
        )

        await query.edit_message_text(
            f"❌ **ENTRY #{entry_id} DENIED**",
            parse_mode="Markdown",
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "❌ **RAFFLE PAYMENT NOT VERIFIED**\n\n"
                    f"🆔 Entry #: **{entry_id}**\n\n"
                    "MelanatedAZ was unable to verify "
                    "your payment.\n\n"
                    "Your raffle entry was **not activated**."
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify participant."
            )


# ==========================================================
# /ENTER
# ==========================================================

async def enter_raffle(
    update,
    context,
):

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ There is no active raffle right now."
        )

        return

    await update.message.reply_text(
        private_raffle_message(raffle),
        reply_markup=private_payment_keyboard(
            raffle["id"]
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# /PAID
# ==========================================================

async def paid_entry(
    update,
    context,
):

    await enter_raffle(
        update,
        context,
    )


# ==========================================================
# /PENDING
# ==========================================================

async def pending_entries(
    update,
    context,
):

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

        display_name = (
            entry.get("first_name")
            or entry.get("username")
            or str(entry.get("user_id"))
        )

        if entry.get("last_name"):
            display_name += (
                f" {entry['last_name']}"
            )

        await update.message.reply_text(
            "💰 **PENDING PAYMENT**\n\n"
            f"🆔 Entry #: **{entry['id']}**\n"
            f"👤 **{display_name}**\n"
            f"💳 **{entry['payment_method']}**\n"
            f"💵 **Payment Status:** "
            f"{entry['payment_status']}",
            reply_markup=admin_entry_keyboard(
                entry["id"]
            ),
            parse_mode="Markdown",
        )


# ==========================================================
# /RAFFLESTATUS
# ==========================================================

async def raffle_status(
    update,
    context,
):

    raffle = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if not raffle:

        await update.message.reply_text(
            "❌ No active or pending raffle."
        )

        return

    approved_count = count_entries(
        raffle["id"],
        approved_only=True,
    )

    await update.message.reply_text(
        "🎟️ **RAFFLE STATUS**\n\n"
        f"🆔 **Raffle #:** {raffle['id']}\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry Price:** "
        f"{format_money(raffle['entry_price'])}\n"
        f"📌 **Status:** {raffle['status']}\n"
        f"👥 **Approved Entries:** {approved_count}\n"
        f"⏳ **{format_countdown(raffle['expires_at'])}**",
        parse_mode="Markdown",
    )


# ==========================================================
# /ENTRIES
# ==========================================================

async def raffle_entries(
    update,
    context,
):

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

    entries = get_raffle_entries(
        raffle["id"],
        approved_only=True,
    )

    if not entries:

        await update.message.reply_text(
            "🎟️ No approved entries yet."
        )

        return

    lines = [
        "🎟️ **APPROVED ENTRIES**",
        "",
    ]

    for entry in entries:

        name = entry.get("first_name") or ""

        if entry.get("last_name"):
            name += f" {entry['last_name']}"

        if not name.strip():
            name = entry.get(
                "username",
                str(entry["user_id"])
            )

        lines.append(
            f"#{entry['id']} — {name}"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ==========================================================
# /CANCELRAFFLE
# ==========================================================

async def cancel_raffle(
    update,
    context,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    raffle = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if not raffle:

        await update.message.reply_text(
            "❌ No active or pending raffle."
        )

        return

    db_cancel_raffle(
        raffle["id"]
    )

    await update.message.reply_text(
        f"🛑 **RAFFLE #{raffle['id']} CANCELLED**\n\n"
        f"🎁 Prize: **{raffle['prize']}**",
        parse_mode="Markdown",
    )


# ==========================================================
# /DRAW
# ==========================================================

async def draw_raffle(
    update,
    context,
):

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

    entries = get_raffle_entries(
        raffle["id"],
        approved_only=True,
    )

    if not entries:

        await update.message.reply_text(
            "❌ No approved paid entries."
        )

        return

    winner = random.choice(
        entries
    )

    # ------------------------------------------------------
    # SAVE WINNER
    # ------------------------------------------------------

    winner_name = (
        winner.get("first_name")
        or ""
    )

    if winner.get("last_name"):
        winner_name += (
            f" {winner['last_name']}"
        )

    if not winner_name.strip():

        winner_name = (
            winner.get("username")
            or str(winner["user_id"])
        )

    set_winner(
        raffle_id=raffle["id"],
        winner_id=winner["user_id"],
        winner_username=winner.get(
            "username"
        ),
        winner_name=winner_name,
    )

    await update.message.reply_text(
        "🎉 **MELANATED AZ RAFFLE WINNER!** 🎉\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry Price:** "
        f"{format_money(raffle['entry_price'])}\n"
        f"🆔 **Raffle #:** {raffle['id']}\n\n"
        f"🏆 **WINNER:** {winner_name}\n"
        f"🆔 **Entry #:** {winner['id']}\n\n"
        "🎉 Congratulations! 🍀",
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # PRIVATE WINNER NOTIFICATION
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=winner["user_id"],
            text=(
                "🎉🎉 **CONGRATULATIONS!** 🎉🎉\n\n"
                "You won the **Melanated AZ Friends Raffle!**\n\n"
                f"🎁 **Prize:** {raffle['prize']}\n"
                f"🆔 **Raffle #:** {raffle['id']}\n"
                f"🎟️ **Entry #:** {winner['id']}\n\n"
                "👑 MelanatedAZ will contact you "
                "regarding your prize.\n\n"
                "Congratulations! 🍀"
            ),
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Unable to notify raffle winner."
        )


# ==========================================================
# /REROLL
# ==========================================================

async def reroll_raffle(
    update,
    context,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    await update.message.reply_text(
        "ℹ️ The previous raffle has been closed.\n\n"
        "Start a new raffle with /startraffle "
        "for another drawing."
    )


# ==========================================================
# /BONUSENTRY
# ==========================================================

async def bonus_entry(
    update,
    context,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    await update.message.reply_text(
        "ℹ️ Bonus entries are not enabled."
    )


# ==========================================================
# /REMOVEENTRY
# ==========================================================

async def remove_raffle_entry(
    update,
    context,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n"
            "/removeentry ENTRY_ID"
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

    entry = get_entry(
        entry_id
    )

    if not entry:

        await update.message.reply_text(
            "❌ Entry not found."
        )

        return

    remove_entry(
        entry_id
    )

    await update.message.reply_text(
        f"🗑️ Entry #{entry_id} removed."
    )


# ==========================================================
# COUNTDOWN UPDATE
# ==========================================================

async def update_raffle_countdown(
    context
):

    if not context.job:
        return

    raffle_id = context.job.data.get(
        "raffle_id"
    )

    if not raffle_id:
        context.job.schedule_removal()
        return

    raffle = get_raffle(
        raffle_id
    )

    if not raffle:

        context.job.schedule_removal()
        return

    if raffle["status"] != "active":

        context.job.schedule_removal()
        return

    if not raffle.get("expires_at"):

        return

    try:

        expiration = datetime.fromisoformat(
            raffle["expires_at"]
        )

    except Exception:

        logger.exception(
            "Invalid raffle expiration."
        )

        return

    # ------------------------------------------------------
    # EXPIRED
    # ------------------------------------------------------

    if datetime.utcnow() >= expiration:

        db_close_raffle(
            raffle_id
        )

        try:

            if raffle.get("chat_id") and raffle.get(
                "message_id"
            ):

                await context.bot.edit_message_text(
                    chat_id=raffle["chat_id"],
                    message_id=raffle["message_id"],
                    text=(
                        "⏰ **MELANATED AZ FRIENDS RAFFLE CLOSED**\n\n"
                        f"🎁 **Prize:** {raffle['prize']}\n"
                        f"💵 **Entry Price:** "
                        f"{format_money(raffle['entry_price'])}\n"
                        f"🆔 **Raffle #:** {raffle_id}\n\n"
                        "Entries are no longer being accepted.\n\n"
                        "Use the admin drawing command to "
                        "select the winner."
                    ),
                    parse_mode="Markdown",
                )

        except Exception:

            logger.exception(
                "Unable to update expired raffle message."
            )

        context.job.schedule_removal()

        return

    # ------------------------------------------------------
    # UPDATE ACTIVE COUNTDOWN
    # ------------------------------------------------------

    try:

        member_keyboard = await raffle_keyboard(
            context,
            raffle_id,
        )

        await context.bot.edit_message_text(
            chat_id=raffle["chat_id"],
            message_id=raffle["message_id"],
            text=raffle_message(raffle),
            reply_markup=member_keyboard,
            parse_mode="Markdown",
        )

    except Exception as error:

        # Telegram sometimes reports "message is not modified"
        # when nothing actually changed. This is harmless.

        if "message is not modified" not in str(error).lower():

            logger.warning(
                "Unable to update raffle countdown: %s",
                error,
            )
