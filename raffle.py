# raffle.py

import os
import sqlite3
import random
import re
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes


# ============================================================
# CONFIGURATION
# ============================================================

def get_money(value, default=5.00):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(value))
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


RAFFLE_ENTRY_COST = get_money(
    os.getenv("RAFFLE_ENTRY_COST", "5")
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
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_raffle_database()


# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now(timezone.utc).isoformat()


def money(amount):
    return f"${float(amount):.2f}"


def is_admin(user_id):
    raw = os.getenv("ADMIN_IDS", "").strip()

    # Compatibility with the existing admin shown in your logs.
    if not raw:
        raw = "5879167814"

    admin_ids = set()

    for item in raw.split(","):
        item = item.strip()

        if item.isdigit():
            admin_ids.add(int(item))

    return user_id in admin_ids


def get_active_raffle():
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


def get_raffle(raffle_id):
    conn = get_connection()

    raffle = conn.execute("""
        SELECT *
        FROM raffles
        WHERE id = ?
    """, (raffle_id,)).fetchone()

    conn.close()

    return raffle


def get_entry_count(raffle_id):
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
    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "❌ Admin only."
        )
        return

    existing = get_active_raffle()

    if existing:
        await update.effective_message.reply_text(
            "⚠️ A raffle is already active.\n\n"
            f"🎟️ Raffle #{existing['id']}\n"
            f"🏆 Prize: {existing['prize']}\n"
            f"💵 Entry: {money(existing['entry_cost'])}"
        )
        return

    prize = (
        " ".join(context.args)
        if context.args
        else "Melanated AZ Raffle Prize"
    )

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
        now()
    ))

    raffle_id = cursor.lastrowid

    conn.commit()
    conn.close()

    payment_lines = []

    if CASH_APP:
        payment_lines.append(
            f"💳 Cash App: {CASH_APP}"
        )

    if ZELLE:
        payment_lines.append(
            f"💳 Zelle: {ZELLE}"
        )

    payment_text = "\n".join(payment_lines)

    if not payment_text:
        payment_text = (
            "💳 Payment information will be provided by an admin."
        )

    await update.effective_message.reply_text(
        "🎉 RAFFLE IS OPEN! 🎉\n\n"
        f"🎟️ Raffle #: {raffle_id}\n"
        f"🏆 Prize: {prize}\n"
        f"💵 Entry: {money(RAFFLE_ENTRY_COST)}\n\n"
        f"{payment_text}\n\n"
        "After payment, submit your payment information "
        "to an admin for verification."
    )


# ============================================================
# RAFFLE STATUS
# ============================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "🎟️ There is currently no active raffle."
        )
        return

    count = get_entry_count(raffle["id"])

    await update.effective_message.reply_text(
        "🎟️ CURRENT RAFFLE\n\n"
        f"🏆 Prize: {raffle['prize']}\n"
        f"💵 Entry: {money(raffle['entry_cost'])}\n"
        f"🎫 Verified Entries: {count}"
    )


# ============================================================
# CREATE / PENDING ENTRY
# ============================================================

async def add_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ There is no active raffle."
        )
        return

    user = update.effective_user

    conn = get_connection()

    existing = conn.execute("""
        SELECT id
        FROM raffle_entries
        WHERE raffle_id = ?
        AND user_id = ?
        AND paid = 1
    """, (
        raffle["id"],
        user.id
    )).fetchone()

    if existing:
        conn.close()

        await update.effective_message.reply_text(
            "⚠️ You already have a verified entry."
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
        user.id,
        user.username or "",
        user.first_name or "",
        now()
    ))

    conn.commit()
    conn.close()

    await update.effective_message.reply_text(
        "📝 Your raffle entry has been recorded as PENDING.\n\n"
        f"💵 Amount: {money(raffle['entry_cost'])}\n\n"
        "An admin must verify your payment before your "
        "entry is included in the drawing."
    )


# ============================================================
# PAID ENTRY
# ============================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Mark a raffle entry as paid.

    Admin usage:

        /paid_entry USER_ID

    Also supports:

        /paid_entry USER_ID PAYMENT_METHOD REFERENCE
    """

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "❌ Admin only."
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage:\n"
            "/paid_entry USER_ID\n\n"
            "Optional:\n"
            "/paid_entry USER_ID PAYMENT_METHOD REFERENCE"
        )
        return

    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "❌ USER_ID must be a number."
        )
        return

    payment_method = (
        context.args[1]
        if len(context.args) >= 2
        else ""
    )

    payment_reference = (
        " ".join(context.args[2:])
        if len(context.args) >= 3
        else ""
    )

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ There is no active raffle."
        )
        return

    conn = get_connection()

    # Find most recent pending entry.
    entry = conn.execute("""
        SELECT *
        FROM raffle_entries
        WHERE raffle_id = ?
        AND user_id = ?
        AND paid = 0
        ORDER BY id DESC
        LIMIT 1
    """, (
        raffle["id"],
        target_user_id
    )).fetchone()

    if entry:
        conn.execute("""
            UPDATE raffle_entries
            SET paid = 1,
                payment_method = ?,
                payment_reference = ?
            WHERE id = ?
        """, (
            payment_method,
            payment_reference,
            entry["id"]
        ))
    else:
        # If no pending entry exists, create a verified entry.
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
            VALUES (?, ?, '', '', 1, ?, ?, 1, ?)
        """, (
            raffle["id"],
            target_user_id,
            payment_method,
            payment_reference,
            now()
        ))

    conn.commit()
    conn.close()

    await update.effective_message.reply_text(
        "✅ PAYMENT VERIFIED\n\n"
        f"👤 User ID: {target_user_id}\n"
        f"🎟️ Raffle: #{raffle['id']}\n"
        f"💵 Amount: {money(raffle['entry_cost'])}\n"
        f"💳 Method: {payment_method or 'Not specified'}"
    )


# ============================================================
# VERIFY ENTRY ALIAS
# ============================================================

async def verify_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    return await paid_entry(update, context)


# ============================================================
# DRAW RAFFLE
# ============================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
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

    entries = conn.execute("""
        SELECT *
        FROM raffle_entries
        WHERE raffle_id = ?
        AND paid = 1
    """, (raffle["id"],)).fetchall()

    if not entries:
        conn.close()

        await update.effective_message.reply_text(
            "❌ There are no verified paid entries."
        )
        return

    tickets = []

    for entry in entries:
        for _ in range(max(1, int(entry["entries"]))):
            tickets.append(entry)

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
        now(),
        raffle["id"]
    ))

    conn.commit()
    conn.close()

    winner_name = (
        f"@{winner['username']}"
        if winner["username"]
        else str(winner["user_id"])
    )

    await update.effective_message.reply_text(
        "🎉🎉 RAFFLE WINNER 🎉🎉\n\n"
        f"🏆 Prize: {raffle['prize']}\n"
        f"🎟️ Raffle #: {raffle['id']}\n\n"
        f"👑 Winner: {winner_name}\n\n"
        "Congratulations! 🎊"
    )


# ============================================================
# CANCEL RAFFLE
# ============================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "❌ Admin only."
        )
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.effective_message.reply_text(
            "❌ No active raffle."
        )
        return

    conn = get_connection()

    conn.execute("""
        UPDATE raffles
        SET status = 'cancelled',
            closed_at = ?
        WHERE id = ?
    """, (
        now(),
        raffle["id"]
    ))

    conn.commit()
    conn.close()

    await update.effective_message.reply_text(
        f"🛑 Raffle #{raffle['id']} cancelled."
    )


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

create_raffle = start_raffle
show_raffle = raffle_status
enter_raffle = add_raffle_entry
verify_entry = paid_entry
close_raffle = draw_raffle
end_raffle = draw_raffle


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "RAFFLE_ENTRY_COST",
    "start_raffle",
    "get_raffle",
    "get_active_raffle",
    "raffle_status",
    "add_raffle_entry",
    "paid_entry",
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
