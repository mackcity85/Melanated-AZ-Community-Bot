# ==========================================================
# Melanated AZ Bot - Event OCR Workflow
# ==========================================================
# Clean Event workflow entry point.
# Reuses the existing event_router functions for:
#   - Event-topic flyer interception
#   - OCR extraction
#   - Missing-field prompts
#   - Member confirmation/editing
#   - Admin approval / denial
#   - Approved Event publication
#   - Chronological Event-topic ordering
#
# This module exists so Event OCR is installed directly and
# independently of the general media spoiler moderation.
# ==========================================================

import logging

from telegram.ext import CallbackQueryHandler, MessageHandler, filters

import event_router

logger = logging.getLogger("event_ocr")

EVENT_HANDLER_GROUP = -30


def install_application(application):
    """Install the Event OCR workflow before general media moderation."""
    if getattr(application, "_melanated_event_ocr_installed", False):
        return

    # Initialize the existing Event database and publication tracking.
    event_router._init_db()
    try:
        event_router._ensure_published_message_column()
    except Exception:
        logger.exception("Could not initialize Event publication tracking.")

    # These handlers intentionally run at -30.
    # bot.py's normal spoiler moderation runs at group 5.
    # Event flyers therefore reach OCR first and stop there.
    application.add_handler(
        MessageHandler(filters.PHOTO, event_router.handle_event_photo),
        group=EVENT_HANDLER_GROUP,
    )
    application.add_handler(
        MessageHandler(filters.VIDEO, event_router.handle_event_video),
        group=EVENT_HANDLER_GROUP,
    )

    # Handles missing Event fields entered after OCR.
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            event_router.handle_event_text,
        ),
        group=EVENT_HANDLER_GROUP,
    )

    # Member confirmation/edit controls.
    application.add_handler(
        CallbackQueryHandler(
            event_router.handle_event_member_callback,
            pattern=r"^event_(?:edit|confirm)_\d+$",
        ),
        group=EVENT_HANDLER_GROUP,
    )

    # Admin approval/denial controls.
    application.add_handler(
        CallbackQueryHandler(
            event_router.handle_event_admin_callback,
            pattern=r"^event_admin_(?:approve|deny)_\d+$",
        ),
        group=EVENT_HANDLER_GROUP,
    )

    application._melanated_event_ocr_installed = True

    logger.info(
        "NEW EVENT OCR WORKFLOW ACTIVE | chat=%s | topic=%s | admin_group=%s | handler_group=%s",
        event_router.EVENT_CHAT_ID,
        event_router.EVENT_TOPIC_ID,
        event_router.ADMIN_GROUP_ID,
        EVENT_HANDLER_GROUP,
    )
