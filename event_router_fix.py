# Compatibility fix for the Events workflow.
# This patch is intentionally limited to the Events topic (12214).
# It keeps Event Name member-supplied, adds Price verification, and cleans
# temporary verification/reminder/reply messages after an event is approved.

import logging
import re
import sqlite3

from telegram.error import TelegramError

import event_router

logger = logging.getLogger("event_router_fix")

CLEANUP_TABLE = "event_cleanup_messages"

# Events now require: Event Name, Date, Time, Location, and Price.
event_router.FIELD_ORDER = ("event", "date", "time", "location", "price")
event_router.FIELD_LABELS = {
    "event": "🎉 Event",
    "date": "📅 Date",
    "time": "⏰ Time",
    "location": "📍 Location",
    "price": "💵 Price",
}


def _db():
    return event_router._db()


def _init_cleanup_db():
    with _db() as conn:
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {CLEANUP_TABLE} (
                submission_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                PRIMARY KEY (submission_id, message_id)
            )"""
        )
        conn.commit()


def _track_message(submission_id, message):
    if not submission_id or not message:
        return
    try:
        with _db() as conn:
            conn.execute(
                f"INSERT OR IGNORE INTO {CLEANUP_TABLE} (submission_id, message_id) VALUES (?, ?)",
                (int(submission_id), int(message.message_id)),
            )
            conn.commit()
    except Exception:
        logger.exception("Could not track Events cleanup message")


def _tracked_messages(submission_id):
    try:
        with _db() as conn:
            rows = conn.execute(
                f"SELECT message_id FROM {CLEANUP_TABLE} WHERE submission_id=?",
                (int(submission_id),),
            ).fetchall()
        return [int(row[0]) for row in rows]
    except Exception:
        logger.exception("Could not read Events cleanup messages")
        return []


def _clear_tracked_messages(submission_id):
    try:
        with _db() as conn:
            conn.execute(
                f"DELETE FROM {CLEANUP_TABLE} WHERE submission_id=?",
                (int(submission_id),),
            )
            conn.commit()
    except Exception:
        logger.exception("Could not clear Events cleanup messages")


async def _cleanup_after_approval(context, submission_id):
    """Delete only temporary bot/member workflow messages in Events topic.

    The approved flyer/event itself is intentionally NOT deleted.
    """
    message_ids = _tracked_messages(submission_id)
    if not message_ids:
        return

    deleted = 0
    for message_id in message_ids:
        try:
            await context.bot.delete_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_id=message_id,
            )
            deleted += 1
        except TelegramError:
            logger.info(
                "Events cleanup skipped message=%s submission=%s",
                message_id,
                submission_id,
            )
        except Exception:
            logger.exception(
                "Events cleanup failed message=%s submission=%s",
                message_id,
                submission_id,
            )

    _clear_tracked_messages(submission_id)
    logger.info(
        "Events workflow cleanup complete | submission=%s | deleted=%s",
        submission_id,
        deleted,
    )


def _extract_price(text):
    """Detect whether flyer/OCR text contains pricing.

    This function is intentionally only an OCR detector now. Manual member
    price entry is never replaced with the first detected dollar amount.
    """
    raw = str(text or "")

    if re.search(r"\b(?:free|no\s+cost|complimentary)\b", raw, re.IGNORECASE):
        return "Free"

    money = re.search(
        r"\$\s*\d+(?:\.\d{1,2})?|\b\d+(?:\.\d{1,2})?\s*(?:USD|dollars?)\b",
        raw,
        re.IGNORECASE,
    )
    if money:
        return money.group(0).strip()

    return None


def _member_required_parse_fields(text):
    fields = event_router._parse_fields_original(text)
    # Event Name must always be entered by the member.
    fields["event"] = None

    # Price must ALWAYS be entered by the member. Flyers can contain
    # multiple prices, discounts, promo codes, tables, headings, etc.
    # Never auto-fill Price from OCR because that would skip the private
    # Price prompt and reduce a structured pricing table to one amount.
    fields["price"] = None
    return fields


async def _ask_next_missing(update, context, submission_id, fields):
    """Events-only replacement that tracks every bot reminder/reply."""
    missing = event_router._missing(fields)
    if not missing:
        sent = await update.effective_message.reply_text(
            "🔎 <b>VERIFY EVENT INFORMATION</b>\n\n"
            + event_router._format_fields(fields)
            + "\n\nIf everything is correct, tap <b>CONFIRM &amp; SUBMIT</b>.",
            parse_mode="HTML",
            reply_markup=event_router._verification_keyboard(submission_id),
        )
        _track_message(submission_id, sent)
        return

    field = missing[0]
    context.user_data["event_waiting_for"] = field
    context.user_data["event_submission_id"] = submission_id
    sent = await update.effective_message.reply_text(
        "⚠️ <b>EVENT INFORMATION MISSING</b>\n\n"
        + event_router._format_fields(fields)
        + f"\n\nPlease provide the missing information:\n<b>{event_router.FIELD_LABELS[field]}</b>",
        parse_mode="HTML",
    )
    _track_message(submission_id, sent)


async def _process_media(update, context):
    message = update.effective_message
    if not message or message.chat_id != event_router.EVENT_CHAT_ID:
        return False
    if getattr(message, "message_thread_id", None) != event_router.EVENT_TOPIC_ID:
        return False
    if not message.photo and not message.video:
        return False

    user = update.effective_user
    if not user or user.is_bot:
        return True

    try:
        if message.photo:
            image_bytes, file_id, media_type = await event_router._download_photo(message)
            ocr_text = event_router._ocr_image(image_bytes)
        else:
            file_id = message.video.file_id
            media_type = "video"
            ocr_text = message.caption or ""
            thumbnail = getattr(message.video, "thumbnail", None)
            if thumbnail:
                try:
                    thumb_file = await thumbnail.get_file()
                    thumb_bytes = bytes(await thumb_file.download_as_bytearray())
                    thumb_text = event_router._ocr_image(thumb_bytes)
                    ocr_text = "\n".join(value for value in (thumb_text, ocr_text) if value)
                except Exception:
                    logger.exception("Event video thumbnail OCR failed")

        combined_text = "\n".join(value for value in (ocr_text, message.caption or "") if value)
        fields = _member_required_parse_fields(combined_text)
        submission_id = event_router._save_submission(user, message, media_type, file_id, fields)

        try:
            await message.delete()
        except TelegramError:
            logger.warning("Could not delete pending event flyer message %s", message.message_id)

        missing = event_router._missing(fields)
        if missing:
            missing_lines = "\n".join(f"❌ {event_router.FIELD_LABELS[key]}" for key in missing)
            reminder = await context.bot.send_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_thread_id=event_router.EVENT_TOPIC_ID,
                text=(
                    "⚠️ <b>EVENT INFORMATION MISSING</b>\n\n"
                    + event_router._format_fields(fields)
                    + "\n\n"
                    + missing_lines
                    + "\n\n"
                    + ("Please enter the <b>Event Name</b>. This must be provided by you." if "event" in missing else "Please provide the missing information.")
                ),
                parse_mode="HTML",
            )
            _track_message(submission_id, reminder)

            field = missing[0]
            context.user_data["event_submission_id"] = submission_id
            context.user_data["event_waiting_for"] = field
            prompt = await context.bot.send_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_thread_id=event_router.EVENT_TOPIC_ID,
                text=f"Please enter <b>{event_router.FIELD_LABELS[field]}</b> below.",
                parse_mode="HTML",
            )
            _track_message(submission_id, prompt)
        else:
            verify = await context.bot.send_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_thread_id=event_router.EVENT_TOPIC_ID,
                text=(
                    "🔎 <b>VERIFY EVENT INFORMATION</b>\n\n"
                    + event_router._format_fields(fields)
                    + "\n\nPlease verify the extracted information."
                ),
                parse_mode="HTML",
                reply_markup=event_router._verification_keyboard(submission_id),
            )
            _track_message(submission_id, verify)

        logger.info("Event flyer captured | submission=%s | user=%s | missing=%s", submission_id, user.id, missing)
        return True
    except Exception:
        logger.exception("Event submission processing failed")
        try:
            error_message = await context.bot.send_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_thread_id=event_router.EVENT_TOPIC_ID,
                text="⚠️ I couldn't process that flyer. Please resend it or include the Event, Date, Time, Location, and Price in the caption.",
            )
            if 'submission_id' in locals():
                _track_message(submission_id, error_message)
        except Exception:
            pass
        return True


async def _fixed_handle_event_photo(update, context):
    if await _process_media(update, context):
        from telegram.ext import ApplicationHandlerStop
        raise ApplicationHandlerStop


async def _fixed_handle_event_video(update, context):
    if await _process_media(update, context):
        from telegram.ext import ApplicationHandlerStop
        raise ApplicationHandlerStop


async def _tracked_handle_event_text(update, context):
    """Track the member's temporary reply, then let the existing handler work."""
    submission_id = context.user_data.get("event_submission_id")
    message = update.effective_message
    await event_router._original_handle_event_text(update, context)
    if submission_id and message and message.chat_id == event_router.EVENT_CHAT_ID and getattr(message, "message_thread_id", None) == event_router.EVENT_TOPIC_ID:
        _track_message(submission_id, message)


async def _tracked_handle_event_member_callback(update, context):
    submission_id = None
    query = update.callback_query
    if query and query.data:
        match = re.fullmatch(r"event_(?:edit|confirm)_(\d+)", query.data)
        if match:
            submission_id = int(match.group(1))

    await event_router._original_handle_event_member_callback(update, context)

    if submission_id and query and query.message:
        row = event_router._get_submission(submission_id)
        if row and row["status"] == "awaiting_confirmation":
            _track_message(submission_id, query.message)


async def _tracked_handle_event_admin_callback(update, context):
    query = update.callback_query
    data = query.data if query else ""
    match = re.fullmatch(r"event_admin_approve_(\d+)", data)
    submission_id = int(match.group(1)) if match else None

    await event_router._original_handle_event_admin_callback(update, context)

    if submission_id:
        row = event_router._get_submission(submission_id)
        if row and row["status"] == "approved":
            await _cleanup_after_approval(context, submission_id)


def install_application(application):
    _init_cleanup_db()

    if not hasattr(event_router, "_parse_fields_original"):
        event_router._parse_fields_original = event_router._parse_fields
    if not hasattr(event_router, "_original_handle_event_text"):
        event_router._original_handle_event_text = event_router.handle_event_text
    if not hasattr(event_router, "_original_handle_event_member_callback"):
        event_router._original_handle_event_member_callback = event_router.handle_event_member_callback
    if not hasattr(event_router, "_original_handle_event_admin_callback"):
        event_router._original_handle_event_admin_callback = event_router.handle_event_admin_callback

    event_router._parse_fields = _member_required_parse_fields
    event_router._process_media = _process_media
    event_router._ask_next_missing = _ask_next_missing
    event_router.handle_event_photo = _fixed_handle_event_photo
    event_router.handle_event_video = _fixed_handle_event_video
    event_router.handle_event_text = _tracked_handle_event_text
    event_router.handle_event_member_callback = _tracked_handle_event_member_callback
    event_router.handle_event_admin_callback = _tracked_handle_event_admin_callback
    event_router.install_application(application)
