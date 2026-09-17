# Compatibility fix for the Events workflow.
# Patches the initial flyer-processing step so the member correction flow
# does not attempt to replace Update.effective_message (a read-only property).

import logging

from telegram.error import TelegramError

import event_router

logger = logging.getLogger("event_router_fix")


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
                    ocr_text = "\n".join(
                        value for value in (thumb_text, ocr_text) if value
                    )
                except Exception:
                    logger.exception("Event video thumbnail OCR failed")

        combined_text = "\n".join(
            value for value in (ocr_text, message.caption or "") if value
        )
        fields = event_router._parse_fields(combined_text)
        submission_id = event_router._save_submission(
            user, message, media_type, file_id, fields
        )

        try:
            await message.delete()
        except TelegramError:
            logger.warning(
                "Could not delete pending event flyer message %s",
                message.message_id,
            )

        missing = event_router._missing(fields)
        if missing:
            missing_lines = "\n".join(
                f"❌ {event_router.FIELD_LABELS[key]}"
                for key in missing
            )
            await context.bot.send_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_thread_id=event_router.EVENT_TOPIC_ID,
                text=(
                    "⚠️ <b>EVENT INFORMATION MISSING</b>\n\n"
                    + event_router._format_fields(fields)
                    + "\n\n"
                    + missing_lines
                    + "\n\nPlease provide the missing information."
                ),
                parse_mode="HTML",
            )
            field = missing[0]
            context.user_data["event_submission_id"] = submission_id
            context.user_data["event_waiting_for"] = field
            await context.bot.send_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_thread_id=event_router.EVENT_TOPIC_ID,
                text=f"Please enter <b>{event_router.FIELD_LABELS[field]}</b> below.",
                parse_mode="HTML",
            )
        else:
            await context.bot.send_message(
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

        logger.info(
            "Event flyer captured | submission=%s | user=%s | missing=%s",
            submission_id,
            user.id,
            missing,
        )
        return True
    except Exception:
        logger.exception("Event submission processing failed")
        try:
            await context.bot.send_message(
                chat_id=event_router.EVENT_CHAT_ID,
                message_thread_id=event_router.EVENT_TOPIC_ID,
                text=(
                    "⚠️ I couldn't process that flyer. Please resend it or include "
                    "the Event, Date, Time, and Location in the caption."
                ),
            )
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


def install_application(application):
    event_router._process_media = _process_media
    event_router.handle_event_photo = _fixed_handle_event_photo
    event_router.handle_event_video = _fixed_handle_event_video
    event_router.install_application(application)
