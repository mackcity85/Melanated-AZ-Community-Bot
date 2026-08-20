"""
Melanated AZ Bot - Raffle System
Compatible with the existing bot.py interface.

Required exported functions:
    start_raffle
    get_raffle
    enter_raffle
    paid_entry
    payment_button
    admin_payment_button
"""

import os
import sqlite3
import random
import re
from datetime import datetime
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# ============================================================
# CONFIGURATION
# ============================================================

# Do NOT require these values from config.py.
# They can optionally be set in Render environment variables.

DB_NAME = os.getenv("RAFFLE_DB_NAME", "raffle_database.db")

def _get_entry_cost() -> float:
    """
    Accepts:
        5
        5.00
        $5
        $5.00
    """
    raw = os.getenv("RAFFLE_ENTRY_COST", "5")

    try:
        cleaned = re.sub(r"[^0-9.]", "", str(raw))
        return float(cleaned)
    except (TypeError, ValueError):
        return 5.00


RAFFLE_ENTRY_COST = _get_entry_cost()

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
            UNIQUE(raffle_id, user_id),
            FOREIGN KEY(raffle_id) REFERENCES raffles(id)
        )
    """)

    conn.commit()
    conn.close()


init_raffle_database()


# ============================================================
# HELPERS
# ============================================================

def get_raffle(raffle_id: Optional[int] = None):
    """
    Get a specific raffle or the most recent open raffle.
    """

    conn = get_connection()
    cursor = conn.cursor()

    if raffle_id is not None:
        cursor.execute(
            "SELECT * FROM raffles WHERE id = ?",
            (raffle_id,)
        )
    else:
        cursor.execute("""
            SELECT *
            FROM raffles
            WHERE status = 'open'
            ORDER BY id DESC
            LIMIT 1
        """)

    raffle = cursor.fetchone()
    conn.close()

    return raffle


def get_open_raffle():
    return get_raffle()


def get_entry_count(raffle_id: int, paid_only: bool = False) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    if paid_only:
        cursor.execute("""
            SELECT COUNT(*)
            FROM raffle_entries
            WHERE raffle_id = ?
              AND paid = 1
        """, (raffle_id,))
    else:
        cursor.execute("""
            SELECT COUNT(*)
            FROM raffle_entries
            WHERE raffle_id = ?
        """, (raffle_id,))

    count = cursor.fetchone()[0]
    conn.close()

    return count


def user_has_entry(raffle_id: int, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM raffle_entries
        WHERE raffle_id = ?
          AND user_id = ?
        LIMIT 1
    """, (raffle_id, user_id))

    result = cursor.fetchone()
    conn.close()

    return result is not None


# ============================================================
# START RAFFLE
# ============================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Starts a raffle.

    Expected command format:

        /raffle
        /raffle Prize Name

    Optional arguments:
        /raffle $100 Gift Card
    """

    if update.effective_user is None:
        return

    user = update.effective_user

    # Build title from command arguments.
    args = context.args or []

    if args:
        title = " ".join(args)
    else:
        title = "Melanated AZ Raffle"

    prize = title

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE raffles
        SET status = 'closed',
            closed_at = ?
        WHERE status = 'open'
    """, (
        datetime.utcnow().isoformat(),
    ))

    cursor.execute("""
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
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)
    """, (
        title,
        "",
        prize,
        RAFFLE_ENTRY_COST,
        0,
        1,
        user.id,
        datetime.utcnow().isoformat(),
    ))

    raffle_id = cursor.lastrowid

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
        ]
    ])

    message = (
        f"🎉 <b>{title}</b>\n\n"
        f"🎁 <b>Prize:</b> {prize}\n"
        f"💵 <b>Entry:</b> ${RAFFLE_ENTRY_COST:.2f}\n\n"
        f"Tap below to enter the raffle."
    )

    await update.effective_message.reply_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    return raffle_id


# ============================================================
# ENTER RAFFLE
# ============================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Handles a raffle entry request.
    """

    query = update.callback_query

    if query:
        await query.answer()

        data = query.data or ""

        try:
            raffle_id = int(data.split(":")[1])
        except (IndexError, ValueError):
            await query.answer(
                "Invalid raffle.",
                show_alert=True
            )
            return

        user = query.from_user

    else:
        user = update.effective_user
        raffle = get_open_raffle()

        if not raffle:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "❌ There is no active raffle."
                )
            return

        raffle_id = raffle["id"]

    raffle = get_raffle(raffle_id)

    if not raffle:
        text = "❌ Raffle not found."

        if query:
            await query.edit_message_text(text)
        else:
            await update.effective_message.reply_text(text)

        return

    if raffle["status"] != "open":
        text = "❌ This raffle is closed."

        if query:
            await query.answer(text, show_alert=True)
        else:
            await update.effective_message.reply_text(text)

        return

    if user_has_entry(raffle_id, user.id):
        text = "⚠️ You already have an entry in this raffle."

        if query:
            await query.answer(text, show_alert=True)
        else:
            await update.effective_message.reply_text(text)

        return

    max_entries = raffle["max_entries"]

    if max_entries and get_entry_count(raffle_id) >= max_entries:
        text = "❌ This raffle is full."

        if query:
            await query.answer(text, show_alert=True)
        else:
            await update.effective_message.reply_text(text)

        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO raffle_entries (
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
        user.username,
        user.first_name,
        datetime.utcnow().isoformat(),
    ))

    conn.commit()
    conn.close()

    keyboard = payment_button(raffle_id)

    text = (
        f"🎟 <b>Entry Created</b>\n\n"
        f"Raffle: <b>{raffle['title']}</b>\n"
        f"Entry cost: <b>${raffle['entry_cost']:.2f}</b>\n\n"
        f"Your entry is pending payment.\n"
        f"Choose a payment method below."
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
# PAID ENTRY
# ============================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Marks the user's raffle entry as paid.

    Intended for admin confirmation through callback buttons.
    """

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""

    try:
        # Format:
        # raffle_paid:raffle_id:user_id
        _, raffle_id, user_id = data.split(":")
        raffle_id = int(raffle_id)
        user_id = int(user_id)
    except (ValueError, IndexError):
        await query.answer(
            "Invalid payment request.",
            show_alert=True
        )
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE raffle_entries
        SET paid = 1
        WHERE raffle_id = ?
          AND user_id = ?
    """, (
        raffle_id,
        user_id,
    ))

    conn.commit()
    changed = cursor.rowcount
    conn.close()

    if changed:
        await query.edit_message_text(
            "✅ Payment confirmed. The raffle entry is active."
        )
    else:
        await query.edit_message_text(
            "❌ Entry could not be found."
        )


# ============================================================
# PAYMENT BUTTON
# ============================================================

def payment_button(raffle_id: Optional[int] = None):
    """
    Creates the payment-method keyboard.

    This function is intentionally synchronous because bot.py
    may call it directly while constructing a reply markup.
    """

    if raffle_id is None:
        raffle = get_open_raffle()
        raffle_id = raffle["id"] if raffle else 0

    buttons = []

    if CASHAPP_USERNAME:
        cashapp_url = (
            f"https://cash.app/${CASHAPP_USERNAME.lstrip('$')}"
        )

        buttons.append([
            InlineKeyboardButton(
                "💚 Pay with Cash App",
                url=cashapp_url
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "💙 Pay with Zelle",
            callback_data=f"raffle_zelle:{raffle_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "✅ I Paid",
            callback_data=f"raffle_paid_request:{raffle_id}"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# ============================================================
# ADMIN PAYMENT BUTTON
# ============================================================

def admin_payment_button(
    raffle_id: int,
    user_id: int
):
    """
    Keyboard for an admin to confirm a user's payment.
    """

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Confirm Payment",
                callback_data=f"raffle_paid:{raffle_id}:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Reject Payment",
                callback_data=f"raffle_reject:{raffle_id}:{user_id}"
            )
        ]
    ])


# ============================================================
# PAYMENT INFORMATION
# ============================================================

async def show_payment_info(
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
            raffle_id = None
    else:
        raffle_id = None

    raffle = get_raffle(raffle_id)

    if not raffle:
        text = "❌ No active raffle."
    else:
        text = (
            f"💳 <b>Payment Information</b>\n\n"
            f"Entry: <b>${raffle['entry_cost']:.2f}</b>\n\n"
        )

        if CASHAPP_USERNAME:
            text += (
                f"💚 <b>Cash App:</b> "
                f"${CASHAPP_USERNAME.lstrip('$')}\n"
            )

        if ZELLE_EMAIL:
            text += (
                f"💙 <b>Zelle:</b> "
                f"{ZELLE_EMAIL}\n"
            )

        text += (
            "\nAfter sending payment, tap "
            "<b>I Paid</b>."
        )

    keyboard = payment_button(
        raffle["id"] if raffle else raffle_id
    )

    if query:
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# ============================================================
# ADMIN PAYMENT REQUEST
# ============================================================

async def payment_confirmation_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    User presses "I Paid".

    This does not automatically mark payment as valid.
    It sends the user/admin flow to payment confirmation.
    """

    query = update.callback_query

    if not query:
        return

    await query.answer(
        "Payment marked for review.",
        show_alert=True
    )

    data = query.data or ""

    try:
        raffle_id = int(data.split(":")[1])
    except (IndexError, ValueError):
        return

    raffle = get_raffle(raffle_id)

    if not raffle:
        return

    user = query.from_user

    # Update payment reference/status without falsely marking it paid.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE raffle_entries
        SET payment_reference = ?
        WHERE raffle_id = ?
          AND user_id = ?
    """, (
        "PAYMENT_REVIEW_REQUESTED",
        raffle_id,
        user.id,
    ))

    conn.commit()
    conn.close()

    await query.edit_message_text(
        "⏳ <b>Payment submitted for review.</b>\n\n"
        "An admin will verify your payment before your "
        "entry becomes active.",
        parse_mode="HTML"
    )


# ============================================================
# ZELLE INFORMATION
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
            f"💙 <b>Zelle Payment</b>\n\n"
            f"Send <b>${RAFFLE_ENTRY_COST:.2f}</b> to:\n"
            f"<code>{ZELLE_EMAIL}</code>\n\n"
            f"After payment, return and tap "
            f"<b>I Paid</b>."
        )
    else:
        text = (
            "💙 <b>Zelle Payment</b>\n\n"
            "Zelle payment information has not been "
            "configured yet."
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML"
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
        _, raffle_id, user_id = data.split(":")
        raffle_id = int(raffle_id)
        user_id = int(user_id)
    except (ValueError, IndexError):
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE raffle_entries
        SET paid = 0,
            payment_reference = 'PAYMENT_REJECTED'
        WHERE raffle_id = ?
          AND user_id = ?
    """, (
        raffle_id,
        user_id,
    ))

    conn.commit()
    conn.close()

    await query.edit_message_text(
        "❌ Payment rejected. The user can submit payment again."
    )


# ============================================================
# DRAW WINNER
# ============================================================

async def draw_winner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Draws a winner from paid entries.

    Admin permission should be enforced by bot.py.
    """

    raffle = get_open_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ There is no active raffle."
        )
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM raffle_entries
        WHERE raffle_id = ?
          AND paid = 1
    """, (raffle["id"],))

    entries = cursor.fetchall()

    if not entries:
        conn.close()

        await update.effective_message.reply_text(
            "❌ There are no paid entries."
        )
        return

    winners = random.sample(
        entries,
        min(
            raffle["winner_count"],
            len(entries)
        )
    )

    cursor.execute("""
        UPDATE raffles
        SET status = 'closed',
            closed_at = ?
        WHERE id = ?
    """, (
        datetime.utcnow().isoformat(),
        raffle["id"],
    ))

    conn.commit()
    conn.close()

    winner_lines = []

    for winner in winners:
        if winner["username"]:
            name = f"@{winner['username']}"
        else:
            name = winner["first_name"] or str(winner["user_id"])

        winner_lines.append(f"🏆 {name}")

    await update.effective_message.reply_text(
        "🎉 <b>RAFFLE WINNER!</b>\n\n"
        f"🎁 {raffle['prize']}\n\n"
        + "\n".join(winner_lines),
        parse_mode="HTML"
    )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "start_raffle",
    "get_raffle",
    "enter_raffle",
    "paid_entry",
    "payment_button",
    "admin_payment_button",
    "show_payment_info",
    "payment_confirmation_request",
    "show_zelle",
    "reject_payment",
    "draw_winner",
    "init_raffle_database",
]
