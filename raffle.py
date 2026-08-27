# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Persistent raffle system
# Python-Telegram-Bot v21+
#
# Works with:
#   raffle_database.py
#   admin.py
#   bot.py
#
# Features:
#   /startraffle
#   /raffle
#   /enterraffle
#   /paid
#   /rafflestatus
#   /raffleentries
#   /pending
#   /approveentry
#   /denyentry
#   /cancelraffle
#   /draw
#   /reroll
#   /bonusentry
#   /removeentry
#
# Supports:
#   Cash App
#   Zelle
#   Private entry flow
#   Admin payment verification
#   Persistent SQLite storage
#   Duplicate-entry protection
#   Countdown
#   Winner selection
#   Raffle post buttons
# ==========================================================

import logging
import os
import random
from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from raffle_database import (
    create_raffle,
    get_raffle,
    get_active_raffle,
    get_pending_raffle,
    approve_raffle,
    cancel_pending_raffle,
    set_raffle_post,
    close_raffle,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
)


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# CONFIG
# ==========================================================

RAFFLE_CHAT_ID = int(
    os.environ.get(
        "RAFFLE_CHAT_ID",
        "-1002697105809",
    )
)

RAFFLE_DURATION_DAYS = int(
    os.environ.get(
        "RAFFLE_DURATION_DAYS",
        "7",
    )
)

CASHAPP_TAG = os.environ.get(
    "CASHAPP_TAG",
    "",
).strip()

CASHAPP_URL = os.environ.get(
    "CASHAPP_URL",
    "",
).strip()

ZELLE_PHONE = os.environ.get(
    "ZELLE_PHONE",
    "",
).strip()

ADMIN_IDS = {
    int(x.strip())
    for x in os.environ.get(
        "ADMIN_IDS",
        "",
    ).split(",")
    if x.strip().isdigit()
}


# ==========================================================
# HELPERS
# ==========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def now_utc():
    return datetime.utcnow()


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def format_countdown(expires_at):
    """
    Format remaining raffle time.
    """

    expiration = parse_datetime(expires_at)

    if expiration is None:
        return "Unknown"

    remaining = expiration - now_utc()

    if remaining.total_seconds() <= 0:
        return "EXPIRED"

    days = remaining.days

    seconds = remaining.seconds

    hours = seconds // 3600

    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m"

    if hours > 0:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def get_user_display_name(user):
    if not user:
        return "Unknown User"

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


def money_text(value):
    if value is None:
        return ""

    return str(value)


# ==========================================================
# RAFFLE TEXT
# ==========================================================

def build_raffle_text(raffle):
    """
    Build the public raffle message.
    """

    prize = raffle.get("prize", "Unknown Prize")

    price = raffle.get("price", "Unknown")

    countdown = format_countdown(
        raffle.get("expires_at")
    )

    return (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
        f"🏆 Prize: {prize}\n"
        f"💵 Entry: {price}\n"
        f"⏳ Time Remaining: {countdown}\n\n"
        "Want to enter?\n"
        "Tap the button below and the bot will continue "
        "the entry process in your private messages.\n\n"
        "🔒 Your raffle entry is private.\n"
        "💳 Payment must be verified by Melanated AZ before "
        "your entry is approved.\n\n"
        "Good luck! 🍀"
    )


def build_payment_text(raffle):
    price = raffle.get("price", "")

    lines = [
        "🎟️ MELANATED AZ FRIENDS RAFFLE",
        "",
        f"🏆 Prize: {raffle.get('prize', 'Unknown')}",
        f"💵 Entry Price: {price}",
        "",
        "Choose your payment method:",
        "",
    ]

    if CASHAPP_TAG:
        lines.append(
            f"💵 Cash App: {CASHAPP_TAG}"
        )

    if ZELLE_PHONE:
        lines.append(
            f"💳 Zelle: {ZELLE_PHONE}"
        )

    lines.extend(
        [
            "",
            "After sending your payment, tap",
            "✅ I PAID below.",
            "",
            "Your payment will be verified by "
            "Melanated AZ before your raffle entry "
            "is approved.",
        ]
    )

    return "\n".join(lines)


def build_entry_pending_text():
    return (
        "⏳ PAYMENT SUBMITTED\n\n"
        "Your raffle payment has been submitted "
        "for verification.\n\n"
        "Melanated AZ will verify your payment "
        "before approving your raffle entry.\n\n"
        "You do not need to submit another entry "
        "while this one is pending."
    )


# ==========================================================
# KEYBOARDS
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
                ),
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data="raffle_zelle",
                ),
            ],
        ]
    )


def payment_keyboard():
    buttons = []

    if CASHAPP_URL:
        buttons.append(
            InlineKeyboardButton(
                "💵 PAY WITH CASH APP",
                url=CASHAPP_URL,
            )
        )

    if ZELLE_PHONE:
        buttons.append(
            InlineKeyboardButton(
                "💳 PAY WITH ZELLE",
                callback_data="raffle_zelle_info",
            )
        )

    keyboard = []

    if buttons:
        keyboard.append(buttons)

    keyboard.append(
        [
            InlineKeyboardButton(
                "✅ I PAID",
                callback_data="raffle_paid",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def admin_entry_keyboard(entry_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"approve_entry:{entry_id}",
                ),
                InlineKeyboardButton(
                    "❌ DENY",
                    callback_data=f"deny_entry:{entry_id}",
                ),
            ]
        ]
    )


# ==========================================================
# /startraffle
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_admin(user.id):
        return

    message = update.effective_message

    if not message:
        return

    pending = get_pending_raffle()

    if pending:
        await message.reply_text(
            "⚠️ There is already a pending raffle.\n\n"
            f"Raffle #{pending['id']}\n"
            f"Prize: {pending['prize']}\n"
            f"Entry: {pending['price']}\n\n"
            "Approve or cancel that raffle before "
            "creating another one."
        )
        return

    active = get_active_raffle()

    if active:
        await message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"Raffle #{active['id']}\n"
            f"Prize: {active['prize']}\n"
            f"Entry: {active['price']}\n"
            f"Time Remaining: "
            f"{format_countdown(active['expires_at'])}"
        )
        return

    context.user_data["awaiting_raffle_setup"] = True

    await message.reply_text(
        "🎟️ CREATE MELANATED AZ FRIENDS RAFFLE\n\n"
        "Send the raffle information in this format:\n\n"
        "Prize | Entry Price\n\n"
        "Example:\n"
        "$100 Cash Prize | $5\n\n"
        "The raffle will be created as PENDING "
        "for admin approval."
    )


# ==========================================================
# /startraffle MESSAGE INPUT
# ==========================================================

async def raffle_setup_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not context.user_data.get(
        "awaiting_raffle_setup"
    ):
        return

    user = update.effective_user

    if not user or not is_admin(user.id):
        return

    message = update.effective_message

    if not message or not message.text:
        return

    text = message.text.strip()

    if "|" not in text:
        await message.reply_text(
            "❌ Invalid format.\n\n"
            "Use:\n"
            "Prize | Entry Price\n\n"
            "Example:\n"
            "$100 Cash Prize | $5"
        )
        return

    prize, price = text.split(
        "|",
        1,
    )

    prize = prize.strip()

    price = price.strip()

    if not prize or not price:
        await message.reply_text(
            "❌ Prize and entry price are both required."
        )
        return

    expires_at = (
        now_utc()
        + timedelta(
            days=RAFFLE_DURATION_DAYS
        )
    ).isoformat()

    raffle_id = create_raffle(
        prize=prize,
        price=price,
        expires_at=expires_at,
    )

    context.user_data.pop(
        "awaiting_raffle_setup",
        None,
    )

    raffle = get_raffle(raffle_id)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE RAFFLE",
                    callback_data=f"approve_raffle:{raffle_id}",
                ),
                InlineKeyboardButton(
                    "❌ CANCEL",
                    callback_data=f"cancel_raffle:{raffle_id}",
                ),
            ]
        ]
    )

    await message.reply_text(
        "🎟️ RAFFLE CREATED — PENDING APPROVAL\n\n"
        + build_raffle_text(raffle)
        + "\n\n"
        "Admin approval is required before posting.",
        reply_markup=keyboard,
    )


# ==========================================================
# APPROVE RAFFLE CALLBACK
# ==========================================================

async def approve_raffle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = query.from_user

    if not is_admin(user.id):
        await query.answer(
            "You are not authorized.",
            show_alert=True,
        )
        return

    await query.answer()

    try:
        raffle_id = int(
            query.data.split(":", 1)[1]
        )
    except Exception:
        await query.edit_message_text(
            "❌ Invalid raffle ID."
        )
        return

    raffle = get_raffle(raffle_id)

    if not raffle:
        await query.edit_message_text(
            "❌ Raffle not found."
        )
        return

    if raffle["status"] != "pending":
        await query.edit_message_text(
            "⚠️ This raffle is no longer pending."
        )
        return

    if not approve_raffle(raffle_id):
        await query.edit_message_text(
            "❌ Unable to approve raffle."
        )
        return

    raffle = get_raffle(raffle_id)

    try:
        sent = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=build_raffle_text(raffle),
            reply_markup=raffle_keyboard(),
        )

        set_raffle_post(
            raffle_id,
            RAFFLE_CHAT_ID,
            sent.message_id,
        )

        await query.edit_message_text(
            "✅ RAFFLE APPROVED AND POSTED\n\n"
            f"Raffle #{raffle_id} is now active."
        )

    except Exception as exc:
        logger.exception(
            "Unable to post raffle: %s",
            exc,
        )

        await query.edit_message_text(
            "⚠️ Raffle was approved, but I could not "
            "post it to the raffle chat.\n\n"
            f"Error: {exc}"
        )


# ==========================================================
# CANCEL RAFFLE CALLBACK
# ==========================================================

async def cancel_raffle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = query.from_user

    if not is_admin(user.id):
        await query.answer(
            "You are not authorized.",
            show_alert=True,
        )
        return

    await query.answer()

    try:
        raffle_id = int(
            query.data.split(":", 1)[1]
        )
    except Exception:
        await query.edit_message_text(
            "❌ Invalid raffle ID."
        )
        return

    if cancel_pending_raffle(raffle_id):
        await query.edit_message_text(
            f"❌ Raffle #{raffle_id} cancelled."
        )
    else:
        await query.edit_message_text(
            "⚠️ Raffle could not be cancelled.\n\n"
            "It may already be active, closed, "
            "or cancelled."
        )


# ==========================================================
# ENTER RAFFLE CALLBACK
# ==========================================================

async def enter_raffle_callback(
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
        await query.answer(
            "There is no active raffle.",
            show_alert=True,
        )
        return

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "👋 Hey! I'm the Melanated AZ Bot.\n\n"
                "I'm messaging you from the "
                "Melanated AZ Friends Raffle.\n\n"
                "🔒 Your raffle entry is handled privately "
                "so the group does not see your payment "
                "or entry information.\n\n"
                + build_payment_text(raffle)
            ),
            reply_markup=payment_keyboard(),
        )

        await query.answer(
            "📩 Check your private messages!",
            show_alert=True,
        )

    except Exception as exc:
        logger.exception(
            "Unable to message raffle user: %s",
            exc,
        )

        await query.answer(
            "I couldn't message you privately. "
            "Please start the bot in private first.",
            show_alert=True,
        )


# ==========================================================
# /enterraffle
# ==========================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    user = update.effective_user

    if not message or not user:
        return

    raffle = get_active_raffle()

    if not raffle:
        await message.reply_text(
            "⚠️ There is no active raffle right now."
        )
        return

    if update.effective_chat.type != "private":
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    "👋 Hey! I'm the Melanated AZ Bot.\n\n"
                    "I'm messaging you from the "
                    "Melanated AZ Friends Raffle.\n\n"
                    + build_payment_text(raffle)
                ),
                reply_markup=payment_keyboard(),
            )

            await message.reply_text(
                "📩 Check your private messages to "
                "complete your raffle entry."
            )

        except Exception:
            await message.reply_text(
                "⚠️ I couldn't message you privately.\n\n"
                "Please open the bot in private and "
                "press Start first."
            )

        return

    await message.reply_text(
        build_payment_text(raffle),
        reply_markup=payment_keyboard(),
    )


# ==========================================================
# CASH APP BUTTON
# ==========================================================

async def payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if query.data == "raffle_cashapp":

        if CASHAPP_URL:
            await query.message.reply_text(
                "💵 Cash App payment:\n\n"
                f"{CASHAPP_URL}\n\n"
                "After sending payment, tap "
                "✅ I PAID."
            )

        elif CASHAPP_TAG:
            await query.message.reply_text(
                "💵 Cash App\n\n"
                f"Send payment to: {CASHAPP_TAG}\n\n"
                "After sending payment, tap "
                "✅ I PAID."
            )

        else:
            await query.message.reply_text(
                "⚠️ Cash App information is not configured."
            )


# ==========================================================
# ZELLE BUTTON
# ==========================================================

async def zelle_payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if ZELLE_PHONE:
        await query.message.reply_text(
            "💳 ZELLE PAYMENT\n\n"
            f"Send your payment to:\n"
            f"{ZELLE_PHONE}\n\n"
            "After sending payment, tap "
            "✅ I PAID."
        )
    else:
        await query.message.reply_text(
            "⚠️ Zelle information is not configured."
        )


# ==========================================================
# I PAID CALLBACK
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    if not user:
        return

    raffle = get_active_raffle()

    if not raffle:
        await query.message.reply_text(
            "⚠️ There is no active raffle."
        )
        return

    existing = None

    try:
        entries = get_approved_entries(
            raffle["id"]
        )

        for entry in entries:
            if entry["user_id"] == user.id:
                existing = entry
                break

        if not existing:
            pending_entries = get_pending_entries()

            for entry in pending_entries:
                if (
                    entry["raffle_id"] == raffle["id"]
                    and entry["user_id"] == user.id
                ):
                    existing = entry
                    break

    except Exception:
        logger.exception(
            "Error checking existing raffle entry"
        )

    if existing:

        if existing["status"] == "approved":
            await query.message.reply_text(
                "✅ You are already approved for this raffle."
            )

        elif existing["status"] == "pending":
            await query.message.reply_text(
                "⏳ Your payment is already pending "
                "verification.\n\n"
                "Melanated AZ will verify your payment."
            )

        return

    context.user_data[
        "awaiting_payment_method"
    ] = raffle["id"]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 CASH APP",
                    callback_data="paid_method_cashapp",
                ),
                InlineKeyboardButton(
                    "💳 ZELLE",
                    callback_data="paid_method_zelle",
                ),
            ]
        ]
    )

    await query.message.reply_text(
        "💳 PAYMENT VERIFICATION\n\n"
        "Which payment method did you use?",
        reply_markup=keyboard,
    )


# ==========================================================
# PAYMENT METHOD CALLBACK
# ==========================================================

async def payment_method_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    raffle_id = context.user_data.get(
        "awaiting_payment_method"
    )

    if not raffle_id:
        raffle = get_active_raffle()

        if not raffle:
            await query.message.reply_text(
                "⚠️ There is no active raffle."
            )
            return

        raffle_id = raffle["id"]

    raffle = get_raffle(raffle_id)

    if not raffle or raffle["status"] != "active":
        await query.message.reply_text(
            "⚠️ This raffle is no longer active."
        )
        return

    if query.data == "paid_method_cashapp":
        payment_method = "Cash App"

    elif query.data == "paid_method_zelle":
        payment_method = "Zelle"

    else:
        payment_method = "Unknown"

    entry_id = add_raffle_entry(
        raffle_id=raffle_id,
        user_id=user.id,
        username=user.username,
        display_name=get_user_display_name(user),
        payment_method=payment_method,
    )

    context.user_data.pop(
        "awaiting_payment_method",
        None,
    )

    if entry_id is None:
        await query.message.reply_text(
            "⚠️ You already have a pending or approved "
            "entry for this raffle."
        )
        return

    entry = get_entry(entry_id)

    await query.message.reply_text(
        build_entry_pending_text()
        + "\n\n"
        f"Payment Method: {payment_method}\n"
        f"Entry ID: #{entry_id}"
    )

    await notify_admins_new_entry(
        context,
        entry,
        raffle,
    )


# ==========================================================
# ADMIN PAYMENT NOTIFICATION
# ==========================================================

async def notify_admins_new_entry(
    context,
    entry,
    raffle,
):

    if not entry:
        return

    text = (
        "💳 NEW RAFFLE PAYMENT\n\n"
        f"🎟️ Raffle: #{raffle['id']}\n"
        f"🏆 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {raffle['price']}\n\n"
        f"👤 Name: {entry.get('display_name') or 'Unknown'}\n"
        f"🔹 Username: "
        f"@{entry['username']}"
        if entry.get("username")
        else
        "🔹 Username: None"
    )

    text += (
        f"\n🆔 User ID: {entry['user_id']}\n"
        f"💳 Payment: {entry.get('payment_method')}\n"
        f"🎫 Entry ID: #{entry['id']}\n\n"
        "⚠️ Verify the payment before approving."
    )

    keyboard = admin_entry_keyboard(
        entry["id"]
    )

    for admin_id in ADMIN_IDS:

        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=keyboard,
            )

        except Exception as exc:
            logger.warning(
                "Unable to notify admin %s: %s",
                admin_id,
                exc,
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

    user = query.from_user

    if not is_admin(user.id):
        await query.answer(
            "You are not authorized.",
            show_alert=True,
        )
        return

    await query.answer()

    data = query.data or ""

    try:
        action, entry_id_text = data.split(
            ":",
            1,
        )

        entry_id = int(entry_id_text)

    except Exception:
        await query.edit_message_text(
            "❌ Invalid entry."
        )
        return

    entry = get_entry(entry_id)

    if not entry:
        await query.edit_message_text(
            "❌ Entry not found."
        )
        return

    raffle = get_raffle(
        entry["raffle_id"]
    )

    if action == "approve_entry":

        changed = approve_entry(
            entry_id,
            user.id,
        )

        if not changed:
            await query.edit_message_text(
                "⚠️ This entry is no longer pending."
            )
            return

        await query.edit_message_text(
            "✅ RAFFLE ENTRY APPROVED\n\n"
            f"Entry #{entry_id}\n"
            f"User: "
            f"{entry.get('display_name') or entry['user_id']}\n"
            f"Payment: {entry.get('payment_method')}"
        )

        try:
            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 YOUR RAFFLE ENTRY IS APPROVED!\n\n"
                    f"🏆 Prize: {raffle['prize']}\n"
                    f"💵 Entry: {raffle['price']}\n\n"
                    f"🎫 Entry ID: #{entry_id}\n\n"
                    "Good luck! 🍀"
                ),
            )
        except Exception:
            logger.warning(
                "Could not notify approved user %s",
                entry["user_id"],
            )

    elif action == "deny_entry":

        changed = deny_entry(
            entry_id,
            user.id,
        )

        if not changed:
            await query.edit_message_text(
                "⚠️ This entry is no longer pending."
            )
            return

        await query.edit_message_text(
            "❌ RAFFLE ENTRY DENIED\n\n"
            f"Entry #{entry_id}"
        )

        try:
            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "❌ YOUR RAFFLE ENTRY WAS NOT APPROVED.\n\n"
                    "Your payment could not be verified "
                    "at this time.\n\n"
                    "Please contact Melanated AZ if you "
                    "believe this was an error."
                ),
            )
        except Exception:
            logger.warning(
                "Could not notify denied user %s",
                entry["user_id"],
            )


# ==========================================================
# /paid
# ==========================================================

async def paid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    raffle = get_active_raffle()

    if not raffle:
        await message.reply_text(
            "⚠️ There is no active raffle."
        )
        return

    context.user_data[
        "awaiting_payment_method"
    ] = raffle["id"]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 CASH APP",
                    callback_data="paid_method_cashapp",
                ),
                InlineKeyboardButton(
                    "💳 ZELLE",
                    callback_data="paid_method_zelle",
                ),
            ]
        ]
    )

    await message.reply_text(
        "💳 PAYMENT VERIFICATION\n\n"
        "Select the payment method you used:",
        reply_markup=keyboard,
    )


# ==========================================================
# /raffle
# ==========================================================

async def raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    active = get_active_raffle()

    if not active:
        await message.reply_text(
            "⚠️ There is no active raffle."
        )
        return

    await message.reply_text(
        build_raffle_text(active),
        reply_markup=raffle_keyboard(),
    )


# ==========================================================
# /rafflestatus
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    active = get_active_raffle()

    if not active:

        pending = get_pending_raffle()

        if pending:
            await message.reply_text(
                "⏳ RAFFLE STATUS\n\n"
                f"Raffle #{pending['id']}\n"
                f"🏆 Prize: {pending['prize']}\n"
                f"💵 Entry: {pending['price']}\n"
                "Status: PENDING APPROVAL"
            )
        else:
            await message.reply_text(
                "⚠️ No active raffle."
            )

        return

    entries = get_approved_entries(
        active["id"]
    )

    await message.reply_text(
        "🎟️ RAFFLE STATUS\n\n"
        f"Raffle #{active['id']}\n"
        f"🏆 Prize: {active['prize']}\n"
        f"💵 Entry: {active['price']}\n"
        f"⏳ Remaining: "
        f"{format_countdown(active['expires_at'])}\n"
        f"👥 Approved Entries: {len(entries)}"
    )


# ==========================================================
# /entries
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_admin(user.id):
        return

    # IMPORTANT:
    # This handler is also called by admin.py from a
    # callback query. Therefore update.message can be None.
    #
    # Always use effective_message.

    message = update.effective_message

    if not message:
        return

    active = get_active_raffle()

    if not active:
        await message.reply_text(
            "⚠️ There is no active raffle."
        )
        return

    entries = get_approved_entries(
        active["id"]
    )

    pending = [
        e
        for e in get_pending_entries()
        if e["raffle_id"] == active["id"]
    ]

    if not entries and not pending:
        await message.reply_text(
            "🎟️ RAFFLE ENTRIES\n\n"
            "There are currently no entries."
        )
        return

    lines = [
        "🎟️ MELANATED AZ FRIENDS RAFFLE",
        "",
        f"Raffle #{active['id']}",
        f"🏆 Prize: {active['prize']}",
        "",
        f"✅ Approved: {len(entries)}",
        f"⏳ Pending: {len(pending)}",
        "",
    ]

    if entries:
        lines.append("✅ APPROVED ENTRIES")

        for index, entry in enumerate(
            entries,
            start=1,
        ):
            name = (
                entry.get("display_name")
                or entry.get("username")
                or str(entry["user_id"])
            )

            username = entry.get("username")

            if username:
                name += f" (@{username})"

            lines.append(
                f"{index}. {name} "
                f"[#{entry['id']}]"
            )

        lines.append("")

    if pending:
        lines.append("⏳ PENDING PAYMENTS")

        for entry in pending:

            name = (
                entry.get("display_name")
                or entry.get("username")
                or str(entry["user_id"])
            )

            username = entry.get("username")

            if username:
                name += f" (@{username})"

            lines.append(
                f"• {name} "
                f"[#{entry['id']}] "
                f"— {entry.get('payment_method')}"
            )

    await message.reply_text(
        "\n".join(lines)
    )


# ==========================================================
# /raffleentries ALIAS
# ==========================================================

async def raffle_entries_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await raffle_entries(
        update,
        context,
    )


# ==========================================================
# /pending
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    entries = get_pending_entries()

    if not entries:
        await message.reply_text(
            "⏳ PENDING ENTRIES\n\n"
            "There are no pending entries."
        )
        return

    lines = [
        "⏳ PENDING RAFFLE ENTRIES",
        "",
    ]

    for entry in entries:

        raffle = get_raffle(
            entry["raffle_id"]
        )

        raffle_name = (
            f"Raffle #{entry['raffle_id']}"
        )

        if raffle:
            raffle_name += (
                f" — {raffle['prize']}"
            )

        name = (
            entry.get("display_name")
            or entry.get("username")
            or str(entry["user_id"])
        )

        username = entry.get("username")

        if username:
            name += f" (@{username})"

        lines.extend(
            [
                f"🎫 Entry #{entry['id']}",
                f"👤 {name}",
                f"🆔 User ID: {entry['user_id']}",
                f"🎟️ {raffle_name}",
                f"💳 {entry.get('payment_method')}",
                "",
            ]
        )

    await message.reply_text(
        "\n".join(lines)
    )


# ==========================================================
# /approveentry
# ==========================================================

async def approve_entry_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    if not context.args:
        await message.reply_text(
            "Usage:\n"
            "/approveentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid entry ID."
        )
        return

    entry = get_entry(entry_id)

    if not entry:
        await message.reply_text(
            "❌ Entry not found."
        )
        return

    changed = approve_entry(
        entry_id,
        user.id,
    )

    if not changed:
        await message.reply_text(
            "⚠️ Entry is no longer pending."
        )
        return

    await message.reply_text(
        f"✅ Entry #{entry_id} approved."
    )

    raffle_data = get_raffle(
        entry["raffle_id"]
    )

    try:
        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "🎉 YOUR RAFFLE ENTRY IS APPROVED!\n\n"
                f"🏆 Prize: "
                f"{raffle_data['prize'] if raffle_data else 'Unknown'}\n\n"
                f"🎫 Entry ID: #{entry_id}\n\n"
                "Good luck! 🍀"
            ),
        )
    except Exception:
        pass


# ==========================================================
# /denyentry
# ==========================================================

async def deny_entry_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    if not context.args:
        await message.reply_text(
            "Usage:\n"
            "/denyentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid entry ID."
        )
        return

    entry = get_entry(entry_id)

    if not entry:
        await message.reply_text(
            "❌ Entry not found."
        )
        return

    changed = deny_entry(
        entry_id,
        user.id,
    )

    if not changed:
        await message.reply_text(
            "⚠️ Entry is no longer pending."
        )
        return

    await message.reply_text(
        f"❌ Entry #{entry_id} denied."
    )

    try:
        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "❌ YOUR RAFFLE ENTRY WAS NOT APPROVED.\n\n"
                "Your payment could not be verified.\n\n"
                "Please contact Melanated AZ if you "
                "believe this was an error."
            ),
        )
    except Exception:
        pass


# ==========================================================
# /cancelraffle
# ==========================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    active = get_active_raffle()

    if not active:
        pending = get_pending_raffle()

        if not pending:
            await message.reply_text(
                "⚠️ There is no active or pending raffle."
            )
            return

        if cancel_pending_raffle(
            pending["id"]
        ):
            await message.reply_text(
                f"❌ Pending raffle #{pending['id']} "
                "cancelled."
            )
        else:
            await message.reply_text(
                "❌ Unable to cancel raffle."
            )

        return

    if close_raffle(
        active["id"]
    ):
        await message.reply_text(
            f"❌ Raffle #{active['id']} cancelled/closed."
        )
    else:
        await message.reply_text(
            "❌ Unable to close raffle."
        )


# ==========================================================
# /draw
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    active = get_active_raffle()

    if not active:

        await message.reply_text(
            "⚠️ There is no active raffle to draw."
        )
        return

    entries = get_approved_entries(
        active["id"]
    )

    if not entries:

        await message.reply_text(
            "⚠️ There are no approved entries."
        )
        return

    winner = random.choice(
        entries
    )

    close_raffle(
        active["id"]
    )

    winner_name = (
        winner.get("display_name")
        or winner.get("username")
        or str(winner["user_id"])
    )

    if winner.get("username"):
        winner_display = (
            f"@{winner['username']}"
        )
    else:
        winner_display = winner_name

    result = (
        "🎉🎉🎉 RAFFLE WINNER 🎉🎉🎉\n\n"
        "🏆 MELANATED AZ FRIENDS RAFFLE\n\n"
        f"Prize: {active['prize']}\n\n"
        f"👑 WINNER: {winner_display}\n\n"
        f"🎫 Entry #{winner['id']}\n\n"
        "Congratulations! 🎉"
    )

    await message.reply_text(
        result
    )

    if active.get("chat_id"):
        try:
            await context.bot.send_message(
                chat_id=active["chat_id"],
                text=result,
            )
        except Exception:
            logger.exception(
                "Unable to post winner to raffle chat"
            )

    try:
        await context.bot.send_message(
            chat_id=winner["user_id"],
            text=(
                "🎉 CONGRATULATIONS!\n\n"
                "You won the Melanated AZ Friends Raffle!\n\n"
                f"🏆 Prize: {active['prize']}\n\n"
                "Please contact Melanated AZ for "
                "prize verification and delivery."
            ),
        )
    except Exception:
        logger.warning(
            "Unable to privately notify winner."
        )


# ==========================================================
# /reroll
# ==========================================================

async def reroll_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    # Find most recent raffle.
    #
    # The database provided does not include a dedicated
    # "last closed raffle" function, so this function uses
    # the active raffle first.
    active = get_active_raffle()

    if active:
        entries = get_approved_entries(
            active["id"]
        )

        if not entries:
            await message.reply_text(
                "⚠️ No approved entries available."
            )
            return

        winner = random.choice(
            entries
        )

        await message.reply_text(
            "🔄 RAFFLE REROLL\n\n"
            f"🏆 Prize: {active['prize']}\n\n"
            f"🎉 New Winner:\n"
            f"{winner.get('display_name') or winner['user_id']}\n\n"
            f"🎫 Entry #{winner['id']}"
        )

        return

    await message.reply_text(
        "⚠️ No active raffle is available for reroll."
    )


# ==========================================================
# /bonusentry
# ==========================================================

async def bonus_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    active = get_active_raffle()

    if not active:
        await message.reply_text(
            "⚠️ There is no active raffle."
        )
        return

    if not context.args:
        await message.reply_text(
            "Usage:\n"
            "/bonusentry USER_ID"
        )
        return

    try:
        target_user_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid user ID."
        )
        return

    entry_id = add_raffle_entry(
        raffle_id=active["id"],
        user_id=target_user_id,
        username=None,
        display_name="Bonus Entry",
        payment_method="BONUS",
    )

    if entry_id is None:
        await message.reply_text(
            "⚠️ That user already has a pending "
            "or approved entry."
        )
        return

    # Immediately approve bonus entry.
    approve_entry(
        entry_id,
        user.id,
    )

    await message.reply_text(
        "🎁 BONUS ENTRY ADDED\n\n"
        f"User ID: {target_user_id}\n"
        f"Entry ID: #{entry_id}\n"
        "Status: APPROVED"
    )

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                "🎁 YOU RECEIVED A BONUS RAFFLE ENTRY!\n\n"
                f"🏆 Prize: {active['prize']}\n"
                f"🎫 Entry ID: #{entry_id}\n\n"
                "Good luck! 🍀"
            ),
        )
    except Exception:
        pass


# ==========================================================
# /removeentry
# ==========================================================

async def remove_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not message:
        return

    if not context.args:
        await message.reply_text(
            "Usage:\n"
            "/removeentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid entry ID."
        )
        return

    entry = get_entry(entry_id)

    if not entry:
        await message.reply_text(
            "❌ Entry not found."
        )
        return

    if remove_entry(entry_id):
        await message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )
    else:
        await message.reply_text(
            "❌ Unable to remove entry."
        )


# ==========================================================
# CALLBACK ROUTER
#
# Useful if bot.py/admin.py routes raffle callbacks
# through one function.
# ==========================================================

async def raffle_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "raffle_enter":
        await enter_raffle_callback(
            update,
            context,
        )
        return

    if data == "raffle_cashapp":
        await payment_button(
            update,
            context,
        )
        return

    if data == "raffle_zelle":
        await zelle_payment_button(
            update,
            context,
        )
        return

    if data == "raffle_zelle_info":
        await zelle_payment_button(
            update,
            context,
        )
        return

    if data == "raffle_paid":
        await paid_entry(
            update,
            context,
        )
        return

    if data.startswith(
        "paid_method_"
    ):
        await payment_method_callback(
            update,
            context,
        )
        return

    if data.startswith(
        "approve_entry:"
    ) or data.startswith(
        "deny_entry:"
    ):
        await admin_payment_button(
            update,
            context,
        )
        return

    if data.startswith(
        "approve_raffle:"
    ):
        await approve_raffle_callback(
            update,
            context,
        )
        return

    if data.startswith(
        "cancel_raffle:"
    ):
        await cancel_raffle_callback(
            update,
            context,
        )
        return


# ==========================================================
# COUNTDOWN UPDATE
# ==========================================================

async def update_raffle_countdown(
    context: ContextTypes.DEFAULT_TYPE,
):

    raffle = get_active_raffle()

    if not raffle:
        return

    expiration = parse_datetime(
        raffle["expires_at"]
    )

    if expiration is None:
        return

    if now_utc() >= expiration:

        if close_raffle(
            raffle["id"]
        ):

            logger.info(
                "Raffle #%s expired.",
                raffle["id"],
            )

            if raffle.get("chat_id"):

                try:
                    await context.bot.send_message(
                        chat_id=raffle["chat_id"],
                        text=(
                            "⏰ RAFFLE CLOSED\n\n"
                            f"🏆 Prize: {raffle['prize']}\n\n"
                            "The raffle has ended.\n"
                            "An admin will conduct the drawing."
                        ),
                    )
                except Exception:
                    logger.exception(
                        "Unable to announce raffle close."
                    )

        return

    if not raffle.get("chat_id"):
        return

    if not raffle.get("message_id"):
        return

    try:

        await context.bot.edit_message_text(
            chat_id=raffle["chat_id"],
            message_id=raffle["message_id"],
            text=build_raffle_text(raffle),
            reply_markup=raffle_keyboard(),
        )

    except Exception as exc:

        # Telegram can reject an edit when the content has
        # not changed. That is harmless.
        logger.debug(
            "Countdown update skipped: %s",
            exc,
        )


# ==========================================================
# START COUNTDOWN JOB
# ==========================================================

def start_raffle_countdown(
    application,
):

    if not application.job_queue:
        logger.warning(
            "Job queue unavailable; raffle countdown "
            "cannot start."
        )
        return

    # Remove existing raffle countdown jobs.
    for job in application.job_queue.get_jobs_by_name(
        "raffle_countdown"
    ):
        job.schedule_removal()

    application.job_queue.run_repeating(
        update_raffle_countdown,
        interval=60,
        first=5,
        name="raffle_countdown",
    )

    logger.info(
        "🎟️ Raffle countdown scheduler started."
    )


# ==========================================================
# REGISTER JOB
#
# bot.py can call:
#
# start_raffle_countdown(application)
#
# ==========================================================


# ==========================================================
# COMPATIBILITY ALIASES
#
# These preserve names used by older bot.py/admin.py files.
# ==========================================================

startraffle = start_raffle

enter = enter_raffle

rafflestatus = raffle_status

raffleentries = raffle_entries

pending = pending_entries

approveentry = approve_entry_command

denyentry = deny_entry_command

cancelraffle = cancel_raffle

draw = draw_raffle

reroll = reroll_raffle

removeentry = remove_raffle_entry


# ==========================================================
# END raffle.py
# ==========================================================
