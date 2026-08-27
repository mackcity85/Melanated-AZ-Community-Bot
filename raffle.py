# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Complete raffle system
#
# IMPORTANT:
# - Uses raffle_database.py as the ONLY database layer.
# - Existing raffle.db is NOT deleted or recreated.
# - Supports old database records.
# - Callback-safe admin functions.
# - Private raffle entry/payment flow.
# - Cash App / Zelle payment verification.
# - Admin approval / denial.
# - Raffle history.
# - Draw / reroll.
# - Bonus entries.
# - Remove entries.
# ==========================================================

import logging
import random
from datetime import datetime, timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

import raffle_database as db


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# DATABASE
# ==========================================================

# Make absolutely sure the existing database is initialized.
# initialize_database() uses CREATE TABLE IF NOT EXISTS and
# therefore does NOT delete existing records.
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
# HELPERS
# ==========================================================

def is_admin_user(user_id):
    """Return True when the Telegram user is an administrator."""
    try:
        return int(user_id) in [int(x) for x in ADMIN_IDS]
    except Exception:
        return False


def utc_now():
    return datetime.now(timezone.utc)


def parse_datetime(value):
    """
    Safely parse database datetime strings.

    Existing databases may contain ISO timestamps with or without
    timezone information.
    """
    if not value:
        return None

    try:
        value = str(value)

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        result = datetime.fromisoformat(value)

        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)

        return result
    except Exception:
        return None


def format_countdown(expires_at):
    """Return a human-readable raffle countdown."""
    expires = parse_datetime(expires_at)

    if not expires:
        return "Unknown"

    remaining = expires - utc_now()

    seconds = int(remaining.total_seconds())

    if seconds <= 0:
        return "EXPIRED"

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days:
        return f"{days}d {hours}h {minutes}m"

    if hours:
        return f"{hours}h {minutes}m"

    if minutes:
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"


def money_text(value):
    if value is None:
        return "$0"

    value = str(value).strip()

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


async def send_message_safe(
    update,
    context,
    text,
    reply_markup=None,
    parse_mode=None,
):
    """
    Send a message safely whether the handler came from:

    - /command
    - callback button
    - another admin handler

    This specifically fixes:

        AttributeError:
        'NoneType' object has no attribute 'reply_text'
    """

    # Normal command/message
    if update and update.message:
        return await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    # Callback query
    if update and update.callback_query:
        query = update.callback_query

        if query.message:
            return await query.message.reply_text(
                text,
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

    # Fallback
    if update and update.effective_chat:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    return None


async def answer_callback(update, text=None):
    """Safely answer an inline button callback."""
    if not update or not update.callback_query:
        return

    try:
        await update.callback_query.answer(
            text=text or ""
        )
    except Exception:
        pass


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


def payment_keyboard(entry_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 CASH APP",
                    callback_data=f"pay_cashapp:{entry_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 ZELLE",
                    callback_data=f"pay_zelle:{entry_id}",
                )
            ]
        ]
    )


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


def raffle_approval_keyboard(raffle_id):
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
# RAFFLE TEXT
# ==========================================================

def build_raffle_text(raffle):
    if not raffle:
        return "🎟️ No raffle information found."

    prize = raffle.get("prize", "Unknown Prize")
    price = money_text(raffle.get("price", ""))

    status = str(
        raffle.get("status", "unknown")
    ).upper()

    countdown = format_countdown(
        raffle.get("expires_at")
    )

    return (
        "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry: {price}\n"
        f"⏳ Time Remaining: {countdown}\n"
        f"📌 Status: {status}\n\n"
        "Want to enter?\n"
        "Tap ENTER RAFFLE below.\n\n"
        "🔒 Your entry/payment process is handled "
        "privately through the bot."
    )


# ==========================================================
# GET CURRENT RAFFLE
# ==========================================================

def get_current_raffle():
    """
    Return the current active raffle.

    Falls back to pending raffle when no active raffle exists.
    """

    raffle = db.get_active_raffle()

    if raffle:
        return raffle

    return db.get_pending_raffle()


# ==========================================================
# /raffle
# ==========================================================

async def raffle(update, context):
    raffle_data = db.get_active_raffle()

    if not raffle_data:
        raffle_data = db.get_pending_raffle()

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
        build_raffle_text(raffle_data),
        reply_markup=raffle_keyboard(),
    )


# Alias commonly used by older bot.py versions.
raffle_command = raffle


# ==========================================================
# /startraffle
# ==========================================================

async def start_raffle(update, context):
    """
    Admin command.

    Usage:

        /startraffle $100 Cash Prize | $5

    The raffle is created as pending until an admin approves it.
    """

    if not update.effective_user:
        return

    if not is_admin_user(update.effective_user.id):
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

    prize, price = raw.split("|", 1)

    prize = prize.strip()
    price = price.strip()

    if not prize or not price:
        await send_message_safe(
            update,
            context,
            "❌ Prize and entry price are required.",
        )
        return

    # Default duration is read from config/environment.
    import os

    duration_days = int(
        os.environ.get(
            "RAFFLE_DURATION_DAYS",
            "7",
        )
    )

    expires_at = (
        utc_now()
        .replace(microsecond=0)
        + __import__("datetime").timedelta(
            days=duration_days
        )
    ).isoformat()

    raffle_id = db.create_raffle(
        prize=prize,
        price=price,
        expires_at=expires_at,
    )

    raffle_data = db.get_raffle(raffle_id)

    await send_message_safe(
        update,
        context,
        (
            "✅ RAFFLE CREATED\n\n"
            f"🎁 Prize: {prize}\n"
            f"💵 Entry: {price}\n"
            f"⏳ Duration: {duration_days} days\n\n"
            "The raffle is currently PENDING admin approval."
        ),
    )

    # Notify all configured admins.
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "🎟️ RAFFLE APPROVAL REQUIRED\n\n"
                    f"🎁 Prize: {prize}\n"
                    f"💵 Entry: {price}\n"
                    f"⏳ Duration: {duration_days} days\n"
                    f"🆔 Raffle ID: {raffle_id}"
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


# Common aliases.
startraffle = start_raffle
create_raffle = start_raffle


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

async def approve_raffle_callback(
    update,
    context,
):
    query = update.callback_query

    await answer_callback(
        update,
        "Approving raffle...",
    )

    if not query or not query.from_user:
        return

    if not is_admin_user(query.from_user.id):
        await send_message_safe(
            update,
            context,
            "❌ You are not authorized.",
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

    raffle_data = db.get_raffle(raffle_id)

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ Raffle not found.",
        )
        return

    changed = db.approve_raffle(
        raffle_id
    )

    if not changed:
        await send_message_safe(
            update,
            context,
            "⚠️ This raffle is no longer pending.",
        )
        return

    raffle_data = db.get_raffle(raffle_id)

    # Post approved raffle into the configured group.
    try:
        message = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=build_raffle_text(raffle_data),
            reply_markup=raffle_keyboard(),
        )

        db.set_raffle_post(
            raffle_id,
            RAFFLE_CHAT_ID,
            message.message_id,
        )

    except Exception as exc:
        logger.exception(
            "Could not post approved raffle: %s",
            exc,
        )

        await send_message_safe(
            update,
            context,
            (
                "⚠️ Raffle approved, but I could not "
                "post it to the raffle chat.\n\n"
                f"Error: {exc}"
            ),
        )
        return

    await send_message_safe(
        update,
        context,
        "✅ Raffle approved and posted to the group.",
    )


approve_raffle = approve_raffle_callback


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle_callback(
    update,
    context,
):
    query = update.callback_query

    await answer_callback(
        update,
        "Cancelling raffle...",
    )

    if not query or not query.from_user:
        return

    if not is_admin_user(query.from_user.id):
        await send_message_safe(
            update,
            context,
            "❌ You are not authorized.",
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

    changed = db.cancel_pending_raffle(
        raffle_id
    )

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
# ENTER RAFFLE BUTTON
# ==========================================================

async def enter_raffle(
    update,
    context,
):
    query = update.callback_query

    await answer_callback(
        update,
        "Opening private entry...",
    )

    if not query or not query.from_user:
        return

    raffle_data = db.get_active_raffle()

    if not raffle_data:
        await send_message_safe(
            update,
            context,
            "❌ There is currently no active raffle.",
        )
        return

    user = query.from_user

    # Entry happens privately.
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "👋 Hi! This is the Melanated AZ Raffle Bot.\n\n"
                "You are entering the raffle from:\n"
                "🎟️ Melanated AZ\n\n"
                f"🎁 Prize: {raffle_data['prize']}\n"
                f"💵 Entry: {money_text(raffle_data['price'])}\n\n"
                "Your raffle entry is handled privately "
                "so other group members do not see you enter.\n\n"
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
                "I've sent you the raffle entry instructions "
                "in your inbox."
            ),
        )

    except Exception:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ I couldn't message you privately.\n\n"
                "Please open the Melanated AZ Raffle Bot "
                "and press START, then try again."
            ),
        )


# Common aliases.
enter = enter_raffle
enterraffle = enter_raffle


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update,
    context,
):
    query = update.callback_query

    await answer_callback(update)

    if not query or not query.from_user:
        return

    parts = query.data.split(":")

    if len(parts) != 2:
        return

    method = parts[0]
    raffle_id = parts[1]

    try:
        raffle_id = int(raffle_id)
    except Exception:
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

    user = query.from_user

    payment_method = (
        "Cash App"
        if method == "pay_cashapp"
        else "Zelle"
    )

    # Create the private pending entry.
    entry_id = db.add_raffle_entry(
        raffle_id=raffle_id,
        user_id=user.id,
        username=user.username,
        display_name=safe_display_name(user),
        payment_method=payment_method,
    )

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
        payment_text = (
            "💵 CASH APP PAYMENT\n\n"
            f"Send {money_text(raffle_data['price'])} to:\n"
            f"{CASHAPP_TAG or 'Cash App information unavailable'}\n\n"
            "After sending payment, send your payment "
            "confirmation/screenshot to the bot.\n\n"
            "⚠️ Payment must be verified by Melanated AZ "
            "before your raffle entry is approved."
        )

    else:
        payment_text = (
            "💳 ZELLE PAYMENT\n\n"
            f"Send {money_text(raffle_data['price'])} to:\n"
            f"{ZELLE_PHONE or 'Zelle information unavailable'}\n\n"
            "After sending payment, send your payment "
            "confirmation/screenshot to the bot.\n\n"
            "⚠️ Payment must be verified by Melanated AZ "
            "before your raffle entry is approved."
        )

    await send_message_safe(
        update,
        context,
        (
            "✅ ENTRY REQUEST CREATED\n\n"
            f"🎁 {raffle_data['prize']}\n"
            f"💵 {money_text(raffle_data['price'])}\n"
            f"💳 Method: {payment_method}\n"
            f"🆔 Entry: #{entry_id}\n\n"
            + payment_text
        ),
    )

    # Notify admins.
    await notify_admins_new_entry(
        context,
        entry_id,
    )


# ==========================================================
# PAID ENTRY
# ==========================================================

async def paid_entry(
    update,
    context,
):
    """
    Compatibility function required by admin.py.

    This handles an admin/payment confirmation request and
    safely works whether called from a message or callback.
    """

    query = update.callback_query

    if query:
        await answer_callback(
            update,
            "Processing payment...",
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
            (
                "💳 Payment verification\n\n"
                "No entry ID was provided."
            ),
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
            "💳 PAYMENT ENTRY\n\n"
            f"🆔 Entry: #{entry['id']}\n"
            f"👤 {entry.get('display_name') or 'Unknown'}\n"
            f"💳 {entry.get('payment_method') or 'Unknown'}\n"
            f"📌 Status: {entry.get('status')}\n\n"
            "Payment must be verified by Melanated AZ "
            "before approval."
        ),
        reply_markup=admin_entry_keyboard(
            entry_id
        )
        if is_admin_user(
            update.effective_user.id
        )
        else None,
    )


# ==========================================================
# ADMIN PAYMENT ENTRY
# ==========================================================

async def admin_payment_button(
    update,
    context,
):
    return await paid_entry(
        update,
        context,
    )


# ==========================================================
# NOTIFY ADMINS
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

    text = (
        "💰 RAFFLE PAYMENT PENDING\n\n"
        f"🎁 Prize: {raffle_data['prize']}\n"
        f"💵 Entry Price: {money_text(raffle_data['price'])}\n"
        f"🆔 Entry: #{entry['id']}\n"
        f"👤 Name: {entry.get('display_name') or 'Unknown'}\n"
        f"👤 Username: @{entry['username']}"
        if entry.get("username")
        else
        "💰 RAFFLE PAYMENT PENDING\n\n"
        f"🎁 Prize: {raffle_data['prize']}\n"
        f"💵 Entry Price: {money_text(raffle_data['price'])}\n"
        f"🆔 Entry: #{entry['id']}\n"
        f"👤 Name: {entry.get('display_name') or 'Unknown'}"
    )

    text += (
        f"\n💳 Payment: {entry.get('payment_method') or 'Unknown'}"
        "\n\n"
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
                "Unable to notify admin %s about entry %s: %s",
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
    if not update.effective_user:
        return

    if not is_admin_user(
        update.effective_user.id
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
        "💰 PENDING RAFFLE ENTRIES\n"
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

    changed = db.approve_entry(
        entry_id,
        query.from_user.id,
    )

    if not changed:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ This entry is no longer pending.\n\n"
                f"Current status: {entry.get('status')}"
            ),
        )
        return

    await send_message_safe(
        update,
        context,
        f"✅ Entry #{entry_id} approved.",
    )

    # Notify entrant privately.
    try:
        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "🎉 YOUR MELANATED AZ RAFFLE ENTRY IS APPROVED!\n\n"
                f"🎟️ Entry #{entry_id}\n\n"
                "Your payment has been verified by "
                "Melanated AZ and your entry is now active."
            ),
        )
    except Exception as exc:
        logger.error(
            "Could not notify entrant %s: %s",
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

    changed = db.deny_entry(
        entry_id,
        query.from_user.id,
    )

    if not changed:
        await send_message_safe(
            update,
            context,
            (
                "⚠️ This entry is no longer pending.\n\n"
                f"Current status: {entry.get('status')}"
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
                "❌ YOUR RAFFLE ENTRY WAS NOT APPROVED\n\n"
                f"Entry #{entry_id}\n\n"
                "Your payment could not be verified by "
                "Melanated AZ."
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
    """
    Admin Raffle Entries screen.

    IMPORTANT:
    This is callback-safe.

    The old code used:

        update.message.reply_text()

    which fails when admin.py invokes this function from
    an inline keyboard because callback updates have:

        update.message == None
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

    await answer_callback(
        update,
        "Loading raffle entries...",
    )

    # Get active raffle first.
    raffle_data = db.get_active_raffle()

    # If there is no active raffle, show history instead
    # rather than claiming the database is empty.
    if not raffle_data:
        await send_message_safe(
            update,
            context,
            (
                "🎟️ RAFFLE ENTRIES\n\n"
                "There is currently no active raffle.\n\n"
                "Use the raffle history option to view "
                "previous raffles and their entries."
            ),
        )
        return

    entries = db.get_approved_entries(
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
        f"✅ Approved Entries: {len(entries)}",
        f"⏳ Pending Entries: {len(pending_for_raffle)}",
        "",
    ]

    if entries:
        lines.append("APPROVED:")

        for number, entry in enumerate(
            entries,
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


# ==========================================================
# HISTORY / RECOVERY
# ==========================================================

async def raffle_history(
    update,
    context,
):
    """
    Show ALL raffles from the existing database.

    This is intentionally not limited to active raffles.
    It allows recovery/viewing of old raffle records.
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
                "No raffle records were found in "
                "the current database file."
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
                (raffle_data["id"],),
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

    # Telegram message limit protection.
    text = "\n".join(lines)

    if len(text) <= 4000:
        await send_message_safe(
            update,
            context,
            text,
        )
        return

    chunks = []

    current = ""

    for line in lines:
        if len(current) + len(line) > 3500:
            chunks.append(current)
            current = ""

        current += line + "\n"

    if current:
        chunks.append(current)

    for chunk in chunks:
        await send_message_safe(
            update,
            context,
            chunk,
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
        f"💵 Entry: {money_text(raffle_data['price'])}",
        f"📌 Status: {raffle_data['status']}",
        f"⏳ {format_countdown(raffle_data['expires_at'])}",
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
            f"{number}. {name} — #{entry['id']}"
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
# UPDATE COUNTDOWN
# ==========================================================

async def update_raffle_countdown(
    context,
):
    """
    Background countdown updater.

    It updates the existing raffle message without creating
    duplicate raffle posts.
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
            pass

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
        # Telegram may return an error when the message did not
        # actually change. This should not kill the scheduler.
        logger.debug(
            "Countdown update skipped: %s",
            exc,
        )


# ==========================================================
# CLOSE RAFFLE
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
            raffle_data = db.get_raffle(
                raffle_id
            )
        except Exception:
            raffle_data = None
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
        or f"User {winner.get('user_id')}"
    )

    await send_message_safe(
        update,
        context,
        (
            "🎉🎉🎉 WINNER DRAWN! 🎉🎉🎉\n\n"
            f"🎟️ Raffle #{raffle_data['id']}\n"
            f"🎁 Prize: {raffle_data['prize']}\n\n"
            f"🏆 WINNER:\n"
            f"{name}\n\n"
            f"🆔 Entry #{winner['id']}"
        ),
    )

    # Close the raffle after the draw.
    try:
        db.close_raffle(
            raffle_data["id"]
        )
    except Exception:
        pass


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
        except Exception:
            await send_message_safe(
                update,
                context,
                "❌ Invalid raffle ID.",
            )
            return
    else:
        # Most recent raffle.
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
    """
    Give an approved participant an additional database entry.

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

    # Bonus entry is intentionally inserted directly as approved.
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
        raise

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
# ALL ENTRIES / DATABASE RECOVERY VIEW
# ==========================================================

async def all_raffle_entries(
    update,
    context,
):
    """
    Display entries across ALL historical raffles.

    This does not modify anything.
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

    # Telegram limit.
    if len(text) <= 4000:
        await send_message_safe(
            update,
            context,
            text,
        )
        return

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
# ADMIN CALLBACK ROUTER
# ==========================================================

async def raffle_callback_router(
    update,
    context,
):
    """
    Optional central callback router.

    Safe to register if admin.py/bot.py needs one callback
    handler for raffle-related buttons.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data == "raffle_enter":
        return await enter_raffle(
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


# ==========================================================
# COMPATIBILITY ALIASES
# ==========================================================

# Older versions of admin.py may use these names.

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

# Common command aliases.
raffleentries = raffle_entries
raffle_entries_command = raffle_entries

pendingraffleentries = pending_entries

approveraﬄeentry = approve_raffle_entry
denyraffleentry = deny_raffle_entry


# ==========================================================
# EXPORT LIST
# ==========================================================

__all__ = [
    # Main raffle
    "raffle",
    "raffle_command",
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

    # Admin entry management
    "pending_entries",
    "pending",
    "raffle_entries",
    "raffleentries",
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
]
