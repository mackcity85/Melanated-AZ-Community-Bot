# ==========================================================
# Melanated AZ Bot - Private Event Submission Flow
# ==========================================================

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, ContextTypes, MessageHandler, CallbackQueryHandler, filters

import event_router
import event_router_fix

logger = logging.getLogger("event_private_flow")

EVENT_CHAT_ID = event_router.EVENT_CHAT_ID
EVENT_TOPIC_ID = event_router.EVENT_TOPIC_ID


def _private_keyboard(submission_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ EDIT / FILL IN", callback_data=f"event_private_edit_{submission_id}")],
        [InlineKeyboardButton("✅ CONFIRM & SUBMIT", callback_data=f"event_private_confirm_{submission_id}")],
    ])


def _fields(row):
    return event_router._fields(row)


def _missing(fields):
    return event_router._missing(fields)


def _set_context(context, submission_id, field=None):
    context.user_data["event_private_submission_id"] = int(submission_id)
    if field:
        context.user_data["event_private_waiting_for"] = field
    else:
        context.user_data.pop("event_private_waiting_for", None)


def _clear_context(context):
    context.user_data.pop("event_private_submission_id", None)
    context.user_data.pop("event_private_waiting_for", None)


async def _send_private_form(context, user_id, submission_id, intro=False):
    row = event_router._get_submission(int(submission_id))
    if not row or row["user_id"] != user_id:
        return False

    if row["status"] not in {"member_input", "awaiting_confirmation"}:
        return False

    fields = _fields(row)
    _set_context(context, submission_id)

    if intro:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔒 <b>PRIVATE EVENT SUBMISSION</b>\n\n"
                "Your event information will be collected here privately. "
                "Nothing you enter will be posted in the group while you are filling it out.\n\n"
                "I will send the completed event to the admins for approval."
            ),
            parse_mode="HTML",
        )

    missing = _missing(fields)
    if missing:
        field = missing[0]
        _set_context(context, submission_id, field)
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔒 <b>EVENT INFORMATION</b>\n\n"
                + event_router._format_fields(fields)
                + f"\n\nPlease send the <b>{event_router.FIELD_LABELS[field]}</b>."
            ),
            parse_mode="HTML",
        )
    else:
        _set_context(context, submission_id)
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔎 <b>VERIFY YOUR EVENT</b>\n\n"
                + event_router._format_fields(fields)
                + "\n\nEverything is ready. Review it below, then confirm."
            ),
            parse_mode="HTML",
            reply_markup=_private_keyboard(submission_id),
        )

    return True


async def _send_start_link(context, user_id, submission_id):
    bot = await context.bot.get_me()
    username = bot.username
    if not username:
        raise RuntimeError("Bot username unavailable for Event private deep link")

    link = f"https://t.me/{username}?start=event_{submission_id}"
    message = await context.bot.send_message(
        chat_id=EVENT_CHAT_ID,
        message_thread_id=EVENT_TOPIC_ID,
        text=(
            "🔒 <b>PRIVATE EVENT SUBMISSION</b>\n\n"
            "I need you to open a private chat with me to finish your event submission.\n\n"
            "Tap the button below. Your Event, Date, Time, Location, and Price answers will only be visible to you and the bot."
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 OPEN PRIVATE EVENT FORM", url=link)]
        ]),
    )

    # event_router_fix already cleans tracked Events-topic workflow messages
    # after approval. Track this fallback notice so it is removed too.
    tracker = getattr(event_router_fix, "_track_message", None)
    if tracker:
        tracker(submission_id, message)

    return message


async def _process_group_media(update, context):
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
                    ocr_text = "\n".join(v for v in (thumb_text, ocr_text) if v)
                except Exception:
                    logger.exception("Event video thumbnail OCR failed")

        combined_text = "\n".join(v for v in (ocr_text, message.caption or "") if v)
        # event_router_fix installs the current Events parsing rules, including
        # Event Name being member-supplied and Price verification.
        fields = event_router._parse_fields(combined_text)
        submission_id = event_router._save_submission(user, message, media_type, file_id, fields)

        try:
            await message.delete()
        except TelegramError:
            logger.warning("Could not delete original Event submission message %s", message.message_id)

        try:
            await _send_private_form(context, user.id, submission_id, intro=True)
            logger.info("Private Event form started | submission=%s | user=%s", submission_id, user.id)
        except TelegramError:
            # First-time users may not have started the bot. Give them a deep
            # link in the Event topic; the answers still remain private.
            start_message = await _send_start_link(context, user.id, submission_id)
            logger.info("Event private deep link sent | submission=%s | message=%s", submission_id, start_message.message_id)
        except Exception:
            logger.exception("Could not start private Event form | submission=%s", submission_id)
            await _send_start_link(context, user.id, submission_id)

        return True
    except Exception:
        logger.exception("Private Event media processing failed")
        try:
            await context.bot.send_message(
                chat_id=EVENT_CHAT_ID,
                message_thread_id=EVENT_TOPIC_ID,
                text="⚠️ I couldn't process that event submission. Please resend the flyer.",
            )
        except Exception:
            pass
        return True


async def handle_group_photo(update, context):
    if await _process_group_media(update, context):
        raise ApplicationHandlerStop


async def handle_group_video(update, context):
    if await _process_group_media(update, context):
        raise ApplicationHandlerStop


async def _start_from_deep_link(update, context):
    message = update.effective_message
    if not message or not update.effective_user:
        return

    text = message.text or ""
    match = re.match(r"^/start(?:@\w+)?\s+event_(\d+)\s*$", text, re.IGNORECASE)
    if not match:
        return

    submission_id = int(match.group(1))
    row = event_router._get_submission(submission_id)
    if not row or row["user_id"] != update.effective_user.id:
        await message.reply_text("⚠️ That Event submission could not be found or does not belong to you.")
        raise ApplicationHandlerStop

    await _send_private_form(context, update.effective_user.id, submission_id, intro=True)
    raise ApplicationHandlerStop


async def handle_private_text(update, context):
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.text:
        return
    if message.chat.type != "private":
        return

    submission_id = context.user_data.get("event_private_submission_id")
    field = context.user_data.get("event_private_waiting_for")
    if not submission_id or not field:
        return

    row = event_router._get_submission(int(submission_id))
    if not row or row["user_id"] != user.id or row["status"] not in {"member_input", "awaiting_confirmation"}:
        _clear_context(context)
        return

    value = message.text.strip()
    if not value:
        await message.reply_text(f"Please provide a value for {event_router.FIELD_LABELS[field]}.")
        raise ApplicationHandlerStop

    fields = _fields(row)
    fields[field] = value
    event_router._update_submission(submission_id, fields=fields, status="member_input")

    missing = _missing(fields)
    if missing:
        _set_context(context, submission_id, missing[0])
        await message.reply_text(
            event_router._format_fields(fields)
            + f"\n\nPlease send the <b>{event_router.FIELD_LABELS[missing[0]]}</b>.",
            parse_mode="HTML",
        )
    else:
        _set_context(context, submission_id)
        event_router._update_submission(submission_id, status="awaiting_confirmation")
        await message.reply_text(
            "🔎 <b>VERIFY YOUR EVENT</b>\n\n"
            + event_router._format_fields(fields)
            + "\n\nIf everything is correct, tap <b>CONFIRM & SUBMIT</b>.",
            parse_mode="HTML",
            reply_markup=_private_keyboard(submission_id),
        )

    raise ApplicationHandlerStop


async def _submit_to_admin(context, submission_id, user_id):
    row = event_router._get_submission(int(submission_id))
    if not row or row["user_id"] != user_id:
        return False, "This Event submission is not yours."
    if row["status"] not in {"member_input", "awaiting_confirmation"}:
        return False, "This Event submission is no longer available."

    fields = _fields(row)
    missing = _missing(fields)
    if missing:
        return False, "Please complete all Event information first."

    submitter = f"@{row['username']}" if row["username"] else (row["first_name"] or str(row["user_id"]))
    caption = "🎟️ <b>EVENT FLYER — PENDING ADMIN APPROVAL</b>\n\nSubmitted by: " + submitter

    try:
        if row["media_type"] == "photo":
            media_message = await context.bot.send_photo(
                chat_id=event_router.ADMIN_GROUP_ID,
                photo=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )
        else:
            media_message = await context.bot.send_video(
                chat_id=event_router.ADMIN_GROUP_ID,
                video=row["file_id"],
                caption=caption,
                parse_mode="HTML",
            )

        details = await context.bot.send_message(
            chat_id=event_router.ADMIN_GROUP_ID,
            text=(
                "🔎 <b>EVENT SUBMISSION</b>\n\n"
                + event_router._format_fields(fields)
                + f"\n\nSubmitted by: {submitter}"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ APPROVE", callback_data=f"event_admin_approve_{submission_id}"),
                    InlineKeyboardButton("❌ DENY", callback_data=f"event_admin_deny_{submission_id}"),
                ]
            ]),
        )

        event_router._update_submission(
            submission_id,
            status="pending_admin",
            admin_message_id=media_message.message_id,
            admin_details_message_id=details.message_id,
        )
        return True, None
    except Exception:
        logger.exception("Could not send Event submission to admin group")
        return False, "I couldn't send the Event to the admins. Please try again."


async def handle_private_callback(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    match = re.fullmatch(r"event_private_(edit|confirm)_(\d+)", query.data or "")
    if not match:
        return

    submission_id = int(match.group(2))
    row = event_router._get_submission(submission_id)
    if not row or row["user_id"] != user.id:
        await query.answer("This Event submission is not yours.", show_alert=True)
        raise ApplicationHandlerStop

    action = match.group(1)

    if action == "edit":
        fields = _fields(row)
        _set_context(context, submission_id, "event")
        await query.answer()
        await query.message.reply_text(
            "✏️ <b>EDIT EVENT</b>\n\n"
            + event_router._format_fields(fields)
            + "\n\nPlease enter the <b>Event Name</b>.",
            parse_mode="HTML",
        )
        raise ApplicationHandlerStop

    ok, error = await _submit_to_admin(context, submission_id, user.id)
    if not ok:
        await query.answer(error, show_alert=True)
        raise ApplicationHandlerStop

    event_router._update_submission(submission_id, status="pending_admin")
    _clear_context(context)
    await query.answer("Submitted to the admins for approval.")
    await query.message.edit_text(
        "✅ <b>EVENT SUBMITTED</b>\n\n"
        "Your event has been sent to the admins for approval.\n"
        "You will not see the admin review, and your form responses were kept private.",
        parse_mode="HTML",
    )
    raise ApplicationHandlerStop


def install_application(application):
    """Install private Event handlers before the existing Events handlers."""
    if getattr(application, "_melanated_private_event_flow_installed", False):
        return

    # Register these handlers first. The existing Events compatibility layer
    # is installed immediately afterward and continues to own admin approval
    # and public publication.
    application.add_handler(
        MessageHandler(filters.PHOTO, handle_group_photo),
        group=0,
    )
    application.add_handler(
        MessageHandler(filters.VIDEO, handle_group_video),
        group=0,
    )
    application.add_handler(
        MessageHandler(filters.Regex(r"^/start(?:@\w+)?\s+event_\d+\s*$"), _start_from_deep_link),
        group=0,
    )
    application.add_handler(
        CallbackQueryHandler(handle_private_callback, pattern=r"^event_private_(?:edit|confirm)_\d+$"),
        group=0,
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_private_text),
        group=0,
    )

    event_router_fix.install_application(application)
    application._melanated_private_event_flow_installed = True
    logger.info("Private Event submission flow enabled | topic=%s", EVENT_TOPIC_ID)
