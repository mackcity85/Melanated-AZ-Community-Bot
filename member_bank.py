# ==========================================================
# Melanated AZ Bot - member_bank.py
#
# ADMIN MEMBER BANK
#
# Shows current community member information, including:
#   - live Telegram membership status
#   - verification status
#   - mandatory intro status / saved intro
#   - intro deadline
#   - optional birthday
#   - username / display name
#
# Uses the existing community_security.db and raffle.db.
# Never deletes or resets member data.
# ==========================================================

import logging
import os
import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import MAIN_GROUP_ID, RAFFLE_CHAT_ID

logger = logging.getLogger(__name__)

COMMUNITY_DB = os.environ.get(
    "COMMUNITY_DB",
    "/var/data/community_security.db",
).strip()

PAGE_SIZE = 8


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
            "SELECT * FROM community_members "
            "WHERE chat_id=? "
            "ORDER BY COALESCE(first_name,''), user_id",
            (int(MAIN_GROUP_ID),),
        ).fetchall()]
    finally:
        conn.close()


def _birthday_map():
    path = os.environ.get("RAFFLE_DB_NAME", "/var/data/raffle.db").strip()
    if not os.path.exists(path):
        return {}
    conn = _db(path)
    try:
        rows = conn.execute(
            "SELECT user_id, birthday, username, display_name "
            "FROM birthdays WHERE chat_id=?",
            (int(RAFFLE_CHAT_ID or MAIN_GROUP_ID),),
        ).fetchall()
        return {int(r["user_id"]): dict(r) for r in rows}
    except Exception:
        logger.exception("Unable to load birthday map for member bank.")
        return {}
    finally:
        conn.close()


def _display_name(row, live=None):
    if live:
        user = getattr(live, "user", None)
        if user:
            name = getattr(user, "full_name", None)
            if name:
                return name
            if getattr(user, "username", None):
                return f"@{user.username}"
    return (
        row.get("display_name")
        or row.get("first_name")
        or (f"@{row.get('username')}" if row.get("username") else None)
        or str(row.get("user_id"))
    )


def _intro_status(row):
    if row.get("intro_text"):
        return "✅ Complete"
    if row.get("verified_at"):
        return "📝 Required"
    return "🔐 Verify first"


def _verification_status(row):
    return "✅ Verified" if row.get("verified_at") else "⏳ Pending"


async def _refresh_live_member(context, row):
    """Read current Telegram membership and refresh stored identity fields when possible."""
    try:
        live = await context.bot.get_chat_member(
            chat_id=int(MAIN_GROUP_ID),
            user_id=int(row["user_id"]),
        )
    except Exception as exc:
        return None, f"Unknown ({exc.__class__.__name__})"

    status = getattr(live, "status", "unknown")
    row["live_status"] = status

    user = getattr(live, "user", None)
    if user:
        row["username"] = getattr(user, "username", None)
        row["first_name"] = getattr(user, "first_name", None)
        row["display_name"] = getattr(user, "full_name", None)

        # Keep the existing community member record current without
        # changing verification or intro state.
        try:
            conn = _db(COMMUNITY_DB)
            columns = {
                r["name"] for r in conn.execute(
                    "PRAGMA table_info(community_members)"
                ).fetchall()
            }
            updates = []
            values = []
            if "username" in columns:
                updates.append("username=?")
                values.append(row.get("username"))
            if "first_name" in columns:
                updates.append("first_name=?")
                values.append(row.get("first_name"))
            if "display_name" in columns:
                updates.append("display_name=?")
                values.append(row.get("display_name"))
            if updates:
                values.extend([int(MAIN_GROUP_ID), int(row["user_id"])])
                conn.execute(
                    f"UPDATE community_members SET {', '.join(updates)} "
                    "WHERE chat_id=? AND user_id=?",
                    values,
                )
                conn.commit()
            conn.close()
        except Exception:
            logger.exception(
                "Unable to refresh stored identity | user_id=%s",
                row.get("user_id"),
            )

    return live, status


def _page_keyboard(rows, page, total_pages):
    buttons = []
    for row in rows:
        user_id = int(row["user_id"])
        name = _display_name(row)
        verified = "✓" if row.get("verified_at") else "!"
        intro = "📝" if row.get("intro_text") else "⚠️"
        buttons.append([
            InlineKeyboardButton(
                f"{verified}{intro} {name}",
                callback_data=f"admin_member_view_{user_id}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            "⬅️ Previous",
            callback_data=f"admin_members_page_{page - 1}",
        ))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            "Next ➡️",
            callback_data=f"admin_members_page_{page + 1}",
        ))
    if nav:
        buttons.append(nav)
    buttons.append([
        InlineKeyboardButton("🔄 Refresh Members", callback_data="admin_members")
    ])
    buttons.append([
        InlineKeyboardButton("⬅️ Back", callback_data="admin_back")
    ])
    return InlineKeyboardMarkup(buttons)


def _summary(rows):
    verified = sum(1 for r in rows if r.get("verified_at"))
    intros = sum(1 for r in rows if r.get("intro_text"))
    pending_intro = sum(1 for r in rows if r.get("verified_at") and not r.get("intro_text"))
    birthdays = len(_birthday_map())
    return verified, intros, pending_intro, birthdays


async def admin_members(update, context, page=0):
    query = update.callback_query
    if not query:
        return

    rows = _community_rows()
    if not rows:
        await query.edit_message_text(
            "👥 **MEMBER BANK**\n\n"
            "No community member records are currently stored.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
            ]),
            parse_mode="Markdown",
        )
        return

    # Refresh every stored member against Telegram so the bank reflects
    # current identity and current membership status whenever opened.
    for row in rows:
        live, status = await _refresh_live_member(context, row)
        row["live_status"] = status
        if live is not None and getattr(live, "user", None):
            row["display_name"] = getattr(live.user, "full_name", None) or row.get("display_name")

    total = len(rows)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(int(page), total_pages - 1))
    start = page * PAGE_SIZE
    current = rows[start:start + PAGE_SIZE]

    verified, intros, pending_intro, birthdays = _summary(rows)

    text = (
        "👥 **MEMBER BANK**\n\n"
        f"👥 Total records: **{total}**\n"
        f"✅ Verified: **{verified}**\n"
        f"📝 Intros completed: **{intros}**\n"
        f"⚠️ Intro still required: **{pending_intro}**\n"
        f"🎂 Birthdays saved: **{birthdays}**\n\n"
        f"Page **{page + 1}** of **{total_pages}**\n\n"
        "✓ = verified   📝 = intro saved   ⚠️ = intro required\n"
        "Select a member for the complete current profile."
    )

    await query.edit_message_text(
        text,
        reply_markup=_page_keyboard(current, page, total_pages),
        parse_mode="Markdown",
    )


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
    birthdays = _birthday_map()
    birthday = birthdays.get(user_id, {})

    name = _display_name(row, live)
    username = row.get("username")
    if username:
        username = f"@{username.lstrip('@')}"
    else:
        username = "Not set"

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
