# ==========================================================
# Melanated AZ Bot - PRIVATE Event Submission Flow
# ==========================================================
# Members never fill out Event information in the public Events topic.
# They open the bot privately, upload the flyer, and complete everything
# in the bot DM. Only the final admin-approved Event is published publicly.
# ==========================================================

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import event_router
import event_router_fix

logger = logging.getLogger("event_private_flow")

EVENT_CHAT_ID = event_router.EVENT_CHAT_ID
EVENT_TOPIC_ID = event_router.EVENT_TOPIC_ID
PRIVATE_MODE_KEY = "event_private_mode"
SUBMISSION_KEY = "event_private_submission_id"
WAITING_KEY = "event_private_waiting_for"


def _fields(row):
    return event_router._fields(row)


def _missing(fields):
    return event_router._missing(fields)


def _set_context(context, submission_id=None, field=None):
    if submission_id is not None:
        context.user_data[SUBMISSION_KEY] = int(submission_id)
    if field:
        context.user_data[WAITING_KEY] = field
    else:
        context.user_data.pop(WAITING_KEY, None)


def _clear_context(context):
    context.user_data.pop(PRIVATE_MODE_KEY, None)
    context.user_data.pop(SUBMISSION_KEY, None)
    context.user_data.pop(WAITING_KEY, None)


def _private_keyboard(submission_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ EDIT / FILL IN", callback_data=f"event_private_edit_{submission_id}")],
        [InlineKeyboardButton("✅ CONFIRM & SUBMIT", callback_data=f"event_private_confirm_{submission_id}")],
    ])


async def _send_private_start(context, user_id):
    context.user_data[PRIVATE_MODE_KEY] = "awaiting_flyer"
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🔒 <b>PRIVATE EVENT SUBMISSION</b>\n\n"
            "Your Event submission is private from start to finish.\n\n"
            "📎 <b>Send me the Event flyer/photo/video here.</b>\n\n"
            "Then I will collect the Event Name, Date, Time, Location, Price, and optional Website here in this private chat.\n\n"
            "Nothing you enter will be posted in the Events topic while you are filling it out."
        ),
        parse_mode="HTML",
    )


async def start_private_event(update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    if not message or not user or user.is_bot:
        return
    if message.chat.type != "private":
        try:
            await message.delete()
        except TelegramError:
            pass
        raise ApplicationHandlerStop
    _clear_context(context)
    await _send_private_start(context, user.id)
    raise ApplicationHandlerStop


async def handle_private_start(update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return
    if not re.match(r"^/start(?:@\w+)?\s+event\s*$", message.text, re.IGNORECASE):
        return
    await start_private_event(update, context)


async def _run_ocr(image_bytes, source):
    if not image_bytes:
        logger.warning("Private Event OCR skipped: no image bytes | source=%s", source)
        return ""
    try:
        text = event_router._ocr_image(image_bytes) or ""
        text = str(text).strip()
        logger.info(
            "Private Event OCR complete | source=%s | chars=%s | lines=%s",
            source, len(text), len(text.splitlines()) if text else 0,
        )
        if not text:
            logger.warning("Private Event OCR returned no text | source=%s", source)
        return text
    except Exception:
        logger.exception("Private Event OCR failed | source=%s", source)
        return ""


async def _save_private_media(update, context):
    message = update.effective_message
    user = update.effective_user
    if not message or not user or user.is_bot or message.chat.type != "private":
        return False
    if context.user_data.get(PRIVATE_MODE_KEY) != "awaiting_flyer":
        return False
    if not message.photo and not message.video:
        return False

    try:
        if message.photo:
            image_bytes, file_id, media_type = await event_router._download_photo(message)
            ocr_text = await _run_ocr(image_bytes, "photo")
        else:
            file_id = message.video.file_id
            media_type = "video"
            ocr_text = message.caption or ""
            thumbnail = getattr(message.video, "thumbnail", None)
            if thumbnail:
                try:
                    thumb_file = await thumbnail.get_file()
                    thumb_bytes = bytes(await thumb_file.download_as_bytearray())
                    thumb_text = await _run_ocr(thumb_bytes, "video-thumbnail")
                    ocr_text = "\n".join(v for v in (thumb_text, ocr_text) if v)
                except Exception:
                    logger.exception("Private Event video thumbnail OCR failed")

        combined_text = "\n".join(v for v in (ocr_text, message.caption or "") if v)

        try:
            if hasattr(event_router_fix, "_member_required_parse_fields"):
                fields = event_router_fix._member_required_parse_fields(combined_text)
            else:
                fields = event_router._parse_fields(combined_text)
        except Exception:
            logger.exception("Private Event field parsing failed; using blank fields")
            fields = {}

        for key in event_router.FIELD_ORDER:
            fields.setdefault(key, None)

        submission_id = event_router._save_submission(
            user, message, media_type, file_id, fields, status="member_input"
        )

        _set_context(context, submission_id)
        context.user_data[PRIVATE_MODE_KEY] = "filling"
        await _send_next_private_field(context, user.id, submission_id)

        logger.info(
            "Private Event flyer captured | submission=%s | user=%s | ocr_chars=%s | fields=%s | missing=%s",
            submission_id, user.id, len(combined_text), fields, _missing(fields),
        )
        return True

    except Exception:
        logger.exception("Private Event flyer processing failed")
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "⚠️ I couldn't save that flyer. Please send the flyer again here.\n\n"
                "If OCR cannot read the flyer, I will still ask you for the missing Event information manually."
            ),
        )
        return True


async def handle_private_photo(update, context):
    if await _save_private_media(update, context):
        raise ApplicationHandlerStop


async def handle_private_video(update, context):
    if await _save_private_media(update, context):
        raise ApplicationHandlerStop


async def _send_next_private_field(context, user_id, submission_id):
    row = event_router._get_submission(int(submission_id))
    if not row or row["user_id"] != user_id:
        logger.warning("Private Event submission lookup failed | submission=%s | user=%s", submission_id, user_id)
        return False

    fields = _fields(row)
    missing = _missing(fields)

    logger.info("Private Event field collection | submission=%s | fields=%s | missing=%s", submission_id, fields, missing)

    if not missing:
        _set_context(context, submission_id)
        event_router._update_submission(submission_id, status="awaiting_confirmation")
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔎 <b>VERIFY YOUR EVENT</b>\n\n"
                + event_router._format_fields(fields)
                + "\n\nEverything is ready. Review it and tap <b>CONFIRM &amp; SUBMIT</b>."
            ),
            parse_mode="HTML",
            reply_markup=_private_keyboard(submission_id),
        )
        return True

    field = missing[0]
    _set_context(context, submission_id, field)
    label = event_router.FIELD_LABELS.get(field, field.title())

    prompts = {
        "event": "🎉 <b>Event Name</b>\n\nPlease enter the name/title of the Event.",
        "date": "📅 <b>Date</b>\n\nPlease enter the Event date.",
        "time": "⏰ <b>Time</b>\n\nPlease enter the Event start time (and end time if applicable).",
        "location": "📍 <b>Location</b>\n\nPlease enter the Event venue/location.",
        "price": (
            "💵 <b>Price</b>\n\n"
            "Please enter the <b>full pricing information</b>. You can paste multiple prices, "
            "early-bird discounts, promo codes, headings, or a pricing table exactly as provided.\n\n"
            "If the Event is free, type <b>Free</b>."
        ),
        "website": "🌐 <b>Website</b>\n\nSend the website/registration link, or type <b>NO WEBSITE</b>.",
    }

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🔒 <b>PRIVATE EVENT INFORMATION</b>\n\n"
            + event_router._format_fields(fields)
            + "\n\n"
            + prompts.get(field, f"Please send the <b>{label}</b>.")
        ),
        parse_mode="HTML",
    )
    return True


async def handle_private_text(update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.text or message.chat.type != "private":
        return

    mode = context.user_data.get(PRIVATE_MODE_KEY)
    if mode not in {"awaiting_flyer", "filling"}:
        return

    if mode == "awaiting_flyer":
        await message.reply_text("🔒 This Event submission is private. Please send the Event flyer/photo/video here first.")
        raise ApplicationHandlerStop

    submission_id = context.user_data.get(SUBMISSION_KEY)
    field = context.user_data.get(WAITING_KEY)
    if not submission_id or not field:
        return

    row = event_router._get_submission(int(submission_id))
    if not row or row["user_id"] != user.id or row["status"] not in {"member_input", "awaiting_confirmation"}:
        _clear_context(context)
        return

    value = message.text.strip()
    if not value:
        await message.reply_text(f"Please provide {event_router.FIELD_LABELS.get(field, field)}.")
        raise ApplicationHandlerStop

    if field == "website":
        if value.lower() in {"none", "no", "n/a", "na", "skip", "no website", "no website / skip"}:
            value = "No website provided"
        elif re.match(r"^www\.", value, re.IGNORECASE):
            value = "https://" + value
        elif not re.match(r"^https?://", value, re.IGNORECASE):
            await message.reply_text("Please send a complete link starting with https:// or http://, or type NO WEBSITE.")
            raise ApplicationHandlerStop

    fields = _fields(row)
    fields[field] = value
    event_router._update_submission(submission_id, fields=fields, status="member_input")
    await _send_next_private_field(context, user.id, int(submission_id))
    raise ApplicationHandlerStop


async def handle_private_callback(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    if not query or not user or not query.message or query.message.chat.type != "private":
        return

    data = query.data or ""
    if data == "event_private_start":
        await query.answer()
        _clear_context(context)
        await _send_private_start(context, user.id)
        raise ApplicationHandlerStop

    match = re.fullmatch(r"event_private_(edit|confirm)_(\d+)", data)
    if not match:
        return

    submission_id = int(match.group(2))
    row = event_router._get_submission(submission_id)
    if not row or row["user_id"] != user.id:
        await query.answer("This Event submission is not yours.", show_alert=True)
        raise ApplicationHandlerStop

    if match.group(1) == "edit":
        _set_context(context, submission_id, "event")
        context.user_data[PRIVATE_MODE_KEY] = "filling"
        await query.answer()
        await query.message.reply_text(
            "✏️ <b>EDIT EVENT</b>\n\n" + event_router._format_fields(_fields(row)) + "\n\nPlease enter the <b>Event Name</b>.",
            parse_mode="HTML",
        )
        raise ApplicationHandlerStop

    ok, error = await _submit_to_admin(context, submission_id, user.id)
    if not ok:
        await query.answer(error, show_alert=True)
        raise ApplicationHandlerStop

    _clear_context(context)
    await query.answer("Submitted to the admins for approval.")
    await query.message.edit_text(
        "✅ <b>EVENT SUBMITTED</b>\n\nYour Event has been sent to the admins for approval.\nEverything you entered was kept private. Nothing was posted in the Events topic.",
        parse_mode="HTML",
    )
    raise ApplicationHandlerStop


async def _submit_to_admin(context, submission_id, user_id):
    row = event_router._get_submission(int(submission_id))
    if not row or row["user_id"] != user_id:
        return False, "This Event submission is not yours."
    if row["status"] not in {"member_input", "awaiting_confirmation"}:
        return False, "This Event submission is no longer available."

    fields = _fields(row)
    if _missing(fields):
        return False, "Please complete all Event information first."

    submitter = f"@{row['username']}" if row["username"] else (row["first_name"] or str(row["user_id"]))
    caption = "🎟️ <b>EVENT FLYER — PENDING ADMIN APPROVAL</b>\n\nSubmitted by: " + submitter

    try:
        if row["media_type"] == "photo":
            media_message = await context.bot.send_photo(chat_id=event_router.ADMIN_GROUP_ID, photo=row["file_id"], caption=caption, parse_mode="HTML")
        else:
            media_message = await context.bot.send_video(chat_id=event_router.ADMIN_GROUP_ID, video=row["file_id"], caption=caption, parse_mode="HTML")

        details = await context.bot.send_message(
            chat_id=event_router.ADMIN_GROUP_ID,
            text=("🔎 <b>EVENT SUBMISSION</b>\n\n" + event_router._format_fields(fields) + f"\n\nSubmitted by: {submitter}"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ APPROVE", callback_data=f"event_admin_approve_{submission_id}"),
                    InlineKeyboardButton("❌ DENY", callback_data=f"event_admin_deny_{submission_id}"),
                ]
            ]),
        )
        event_router._update_submission(submission_id, status="pending_admin", admin_message_id=media_message.message_id, admin_details_message_id=details.message_id)
        return True, None
    except Exception:
        logger.exception("Could not send private Event submission to admin group")
        return False, "I couldn't send the Event to the admins. Please try again."


def _remove_public_event_handlers(application):
    for group, handlers in list(application.handlers.items()):
        kept = []
        for handler in handlers:
            callback = getattr(handler, "callback", None)
            module = getattr(callback, "__module__", "")
            name = getattr(callback, "__name__", "")
            if module == "event_router" and name in {"handle_event_photo", "handle_event_video", "handle_event_text"}:
                continue
            kept.append(handler)
        application.handlers[group] = kept


async def block_public_event_media(update, context):
    """If someone posts an Event flyer publicly, remove it and give them the private submission entry point."""
    message = update.effective_message
    user = update.effective_user
    if not message or message.chat_id != EVENT_CHAT_ID:
        return
    if getattr(message, "message_thread_id", None) != EVENT_TOPIC_ID:
        return
    if not message.photo and not message.video:
        return

    try:
        await message.delete()
    except TelegramError:
        pass

    try:
        bot = await context.bot.get_me()
        if bot.username:
            link = f"https://t.me/{bot.username}?start=event"
            prompt = await context.bot.send_message(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                text=(
                    f"🔒 <b>{user.mention_html()}</b>, Event submissions are private.\n\n"
                    "Please use the button below to open a private chat with the bot and submit your flyer there."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔒 SUBMIT EVENT PRIVATELY", url=link)]
                ]),
            )
            if context.job_queue:
                context.job_queue.run_once(
                    _delete_public_prompt,
                    when=120,
                    data={"chat_id": prompt.chat_id, "message_id": prompt.message_id},
                    name=f"event-private-prompt:{prompt.message_id}",
                )
    except Exception:
        logger.exception("Could not send private Event submission prompt")

    raise ApplicationHandlerStop


async def _delete_public_prompt(context):
    data = context.job.data or {}
    try:
        await context.bot.delete_message(chat_id=data.get("chat_id"), message_id=data.get("message_id"))
    except Exception:
        pass


def install_application(application):
    """Enable private Event submissions and leave only admin approval public."""
    if getattr(application, "_melanated_private_event_flow_installed", False):
        return

    event_router.install_application(application)
    _remove_public_event_handlers(application)

    application.add_handler(MessageHandler(filters.PHOTO, block_public_event_media), group=-10)
    application.add_handler(MessageHandler(filters.VIDEO, block_public_event_media), group=-10)
    application.add_handler(CommandHandler("event", start_private_event), group=-5)
    application.add_handler(
        MessageHandler(filters.Regex(r"^/start(?:@\w+)?\s+event\s*$"), handle_private_start),
        group=-5,
    )
    application.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_private_photo), group=-4)
    application.add_handler(MessageHandler(filters.VIDEO & filters.ChatType.PRIVATE, handle_private_video), group=-4)
    application.add_handler(
        CallbackQueryHandler(handle_private_callback, pattern=r"^(?:event_private_start|event_private_(?:edit|confirm)_\d+)$"),
        group=-4,
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_private_text),
        group=-4,
    )
    application._melanated_private_event_flow_installed = True
    logger.info("PRIVATE Event submission flow enabled | topic=%s", EVENT_TOPIC_ID)
