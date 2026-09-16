"""Keep member introductions permanent and restore saved introductions.

Introductions are community content and must remain live in the Introductions
forum topic. This module protects saved intro text from being wiped when a
member rejoins and performs a one-time rebuild of saved introductions whose
Telegram posts may have been removed by the old cleanup behavior.
"""

import logging
import os

import bot

logger = logging.getLogger("melanated_az_intro_persistence")
COMMUNITY_DB = bot.COMMUNITY_DB
INTRO_TOPIC_ID = int(os.environ.get("INTRO_TOPIC_ID", "11570") or "11570")
MAIN_GROUP_ID = bot.configured_main_group_id()
RECOVERY_MARKER = "/var/data/intro_topic_recovery_2026-09-16.done"
LEGACY_MARKER = "Legacy member — intro status backfilled"


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


def _is_real_saved_intro(text):
    text = str(text or "").strip()
    return bool(text) and LEGACY_MARKER not in text


async def recover_saved_introductions(application):
    """One-time rebuild of real saved introductions in the intro topic.

    Older cleanup code could delete introduction posts while leaving their
    text in community_security.db. Telegram does not provide a bot API for
    checking whether an arbitrary old message still exists, so this migration
    intentionally rebuilds every real saved intro once. After that migration,
    new intros are posted normally and are never scheduled for cleanup.
    """
    if not MAIN_GROUP_ID or not os.path.exists(COMMUNITY_DB):
        return

    if os.path.exists(RECOVERY_MARKER):
        return

    try:
        with bot.community_db_connect() as conn:
            rows = conn.execute(
                """SELECT user_id, username, first_name, intro_text
                     FROM community_members
                    WHERE chat_id=?
                      AND intro_text IS NOT NULL
                      AND TRIM(intro_text) <> ''
                    ORDER BY COALESCE(intro_posted_at, joined_at), user_id""",
                (MAIN_GROUP_ID,),
            ).fetchall()

        recovered = 0
        skipped = 0
        for row in rows:
            intro_text = str(row["intro_text"] or "").strip()
            if not _is_real_saved_intro(intro_text):
                skipped += 1
                continue

            try:
                user_id = int(row["user_id"])

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

                # Store the new live Telegram message ID so future recovery
                # runs do not need to recreate this introduction.
                bot.save_intro(MAIN_GROUP_ID, user_id, intro_text, message.message_id)
                recovered += 1
                logger.info(
                    "Restored introduction | user_id=%s | message_id=%s | topic=%s",
                    user_id,
                    message.message_id,
                    INTRO_TOPIC_ID,
                )
            except Exception:
                logger.exception("Could not restore introduction for user_id=%s", row["user_id"])

        # Only create the marker after the complete pass. If Render restarts
        # during recovery, the pass can safely retry rather than losing rows.
        os.makedirs(os.path.dirname(RECOVERY_MARKER) or ".", exist_ok=True)
        with open(RECOVERY_MARKER, "w", encoding="utf-8") as marker:
            marker.write(
                f"Recovered {recovered} introductions; skipped {skipped} legacy placeholders.\n"
            )

        logger.info(
            "INTRO TOPIC RECOVERY COMPLETE | restored=%s | skipped_legacy=%s | topic=%s",
            recovered,
            skipped,
            INTRO_TOPIC_ID,
        )
    except Exception:
        logger.exception("Saved introduction recovery failed; migration marker not created.")


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
