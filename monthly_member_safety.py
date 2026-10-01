# ==========================================================
# Melanated AZ Bot
# monthly_member_safety.py
# Independent monthly member safety check-in and audit.
# ==========================================================

import logging
import os
import sqlite3
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from config import ADMIN_IDS

logger = logging.getLogger("melanated_az_monthly_safety")

COMMUNITY_DB = "/var/data/community_security.db" if os.path.isdir("/var/data") else "./community_security.db"
MONTHLY_SAFETY_JOB_NAME = "monthly-member-safety-check"
MONTHLY_SAFETY_STARTUP_JOB_NAME = "monthly-member-safety-startup"

def _db():
    conn = sqlite3.connect(COMMUNITY_DB)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_monthly_safety_schema():
    os.makedirs(os.path.dirname(COMMUNITY_DB) or ".", exist_ok=True)
    with _db() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(community_members)").fetchall()}
        additions = [
            ("monthly_safety_sent_at", "TEXT"),
            ("monthly_safety_confirmed_at", "TEXT"),
        ]
        for name, definition in additions:
            if name not in columns:
                conn.execute(f"ALTER TABLE community_members ADD COLUMN {name} {definition}")
        conn.commit()

def _now():
    return datetime.now(timezone.utc).isoformat()

def _main_group_id():
    try:
        return int(os.environ.get("MAIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        return 0

def _eligible_rows(main):
    with _db() as conn:
        return conn.execute(
            """SELECT user_id, username, first_name, status, monthly_safety_sent_at
               FROM community_members
               WHERE chat_id=?
                 AND status NOT IN ('left','removed','removed_by_admin')
               ORDER BY user_id""",
            (main,),
        ).fetchall()

def _already_sent_this_month(value, now):
    if not value:
        return False
    try:
        sent = datetime.fromisoformat(value)
        return sent.year == now.year and sent.month == now.month
    except Exception:
        return False

def safety_check_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛡️ I'M SAFE & STILL HERE", callback_data="monthly_safety:confirm")],
        [InlineKeyboardButton("📜 REVIEW COMMUNITY RULES", callback_data="monthly_safety:rules")],
    ])

def monthly_safety_message():
    return (
        "🛡️ <b>Melanated AZ Monthly Safety Check-In</b>\n\n"
        "We're doing our monthly community safety check to help keep Melanated AZ safe, "
        "active, and accountable.\n\n"
        "Please confirm that you're still an active member and take a moment to review "
        "the community rules.\n\n"
        "📸 Make sure your Telegram profile photo is current.\n"
        "🔒 Protect your privacy and personal information.\n"
        "🤝 Respect consent and boundaries.\n"
        "🚩 Report suspicious, threatening, or inappropriate behavior to an admin.\n\n"
        "<b>This check-in does not replace the community rules or the profile-photo requirement.</b>"
    )

async def send_monthly_safety_check(bot, user_id):
    try:
        await bot.send_message(
            chat_id=int(user_id),
            text=monthly_safety_message(),
            reply_markup=safety_check_keyboard(),
            parse_mode="HTML",
        )
        return True
    except TelegramError:
        logger.info("Monthly safety check could not be sent privately | user_id=%s", user_id)
        return False

async def monthly_safety_check(context):
    """Independent monthly audit/check-in. It never removes members by itself."""
    ensure_monthly_safety_schema()
    main = _main_group_id()
    if not main:
        logger.warning("MONTHLY SAFETY CHECK SKIPPED | MAIN_GROUP_ID is not configured")
        return

    now = datetime.now(timezone.utc)
    rows = _eligible_rows(main)
    sent = 0
    skipped = 0
    inactive_or_missing = 0
    errors = 0

    for row in rows:
        user_id = int(row["user_id"])
        if user_id in {int(x) for x in ADMIN_IDS}:
            skipped += 1
            continue

        try:
            member = await context.bot.get_chat_member(main, user_id)
            status = getattr(member, "status", "")
            if status in {"left", "kicked"}:
                inactive_or_missing += 1
                continue
            if status in {"administrator", "creator"}:
                skipped += 1
                continue

            if _already_sent_this_month(row["monthly_safety_sent_at"], now):
                continue

            if await send_monthly_safety_check(context.bot, user_id):
                with _db() as conn:
                    conn.execute(
                        "UPDATE community_members SET monthly_safety_sent_at=? WHERE chat_id=? AND user_id=?",
                        (now.isoformat(), main, user_id),
                    )
                    conn.commit()
                sent += 1
        except TelegramError:
            errors += 1
        except Exception:
            errors += 1
            logger.exception("MONTHLY SAFETY CHECK FAILED | user_id=%s", user_id)

    logger.info(
        "MONTHLY SAFETY CHECK COMPLETE | members=%s | sent=%s | skipped=%s | inactive_or_missing=%s | errors=%s",
        len(rows), sent, skipped, inactive_or_missing, errors,
    )

async def monthly_safety_callback(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user or not query.data:
        return

    main = _main_group_id()
    if not main:
        await query.answer("Safety check is temporarily unavailable.", show_alert=True)
        return

    prefix, action = query.data.split(":", 1)
    if prefix != "monthly_safety":
        return

    if action == "confirm":
        now = _now()
        with _db() as conn:
            conn.execute(
                "UPDATE community_members SET monthly_safety_confirmed_at=? WHERE chat_id=? AND user_id=?",
                (now, main, user.id),
            )
            conn.commit()
        await query.answer("Thanks — your monthly safety check is confirmed. 🛡️")
        try:
            await query.edit_message_text(
                "🛡️ <b>Monthly safety check complete.</b>\n\n"
                "Thanks for checking in with Melanated AZ. 💜\n\n"
                "Please keep your profile photo current and report any safety concerns to an admin.",
                parse_mode="HTML",
            )
        except TelegramError:
            pass
    elif action == "rules":
        await query.answer()
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text="📜 <b>Review the Melanated AZ community rules.</b>\n\nUse /rules in the community to view the current rules.",
                parse_mode="HTML",
            )
        except TelegramError:
            pass

def register_monthly_safety(application):
    ensure_monthly_safety_schema()
    if not application.job_queue:
        logger.warning("MONTHLY SAFETY CHECK NOT REGISTERED | JobQueue unavailable")
        return

    for name in (MONTHLY_SAFETY_JOB_NAME, MONTHLY_SAFETY_STARTUP_JOB_NAME):
        for job in application.job_queue.get_jobs_by_name(name):
            job.schedule_removal()

    # A startup run only fills a missed monthly check; the function itself is
    # idempotent for the current month, so restarts cannot spam members.
    application.job_queue.run_once(
        monthly_safety_check,
        when=20,
        name=MONTHLY_SAFETY_STARTUP_JOB_NAME,
    )

    # Check daily whether a new month has started. The database timestamp
    # prevents duplicate monthly messages.
    application.job_queue.run_repeating(
        monthly_safety_check,
        interval=86400,
        first=86400,
        name=MONTHLY_SAFETY_JOB_NAME,
    )
    logger.info("Monthly member safety check ENABLED | daily scheduler | one check-in per member per month")
