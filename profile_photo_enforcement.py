# ==========================================================
# Melanated AZ Bot
# profile_photo_enforcement.py
# Profile-photo requirement for onboarding and existing members.
# ==========================================================

import logging
import os
import sqlite3
from datetime import datetime, timezone

from telegram.error import TelegramError

logger = logging.getLogger("melanated_az_profile_photo")

COMMUNITY_DB = "/var/data/community_security.db" if os.path.isdir("/var/data") else "./community_security.db"
PROFILE_PHOTO_REMINDER_SECONDS = int(os.environ.get("PROFILE_PHOTO_REMINDER_SECONDS", "86400") or "86400")


def _db():
    conn = sqlite3.connect(COMMUNITY_DB)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_profile_photo_schema():
    """Additive migration only. Never removes or rewrites existing member data."""
    os.makedirs(os.path.dirname(COMMUNITY_DB) or ".", exist_ok=True)
    with _db() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(community_members)").fetchall()}
        additions = [
            ("profile_photo_file_id", "TEXT"),
            ("profile_photo_checked_at", "TEXT"),
            ("profile_photo_required", "INTEGER DEFAULT 0"),
            ("profile_photo_reminder_at", "TEXT"),
        ]
        for name, definition in additions:
            if name not in columns:
                conn.execute(f"ALTER TABLE community_members ADD COLUMN {name} {definition}")
        conn.commit()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _save_status(chat_id, user_id, has_photo, file_id=None):
    ensure_profile_photo_schema()
    with _db() as conn:
        conn.execute(
            """
            UPDATE community_members
               SET profile_photo_file_id=?,
                   profile_photo_checked_at=?,
                   profile_photo_required=?
             WHERE chat_id=? AND user_id=?
            """,
            (file_id, _now(), 0 if has_photo else 1, int(chat_id), int(user_id)),
        )
        conn.commit()


async def check_profile_photo(bot, user_id):
    """
    Returns:
      True  = Telegram confirmed at least one profile photo.
      False = Telegram confirmed no profile photo.
      None  = Telegram/API error; do not change enforcement state.
    """
    try:
        photos = await bot.get_user_profile_photos(user_id=int(user_id), limit=1)
        if getattr(photos, "total_count", 0) > 0 and getattr(photos, "photos", None):
            sizes = photos.photos[0]
            file_id = sizes[-1].file_id if sizes else None
            return True, file_id
        return False, None
    except TelegramError as exc:
        logger.warning("Profile photo check failed | user_id=%s | error=%s", user_id, exc)
        return None, None
    except Exception:
        logger.exception("Unexpected profile photo check failure | user_id=%s", user_id)
        return None, None


async def refresh_profile_photo(bot, chat_id, user_id):
    result, file_id = await check_profile_photo(bot, user_id)
    if result is None:
        return None
    _save_status(chat_id, user_id, result, file_id)
    return result


def profile_photo_requirement_text():
    return (
        "📸 <b>Melanated AZ Profile Photo Required</b>\n\n"
        "A current Telegram profile photo is part of the Melanated AZ community rules "
        "and member onboarding process.\n\n"
        "Please add a profile photo to your Telegram account. This helps members know "
        "who they are interacting with and keeps our community more accountable.\n\n"
        "✅ Once your photo is added, the bot will automatically recognize your profile "
        "as complete.\n\n"
        "📜 Please also review the pinned community rules."
    )


async def send_profile_photo_requirement(bot, user_id):
    try:
        await bot.send_message(
            chat_id=int(user_id),
            text=profile_photo_requirement_text(),
            parse_mode="HTML",
        )
        return True
    except TelegramError:
        logger.info("Could not send profile-photo requirement privately | user_id=%s", user_id)
        return False


def mark_photo_required(chat_id, user_id):
    ensure_profile_photo_schema()
    with _db() as conn:
        conn.execute(
            "UPDATE community_members SET profile_photo_required=1 WHERE chat_id=? AND user_id=?",
            (int(chat_id), int(user_id)),
        )
        conn.commit()


def clear_photo_required(chat_id, user_id, file_id=None):
    ensure_profile_photo_schema()
    with _db() as conn:
        conn.execute(
            """
            UPDATE community_members
               SET profile_photo_required=0,
                   profile_photo_file_id=COALESCE(?, profile_photo_file_id),
                   profile_photo_checked_at=?
             WHERE chat_id=? AND user_id=?
            """,
            (file_id, _now(), int(chat_id), int(user_id)),
        )
        conn.commit()
