# ==========================================================
# Melanated AZ Bot - Photo / Video Topic Router
# ==========================================================

import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, ContextTypes, MessageHandler, filters

import event_private_flow
import event_text_guard
import event_website_patch

logger = logging.getLogger("media_router")

MEDIA_CHAT_ID = -1002697105809
EVENT_TOPIC_ID = 12214


def install_application(application):
    """Install Event/OCR routing only.

    Event submissions are private and must be handled before bot.py's
    general media-spoiler handlers. This router does NOT move media to
    another topic and does NOT create an NSFW/media destination.
    """
    if getattr(application, "_melanated_media_router_installed", False):
        return

    event_website_patch.install()
    event_private_flow.install_application(application)
    event_text_guard.install_application(application)

    application._melanated_media_router_installed = True

    logger.info(
        "Event/OCR routing enabled | chat=%s | event_topic=%s | "
        "general media routing disabled",
        MEDIA_CHAT_ID,
        EVENT_TOPIC_ID,
    )


def install(bot_module):
    """Install Event/OCR routing when bot.py builds the application."""
    if getattr(bot_module, "_melanated_media_router_wrapped", False):
        return

    original_build_application = bot_module.build_application

    def wrapped_build_application(*args, **kwargs):
        application = original_build_application(*args, **kwargs)
        install_application(application)
        return application

    bot_module.build_application = wrapped_build_application
    bot_module._melanated_media_router_wrapped = True
