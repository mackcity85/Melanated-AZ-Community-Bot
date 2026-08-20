# raffle.py
# Melanated AZ Bot - Raffle System
# Compatible with the existing bot.py imports

import os
import re
import random
import sqlite3
import logging
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_FILE = os.getenv("RAFFLE_DB", "raffle.db")

# Accept:
#   5
#   5.00
#   $5
#   $5.00
# from Render environment variables.
_raw_cost = os.getenv("RAFFLE_ENTRY_COST", "5")

try:
    RAFFLE_ENTRY_COST = float(
        str(_raw_cost).replace("$", "").replace(",", "").strip()
    )
except (ValueError, TypeError):
    RAFFLE_ENTRY_COST = 5.00

if RAFFLE_ENTRY_COST <= 0:
    RAFFLE_ENTRY_COST = 5.00


CASHAPP = os.getenv("CASHAPP", os.getenv("CASH_APP", ""))
ZELLE = os.getenv("ZELLE", "")

# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raffles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            prize TEXT,
            entry_cost REAL NOT NULL DEFAULT 5.00,
            max_entries INTEGER,
            active INTEGER NOT NULL DEFAULT 1,
            winner_id INTEGER,
            winner_name TEXT,
            created_at TEXT NOT NULL,
            ended_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raffle_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raffle_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            payment_method TEXT,
            payment_reference TEXT,
            paid INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (raffle_id) REFERENCES raffles(id)
        )
    """)

    conn.commit()
    conn.close()


init_database()


# ============================================================
# HELPERS
# ============================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def money(value):
    return f"${float(value):.2f}"


def get_active_raffle():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM raffles
        WHERE active = 1
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()

    return row


def get_raffle(raffle_id=None):
    """
    Return a raffle by ID.

    If raffle_id is omitted, return the current active raffle.
    """

    conn = get_connection()
    cur = conn.cursor()

    if raffle_id is None:
        cur.execute("""
            SELECT *
            FROM raffles
            WHERE active = 1
            ORDER BY id DESC
            LIMIT 1
        """)
    else:
        cur.execute("""
            SELECT *
            FROM raffles
            WHERE id = ?
            LIMIT 1
        """, (raffle_id,))

    row = cur.fetchone()
    conn.close()

    return row


def get_entry_count(raffle_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM raffle_entries
        WHERE raffle_id = ?
        AND paid = 1
    """, (raffle_id,))

    count = cur.fetchone()[0]
    conn.close()

    return count


def user_has_entry(raffle_id, user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM raffle_entries
        WHERE raffle_id = ?
        AND user_id = ?
        LIMIT 1
    """, (raffle_id, user_id))

    row = cur.fetchone()
    conn.close()

    return row is not None


# ============================================================
# ADMIN - START RAFFLE
# ============================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Start a raffle.

    Supported command format:

    /raffle Prize Name

    Optional:

    /raffle Prize Name | Description

    Example:

    /raffle $100 Cash Prize | One winner
    """

    if not update.effective_user:
        return

    args = context.args or []

    if not args:
        await update.effective_message.reply_text(
            "❌ Please provide a raffle title.\n\n"
            "Example:\n"
            "/raffle $100 Cash Prize"
        )
        return

    title_text = " ".join(args).strip()

    if "|" in title_text:
        title, description = title_text.split("|", 1)
        title = title.strip()
        description = description.strip()
    else:
        title = title_text
        description = ""

    # End any existing raffle.
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE raffles
        SET active = 0,
            ended_at = ?
        WHERE active = 1
    """, (now_iso(),))

    cur.execute("""
        INSERT INTO raffles (
            title,
            description,
            prize,
            entry_cost,
            active,
            created_at
        )
        VALUES (?, ?, ?, ?, 1, ?)
    """, (
        title,
        description,
        title,
        RAFFLE_ENTRY_COST,
        now_iso()
    ))

    raffle_id = cur.lastrowid

    conn.commit()
    conn.close()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎟 Enter Raffle",
                callback_data=f"raffle_enter:{raffle_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Payment Info",
                callback_data=f"raffle_payment:{raffle_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Raffle Status",
                callback_data=f"raffle_status:{raffle_id}"
            )
        ]
    ])

    message = (
        "🎉 <b>NEW RAFFLE!</b>\n\n"
        f"🎁 <b>{title}</b>\n"
    )

    if description:
        message += f"📝 {description}\n"

    message += (
        f"\n🎟 Entry: <b>{money(RAFFLE_ENTRY_COST)}</b>\n"
        "\n"
        "Click <b>Enter Raffle</b> to participate."
    )

    await update.effective_message.reply_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# PAYMENT BUTTON
# ============================================================

def payment_button(raffle_id=None):
    """
    Return payment keyboard.

    Kept as a normal function so bot.py can import it.
    """

    suffix = str(raffle_id) if raffle_id else "0"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💵 Cash App",
                callback_data=f"raffle_cashapp:{suffix}"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Zelle",
                callback_data=f"raffle_zelle:{suffix}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=f"raffle_back:{suffix}"
            )
        ]
    ])


# ============================================================
# PAID ENTRY
# ============================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Process a paid raffle entry.

    This records the user's payment submission.
    Admins can verify payment separately.
    """

    query = update.callback_query

    if query:
        await query.answer()

    user = update.effective_user

    if not user:
        return

    raffle = get_active_raffle()

    if not raffle:
        message = "❌ There is no active raffle right now."

        if query:
            await query.edit_message_text(message)
        else:
            await update.effective_message.reply_text(message)

        return

    raffle_id = raffle["id"]

    if user_has_entry(raffle_id, user.id):
        message = (
            "⚠️ You already have an entry for this raffle.\n\n"
            f"🎟 Entry cost: {money(raffle['entry_cost'])}"
        )

        if query:
            await query.edit_message_text(message)
        else:
            await update.effective_message.reply_text(message)

        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO raffle_entries (
            raffle_id,
            user_id,
            username,
            first_name,
            payment_method,
            payment_reference,
            paid,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
    """, (
        raffle_id,
        user.id,
        user.username or "",
        user.first_name or "",
        "",
        "",
        now_iso()
    ))

    conn.commit()
    conn.close()

    message = (
        "🎟 <b>RAFFLE ENTRY STARTED</b>\n\n"
        f"🎁 {raffle['title']}\n"
        f"💰 Entry: <b>{money(raffle['entry_cost'])}</b>\n\n"
        "Choose a payment method below.\n"
        "After sending payment, provide the payment reference "
        "or transaction information to the raffle admin."
    )

    keyboard = payment_button(raffle_id)

    if query:
        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await update.effective_message.reply_text(
            message,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# ============================================================
# PAYMENT INFORMATION
# ============================================================

async def show_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    method: str
):
    query = update.callback_query

    if query:
        await query.answer()

    raffle = get_active_raffle()

    cost = RAFFLE_ENTRY_COST

    if raffle:
        cost = raffle["entry_cost"]

    if method.lower() == "cashapp":
        account = CASHAPP or "Not configured"

        text = (
            "💵 <b>Cash App Payment</b>\n\n"
            f"Amount: <b>{money(cost)}</b>\n"
            f"Cash App: <b>{account}</b>\n\n"
            "After sending payment, save your transaction "
            "information and send it to the raffle admin."
        )

    else:
        account = ZELLE or "Not configured"

        text = (
            "💳 <b>Zelle Payment</b>\n\n"
            f"Amount: <b>{money(cost)}</b>\n"
            f"Zelle: <b>{account}</b>\n\n"
            "After sending payment, save your transaction "
            "information and send it to the raffle admin."
        )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=(
                    f"raffle_payment:"
                    f"{raffle['id'] if raffle else 0}"
                )
            )
        ]
    ])

    if query:
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# ============================================================
# STATUS
# ============================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query:
        await query.answer()

    raffle = get_active_raffle()

    if not raffle:
        text = "❌ There is no active raffle."

        if query:
            await query.edit_message_text(text)
        else:
            await update.effective_message.reply_text(text)

        return

    count = get_entry_count(raffle["id"])

    text = (
        "📊 <b>RAFFLE STATUS</b>\n\n"
        f"🎁 {raffle['title']}\n"
        f"🎟 Entry: {money(raffle['entry_cost'])}\n"
        f"👥 Paid Entries: <b>{count}</b>\n"
    )

    if raffle["max_entries"]:
        text += f"🔢 Maximum Entries: {raffle['max_entries']}\n"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎟 Enter",
                callback_data=f"raffle_enter:{raffle['id']}"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Payment",
                callback_data=f"raffle_payment:{raffle['id']}"
            )
        ]
    ])

    if query:
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# ============================================================
# DRAW WINNER
# ============================================================

async def draw_winner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not user:
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ No active raffle."
        )
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM raffle_entries
        WHERE raffle_id = ?
        AND paid = 1
    """, (raffle["id"],))

    entries = cur.fetchall()

    if not entries:
        conn.close()

        await update.effective_message.reply_text(
            "❌ There are no verified paid entries."
        )
        return

    winner = random.choice(entries)

    cur.execute("""
        UPDATE raffles
        SET active = 0,
            winner_id = ?,
            winner_name = ?,
            ended_at = ?
        WHERE id = ?
    """, (
        winner["user_id"],
        winner["first_name"] or winner["username"],
        now_iso(),
        raffle["id"]
    ))

    conn.commit()
    conn.close()

    winner_name = winner["first_name"] or winner["username"] or str(
        winner["user_id"]
    )

    await update.effective_message.reply_text(
        "🎉 <b>RAFFLE WINNER!</b>\n\n"
        f"🎁 {raffle['title']}\n\n"
        f"👑 Winner: <b>{winner_name}</b>\n\n"
        "Congratulations! 🎊",
        parse_mode="HTML"
    )


# ============================================================
# EXPORTS / COMPATIBILITY
# ============================================================

__all__ = [
    "RAFFLE_ENTRY_COST",
    "start_raffle",
    "get_raffle",
    "paid_entry",
    "payment_button",
    "show_payment",
    "raffle_status",
    "draw_winner",
    "init_database",
]
