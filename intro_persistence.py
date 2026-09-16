"""Keep member introductions permanent and preserve them across re-joins.

This is loaded by run_bot.py so the validated bot.py does not need to be
rewritten. It also recovers saved real introductions that have text in the
community database but no recorded Telegram message ID.
"""

import logging
import os
import sqlite3

import bot

logger = logging.getLogger("melanated_az_intro_persistence")
COMMUNITY_DB = bot.COMMUNITY_DB
INTRO_TOPIC_ID = int(os.environ.get("INTRO_TOPIC_ID", "11570") or "11570")
MAIN_GROUP_ID = bot.configured_main_group_id()


def _preserve_saved_intro_on_rejoin():
    original = bot.save_joining_member
    if getattr(original, "_intro_persistence_wrapped", False):
        return

    def preserved_save_joining_member(chat_id, user):
        """Start verification again without erasing a member's saved intro."""
        existing = bot.community_member(chat_id, user.id)
        if not existing or not existing["intro_text"]:
            return original(chat_id, user)

        now = bot.iso_now()
        with bot.community_db_connect() as conn:
            conn.execute(
                """UPDATE community_members
                   SET username=?, first_name=?, joined_at=?,
                       verified_at=NULL, intro_deadline=NULL,
                       last_post_at=NULL, verification_attempts=0,
                       verification_message_id=NULL,
                       verification_challenge=NULL,
                       verification_expires_at=NULL,
                       inactivity_notice_at=NULL,
                       inactivity_notice_message_id=NULL,
                       status='pending_verification'
                 WHERE chat_id=? AND user_id=?""",
                (user.username, user.first_name, now, chat_id, user.id),
            )
            conn.commit()
        logger.info("Preserved saved introduction for returning user_id=%s", user.id)

    preserved_save_joining_member._intro_persistence_wrapped = True
    bot.save_joining_member = preserved_save_joining_member


async def recover_saved_introductions(application):
    """Repost only real saved intros that have no recorded Telegram post ID.

    We intentionally do not repost rows that already have intro_message_id,
    because Telegram has no get-message API and reposting those blindly could
    create duplicates when the original post is still live.
    """
    if not MAIN_GROUP_ID or not os.path.exists(COMMUNITY_DB):
        return

    try:
        with bot.community_db_connect() as conn:
            rows = conn.execute(
                """SELECT user_id, username, first_name, intro_text
                     FROM community_members
                    WHERE chat_id=?
                      AND intro_text IS NOT NULL
                      AND TRIM(intro_text) <> ''
                      AND COALESCE(intro_message_id, 0)=0
                      AND COALESCE(intro_source, '') <> 'legacy_backfill'""",
                (MAIN_GROUP_ID,),
            ).fetchall()

        recovered = 0
        for row in rows:
            try:
                user_id = int(row["user_id"])
                intro_text = str(row["intro_text"] or "").strip()
                if not intro_text:
                    continue

                class SavedUser:
                    pass

                user = SavedUser()
                user.first_name = row["first_name"] or row["username"] or "Melanated AZ Member"
                user.full_name = user.first_name

                message = await application.bot.send_message(
                    chat_id=MAIN_GROUP_ID,
                    message_thread_id=INTRO_TOPIC_ID,
                    text=bot.intro_topic_text(user, intro_text, updated=False),
                    parse_mode=bot.ParseMode.HTML,
                )
                bot.save_intro(MAIN_GROUP_ID, user_id, intro_text, message.message_id)
                recovered += 1
                logger.info("Recovered saved introduction | user_id=%s | message_id=%s", user_id, message.message_id)
            except Exception:
                logger.exception("Could not recover saved introduction for user_id=%s", row["user_id"])

        if recovered:
            logger.info("INTRO RECOVERY COMPLETE | recovered=%s | topic=%s", recovered, INTRO_TOPIC_ID)
        else:
            logger.info("Intro recovery: no saved introductions required recovery.")
    except Exception:
        logger.exception("Saved introduction recovery failed.")


def _patch_post_init():
    original = bot.post_init
    if getattr(original, "_intro_persistence_wrapped", False):
        return

    async def wrapped_post_init(application):
        await original(application)
        await recover_saved_introductions(application)

    wrapped_post_init._intro_persistence_wrapped = True
    bot.post_init = wrapped_post_init


_preserve_saved_intro_on_rejoin()
_patch_post_init()
