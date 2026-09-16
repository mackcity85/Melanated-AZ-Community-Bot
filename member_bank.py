# ==========================================================
# Melanated AZ Bot - member_bank.py
# ADMIN MEMBER BANK + ONE-TIME LEGACY INTRO BACKFILL
# ==========================================================

import logging
import os
import sqlite3
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import MAIN_GROUP_ID, RAFFLE_CHAT_ID

logger = logging.getLogger(__name__)

COMMUNITY_DB = os.environ.get("COMMUNITY_DB", "/var/data/community_security.db").strip()
RAFFLE_DB = os.environ.get("RAFFLE_DB_NAME", "/var/data/raffle.db").strip()
PAGE_SIZE = 8
BACKFILL_MARKER = os.path.join(
    "/var/data" if os.path.isdir("/var/data") else ".",
    "legacy_intro_backfill_2026-09-16.done",
)
LEGACY_INTRO_TEXT = (
    "Legacy member — intro status backfilled on 2026-09-16 from existing "
    "community/raffle records. No new public intro post was created."
)


def _db(path):
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _community_rows():
    if not os.path.exists(COMMUNITY_DB):
        return []
    conn = _db(COMMUNITY_DB)
    try:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM community_members WHERE chat_id=? "
            "ORDER BY COALESCE(first_name,''), user_id",
            (int(MAIN_GROUP_ID),),
        ).fetchall()]
    finally:
        conn.close()


def _birthday_map():
    if not os.path.exists(RAFFLE_DB):
        return {}
    conn = _db(RAFFLE_DB)
    try:
        rows = conn.execute(
            "SELECT user_id, birthday, username, display_name FROM birthdays WHERE chat_id=?",
            (int(RAFFLE_CHAT_ID or MAIN_GROUP_ID),),
        ).fetchall()
        return {int(r["user_id"]): dict(r) for r in rows}
    except Exception:
        logger.exception("Unable to load birthday map for member bank.")
        return {}
    finally:
        conn.close()


def _legacy_people():
    """Collect every identifiable person from the community and raffle databases."""
    people = {}

    if os.path.exists(COMMUNITY_DB):
        conn = _db(COMMUNITY_DB)
        try:
            rows = conn.execute(
                "SELECT user_id, username, first_name, joined_at, verified_at "
                "FROM community_members WHERE chat_id=?",
                (int(MAIN_GROUP_ID),),
            ).fetchall()
            for r in rows:
                uid = int(r["user_id"])
                people[uid] = {
                    "user_id": uid,
                    "username": r["username"],
                    "first_name": r["first_name"],
                    "joined_at": r["joined_at"],
                    "verified_at": r["verified_at"],
                    "source": "community_members",
                }
        finally:
            conn.close()

    if not os.path.exists(RAFFLE_DB):
        return people

    conn = _db(RAFFLE_DB)
    try:
        chat_id = int(RAFFLE_CHAT_ID or MAIN_GROUP_ID)

        try:
            rows = conn.execute(
                "SELECT user_id, username, display_name, first_seen_at "
                "FROM members WHERE chat_id=?",
                (chat_id,),
            ).fetchall()
            for r in rows:
                uid = int(r["user_id"])
                p = people.setdefault(uid, {"user_id": uid})
                p["username"] = p.get("username") or r["username"]
                p["first_name"] = p.get("first_name") or r["display_name"]
                p["joined_at"] = p.get("joined_at") or r["first_seen_at"]
                p["source"] = (p.get("source") or "") + ",raffle_members"
        except sqlite3.Error:
            logger.exception("Unable to read raffle members for legacy intro backfill.")

        try:
            rows = conn.execute(
                "SELECT e.user_id, e.username, e.display_name, e.created_at "
                "FROM raffle_entries e JOIN raffles r ON r.id=e.raffle_id "
                "WHERE COALESCE(r.chat_id, ?) = ?",
                (chat_id, chat_id),
            ).fetchall()
            for r in rows:
                uid = int(r["user_id"])
                p = people.setdefault(uid, {"user_id": uid})
                p["username"] = p.get("username") or r["username"]
                p["first_name"] = p.get("first_name") or r["display_name"]
                p["joined_at"] = p.get("joined_at") or r["created_at"]
                p["source"] = (p.get("source") or "") + ",raffle_entries"
        except sqlite3.Error:
            logger.exception("Unable to read raffle entries for legacy intro backfill.")

        try:
            rows = conn.execute(
                "SELECT user_id, username, display_name, created_at FROM birthdays WHERE chat_id=?",
                (chat_id,),
            ).fetchall()
            for r in rows:
                uid = int(r["user_id"])
                p = people.setdefault(uid, {"user_id": uid})
                p["username"] = p.get("username") or r["username"]
                p["first_name"] = p.get("first_name") or r["display_name"]
                p["joined_at"] = p.get("joined_at") or r["created_at"]
                p["source"] = (p.get("source") or "") + ",birthdays"
        except sqlite3.Error:
            logger.exception("Unable to read birthdays for legacy intro backfill.")
    finally:
        conn.close()

    return people


def run_legacy_intro_backfill():
    """One-time database migration for people already known before intro tracking."""
    if os.path.exists(BACKFILL_MARKER):
        return
    if not os.path.exists(COMMUNITY_DB):
        logger.info("Legacy intro backfill skipped: community database not found yet.")
        return

    people = _legacy_people()
    now = datetime.now(timezone.utc).isoformat()
    marked = 0
    inserted = 0

    conn = _db(COMMUNITY_DB)
    try:
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(community_members)").fetchall()}
        if "intro_source" not in columns:
            conn.execute("ALTER TABLE community_members ADD COLUMN intro_source TEXT")
        if "intro_backfilled_at" not in columns:
            conn.execute("ALTER TABLE community_members ADD COLUMN intro_backfilled_at TEXT")

        for uid, person in people.items():
            row = conn.execute(
                "SELECT * FROM community_members WHERE chat_id=? AND user_id=?",
                (int(MAIN_GROUP_ID), uid),
            ).fetchone()

            if row:
                # Never overwrite a real introduction or verification state.
                if row["intro_text"]:
                    continue
                conn.execute(
                    "UPDATE community_members SET username=?, first_name=?, "
                    "intro_text=?, intro_posted_at=COALESCE(intro_posted_at,?), "
                    "intro_source='legacy_backfill', intro_backfilled_at=? "
                    "WHERE chat_id=? AND user_id=?",
                    (
                        person.get("username"),
                        person.get("first_name"),
                        LEGACY_INTRO_TEXT,
                        now,
                        now,
                        int(MAIN_GROUP_ID),
                        uid,
                    ),
                )
                marked += 1
                continue

            # Raffle/birthday history can identify members that predate the
            # community security database. Preserve the historical first-seen
            # date when available and grandfather them into the active member bank.
            conn.execute(
                "INSERT INTO community_members "
                "(chat_id,user_id,username,first_name,joined_at,verified_at,"
                "intro_posted_at,intro_text,last_post_at,status,intro_source,intro_backfilled_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,'active','legacy_backfill',?)",
                (
                    int(MAIN_GROUP_ID),
                    uid,
                    person.get("username"),
                    person.get("first_name"),
                    person.get("joined_at") or now,
                    person.get("verified_at") or now,
                    now,
                    LEGACY_INTRO_TEXT,
                    now,
                    now,
                ),
            )
            inserted += 1

        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Legacy intro backfill failed.")
        return
    finally:
        conn.close()

    with open(BACKFILL_MARKER, "w", encoding="utf-8") as fh:
        fh.write(
            "Legacy intro backfill completed 2026-09-16\n"
            f"Known people examined: {len(people)}\n"
            f"Existing records marked: {marked}\n"
            f"Historical records added: {inserted}\n"
        )
    logger.info(
        "LEGACY INTRO BACKFILL COMPLETE | known=%s | marked=%s | inserted=%s",
        len(people), marked, inserted,
    )


def _display_name(row, live=None):
    if live is not None:
        user = getattr(live, "user", None)
        if user:
            return getattr(user, "full_name", None) or (
                f"@{user.username}" if getattr(user, "username", None) else None
            ) or str(row.get("user_id"))
    return row.get("display_name") or row.get("first_name") or (
        f"@{row.get('username')}" if row.get("username") else None
    ) or str(row.get("user_id"))


def _intro_status(row):
    if row.get("intro_text"):
        return "✅ Complete"
    if row.get("verified_at"):
        return "📝 Required"
    return "🔐 Verify first"


def _verification_status(row):
    return "✅ Verified" if row.get("verified_at") else "⏳ Pending"


async def _refresh_live_member(context, row):
    try:
        live = await context.bot.get_chat_member(int(MAIN_GROUP_ID), int(row["user_id"]))
    except Exception as exc:
        return None, f"Unknown ({exc.__class__.__name__})"

    status = getattr(live, "status", "unknown")
    row["live_status"] = status
    user = getattr(live, "user", None)
    if user:
        row["username"] = getattr(user, "username", None)
        row["first_name"] = getattr(user, "first_name", None)
        row["display_name"] = getattr(user, "full_name", None)
        try:
            conn = _db(COMMUNITY_DB)
            columns = {r["name"] for r in conn.execute("PRAGMA table_info(community_members)").fetchall()}
            updates, values = [], []
            for col, value in (("username", row.get("username")), ("first_name", row.get("first_name")), ("display_name", row.get("display_name"))):
                if col in columns:
                    updates.append(f"{col}=?")
                    values.append(value)
            if updates:
                values.extend([int(MAIN_GROUP_ID), int(row["user_id"])])
                conn.execute(
                    f"UPDATE community_members SET {', '.join(updates)} WHERE chat_id=? AND user_id=?",
                    values,
                )
                conn.commit()
            conn.close()
        except Exception:
            logger.exception("Unable to refresh member identity | user_id=%s", row.get("user_id"))
    return live, status


def _page_keyboard(rows, page, total_pages):
    buttons = []
    for row in rows:
        uid = int(row["user_id"])
        verified = "✓" if row.get("verified_at") else "!"
        intro = "📝" if row.get("intro_text") else "⚠️"
        buttons.append([InlineKeyboardButton(
            f"{verified}{intro} {_display_name(row)}",
            callback_data=f"admin_member_view_{uid}",
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_members_page_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"admin_members_page_{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔄 Refresh Members", callback_data="admin_members")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_back")])
    return InlineKeyboardMarkup(buttons)


def _summary(rows):
    verified = sum(1 for r in rows if r.get("verified_at"))
    intros = sum(1 for r in rows if r.get("intro_text"))
    pending = sum(1 for r in rows if r.get("verified_at") and not r.get("intro_text"))
    birthdays = len(_birthday_map())
    legacy = sum(1 for r in rows if r.get("intro_source") == "legacy_backfill")
    return verified, intros, pending, birthdays, legacy


async def admin_members(update, context, page=0):
    query = update.callback_query
    if not query:
        return
    rows = _community_rows()
    if not rows:
        await query.edit_message_text(
            "👥 **MEMBER BANK**\n\nNo community member records are currently stored.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]),
            parse_mode="Markdown",
        )
        return

    for row in rows:
        live, status = await _refresh_live_member(context, row)
        row["live_status"] = status
        if live is not None and getattr(live, "user", None):
            row["display_name"] = getattr(live.user, "full_name", None) or row.get("display_name")

    total = len(rows)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(int(page), total_pages - 1))
    current = rows[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    verified, intros, pending, birthdays, legacy = _summary(rows)

    text = (
        "👥 **MEMBER BANK**\n\n"
        f"👥 Total records: **{total}**\n"
        f"✅ Verified: **{verified}**\n"
        f"📝 Intros completed: **{intros}**\n"
        f"🕘 Legacy intros: **{legacy}**\n"
        f"⚠️ Intro still required: **{pending}**\n"
        f"🎂 Birthdays saved: **{birthdays}**\n\n"
        f"Page **{page + 1}** of **{total_pages}**\n\n"
        "✓ = verified   📝 = intro recorded   ⚠️ = intro required\n"
        "Select a member for the current profile."
    )
    await query.edit_message_text(text, reply_markup=_page_keyboard(current, page, total_pages), parse_mode="Markdown")


async def admin_member_view(update, context, user_id):
    query = update.callback_query
    if not query:
        return
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        await query.answer("Invalid member.", show_alert=True)
        return

    rows = _community_rows()
    row = next((r for r in rows if int(r["user_id"]) == user_id), None)
    if not row:
        await query.answer("Member not found.", show_alert=True)
        return

    live, status = await _refresh_live_member(context, row)
    birthday = _birthday_map().get(user_id, {})
    name = _display_name(row, live)
    username = row.get("username")
    username = f"@{username.lstrip('@')}" if username else "Not set"
    live_label = {
        "member": "🟢 Member",
        "administrator": "👑 Administrator",
        "creator": "👑 Creator",
        "restricted": "🟡 Restricted",
        "left": "🔴 Left",
        "kicked": "⛔ Kicked",
    }.get(status, f"❔ {status}")
    intro = row.get("intro_text") or "⚠️ No introduction has been saved yet."
    if len(intro) > 1200:
        intro = intro[:1200] + "…"

    text = (
        "👤 **MEMBER PROFILE**\n\n"
        f"**Name:** {name}\n"
        f"**Username:** {username}\n"
        f"**User ID:** `{user_id}`\n"
        f"**Telegram Status:** {live_label}\n"
        f"**Verification:** {_verification_status(row)}\n"
        f"**Intro:** {_intro_status(row)}\n"
        f"**Intro Source:** {row.get('intro_source') or 'member submission'}\n"
        f"**Joined:** {row.get('joined_at') or 'Unknown'}\n"
        f"**Intro Deadline:** {row.get('intro_deadline') or 'N/A'}\n"
        f"**Birthday:** {birthday.get('birthday') or 'Not added'}\n\n"
        "**Saved Introduction**\n"
        f"{intro}"
    )
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Members", callback_data="admin_members")],
            [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
        ]),
        parse_mode="Markdown",
    )


# Run automatically when the member-bank module is imported by admin.py.
# This is database-only and does not post/delete/move anything in Telegram.
try:
    run_legacy_intro_backfill()
except Exception:
    logger.exception("Unable to run legacy intro backfill at import time.")
