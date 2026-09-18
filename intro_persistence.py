"""Keep saved member introductions visible in the Introductions topic.

This module never deletes introductions. It preserves saved intro text when a
member rejoins and performs a versioned recovery pass for saved introductions
whose old Telegram posts are missing.
"""

import logging
import os

import bot

logger = logging.getLogger("melanated_az_intro_persistence")
COMMUNITY_DB = bot.COMMUNITY_DB
INTRO_TOPIC_ID = int(os.environ.get("INTRO_TOPIC_ID", "11570") or "11570")
LEGACY_MARKER = "Legacy member — intro status backfilled"

# New recovery version. This deliberately ignores older recovery markers so
# Render performs a fresh recovery pass after this fix is deployed.
RECOVERY_MARKER = "/var/data/intro_topic_recovery_2026-09-16-v3.done"


def _main_group_id():
    return bot.configured_main_group_id()


def _preserve_saved_intro_on_rejoin():
    original = bot.save_joining_member
    if getattr(original, "_intro_persistence_wrapped", False):
        return

    def preserved_save_joining_member(chat_id, user):
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
    """Repost every real saved introduction into topic 11570 once for v3.

    Telegram's Bot API cannot retrieve arbitrary historical/deleted messages.
    Therefore recovery is based on intro_text still stored in the community DB.
    """
    main = _main_group_id()
    if not main:
        logger.error("INTRO RECOVERY SKIPPED: MAIN_GROUP_ID is not configured.")
        return
    if not os.path.exists(COMMUNITY_DB):
        logger.error("INTRO RECOVERY SKIPPED: community database does not exist: %s", COMMUNITY_DB)
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
                (main,),
            ).fetchall()

        logger.info(
            "INTRO RECOVERY v3 START | saved_rows=%s | main=%s | topic=%s",
            len(rows), main, INTRO_TOPIC_ID,
        )

        recovered = 0
        skipped = 0
        failed = 0

        for row in rows:
            intro_text = str(row["intro_text"] or "").strip()
            if not _is_real_saved_intro(intro_text):
                skipped += 1
                continue

            try:
                class SavedUser:
                    pass

                user = SavedUser()
                user.first_name = row["first_name"] or row["username"] or "Melanated AZ Member"
                user.full_name = user.first_name

                message = await application.bot.send_message(
                    chat_id=main,
                    message_thread_id=INTRO_TOPIC_ID,
                    text=bot.intro_topic_text(user, intro_text, updated=False),
                    parse_mode=bot.ParseMode.HTML,
                )

                # Keep the latest live topic message ID with the saved intro.
                bot.save_intro(main, int(row["user_id"]), intro_text, message.message_id)
                recovered += 1
                logger.info(
                    "INTRO RECOVERED | user_id=%s | message_id=%s | topic=%s",
                    row["user_id"], message.message_id, INTRO_TOPIC_ID,
                )
            except Exception:
                failed += 1
                logger.exception("INTRO RECOVERY FAILED | user_id=%s", row["user_id"])

        # If any row failed, don't create the marker. A restart will retry it.
        if failed:
            logger.error(
                "INTRO RECOVERY v3 INCOMPLETE | recovered=%s | failed=%s | skipped=%s",
                recovered, failed, skipped,
            )
            return

        os.makedirs(os.path.dirname(RECOVERY_MARKER) or ".", exist_ok=True)
        with open(RECOVERY_MARKER, "w", encoding="utf-8") as marker:
            marker.write(
                f"Recovered {recovered} introductions; skipped {skipped} legacy placeholders.\n"
            )

        logger.info(
            "INTRO RECOVERY v3 COMPLETE | recovered=%s | skipped=%s | topic=%s",
            recovered, skipped, INTRO_TOPIC_ID,
        )
    except Exception:
        logger.exception("INTRO RECOVERY v3 failed; marker was not created.")
