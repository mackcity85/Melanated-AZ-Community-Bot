# ==========================================================
# Melanated AZ Bot - INDEPENDENT EVENT OCR SYSTEM
# event_ocr.py
# ==========================================================
# This file is the complete Event workflow.
#
# It intentionally has NO dependency on event_router.py,
# event_router_fix.py, event_private_flow.py, or
# event_website_patch.py.
#
# Flow:
#   1. Detect Events topic
#   2. Intercept flyer photo/video before media moderation
#   3. OCR photo (and video thumbnail when available)
#   4. Extract Event / Date / Time / Location / Price / Website
#   5. Ask member to fill missing fields and confirm
#   6. Send confirmed submission to admin group
#   7. Admin approves or denies
#   8. Approved events are rebuilt in chronological order
#
# The rest of the bot is not changed by this module.
# ==========================================================

import html
import io
import json
import logging
import os
import re
import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

logger = logging.getLogger("event_ocr")

EVENT_CHAT_ID = -1002697105809
EVENT_TOPIC_ID = 12214
ADMIN_GROUP_ID = -5241371581
DB_PATH = "/var/data/events.db" if os.path.isdir("/var/data") else "./events.db"

FIELD_ORDER = ("event", "date", "time", "location", "price", "website")
FIELD_LABELS = {
    "event": "🎉 Event",
    "date": "📅 Date",
    "time": "⏰ Time",
    "location": "📍 Location",
    "price": "💵 Price",
    "website": "🌐 Website",
}
REQUIRED_FIELDS = ("event", "date", "time", "location", "price")

_ENGINE = None


# ==========================================================
# DATABASE
# ==========================================================

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


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
                published_message_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(event_submissions)").fetchall()
        }

        additions = {
            "admin_message_id": "INTEGER",
            "admin_details_message_id": "INTEGER",
            "published_message_id": "INTEGER",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        }

        for name, definition in additions.items():
            if name not in columns:
                conn.execute(
                    f"ALTER TABLE event_submissions ADD COLUMN {name} {definition}"
                )

        conn.commit()


def _save_submission(user, message, media_type, file_id, fields):
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
                "member_input",
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid


def _get_submission(submission_id):
    with _db() as conn:
        return conn.execute(
            "SELECT * FROM event_submissions WHERE id=?",
            (int(submission_id),),
        ).fetchone()


def _latest_editable_submission(user_id):
    with _db() as conn:
        return conn.execute(
            "SELECT * FROM event_submissions "
            "WHERE user_id=? AND status IN ('member_input', 'awaiting_confirmation') "
            "ORDER BY id DESC LIMIT 1",
            (int(user_id),),
        ).fetchone()


def _update_submission(
    submission_id,
    *,
    fields=None,
    status=None,
    admin_message_id=None,
    admin_details_message_id=None,
    published_message_id=None,
):
    sets = []
    values = []

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

    if published_message_id is not None:
        sets.append("published_message_id=?")
        values.append(published_message_id)

    sets.append("updated_at=?")
    values.append(_now())
    values.append(int(submission_id))

    with _db() as conn:
        conn.execute(
            f"UPDATE event_submissions SET {', '.join(sets)} WHERE id=?",
            values,
        )
        conn.commit()


def _fields(row):
    try:
        data = json.loads(row["fields_json"] or "{}")
    except Exception:
        data = {}

    return {
        key: (str(data.get(key) or "").strip() or None)
        for key in FIELD_ORDER
    }


# ==========================================================
# EVENT TOPIC DETECTION
# ==========================================================

def _is_events_topic(message):
    if not message:
        return False
    return (
        message.chat_id == EVENT_CHAT_ID
        and getattr(message, "message_thread_id", None) == EVENT_TOPIC_ID
    )


# ==========================================================
# OCR
# ==========================================================

def _ocr_image(image_bytes):
    global _ENGINE

    if not image_bytes:
        return ""

    try:
        from PIL import Image
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR

        if _ENGINE is None:
            logger.info("Initializing independent Event OCR engine")
            _ENGINE = RapidOCR()

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        result, _ = _ENGINE(np.array(image))

        if not result:
            return ""

        text = "\n".join(
            str(item[1])
            for item in result
            if isinstance(item, (list, tuple)) and len(item) >= 2 and item[1]
        )

        logger.info(
            "Event OCR complete | chars=%s | lines=%s",
            len(text),
            len(text.splitlines()) if text else 0,
        )
        return text

    except Exception:
        logger.exception("Independent Event OCR failed")
        return ""


async def _download_photo(message):
    photo = message.photo[-1]
    telegram_file = await photo.get_file()
    image_bytes = bytes(await telegram_file.download_as_bytearray())
    return image_bytes, photo.file_id, "photo"


async def _download_video_thumbnail(message):
    video = message.video
    thumbnail = getattr(video, "thumbnail", None) or getattr(video, "thumb", None)
    if not thumbnail:
        return "", video.file_id, "video"

    try:
        telegram_file = await thumbnail.get_file()
        image_bytes = bytes(await telegram_file.download_as_bytearray())
        return image_bytes, video.file_id, "video"
    except Exception:
        logger.exception("Event video thumbnail download failed")
        return "", video.file_id, "video"


# ==========================================================
# OCR FIELD EXTRACTION
# ==========================================================

def _clean_lines(text):
    result = []
    for raw in str(text or "").splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" |•\t")
        if line and line not in result:
            result.append(line)
    return result


def _extract_labeled(lines, labels):
    for line in lines:
        for label in labels:
            match = re.search(
                rf"\b{re.escape(label)}\s*[:\-]\s*(.+)$",
                line,
                re.IGNORECASE,
            )
            if match:
                return match.group(1).strip()
    return None


def _extract_date(text):
    patterns = (
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
        r"nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?"
        r"(?:,?\s+\d{2,4})?\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}[/-]\d{1,2}\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _extract_time(text):
    pattern = (
        r"\b\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\b"
        r"(?:\s*[-–—]\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\b)?"
    )
    match = re.search(pattern, text)
    return match.group(0).strip() if match else None


def _extract_price(text):
    raw = str(text or "")

    if re.search(
        r"\b(?:free|no\s+cost|complimentary)\b",
        raw,
        re.IGNORECASE,
    ):
        return "Free"

    # Preserve common price-table information when OCR produces a
    # simple labeled line rather than reducing it to one number.
    labeled = re.search(
        r"(?im)^\s*(?:price|prices|admission|tickets?|entry|cost)\s*[:\-]\s*(.+)$",
        raw,
    )
    if labeled:
        return labeled.group(1).strip()

    money = re.findall(
        r"\$\s*\d+(?:\.\d{1,2})?|\b\d+(?:\.\d{1,2})?\s*(?:USD|dollars?)\b",
        raw,
        re.IGNORECASE,
    )
    if money:
        unique = []
        for item in money:
            item = item.strip()
            if item not in unique:
                unique.append(item)
        return " / ".join(unique[:6])

    return None


def _extract_website(text):
    raw = str(text or "")

    match = re.search(r"(?i)\bhttps?://[^\s<>\]\[()]+", raw)
    if not match:
        match = re.search(r"(?i)\bwww\.[^\s<>\]\[()]+", raw)

    if not match:
        match = re.search(
            r"(?i)\b(?:[a-z0-9-]+\.)+(?:com|org|net|co|io|us|me)"
            r"(?:/[^\s<>\]\[()]+)?",
            raw,
        )

    if not match:
        return None

    url = match.group(0).rstrip(".,;:!?)\"'")
    if url.lower().startswith("www."):
        url = "https://" + url
    elif not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    return url


def _extract_location(lines):
    value = _extract_labeled(lines, ("location", "venue", "address"))
    if value:
        return value

    for line in lines:
        match = re.search(
            r"\b(?:at|@)\s+(.{3,120})$",
            line,
            re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip(" .|,-")
            if not re.search(r"\b(?:am|pm)\b", candidate, re.IGNORECASE):
                return candidate

    location_terms = re.compile(
        r"\b(?:street|st\.?|avenue|ave\.?|road|rd\.?|drive|dr\.?|"
        r"boulevard|blvd\.?|suite|ste\.?|tucson|phoenix|mesa|tempe|"
        r"scottsdale|chandler|gilbert|arizona|az)\b",
        re.IGNORECASE,
    )

    for line in lines:
        if (
            location_terms.search(line)
            and not _extract_date(line)
            and not _extract_time(line)
        ):
            return line.strip()

    return None


def _extract_event(lines):
    value = _extract_labeled(lines, ("event", "event name", "name", "title"))
    if value:
        return value

    keywords = re.compile(
        r"\b(?:event|party|festival|concert|mixer|brunch|gala|meetup|"
        r"social|night|day party|showcase|celebration|networking|expo|"
        r"conference|workshop|fundraiser|kickback)\b",
        re.IGNORECASE,
    )

    for line in lines[:15]:
        if (
            keywords.search(line)
            and not _extract_date(line)
            and not _extract_time(line)
        ):
            return line.strip(" -:|•")

    for line in lines[:10]:
        if (
            len(line) >= 4
            and not _extract_date(line)
            and not _extract_time(line)
            and not re.search(
                r"\b(?:location|venue|address|doors|tickets?|price|"
                r"admission|www\.|https?://)\b",
                line,
                re.IGNORECASE,
            )
        ):
            return line.strip(" -:|•")

    return None


def _parse_fields(text):
    lines = _clean_lines(text)
    full = "\n".join(lines)

    fields = {
        "event": _extract_event(lines),
        "date": _extract_date(full),
        "time": _extract_time(full),
        "location": _extract_location(lines),
        "price": _extract_price(full),
        "website": _extract_website(full),
    }

    # Event Name and Price are intentionally member-confirmed fields.
    # OCR can suggest them, but the member must confirm/fill them.
    fields["event"] = None
    fields["price"] = None

    return fields


# ==========================================================
# DISPLAY / MEMBER CONFIRMATION
# ==========================================================

def _missing(fields):
    return [key for key in REQUIRED_FIELDS if not fields.get(key)]


def _format_fields(fields):
    lines = []

    for key in FIELD_ORDER:
        value = fields.get(key)
        if key == "website" and value:
            safe = html.escape(str(value), quote=True)
            visible = html.escape(str(value))
            lines.append(f'{FIELD_LABELS[key]}: <a href="{safe}">{visible}</a>')
        else:
            lines.append(
                f"{FIELD_LABELS[key]}: "
                f"{html.escape(str(value)) if value else '❌ Missing'}"
            )

    return "\n".join(lines)


def _member_keyboard(submission_id, website_missing=False):
    buttons = [
        [
            InlineKeyboardButton(
                "✏️ EDIT / FILL IN",
                callback_data=f"event_ocr_edit_{submission_id}",
            )
        ]
    ]

    if website_missing:
        buttons.append(
            [
                InlineKeyboardButton(
                    "🌐 ENTER WEBSITE",
                    callback_data=f"event_ocr_website_{submission_id}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "✅ CONFIRM & SUBMIT",
                callback_data=f"event_ocr_confirm_{submission_id}",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


def _admin_keyboard(submission_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"event_ocr_admin_approve_{submission_id}",
                ),
                InlineKeyboardButton(
                    "❌ DENY",
                    callback_data=f"event_ocr_admin_deny_{submission_id}",
                ),
            ]
        ]
    )


async def _prompt_next_missing(context, user_id, submission_id):
    row = _get_submission(submission_id)
    if not row or row["user_id"] != user_id:
        return

    fields = _fields(row)
    missing = _missing(fields)

    if not missing:
        _update_submission(submission_id, status="awaiting_confirmation")
        await context.bot.send_message(
            chat_id=EVENT_CHAT_ID,
            message_thread_id=EVENT_TOPIC_ID,
            text=(
                "🔎 <b>VERIFY EVENT INFORMATION</b>\n\n"
                + _format_fields(fields)
                + "\n\nEverything required is present. "
                  "Review it and tap <b>CONFIRM &amp; SUBMIT</b>."
            ),
            parse_mode="HTML",
            reply_markup=_member_keyboard(submission_id, website_missing=not fields.get("website")),
        )
        return

    field = missing[0]
    context.user_data["event_ocr_submission_id"] = int(submission_id)
    context.user_data["event_ocr_waiting_for"] = field

    prompts = {
        "event": "🎉 <b>Event Name</b>\n\nPlease enter the name/title of the Event.",
        "date": "📅 <b>Date</b>\n\nPlease enter the Event date.",
        "time": "⏰ <b>Time</b>\n\nPlease enter the Event start time (and end time if applicable).",
        "location": "📍 <b>Location</b>\n\nPlease enter the Event venue/location.",
        "price": (
            "💵 <b>Price</b>\n\n"
            "Please enter the full pricing information. "
            "You may enter multiple prices, early-bird pricing, promo codes, "
            "or a pricing table. If it is free, type <b>Free</b>."
        ),
    }

    await context.bot.send_message(
        chat_id=EVENT_CHAT_ID,
        message_thread_id=EVENT_TOPIC_ID,
        text=(
            "⚠️ <b>EVENT INFORMATION MISSING</b>\n\n"
            + _format_fields(fields)
            + "\n\n"
            + prompts[field]
        ),
        parse_mode="HTML",
    )


async def _send_to_admins(context, submission_id):
    row = _get_submission(submission_id)
    if not row:
        return False

    fields = _fields(row)
    if _missing(fields):
        return False

    submitter = (
        f"@{row['username']}"
        if row["username"]
        else (row["first_name"] or str(row["user_id"]))
    )

    try:
        caption = (
            "🎟️ <b>EVENT FLYER — PENDING ADMIN APPROVAL</b>\n\n"
            f"Submitted by: {html.escape(submitter)}"
        )

        if row["media_type"] == "photo":
            media = await context.bot.send_photo(
                chat_id=ADMIN_GROUP_ID,
                photo=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )
        else:
            media = await context.bot.send_video(
                chat_id=ADMIN_GROUP_ID,
                video=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )

        details = await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                "🔎 <b>EVENT SUBMISSION</b>\n\n"
                + _format_fields(fields)
                + f"\n\nSubmitted by: {html.escape(submitter)}\n\n"
                "All required fields are present. Final decision requires admin approval."
            ),
            parse_mode="HTML",
            reply_markup=_admin_keyboard(submission_id),
        )

        _update_submission(
            submission_id,
            status="pending_admin",
            admin_message_id=media.message_id,
            admin_details_message_id=details.message_id,
        )
        logger.info(
            "Independent Event submission sent to admin group | submission=%s",
            submission_id,
        )
        return True

    except Exception:
        logger.exception(
            "Independent Event admin delivery failed | submission=%s",
            submission_id,
        )
        _update_submission(submission_id, status="admin_send_failed")
        return False


# ==========================================================
# PRIVATE EVENT EDIT FLOW
# ==========================================================

async def _event_bot_username(context):
    username = context.application.bot_data.get("bot_username")
    if username:
        return username
    try:
        me = await context.bot.get_me()
        username = me.username
        if username:
            context.application.bot_data["bot_username"] = username
            return username
    except Exception:
        logger.exception("Could not resolve Event bot username")
    return None


async def _delete_public_edit_prompt(context):
    job = context.job
    data = job.data or {}
    message_id = data.get("message_id")
    if not message_id:
        return

    try:
        await context.bot.delete_message(
            chat_id=EVENT_CHAT_ID,
            message_id=int(message_id),
        )
        logger.info("Deleted Event flyer received message | message=%s", message_id)
    except TelegramError:
        logger.info("Event flyer received message already gone | message=%s", message_id)
    except Exception:
        logger.exception("Could not delete Event flyer received message | message=%s", message_id)


async def _schedule_public_edit_prompt_cleanup(context, message):
    if not message or not getattr(context, "job_queue", None):
        return
    context.job_queue.run_once(
        _delete_public_edit_prompt,
        when=300,
        data={"message_id": message.message_id},
        name=f"event-flyer-received-cleanup:{message.message_id}",
    )


async def _send_public_edit_prompt(context, submission_id):
    username = await _event_bot_username(context)
    if not username:
        sent = await context.bot.send_message(
            chat_id=EVENT_CHAT_ID,
            message_thread_id=EVENT_TOPIC_ID,
            text=(
                "📸 <b>EVENT FLYER RECEIVED</b>\n\n"
                "The flyer was captured and OCR is complete. "
                "Please open the Melanated AZ Bot privately to edit/fill in "
                "the Event information."
            ),
            parse_mode="HTML",
        )
        await _schedule_public_edit_prompt_cleanup(context, sent)
        return

    url = f"https://t.me/{username}?start=eventocr_{submission_id}"
    sent = await context.bot.send_message(
        chat_id=EVENT_CHAT_ID,
        message_thread_id=EVENT_TOPIC_ID,
        text=(
            "📸 <b>EVENT FLYER RECEIVED</b>\n\n"
            "The flyer was captured and OCR is complete. "
            "Tap the button below to open the <b>Melanated AZ Bot</b> "
            "privately and edit/fill in the Event information.\n\n"
            "Nothing will be posted publicly until you confirm it and an admin approves it."
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📝 OPEN MELANATED AZ BOT — EDIT FLYER", url=url)]]
        ),
    )
    await _schedule_public_edit_prompt_cleanup(context, sent)


async def _send_private_event_editor(context, user_id, submission_id):
    row = _get_submission(submission_id)
    if not row or int(row["user_id"]) != int(user_id):
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ I couldn't find that Event submission. Please resend the flyer in the Events topic.",
        )
        return True

    if row["status"] not in {"member_input", "awaiting_confirmation"}:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ That Event submission is no longer editable.",
        )
        return True

    fields = _fields(row)
    missing = _missing(fields)
    context.user_data["event_ocr_submission_id"] = int(submission_id)
    if missing:
        context.user_data["event_ocr_waiting_for"] = missing[0]
    else:
        context.user_data.pop("event_ocr_waiting_for", None)

    caption = (
        "📝 <b>EDIT YOUR EVENT FLYER</b>\n\n"
        + _format_fields(fields)
        + "\n\nReview the information below. I will ask only for information that is missing."
    )

    try:
        if row["media_type"] == "photo":
            await context.bot.send_photo(
                chat_id=user_id,
                photo=row["file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=_member_keyboard(submission_id, website_missing=not fields.get("website")),
            )
        else:
            await context.bot.send_video(
                chat_id=user_id,
                video=row["file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=_member_keyboard(submission_id, website_missing=not fields.get("website")),
            )
    except TelegramError:
        logger.exception("Could not send Event flyer to private bot chat | submission=%s", submission_id)
        await context.bot.send_message(
            chat_id=user_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=_member_keyboard(submission_id, website_missing=not fields.get("website")),
        )

    if missing:
        prompts = {
            "event": "🎉 <b>Event Name</b>\n\nPlease enter the name/title of the Event.",
            "date": "📅 <b>Date</b>\n\nPlease enter the Event date.",
            "time": "⏰ <b>Time</b>\n\nPlease enter the Event start time (and end time if applicable).",
            "location": "📍 <b>Location</b>\n\nPlease enter the Event venue/location.",
            "price": (
                "💵 <b>Price</b>\n\n"
                "Please enter the full pricing information. "
                "You may enter multiple prices, early-bird pricing, promo codes, "
                "or a pricing table. If it is free, type <b>Free</b>."
            ),
            "website": (
                "🌐 <b>Website</b>\n\n"
                "OCR did not find a website on this flyer. "
                "Please enter the website manually. "
                "You can enter a full URL or a domain such as example.com. "
                "This field is optional; tap <b>CONFIRM &amp; SUBMIT</b> "
                "if the event has no website."
            ),
        }
        await context.bot.send_message(
            chat_id=user_id,
            text=prompts[missing[0]],
            parse_mode="HTML",
        )
    else:
        _update_submission(submission_id, status="awaiting_confirmation")

    return True


async def handle_event_start(update, context):
    message = update.effective_message
    user = update.effective_user
    if not message or not user or message.chat.type != "private":
        return

    args = getattr(context, "args", None) or []
    if not args or not args[0].lower().startswith("eventocr_"):
        return

    try:
        submission_id = int(args[0].split("_", 1)[1])
    except (ValueError, IndexError):
        return

    await _send_private_event_editor(context, user.id, submission_id)
    raise ApplicationHandlerStop


# ==========================================================
# MEDIA INTERCEPTION
# ==========================================================

async def _process_media(update, context):
    message = update.effective_message

    if not _is_events_topic(message):
        return False

    if not message.photo and not message.video:
        return False

    user = update.effective_user
    if not user or user.is_bot:
        return True

    submission_id = None

    try:
        if message.photo:
            image_bytes, file_id, media_type = await _download_photo(message)
            ocr_text = _ocr_image(image_bytes)
        else:
            image_bytes, file_id, media_type = await _download_video_thumbnail(message)
            ocr_text = _ocr_image(image_bytes) if image_bytes else ""
            if message.caption:
                ocr_text = "\n".join(
                    value for value in (ocr_text, message.caption) if value
                )

        if message.photo and message.caption:
            ocr_text = "\n".join(
                value for value in (ocr_text, message.caption) if value
            )

        fields = _parse_fields(ocr_text)
        submission_id = _save_submission(
            user,
            message,
            media_type,
            file_id,
            fields,
        )

        # Remove the raw flyer from the public topic while it is pending.
        try:
            await message.delete()
        except TelegramError:
            logger.warning(
                "Could not delete pending Event flyer | message=%s",
                message.message_id,
            )

        await _send_public_edit_prompt(
            context,
            submission_id,
        )

        logger.info(
            "Independent Event flyer captured | submission=%s | user=%s | "
            "ocr_chars=%s | fields=%s | missing=%s",
            submission_id,
            user.id,
            len(ocr_text or ""),
            fields,
            _missing(fields),
        )

        return True

    except Exception:
        logger.exception(
            "Independent Event flyer processing failed | submission=%s",
            submission_id,
        )

        try:
            await context.bot.send_message(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                text=(
                    "⚠️ <b>I couldn't process that Event flyer.</b>\n\n"
                    "Please resend the flyer. If OCR cannot read it, "
                    "I will ask you for the Event Name, Date, Time, "
                    "Location, and Price manually."
                ),
                parse_mode="HTML",
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


# ==========================================================
# MEMBER TEXT / CALLBACKS
# ==========================================================

async def handle_event_text(update, context):
    message = update.effective_message
    if not message:
        return

    is_private = message.chat.type == "private"
    if not is_private and not _is_events_topic(message):
        return

    submission_id = context.user_data.get("event_ocr_submission_id")
    field = context.user_data.get("event_ocr_waiting_for")

    # Recover the active Event submission if Telegram/user_data was lost
    # during the private handoff or a bot restart.
    if not submission_id:
        latest = _latest_editable_submission(update.effective_user.id) if update.effective_user else None
        if latest:
            submission_id = int(latest["id"])
            context.user_data["event_ocr_submission_id"] = submission_id
            if not field:
                fields = _fields(latest)
                missing = _missing(fields)
                if missing:
                    field = missing[0]
                    context.user_data["event_ocr_waiting_for"] = field
            logger.info(
                "Recovered Event OCR member state | submission=%s | user=%s | field=%s",
                submission_id,
                update.effective_user.id if update.effective_user else None,
                field,
            )

    if not submission_id or not field or not message.text:
        logger.info(
            "Ignored text with no active Event OCR state | user=%s | private=%s",
            update.effective_user.id if update.effective_user else None,
            is_private,
        )
        return

    row = _get_submission(int(submission_id))
    user = update.effective_user

    if (
        not row
        or not user
        or row["user_id"] != user.id
        or row["status"] not in {"member_input", "awaiting_confirmation"}
    ):
        context.user_data.pop("event_ocr_submission_id", None)
        context.user_data.pop("event_ocr_waiting_for", None)
        return

    value = message.text.strip()
    if not value:
        return

    fields = _fields(row)
    logger.info(
        "Event OCR member field received | submission=%s | user=%s | field=%s",
        submission_id,
        user.id,
        field,
    )
    fields[field] = value
    _update_submission(
        submission_id,
        fields=fields,
        status="member_input",
    )

    context.user_data.pop("event_ocr_waiting_for", None)
    if is_private:
        await _send_private_event_editor(
            context,
            user.id,
            int(submission_id),
        )
    else:
        await _prompt_next_missing(
            context,
            user.id,
            int(submission_id),
        )
    raise ApplicationHandlerStop


async def handle_event_member_callback(update, context):
    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    match = re.fullmatch(
        r"event_ocr_(edit|website|confirm)_(\d+)",
        query.data or "",
    )
    if not match:
        return

    submission_id = int(match.group(2))
    row = _get_submission(submission_id)

    if not row or row["user_id"] != user.id:
        await query.answer(
            "This Event submission is not yours.",
            show_alert=True,
        )
        return

    if row["status"] not in {"member_input", "awaiting_confirmation"}:
        await query.answer(
            "This submission is no longer editable.",
            show_alert=True,
        )
        return

    fields = _fields(row)

    if match.group(1) == "website":
        context.user_data["event_ocr_submission_id"] = submission_id
        context.user_data["event_ocr_waiting_for"] = "website"
        await query.answer()
        await query.message.reply_text(
            "🌐 <b>Website</b>\n\n"
            "OCR did not find a website on this flyer. "
            "Please enter the website manually. "
            "You can enter a full URL or a domain such as example.com.",
            parse_mode="HTML",
        )
        return

    if match.group(1) == "edit":
        context.user_data["event_ocr_submission_id"] = submission_id
        context.user_data["event_ocr_waiting_for"] = "event"
        await query.answer()
        if query.message.chat.type == "private":
            await query.message.reply_text(
                "✏️ <b>EDIT EVENT</b>\n\n"
                + _format_fields(fields)
                + "\n\nPlease enter the <b>Event Name</b>.",
                parse_mode="HTML",
            )
        else:
            await query.message.reply_text(
                "✏️ <b>EDIT EVENT</b>\n\n"
                "Please use the private Melanated AZ Bot chat to edit the Event.",
                parse_mode="HTML",
            )
        return

    missing = _missing(fields)
    if missing:
        context.user_data["event_ocr_submission_id"] = submission_id
        context.user_data["event_ocr_waiting_for"] = missing[0]
        await query.answer(
            "Some required information is still missing.",
            show_alert=True,
        )
        if query.message.chat.type == "private":
            await _send_private_event_editor(
                context,
                user.id,
                submission_id,
            )
        else:
            await _prompt_next_missing(
                context,
                user.id,
                submission_id,
            )
        return

    await query.answer("Submitting to admins...")
    ok = await _send_to_admins(context, submission_id)

    if not ok:
        await query.answer(
            "I couldn't send the Event to the admins. Please try again.",
            show_alert=True,
        )
        return

    context.user_data.pop("event_ocr_submission_id", None)
    context.user_data.pop("event_ocr_waiting_for", None)

    try:
        await query.message.edit_text(
            "✅ <b>EVENT SUBMITTED FOR ADMIN APPROVAL</b>\n\n"
            + _format_fields(fields)
            + "\n\nThe flyer is now with the admins. "
              "It will only be posted publicly if approved.",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ==========================================================
# ADMIN APPROVAL
# ==========================================================

async def handle_event_admin_callback(update, context):
    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    match = re.fullmatch(
        r"event_ocr_admin_(approve|deny)_(\d+)",
        query.data or "",
    )
    if not match:
        return

    try:
        from admin import is_admin

        if not await is_admin(user.id, context):
            await query.answer(
                "⛔ You are not authorized.",
                show_alert=True,
            )
            return
    except Exception:
        logger.exception("Independent Event admin authorization failed")
        await query.answer(
            "⛔ Unable to verify admin access.",
            show_alert=True,
        )
        return

    submission_id = int(match.group(2))
    row = _get_submission(submission_id)

    if not row or row["status"] != "pending_admin":
        await query.answer(
            "This Event has already been processed.",
            show_alert=True,
        )
        return

    fields = _fields(row)
    action = match.group(1)

    if action == "deny":
        _update_submission(submission_id, status="denied")
        await query.answer("Event denied.")

        try:
            await query.edit_message_text(
                "❌ <b>EVENT DENIED</b>\n\n"
                + _format_fields(fields),
                parse_mode="HTML",
            )
        except Exception:
            pass

        await _notify_submitter(
            context,
            row,
            "❌ Your Event flyer was not approved by the admins.",
        )
        return

    await query.answer("Publishing Event...")

    try:
        _update_submission(submission_id, status="approved")

        # Rebuild all approved Events in date order. This keeps the
        # Events topic sorted by event day rather than approval order.
        await _republish_events_in_date_order(context)

        try:
            await query.edit_message_text(
                "✅ <b>EVENT APPROVED & PUBLISHED</b>\n\n"
                + _format_fields(fields),
                parse_mode="HTML",
            )
        except Exception:
            pass

        await _notify_submitter(
            context,
            row,
            "✅ Your Event flyer was approved and posted in the Events topic.",
        )

        logger.info(
            "Independent Event approved | submission=%s",
            submission_id,
        )

    except Exception:
        logger.exception(
            "Independent Event publication failed | submission=%s",
            submission_id,
        )
        _update_submission(submission_id, status="pending_admin")
        await query.answer(
            "Publishing failed. Check the Render logs.",
            show_alert=True,
        )


async def _notify_submitter(context, row, text):
    try:
        await context.bot.send_message(
            chat_id=row["user_id"],
            text=text,
        )
    except TelegramError:
        logger.info(
            "Could not DM Event submitter | user_id=%s",
            row["user_id"],
        )


# ==========================================================
# CHRONOLOGICAL PUBLICATION
# ==========================================================

def _parse_event_date(raw):
    raw = str(raw or "").strip()
    if not raw:
        return None

    cleaned = re.sub(
        r"(st|nd|rd|th)",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    for fmt in (
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%m/%d/%y",
        "%m-%d-%y",
        "%B %d, %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%b %d %Y",
    ):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass

    # Handle OCR strings such as "September 18" by assuming the
    # current year. This is only a sort key; the displayed value is
    # never changed.
    for fmt in ("%B %d", "%b %d"):
        try:
            return datetime.strptime(
                f"{cleaned} {datetime.now().year}",
                f"{fmt} %Y",
            ).date()
        except ValueError:
            pass

    return None


def _sort_key(row):
    fields = _fields(row)
    parsed = _parse_event_date(fields.get("date"))

    if parsed is None:
        return (2, str(fields.get("date") or "").lower(), int(row["id"]))

    today = datetime.now().date()
    return (
        0 if parsed >= today else 1,
        parsed,
        int(row["id"]),
    )


def _approved_rows():
    with _db() as conn:
        return conn.execute(
            "SELECT * FROM event_submissions "
            "WHERE status='approved' ORDER BY id ASC"
        ).fetchall()


async def _republish_events_in_date_order(context):
    rows = sorted(_approved_rows(), key=_sort_key)

    if not rows:
        return

    # Delete only messages that this independent system previously
    # published. Nothing else in the Events topic is touched.
    for row in rows:
        old_id = row["published_message_id"]
        if not old_id:
            continue

        try:
            await context.bot.delete_message(
                chat_id=EVENT_CHAT_ID,
                message_id=int(old_id),
            )
        except TelegramError:
            logger.info(
                "Prior Event publication already gone | message=%s",
                old_id,
            )

    for row in rows:
        fields = _fields(row)
        caption = (
            "📅 <b>EVENT</b>\n\n"
            + _format_fields(fields)
        )

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

        _update_submission(
            row["id"],
            published_message_id=published.message_id,
        )

    logger.info(
        "Independent Events chronological rebuild complete | count=%s",
        len(rows),
    )


# ==========================================================
# INSTALLATION
# ==========================================================

def install_application(application):
    """Install ONLY the independent Event OCR handlers."""

    if getattr(application, "_melanated_event_ocr_installed", False):
        return

    _init_db()

    group = -30

    application.add_handler(
        CommandHandler(
            "start",
            handle_event_start,
        ),
        group=group,
    )

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_event_photo,
        ),
        group=group,
    )
    application.add_handler(
        MessageHandler(
            filters.VIDEO,
            handle_event_video,
        ),
        group=group,
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_event_text,
        ),
        group=group,
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_event_member_callback,
            pattern=r"^event_ocr_(?:edit|website|confirm)_\d+$",
        ),
        group=group,
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_event_admin_callback,
            pattern=r"^event_ocr_admin_(?:approve|deny)_\d+$",
        ),
        group=group,
    )

    application._melanated_event_ocr_installed = True

    logger.info(
        "INDEPENDENT EVENT OCR ACTIVE | chat=%s | topic=%s | "
        "admin_group=%s | handler_group=%s | dependency=NONE",
        EVENT_CHAT_ID,
        EVENT_TOPIC_ID,
        ADMIN_GROUP_ID,
        group,
    )