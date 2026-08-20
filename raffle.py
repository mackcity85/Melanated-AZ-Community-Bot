# ==========================================================
# Melanated AZ Bot
# raffle.py
# ==========================================================

import logging
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# ==========================================================
# STATE
# ==========================================================

current_raffle = {
    "active": False,
    "name": None,
    "prize": None,
    "entries": [],
    "winner": None,
}

pending = {}
last_winner = None


# ==========================================================
# HELPERS
# ==========================================================

def is_admin(user_id):
    try:
        from config import ADMIN_IDS
        return user_id in ADMIN_IDS
    except Exception:
        return False


def get_user_name(user):
    if getattr(user, "username", None):
        return f"@{user.username}"

    return getattr(user, "full_name", "Unknown User")


def raffle_is_active():
    return current_raffle.get("active", False)


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(update, context):

    if update.effective_user is None:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ You are not authorized to start a raffle."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/startraffle Prize Name"
        )
        return

    prize = " ".join(context.args)

    current_raffle["active"] = True
    current_raffle["name"] = "Melanated AZ Raffle"
    current_raffle["prize"] = prize
    current_raffle["entries"] = []
    current_raffle["winner"] = None

    pending.clear()

    await update.message.reply_text(
        f"🎟️ *RAFFLE STARTED!*\n\n"
        f"🏆 Prize: *{prize}*\n\n"
        f"Use /enter to enter.\n"
        f"Use /paid to submit payment information.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ==========================================================
# FREE / NORMAL ENTRY
# ==========================================================

async def enter_raffle(update, context):

    if not raffle_is_active():
        await update.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    user = update.effective_user

    if user is None:
        return

    user_id = user.id

    for entry in current_raffle["entries"]:
        if entry["user_id"] == user_id:
            await update.message.reply_text(
                "⚠️ You are already entered."
            )
            return

    entry = {
        "user_id": user_id,
        "name": get_user_name(user),
        "paid": False,
        "bonus": 0,
    }

    current_raffle["entries"].append(entry)

    await update.message.reply_text(
        "🎟️ You have been entered into the raffle!"
    )


# ==========================================================
# PAID ENTRY
# ==========================================================

async def paid_entry(update, context):

    if not raffle_is_active():
        await update.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    user = update.effective_user

    if user is None:
        return

    pending[user.id] = {
        "user_id": user.id,
        "name": get_user_name(user),
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "💵 Cash App",
                url=_cashapp_url(),
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Zelle",
                callback_data="raffle_zelle",
            )
        ],
    ]

    await update.message.reply_text(
        "💳 *PAID RAFFLE ENTRY*\n\n"
        "Choose your payment method below.\n\n"
        "After payment, an admin will verify your entry.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


def _cashapp_url():

    try:
        from config import CASHAPP_URL

        if CASHAPP_URL:
            return CASHAPP_URL
    except Exception:
        pass

    return "https://cash.app/"


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(update, context):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    user = query.from_user

    if query.data == "raffle_zelle":

        try:
            from config import ZELLE_PHONE
            zelle = ZELLE_PHONE
        except Exception:
            zelle = "Contact an admin for Zelle information."

        await query.message.reply_text(
            "💳 *ZELLE PAYMENT*\n\n"
            f"Send payment to:\n`{zelle}`\n\n"
            "After sending payment, an admin will verify your entry.",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif query.data == "raffle_paid":

        await query.message.reply_text(
            "💳 Payment instructions have been sent."
        )


# ==========================================================
# ADMIN PAYMENT BUTTON
# ==========================================================

async def admin_payment_button(update, context):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.message.reply_text(
            "❌ Admin access required."
        )
        return

    data = query.data

    if data.startswith("approve_"):

        target_id = int(data.split("_", 1)[1])

        result = _approve(target_id)

        await query.message.reply_text(result)

    elif data.startswith("deny_"):

        target_id = int(data.split("_", 1)[1])

        result = _deny(target_id)

        await query.message.reply_text(result)


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    if not pending:
        await update.message.reply_text(
            "✅ There are no pending entries."
        )
        return

    lines = ["⏳ *PENDING ENTRIES*\n"]

    for user_id, entry in pending.items():

        lines.append(
            f"👤 {entry['name']}\n"
            f"ID: `{user_id}`\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def _approve(user_id):

    entry = pending.pop(user_id, None)

    if entry is None:
        return "❌ Pending entry not found."

    for existing in current_raffle["entries"]:

        if existing["user_id"] == user_id:
            existing["paid"] = True
            return "✅ Entry approved."

    current_raffle["entries"].append(
        {
            "user_id": user_id,
            "name": entry["name"],
            "paid": True,
            "bonus": 0,
        }
    )

    return "✅ Paid raffle entry approved."


async def approve_raffle_entry(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/approveentry USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID."
        )
        return

    await update.message.reply_text(
        _approve(user_id)
    )


# ==========================================================
# DENY ENTRY
# ==========================================================

def _deny(user_id):

    if user_id not in pending:
        return "❌ Pending entry not found."

    pending.pop(user_id)

    return "❌ Entry denied."


async def deny_raffle_entry(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/denyentry USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID."
        )
        return

    await update.message.reply_text(
        _deny(user_id)
    )


# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(update, context):

    if not raffle_is_active():

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    count = len(current_raffle["entries"])

    await update.message.reply_text(
        f"🎟️ *RAFFLE STATUS*\n\n"
        f"🏆 Prize: {current_raffle['prize']}\n"
        f"👥 Entries: {count}\n"
        f"🟢 Status: ACTIVE",
        parse_mode=ParseMode.MARKDOWN,
    )


# ==========================================================
# LIST ENTRIES
# ==========================================================

async def raffle_entries(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    entries = current_raffle["entries"]

    if not entries:
        await update.message.reply_text(
            "There are no entries."
        )
        return

    lines = ["🎟️ *RAFFLE ENTRIES*\n"]

    for number, entry in enumerate(entries, 1):

        bonus = entry.get("bonus", 0)

        lines.append(
            f"{number}. {entry['name']} "
            f"(ID: `{entry['user_id']}`) "
            f"+{bonus} bonus"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )


# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(update, context):

    global last_winner

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    if not raffle_is_active():
        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    entries = current_raffle["entries"]

    if not entries:
        await update.message.reply_text(
            "❌ There are no entries."
        )
        return

    weighted = []

    for entry in entries:

        weight = 1 + int(entry.get("bonus", 0))

        weighted.extend(
            [entry] * weight
        )

    winner = random.choice(weighted)

    last_winner = winner
    current_raffle["winner"] = winner
    current_raffle["active"] = False

    await update.message.reply_text(
        f"🎉 *WE HAVE A WINNER!*\n\n"
        f"🏆 Prize: *{current_raffle['prize']}*\n"
        f"👑 Winner: *{winner['name']}*",
        parse_mode=ParseMode.MARKDOWN,
    )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(update, context):

    global last_winner

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    entries = current_raffle["entries"]

    if not entries:
        await update.message.reply_text(
            "❌ No entries available."
        )
        return

    available = [
        entry
        for entry in entries
        if not last_winner
        or entry["user_id"] != last_winner["user_id"]
    ]

    if not available:
        await update.message.reply_text(
            "❌ No other entrants are available for a reroll."
        )
        return

    winner = random.choice(available)

    last_winner = winner
    current_raffle["winner"] = winner

    await update.message.reply_text(
        f"🔄 *REROLL!*\n\n"
        f"👑 New Winner: *{winner['name']}*",
        parse_mode=ParseMode.MARKDOWN,
    )


# ==========================================================
# CANCEL
# ==========================================================

async def cancel_raffle(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    current_raffle["active"] = False
    current_raffle["winner"] = None
    current_raffle["entries"] = []

    pending.clear()

    await update.message.reply_text(
        "🛑 Raffle cancelled."
    )


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "Usage:\n/bonusentry USER_ID AMOUNT"
        )
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:

        await update.message.reply_text(
            "❌ Invalid values."
        )
        return

    for entry in current_raffle["entries"]:

        if entry["user_id"] == user_id:

            entry["bonus"] = (
                entry.get("bonus", 0) + amount
            )

            await update.message.reply_text(
                f"✅ Added {amount} bonus entries."
            )

            return

    await update.message.reply_text(
        "❌ User is not entered in the raffle."
    )


# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin access required."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n/removeentry USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:

        await update.message.reply_text(
            "❌ Invalid user ID."
        )
        return

    before = len(current_raffle["entries"])

    current_raffle["entries"] = [
        entry
        for entry in current_raffle["entries"]
        if entry["user_id"] != user_id
    ]

    after = len(current_raffle["entries"])

    if before == after:

        await update.message.reply_text(
            "❌ Entry not found."
        )
    else:

        await update.message.reply_text(
            "✅ Entry removed."
        )


# ==========================================================
# MODULE READY
# ==========================================================

logger.info("🎟️ Raffle module loaded successfully")
