# ==========================================================
# Melanated AZ - Raffle Pin Manager
# ==========================================================
# Keeps exactly one active raffle pinned in the Games topic.
# The active raffle post itself is the pinned entry point.
# Temporary "NEW RAFFLE IS LIVE" notifications are never pinned.
# When the raffle is no longer active, its pinned post is unpinned
# and removed so the next raffle can take its place.
# ==========================================================

import functools
import json
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from telegram.error import TelegramError

from games.game_center import GAMES_CHAT_ID, GAMES_TOPIC_ID
from raffle_database import get_active_raffle, get_approved_entries, close_raffle

logger = logging.getLogger("melanatedaz.raffle_pin_manager")

RAFFLE_STATE_FILE = Path(
    os.environ.get("RAFFLE_PIN_STATE_FILE", "/var/data/raffle_pin.json")
)


def _main_group_id():
    try:
        return int(
            os.environ.get("MAIN_GROUP_ID", str(GAMES_CHAT_ID))
            or str(GAMES_CHAT_ID)
        )
    except (TypeError, ValueError):
        return GAMES_CHAT_ID


def _load_state():
    try:
        data = json.loads(RAFFLE_STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        raffle_id = int(data.get("raffle_id", 0))
        message_id = int(data.get("message_id", 0))
        chat_id = int(data.get("chat_id", 0))
        if raffle_id > 0 and message_id > 0 and chat_id:
            return {
                "raffle_id": raffle_id,
                "message_id": message_id,
                "chat_id": chat_id,
            }
    except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return None


def _save_state(raffle_id, chat_id, message_id):
    try:
        RAFFLE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = RAFFLE_STATE_FILE.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                {
                    "raffle_id": int(raffle_id),
                    "chat_id": int(chat_id),
                    "message_id": int(message_id),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        temp.replace(RAFFLE_STATE_FILE)
    except OSError:
        logger.exception("Could not save raffle pin state.")


def _clear_state():
    try:
        RAFFLE_STATE_FILE.unlink(missing_ok=True)
    except OSError:
        logger.exception("Could not clear raffle pin state.")


async def _remove_pinned_raffle(context, state=None):
    state = state or _load_state()
    if not state:
        return

    chat_id = state["chat_id"]
    message_id = state["message_id"]

    try:
        await context.bot.unpin_chat_message(
            chat_id=chat_id,
            message_id=message_id,
        )
    except TelegramError:
        logger.debug(
            "Raffle post was already unpinned or could not be unpinned | chat=%s message=%s",
            chat_id,
            message_id,
        )

    try:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
    except TelegramError:
        logger.debug(
            "Raffle post was already deleted or could not be deleted | chat=%s message=%s",
            chat_id,
            message_id,
        )

    _clear_state()
    logger.info(
        "Active raffle pin removed | raffle=%s | chat=%s | message=%s",
        state["raffle_id"],
        chat_id,
        message_id,
    )


async def _remove_legacy_raffle_notification_pin(context):
    """Remove the old main-chat notification pin created by older raffle.py."""
    chat_id = _main_group_id()
    try:
        chat = await context.bot.get_chat(chat_id)
        pinned = getattr(chat, "pinned_message", None)
        if not pinned:
            return
        text = (pinned.text or pinned.caption or "").strip()
        if "NEW RAFFLE IS LIVE" not in text:
            return
        await context.bot.unpin_chat_message(
            chat_id=chat_id,
            message_id=pinned.message_id,
        )
        logger.info(
            "Removed legacy main-chat raffle notification pin | message=%s",
            pinned.message_id,
        )
    except TelegramError:
        logger.debug("No removable legacy raffle notification pin was found.")


async def _refresh_games_launcher(context):
    """Refresh the permanent Games launcher so its raffle button matches state."""
    try:
        from games_reminder import ensure_games_topic_launcher
        await ensure_games_topic_launcher(context)
    except Exception:
        logger.exception("Could not refresh Games-topic launcher after raffle state change.")


async def _finish_expired_raffle(context, raffle):
    """Close an expired raffle, announce the winner, and clear its pinned post."""
    raffle_id = int(raffle["id"])
    chat_id = int(raffle.get("chat_id") or _main_group_id())
    message_id = int(raffle.get("message_id") or 0)
    state = _load_state()

    # Prevent duplicate processing if the monitor runs twice around expiry.
    if raffle.get("status") != "active":
        return

    entries = get_approved_entries(raffle_id)
    winner = random.choice(entries) if entries else None

    close_raffle(raffle_id)

    if winner:
        winner_user_id = int(winner.get("user_id"))
        winner_name = winner.get("display_name") or winner.get("username") or str(winner_user_id)
        winner_text = (
            "🎉 <b>RAFFLE WINNER!</b> 🎉\n\n"
            f"🎁 <b>Prize:</b> {html_escape(str(raffle.get('prize') or 'Raffle'))}\n"
            f"👑 <b>Winner:</b> {html_escape(str(winner_name))}\n\n"
            "Congratulations! 🔥🎊"
        )
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=GAMES_TOPIC_ID,
                text=winner_text,
                parse_mode="HTML",
            )
        except TelegramError:
            logger.exception("Could not post expired raffle winner announcement | raffle=%s", raffle_id)

        try:
            await context.bot.send_message(
                chat_id=winner_user_id,
                text=(
                    "🎉 <b>CONGRATULATIONS!</b> 🎉\n\n"
                    f"You won the Melanated AZ raffle!\n\n"
                    f"🎁 <b>Prize:</b> {html_escape(str(raffle.get('prize') or 'Raffle'))}\n\n"
                    "An administrator will contact you regarding your prize."
                ),
                parse_mode="HTML",
            )
        except TelegramError:
            logger.info("Could not privately notify raffle winner %s.", winner_user_id)
    else:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=GAMES_TOPIC_ID,
                text=(
                    "⚠️ <b>RAFFLE CLOSED</b>\n\n"
                    f"🎁 <b>Prize:</b> {html_escape(str(raffle.get('prize') or 'Raffle'))}\n\n"
                    "No approved entries were received."
                ),
                parse_mode="HTML",
            )
        except TelegramError:
            logger.exception("Could not post expired raffle closure notice | raffle=%s", raffle_id)

    if state and state.get("raffle_id") == raffle_id:
        await _remove_pinned_raffle(context, state)
    elif message_id:
        try:
            await context.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        except TelegramError:
            pass
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except TelegramError:
            pass

    logger.info("Expired raffle finalized | raffle=%s | winner=%s", raffle_id, winner_user_id if winner else None)


# HTML helper kept local so this manager does not depend on raffle.py internals.
def html_escape(value):
    import html
    return html.escape(str(value))


async def sync_raffle_pin(context):
    """Ensure the current active raffle is the only raffle post we track/pin."""
    await _remove_legacy_raffle_notification_pin(context)

    active = get_active_raffle()
    state = _load_state()

    if not active:
        if state:
            await _remove_pinned_raffle(context, state)
        await _refresh_games_launcher(context)
        return

    try:
        expires = datetime.fromisoformat(str(active.get("expires_at")))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            await _finish_expired_raffle(context, active)
            await _refresh_games_launcher(context)
            return
    except (TypeError, ValueError):
        pass

    chat_id = int(active.get("chat_id") or _main_group_id())
    message_id = int(active.get("message_id") or 0)
    raffle_id = int(active["id"])

    if not message_id:
        await _refresh_games_launcher(context)
        return

    if state and (
        state["raffle_id"] != raffle_id
        or state["message_id"] != message_id
        or state["chat_id"] != chat_id
    ):
        await _remove_pinned_raffle(context, state)
        state = None

    if not state:
        try:
            await context.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=message_id,
                disable_notification=True,
            )
            _save_state(raffle_id, chat_id, message_id)
            logger.info(
                "Active raffle pinned | raffle=%s | chat=%s | topic=%s | message=%s",
                raffle_id,
                chat_id,
                GAMES_TOPIC_ID,
                message_id,
            )
        except TelegramError:
            logger.exception(
                "Could not pin active raffle | raffle=%s | chat=%s | message=%s",
                raffle_id,
                chat_id,
                message_id,
            )

    await _refresh_games_launcher(context)


def install_raffle_publish_pin_guard():
    """Prevent raffle.py from pinning its temporary main-chat notification.

    raffle.py already pins the real raffle post, then pins a second
    "NEW RAFFLE IS LIVE" notification. This wrapper allows the first pin
    and suppresses the second one without replacing raffle.py.
    """
    import raffle

    if getattr(raffle, "_melanated_raffle_pin_guard_installed", False):
        return

    original_publish = raffle.publish_raffle

    @functools.wraps(original_publish)
    async def guarded_publish(raffle_id, context):
        bot = context.bot
        original_pin = bot.pin_chat_message
        pin_count = 0

        async def guarded_pin(*args, **kwargs):
            nonlocal pin_count
            pin_count += 1
            if pin_count == 1:
                return await original_pin(*args, **kwargs)
            logger.info(
                "Suppressed temporary raffle notification pin | raffle=%s",
                raffle_id,
            )
            return None

        bot.pin_chat_message = guarded_pin
        try:
            return await original_publish(raffle_id, context)
        finally:
            bot.pin_chat_message = original_pin

    raffle.publish_raffle = guarded_publish
    raffle._melanated_raffle_pin_guard_installed = True
    logger.info("Raffle publish pin guard installed.")


def start_raffle_pin_manager(application):
    """Install the publish guard and keep raffle pin state synchronized."""
    if not getattr(application, "job_queue", None):
        logger.warning("Raffle pin manager unavailable: JobQueue not installed.")
        return

    install_raffle_publish_pin_guard()

    for job in application.job_queue.get_jobs_by_name("raffle-pin-manager"):
        job.schedule_removal()

    application.job_queue.run_repeating(
        sync_raffle_pin,
        interval=30,
        first=15,
        name="raffle-pin-manager",
    )
    logger.info(
        "Raffle pin manager scheduled | interval=30s | chat=%s | topic=%s",
        _main_group_id(),
        GAMES_TOPIC_ID,
    )
