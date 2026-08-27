# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# COMPLETE REPLACEMENT
#
# OLD APPROVAL SYSTEM RETAINED
#
# Database:
#   raffle_database.py is the ONLY database layer.
#
# IMPORTANT:
#   Existing raffle.db is preserved.
#   This file NEVER deletes or recreates the database.
#
# Required by current bot.py:
#   raffle_private_start
#   raffle_approval_button
#   raffle_enter_button
#
# Features:
#   - Admin raffle creation
#   - Admin raffle approval
#   - Admin raffle cancellation
#   - Private raffle entry
#   - Cash App / Zelle
#   - Admin payment verification
#   - Entry approval / denial
#   - Raffle countdown
#   - Raffle status
#   - Raffle history
#   - Draw
#   - Reroll
#   - Bonus entries
#   - Remove entries
#   - Database recovery/history
#   - Callback-safe handlers
# ==========================================================

import logging
import os
import random
from datetime import datetime, timezone, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

import raffle_database as db


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

# IMPORTANT:
# initialize_database() must use CREATE TABLE IF NOT EXISTS.
# It does NOT intentionally delete existing records.

db.initialize_database()


# ==========================================================
# CONFIG
# ==========================================================

try:
    from config import (
        ADMIN_IDS,
        RAFFLE_CHAT_ID,
        CASHAPP_TAG,
        CASHAPP_URL,
        ZELLE_PHONE,
    )
except ImportError:
    ADMIN_IDS = []
    RAFFLE_CHAT_ID = None
    CASHAPP_TAG = ""
    CASHAPP_URL = ""
    ZELLE_PHONE = ""


# ==========================================================
# ENVIRONMENT FALLBACKS
# ==========================================================

if not ADMIN_IDS:
    raw_admins = os.environ.get("ADMIN_IDS", "")

    if raw_admins:
        ADMIN_IDS = [
            x.strip()
            for x in raw_admins.split(",")
            if x.strip()
        ]


if not RAFFLE_CHAT_ID:
    RAFFLE_CHAT_ID = os.environ.get(
        "RAFFLE_CHAT_ID"
    )


if not CASHAPP_TAG:
    CASHAPP_TAG = os.environ.get(
        "CASHAPP_TAG",
        "",
    )


if not CASHAPP_URL:
    CASHAPP_URL = os.environ.get(
        "CASHAPP_URL",
        "",
    )


if not ZELLE_PHONE:
    ZELLE_PHONE = os.environ.get(
        "ZELLE_PHONE",
        "",
    )


# ==========================================================
# HELPERS
# ==========================================================

def is_admin_user(user_id):
    """Return True if Telegram user is configured as an admin."""

    try:
        return int(user_id) in [
            int(x)
            for x in ADMIN_IDS
        ]
    except Exception:
        return False


def utc_now():
    return datetime.now(timezone.utc)


def parse_datetime(value):
    """Safely parse SQLite/ISO datetime values."""

    if not value:
        return None

    try:
        value = str(value).strip()

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        result = datetime.fromisoformat(value)

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result

    except Exception:
        return None


def format_countdown(expires_at):
    """Return human-readable remaining raffle time."""

    expires = parse_datetime(expires_at)

    if not expires:
        return "Unknown"

    remaining = expires - utc_now()

    seconds = int(
        remaining.total_seconds()
    )

    if seconds <= 0:
        return "EXPIRED"

    days, remainder = divmod(
        seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if days:
        return (
            f"{days}d "
            f"{hours}h "
            f"{minutes}m"
        )

    if hours:
        return (
            f"{hours}h "
            f"{minutes}m"
        )

    if minutes:
        return (
            f"{minutes}m "
            f"{seconds}s"
        )

    return f"{seconds}s"


def money_text(value):
    if value is None:
        return "$0"

    value = str(value).strip()

    if not value:
        return "$0"

    if value.startswith("$"):
        return value

    return f"${value}"


def safe_display_name(user):
    if not user:
        return "Unknown User"

    name = getattr(
        user,
        "full_name",
        None,
    )

    if name:
        return name

    username = getattr(
        user,
        "username",
        None,
    )

    if username:
        return f"@{username}"

    return str(
        getattr(user, "id", "Unknown")
    )


async def answer_callback(
    update,
    text=None,
):
    """Safely answer Telegram callback queries."""

    query = getattr(
        update,
        "callback_query",
        None,
    )

    if not query:
        return

    try:
        await query.answer(
            text=text or ""
        )
    except Exception:
        pass


async def send_message_safe(
    update,
    context,
    text,
    reply_markup=None,
):
    """
    Safely send a Telegram message regardless of
    whether the handler came from a command or callback.
    """

    if update and update.message:
        return await update.message.reply_text(
            text,
            reply_markup=reply_markup,
        )

    query = getattr(
        update,
        "callback_query",
        None,
    )

    if query:

        if query.message:
            return await query.message.reply_text(
                text,
                reply_markup=reply_markup,
            )

        if query.from_user:
            return await context.bot.send_message(
                chat_id=query.from_user.id,
                text=text,
                reply_markup=reply_markup,
            )

    if update and update.effective_chat:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
        )

    return None


# ==========================================================
# DATABASE COMPATIBILITY HELPERS
# ==========================================================

def get_current_raffle():
    raffle_data = db.get_active_raffle()

    if raffle_data:
        return raffle_data

    return db.get_pending_raffle()


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


def payment_keyboard(
    raffle_id,
):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 CASH APP",
                    callback_data=f"pay_cashapp:{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 ZELLE",
                    callback_data=f"pay_zelle:{raffle_id}",
                )
            ],
        ]
    )


def raffle_approval_keyboard(
    raffle_id,
):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE RAFFLE",
                    callback_data=f"approve_raffle:{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ CANCEL RAFFLE",
                    callback_data=f"cancel_raffle:{raffle_id}",
                )
            ],
        ]
    )


def admin_entry_keyboard(
    entry_id,
):
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
# RAFFLE DISPLAY
# ==========================================================

def build_raffle_text(
    raffle_data,
):
    if not raffle_data:
        return (
            "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
            "There is currently no raffle available."
        )

    prize = raffle_data.get(
        "prize",
        "Unknown Prize",
    )

    price = money_text(
        raffle_data.get("price")
    )

    status = str(
        raffle_data.get(
            "status",
            "unknown",
        )
    ).upper()

    countdown = format_countdown(
        raffle_data.get("expires_at")
    )

    return (
        "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry: {price}\n"
        f"⏳ Time Remaining: {countdown}\n"
        f"📌 Status: {status}\n\n"
        "Want to enter?\n"
        "Tap ENTER RAFFLE below.\n\n"
        "🔒 Your entry and payment information "
        "are handled privately through the bot."
    )


# ==========================================================
# /raffle
# ==========================================================

async def raffle(
    update,
    context,
):
    raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "🎟️ There is currently no active raffle.",
        )
        return

    await send_message_safe(
        update,
        context,
        build_raffle_text(
            raffle_data
        ),
        reply_markup=raffle_keyboard(),
    )


raffle_command = raffle


# ==========================================================
# OLD APPROVAL SYSTEM
# /startraffle
# ==========================================================

async def start_raffle(
    update,
    context,
):
    """
    Create a raffle.

    OLD APPROVAL SYSTEM:
    The raffle is created as pending.
    Admins receive APPROVE / CANCEL buttons.
    It is not posted publicly until approved.
    """

    user = update.effective_user

    if not user:
        return

    if not is_admin_user(user.id):
        await send_message_safe(
            update,
            context,
            "❌ You are not authorized to start a raffle.",
        )
        return

    args = context.args or []

    if not args:
        await send_message_safe(
            update,
            context,
            (
                "🎟️ START RAFFLE\n\n"
                "Use:\n"
                "/startraffle Prize | Entry Price\n\n"
                "Example:\n"
                "/startraffle $100 Cash Prize | $5"
            ),
        )
        return

    raw = " ".join(args)

    if "|" not in raw:
        await send_message_safe(
            update,
            context,
            (
                "❌ Invalid format.\n\n"
                "Use:\n"
                "/startraffle Prize | Entry Price"
            ),
        )
        return

    prize, price = raw.split(
        "|",
        1,
    )

    prize = prize.strip()
    price = price.strip()

    if not prize or not price:
        await send_message_safe(
            update,
            context,
            "❌ Prize and entry price are required.",
        )
        return

    try:
        duration_days = int(
            os.environ.get(
                "RAFFLE_DURATION_DAYS",
                "7",
            )
        )
    except Exception:
        duration_days = 7

    expires_at = (
        utc_now()
        + timedelta(
            days=duration_days
        )
    ).replace(
        microsecond=0
    ).isoformat()

    raffle_id = db.create_raffle(
        prize=prize,
        price=price,
        expires_at=expires_at,
    )

    if not raffle_id:
        await send_message_safe(
            update,
            context,
            "❌ Unable to create raffle.",
        )
        return

    await send_message_safe(
        update,
        context,
        (
            "🎟️ RAFFLE CREATED\n\n"
            f"🎁 Prize: {prize}\n"
            f"💵 Entry: {price}\n"
            f"⏳ Duration: {duration_days} days\n"
            f"🆔 Raffle ID: #{raffle_id}\n\n"
            "⏳ The raffle is waiting for admin approval."
        ),
    )

    # Notify every configured admin.
    for admin_id in ADMIN_IDS:

        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "🎟️ RAFFLE APPROVAL REQUIRED\n\n"
                    f"🎁 Prize: {prize}\n"
                    f"💵 Entry: {price}\n"
                    f"⏳ Duration: {duration_days} days\n"
                    f"🆔 Raffle ID: #{raffle_id}\n\n"
                    "Approve this raffle to post it "
                    "in the Melanated AZ group."
                ),
                reply_markup=raffle_approval_keyboard(
                    raffle_id
                ),
            )

        except Exception as exc:
            logger.error(
                "Unable to notify admin %s: %s",
                admin_id,
                exc,
            )


startraffle = start_raffle
create_raffle = start_raffle


# ==========================================================
# REQUIRED CURRENT BOT.PY FUNCTION
#
# raffle_private_start
# ==========================================================

async def raffle_private_start(
    update,
    context,
):
    """
    Compatibility handler required by current bot.py.

    This opens the private raffle-entry process.
    """

    query = update.callback_query

    if query:
        await answer_callback(
            update,
            "Opening raffle...",
        )

    user = update.effective_user

    if not user:
        return

    raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ There is currently no active raffle.",
        )
        return

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "👋 Welcome to the Melanated AZ "
                "Raffle Bot!\n\n"
                "🎟️ You are entering from "
                "Melanated AZ.\n\n"
                f"🎁 Prize: {raffle_data['prize']}\n"
                f"💵 Entry: "
                f"{money_text(raffle_data['price'])}\n\n"
                "Your entry is handled privately.\n\n"
                "Choose your payment method:"
            ),
            reply_markup=payment_keyboard(
                raffle_data["id"]
            ),
        )

        await send_message_safe(
            update,
            context,
            (
                "📩 Check your private messages.\n\n"
                "I've sent your raffle entry "
                "instructions to your inbox."
            ),
        )

    except Exception as exc:

        logger.error(
            "Unable to start private raffle entry "
            "for user %s: %s",
            user.id,
            exc,
        )

        await send_message_safe(
            update,
            context,
            (
                "⚠️ I couldn't message you privately.\n\n"
                "Open the Melanated AZ Raffle Bot, "
                "press START, and then try again."
            ),
        )


# ==========================================================
# REQUIRED CURRENT BOT.PY FUNCTION
#
# raffle_enter_button
# ==========================================================

async def raffle_enter_button(
    update,
    context,
):
    """
    Compatibility handler required by current bot.py.

    Performs the same private-entry operation as
    raffle_private_start.
    """

    return await raffle_private_start(
        update,
        context,
    )


# ==========================================================
# OLD ALIASES
# ==========================================================

enter_raffle = raffle_private_start
enter = raffle_private_start
enterraffle = raffle_private_start


# ==========================================================
# REQUIRED CURRENT BOT.PY FUNCTION
#
# raffle_approval_button
# ==========================================================

async def raffle_approval_button(
    update,
    context,
):
    """
    Compatibility handler required by current bot.py.

    This is the OLD raffle approval system.

    Admin presses APPROVE RAFFLE.
    The raffle becomes active.
    The bot posts it to the group.
    """

    query = update.callback_query

    if not query:
        return

    await answer_callback(
        update,
        "Approving raffle...",
    )

    user = query.from_user

    if not user:
        return

    if not is_admin_user(user.id):
        await send_message_safe(
            update,
            context,
            "❌ You are not authorized.",
        )
        return

    data = query.data or ""

    try:
        raffle_id = int(
            data.split(":", 1)[1]
        )
    except Exception:
        await send_message_safe(
            update,
            context,
            "❌ Invalid raffle ID.",
        )
        return

    raffle_data = db.get_raffle(
        raffle_id
    )

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ Raffle not found.",
        )
        return

    current_status = str(
        raffle_data.get(
            "status",
            "",
        )
    ).lower()

    if current_status not in (
        "pending",
        "pending_approval",
    ):
        await send_message_safe(
            update,
            context,
            (
                "⚠️ This raffle is no longer "
                "waiting for approval.\n\n"
                f"Current status: "
                f"{raffle_data.get('status')}"
            ),
        )
        return

    try:
        changed = db.approve_raffle(
            raffle_id
        )
    except Exception as exc:
        logger.exception(
            "Database error approving raffle %s",
            raffle_id,
        )

        await send_message_safe(
            update,
            context,
            (
                "❌ Database error while approving "
                "the raffle."
            ),
        )
        return

    if not changed:
        await send_message_safe(
            update,
            context,
            "⚠️ Raffle could not be approved.",
        )
        return

    raffle_data = db.get_raffle(
        raffle_id
    )

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "⚠️ Raffle approved but could not be reloaded.",
        )
        return

    if not RAFFLE_CHAT_ID:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ Raffle approved, but "
                "RAFFLE_CHAT_ID is not configured."
            ),
        )
        return

    try:

        message = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=build_raffle_text(
                raffle_data
            ),
            reply_markup=raffle_keyboard(),
        )

        db.set_raffle_post(
            raffle_id,
            RAFFLE_CHAT_ID,
            message.message_id,
        )

    except Exception as exc:

        logger.exception(
            "Unable to post approved raffle %s",
            raffle_id,
        )

        await send_message_safe(
            update,
            context,
            (
                "⚠️ Raffle was approved, "
                "but I could not post it "
                "to the raffle group.\n\n"
                "Check that the bot is an administrator "
                "and has permission to send messages."
            ),
        )
        return

    await send_message_safe(
        update,
        context,
        (
            f"✅ Raffle #{raffle_id} approved "
            "and posted to Melanated AZ."
        ),
    )


approve_raffle_callback = raffle_approval_button
approve_raffle = raffle_approval_button


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle_callback(
    update,
    context,
):
    query = update.callback_query

    if query:
        await answer_callback(
            update,
            "Cancelling raffle...",
        )

    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    try:
        raffle_id = int(
            query.data.split(":", 1)[1]
        )
    except Exception:
        await send_message_safe(
            update,
            context,
            "❌ Invalid raffle ID.",
        )
        return

    try:
        changed = db.cancel_pending_raffle(
            raffle_id
        )
    except Exception:
        logger.exception(
            "Error cancelling raffle %s",
            raffle_id,
        )
        changed = False

    if changed:
        await send_message_safe(
            update,
            context,
            f"❌ Raffle #{raffle_id} cancelled.",
        )
    else:
        await send_message_safe(
            update,
            context,
            "⚠️ Raffle was not pending.",
        )


cancel_raffle = cancel_raffle_callback


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

    await answer_callback(
        update
    )

    user = query.from_user

    if not user:
        return

    data = query.data or ""

    # ------------------------------------------------------
    # Public raffle payment buttons
    #
    # raffle_cashapp
    # raffle_zelle
    #
    # These buttons need to know the current active raffle.
    # ------------------------------------------------------

    if data in (
        "raffle_cashapp",
        "raffle_zelle",
    ):

        raffle_data = db.get_active_raffle()

        if not raffle_data:
            await send_message_safe(
                update,
                context,
                "❌ There is currently no active raffle.",
            )
            return

        raffle_id = raffle_data["id"]

        method = (
            "Cash App"
            if data == "raffle_cashapp"
            else "Zelle"
        )

    else:

        parts = data.split(":")

        if len(parts) != 2:
            await send_message_safe(
                update,
                context,
                "❌ Invalid payment request.",
            )
            return

        method_key = parts[0]

        try:
            raffle_id = int(
                parts[1]
            )
        except Exception:
            await send_message_safe(
                update,
                context,
                "❌ Invalid raffle ID.",
            )
            return

        method = (
            "Cash App"
            if method_key == "pay_cashapp"
            else "Zelle"
        )

    raffle_data = db.get_raffle(
        raffle_id
    )

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ Raffle not found.",
        )
        return

    # Only active raffles can receive entries.
    status = str(
        raffle_data.get(
            "status",
            "",
        )
    ).lower()

    if status != "active":
        await send_message_safe(
            update,
            context,
            "❌ This raffle is not currently active.",
        )
        return

    # ------------------------------------------------------
    # Create pending entry.
    # ------------------------------------------------------

    try:
        entry_id = db.add_raffle_entry(
            raffle_id=raffle_id,
            user_id=user.id,
            username=user.username,
            display_name=safe_display_name(user),
            payment_method=method,
        )

    except Exception:
        logger.exception(
            "Unable to create raffle entry."
        )

        await send_message_safe(
            update,
            context,
            (
                "❌ I couldn't create your raffle "
                "entry right now. Please try again."
            ),
        )
        return

    if entry_id is None:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ You already have a pending "
                "or approved entry for this raffle."
            ),
        )
        return

    # ------------------------------------------------------
    # Payment instructions.
    # ------------------------------------------------------

    if method == "Cash App":

        payment_destination = (
            CASHAPP_TAG
            or "Cash App information unavailable"
        )

        payment_text = (
            "💵 CASH APP PAYMENT\n\n"
            f"Send {money_text(raffle_data['price'])} to:\n"
            f"{payment_destination}\n\n"
        )

        if CASHAPP_URL:
            payment_text += (
                f"{CASHAPP_URL}\n\n"
            )

        payment_text += (
            "After sending payment, send your "
            "payment confirmation/screenshot "
            "to this bot.\n\n"
            "Your entry will remain PENDING until "
            "an administrator verifies the payment."
        )

    else:

        payment_destination = (
            ZELLE_PHONE
            or "Zelle information unavailable"
        )

        payment_text = (
            "💳 ZELLE PAYMENT\n\n"
            f"Send {money_text(raffle_data['price'])} to:\n"
            f"{payment_destination}\n\n"
            "After sending payment, send your "
            "payment confirmation/screenshot "
            "to this bot.\n\n"
            "Your entry will remain PENDING until "
            "an administrator verifies the payment."
        )

    await send_message_safe(
        update,
        context,
        (
            "✅ RAFFLE ENTRY CREATED\n\n"
            f"🎟️ Entry #{entry_id}\n"
            f"🎁 Prize: {raffle_data['prize']}\n"
            f"💵 Amount: "
            f"{money_text(raffle_data['price'])}\n"
            f"💳 Method: {method}\n\n"
            f"{payment_text}"
        ),
    )

    await notify_admins_new_entry(
        context,
        entry_id,
    )


# ==========================================================
# ADMIN PAYMENT / ENTRY VIEW
# ==========================================================

async def paid_entry(
    update,
    context,
):
    """
    Display a pending entry to an administrator.
    """

    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    query = update.callback_query

    if query:
        await answer_callback(
            update,
            "Loading payment entry...",
        )

        data = query.data or ""

        try:
            entry_id = int(
                data.split(":")[-1]
            )
        except Exception:
            entry_id = None

    else:

        args = context.args or []

        try:
            entry_id = int(
                args[0]
            )
        except Exception:
            entry_id = None

    if not entry_id:
        await send_message_safe(
            update,
            context,
            "❌ No entry ID was provided.",
        )
        return

    entry = db.get_entry(
        entry_id
    )

    if not entry:
        await send_message_safe(
            update,
            context,
            "❌ Entry not found.",
        )
        return

    await send_message_safe(
        update,
        context,
        (
            "💳 RAFFLE PAYMENT ENTRY\n\n"
            f"🆔 Entry: #{entry['id']}\n"
            f"👤 Name: "
            f"{entry.get('display_name') or 'Unknown'}\n"
            f"💳 Payment: "
            f"{entry.get('payment_method') or 'Unknown'}\n"
            f"📌 Status: "
            f"{entry.get('status') or 'Unknown'}\n\n"
            "Verify the payment before approving."
        ),
        reply_markup=admin_entry_keyboard(
            entry_id
        ),
    )


admin_payment_button = paid_entry


# ==========================================================
# ADMIN NOTIFICATION
# ==========================================================

async def notify_admins_new_entry(
    context,
    entry_id,
):
    entry = db.get_entry(
        entry_id
    )

    if not entry:
        return

    raffle_data = db.get_raffle(
        entry["raffle_id"]
    )

    if not raffle_data:
        return

    username = entry.get(
        "username"
    )

    username_text = (
        f"@{username}"
        if username
        else "No username"
    )

    text = (
        "💰 RAFFLE PAYMENT PENDING\n\n"
        f"🎟️ Raffle #{raffle_data['id']}\n"
        f"🎁 Prize: {raffle_data['prize']}\n"
        f"💵 Amount: "
        f"{money_text(raffle_data['price'])}\n"
        f"🆔 Entry: #{entry['id']}\n"
        f"👤 Name: "
        f"{entry.get('display_name') or 'Unknown'}\n"
        f"👤 Username: {username_text}\n"
        f"💳 Payment: "
        f"{entry.get('payment_method') or 'Unknown'}\n\n"
        "Verify the payment before approving this entry."
    )

    for admin_id in ADMIN_IDS:

        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=admin_entry_keyboard(
                    entry_id
                ),
            )

        except Exception as exc:
            logger.error(
                "Unable to notify admin %s "
                "about entry %s: %s",
                admin_id,
                entry_id,
                exc,
            )


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    entries = db.get_pending_entries()

    if not entries:
        await send_message_safe(
            update,
            context,
            "✅ There are no pending raffle entries.",
        )
        return

    lines = [
        "💰 PENDING RAFFLE ENTRIES",
        "",
    ]

    for entry in entries:

        lines.append(
            (
                f"🆔 #{entry['id']} | "
                f"{entry.get('display_name') or 'Unknown'} | "
                f"{entry.get('payment_method') or 'Unknown'}"
            )
        )

    await send_message_safe(
        update,
        context,
        "\n".join(lines),
    )


pending = pending_entries


# ==========================================================
# APPROVE ENTRY
# ==========================================================

async def approve_raffle_entry(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return

    await answer_callback(
        update,
        "Approving entry...",
    )

    user = query.from_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    try:
        entry_id = int(
            query.data.split(":", 1)[1]
        )
    except Exception:
        await send_message_safe(
            update,
            context,
            "❌ Invalid entry ID.",
        )
        return

    entry = db.get_entry(
        entry_id
    )

    if not entry:
        await send_message_safe(
            update,
            context,
            "❌ Entry not found.",
        )
        return

    try:
        changed = db.approve_entry(
            entry_id,
            user.id,
        )
    except Exception:
        logger.exception(
            "Error approving entry %s",
            entry_id,
        )
        changed = False

    if not changed:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ This entry is no longer pending.\n\n"
                f"Current status: "
                f"{entry.get('status')}"
            ),
        )
        return

    await send_message_safe(
        update,
        context,
        f"✅ Entry #{entry_id} approved.",
    )

    try:
        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "🎉 YOUR MELANATED AZ "
                "RAFFLE ENTRY IS APPROVED!\n\n"
                f"🎟️ Entry #{entry_id}\n\n"
                "Your payment has been verified "
                "and your raffle entry is now active."
            ),
        )
    except Exception as exc:
        logger.error(
            "Unable to notify entrant %s: %s",
            entry["user_id"],
            exc,
        )


approve_entry = approve_raffle_entry


# ==========================================================
# DENY ENTRY
# ==========================================================

async def deny_raffle_entry(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return

    await answer_callback(
        update,
        "Denying entry...",
    )

    user = query.from_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    try:
        entry_id = int(
            query.data.split(":", 1)[1]
        )
    except Exception:
        await send_message_safe(
            update,
            context,
            "❌ Invalid entry ID.",
        )
        return

    entry = db.get_entry(
        entry_id
    )

    if not entry:
        await send_message_safe(
            update,
            context,
            "❌ Entry not found.",
        )
        return

    try:
        changed = db.deny_entry(
            entry_id,
            user.id,
        )
    except Exception:
        logger.exception(
            "Error denying entry %s",
            entry_id,
        )
        changed = False

    if not changed:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ This entry is no longer pending.\n\n"
                f"Current status: "
                f"{entry.get('status')}"
            ),
        )
        return

    await send_message_safe(
        update,
        context,
        f"❌ Entry #{entry_id} denied.",
    )

    try:
        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "❌ YOUR MELANATED AZ "
                "RAFFLE ENTRY WAS NOT APPROVED\n\n"
                f"Entry #{entry_id}\n\n"
                "Your payment could not be verified."
            ),
        )
    except Exception:
        pass


deny_entry = deny_raffle_entry


# ==========================================================
# RAFFLE ENTRIES
# ==========================================================

async def raffle_entries(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    await answer_callback(
        update,
        "Loading entries...",
    )

    raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            (
                "🎟️ RAFFLE ENTRIES\n\n"
                "There is currently no active raffle."
            ),
        )
        return

    approved = db.get_approved_entries(
        raffle_data["id"]
    )

    pending_all = db.get_pending_entries()

    pending_for_raffle = [
        entry
        for entry in pending_all
        if entry.get("raffle_id")
        == raffle_data["id"]
    ]

    lines = [
        "🎟️ RAFFLE ENTRIES",
        "",
        f"🎁 Prize: {raffle_data['prize']}",
        f"💵 Entry: "
        f"{money_text(raffle_data['price'])}",
        f"📌 Status: {raffle_data['status']}",
        "",
        f"✅ Approved Entries: {len(approved)}",
        f"⏳ Pending Entries: "
        f"{len(pending_for_raffle)}",
        "",
    ]

    if approved:

        lines.append(
            "APPROVED:"
        )

        for number, entry in enumerate(
            approved,
            start=1,
        ):

            name = (
                entry.get("display_name")
                or entry.get("username")
                or str(entry.get("user_id"))
            )

            lines.append(
                f"{number}. {name} "
                f"— Entry #{entry['id']}"
            )

    else:
        lines.append(
            "No approved entries yet."
        )

    if pending_for_raffle:

        lines.extend(
            [
                "",
                "⏳ PENDING:",
            ]
        )

        for entry in pending_for_raffle:

            name = (
                entry.get("display_name")
                or entry.get("username")
                or str(entry.get("user_id"))
            )

            lines.append(
                f"• {name} "
                f"— Entry #{entry['id']}"
            )

    await send_message_safe(
        update,
        context,
        "\n".join(lines),
    )


raffleentries = raffle_entries
raffle_entries_command = raffle_entries


# ==========================================================
# HISTORY
# ==========================================================

async def raffle_history(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    conn = db.get_connection()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM raffles
            ORDER BY id DESC
            """
        ).fetchall()

    finally:
        conn.close()

    if not rows:
        await send_message_safe(
            update,
            context,
            (
                "📚 RAFFLE HISTORY\n\n"
                "No raffle records were found."
            ),
        )
        return

    lines = [
        "📚 MELANATED AZ RAFFLE HISTORY",
        "",
    ]

    for row in rows:

        raffle_data = dict(row)

        conn = db.get_connection()

        try:

            count_row = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM raffle_entries
                WHERE raffle_id = ?
                AND status = 'approved'
                """,
                (
                    raffle_data["id"],
                ),
            ).fetchone()

        finally:
            conn.close()

        count = (
            count_row["total"]
            if count_row
            else 0
        )

        lines.append(
            (
                f"🎟️ Raffle #{raffle_data['id']}\n"
                f"🎁 {raffle_data['prize']}\n"
                f"💵 "
                f"{money_text(raffle_data['price'])}\n"
                f"📌 {raffle_data['status']}\n"
                f"👥 Approved Entries: {count}\n"
                f"📅 {raffle_data['created_at']}\n"
            )
        )

    text = "\n".join(lines)

    if len(text) <= 4000:

        await send_message_safe(
            update,
            context,
            text,
        )

        return

    current = ""

    for line in lines:

        if len(current) + len(line) > 3500:

            await send_message_safe(
                update,
                context,
                current,
            )

            current = ""

        current += line + "\n"

    if current:

        await send_message_safe(
            update,
            context,
            current,
        )


history = raffle_history
raffles = raffle_history


# ==========================================================
# VIEW RAFFLE BY ID
# ==========================================================

async def raffle_by_id(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    args = context.args or []

    if not args:
        await send_message_safe(
            update,
            context,
            "Use /raffleid <raffle_id>",
        )
        return

    try:
        raffle_id = int(args[0])
    except Exception:
        await send_message_safe(
            update,
            context,
            "❌ Invalid raffle ID.",
        )
        return

    raffle_data = db.get_raffle(
        raffle_id
    )

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            f"❌ Raffle #{raffle_id} not found.",
        )
        return

    entries = db.get_approved_entries(
        raffle_id
    )

    lines = [
        f"🎟️ RAFFLE #{raffle_id}",
        "",
        f"🎁 Prize: {raffle_data['prize']}",
        f"💵 Entry: "
        f"{money_text(raffle_data['price'])}",
        f"📌 Status: {raffle_data['status']}",
        f"⏳ Time: "
        f"{format_countdown(raffle_data['expires_at'])}",
        "",
        f"✅ Approved Entries: {len(entries)}",
        "",
    ]

    for number, entry in enumerate(
        entries,
        start=1,
    ):

        name = (
            entry.get("display_name")
            or entry.get("username")
            or str(entry.get("user_id"))
        )

        lines.append(
            f"{number}. {name} "
            f"— Entry #{entry['id']}"
        )

    await send_message_safe(
        update,
        context,
        "\n".join(lines),
    )


# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(
    update,
    context,
):
    raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "🎟️ No active raffle.",
        )
        return

    entries = db.get_approved_entries(
        raffle_data["id"]
    )

    await send_message_safe(
        update,
        context,
        (
            "🎟️ RAFFLE STATUS\n\n"
            f"🎁 Prize: {raffle_data['prize']}\n"
            f"💵 Entry: "
            f"{money_text(raffle_data['price'])}\n"
            f"📌 Status: {raffle_data['status']}\n"
            f"⏳ Time Remaining: "
            f"{format_countdown(raffle_data['expires_at'])}\n"
            f"👥 Entries: {len(entries)}"
        ),
    )


status = raffle_status
rafflestatus = raffle_status


# ==========================================================
# COUNTDOWN
# ==========================================================

async def update_raffle_countdown(
    context,
):
    """
    Updates the existing raffle post.

    Does not create duplicate raffle messages.
    """

    raffle_data = db.get_active_raffle()

    if not raffle_data:
        return

    expires = parse_datetime(
        raffle_data.get(
            "expires_at"
        )
    )

    if expires and expires <= utc_now():

        try:
            db.close_raffle(
                raffle_data["id"]
            )
        except Exception:
            logger.exception(
                "Unable to close expired raffle."
            )

        return

    chat_id = raffle_data.get(
        "chat_id"
    )

    message_id = raffle_data.get(
        "message_id"
    )

    if not chat_id or not message_id:
        return

    try:

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=build_raffle_text(
                raffle_data
            ),
            reply_markup=raffle_keyboard(),
        )

    except Exception as exc:

        logger.debug(
            "Raffle countdown update skipped: %s",
            exc,
        )


# ==========================================================
# CANCEL ACTIVE RAFFLE
# ==========================================================

async def cancel_active_raffle(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ No active raffle.",
        )
        return

    db.close_raffle(
        raffle_data["id"]
    )

    await send_message_safe(
        update,
        context,
        (
            f"🛑 Raffle #{raffle_data['id']} closed."
        ),
    )


cancelraffle = cancel_active_raffle


# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    args = context.args or []

    raffle_data = None

    if args:

        try:
            raffle_data = db.get_raffle(
                int(args[0])
            )
        except Exception:
            pass

    else:
        raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ No raffle found.",
        )
        return

    entries = db.get_approved_entries(
        raffle_data["id"]
    )

    if not entries:
        await send_message_safe(
            update,
            context,
            (
                f"❌ Raffle #{raffle_data['id']} "
                "has no approved entries."
            ),
        )
        return

    winner = random.choice(
        entries
    )

    name = (
        winner.get("display_name")
        or winner.get("username")
        or str(winner.get("user_id"))
    )

    await send_message_safe(
        update,
        context,
        (
            "🎉🎉🎉 WINNER DRAWN! 🎉🎉🎉\n\n"
            f"🎟️ Raffle #{raffle_data['id']}\n"
            f"🎁 Prize: {raffle_data['prize']}\n\n"
            f"🏆 WINNER:\n{name}\n\n"
            f"🆔 Entry #{winner['id']}"
        ),
    )

    try:
        db.close_raffle(
            raffle_data["id"]
        )
    except Exception:
        logger.exception(
            "Unable to close raffle after draw."
        )


draw = draw_raffle
drawraffle = draw_raffle


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    args = context.args or []

    raffle_id = None

    if args:

        try:
            raffle_id = int(
                args[0]
            )
        except Exception:
            await send_message_safe(
                update,
                context,
                "❌ Invalid raffle ID.",
            )
            return

    else:

        conn = db.get_connection()

        try:

            row = conn.execute(
                """
                SELECT id
                FROM raffles
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        finally:
            conn.close()

        if not row:
            await send_message_safe(
                update,
                context,
                "❌ No raffles found.",
            )
            return

        raffle_id = row["id"]

    entries = db.get_approved_entries(
        raffle_id
    )

    if not entries:
        await send_message_safe(
            update,
            context,
            "❌ No approved entries available.",
        )
        return

    winner = random.choice(
        entries
    )

    name = (
        winner.get("display_name")
        or winner.get("username")
        or str(winner.get("user_id"))
    )

    await send_message_safe(
        update,
        context,
        (
            "🔄 RAFFLE REROLL\n\n"
            f"🎟️ Raffle #{raffle_id}\n\n"
            f"🏆 NEW WINNER:\n{name}\n\n"
            f"🆔 Entry #{winner['id']}"
        ),
    )


reroll = reroll_raffle


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    args = context.args or []

    if len(args) < 2:
        await send_message_safe(
            update,
            context,
            (
                "Usage:\n"
                "/bonusentry USER_ID RAFFLE_ID"
            ),
        )
        return

    try:
        target_user_id = int(args[0])
        raffle_id = int(args[1])
    except Exception:
        await send_message_safe(
            update,
            context,
            "❌ Invalid user ID or raffle ID.",
        )
        return

    raffle_data = db.get_raffle(
        raffle_id
    )

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ Raffle not found.",
        )
        return

    conn = db.get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO raffle_entries (
                raffle_id,
                user_id,
                username,
                display_name,
                payment_method,
                status,
                approved_by,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, 'approved', ?, ?
            )
            """,
            (
                raffle_id,
                target_user_id,
                None,
                f"Bonus Entry {target_user_id}",
                "BONUS",
                user.id,
                utc_now().isoformat(),
            ),
        )

        entry_id = cursor.lastrowid

        conn.commit()

    except Exception:

        conn.rollback()

        logger.exception(
            "Unable to create bonus entry."
        )

        await send_message_safe(
            update,
            context,
            "❌ Unable to create bonus entry.",
        )

        return

    finally:
        conn.close()

    await send_message_safe(
        update,
        context,
        (
            "🎁 BONUS ENTRY ADDED\n\n"
            f"🎟️ Raffle #{raffle_id}\n"
            f"👤 User ID: {target_user_id}\n"
            f"🆔 Entry #{entry_id}"
        ),
    )


bonusentry = bonus_entry


# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    args = context.args or []

    if not args:
        await send_message_safe(
            update,
            context,
            "Usage: /removeentry ENTRY_ID",
        )
        return

    try:
        entry_id = int(args[0])
    except Exception:
        await send_message_safe(
            update,
            context,
            "❌ Invalid entry ID.",
        )
        return

    entry = db.get_entry(
        entry_id
    )

    if not entry:
        await send_message_safe(
            update,
            context,
            "❌ Entry not found.",
        )
        return

    changed = db.remove_entry(
        entry_id
    )

    if changed:
        await send_message_safe(
            update,
            context,
            f"🗑️ Entry #{entry_id} removed.",
        )
    else:
        await send_message_safe(
            update,
            context,
            "❌ Entry could not be removed.",
        )


removeentry = remove_raffle_entry


# ==========================================================
# ALL ENTRIES
# ==========================================================

async def all_raffle_entries(
    update,
    context,
):
    user = update.effective_user

    if not user or not is_admin_user(
        user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    conn = db.get_connection()

    try:

        rows = conn.execute(
            """
            SELECT
                e.*,
                r.prize,
                r.price,
                r.status AS raffle_status
            FROM raffle_entries e
            LEFT JOIN raffles r
                ON r.id = e.raffle_id
            ORDER BY e.id DESC
            """
        ).fetchall()

    finally:
        conn.close()

    if not rows:
        await send_message_safe(
            update,
            context,
            (
                "📋 DATABASE ENTRIES\n\n"
                "No raffle entries were found."
            ),
        )
        return

    lines = [
        "📋 ALL RAFFLE ENTRIES",
        "",
    ]

    for row in rows:

        row = dict(row)

        name = (
            row.get("display_name")
            or row.get("username")
            or str(row.get("user_id"))
        )

        lines.append(
            (
                f"#{row['id']} | "
                f"Raffle #{row['raffle_id']} | "
                f"{name} | "
                f"{row.get('status')}"
            )
        )

    text = "\n".join(lines)

    for index in range(
        0,
        len(text),
        3500,
    ):

        await send_message_safe(
            update,
            context,
            text[index:index + 3500],
        )


entries = all_raffle_entries


# ==========================================================
# CENTRAL CALLBACK ROUTER
# ==========================================================

async def raffle_callback_router(
    update,
    context,
):
    """
    Central raffle callback dispatcher.

    Safe to register in bot.py/admin.py.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "raffle_enter":
        return await raffle_enter_button(
            update,
            context,
        )

    if data in (
        "raffle_cashapp",
        "raffle_zelle",
    ):
        return await payment_button(
            update,
            context,
        )

    if data.startswith(
        "pay_cashapp:"
    ):
        return await payment_button(
            update,
            context,
        )

    if data.startswith(
        "pay_zelle:"
    ):
        return await payment_button(
            update,
            context,
        )

    if data.startswith(
        "approve_raffle:"
    ):
        return await raffle_approval_button(
            update,
            context,
        )

    if data.startswith(
        "cancel_raffle:"
    ):
        return await cancel_raffle_callback(
            update,
            context,
        )

    if data.startswith(
        "approve_entry:"
    ):
        return await approve_raffle_entry(
            update,
            context,
        )

    if data.startswith(
        "deny_entry:"
    ):
        return await deny_raffle_entry(
            update,
            context,
        )


# ==========================================================
# DATABASE COMPATIBILITY ALIASES
# ==========================================================

get_active_raffle = db.get_active_raffle
get_pending_raffle = db.get_pending_raffle
get_raffle = db.get_raffle

get_approved_entries = db.get_approved_entries
get_pending_entries = db.get_pending_entries

approve_entry_database = db.approve_entry
deny_entry_database = db.deny_entry
remove_entry_database = db.remove_entry

create_raffle_database = db.create_raffle
close_raffle_database = db.close_raffle


# ==========================================================
# COMPATIBILITY COMMAND ALIASES
# ==========================================================

pendingraffleentries = pending_entries

raffleentries = raffle_entries

raffle_entries_command = raffle_entries

raffleid = raffle_by_id


# ==========================================================
# EXPORTS
# ==========================================================

__all__ = [
    # Required current bot.py functions
    "raffle_private_start",
    "raffle_approval_button",
    "raffle_enter_button",

    # Main raffle
    "raffle",
    "raffle_command",

    # Creation
    "start_raffle",
    "startraffle",
    "create_raffle",

    # Entry
    "enter_raffle",
    "enter",
    "enterraffle",

    # Payments
    "payment_button",
    "paid_entry",
    "admin_payment_button",

    # Entry approval
    "approve_raffle_entry",
    "approve_entry",
    "deny_raffle_entry",
    "deny_entry",

    # Pending
    "pending_entries",
    "pending",
    "pendingraffleentries",

    # Raffle approval
    "approve_raffle_callback",
    "approve_raffle",
    "cancel_raffle_callback",
    "cancel_raffle",

    # Entries/history
    "raffle_entries",
    "raffleentries",
    "raffle_entries_command",
    "raffle_history",
    "history",
    "raffles",
    "raffle_by_id",
    "raffleid",
    "all_raffle_entries",
    "entries",

    # Status
    "raffle_status",
    "status",
    "rafflestatus",

    # Draw
    "draw_raffle",
    "draw",
    "drawraffle",

    # Reroll
    "reroll_raffle",
    "reroll",

    # Bonus/remove
    "bonus_entry",
    "bonusentry",
    "remove_raffle_entry",
    "removeentry",

    # Scheduler
    "update_raffle_countdown",

    # Callback
    "raffle_callback_router",

    # Helpers
    "build_raffle_text",
    "format_countdown",

    # Database compatibility
    "get_active_raffle",
    "get_pending_raffle",
    "get_raffle",
    "get_approved_entries",
    "get_pending_entries",
]
