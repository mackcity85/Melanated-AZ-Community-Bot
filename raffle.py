
"""
raffle.py
Melanated AZ Bot Raffle System

This file is designed to work with the existing bot.py.
SQLite is self-contained and does not depend on DB_NAME
or RAFFLE_ENTRY_COST being present in config.py.
"""

import os
import re
import random
import sqlite3
from datetime import datetime
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# ============================================================
# CONFIGURATION
# ============================================================

DB_NAME = os.getenv("RAFFLE_DB_NAME", "raffle_database.db")


def get_entry_cost() -> float:
    """
    Accepts values such as:
        5
        5.00
        $5
        $5.00
    """

    value = os.getenv("RAFFLE_ENTRY_COST", "5")

    try:
        cleaned = re.sub(r"[^0-9.]", "", str(value))

        if not cleaned:
            return 5.00

        return float(cleaned)

    except (ValueError, TypeError):
        return 5.00


RAFFLE_ENTRY_COST = get_entry_cost()

CASHAPP_USERNAME = os.getenv("CASHAPP_USERNAME", "").strip()
ZELLE_EMAIL = os.getenv("ZELLE_EMAIL", "").strip()


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_raffle_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raffles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            prize TEXT NOT NULL,
            entry_cost REAL NOT NULL,
            max_entries INTEGER DEFAULT 0,
            winner_count INTEGER DEFAULT 1,
            status TEXT DEFAULT 'open',
            created_by INTEGER,
            created_at TEXT NOT NULL,
            closed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raffle_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raffle_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            payment_method TEXT,
            payment_reference TEXT,
            paid INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(raffle_id, user_id)
        )
    """)

    conn.commit()
    conn.close()


init_raffle_database()


# ============================================================
# RAFFLE LOOKUP
# ============================================================

def get_raffle(raffle_id: Optional[int] = None):
    """
    Return a specific raffle.

    If no raffle_id is supplied, return the newest open raffle.
    """

    conn = get_connection()
    cursor = conn.cursor()

    if raffle_id is not None:
        cursor.execute(
            """
            SELECT *
            FROM raffles
            WHERE id = ?
            LIMIT 1
            """,
            (raffle_id,),
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM raffles
            WHERE status = 'open'
            ORDER BY id DESC
            LIMIT 1
            """
        )

    raffle = cursor.fetchone()

    conn.close()

    return raffle


def get_open_raffle():
    return get_raffle()


# ============================================================
# ENTRY HELPERS
# ============================================================

def get_entry_count(
    raffle_id: int,
    paid_only: bool = False
) -> int:

    conn = get_connection()
    cursor = conn.cursor()

    if paid_only:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raffle_entries
            WHERE raffle_id = ?
              AND paid = 1
            """,
            (raffle_id,),
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raffle_entries
            WHERE raffle_id = ?
            """,
            (raffle_id,),
        )

    result = cursor.fetchone()
    conn.close()

    return int(result[0]) if result else 0


def user_has_entry(
    raffle_id: int,
    user_id: int
) -> bool:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM raffle_entries
        WHERE raffle_id = ?
          AND user_id = ?
        LIMIT 1
        """,
        (raffle_id, user_id),
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def pending_entries(raffle_id=None):
    """
    Return all unpaid/pending entries.

    This is intentionally a normal synchronous function because
    bot.py may call it directly.
    """

    if raffle_id is None:
        raffle = get_open_raffle()

        if not raffle:
            return []

        raffle_id = raffle["id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            raffle_id,
            user_id,
            username,
            first_name,
            payment_method,
            payment_reference,
            paid,
            created_at
        FROM raffle_entries
        WHERE raffle_id = ?
          AND paid = 0
        ORDER BY created_at ASC
        """,
        (raffle_id,),
    )

    entries = cursor.fetchall()

    conn.close()

    return entries


# ============================================================
# START RAFFLE
# ============================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if user is None or update.effective_message is None:
        return

    args = context.args or []

    if args:
        title = " ".join(args)
    else:
        title = "Melanated AZ Raffle"

    prize = title

    conn = get_connection()
    cursor = conn.cursor()

    # Close any previous active raffle.
    cursor.execute(
        """
        UPDATE raffles
        SET status = 'closed',
            closed_at = ?
        WHERE status = 'open'
        """,
        (datetime.utcnow().isoformat(),),
    )

    cursor.execute(
        """
        INSERT INTO raffles (
            title,
            description,
            prize,
            entry_cost,
            max_entries,
            winner_count,
            status,
            created_by,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            "",
            prize,
            RAFFLE_ENTRY_COST,
            0,
            1,
            "open",
            user.id,
            datetime.utcnow().isoformat(),
        ),
    )

    raffle_id = cursor.lastrowid

    conn.commit()
    conn.close()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎟 Enter Raffle",
                callback_data=f"raffle_enter:{raffle_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Payment Info",
                callback_data=f"raffle_payment:{raffle_id}",
            )
        ],
    ])

    text = (
        f"🎉 <b>{title}</b>\n\n"
        f"🎁 Prize: <b>{prize}</b>\n"
        f"💵 Entry: <b>${RAFFLE_ENTRY_COST:.2f}</b>\n\n"
        "Tap below to enter."
    )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    return raffle_id


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

        data = query.data or ""

        try:
            raffle_id = int(data.split(":")[1])
        except (IndexError, ValueError):
            await query.answer(
                "Invalid raffle.",
                show_alert=True,
            )
            return

        user = query.from_user

    else:
        user = update.effective_user
        raffle = get_open_raffle()

        if not raffle:
            await update.effective_message.reply_text(
                "❌ There is no active raffle."
            )
            return

        raffle_id = raffle["id"]

    raffle = get_raffle(raffle_id)

    if not raffle:
        if query:
            await query.answer(
                "Raffle not found.",
                show_alert=True,
            )
        return

    if raffle["status"] != "open":
        if query:
            await query.answer(
                "This raffle is closed.",
                show_alert=True,
            )
        return

    if user_has_entry(raffle_id, user.id):
        if query:
            await query.answer(
                "You already entered this raffle.",
                show_alert=True,
            )
        return

    max_entries = int(raffle["max_entries"] or 0)

    if max_entries > 0:
        current_count = get_entry_count(raffle_id)

        if current_count >= max_entries:
            if query:
                await query.answer(
                    "This raffle is full.",
                    show_alert=True,
                )
            return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO raffle_entries (
            raffle_id,
            user_id,
            username,
            first_name,
            payment_method,
            payment_reference,
            paid,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            raffle_id,
            user.id,
            user.username,
            user.first_name,
            None,
            None,
            0,
            datetime.utcnow().isoformat(),
        ),
    )

    conn.commit()
    conn.close()

    text = (
        f"🎟 <b>Entry Created</b>\n\n"
        f"Raffle: <b>{raffle['title']}</b>\n"
        f"Entry Cost: <b>${raffle['entry_cost']:.2f}</b>\n\n"
        "Your entry is pending payment.\n"
        "Choose a payment method below."
    )

    if query:
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=payment_button(raffle_id),
        )
    else:
        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=payment_button(raffle_id),
        )


# ============================================================
# PAYMENT BUTTON
# ============================================================

def payment_button(raffle_id=None):

    if raffle_id is None:
        raffle = get_open_raffle()
        raffle_id = raffle["id"] if raffle else 0

    buttons = []

    if CASHAPP_USERNAME:
        cashapp = CASHAPP_USERNAME.lstrip("$")

        buttons.append([
            InlineKeyboardButton(
                "💚 Cash App",
                url=f"https://cash.app/${cashapp}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "💙 Zelle",
            callback_data=f"raffle_zelle:{raffle_id}",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "✅ I Paid",
            callback_data=f"raffle_paid_request:{raffle_id}",
        )
    ])

    return InlineKeyboardMarkup(buttons)


# ============================================================
# ADMIN PAYMENT BUTTON
# ============================================================

def admin_payment_button(
    raffle_id,
    user_id
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Confirm Payment",
                callback_data=(
                    f"raffle_paid:{raffle_id}:{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Reject Payment",
                callback_data=(
                    f"raffle_reject:{raffle_id}:{user_id}"
                ),
            )
        ],
    ])


# ============================================================
# PAID ENTRY
# ============================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""

    try:
        parts = data.split(":")

        raffle_id = int(parts[1])
        user_id = int(parts[2])

    except (IndexError, ValueError):
        await query.answer(
            "Invalid payment.",
            show_alert=True,
        )
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE raffle_entries
        SET paid = 1,
            payment_reference = 'ADMIN_CONFIRMED'
        WHERE raffle_id = ?
          AND user_id = ?
        """,
        (
            raffle_id,
            user_id,
        ),
    )

    changed = cursor.rowcount

    conn.commit()
    conn.close()

    if changed:
        await query.edit_message_text(
            "✅ Payment confirmed.\n\n"
            "The raffle entry is now active."
        )
    else:
        await query.edit_message_text(
            "❌ Raffle entry was not found."
        )


# ============================================================
# PAYMENT INFORMATION
# ============================================================

async def show_payment_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""

    try:
        raffle_id = int(data.split(":")[1])
    except (IndexError, ValueError):
        raffle_id = None

    raffle = get_raffle(raffle_id)

    if not raffle:
        await query.edit_message_text(
            "❌ No active raffle."
        )
        return

    text = (
        "💳 <b>Raffle Payment Information</b>\n\n"
        f"💵 Entry Cost: "
        f"<b>${raffle['entry_cost']:.2f}</b>\n\n"
    )

    if CASHAPP_USERNAME:
        text += (
            "💚 <b>Cash App:</b> "
            f"${CASHAPP_USERNAME.lstrip('$')}\n"
        )

    if ZELLE_EMAIL:
        text += (
            "💙 <b>Zelle:</b> "
            f"{ZELLE_EMAIL}\n"
        )

    text += (
        "\nAfter sending payment, press "
        "<b>I Paid</b>."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=payment_button(raffle["id"]),
    )


# ============================================================
# USER PAYMENT CONFIRMATION REQUEST
# ============================================================

async def payment_confirmation_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer(
        "Payment submitted for review.",
        show_alert=True,
    )

    user = query.from_user
    data = query.data or ""

    try:
        raffle_id = int(data.split(":")[1])
    except (IndexError, ValueError):
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE raffle_entries
        SET payment_reference = 'PAYMENT_REVIEW_REQUESTED'
        WHERE raffle_id = ?
          AND user_id = ?
        """,
        (
            raffle_id,
            user.id,
        ),
    )

    conn.commit()
    conn.close()

    await query.edit_message_text(
        "⏳ <b>Payment Submitted</b>\n\n"
        "Your payment is now waiting for admin "
        "verification.\n\n"
        "You will be entered once payment is confirmed.",
        parse_mode="HTML",
    )


# ============================================================
# ZELLE
# ============================================================

async def show_zelle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if ZELLE_EMAIL:
        text = (
            "💙 <b>Zelle Payment</b>\n\n"
            f"Send <b>${RAFFLE_ENTRY_COST:.2f}</b> to:\n\n"
            f"<code>{ZELLE_EMAIL}</code>\n\n"
            "After sending payment, return and "
            "press <b>I Paid</b>."
        )
    else:
        text = (
            "💙 <b>Zelle Payment</b>\n\n"
            "Zelle has not been configured yet."
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# REJECT PAYMENT
# ============================================================

async def reject_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""

    try:
        parts = data.split(":")

        raffle_id = int(parts[1])
        user_id = int(parts[2])

    except (IndexError, ValueError):
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE raffle_entries
        SET paid = 0,
            payment_reference = 'PAYMENT_REJECTED'
        WHERE raffle_id = ?
          AND user_id = ?
        """,
        (
            raffle_id,
            user_id,
        ),
    )

    conn.commit()
    conn.close()

    await query.edit_message_text(
        "❌ Payment rejected."
    )


# ============================================================
# DRAW WINNER
# ============================================================

async def draw_winner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_message is None:
        return

    raffle = get_open_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ There is no active raffle."
        )
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM raffle_entries
        WHERE raffle_id = ?
          AND paid = 1
        """,
        (raffle["id"],),
    )

    entries = cursor.fetchall()

    if not entries:
        conn.close()

        await update.effective_message.reply_text(
            "❌ There are no paid entries."
        )
        return

    winner_count = int(raffle["winner_count"] or 1)

    winner_count = min(
        winner_count,
        len(entries),
    )

    winners = random.sample(
        entries,
        winner_count,
    )

    cursor.execute(
        """
        UPDATE raffles
        SET status = 'closed',
            closed_at = ?
        WHERE id = ?
        """,
        (
            datetime.utcnow().isoformat(),
            raffle["id"],
        ),
    )

    conn.commit()
    conn.close()

    names = []

    for winner in winners:

        if winner["username"]:
            name = f"@{winner['username']}"
        elif winner["first_name"]:
            name = winner["first_name"]
        else:
            name = str(winner["user_id"])

        names.append(f"🏆 {name}")

    winners_text = "\n".join(names)

    await update.effective_message.reply_text(
        "🎉 <b>RAFFLE WINNER!</b>\n\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n\n"
        f"{winners_text}",
        parse_mode="HTML",
    )


# ============================================================
# ALIASES
# ============================================================

# These aliases make the module more tolerant of older bot.py
# versions.

create_raffle = start_raffle
join_raffle = enter_raffle
confirm_payment = paid_entry


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "RAFFLE_ENTRY_COST",
    "DB_NAME",
    "CASHAPP_USERNAME",
    "ZELLE_EMAIL",

    "init_raffle_database",

    "get_connection",
    "get_raffle",
    "get_open_raffle",
    "get_entry_count",
    "user_has_entry",
    "pending_entries",

    "start_raffle",
    "create_raffle",

    "enter_raffle",
    "join_raffle",

    "payment_button",
    "admin_payment_button",

    "paid_entry",
    "confirm_payment",

    "show_payment_info",
    "payment_confirmation_request",
    "show_zelle",
    "reject_payment",

    "draw_winner",
]
