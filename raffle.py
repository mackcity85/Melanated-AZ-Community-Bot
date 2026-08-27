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
from telegram.error import BadRequest

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
    try:
        return int(user_id) in [int(x) for x in ADMIN_IDS]
    except Exception:
        return False


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
# RAFFLE APPROVAL KEYBOARD
# ==========================================================

def raffle_approval_keyboard(raffle_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "APPROVE RAFFLE",
                    callback_data=f"raffleapprove_{raffle_id}",
                ),
                InlineKeyboardButton(
                    "CANCEL",
                    callback_data=f"rafflecancel_{raffle_id}",
                ),
            ]
        ]
    )


# ==========================================================
# MEMBER REGISTRATION KEYBOARD
# ==========================================================

async def raffle_keyboard(context, raffle_id):
    bot_info = await context.bot.get_me()

    if not bot_info.username:
        raise ValueError("Bot username unavailable.")

    deep_link = (
        f"https://t.me/{bot_info.username}"
        f"?start=raffle_{raffle_id}"
    )

    logger.info(
        "Created raffle registration deep link: %s",
        deep_link,
    )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "REGISTER WITH MELANATED AZ",
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
                    "PAY WITH CASH APP",
                    callback_data=f"raffle_cashapp_{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "PAY WITH ZELLE",
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
                    "APPROVE",
                    callback_data=f"approve_{entry_id}",
                ),
                InlineKeyboardButton(
                    "DENY",
                    callback_data=f"deny_{entry_id}",
                ),
            ]
        ]
    )


# ==========================================================
# COUNTDOWN
# ==========================================================

def format_countdown(expires_at):
    try:
        expiration = datetime.fromisoformat(expires_at)
    except Exception:
        return "Expiration unavailable"

    remaining = expiration - datetime.utcnow()

    if remaining.total_seconds() <= 0:
        return "EXPIRED"

    total_seconds = int(remaining.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m remaining"

    return f"{hours}h {minutes}m remaining"


# ==========================================================
# GROUP RAFFLE MESSAGE
# ==========================================================

def raffle_message(raffle):
    countdown = format_countdown(raffle["expires_at"])

    return (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"

        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['price']}\n"
        f"🆔 Raffle #: {raffle['id']}\n\n"

        "🔒 PRIVATE RAFFLE\n"
        "This raffle is for friends and members "
        "of the Melanated AZ community.\n\n"

        f"⏳ Time Remaining: {countdown}\n\n"

        "📝 HOW TO ENTER\n\n"

        "Click REGISTER WITH MELANATED AZ below.\n\n"

        "Telegram will open the MelanatedAZ Bot "
        "privately.\n\n"

        "If you have never activated the bot before, "
        "Telegram will ask you to tap Start once.\n\n"

        "After activation, your raffle registration "
        "will continue automatically in your private chat.\n\n"

        "🔒 Payment information remains private.\n\n"

        "⚠️ IMPORTANT:\n"
        "Your raffle entry is NOT active until "
        "MelanatedAZ verifies and approves your payment."
    )


# ==========================================================
# PRIVATE RAFFLE MESSAGE
# ==========================================================

def private_raffle_message(raffle):
    return (
        "👑 WELCOME TO MELANATED AZ\n\n"

        "📝 RAFFLE REGISTRATION\n\n"

        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['price']}\n"
        f"🆔 Raffle #: {raffle['id']}\n\n"

        "✅ You are now connected to the "
        "MelanatedAZ Bot.\n\n"

        "🔒 Your raffle registration is being "
        "handled privately.\n\n"

        "Choose your payment method below.\n\n"

        "⚠️ IMPORTANT:\n\n"

        "Your payment will be verified by "
        "MelanatedAZ before your raffle entry "
        "is activated.\n\n"

        "Your entry is NOT valid or active until "
        "payment has been verified and approved "
        "by MelanatedAZ."
    )


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(update, context):
    user = update.effective_user

    if not user:
        return

    if not is_admin(user.id):
        if update.message:
            await update.message.reply_text(
                "Admins only."
            )
        return

    if update.message and context.args:
        text = " ".join(context.args).strip()

        if "|" not in text:
            await update.message.reply_text(
                "Invalid format.\n\n"
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

    text = (
        "🎟️ START A NEW RAFFLE\n\n"

        "Send the raffle information in this format:\n\n"

        "Prize | Entry Price\n\n"

        "Example:\n"
        "$100 Cash Prize | $5"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(text)

    elif update.message:
        await update.message.reply_text(text)


# ==========================================================
# HANDLE RAFFLE SETUP TEXT
# ==========================================================

async def handle_raffle_setup(update, context):
    user = update.effective_user
    message = update.message

    if not user or not message:
        return False

    if not is_admin(user.id):
        return False

    if not context.user_data.get("awaiting_raffle_setup"):
        return False

    if not message.text:
        return False

    text = message.text.strip()

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
            "Raffle setup cancelled."
        )

        return True

    if "|" not in text:
        await message.reply_text(
            "I couldn't read that.\n\n"
            "Use exactly:\n\n"
            "Prize | Entry Price\n\n"
            "Example:\n"
            "$100 Cash Prize | $5"
        )

        return True

    prize, price = text.split("|", 1)

    prize = prize.strip()
    price = price.strip()

    if not prize or not price:
        await message.reply_text(
            "Both the prize and entry price are required.\n\n"
            "Example:\n"
            "$100 Cash Prize | $5"
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

    if not prize or not price:
        await message.reply_text(
            "Both the prize and entry price are required."
        )
        return

    # IMPORTANT:
    # Never create another raffle when one already exists.
    existing = get_active_raffle() or get_pending_raffle()

    if existing:
        await message.reply_text(
            "⚠️ There is already an active or pending raffle.\n\n"
            f"🎁 Prize: {existing['prize']}\n"
            f"💵 Entry Price: {existing['price']}\n"
            f"🆔 Raffle #: {existing['id']}\n"
            f"📌 Status: {existing['status']}"
        )
        return

    expiration = (
        datetime.utcnow()
        + timedelta(days=RAFFLE_DURATION_DAYS)
    ).isoformat()

    raffle_id = create_raffle(
        prize,
        price,
        expiration,
    )

    await message.reply_text(
        "📋 RAFFLE CREATED — AWAITING ADMIN APPROVAL\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry Price: {price}\n"
        f"🆔 Raffle #: {raffle_id}\n\n"
        "The raffle has NOT been posted to the group yet.\n\n"
        "An admin must approve it first."
    )

    approval_text = (
        "🚨 RAFFLE APPROVAL REQUIRED 🚨\n\n"

        "A new raffle is waiting for approval.\n\n"

        f"🎁 Prize: {prize}\n"
        f"💵 Entry Price: {price}\n"
        f"🆔 Raffle #: {raffle_id}\n\n"

        "Approve it to automatically post the raffle "
        "in the Melanated AZ group."
    )

    approval_markup = raffle_approval_keyboard(
        raffle_id
    )

    approval_sent = False

    if RAFFLE_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=RAFFLE_CHAT_ID,
                text=approval_text,
                reply_markup=approval_markup,
            )

            approval_sent = True

            logger.info(
                "Raffle approval message sent to raffle chat."
            )

        except Exception:
            logger.exception(
                "Could not send raffle approval to raffle chat."
            )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=approval_text,
                reply_markup=approval_markup,
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
            "Check RAFFLE_CHAT_ID and make sure the bot "
            "can send messages there."
        )


# ==========================================================
# PRIVATE START / REGISTRATION
# ==========================================================

async def raffle_private_start(update, context):
    message = update.message

    if not message:
        return

    user = update.effective_user

    if not user:
        return

    args = context.args or []

    if not args:
        await message.reply_text(
            "👑 WELCOME TO MELANATED AZ\n\n"

            "I'm the MelanatedAZ Bot.\n\n"

            "To register for a raffle, use the "
            "REGISTER WITH MELANATED AZ button "
            "posted in the Melanated AZ group."
        )
        return

    payload = args[0].strip()

    logger.info(
        "Raffle start payload received from user %s: %s",
        user.id,
        payload,
    )

    if not payload.startswith("raffle_"):
        await message.reply_text(
            "👑 WELCOME TO MELANATED AZ\n\n"

            "I'm the MelanatedAZ Bot.\n\n"

            "Please use the REGISTER WITH MELANATED AZ "
            "button from the active raffle in the group."
        )
        return

    try:
        raffle_id = int(
            payload.split("_", 1)[1]
        )

    except Exception:
        await message.reply_text(
            "Invalid raffle registration link."
        )
        return

    raffle = get_raffle(raffle_id)

    if not raffle:
        await message.reply_text(
            "This raffle no longer exists."
        )
        return

    if raffle["status"] != "active":
        await message.reply_text(
            "This raffle is no longer accepting registrations."
        )
        return

    await message.reply_text(
        private_raffle_message(raffle),
        reply_markup=private_payment_keyboard(raffle_id),
    )

    logger.info(
        "Raffle registration displayed to user %s for raffle %s",
        user.id,
        raffle_id,
    )


# ==========================================================
# RAFFLE APPROVAL BUTTON
# ==========================================================

async def raffle_approval_button(update, context):
    query = update.callback_query

    if not query:
        return

    logger.info(
        "Raffle approval callback received: %s",
        query.data,
    )

    if not is_admin(query.from_user.id):
        await query.answer(
            "Not authorized.",
            show_alert=True,
        )
        return

    await query.answer()

    try:
        action, raffle_id_text = query.data.split("_", 1)
        raffle_id = int(raffle_id_text)

    except Exception:
        await query.answer(
            "Invalid raffle.",
            show_alert=True,
        )
        return

    raffle = get_raffle(raffle_id)

    if not raffle:
        await query.answer(
            "Raffle not found.",
            show_alert=True,
        )
        return

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    if action == "rafflecancel":

        if raffle["status"] != "pending":
            await query.message.reply_text(
                f"Raffle #{raffle_id} is already "
                f"{raffle['status']}."
            )
            return

        if cancel_pending_raffle(raffle_id):

            await query.edit_message_text(
                "❌ RAFFLE CANCELLED\n\n"
                f"Raffle #: {raffle_id}\n"
                f"Prize: {raffle['prize']}\n"
                f"Entry Price: {raffle['price']}"
            )

        else:
            await query.message.reply_text(
                "⚠️ This raffle has already been processed."
            )

        return

    # ------------------------------------------------------
    # APPROVE
    # ------------------------------------------------------

    if action != "raffleapprove":
        return

    if raffle["status"] != "pending":
        await query.message.reply_text(
            f"Raffle #{raffle_id} is already "
            f"{raffle['status']}."
        )
        return

    if not approve_raffle(raffle_id):
        await query.message.reply_text(
            "⚠️ This raffle has already been processed."
        )
        return

    raffle = get_raffle(raffle_id)

    if not raffle:
        await query.message.reply_text(
            "❌ Raffle could not be loaded after approval."
        )
        return

    if not RAFFLE_CHAT_ID:
        await query.message.reply_text(
            "❌ RAFFLE_CHAT_ID is not configured."
        )
        return

    try:
        member_keyboard = await raffle_keyboard(
            context,
            raffle_id,
        )

        posted = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=raffle_message(raffle),
            reply_markup=member_keyboard,
        )

        set_raffle_post(
            raffle_id,
            RAFFLE_CHAT_ID,
            posted.message_id,
        )

        try:
            await query.edit_message_text(
                "✅ RAFFLE APPROVED AND POSTED\n\n"
                f"Prize: {raffle['prize']}\n"
                f"Entry Price: {raffle['price']}\n"
                f"Raffle #: {raffle_id}"
            )

        except Exception:
            logger.warning(
                "Could not edit admin approval message.",
                exc_info=True,
            )

        # Start countdown after 5 seconds.
        if context.job_queue:

            job_name = f"raffle_{raffle_id}"

            for job in context.job_queue.get_jobs_by_name(
                job_name
            ):
                job.schedule_removal()

            context.job_queue.run_repeating(
                update_raffle_countdown,
                interval=60,
                first=5,
                data={"raffle_id": raffle_id},
                name=job_name,
            )

        logger.info(
            "Raffle %s approved and posted.",
            raffle_id,
        )

    except Exception:
        logger.exception(
            "Failed to post raffle."
        )

        await query.message.reply_text(
            "❌ Raffle was approved, but I could not post it.\n\n"
            "Check RAFFLE_CHAT_ID and make sure the bot "
            "can send messages there."
        )


# ==========================================================
# LEGACY ENTER BUTTON
# ==========================================================

async def raffle_enter_button(update, context):
    query = update.callback_query

    if not query:
        return

    logger.info(
        "Legacy ENTER RAFFLE callback received: %s",
        query.data,
    )

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

    raffle = get_raffle(raffle_id)

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

        if not bot_info.username:
            raise ValueError(
                "Bot username unavailable."
            )

        deep_link = (
            f"https://t.me/{bot_info.username}"
            f"?start=raffle_{raffle_id}"
        )

        await query.answer(
            "Opening MelanatedAZ registration...",
            url=deep_link,
        )

    except Exception:
        logger.exception(
            "Unable to create raffle deep link."
        )

        await query.answer(
            "Please open the MelanatedAZ Bot.",
            show_alert=True,
        )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(update, context):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:
        raffle_id = int(
            query.data.rsplit("_", 1)[1]
        )

    except Exception:
        await query.message.reply_text(
            "Invalid raffle."
        )
        return

    raffle = get_raffle(raffle_id)

    if not raffle:
        await query.message.reply_text(
            "Raffle not found."
        )
        return

    if raffle["status"] != "active":
        await query.message.reply_text(
            "This raffle is no longer active."
        )
        return

    user = query.from_user

    if query.data.startswith("raffle_zelle_"):
        payment_method = "Zelle"
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
            "💵 Cash App\n\n"
            f"Send {raffle['price']} to:\n"
            f"{CASHAPP_TAG}"
        )

        if CASHAPP_URL:
            payment_text += (
                f"\n\n{CASHAPP_URL}"
            )

    else:

        payment_text = (
            "💳 Zelle\n\n"
            f"Send {raffle['price']} to:\n"
            f"{ZELLE_PHONE}"
        )

    await query.message.reply_text(
        "🎟️ ENTRY CREATED\n\n"

        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['price']}\n"
        f"🆔 Entry #: {entry_id}\n"
        f"💳 Payment Method: {payment_method}\n\n"

        f"{payment_text}\n\n"

        "⚠️ IMPORTANT:\n\n"

        "Your payment will be verified by "
        "MelanatedAZ before your raffle entry "
        "is activated.\n\n"

        "Your entry is NOT valid or active until "
        "payment has been verified and approved."
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),

                text=(
                    "💰 RAFFLE PAYMENT PENDING\n\n"

                    f"🎁 Prize: {raffle['prize']}\n"
                    f"💵 Amount: {raffle['price']}\n"
                    f"🆔 Entry #: {entry_id}\n"
                    f"👤 Name: {get_display_name(user)}\n"
                    f"🆔 User ID: {user.id}\n"
                    f"💳 Payment: {payment_method}\n\n"

                    "⚠️ Verify the payment before approving."
                ),

                reply_markup=admin_entry_keyboard(
                    entry_id
                ),
            )

        except Exception:
            logger.exception(
                "Unable to notify admin %s.",
                admin_id,
            )


# ==========================================================
# ADMIN PAYMENT APPROVAL
# ==========================================================

async def admin_payment_button(update, context):
    query = update.callback_query

    if not query:
        return

    if not is_admin(query.from_user.id):
        await query.answer(
            "Not authorized.",
            show_alert=True,
        )
        return

    await query.answer()

    try:
        action, entry_text = query.data.split("_", 1)
        entry_id = int(entry_text)

    except Exception:
        await query.answer(
            "Invalid entry.",
            show_alert=True,
        )
        return

    entry = get_entry(entry_id)

    if not entry:
        await query.message.reply_text(
            "Entry not found."
        )
        return

    # ------------------------------------------------------
    # APPROVE PAYMENT
    # ------------------------------------------------------

    if action == "approve":

        if not approve_entry(
            entry_id,
            query.from_user.id,
        ):
            await query.message.reply_text(
                "⚠️ Entry has already been processed."
            )
            return

        try:
            await query.edit_message_text(
                f"✅ Entry #{entry_id} approved."
            )

        except Exception:
            logger.warning(
                "Unable to edit admin payment message.",
                exc_info=True,
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
                    "🎉 RAFFLE ENTRY APPROVED! 🎉\n\n"

                    f"🎁 Prize: {raffle['prize']}\n"
                    f"💵 Entry Price: {raffle['price']}\n"
                    f"🆔 Entry #: {entry_id}\n\n"

                    "✅ Your payment has been verified "
                    "by MelanatedAZ.\n\n"

                    "Your raffle entry is now active.\n\n"

                    "Good luck! 🍀"
                ),
            )

        except Exception:
            logger.exception(
                "Unable to notify participant."
            )

        return

    # ------------------------------------------------------
    # DENY PAYMENT
    # ------------------------------------------------------

    if action == "deny":

        if not deny_entry(
            entry_id,
            query.from_user.id,
        ):
            await query.message.reply_text(
                "⚠️ Entry has already been processed."
            )
            return

        try:

            await query.edit_message_text(
                f"❌ Entry #{entry_id} denied."
            )

        except Exception:
            logger.warning(
                "Unable to edit admin payment message.",
                exc_info=True,
            )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],

                text=(
                    "❌ RAFFLE PAYMENT NOT VERIFIED\n\n"

                    f"🆔 Entry #: {entry_id}\n\n"

                    "MelanatedAZ was unable to verify "
                    "your payment, so your raffle entry "
                    "was not activated."
                ),
            )

        except Exception:
            logger.exception(
                "Unable to notify participant."
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
            "❌ There is no active raffle."
        )
        return

    await update.message.reply_text(
        private_raffle_message(raffle),
        reply_markup=private_payment_keyboard(
            raffle["id"]
        ),
    )


# ==========================================================
# PAID ENTRY
# ==========================================================

async def paid_entry(update, context):
    await enter_raffle(update, context)


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(update, context):
    if not is_admin(update.effective_user.id):
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

            f"🆔 Entry #: {entry['id']}\n"
            f"👤 {entry['display_name']}\n"
            f"💳 {entry['payment_method']}",

            reply_markup=admin_entry_keyboard(
                entry["id"]
            ),
        )


# ==========================================================
# RAFFLE STATUS
# ==========================================================

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
        "🎟️ RAFFLE STATUS\n\n"

        f"🆔 Raffle #: {raffle['id']}\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['price']}\n"
        f"📌 Status: {raffle['status']}\n"
        f"👥 Approved Entries: {len(entries)}\n"
        f"⏳ {format_countdown(raffle['expires_at'])}"
    )


# ==========================================================
# RAFFLE ENTRIES
# ==========================================================

async def raffle_entries(update, context):
    if not is_admin(update.effective_user.id):
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
        "",
    ]

    for entry in entries:
        lines.append(
            f"#{entry['id']} — {entry['display_name']}"
        )

    await update.message.reply_text(
        "\n".join(lines)
    )


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle(update, context):
    if not is_admin(update.effective_user.id):
        return

    raffle = get_active_raffle()

    if raffle:

        if close_raffle(raffle["id"]):

            await update.message.reply_text(
                f"🛑 Raffle #{raffle['id']} cancelled/closed."
            )

        else:

            await update.message.reply_text(
                "⚠️ Raffle could not be closed."
            )

        return

    raffle = get_pending_raffle()

    if raffle:

        if cancel_pending_raffle(raffle["id"]):

            await update.message.reply_text(
                f"🛑 Pending raffle #{raffle['id']} cancelled."
            )

        else:

            await update.message.reply_text(
                "⚠️ Pending raffle could not be cancelled."
            )

        return

    await update.message.reply_text(
        "❌ No active or pending raffle."
    )


# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(update, context):
    if not is_admin(update.effective_user.id):
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
        "🎉 RAFFLE WINNER! 🎉\n\n"

        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['price']}\n\n"

        f"🏆 Winner: {winner['display_name']}\n"
        f"🆔 Entry #: {winner['id']}\n\n"

        "Congratulations! 🍀"
    )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(update, context):
    await update.message.reply_text(
        "Use a new raffle for another drawing."
    )


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(update, context):
    await update.message.reply_text(
        "ℹ️ Bonus entries are not enabled."
    )


# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(update, context):
    if not is_admin(update.effective_user.id):
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

    if remove_entry(entry_id):

        await update.message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )


# ==========================================================
# RECOVER EXISTING RAFFLE
#
# IMPORTANT:
# This function NEVER creates a new raffle.
#
# It uses the existing raffle database record.
# ==========================================================

async def recover_existing_raffle(
    context,
    raffle,
):
    raffle_id = raffle["id"]

    if not RAFFLE_CHAT_ID:
        logger.error(
            "Cannot recover raffle %s: "
            "RAFFLE_CHAT_ID is not configured.",
            raffle_id,
        )
        return None

    logger.info(
        "Recovering existing raffle %s.",
        raffle_id,
    )

    member_keyboard = await raffle_keyboard(
        context,
        raffle_id,
    )

    posted = await context.bot.send_message(
        chat_id=RAFFLE_CHAT_ID,
        text=raffle_message(raffle),
        reply_markup=member_keyboard,
    )

    set_raffle_post(
        raffle_id,
        RAFFLE_CHAT_ID,
        posted.message_id,
    )

    logger.info(
        "Existing raffle %s recovered. "
        "New Telegram message ID: %s",
        raffle_id,
        posted.message_id,
    )

    return posted


# ==========================================================
# CHECK WHETHER TELEGRAM MESSAGE STILL EXISTS
# ==========================================================

async def verify_raffle_message(
    context,
    raffle,
):
    chat_id = raffle.get("chat_id")
    message_id = raffle.get("message_id")

    if not chat_id or not message_id:
        return False

    try:
        await context.bot.forward_message(
            chat_id=chat_id,
            from_chat_id=chat_id,
            message_id=message_id,
        )

        return True

    except Exception:
        return False


# ==========================================================
# COUNTDOWN UPDATE
#
# Existing raffle is ALWAYS loaded from database.
#
# No new raffle is created here.
# ==========================================================

async def update_raffle_countdown(context):
    if not context.job:
        return

    job_data = context.job.data or {}

    raffle_id = job_data.get("raffle_id")

    if not raffle_id:
        context.job.schedule_removal()
        return

    raffle = get_raffle(raffle_id)

    if not raffle:
        logger.warning(
            "Raffle %s no longer exists. "
            "Removing countdown job.",
            raffle_id,
        )

        context.job.schedule_removal()
        return

    if raffle["status"] != "active":
        logger.info(
            "Raffle %s is no longer active. "
            "Removing countdown job.",
            raffle_id,
        )

        context.job.schedule_removal()
        return

    try:

        expiration = datetime.fromisoformat(
            raffle["expires_at"]
        )

        # --------------------------------------------------
        # EXPIRED
        # --------------------------------------------------

        if datetime.utcnow() >= expiration:

            close_raffle(raffle_id)

            chat_id = raffle.get("chat_id")
            message_id = raffle.get("message_id")

            if chat_id and message_id:

                try:

                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,

                        text=(
                            "⏰ MELANATED AZ FRIENDS "
                            "RAFFLE CLOSED\n\n"

                            f"🎁 Prize: {raffle['prize']}\n"
                            f"💵 Entry Price: {raffle['price']}\n"
                            f"🆔 Raffle #: {raffle_id}\n\n"

                            "Entries are no longer being accepted."
                        ),
                    )

                except Exception:
                    logger.warning(
                        "Could not update expired raffle "
                        "message %s.",
                        raffle_id,
                        exc_info=True,
                    )

            context.job.schedule_removal()
            return

        # --------------------------------------------------
        # NO SAVED TELEGRAM POST
        # --------------------------------------------------

        if not raffle.get("chat_id") or not raffle.get(
            "message_id"
        ):

            logger.warning(
                "Raffle %s has no stored Telegram "
                "message information. Recovering it.",
                raffle_id,
            )

            try:

                await recover_existing_raffle(
                    context,
                    raffle,
                )

            except Exception:
                logger.exception(
                    "Unable to recover raffle %s.",
                    raffle_id,
                )

            return

        # --------------------------------------------------
        # UPDATE EXISTING POST
        # --------------------------------------------------

        member_keyboard = await raffle_keyboard(
            context,
            raffle_id,
        )

        try:

            await context.bot.edit_message_text(
                chat_id=raffle["chat_id"],
                message_id=raffle["message_id"],
                text=raffle_message(raffle),
                reply_markup=member_keyboard,
            )

            logger.debug(
                "Updated countdown for raffle %s.",
                raffle_id,
            )

            return

        except BadRequest as error:

            error_text = str(error).lower()

            if (
                "message to edit not found" in error_text
                or "message not found" in error_text
                or "message can't be edited" in error_text
                or "message is not modified" in error_text
            ):

                if "message is not modified" in error_text:
                    logger.debug(
                        "Raffle %s message already contains "
                        "current countdown.",
                        raffle_id,
                    )
                    return

                logger.warning(
                    "Telegram message for raffle %s is "
                    "unavailable. Reposting SAME raffle.",
                    raffle_id,
                )

                try:

                    await recover_existing_raffle(
                        context,
                        raffle,
                    )

                except Exception:
                    logger.exception(
                        "Unable to repost existing raffle %s.",
                        raffle_id,
                    )

                return

            logger.warning(
                "Telegram rejected countdown update "
                "for raffle %s: %s",
                raffle_id,
                error,
            )

            return

        except Exception:

            logger.exception(
                "Unexpected error updating raffle %s.",
                raffle_id,
            )

            return

    except Exception:

        logger.exception(
            "Unable to update raffle countdown for raffle %s.",
            raffle_id,
        )


# ==========================================================
# START COUNTDOWN FOR EXISTING RAFFLE
#
# This does NOT create a raffle.
# ==========================================================

async def recover_active_raffle_job(context):
    raffle = get_active_raffle()

    if not raffle:
        logger.info(
            "No active raffle found during startup recovery."
        )
        return

    raffle_id = raffle["id"]

    logger.info(
        "Found existing active raffle %s during startup recovery.",
        raffle_id,
    )

    # ------------------------------------------------------
    # Check expiration.
    # ------------------------------------------------------

    try:

        expiration = datetime.fromisoformat(
            raffle["expires_at"]
        )

        if datetime.utcnow() >= expiration:

            logger.info(
                "Existing raffle %s is already expired.",
                raffle_id,
            )

            close_raffle(raffle_id)
            return

    except Exception:

        logger.exception(
            "Unable to validate expiration for raffle %s.",
            raffle_id,
        )

        return

    if not context.job_queue:
        logger.warning(
            "Job queue unavailable. "
            "Cannot start raffle countdown."
        )
        return

    # ------------------------------------------------------
    # Prevent duplicate countdown jobs.
    # ------------------------------------------------------

    job_name = f"raffle_{raffle_id}"

    existing_jobs = context.job_queue.get_jobs_by_name(
        job_name
    )

    if existing_jobs:

        logger.info(
            "Countdown job already exists for raffle %s.",
            raffle_id,
        )

        return

    # ------------------------------------------------------
    # IMPORTANT:
    # Recover the existing Telegram post immediately
    # if there is no saved message information.
    # ------------------------------------------------------

    if (
        not raffle.get("chat_id")
        or not raffle.get("message_id")
    ):

        logger.warning(
            "Existing raffle %s has no saved Telegram "
            "message ID. Reposting SAME raffle.",
            raffle_id,
        )

        try:

            await recover_existing_raffle(
                context,
                raffle,
            )

            raffle = get_raffle(
                raffle_id
            )

        except Exception:

            logger.exception(
                "Unable to recover existing raffle %s.",
                raffle_id,
            )

    # ------------------------------------------------------
    # Start countdown.
    #
    # 5-second startup delay, NOT 5 minutes.
    # ------------------------------------------------------

    context.job_queue.run_repeating(
        update_raffle_countdown,
        interval=60,
        first=5,
        data={
            "raffle_id": raffle_id
        },
        name=job_name,
    )

    logger.info(
        "Recovered countdown job for existing raffle %s. "
        "First update in 5 seconds.",
        raffle_id,
    )
