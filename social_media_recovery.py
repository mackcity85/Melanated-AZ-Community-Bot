# ==========================================================
# Melanated AZ Bot - Social Media Recovery
# Topic: -1002697105809_9513
#
# Purpose:
#   Recover saved social-media profiles if their Telegram topic
#   messages were deleted. Saved links remain in SQLite, so this
#   module republishes them into the Friends topic.
# ==========================================================

import logging
import os
import sqlite3

CHAT_ID = -1002697105809
TOPIC_ID = 9513
DB_PATH = os.environ.get("SOCIAL_MEDIA_DB", "/var/data/social_media.db").strip()

logger = logging.getLogger("melanated_az_social_recovery")



def _connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn



def _saved_user_ids():
    if not os.path.exists(DB_PATH):
        return []
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT user_id FROM social_links ORDER BY user_id"
            ).fetchall()
        return [int(row["user_id"]) for row in rows]
    except Exception:
        logger.exception("Unable to read saved social links for recovery")
        return []


async def recover_social_profiles(bot):
    """Recreate missing social profiles from the persistent SQLite bank."""
    try:
        from social_media import initialize_social_media_database, _publish_member_profile

        initialize_social_media_database()
        user_ids = _saved_user_ids()
        if not user_ids:
            logger.info("Social media recovery: no saved profiles found.")
            return 0

        recovered = 0
        for user_id in user_ids:
            try:
                before = None
                with _connect() as conn:
                    row = conn.execute(
                        "SELECT topic_message_id FROM social_links WHERE user_id=? LIMIT 1",
                        (user_id,),
                    ).fetchone()
                    before = row["topic_message_id"] if row else None

                await _publish_member_profile(bot, user_id)

                with _connect() as conn:
                    row = conn.execute(
                        "SELECT topic_message_id FROM social_links WHERE user_id=? LIMIT 1",
                        (user_id,),
                    ).fetchone()
                    after = row["topic_message_id"] if row else None

                if after and str(after) != str(before):
                    recovered += 1
                    logger.info(
                        "Recovered social profile | user_id=%s | old_message=%s | new_message=%s | chat=%s topic=%s",
                        user_id,
                        before,
                        after,
                        CHAT_ID,
                        TOPIC_ID,
                    )
            except Exception:
                logger.exception("Social profile recovery failed | user_id=%s", user_id)

        logger.info(
            "Social media recovery COMPLETE | saved_profiles=%s | recovered_or_recreated=%s | chat=%s topic=%s",
            len(user_ids),
            recovered,
            CHAT_ID,
            TOPIC_ID,
        )
        return recovered
    except Exception:
        logger.exception("Social media recovery module failed")
        return 0


async def scheduled_social_recovery(context):
    await recover_social_profiles(context.bot)
