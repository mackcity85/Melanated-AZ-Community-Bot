# ==========================================================
# Melanated AZ Bot - Events Admin Panel
# Safe compatibility patch: adds Events controls without
# replacing the existing admin panel implementation.
# ==========================================================

import json
import logging
import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import admin

logger = logging.getLogger("event_admin_panel")

DB_PATH = "/var/data/events.db"
EVENT_TOPIC_ID = 12214

_previous_admin_button = None
_previous_admin_main_keyboard = None


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(status=None):
    try:
        with _db() as conn:
            if status:
                return conn.execute(
                    "SELECT * FROM event_submissions WHERE status=? ORDER BY id DESC",
                    (status,),
                ).fetchall()
            return conn.execute(
                "SELECT * FROM event_submissions ORDER BY id DESC"
            ).fetchall()
    except Exception:
        logger.exception("Unable to read Events database")
        return []


def _fields(row):
    try:
        return json.loads(row["fields_json"] or "{}")
    except Exception:
        return {}


def _label(row):
    fields = _fields(row)
    event = fields.get("event") or "Unknown event"
    date = fields.get("date") or "Unknown date"
    return f"{event} — {date}"


def _event_button():
    return InlineKeyboardButton("📅 Events", callback_data="admin_events")


def _patched_admin_main_keyboard(*args, **kwargs):
    keyboard = _previous_admin_main_keyboard(*args, **kwargs)
    # Do not mutate the original list in place in case another patch keeps a
    # reference to it. Add one dedicated row to the returned markup.
    rows = [list(row) for row in (keyboard.inline_keyboard or [])]
    if not any(
        button.callback_data == "admin_events"
        for row in rows
        for button in row
    ):
        rows.append([_event_button()])
    return InlineKeyboardMarkup(rows)


async def admin_events(update, context):
    if not await admin.require_admin(update, context):
        return

    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    pending = _rows("pending_admin")
    all_rows = _rows()
    approved = sum(1 for row in all_rows if row["status"] == "approved")
    denied = sum(1 for row in all_rows if row["status"] == "denied")
    failed = sum(1 for row in all_rows if row["status"] == "admin_send_failed")

    text = (
        "📅 **EVENTS ADMIN**\n\n"
        f"⏳ Pending approval: **{len(pending)}**\n"
        f"✅ Approved/published: **{approved}**\n"
        f"❌ Denied: **{denied}**\n"
        f"⚠️ Send failures: **{failed}**\n\n"
        "📍 Public destination: Events topic `12214`\n"
        "🔐 All public event flyers require admin approval."
    )

    buttons = [
        [InlineKeyboardButton("⏳ Pending Events", callback_data="admin_events_pending")],
        [InlineKeyboardButton("📊 Event Statistics", callback_data="admin_events_stats")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_events")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")],
    ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def admin_events_pending(update, context):
    if not await admin.require_admin(update, context):
        return

    query = update.callback_query
    if not query:
        return
    await query.answer()

    pending = _rows("pending_admin")
    if not pending:
        await query.edit_message_text(
            "⏳ **PENDING EVENTS**\n\nThere are currently no events waiting for approval.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📅 Events Controls", callback_data="admin_events")],
                [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return

    lines = ["⏳ **PENDING EVENTS**", ""]
    buttons = []
    for row in pending[:20]:
        lines.append(f"• **#{row['id']}** {_label(row)}")
        buttons.append([
            InlineKeyboardButton(
                f"👀 #{row['id']} Review",
                callback_data=f"event_admin_review_{row['id']}",
            )
        ])

    lines.append("")
    lines.append("Select an event to send its flyer to this admin chat with approval controls.")
    buttons.extend([
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_events_pending")],
        [InlineKeyboardButton("⬅️ Events Controls", callback_data="admin_events")],
    ])

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def admin_events_review(update, context, submission_id):
    if not await admin.require_admin(update, context):
        return

    query = update.callback_query
    if not query:
        return
    await query.answer("Loading event review...")

    try:
        submission_id = int(submission_id)
        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM event_submissions WHERE id=?",
                (submission_id,),
            ).fetchone()
    except Exception:
        row = None

    if not row:
        await query.answer("Event submission not found.", show_alert=True)
        return
    if row["status"] != "pending_admin":
        await query.answer("This event is no longer pending.", show_alert=True)
        return

    fields = _fields(row)
    submitter = f"@{row['username']}" if row["username"] else row["first_name"] or str(row["user_id"])
    details = (
        "📅 **EVENT REVIEW**\n\n"
        f"**Submission:** #{submission_id}\n"
        f"**Submitted by:** {submitter}\n\n"
        f"🎉 **Event:** {fields.get('event') or 'Missing'}\n"
        f"📅 **Date:** {fields.get('date') or 'Missing'}\n"
        f"⏰ **Time:** {fields.get('time') or 'Missing'}\n"
        f"📍 **Location:** {fields.get('location') or 'Missing'}\n\n"
        "Use the buttons below to approve or deny."
    )

    # Send the actual stored flyer to the admin chat again, with the same
    # authoritative approval callbacks used by the main Events workflow.
    try:
        if row["media_type"] == "photo":
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=row["file_id"],
                caption=details,
                parse_mode="Markdown",
            )
        else:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=row["file_id"],
                caption=details,
                parse_mode="Markdown",
            )
    except Exception:
        logger.exception("Unable to resend event flyer for review")

    await query.edit_message_text(
        details,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ APPROVE", callback_data=f"event_admin_approve_{submission_id}"),
                InlineKeyboardButton("❌ DENY", callback_data=f"event_admin_deny_{submission_id}"),
            ],
            [InlineKeyboardButton("⬅️ Pending Events", callback_data="admin_events_pending")],
        ]),
        parse_mode="Markdown",
    )


async def admin_events_stats(update, context):
    if not await admin.require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer()

    rows = _rows()
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    await query.edit_message_text(
        "📊 **EVENT STATISTICS**\n\n"
        f"📥 Total submissions: **{len(rows)}**\n"
        f"⏳ Pending admin approval: **{counts.get('pending_admin', 0)}**\n"
        f"✏️ Waiting for member info: **{counts.get('member_input', 0)}**\n"
        f"🔎 Awaiting member confirmation: **{counts.get('awaiting_confirmation', 0)}**\n"
        f"✅ Approved/published: **{counts.get('approved', 0)}**\n"
        f"❌ Denied: **{counts.get('denied', 0)}**\n"
        f"⚠️ Admin send failures: **{counts.get('admin_send_failed', 0)}**\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Events Controls", callback_data="admin_events")],
            [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
        ]),
        parse_mode="Markdown",
    )


async def _patched_admin_button(update, context):
    query = update.callback_query
    data = query.data if query else ""

    if data == "admin_events":
        await admin_events(update, context)
        return
    if data == "admin_events_pending":
        await admin_events_pending(update, context)
        return
    if data == "admin_events_stats":
        await admin_events_stats(update, context)
        return
    if data.startswith("event_admin_review_"):
        await admin_events_review(update, context, data.rsplit("_", 1)[-1])
        return

    await _previous_admin_button(update, context)


def install():
    global _previous_admin_button, _previous_admin_main_keyboard

    if getattr(admin, "_melanated_event_admin_installed", False):
        return

    _previous_admin_button = admin.admin_button
    _previous_admin_main_keyboard = admin.admin_main_keyboard

    admin.admin_button = _patched_admin_button
    admin.admin_main_keyboard = _patched_admin_main_keyboard
    admin._melanated_event_admin_installed = True
    logger.info(
        "Events admin panel installed | topic=%s | database=%s",
        EVENT_TOPIC_ID,
        DB_PATH,
    )
