# ==========================================================
# Melanated AZ Bot - Notification / Clean Chat Policy
# ==========================================================
#
# Central policy for bot-generated notifications in the main
# community chat.
#
# - Mirrors bot notifications to ADMIN_GROUP_ID.
# - Automatically removes temporary bot messages from the
#   main community chat after CLEAN_CHAT_SECONDS.
# - Never removes the permanent Games or Introduction launchers.
# - Never mirrors/deletes messages already sent to the admin group.
#
# This patches ExtBot.send_message once at import time so existing
# modules do not need to be rewritten one-by-one.
# ==========================================================

import asyncio
import logging
import os
from functools import wraps

from telegram.error import TelegramError
from telegram.ext import ExtBot

logger = logging.getLogger("melanated_az.notification_policy")

CLEAN_CHAT_SECONDS = int(os.environ.get("CLEAN_CHAT_SECONDS", "180") or "180")
ADMIN_GROUP_ID_ENV = os.environ.get("ADMIN_GROUP_ID", "") or ""
MAIN_GROUP_ID_ENV = os.environ.get("MAIN_GROUP_ID", "") or ""

# Permanent forum launchers. These must remain in place.
PERMANENT_TOPIC_IDS = {
    8809,   # Games
    11570,  # Introduction
}

_PATCHED = False
_ORIGINAL_SEND_MESSAGE = None


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _admin_group_id():
    return _as_int(ADMIN_GROUP_ID_ENV, 0)


def _main_group_id():
    return _as_int(MAIN_GROUP_ID_ENV, 0)


def _is_main_chat(chat_id):
    main_id = _main_group_id()
    return bool(main_id and _as_int(chat_id) == main_id)


def _is_admin_chat(chat_id):
    admin_id = _admin_group_id()
    return bool(admin_id and _as_int(chat_id) == admin_id)


def _is_permanent_launcher(kwargs):
    topic_id = kwargs.get("message_thread_id")
    return _as_int(topic_id, 0) in PERMANENT_TOPIC_IDS


def _clean_admin_copy_kwargs(kwargs):
    """Remove main-chat-only routing/reply fields before mirroring."""
    copy = dict(kwargs)
    copy.pop("chat_id", None)
    copy.pop("message_thread_id", None)
    copy.pop("reply_to_message_id", None)
    copy.pop("reply_parameters", None)
    copy.pop("allow_sending_without_reply", None)
    return copy


async def _delete_later(bot, chat_id, message_id):
    if CLEAN_CHAT_SECONDS <= 0:
        return

    await asyncio.sleep(CLEAN_CHAT_SECONDS)

    try:
        await _ORIGINAL_SEND_MESSAGE.__self__.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
    except TelegramError as exc:
        logger.debug(
            "Temporary bot message could not be removed | chat=%s | message=%s | %s",
            chat_id,
            message_id,
            exc,
        )
    except Exception:
        logger.exception(
            "Unexpected clean-chat failure | chat=%s | message=%s",
            chat_id,
            message_id,
        )


async def _send_message_with_policy(self, *args, **kwargs):
    """Send normally, mirror to admins, and clean temporary main-chat posts."""
    sent = await _ORIGINAL_SEND_MESSAGE(self, *args, **kwargs)

    chat_id = kwargs.get("chat_id")
    if chat_id is None and args:
        # ExtBot.send_message's first positional argument is chat_id.
        chat_id = args[0]

    if not _is_main_chat(chat_id) or _is_admin_chat(chat_id):
        return sent

    permanent = _is_permanent_launcher(kwargs)

    # Mirror the notification to the admin group. The permanent launchers
    # are intentionally not duplicated into the admin chat.
    admin_id = _admin_group_id()
    if admin_id and not permanent:
        try:
            admin_kwargs = _clean_admin_copy_kwargs(kwargs)
            await _ORIGINAL_SEND_MESSAGE(
                self,
                chat_id=admin_id,
                **admin_kwargs,
            )
        except TelegramError:
            logger.exception(
                "Could not mirror bot notification to ADMIN_GROUP_ID=%s",
                admin_id,
            )
        except Exception:
            logger.exception("Unexpected admin notification mirror failure.")

    # Temporary main-chat notifications are removed automatically.
    # Permanent Games/Introduction launchers are left alone.
    if not permanent and CLEAN_CHAT_SECONDS > 0:
        try:
            asyncio.create_task(
                _delete_message_later(
                    self,
                    chat_id,
                    sent.message_id,
                )
            )
        except Exception:
            logger.exception("Could not schedule clean-chat deletion.")

    return sent


async def _delete_message_later(bot, chat_id, message_id):
    await asyncio.sleep(CLEAN_CHAT_SECONDS)
    try:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
        logger.debug(
            "Clean-chat removed bot message | chat=%s | message=%s",
            chat_id,
            message_id,
        )
    except TelegramError as exc:
        logger.debug(
            "Clean-chat deletion skipped | chat=%s | message=%s | %s",
            chat_id,
            message_id,
            exc,
        )
    except Exception:
        logger.exception(
            "Unexpected clean-chat deletion failure | chat=%s | message=%s",
            chat_id,
            message_id,
        )


def install_notification_policy():
    global _PATCHED, _ORIGINAL_SEND_MESSAGE

    if _PATCHED:
        return

    _ORIGINAL_SEND_MESSAGE = ExtBot.send_message
    ExtBot.send_message = _send_message_with_policy
    _PATCHED = True

    logger.info(
        "Clean-chat policy enabled | delete_after=%ss | main_group=%s | admin_group=%s | permanent_topics=%s",
        CLEAN_CHAT_SECONDS,
        _main_group_id(),
        _admin_group_id(),
        sorted(PERMANENT_TOPIC_IDS),
    )


install_notification_policy()
