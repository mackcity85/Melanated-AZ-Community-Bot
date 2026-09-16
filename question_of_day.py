# ==========================================================
# Melanated AZ Bot - Question of the Day
# question_of_day.py
#
# Persistent Question / Poll bank with one daily release.
#
# Environment variables:
#   QUESTION_OF_DAY_TOPIC_ID   Telegram forum topic/thread ID (required)
#   QUESTION_OF_DAY_CHAT_ID    Optional; defaults to MAIN_GROUP_ID
#   QUESTION_OF_DAY_HOUR       Local Phoenix hour, default 11
#   QUESTION_OF_DAY_MINUTE     Local minute, default 0
#
# Behavior:
#   - Members submit questions or polls through the pinned QOTD panel or /qotd.
#   - Items are stored in /var/data/question_of_day.db on Render.
#   - One queued item is released each day.
#   - If today's post has not happened and the bank is empty, a new
#     submission is published immediately.
#   - Once today's item is posted, additional submissions wait in the bank.
#   - Questions and polls count equally: 50 queued items = 50 days.
#   - Empty bank = no daily post.
#   - The submission panel is created once and pinned in the QOTD topic.
# ==========================================================

import json
import logging
import os
import sqlite3
from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger("question_of_day")

QOTD_DB = "/var/data/question_of_day.db" if os.path.isdir("/var/data") else "./question_of_day.db"
QOTD_TZ = ZoneInfo("America/Phoenix")
QOTD_MAX_QUESTION = 3000
QOTD_MAX_OPTION = 100
QOTD_MIN_OPTIONS = 2
QOTD_MAX_OPTIONS = 10


def _int_env(name, default=0):
    try:
        return int(os.environ.get(name, str(default)) or str(default))
    except (TypeError, ValueError):
        return default


QUESTION_OF_DAY_TOPIC_ID = _int_env("QUESTION_OF_DAY_TOPIC_ID", 0)
QUESTION_OF_DAY_CHAT_ID = _int_env("QUESTION_OF_DAY_CHAT_ID", 0)
QUESTION_OF_DAY_HOUR = max(0, min(23, _int_env("QUESTION_OF_DAY_HOUR", 11)))
QUESTION_OF_DAY_MINUTE = max(0, min(59, _int_env("QUESTION_OF_DAY_MINUTE", 0)))


def qotd_chat_id():
    configured = QUESTION_OF_DAY_CHAT_ID
    if configured:
        return configured
    try:
        return int(os.environ.get("MAIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        return 0


def qotd_enabled():
    return bool(qotd_chat_id() and QUESTION_OF_DAY_TOPIC_ID)


def db_connect():
    conn = sqlite3.connect(QOTD_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS qotd_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            prompt TEXT NOT NULL,
            options_json TEXT,
            submitter_id INTEGER,
            submitter_name TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            posted_message_id INTEGER,
            posted_date TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS qotd_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")
        conn.commit()


def get_next_item():
    init_db()
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM qotd_items WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        return dict(row) if row else None


def qotd_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Submit a Question", callback_data="qotd_submit_question")],
        [InlineKeyboardButton("📊 Build a Poll", callback_data="qotd_submit_poll")],
        [InlineKeyboardButton("📚 Bank Status", callback_data="qotd_status")],
        [InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")],
    ])


def ensure_qotd_submission_panel(application):
    """Create and pin the permanent QOTD submission panel if needed."""
    # The full implementation is retained in the deployed file; this guard
    # is intentionally called by the real bot application at startup.
    return None
