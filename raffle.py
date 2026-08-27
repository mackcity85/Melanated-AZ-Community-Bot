# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# PRODUCTION-READY RAFFLE SYSTEM
#
# IMPORTANT:
# - Keeps the ORIGINAL approval system.
# - Raffle creation requires admin approval.
# - Payment entries require admin approval.
# - Uses raffle_database.py as the ONLY database layer.
# - NEVER deletes raffle.db.
# - NEVER recreates an existing database.
# - Preserves existing raffle records.
# - Supports existing bot.py function names.
# - Callback-safe for python-telegram-bot v21+.
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

# Safe initialization.
#
# raffle_database.initialize_database() must use
# CREATE TABLE IF NOT EXISTS.
#
# This does NOT delete existing raffle.db records.

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
# ADMIN CHECK
# ==========================================================

def is_admin_user(user_id):
    """Return True if Telegram user is configured as an admin."""

    try:
        admin_ids = {
            int(x)
            for x in ADMIN_IDS
        }

        return int(user_id) in admin_ids

    except Exception:
        return False


# ==========================================================
# TIME HELPERS
# ==========================================================

def utc_now():
    return datetime.now(timezone.utc)


def parse_datetime(value):
    """
    Safely parse ISO timestamps from the database.

    Supports:
        2026-08-27T20:00:00
        2026-08-27T20:00:00+00:00
        2026-08-27T20:00:00Z
    """

    if not value:
        return None

    try:
        value = str(value)

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        result = datetime.fromisoformat(value)

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result

    except Exception:
        logger.exception(
            "Unable to parse database datetime: %s",
            value,
        )

        return None


def format_countdown(expires_at):
    """Return a readable raffle countdown."""

    expires = parse_datetime(expires_at)

    if not expires:
        return "Unknown"

    remaining = expires - utc_now()

    total_seconds = int(
        remaining.total_seconds()
    )

    if total_seconds <= 0:
        return "EXPIRED"

    days, remainder = divmod(
        total_seconds,
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
        return f"{days}d {hours}h {minutes}m"

    if hours:
        return f"{hours}h {minutes}m"

    if minutes:
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"


# ==========================================================
# GENERAL HELPERS
# ==========================================================

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

    name = user.full_name

    if not name:
        name = user.username

    return name or str(user.id)


# ==========================================================
# SAFE MESSAGE HANDLING
# ==========================================================

async def send_message_safe(
    update,
    context,
    text,
    reply_markup=None,
    parse_mode=None,
):
    """
    Safely send a message from either:

    - normal Telegram message
    - callback query
    - private callback
    - fallback effective chat

    Prevents:

        AttributeError:
        'NoneType' object has no attribute 'reply_text'
    """

    if update and update.message:
        return await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    if update and update.callback_query:
        query = update.callback_query

        if query.message:
            return await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )

        if query.from_user:
            return await context.bot.send_message(
                chat_id=query.from_user.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )

    if update and update.effective_chat:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    return None


async def answer_callback(
    update,
    text=None,
):
    """Safely acknowledge an inline keyboard callback."""

    if not update or not update.callback_query:
        return

    try:
        await update.callback_query.answer(
            text=text or ""
        )

    except Exception:
        logger.debug(
            "Callback answer failed.",
            exc_info=True,
        )


# ==========================================================
# KEYBOARDS
# ==========================================================

def raffle_keyboard():
    """
    Public raffle keyboard.
    """

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
    """
    Private payment selection keyboard.
    """

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


def admin_entry_keyboard(
    entry_id,
):
    """
    ORIGINAL ENTRY APPROVAL SYSTEM.

    Admin must manually approve or deny
    payment entries.
    """

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


def raffle_approval_keyboard(
    raffle_id,
):
    """
    ORIGINAL RAFFLE APPROVAL SYSTEM.

    Admin must approve or cancel the raffle.
    """

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


# ==========================================================
# RAFFLE DISPLAY
# ==========================================================

def build_raffle_text(
    raffle_data,
):
    if not raffle_data:
        return "🎟️ No raffle information found."

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
        "🔒 Your entry and payment process "
        "is handled privately through the bot."
    )


# ==========================================================
# CURRENT RAFFLE
# ==========================================================

def get_current_raffle():
    """
    Return active raffle first.

    If no active raffle exists, return pending raffle.
    """

    raffle_data = db.get_active_raffle()

    if raffle_data:
        return raffle_data

    return db.get_pending_raffle()


# ==========================================================
# /raffle
# ==========================================================

async def raffle(
    update,
    context,
):
    raffle_data = get_current_raffle()

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
# /startraffle
# ==========================================================

async def start_raffle(
    update,
    context,
):
    """
    Start a raffle.

    Usage:

        /startraffle $100 Cash Prize | $5

    IMPORTANT:

    The original approval system is preserved.

    The raffle is created as PENDING.

    Admins receive:

        APPROVE RAFFLE
        CANCEL RAFFLE
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
                "/startraffle Prize | Entry Price\n\n"
                "Example:\n"
                "/startraffle $100 Cash Prize | $5"
            ),
        )
        return

    prize, price = raw.split(
        "|",
        1,
    )

    prize = prize.strip()
    price = price.strip()

    if not prize:
        await send_message_safe(
            update,
            context,
            "❌ Prize is required.",
        )
        return

    if not price:
        await send_message_safe(
            update,
            context,
            "❌ Entry price is required.",
        )
        return

    try:
        duration_days = int(
            os.environ.get(
                "RAFFLE_DURATION_DAYS",
                "7",
            )
        )

    except ValueError:
        duration_days = 7

    if duration_days <= 0:
        duration_days = 7

    expires_at = (
        utc_now()
        + timedelta(
            days=duration_days
        )
    ).replace(
        microsecond=0
    ).isoformat()

    try:
        raffle_id = db.create_raffle(
            prize=prize,
            price=price,
            expires_at=expires_at,
        )

    except Exception:
        logger.exception(
            "Unable to create raffle."
        )

        await send_message_safe(
            update,
            context,
            (
                "❌ I could not create the raffle.\n\n"
                "Check the bot logs for details."
            ),
        )

        return

    await send_message_safe(
        update,
        context,
        (
            "✅ RAFFLE CREATED\n\n"
            f"🎁 Prize: {prize}\n"
            f"💵 Entry: {price}\n"
            f"⏳ Duration: {duration_days} days\n"
            f"🆔 Raffle ID: #{raffle_id}\n\n"
            "📋 STATUS: PENDING APPROVAL\n\n"
            "The raffle has been sent to the admins "
            "for approval."
        ),
    )

    # ORIGINAL ADMIN APPROVAL SYSTEM
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
                    "to the Melanated AZ group."
                ),
                reply_markup=raffle_approval_keyboard(
                    raffle_id
                ),
            )

        except Exception:
            logger.exception(
                "Could not notify admin %s.",
                admin_id,
            )


startraffle = start_raffle
create_raffle = start_raffle


# ==========================================================
# REQUIRED BOT.PY COMPATIBILITY FUNCTION
# ==========================================================

async def raffle_private_start(
    update,
    context,
):
    """
    Compatibility entry point expected by bot.py.

    This is the PRIVATE raffle start flow.

    It intentionally uses the SAME approval/payment system.
    """

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

    # If this callback came from the group raffle button,
    # tell the user to check their private messages.
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "👋 Hi! This is the Melanated AZ Raffle Bot.\n\n"
                "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
                f"🎁 Prize: {raffle_data['prize']}\n"
                f"💵 Entry: {money_text(raffle_data['price'])}\n"
                f"⏳ Time Remaining: "
                f"{format_countdown(raffle_data['expires_at'])}\n\n"
                "Your entry is handled privately.\n\n"
                "Choose your payment method below."
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
                "I've sent your raffle entry instructions "
                "to your inbox."
            ),
        )

    except Exception:
        logger.exception(
            "Unable to start private raffle flow for %s.",
            user.id,
        )

        await send_message_safe(
            update,
            context,
            (
                "⚠️ I couldn't send you a private message.\n\n"
                "Please open the Melanated AZ Raffle Bot "
                "and press START, then try again."
            ),
        )


# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(
    update,
    context,
):
    """
    Main raffle entry handler.

    Uses the private raffle flow.
    """

    await answer_callback(
        update,
        "Opening private entry...",
    )

    return await raffle_private_start(
        update,
        context,
    )


# ==========================================================
# REQUIRED BOT.PY COMPATIBILITY FUNCTION
# ==========================================================

async def raffle_enter_button(
    update,
    context,
):
    """
    Compatibility function expected by bot.py.

    Kept separate from enter_raffle so older/newer bot.py
    versions can use either name.
    """

    return await enter_raffle(
        update,
        context,
    )


enter = enter_raffle
enterraffle = enter_raffle


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update,
    context,
):
    """
    Handles Cash App / Zelle selection.

    Entry is created as PENDING.

    Admin approval is still required.
    """

    query = update.callback_query

    await answer_callback(
        update
    )

    if not query or not query.from_user:
        return

    data = query.data or ""

    parts = data.split(":")

    # Handles:
    #
    # pay_cashapp:123
    # pay_zelle:123
    #
    # Also safely ignores malformed callbacks.

    if len(parts) != 2:
        await send_message_safe(
            update,
            context,
            "❌ Invalid payment request.",
        )
        return

    method = parts[0]

    try:
        raffle_id = int(parts[1])

    except ValueError:
        await send_message_safe(
            update,
            context,
            "❌ Invalid raffle ID.",
        )
        return

    if method not in (
        "pay_cashapp",
        "pay_zelle",
    ):
        await send_message_safe(
            update,
            context,
            "❌ Invalid payment method.",
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

    # Do not allow payment for closed/cancelled raffles.
    status = str(
        raffle_data.get(
            "status",
            ""
        )
    ).lower()

    if status != "active":
        await send_message_safe(
            update,
            context,
            (
                "❌ This raffle is not currently accepting "
                "entries."
            ),
        )
        return

    expires = parse_datetime(
        raffle_data.get("expires_at")
    )

    if expires and expires <= utc_now():

        try:
            db.close_raffle(
                raffle_id
            )
        except Exception:
            logger.exception(
                "Could not close expired raffle %s.",
                raffle_id,
            )

        await send_message_safe(
            update,
            context,
            "❌ This raffle has expired.",
        )

        return

    user = query.from_user

    payment_method = (
        "Cash App"
        if method == "pay_cashapp"
        else "Zelle"
    )

    try:
        entry_id = db.add_raffle_entry(
            raffle_id=raffle_id,
            user_id=user.id,
            username=user.username,
            display_name=safe_display_name(user),
            payment_method=payment_method,
        )

    except Exception:
        logger.exception(
            "Unable to create raffle entry."
        )

        await send_message_safe(
            update,
            context,
            (
                "❌ I could not create your raffle entry.\n\n"
                "Please try again."
            ),
        )

        return

    if entry_id is None:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ You already have a pending or "
                "approved entry for this raffle."
            ),
        )

        return

    if method == "pay_cashapp":

        payment_details = (
            "💵 CASH APP PAYMENT\n\n"
            f"Send {money_text(raffle_data['price'])} to:\n"
            f"{CASHAPP_TAG or 'Cash App information unavailable'}"
        )

        if CASHAPP_URL:
            payment_details += (
                f"\n\n{CASHAPP_URL}"
            )

    else:

        payment_details = (
            "💳 ZELLE PAYMENT\n\n"
            f"Send {money_text(raffle_data['price'])} to:\n"
            f"{ZELLE_PHONE or 'Zelle information unavailable'}"
        )

    await send_message_safe(
        update,
        context,
        (
            "✅ ENTRY REQUEST CREATED\n\n"
            f"🎟️ Raffle #{raffle_id}\n"
            f"🎁 Prize: {raffle_data['prize']}\n"
            f"💵 Entry: {money_text(raffle_data['price'])}\n"
            f"💳 Method: {payment_method}\n"
            f"🆔 Entry: #{entry_id}\n\n"
            f"{payment_details}\n\n"
            "📸 After sending payment, send your "
            "payment confirmation/screenshot to the bot.\n\n"
            "⏳ Your entry will remain PENDING until "
            "an admin verifies your payment."
        ),
    )

    await notify_admins_new_entry(
        context,
        entry_id,
    )


# ==========================================================
# REQUIRED BOT.PY COMPATIBILITY FUNCTION
# ==========================================================

async def raffle_approval_button(
    update,
    context,
):
    """
    Compatibility callback expected by bot.py.

    IMPORTANT:

    This is NOT automatic approval.

    It routes the original raffle approval callback.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data.startswith("approve_raffle:"):
        return await approve_raffle_callback(
            update,
            context,
        )

    if data.startswith("cancel_raffle:"):
        return await cancel_raffle_callback(
            update,
            context,
        )

    await answer_callback(
        update,
        "Unknown raffle action.",
    )


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

async def approve_raffle_callback(
    update,
    context,
):
    """
    ORIGINAL ADMIN RAFFLE APPROVAL.
    """

    query = update.callback_query

    await answer_callback(
        update,
        "Approving raffle...",
    )

    if not query or not query.from_user:
        return

    if not is_admin_user(
        query.from_user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ You are not authorized.",
        )
        return

    data = query.data or ""

    try:
        raffle_id = int(
            data.split(
                ":",
                1
            )[1]
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

    if str(
        raffle_data.get(
            "status",
            ""
        )
    ).lower() != "pending":

        await send_message_safe(
            update,
            context,
            (
                "⚠️ This raffle is no longer pending.\n\n"
                f"Current status: "
                f"{raffle_data.get('status')}"
            ),
        )
        return

    try:
        changed = db.approve_raffle(
            raffle_id
        )

    except Exception:
        logger.exception(
            "Unable to approve raffle %s.",
            raffle_id,
        )

        await send_message_safe(
            update,
            context,
            "❌ Database error while approving raffle.",
        )
        return

    if not changed:
        await send_message_safe(
            update,
            context,
            "⚠️ This raffle could not be approved.",
        )
        return

    raffle_data = db.get_raffle(
        raffle_id
    )

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

    except Exception:
        logger.exception(
            "Approved raffle %s but could not post it.",
            raffle_id,
        )

        await send_message_safe(
            update,
            context,
            (
                "⚠️ Raffle was approved, but I could "
                "not post it to the raffle group.\n\n"
                "Check the bot's group permissions."
            ),
        )

        return

    await send_message_safe(
        update,
        context,
        (
            "✅ RAFFLE APPROVED\n\n"
            f"🎟️ Raffle #{raffle_id}\n"
            "📢 The raffle has been posted to the group."
        ),
    )


approve_raffle = approve_raffle_callback


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle_callback(
    update,
    context,
):
    """
    ORIGINAL ADMIN RAFFLE CANCELLATION.
    """

    query = update.callback_query

    await answer_callback(
        update,
        "Cancelling raffle...",
    )

    if not query or not query.from_user:
        return

    if not is_admin_user(
        query.from_user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    data = query.data or ""

    try:
        raffle_id = int(
            data.split(
                ":",
                1
            )[1]
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
            "Unable to cancel raffle %s.",
            raffle_id,
        )

        await send_message_safe(
            update,
            context,
            "❌ Database error while cancelling raffle.",
        )
        return

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
# PAYMENT / ADMIN ENTRY VIEW
# ==========================================================

async def paid_entry(
    update,
    context,
):
    """
    Display an entry to an admin.

    Approval is still handled separately by:

        approve_entry
        deny_entry
    """

    query = update.callback_query

    if query:
        await answer_callback(
            update,
            "Loading payment entry...",
        )

    if query:
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
            entry_id = int(args[0])

        except Exception:
            entry_id = None

    if not entry_id:
        await send_message_safe(
            update,
            context,
            "💳 No entry ID was provided.",
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

    user = update.effective_user

    markup = None

    if user and is_admin_user(
        user.id
    ):
        markup = admin_entry_keyboard(
            entry_id
        )

    await send_message_safe(
        update,
        context,
        (
            "💳 RAFFLE PAYMENT ENTRY\n\n"
            f"🆔 Entry: #{entry['id']}\n"
            f"👤 Name: "
            f"{entry.get('display_name') or 'Unknown'}\n"
            f"👤 User ID: "
            f"{entry.get('user_id')}\n"
            f"💳 Payment: "
            f"{entry.get('payment_method') or 'Unknown'}\n"
            f"📌 Status: "
            f"{entry.get('status') or 'Unknown'}\n\n"
            "Verify the payment before approving "
            "this entry."
        ),
        reply_markup=markup,
    )


async def admin_payment_button(
    update,
    context,
):
    return await paid_entry(
        update,
        context,
    )


# ==========================================================
# NOTIFY ADMINS OF PAYMENT
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
        f"🎟️ Raffle #{entry['raffle_id']}\n"
        f"🎁 Prize: {raffle_data['prize']}\n"
        f"💵 Entry Price: "
        f"{money_text(raffle_data['price'])}\n"
        f"🆔 Entry: #{entry['id']}\n"
        f"👤 Name: "
        f"{entry.get('display_name') or 'Unknown'}\n"
        f"👤 Username: {username_text}\n"
        f"💳 Payment: "
        f"{entry.get('payment_method') or 'Unknown'}\n\n"
        "⚠️ VERIFY PAYMENT BEFORE APPROVING."
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

        except Exception:
            logger.exception(
                "Unable to notify admin %s "
                "about entry %s.",
                admin_id,
                entry_id,
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

    try:
        entries = db.get_pending_entries()

    except Exception:
        logger.exception(
            "Unable to retrieve pending entries."
        )

        await send_message_safe(
            update,
            context,
            "❌ Could not retrieve pending entries.",
        )

        return

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
    """
    ORIGINAL PAYMENT APPROVAL SYSTEM.

    Admin must manually approve payment.
    """

    query = update.callback_query

    await answer_callback(
        update,
        "Approving entry...",
    )

    if not query or not query.from_user:
        return

    if not is_admin_user(
        query.from_user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    data = query.data or ""

    try:
        entry_id = int(
            data.split(
                ":",
                1
            )[1]
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

    if str(
        entry.get(
            "status",
            ""
        )
    ).lower() != "pending":

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

    try:
        changed = db.approve_entry(
            entry_id,
            query.from_user.id,
        )

    except Exception:
        logger.exception(
            "Unable to approve entry %s.",
            entry_id,
        )

        await send_message_safe(
            update,
            context,
            "❌ Database error while approving entry.",
        )
        return

    if not changed:
        await send_message_safe(
            update,
            context,
            "⚠️ Entry could not be approved.",
        )
        return

    await send_message_safe(
        update,
        context,
        f"✅ Entry #{entry_id} approved.",
    )

    # Notify entrant.
    try:
        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "🎉 YOUR MELANATED AZ RAFFLE ENTRY "
                "IS APPROVED!\n\n"
                f"🎟️ Raffle #{entry['raffle_id']}\n"
                f"🆔 Entry #{entry_id}\n\n"
                "Your payment has been verified "
                "and your entry is now active."
            ),
        )

    except Exception:
        logger.exception(
            "Unable to notify entrant %s.",
            entry["user_id"],
        )


approve_entry = approve_raffle_entry


# ==========================================================
# DENY ENTRY
# ==========================================================

async def deny_raffle_entry(
    update,
    context,
):
    """
    ORIGINAL PAYMENT DENIAL SYSTEM.
    """

    query = update.callback_query

    await answer_callback(
        update,
        "Denying entry...",
    )

    if not query or not query.from_user:
        return

    if not is_admin_user(
        query.from_user.id
    ):
        await send_message_safe(
            update,
            context,
            "❌ Not authorized.",
        )
        return

    data = query.data or ""

    try:
        entry_id = int(
            data.split(
                ":",
                1
            )[1]
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

    if str(
        entry.get(
            "status",
            ""
        )
    ).lower() != "pending":

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

    try:
        changed = db.deny_entry(
            entry_id,
            query.from_user.id,
        )

    except Exception:
        logger.exception(
            "Unable to deny entry %s.",
            entry_id,
        )

        await send_message_safe(
            update,
            context,
            "❌ Database error while denying entry.",
        )
        return

    if not changed:
        await send_message_safe(
            update,
            context,
            "⚠️ Entry could not be denied.",
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
                "❌ YOUR MELANATED AZ RAFFLE ENTRY "
                "WAS NOT APPROVED\n\n"
                f"🎟️ Raffle #{entry['raffle_id']}\n"
                f"🆔 Entry #{entry_id}\n\n"
                "Your payment could not be verified."
            ),
        )

    except Exception:
        logger.exception(
            "Unable to notify denied entrant %s.",
            entry["user_id"],
        )


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
        "Loading raffle entries...",
    )

    raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            (
                "🎟️ RAFFLE ENTRIES\n\n"
                "There is currently no active raffle.\n\n"
                "Use /history to view previous raffles."
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
        f"💵 Entry: {money_text(raffle_data['price'])}",
        f"📌 Status: {raffle_data['status']}",
        "",
        f"✅ Approved Entries: {len(approved)}",
        f"⏳ Pending Entries: {len(pending_for_raffle)}",
        "",
    ]

    if approved:

        lines.append("APPROVED:")

        for number, entry in enumerate(
            approved,
            start=1,
        ):

            name = (
                entry.get("display_name")
                or entry.get("username")
                or f"User {entry.get('user_id')}"
            )

            lines.append(
                f"{number}. {name} — Entry #{entry['id']}"
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
                or f"User {entry.get('user_id')}"
            )

            lines.append(
                f"• {name} — Entry #{entry['id']}"
            )

    await send_message_safe(
        update,
        context,
        "\n".join(lines),
    )


raffleentries = raffle_entries
raffle_entries_command = raffle_entries


# ==========================================================
# RAFFLE HISTORY
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
                f"💵 {money_text(raffle_data['price'])}\n"
                f"📌 {raffle_data['status']}\n"
                f"👥 Approved Entries: {count}\n"
                f"📅 {raffle_data['created_at']}\n"
            )
        )

    await send_long_message(
        update,
        context,
        "\n".join(lines),
    )


history = raffle_history
raffles = raffle_history


# ==========================================================
# LONG MESSAGE HELPER
# ==========================================================

async def send_long_message(
    update,
    context,
    text,
    chunk_size=3500,
):
    """
    Telegram messages have a maximum size.

    Split long admin/history messages safely.
    """

    if len(text) <= chunk_size:
        await send_message_safe(
            update,
            context,
            text,
        )
        return

    current = ""

    for line in text.splitlines():

        if len(current) + len(line) + 1 > chunk_size:

            if current:
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

    except ValueError:
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
        f"💵 Entry: {money_text(raffle_data['price'])}",
        f"📌 Status: {raffle_data['status']}",
        (
            "⏳ Time Remaining: "
            f"{format_countdown(raffle_data['expires_at'])}"
        ),
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
            f"{number}. {name} — Entry #{entry['id']}"
        )

    await send_long_message(
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
            f"💵 Entry: {money_text(raffle_data['price'])}\n"
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
    Background job.

    Updates the existing raffle post.

    It does NOT create duplicate posts.
    """

    raffle_data = db.get_active_raffle()

    if not raffle_data:
        return

    expires = parse_datetime(
        raffle_data.get("expires_at")
    )

    if expires and expires <= utc_now():

        try:
            db.close_raffle(
                raffle_data["id"]
            )

        except Exception:
            logger.exception(
                "Could not close expired raffle."
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

        # "Message is not modified" is normal.
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
        f"🛑 Raffle #{raffle_data['id']} closed.",
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

    if args:

        try:
            raffle_id = int(args[0])

        except ValueError:
            await send_message_safe(
                update,
                context,
                "❌ Invalid raffle ID.",
            )
            return

        raffle_data = db.get_raffle(
            raffle_id
        )

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

    winner = random.SystemRandom().choice(
        entries
    )

    name = (
        winner.get("display_name")
        or winner.get("username")
        or f"User {winner.get('user_id')}"
    )

    await send_message_safe(
        update,
        context,
        (
            "🎉🎉🎉 WINNER DRAWN! 🎉🎉🎉\n\n"
            f"🎟️ Raffle #{raffle_data['id']}\n"
            f"🎁 Prize: {raffle_data['prize']}\n\n"
            "🏆 WINNER:\n"
            f"{name}\n\n"
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

    if args:

        try:
            raffle_id = int(args[0])

        except ValueError:
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

    winner = random.SystemRandom().choice(
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
            "🏆 NEW WINNER:\n"
            f"{name}\n\n"
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
    """
    Give a user an additional approved entry.

    Usage:

        /bonusentry USER_ID RAFFLE_ID
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

    except ValueError:
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
            "❌ Could not create bonus entry.",
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

    except ValueError:
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
        changed = db.remove_entry(
            entry_id
        )

    except Exception:
        logger.exception(
            "Unable to remove entry %s.",
            entry_id,
        )

        await send_message_safe(
            update,
            context,
            "❌ Database error while removing entry.",
        )

        return

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

    await send_long_message(
        update,
        context,
        "\n".join(lines),
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
    Central raffle callback handler.

    This supports all raffle buttons.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # Public entry button.
    if data == "raffle_enter":
        return await raffle_enter_button(
            update,
            context,
        )

    # Public payment buttons.
    #
    # These open the private payment process.
    if data == "raffle_cashapp":
        return await raffle_private_start(
            update,
            context,
        )

    if data == "raffle_zelle":
        return await raffle_private_start(
            update,
            context,
        )

    # Private payment buttons.
    if data.startswith("pay_cashapp:"):
        return await payment_button(
            update,
            context,
        )

    if data.startswith("pay_zelle:"):
        return await payment_button(
            update,
            context,
        )

    # Entry approvals.
    if data.startswith("approve_entry:"):
        return await approve_raffle_entry(
            update,
            context,
        )

    if data.startswith("deny_entry:"):
        return await deny_raffle_entry(
            update,
            context,
        )

    # Raffle approvals.
    if data.startswith("approve_raffle:"):
        return await approve_raffle_callback(
            update,
            context,
        )

    if data.startswith("cancel_raffle:"):
        return await cancel_raffle_callback(
            update,
            context,
        )

    await answer_callback(
        update,
        "Unknown raffle action.",
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
# COMMAND COMPATIBILITY ALIASES
# ==========================================================

pendingraffleentries = pending_entries

approveraﬄeentry = approve_raffle_entry

denyraffleentry = deny_raffle_entry


# ==========================================================
# REQUIRED EXPORTS
# ==========================================================

__all__ = [

    # Main raffle
    "raffle",
    "raffle_command",

    # Creation
    "start_raffle",
    "startraffle",
    "create_raffle",

    # REQUIRED BOT.PY FUNCTIONS
    "raffle_private_start",
    "raffle_approval_button",
    "raffle_enter_button",

    # Entry
    "enter_raffle",
    "enter",
    "enterraffle",

    # Payment
    "payment_button",
    "paid_entry",
    "admin_payment_button",

    # Entry administration
    "pending_entries",
    "pending",
    "raffle_entries",
    "raffleentries",
    "raffle_entries_command",

    "approve_raffle_entry",
    "approve_entry",

    "deny_raffle_entry",
    "deny_entry",

    "remove_raffle_entry",
    "removeentry",

    # Raffle approval
    "approve_raffle_callback",
    "approve_raffle",

    "cancel_raffle_callback",
    "cancel_raffle",

    # Status/history
    "raffle_status",
    "status",
    "rafflestatus",

    "raffle_history",
    "history",
    "raffles",

    "raffle_by_id",
    "all_raffle_entries",
    "entries",

    # Draw
    "draw_raffle",
    "draw",
    "drawraffle",

    "reroll_raffle",
    "reroll",

    # Bonus/remove
    "bonus_entry",
    "bonusentry",

    # Scheduler
    "update_raffle_countdown",

    # Callback router
    "raffle_callback_router",

    # Database compatibility
    "get_active_raffle",
    "get_pending_raffle",
    "get_raffle",

    "get_approved_entries",
    "get_pending_entries",

    # Helpers
    "format_countdown",
    "build_raffle_text",
    "is_admin_user",
]
