"""Daily random-member spotlight for the Melanated AZ community."""

import logging
import os
import random
import sqlite3
from datetime import time
from zoneinfo import ZoneInfo

from telegram.constants import ParseMode
from telegram.error import TelegramError
from member_spotlight_question_bank import QUESTION_BANK

logger = logging.getLogger("melanatedaz.member_spotlight")

CHAT_ID = int(os.environ.get("MAIN_GROUP_ID", "-1002697105809") or "-1002697105809")
TOPIC_ID = int(os.environ.get("MEMBER_SPOTLIGHT_TOPIC_ID", "11999") or "11999")
ARIZONA_TZ = ZoneInfo("America/Phoenix")
JOB_NAME = "melanated-member-spotlight"
COMMUNITY_DB = "/var/data/community_security.db" if os.path.isdir("/var/data") else "./community_security.db"

# Prompts are loaded from member_spotlight_question_bank.py (200 curated questions).

def _connect():
    conn = sqlite3.connect(COMMUNITY_DB, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def _choose_member():
    from config import ADMIN_IDS

    excluded = {int(value) for value in ADMIN_IDS}
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS member_spotlight_history (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                selected_count INTEGER NOT NULL DEFAULT 0,
                last_selected_at TEXT,
                PRIMARY KEY (chat_id, user_id)
            )"""
        )
        placeholders = ",".join("?" for _ in excluded)
        sql = """
            SELECT m.user_id, m.first_name, m.username,
                   COALESCE(h.selected_count, 0) AS selected_count
            FROM community_members AS m
            LEFT JOIN member_spotlight_history AS h
              ON h.chat_id=m.chat_id AND h.user_id=m.user_id
            WHERE m.chat_id=? AND m.status='active'
              AND m.verified_at IS NOT NULL AND m.intro_posted_at IS NOT NULL
        """
        params = [CHAT_ID]
        if excluded:
            sql += f" AND m.user_id NOT IN ({placeholders})"
            params.extend(sorted(excluded))
        rows = conn.execute(sql, params).fetchall()
        if not rows:
            return None
        least_selected = min(int(row["selected_count"]) for row in rows)
        eligible = [row for row in rows if int(row["selected_count"]) == least_selected]
        selected = random.choice(eligible)
        return dict(selected)


async def send_member_spotlight(context):
    member = _choose_member()
    if not member:
        logger.info("Member Spotlight skipped: no eligible verified, introduced members.")
        return

    selected_prompt = random.choice(QUESTION_BANK)
    category = selected_prompt["category"]
    prompt = selected_prompt["question"]
    title = f"💭 MEMBER SPOTLIGHT — {category.upper()}"

    name = member.get("first_name") or member.get("username") or "you"
    mention = f'<a href="tg://user?id={int(member["user_id"])}">{_escape(name)}</a>'
    message = (
        f"<b>{title}</b>\n\n"
        f"Hey {mention}! Today's question is for YOU! 👀\n\n"
        f"<b>{prompt}</b>\n\n"
        "Everyone else is welcome to answer the same question, too!\n\n"
        "💬 Let's hear from the whole room!\n\n"
        "<i>Keep it respectful. Respect boundaries. PASS is always an option.</i>"
    )

    try:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=TOPIC_ID,
            text=message,
            parse_mode=ParseMode.HTML,
        )
        with _connect() as conn:
            conn.execute(
                """INSERT INTO member_spotlight_history
                   (chat_id, user_id, selected_count, last_selected_at)
                   VALUES (?, ?, 1, datetime('now'))
                   ON CONFLICT(chat_id, user_id) DO UPDATE SET
                     selected_count=selected_count+1,
                     last_selected_at=datetime('now')""",
                (CHAT_ID, int(member["user_id"])),
            )
            conn.commit()
        logger.info("Member Spotlight posted | chat=%s | user_id=%s", CHAT_ID, member["user_id"])
    except TelegramError:
        logger.exception("Could not post Member Spotlight.")


def _escape(value):
    import html
    return html.escape(str(value), quote=True)


def start_member_spotlight_scheduler(application):
    if not getattr(application, "job_queue", None):
        logger.warning("Member Spotlight scheduler unavailable: JobQueue not installed.")
        return
    for job in application.job_queue.get_jobs_by_name(JOB_NAME):
        job.schedule_removal()
    application.job_queue.run_daily(
        send_member_spotlight,
        time(hour=13, minute=0, tzinfo=ARIZONA_TZ),
        name=JOB_NAME,
    )
    logger.info("Member Spotlight scheduled daily | 13:00 Arizona | chat=%s | topic=%s", CHAT_ID, TOPIC_ID)
