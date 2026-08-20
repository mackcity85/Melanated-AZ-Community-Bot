# raffle.py
"""
Melanated AZ Bot - Raffle System

Compatible with:
- Python 3.12+
- python-telegram-bot 21+
- Existing bot.py imports

This module intentionally keeps configuration simple so it does not
depend on RAFFLE_ENTRY_COST or DB_NAME being present in config.py.
"""

import os
import sqlite3
import random
import re
from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes


# ============================================================
# CONFIGURATION
# ============================================================

RAFFLE_ENTRY_COST = float(
    re.sub(
        r"[^0-9.]",
        "",
        os.getenv("RAFFLE_ENTRY_COST", "5")
    ) or "5"
)

DB_NAME = os.getenv(
    "RAFFLE_DB_NAME",
    "raffle.db"
)

CASH_APP = os.getenv(
    "CASH_APP",
    os.getenv("CASHAPP", "")
)

ZELLE = os.getenv(
    "ZELLE",
    ""
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    """Return a SQLite connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_raffle_database():
    """Create raffle tables if they do not already exist."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raffles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            prize TEXT NOT NULL,
            entry_cost REAL NOT NULL,
            max_entries INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'open',
            winner_user_id INTEGER,
            winner_username TEXT,
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
            entries INTEGER NOT NULL DEFAULT 1,
            payment_method TEXT,
            payment_reference TEXT,
            paid INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (raffle_id) REFERENCES raffles(id)
        )
    """)

    conn.commit()
    conn.close()


# Initialize automatically when imported.
init_raffle_database()


# ============================================================
# HELPERS
# ============================================================

def _now():
    return datetime.now(timezone.utc).isoformat()


def _format_money(amount):
    return f"${amount:.2f}"


def _is_admin(user_id: int) -> bool:
    """
    Check ADMIN_IDS without requiring config.py.
    """

    raw = os.getenv("ADMIN_IDS", "")

    if not raw.strip():
        # Keep compatibility with the admin ID shown in your logs.
        raw = "5879167814"

    admin_ids = set()

    for value in raw.split(","):
        value = value.strip()

        if value.isdigit():
            admin_ids.add(int(value))

    return user_id in admin_ids


def get_active_raffle():
    """Return the currently open raffle."""

    conn = get_connection()

    raffle = conn.execute("""
        SELECT *
        FROM raffles
        WHERE status = 'open'
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    return raffle


def get_raffle(raffle_id: int):
    """Return a raffle by ID."""

    conn = get_connection()

    raffle = conn.execute("""
        SELECT *
        FROM raffles
        WHERE id = ?
    """, (raffle_id,)).fetchone()

    conn.close()

    return raffle


def get_entry_count(raffle_id: int):
    """Return total paid entries for a raffle."""

    conn = get_connection()

    row = conn.execute("""
        SELECT COALESCE(SUM(entries), 0) AS total
        FROM raffle_entries
        WHERE raffle_id = ?
        AND paid = 1
    """, (raffle_id,)).fetchone()

    conn.close()

    return int(row["total"])


# ============================================================
# START RAFFLE
# ============================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Start a new raffle.

    Usage:
        /raffle
        /raffle Prize Name

    Admin only.
    """

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    if not _is_admin(user_id):
        await update.effective_message.reply_text(
            "❌ You are not authorized to start a raffle."
        )
        return

    existing = get_active_raffle()

    if existing:
        await update.effective_message.reply_text(
            f"⚠️ There is already an active raffle.\n\n"
            f"🎟️ Raffle #{existing['id']}\n"
            f"🏆 Prize: {existing['prize']}\n"
            f"💵 Entry: {_format_money(existing['entry_cost'])}"
        )
        return

    args = context.args or []

    if args:
        prize = " ".join(args)
    else:
        prize = "Melanated AZ Raffle Prize"

    conn = get_connection()

    cursor = conn.execute("""
        INSERT INTO raffles (
            title,
            prize,
            entry_cost,
            max_entries,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, 'open', ?)
    """, (
        "Melanated AZ Raffle",
        prize,
        RAFFLE_ENTRY_COST,
        0,
        _now()
    ))

    raffle_id = cursor.lastrowid

    conn.commit()
    conn.close()

    payment_text = []

    if CASH_APP:
        payment_text.append(f"💳 Cash App: {CASH_APP}")

    if ZELLE:
        payment_text.append(f"💳 Zelle: {ZELLE}")

    payment_info = "\n".join(payment_text)

    if not payment_info:
        payment_info = (
            "💳 Payment information will be provided by an admin."
        )

    message = (
        "🎉 **RAFFLE IS NOW OPEN!** 🎉\n\n"
        f"🎟️ Raffle #: `{raffle_id}`\n"
        f"🏆 Prize: **{prize}**\n"
        f"💵 Entry: **{_format_money(RAFFLE_ENTRY_COST)}**\n\n"
        "To enter, send your payment using one of the methods below "
        "and then submit your payment reference to an admin.\n\n"
        f"{payment_info}\n\n"
        "Good luck! 🍀"
    )

    await update.effective_message.reply_text(
        message,
        parse_mode="Markdown"
    )


# ============================================================
# SHOW RAFFLE
# ============================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Show the current raffle."""

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "🎟️ There is currently no active raffle."
        )
        return

    entries = get_entry_count(raffle["id"])

    message = (
        "🎟️ **CURRENT RAFFLE**\n\n"
        f"🏆 Prize: **{raffle['prize']}**\n"
        f"💵 Entry: **{_format_money(raffle['entry_cost'])}**\n"
        f"🎫 Paid Entries: **{entries}**\n\n"
        "Use the raffle entry process to participate."
    )

    await update.effective_message.reply_text(
        message,
        parse_mode="Markdown"
    )


# ============================================================
# ADD ENTRY
# ============================================================

async def add_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Add a paid raffle entry.

    Admin can enter:
        /raffleentry USER_ID

    Or a user can enter:
        /raffleentry

    Payment is NOT automatically considered verified.
    """

    if not update.effective_user:
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ There is no active raffle right now."
        )
        return

    user = update.effective_user

    target_user_id = user.id

    if context.args and _is_admin(user.id):
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.effective_message.reply_text(
                "❌ Invalid user ID."
            )
            return

    conn = get_connection()

    existing = conn.execute("""
        SELECT id
        FROM raffle_entries
        WHERE raffle_id = ?
        AND user_id = ?
        AND paid = 1
    """, (
        raffle["id"],
        target_user_id
    )).fetchone()

    if existing:
        conn.close()

        await update.effective_message.reply_text(
            "⚠️ That user already has a paid entry in this raffle."
        )
        return

    conn.execute("""
        INSERT INTO raffle_entries (
            raffle_id,
            user_id,
            username,
            first_name,
            entries,
            payment_method,
            payment_reference,
            paid,
            created_at
        )
        VALUES (?, ?, ?, ?, 1, '', '', 0, ?)
    """, (
        raffle["id"],
        target_user_id,
        user.username or "",
        user.first_name or "",
        _now()
    ))

    conn.commit()
    conn.close()

    await update.effective_message.reply_text(
        "📝 Entry recorded as **PENDING PAYMENT**.\n\n"
        f"💵 Amount: {_format_money(raffle['entry_cost'])}\n"
        "An admin must verify the payment before the entry "
        "is included in the drawing.",
        parse_mode="Markdown"
    )


# ============================================================
# VERIFY ENTRY
# ============================================================

async def verify_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Admin command:

        /verifyraffle USER_ID

    Marks the user's most recent pending entry as paid.
    """

    if not update.effective_user:
        return

    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "❌ Admin only."
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage:\n/verifyraffle USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Invalid user ID."
        )
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ No active raffle."
        )
        return

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM raffle_entries
        WHERE raffle_id = ?
        AND user_id = ?
        AND paid = 0
        ORDER BY id DESC
        LIMIT 1
    """, (
        raffle["id"],
        user_id
    )).fetchone()

    if not row:
        conn.close()

        await update.effective_message.reply_text(
            "❌ No pending entry was found for that user."
        )
        return

    conn.execute("""
        UPDATE raffle_entries
        SET paid = 1
        WHERE id = ?
    """, (row["id"],))

    conn.commit()
    conn.close()

    await update.effective_message.reply_text(
        f"✅ Raffle entry verified for user `{user_id}`.",
        parse_mode="Markdown"
    )


# ============================================================
# DRAW RAFFLE
# ============================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Draw a random winner. Admin only."""

    if not update.effective_user:
        return

    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "❌ Admin only."
        )
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ There is no active raffle."
        )
        return

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM raffle_entries
        WHERE raffle_id = ?
        AND paid = 1
    """, (raffle["id"],)).fetchall()

    if not rows:
        conn.close()

        await update.effective_message.reply_text(
            "❌ There are no verified paid entries."
        )
        return

    # Create one weighted ticket per entry.
    tickets = []

    for row in rows:
        for _ in range(max(1, int(row["entries"]))):
            tickets.append(row)

    winner = random.choice(tickets)

    conn.execute("""
        UPDATE raffles
        SET status = 'closed',
            winner_user_id = ?,
            winner_username = ?,
            closed_at = ?
        WHERE id = ?
    """, (
        winner["user_id"],
        winner["username"] or "",
        _now(),
        raffle["id"]
    ))

    conn.commit()
    conn.close()

    winner_name = winner["username"]

    if winner_name:
        winner_display = f"@{winner_name}"
    else:
        winner_display = str(winner["user_id"])

    await update.effective_message.reply_text(
        "🎉 **RAFFLE WINNER!** 🎉\n\n"
        f"🏆 Prize: **{raffle['prize']}**\n"
        f"🎟️ Raffle #: `{raffle['id']}`\n\n"
        f"👑 Winner: **{winner_display}**\n\n"
        "Congratulations! 🎊",
        parse_mode="Markdown"
    )


# ============================================================
# CANCEL RAFFLE
# ============================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Cancel the active raffle. Admin only."""

    if not update.effective_user:
        return

    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "❌ Admin only."
        )
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ There is no active raffle."
        )
        return

    conn = get_connection()

    conn.execute("""
        UPDATE raffles
        SET status = 'cancelled',
            closed_at = ?
        WHERE id = ?
    """, (
        _now(),
        raffle["id"]
    ))

    conn.commit()
    conn.close()

    await update.effective_message.reply_text(
        f"🛑 Raffle #{raffle['id']} has been cancelled."
    )


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

# These aliases allow different versions of bot.py to work
# without requiring another raffle.py rewrite.

create_raffle = start_raffle
show_raffle = raffle_status
enter_raffle = add_raffle_entry
verify_entry = verify_raffle_entry
close_raffle = draw_raffle
end_raffle = draw_raffle


# ============================================================
# EXPORTED FUNCTIONS
# ============================================================

__all__ = [
    "RAFFLE_ENTRY_COST",
    "start_raffle",
    "get_raffle",
    "get_active_raffle",
    "raffle_status",
    "add_raffle_entry",
    "verify_raffle_entry",
    "draw_raffle",
    "cancel_raffle",
    "create_raffle",
    "show_raffle",
    "enter_raffle",
    "verify_entry",
    "close_raffle",
    "end_raffle",
]
