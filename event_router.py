# ==========================================================
# Melanated AZ Bot - Event Flyer Verification / Approval
# ==========================================================

import json
import logging
import os
import re
import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger("event_router")

EVENT_CHAT_ID = -1002697105809
EVENT_TOPIC_ID = 12214
ADMIN_GROUP_ID = -5241371581
DB_PATH = "/var/data/events.db" if os.path.isdir("/var/data") else "./events.db"

FIELD_ORDER = ("event", "date", "time", "location")
FIELD_LABELS = {
    "event": "🎉 Event",
    "date": "📅 Date",
    "time": "⏰ Time",
    "location": "📍 Location",
}

_engine = None


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with _db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS event_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                source_chat_id INTEGER NOT NULL,
                source_message_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                file_id TEXT NOT NULL,
                fields_json TEXT NOT NULL,
                status TEXT NOT NULL,
                admin_message_id INTEGER,
                admin_details_message_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        conn.commit()


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def _save_submission(user, message, media_type, file_id, fields, status="member_input"):
    now = _now()
    with _db() as conn:
        cur = conn.execute(
            """INSERT INTO event_submissions
            (user_id, username, first_name, source_chat_id, source_message_id,
             media_type, file_id, fields_json, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user.id,
                user.username,
                user.first_name,
                message.chat_id,
                message.message_id,
                media_type,
                file_id,
                json.dumps(fields, ensure_ascii=False),
                status,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid


def _get_submission(submission_id):
    with _db() as conn:
        return conn.execute(
            "SELECT * FROM event_submissions WHERE id=?", (submission_id,)
        ).fetchone()


def _update_submission(submission_id, *, fields=None, status=None, admin_message_id=None, admin_details_message_id=None):
    row = _get_submission(submission_id)
    if not row:
        return
    values = []
    sets = []
    if fields is not None:
        sets.append("fields_json=?")
        values.append(json.dumps(fields, ensure_ascii=False))
    if status is not None:
        sets.append("status=?")
        values.append(status)
    if admin_message_id is not None:
        sets.append("admin_message_id=?")
        values.append(admin_message_id)
    if admin_details_message_id is not None:
        sets.append("admin_details_message_id=?")
        values.append(admin_details_message_id)
    sets.append("updated_at=?")
    values.append(_now())
    values.append(submission_id)
    with _db() as conn:
        conn.execute(
            f"UPDATE event_submissions SET {', '.join(sets)} WHERE id=?", values
        )
        conn.commit()




def _fields(row):
    try:
        data = json.loads(row["fields_json"] or "{}")
        return {
            key: (str(data.get(key) or "").strip() or None)
            for key in FIELD_ORDER
        }
    except (TypeError, ValueError, json.JSONDecodeError):
        return {key: None for key in FIELD_ORDER}


def _ensure_published_message_column():
    """Add the publication tracking column for sortable public event flyers."""
    with _db() as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(event_submissions)").fetchall()
        }
        if "published_message_id" not in columns:
            conn.execute(
                "ALTER TABLE event_submissions ADD COLUMN published_message_id INTEGER"
            )
        conn.commit()


def _event_sort_key(row):
    """Return a chronological sort key, with unknown dates safely last."""
    fields = _fields(row)
    raw = str(fields.get("date") or "").strip()
    today = datetime.now().date()
    patterns = (
        (r"^(\\d{1,2})[/-](\\d{1,2})[/-](\\d{4})$", "%m/%d/%Y"),
        (r"^(\\d{1,2})[/-](\\d{1,2})[/-](\\d{2})$", "%m/%d/%y"),
    )
    parsed = None
    for pattern, fmt in patterns:
        if re.match(pattern, raw):
            try:
                parsed = datetime.strptime(raw, fmt).date()
                break
            except ValueError:
                pass
    if parsed is None:
        cleaned = re.sub(r"(st|nd|rd|th)", "", raw, flags=re.IGNORECASE)
        for fmt in ("%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y"):
            try:
                parsed = datetime.strptime(cleaned, fmt).date()
                break
            except ValueError:
                pass
    if parsed is None:
        return (2, raw.lower(), int(row["id"]))
    return (0 if parsed >= today else 1, parsed, int(row["id"]))


def _approved_rows():
    with _db() as conn:
        return conn.execute(
            "SELECT * FROM event_submissions WHERE status='approved' ORDER BY id ASC"
        ).fetchall()


def _set_published_message_id(submission_id, message_id):
    with _db() as conn:
        conn.execute(
            "UPDATE event_submissions SET published_message_id=?, updated_at=? WHERE id=?",
            (message_id, _now(), submission_id),
        )
        conn.commit()


async def _republish_events_in_date_order(context):
    """Rebuild approved Events-topic flyers in chronological event-date order."""
    rows = sorted(_approved_rows(), key=_event_sort_key)
    if not rows:
        return

    for row in rows:
        message_id = row["published_message_id"]
        if message_id:
            try:
                await context.bot.delete_message(
                    chat_id=EVENT_CHAT_ID,
                    message_id=message_id,
                )
            except TelegramError:
                logger.info("Could not delete prior published event message %s", message_id)

    for row in rows:
        fields = _fields(row)
        caption = "📅 <b>EVENT</b>\\n\\n" + _format_fields(fields)
        if row["media_type"] == "photo":
            published = await context.bot.send_photo(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                photo=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )
        else:
            published = await context.bot.send_video(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                video=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )
        _set_published_message_id(row["id"], published.message_id)

    logger.info("Events topic reordered by event day | count=%s", len(rows))

def _missing(fields):
    return [key for key in FIELD_ORDER if not fields.get(key)]


def _clean_ocr_text(text):
    lines = []
    for raw in str(text or "").splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" |•\t")
        if line and line not in lines:
            lines.append(line)
    return lines


def _extract_field(lines, labels):
    for line in lines:
        low = line.lower()
        for label in labels:
            match = re.search(rf"\b{re.escape(label)}\s*[:\-]\s*(.+)$", low)
            if match:
                start = match.start(1)
                return line[start:].strip()
    return None


def _extract_date(text):
    patterns = [
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{2,4})?\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}[/-]\d{1,2}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _extract_time(text):
    pattern = r"\b\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\b(?:\s*[-–—]\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\b)?"
    match = re.search(pattern, text)
    return match.group(0).strip() if match else None


def _extract_location(lines, text):
    value = _extract_field(lines, ("location", "venue", "address"))
    if value:
        return value
    for line in lines:
        match = re.search(r"\b(?:at|@)\s+(.{3,100})$", line, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .|,-")
            if not re.search(r"\b(?:pm|am)\b", candidate, re.IGNORECASE):
                return candidate
    # Common venue/address clues when no explicit label is present.
    for line in lines:
        if re.search(r"\b(?:street|st\.?|avenue|ave\.?|road|rd\.?|drive|dr\.?|blvd\.?|boulevard|suite|ste\.?|tucson|phoenix|mesa|tempe|scottsdale|az)\b", line, re.IGNORECASE):
            if not _extract_date(line) and not _extract_time(line):
                return line.strip()
    return None


def _extract_event(lines):
    value = _extract_field(lines, ("event", "event name", "name"))
    if value:
        return value
    keywords = re.compile(
        r"\b(?:event|party|festival|concert|mixer|brunch|gala|meetup|social|night|day party|showcase|celebration|networking|expo|conference|workshop|fundraiser|kickback)\b",
        re.IGNORECASE,
    )
    for line in lines[:12]:
        if keywords.search(line) and not _extract_date(line) and not _extract_time(line):
            return line.strip(" -:|•")
    # A flyer normally puts the title near the top. Use the first substantial
    # line as a candidate, but it remains subject to member confirmation.
    for line in lines[:8]:
        if len(line) >= 4 and not _extract_date(line) and not _extract_time(line):
            if not re.search(r"\b(?:location|venue|address|doors|tickets?)\b", line, re.IGNORECASE):
                return line.strip(" -:|•")
    return None


def _ocr_image(image_bytes):
    global _engine
    try:
        from PIL import Image
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR

        if _engine is None:
            _engine = RapidOCR()
        image = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGB")
        result, _ = _engine(np.array(image))
        if not result:
            return ""
        return "\n".join(str(item[1]) for item in result if len(item) >= 2)
    except Exception:
        logger.exception("Event flyer OCR failed")
        return ""


async def _download_photo(message):
    photo = message.photo[-1]
    file = await photo.get_file()
    return bytes(await file.download_as_bytearray()), photo.file_id, "photo"


async def _download_video(message):
    # Video OCR is intentionally limited to the video's thumbnail/metadata path.
    # Members can still provide missing fields manually. The video itself is
    # preserved for admin review and final publication.
    return None, message.video.file_id, "video"


def _parse_fields(text):
    lines = _clean_ocr_text(text)
    full = "\n".join(lines)
    return {
        "event": _extract_event(lines),
        "date": _extract_date(full),
        "time": _extract_time(full),
        "location": _extract_location(lines, full),
    }


def _format_fields(fields):
    return "\n".join(
        f"{FIELD_LABELS[key]}: {fields.get(key) or '❌ Missing'}"
        for key in FIELD_ORDER
    )


def _verification_keyboard(submission_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ EDIT / FILL IN", callback_data=f"event_edit_{submission_id}")],
        [InlineKeyboardButton("✅ CONFIRM & SUBMIT", callback_data=f"event_confirm_{submission_id}")],
    ])


async def _ask_next_missing(update, context, submission_id, fields):
    missing = _missing(fields)
    if not missing:
        await update.effective_message.reply_text(
            "🔎 <b>VERIFY EVENT INFORMATION</b>\n\n"
            + _format_fields(fields)
            + "\n\nIf everything is correct, tap <b>CONFIRM & SUBMIT</b>.",
            parse_mode="HTML",
            reply_markup=_verification_keyboard(submission_id),
        )
        return

    field = missing[0]
    context.user_data["event_waiting_for"] = field
    context.user_data["event_submission_id"] = submission_id
    await update.effective_message.reply_text(
        "⚠️ <b>EVENT INFORMATION MISSING</b>\n\n"
        + _format_fields(fields)
        + f"\n\nPlease provide the missing information:\n<b>{FIELD_LABELS[field]}</b>",
        parse_mode="HTML",
    )


async def _process_media(update, context):
    message = update.effective_message
    if not message or message.chat_id != EVENT_CHAT_ID:
        return False
    if getattr(message, "message_thread_id", None) != EVENT_TOPIC_ID:
        return False
    if not message.photo and not message.video:
        return False

    user = update.effective_user
    if not user or user.is_bot:
        return True

    try:
        if message.photo:
            image_bytes, file_id, media_type = await _download_photo(message)
            ocr_text = _ocr_image(image_bytes)
        else:
            image_bytes, file_id, media_type = await _download_video(message)
            ocr_text = message.caption or ""

        combined_text = "\n".join(x for x in (ocr_text, message.caption or "") if x)
        fields = _parse_fields(combined_text)
        submission_id = _save_submission(user, message, media_type, file_id, fields)

        # The flyer never becomes public while it is being verified.
        try:
            await message.delete()
        except TelegramError:
            logger.warning("Could not delete pending event flyer message %s", message.message_id)

        if _missing(fields):
            await context.bot.send_message(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                text=(
                    "⚠️ <b>EVENT FLYER NEEDS INFORMATION</b>\n\n"
                    + _format_fields(fields)
                    + "\n\nI need the missing information before I can send this event to the admins for approval."
                ),
                parse_mode="HTML",
            )
            fake_update = update
            fake_update.effective_message = await context.bot.send_message(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                text="Please provide the missing information below.",
            )
            await _ask_next_missing(fake_update, context, submission_id, fields)
        else:
            sent = await context.bot.send_message(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                text=(
                    "🔎 <b>VERIFY EVENT INFORMATION</b>\n\n"
                    + _format_fields(fields)
                    + "\n\nPlease verify the extracted information before I send the flyer to the admins."
                ),
                parse_mode="HTML",
                reply_markup=_verification_keyboard(submission_id),
            )
            logger.info("Event submission %s awaiting member confirmation", submission_id)
        return True
    except Exception:
        logger.exception("Event submission processing failed")
        try:
            await context.bot.send_message(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                text="⚠️ I couldn't process that flyer. Please resend the flyer or provide the Event, Date, Time, and Location in the message caption.",
            )
        except Exception:
            pass
        return True


async def handle_event_photo(update, context):
    if await _process_media(update, context):
        raise ApplicationHandlerStop


async def handle_event_video(update, context):
    if await _process_media(update, context):
        raise ApplicationHandlerStop


async def handle_event_text(update, context):
    message = update.effective_message
    if not message or message.chat_id != EVENT_CHAT_ID:
        return
    if getattr(message, "message_thread_id", None) != EVENT_TOPIC_ID:
        return

    submission_id = context.user_data.get("event_submission_id")
    field = context.user_data.get("event_waiting_for")
    if not submission_id or not field:
        return

    row = _get_submission(int(submission_id))
    if not row or row["status"] not in {"member_input", "awaiting_confirmation"}:
        context.user_data.pop("event_submission_id", None)
        context.user_data.pop("event_waiting_for", None)
        return

    value = (message.text or "").strip()
    if not value:
        await message.reply_text(f"Please provide a value for {FIELD_LABELS[field]}.")
        raise ApplicationHandlerStop

    fields = _fields(row)
    fields[field] = value
    _update_submission(submission_id, fields=fields, status="member_input")
    context.user_data.pop("event_waiting_for", None)
    await _ask_next_missing(update, context, int(submission_id), fields)
    raise ApplicationHandlerStop


async def handle_event_member_callback(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    data = query.data or ""
    match = re.fullmatch(r"event_(edit|confirm)_(\d+)", data)
    if not match:
        return
    submission_id = int(match.group(2))
    row = _get_submission(submission_id)
    if not row or row["user_id"] != user.id:
        await query.answer("This event submission is not yours.", show_alert=True)
        return
    if row["status"] not in {"member_input", "awaiting_confirmation"}:
        await query.answer("This submission is no longer editable.", show_alert=True)
        return

    fields = _fields(row)
    if match.group(1) == "edit":
        await query.answer()
        context.user_data["event_submission_id"] = submission_id
        context.user_data["event_waiting_for"] = _missing(fields)[0] if _missing(fields) else "event"
        await query.message.reply_text(
            "✏️ <b>EDIT EVENT INFORMATION</b>\n\n"
            + _format_fields(fields)
            + f"\n\nEnter the value for <b>{FIELD_LABELS[context.user_data['event_waiting_for']]}</b>.",
            parse_mode="HTML",
        )
        return

    missing = _missing(fields)
    if missing:
        await query.answer("Some required information is still missing.", show_alert=True)
        context.user_data["event_submission_id"] = submission_id
        context.user_data["event_waiting_for"] = missing[0]
        await query.message.reply_text(
            "⚠️ <b>Missing information</b>\n\n"
            + "\n".join(f"❌ {FIELD_LABELS[k]}" for k in missing)
            + "\n\nPlease provide the missing information.",
            parse_mode="HTML",
        )
        return

    await query.answer("Submitting to admins...")
    await _send_to_admins(context, submission_id, row, fields)
    context.user_data.pop("event_submission_id", None)
    context.user_data.pop("event_waiting_for", None)
    try:
        await query.message.edit_text(
            "✅ <b>EVENT SUBMITTED FOR ADMIN APPROVAL</b>\n\n"
            + _format_fields(fields)
            + "\n\nThe flyer is now with the admins. It will be posted publicly only if approved.",
            parse_mode="HTML",
        )
    except Exception:
        pass


async def _send_to_admins(context, submission_id, row, fields):
    submitter = f"@{row['username']}" if row["username"] else row["first_name"] or str(row["user_id"])
    caption = "🎟️ <b>EVENT FLYER — PENDING ADMIN APPROVAL</b>\n\nSubmitted by: " + submitter
    try:
        if row["media_type"] == "photo":
            media_message = await context.bot.send_photo(
                chat_id=ADMIN_GROUP_ID,
                photo=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )
        else:
            media_message = await context.bot.send_video(
                chat_id=ADMIN_GROUP_ID,
                video=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )

        details = await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                "📋 <b>EVENT REVIEW</b>\n\n"
                + _format_fields(fields)
                + "\n\n"
                "🔎 <b>Automated check:</b> All four required fields are present.\n"
                "👤 <b>Final decision:</b> Admin approval required."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ APPROVE", callback_data=f"event_admin_approve_{submission_id}"),
                    InlineKeyboardButton("❌ DENY", callback_data=f"event_admin_deny_{submission_id}"),
                ]
            ]),
        )
        _update_submission(
            submission_id,
            status="pending_admin",
            admin_message_id=media_message.message_id,
            admin_details_message_id=details.message_id,
        )
        logger.info("Event submission %s sent to admin group", submission_id)
    except Exception:
        logger.exception("Could not send event submission %s to admin group", submission_id)
        _update_submission(submission_id, status="admin_send_failed")
        try:
            await context.bot.send_message(
                chat_id=row["source_chat_id"],
                message_thread_id=EVENT_TOPIC_ID,
                text="⚠️ I couldn't send the event flyer to the admins. Please try again.",
            )
        except Exception:
            pass


async def handle_event_admin_callback(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    data = query.data or ""
    match = re.fullmatch(r"event_admin_(approve|deny)_(\d+)", data)
    if not match:
        return

    try:
        from admin import is_admin
        if not await is_admin(user.id, context):
            await query.answer("⛔ You are not authorized.", show_alert=True)
            return
    except Exception:
        await query.answer("⛔ Unable to verify admin access.", show_alert=True)
        return

    submission_id = int(match.group(2))
    row = _get_submission(submission_id)
    if not row or row["status"] != "pending_admin":
        await query.answer("This event has already been processed.", show_alert=True)
        return

    fields = _fields(row)
    action = match.group(1)
    if action == "deny":
        _update_submission(submission_id, status="denied")
        await query.answer("Event denied.")
        try:
            await query.edit_message_text(
                "❌ <b>EVENT DENIED</b>\n\n" + _format_fields(fields),
                parse_mode="HTML",
            )
        except Exception:
            pass
        await _notify_submitter(context, row, "❌ Your event flyer was not approved by the admins.")
        return

    await query.answer("Publishing event...")
    try:
        caption = "📅 <b>EVENT</b>\n\n" + _format_fields(fields)
        if row["media_type"] == "photo":
            published = await context.bot.send_photo(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                photo=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )
        else:
            published = await context.bot.send_video(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                video=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )
        _update_submission(submission_id, status="approved")
        await _republish_events_in_date_order(context)
        try:
            await query.edit_message_text(
                "✅ <b>EVENT APPROVED & PUBLISHED</b>\n\n"
                + _format_fields(fields)
                + f"\n\nPublished message: {published.message_id}",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await _notify_submitter(context, row, "✅ Your event flyer was approved and posted in the Events topic.")
        logger.info("Event submission %s approved and published", submission_id)
    except Exception:
        logger.exception("Could not publish approved event %s", submission_id)
        await query.answer("Publishing failed. Check the Render logs.", show_alert=True)


async def _notify_submitter(context, row, text):
    try:
        await context.bot.send_message(chat_id=row["user_id"], text=text)
    except TelegramError:
        # The bot cannot initiate a DM if the member has never started it.
        logger.info("Could not DM event submitter user_id=%s", row["user_id"])


def install_application(application):
    if getattr(application, "_melanated_event_router_installed", False):
        return
    _init_db()

    # Event handlers run before the general media router so event flyers are
    # held for verification instead of being moved to the Media topic.
    application.add_handler(MessageHandler(filters.PHOTO, handle_event_photo), group=-2)
    application.add_handler(MessageHandler(filters.VIDEO, handle_event_video), group=-2)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_event_text), group=-2)
    application.add_handler(
        CallbackQueryHandler(handle_event_member_callback, pattern=r"^event_(?:edit|confirm)_\d+$"),
        group=-2,
    )
    application.add_handler(
        CallbackQueryHandler(handle_event_admin_callback, pattern=r"^event_admin_(?:approve|deny)_\d+$"),
        group=-2,
    )
    application._melanated_event_router_installed = True
    logger.info(
        "Event flyer approval workflow enabled | chat=%s | topic=%s | admin_group=%s",
        EVENT_CHAT_ID,
        EVENT_TOPIC_ID,
        ADMIN_GROUP_ID,
    )


def install(bot_module):
    original_build_application = bot_module.build_application

    def wrapped_build_application(*args, **kwargs):
        application = original_build_application(*args, **kwargs)
        install_application(application)
        return application

    bot_module.build_application = wrapped_build_application
