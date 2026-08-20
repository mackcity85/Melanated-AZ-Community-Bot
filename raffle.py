"""
Melanated AZ Bot - Raffle System
Compatible with python-telegram-bot 21+

This file intentionally keeps raffle configuration and database handling
out of config.py so missing config variables do not crash the bot.
"""

import os
import random
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

# Raffle entry price.
# Render can override this with RAFFLE_ENTRY_COST=5
# Both "$5" and "5" are accepted.
def get_entry_cost() -> float:
    value = os.getenv("RAFFLE_ENTRY_COST", "5")

    try:
        cleaned = (
            str(value)
            .strip()
            .replace("$", "")
            .replace(",", "")
        )

        return float(cleaned)

    except (ValueError, TypeError):
        logger.warning(
            "Invalid RAFFLE_ENTRY_COST=%r. Using $5.00.",
            value,
        )
        return 5.00


RAFFLE_ENTRY_COST = get_entry_cost()

# Database location.
# Does NOT require DB_NAME in config.py.
DB_NAME = os.getenv(
    "RAFFLE_DB_NAME",
    "raffle_database.db",
)

DB_PATH = Path(DB_NAME)

# Payment methods
CASHAPP = os.getenv("CASHAPP_USERNAME", "").strip()
ZELLE = os.getenv("ZELLE_EMAIL", "").strip()

# ============================================================
# DATABASE
# ============================================================


def get_connection():
    """Return a SQLite connection."""
    connection = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_database():
    """Create raffle tables if they do not already exist."""

    with get_connection() as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raffles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                prize TEXT NOT NULL,
                entry_cost REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                winner_user_id INTEGER,
                winner_username TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raffle_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raffle_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                payment_method TEXT,
                payment_reference TEXT,
                verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,

                FOREIGN KEY (raffle_id)
                REFERENCES raffles(id)
            )
            """
        )

        conn.commit()


# Initialize immediately when imported.
init_database()


# ============================================================
# HELPERS
# ============================================================


def money(value: float) -> str:
    return f"${value:.2f}"


def is_admin(user_id: int) -> bool:
    """
    Admin IDs are read directly from ADMIN_IDS.

    Example Render variable:
        ADMIN_IDS=5879167814,123456789
    """

    raw = os.getenv("ADMIN_IDS", "")

    if not raw:
        return False

    admin_ids = set()

    for item in raw.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            admin_ids.add(int(item))
        except ValueError:
            continue

    return user_id in admin_ids


def get_open_raffle():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM raffles
            WHERE status = 'open'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return row


def get_raffle(raffle_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM raffles
            WHERE id = ?
            """,
            (raffle_id,),
        ).fetchone()

    return row


def user_already_entered(
    raffle_id: int,
    user_id: int,
) -> bool:

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM raffle_entries
            WHERE raffle_id = ?
              AND user_id = ?
              AND verified = 1
            LIMIT 1
            """,
            (raffle_id, user_id),
        ).fetchone()

    return row is not None


def get_entry_count(raffle_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM raffle_entries
            WHERE raffle_id = ?
              AND verified = 1
            """,
            (raffle_id,),
        ).fetchone()

    return int(row["total"])


# ============================================================
# CREATE RAFFLE
# ============================================================


async def raffle_create(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ You are not authorized to create raffles."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n"
            "/raffle_create Prize Name | Description\n\n"
            "Example:\n"
            "/raffle_create $100 Cash Prize | Melanated AZ raffle"
        )
        return

    raw = " ".join(context.args)

    if "|" in raw:
        prize, name = raw.split("|", 1)
        prize = prize.strip()
        name = name.strip()
    else:
        prize = raw.strip()
        name = "Melanated AZ Raffle"

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO raffles
            (
                name,
                prize,
                entry_cost,
                status,
                created_at
            )
            VALUES (?, ?, ?, 'open', ?)
            """,
            (
                name,
                prize,
                RAFFLE_ENTRY_COST,
                now,
            ),
        )

        raffle_id = cursor.lastrowid

        conn.commit()

    await update.message.reply_text(
        f"🎟️ *RAFFLE CREATED!*\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry: {money(RAFFLE_ENTRY_COST)}\n"
        f"🆔 Raffle #: {raffle_id}\n\n"
        f"Use /raffle to view the raffle.",
        parse_mode="Markdown",
    )


# ============================================================
# SHOW RAFFLE
# ============================================================


async def raffle_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    raffle = get_open_raffle()

    if not raffle:
        await update.message.reply_text(
            "🎟️ There is currently no open raffle."
        )
        return

    count = get_entry_count(raffle["id"])

    keyboard = [
        [
            InlineKeyboardButton(
                "🎟️ Enter Raffle",
                callback_data=f"raffle_enter:{raffle['id']}",
            )
        ]
    ]

    await update.message.reply_text(
        f"🎟️ *{raffle['name']}*\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {money(raffle['entry_cost'])}\n"
        f"👥 Entries: {count}\n\n"
        f"Choose *Enter Raffle* below to get payment instructions.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ============================================================
# ENTER RAFFLE
# ============================================================


async def raffle_enter_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if not query.from_user:
        return

    try:
        raffle_id = int(
            query.data.split(":", 1)[1]
        )
    except (ValueError, IndexError):
        await query.message.reply_text(
            "❌ Invalid raffle."
        )
        return

    raffle = get_raffle(raffle_id)

    if not raffle or raffle["status"] != "open":
        await query.message.reply_text(
            "❌ This raffle is no longer open."
        )
        return

    if user_already_entered(
        raffle_id,
        query.from_user.id,
    ):
        await query.message.reply_text(
            "✅ You are already entered in this raffle."
        )
        return

    payment_lines = []

    if CASHAPP:
        payment_lines.append(
            f"💵 Cash App: {CASHAPP}"
        )

    if ZELLE:
        payment_lines.append(
            f"🏦 Zelle: {ZELLE}"
        )

    if not payment_lines:
        payment_lines.append(
            "⚠️ Payment information has not been configured yet."
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "💵 Cash App",
                callback_data=f"raffle_payment:cashapp:{raffle_id}",
            ),
            InlineKeyboardButton(
                "🏦 Zelle",
                callback_data=f"raffle_payment:zelle:{raffle_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "✅ I Paid",
                callback_data=f"raffle_paid:{raffle_id}",
            )
        ],
    ]

    await query.message.reply_text(
        f"🎟️ *Raffle Entry*\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Cost: {money(raffle['entry_cost'])}\n\n"
        + "\n".join(payment_lines)
        + "\n\n"
        "Send the entry fee, then press *I Paid*.\n"
        "Your entry will be recorded for verification.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ============================================================
# PAYMENT BUTTON
# ============================================================


async def raffle_payment_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    parts = query.data.split(":")

    if len(parts) != 3:
        return

    method = parts[1]
    raffle_id = parts[2]

    if method == "cashapp":
        account = CASHAPP
        label = "Cash App"
    else:
        account = ZELLE
        label = "Zelle"

    if not account:
        await query.message.reply_text(
            f"❌ {label} is not configured."
        )
        return

    await query.message.reply_text(
        f"💳 *{label} Payment*\n\n"
        f"Send *{money(RAFFLE_ENTRY_COST)}* to:\n"
        f"`{account}`\n\n"
        f"After sending payment, return to the raffle "
        f"and press *I Paid*.",
        parse_mode="Markdown",
    )


# ============================================================
# MARK AS PAID
# ============================================================


async def raffle_paid_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    try:
        raffle_id = int(
            query.data.split(":", 1)[1]
        )
    except (ValueError, IndexError):
        return

    raffle = get_raffle(raffle_id)

    if not raffle or raffle["status"] != "open":
        await query.message.reply_text(
            "❌ This raffle is closed."
        )
        return

    if user_already_entered(
        raffle_id,
        user.id,
    ):
        await query.message.reply_text(
            "✅ You are already entered."
        )
        return

    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO raffle_entries
            (
                raffle_id,
                user_id,
                username,
                first_name,
                payment_method,
                payment_reference,
                verified,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                raffle_id,
                user.id,
                user.username,
                user.first_name,
                "pending",
                None,
                now,
            ),
        )

        conn.commit()

    await query.message.reply_text(
        "📝 *Payment Submitted*\n\n"
        "Your raffle entry has been submitted for verification.\n\n"
        "Once payment is verified, your entry will be officially "
        "added to the drawing.",
        parse_mode="Markdown",
    )


# ============================================================
# ADMIN: VERIFY ENTRY
# ============================================================


async def raffle_verify(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin only."
        )
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n"
            "/raffle_verify ENTRY_ID"
        )
        return

    try:
        entry_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )
        return

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE id = ?
            """,
            (entry_id,),
        ).fetchone()

        if not row:
            await update.message.reply_text(
                "❌ Entry not found."
            )
            return

        conn.execute(
            """
            UPDATE raffle_entries
            SET verified = 1
            WHERE id = ?
            """,
            (entry_id,),
        )

        conn.commit()

    await update.message.reply_text(
        f"✅ Entry #{entry_id} verified."
    )


# ============================================================
# ADMIN: DRAW WINNER
# ============================================================


async def raffle_draw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin only."
        )
        return

    raffle = get_open_raffle()

    if not raffle:
        await update.message.reply_text(
            "❌ No open raffle."
        )
        return

    with get_connection() as conn:
        entries = conn.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE raffle_id = ?
              AND verified = 1
            """,
            (raffle["id"],),
        ).fetchall()

    if not entries:
        await update.message.reply_text(
            "❌ There are no verified entries."
        )
        return

    winner = random.choice(entries)

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE raffles
            SET
                status = 'closed',
                winner_user_id = ?,
                winner_username = ?
            WHERE id = ?
            """,
            (
                winner["user_id"],
                winner["username"],
                raffle["id"],
            ),
        )

        conn.commit()

    winner_name = (
        f"@{winner['username']}"
        if winner["username"]
        else winner["first_name"]
        or str(winner["user_id"])
    )

    await update.message.reply_text(
        f"🎉 *RAFFLE WINNER!*\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"🏆 Winner: {winner_name}\n\n"
        f"Congratulations! 🎊",
        parse_mode="Markdown",
    )


# ============================================================
# ADMIN: RAFFLE STATUS
# ============================================================


async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ Admin only."
        )
        return

    raffle = get_open_raffle()

    if not raffle:
        await update.message.reply_text(
            "🎟️ No open raffle."
        )
        return

    count = get_entry_count(raffle["id"])

    await update.message.reply_text(
        f"🎟️ *Raffle Status*\n\n"
        f"🆔 #{raffle['id']}\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {money(raffle['entry_cost'])}\n"
        f"👥 Verified Entries: {count}\n"
        f"📌 Status: {raffle['status']}",
        parse_mode="Markdown",
    )


# ============================================================
# HANDLER REGISTRATION
# ============================================================


def get_raffle_handlers():

    return [
        CommandHandler(
            "raffle",
            raffle_command,
        ),

        CommandHandler(
            "raffle_create",
            raffle_create,
        ),

        CommandHandler(
            "raffle_verify",
            raffle_verify,
        ),

        CommandHandler(
            "raffle_draw",
            raffle_draw,
        ),

        CommandHandler(
            "raffle_status",
            raffle_status,
        ),

        CallbackQueryHandler(
            raffle_enter_callback,
            pattern=r"^raffle_enter:\d+$",
        ),

        CallbackQueryHandler(
            raffle_payment_callback,
            pattern=r"^raffle_payment:(cashapp|zelle):\d+$",
        ),

        CallbackQueryHandler(
            raffle_paid_callback,
            pattern=r"^raffle_paid:\d+$",
        ),
    ]


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

# These make it easier for bot.py to import the module even if
# your previous bot.py used slightly different function names.

raffle_handlers = get_raffle_handlers()

handlers = raffle_handlers
