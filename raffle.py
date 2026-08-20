# raffle.py
# Melanated AZ Bot - Raffle System

import os
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

_raw_cost = os.getenv("RAFFLE_ENTRY_COST", "5")

try:
    RAFFLE_ENTRY_COST = float(
        str(_raw_cost)
        .replace("$", "")
        .replace(",", "")
        .strip()
    )
except (ValueError, TypeError):
    RAFFLE_ENTRY_COST = 5.00

if RAFFLE_ENTRY_COST <= 0:
    RAFFLE_ENTRY_COST = 5.00

CASHAPP = os.getenv(
    "CASHAPP",
    os.getenv("CASH_APP", "")
)

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
            FOREIGN KEY (raffle_id)
                REFERENCES raffles(id)
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
# START RAFFLE
# ============================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

        title, description = title_text.split(
            "|",
            1
        )

        title = title.strip()
        description = description.strip()

    else:

        title = title_text
        description = ""

    conn = get_connection()
    cur = conn.cursor()

    # Close previous raffle.

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
        f"\n🎟 Entry: <b>{money(RAFFLE_ENTRY_COST)}</b>\n\n"
        "Click <b>Enter Raffle</b> to participate."
    )

    await update.effective_message.reply_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# ENTER RAFFLE
# ============================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:
        await query.answer()

    user = update.effective_user

    if not user:
        return

    raffle = get_active_raffle()

    if not raffle:

        text = (
            "❌ There is currently no active raffle."
        )

        if query:
            await query.edit_message_text(text)
        else:
            await update.effective_message.reply_text(text)

        return

    raffle_id = raffle["id"]

    # Prevent duplicate entries.

    if user_has_entry(
        raffle_id,
        user.id
    ):

        text = (
            "⚠️ <b>You already entered this raffle.</b>\n\n"
            f"🎁 {raffle['title']}\n"
            f"🎟 Entry: {money(raffle['entry_cost'])}\n\n"
            "Your payment must be verified by an admin."
        )

        if query:
            await query.edit_message_text(
                text,
                parse_mode="HTML"
            )
        else:
            await update.effective_message.reply_text(
                text,
                parse_mode="HTML"
            )

        return

    # Create pending entry.

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
        VALUES (?, ?, ?, ?, '', '', 0, ?)
    """, (
        raffle_id,
        user.id,
        user.username or "",
        user.first_name or "",
        now_iso()
    ))

    conn.commit()
    conn.close()

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "💵 Cash App",
                callback_data=f"raffle_cashapp:{raffle_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Zelle",
                callback_data=f"raffle_zelle:{raffle_id}"
            )
        ]

    ])

    text = (
        "🎟 <b>RAFFLE ENTRY</b>\n\n"
        f"🎁 {raffle['title']}\n"
        f"💰 Entry Cost: <b>{money(raffle['entry_cost'])}</b>\n\n"
        "Choose your payment method below.\n\n"
        "After payment, your entry will remain "
        "<b>pending</b> until an admin verifies it."
    )

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
# PAYMENT BUTTON
# ============================================================

def payment_button(raffle_id=None):

    raffle_id = raffle_id or 0

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "💵 Cash App",
                callback_data=f"raffle_cashapp:{raffle_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Zelle",
                callback_data=f"raffle_zelle:{raffle_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=f"raffle_back:{raffle_id}"
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

    query = update.callback_query

    if query:
        await query.answer()

    user = update.effective_user

    if not user:
        return

    raffle = get_active_raffle()

    if not raffle:

        text = "❌ There is no active raffle."

        if query:
            await query.edit_message_text(text)
        else:
            await update.effective_message.reply_text(text)

        return

    raffle_id = raffle["id"]

    if not user_has_entry(
        raffle_id,
        user.id
    ):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO raffle_entries (
                raffle_id,
                user_id,
                username,
                first_name,
                paid,
                created_at
            )
            VALUES (?, ?, ?, ?, 0, ?)
        """, (
            raffle_id,
            user.id,
            user.username or "",
            user.first_name or "",
            now_iso()
        ))

        conn.commit()
        conn.close()

    text = (
        "💰 <b>PAYMENT REQUIRED</b>\n\n"
        f"🎁 {raffle['title']}\n"
        f"💵 Amount: <b>{money(raffle['entry_cost'])}</b>\n\n"
        "Choose your payment method:"
    )

    keyboard = payment_button(
        raffle_id
    )

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

    method = method.lower()

    if method == "cashapp":

        account = CASHAPP or "Not configured"

        text = (
            "💵 <b>CASH APP</b>\n\n"
            f"Amount: <b>{money(cost)}</b>\n"
            f"Cash App: <b>{account}</b>\n\n"
            "Send the payment and keep your "
            "transaction information."
        )

    else:

        account = ZELLE or "Not configured"

        text = (
            "💳 <b>ZELLE</b>\n\n"
            f"Amount: <b>{money(cost)}</b>\n"
            f"Zelle: <b>{account}</b>\n\n"
            "Send the payment and keep your "
            "transaction information."
        )

    if raffle:

        raffle_id = raffle["id"]

    else:

        raffle_id = 0

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=f"raffle_payment:{raffle_id}"
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
# RAFFLE STATUS
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

    count = get_entry_count(
        raffle["id"]
    )

    text = (
        "📊 <b>RAFFLE STATUS</b>\n\n"
        f"🎁 {raffle['title']}\n"
        f"🎟 Entry: {money(raffle['entry_cost'])}\n"
        f"👥 Verified Entries: <b>{count}</b>\n"
    )

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

    winner_name = (
        winner["first_name"]
        or winner["username"]
        or str(winner["user_id"])
    )

    cur.execute("""
        UPDATE raffles
        SET active = 0,
            winner_id = ?,
            winner_name = ?,
            ended_at = ?
        WHERE id = ?
    """, (
        winner["user_id"],
        winner_name,
        now_iso(),
        raffle["id"]
    ))

    conn.commit()
    conn.close()

    await update.effective_message.reply_text(
        "🎉 <b>RAFFLE WINNER!</b>\n\n"
        f"🎁 {raffle['title']}\n\n"
        f"👑 Winner: <b>{winner_name}</b>\n\n"
        "Congratulations! 🎊",
        parse_mode="HTML"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "RAFFLE_ENTRY_COST",
    "start_raffle",
    "enter_raffle",
    "get_raffle",
    "paid_entry",
    "payment_button",
    "show_payment",
    "raffle_status",
    "draw_winner",
    "init_database",
]
