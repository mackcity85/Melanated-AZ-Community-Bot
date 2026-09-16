# ==========================================================
# Melanated AZ Bot - legacy_intro_backfill.py
#
# ONE-TIME GRANDFATHERING OF EXISTING MEMBERS
#
# Marks known existing/current members as having an intro so the
# new mandatory-intro system does not penalize people who joined
# before intro tracking was implemented.
#
# Sources used:
#   - community_security.db / community_members
#   - raffle.db / members
#   - raffle.db / raffle_entries
#   - raffle.db / birthdays
#
# This does NOT post anything to the group and does NOT delete or
# modify existing posts. It only records legacy intro status.
# ==========================================================

import logging
import os
import sqlite3
from datetime import datetime, timezone

from config import MAIN_GROUP_ID, RAFFLE_CHAT_ID

logger = logging.getLogger(__name__)

COMMUNITY_DB = os.environ.get("COMMUNITY_DB", "/var/data/community_security.db").strip()
RAFFLE_DB = os.environ.get("RAFFLE_DB_NAME", "/var/data/raffle.db").strip()
MARKER = os.path.join(
    "/var/data" if os.path.isdir("/var/data") else ".",
    "legacy_intro_backfill_2026-09-16.done",
)
LEGACY_TEXT = (
    "Legacy member — intro status backfilled on 2026-09-16 from existing "
    "community/raffle records. No new public intro post was created."
)


def _db(path):
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _known_people():
    """Return known user records from all available persistent sources."""
    people = {}

    if os.path.exists(COMMUNITY_DB):
        conn = _db(COMMUNITY_DB)
        try:
            rows = conn.execute(
                "SELECT user_id, username, first_name, joined_at, verified_at, status "
                "FROM community_members WHERE chat_id=?",
                (int(MAIN_GROUP_ID),),
            ).fetchall()
            for row in rows:
                people[int(row["user_id"])] = {
                    "user_id": int(row["user_id"]),
                    "username": row["username"],
                    "first_name": row["first_name"],
                    "joined_at": row["joined_at"],
                    "verified_at": row["verified_at"],
                    "source": "community_members",
                }
        finally:
            conn.close()

    if not os.path.exists(RAFFLE_DB):
        return people

    conn = _db(RAFFLE_DB)
    try:
        # Raffle member directory.
        try:
            rows = conn.execute(
                "SELECT user_id, username, display_name, first_seen_at "
                "FROM members WHERE chat_id=?",
                (int(RAFFLE_CHAT_ID or MAIN_GROUP_ID),),
            ).fetchall()
            for row in rows:
                uid = int(row["user_id"])
                current = people.setdefault(uid, {"user_id": uid})
                current.setdefault("username", row["username"])
                current.setdefault("first_name", row["display_name"])
                current.setdefault("joined_at", row["first_seen_at"])
                current["source"] = current.get("source", "") + ",raffle_members"
        except sqlite3.Error:
            logger.exception("Could not read raffle members during legacy intro backfill.")

        # Every raffle entry is also a historical member signal. raffle_entries
        # has no chat_id, so scope through the raffle records themselves.
        try:
            rows = conn.execute(
                "SELECT e.user_id, e.username, e.display_name, e.created_at "
                "FROM raffle_entries e "
                "JOIN raffles r ON r.id=e.raffle_id "
                "WHERE COALESCE(r.chat_id, ?) = ?",
                (int(RAFFLE_CHAT_ID or MAIN_GROUP_ID), int(RAFFLE_CHAT_ID or MAIN_GROUP_ID)),
            ).fetchall()
            for row in rows:
                uid = int(row["user_id"])
                current = people.setdefault(uid, {"user_id": uid})
                if not current.get("username"):
                    current["username"] = row["username"]
                if not current.get("first_name"):
                    current["first_name"] = row["display_name"]
                if not current.get("joined_at"):
                    current["joined_at"] = row["created_at"]
                current["source"] = current.get("source", "") + ",raffle_entries"
        except sqlite3.Error:
            logger.exception("Could not read raffle entries during legacy intro backfill.")

        # Birthday records are another persistent member signal.
        try:
            rows = conn.execute(
                "SELECT user_id, username, display_name, created_at "
                "FROM birthdays WHERE chat_id=?",
                (int(RAFFLE_CHAT_ID or MAIN_GROUP_ID),),
            ).fetchall()
            for row in rows:
                uid = int(row["user_id"])
                current = people.setdefault(uid, {"user_id": uid})
                if not current.get("username"):
                    current["username"] = row["username"]
                if not current.get("first_name"):
                    current["first_name"] = row["display_name"]
                if not current.get("joined_at"):
                    current["joined_at"] = row["created_at"]
                current["source"] = current.get("source", "") + ",birthdays"
        except sqlite3.Error:
            logger.exception("Could not read birthdays during legacy intro backfill.")
    finally:
        conn.close()

    return people


async def run_legacy_intro_backfill(application):
    """One-time async migration using only people we can identify as members."""
    if os.path.exists(MARKER):
        logger.info("Legacy intro backfill already completed | marker=%s", MARKER)
        return

    if not os.path.exists(COMMUNITY_DB):
        logger.warning("Legacy intro backfill skipped: community DB does not exist yet.")
        return

    people = _known_people()
    checked = 0
    current_members = 0
    marked = 0
    inserted = 0
    skipped = 0

    conn = _db(COMMUNITY_DB)
    try:
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(community_members)").fetchall()}
        if "intro_source" not in columns:
            conn.execute("ALTER TABLE community_members ADD COLUMN intro_source TEXT")
        if "intro_backfilled_at" not in columns:
            conn.execute("ALTER TABLE community_members ADD COLUMN intro_backfilled_at TEXT")
        conn.commit()

        for uid, person in people.items():
            checked += 1
            try:
                live = await application.bot.get_chat_member(int(MAIN_GROUP_ID), int(uid))
                status = getattr(live, "status", "")
                if status not in {"member", "administrator", "creator"}:
                    skipped += 1
                    continue
                current_members += 1

                user = getattr(live, "user", None)
                username = getattr(user, "username", None) if user else person.get("username")
                first_name = getattr(user, "first_name", None) if user else person.get("first_name")
                display_name = getattr(user, "full_name", None) if user else person.get("first_name")
                now = datetime.now(timezone.utc).isoformat()

                row = conn.execute(
                    "SELECT * FROM community_members WHERE chat_id=? AND user_id=?",
                    (int(MAIN_GROUP_ID), int(uid)),
                ).fetchone()

                if row:
                    # Preserve verification, dates, status, and any real intro.
                    # Only fill an empty intro field for legacy members.
                    if row["intro_text"]:
                        continue
                    conn.execute(
                        "UPDATE community_members SET username=?, first_name=?, "
                        "intro_text=?, intro_posted_at=COALESCE(intro_posted_at,?), "
                        "intro_source='legacy_backfill', intro_backfilled_at=? "
                        "WHERE chat_id=? AND user_id=?",
                        (
                            username,
                            first_name,
                            LEGACY_TEXT,
                            now,
                            now,
                            int(MAIN_GROUP_ID),
                            int(uid),
                        ),
                    )
                    marked += 1
                else:
                    # Historical member found in raffle/birthday records but not
                    # previously tracked by community security. Grandfather them
                    # as an existing verified/active member and record the source.
                    conn.execute(
                        "INSERT INTO community_members "
                        "(chat_id,user_id,username,first_name,joined_at,verified_at,"
                        "intro_posted_at,intro_text,last_post_at,status,intro_source,intro_backfilled_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,'active','legacy_backfill',?)",
                        (
                            int(MAIN_GROUP_ID),
                            int(uid),
                            username,
                            first_name,
                            person.get("joined_at") or now,
                            person.get("verified_at") or now,
                            now,
                            LEGACY_TEXT,
                            now,
                            now,
                        ),
                    )
                    inserted += 1
            except Exception as exc:
                skipped += 1
                logger.info("Legacy intro backfill could not verify user_id=%s | %s", uid, exc.__class__.__name__)

        conn.commit()
    finally:
        conn.close()

    os.makedirs(os.path.dirname(MARKER) or ".", exist_ok=True)
    with open(MARKER, "w", encoding="utf-8") as fh:
        fh.write(
            "Legacy intro backfill completed 2026-09-16\n"
            f"Known records checked: {checked}\n"
            f"Current Telegram members confirmed: {current_members}\n"
            f"Existing records marked with legacy intro: {marked}\n"
            f"Historical records inserted and marked: {inserted}\n"
            f"Skipped/unavailable/not-current: {skipped}\n"
        )

    logger.info(
        "LEGACY INTRO BACKFILL COMPLETE | checked=%s | current_members=%s | marked=%s | inserted=%s | skipped=%s",
        checked,
        current_members,
        marked,
        inserted,
        skipped,
    )
