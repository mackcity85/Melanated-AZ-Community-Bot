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

PIN_STATE_FILE = Path("/var/data/raffle_pin.json")


def _main_group_id():
    raw = os.environ.get("MAIN_GROUP_ID", "") or ""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return GAMES_CHAT_ID


def _load_state():
    try:
        return json.loads(PIN_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_state(state):
    try:
        PIN_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PIN_STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        logger.exception("Could not save raffle pin state.")


def _clear_state():
    try:
        PIN_STATE_FILE.unlink(missing_ok=True)
    except OSError:
        logger.exception("Could not clear raffle pin state.")


async def _remove_pinned_raffle(context, state):
    chat_id = int(state.get("chat_id") or _main_group_id())
    message_id = int(state.get("message_id") or 0)
    if not message_id:
        _clear_state()
        return

    try:
        await context.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass
    _clear_state()


async def _remove_legacy_raffle_notification_pin(context):
    main_group_id = _main_group_id()
    try:
        chat = await context.bot.get_chat(main_group_id)
        pinned = getattr(chat, "pinned_message", None)
        if not pinned:
            return
        value = (pinned.text or pinned.caption or "").strip()
        if "NEW RAFFLE IS LIVE" not in value:
            return
        try:
            await context.bot.unpin_chat_message(chat_id=main_group_id, message_id=pinned.message_id)
        except TelegramError:
            pass
    except TelegramError:
        logger.exception("Could not inspect/remove legacy raffle notification pin.")


async def _refresh_games_launcher(context):
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

    if raffle.get("status") != "active":
        return

    entries = get_approved_entries(raffle_id)
    winner = random.choice(entries) if entries else None
    winner_user_id = None

    close_raffle(raffle_id)

    def html_escape(value):
        import html
        return html.escape(str(value))

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
                    "You won the Melanated AZ raffle!\n\n"
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

    logger.info("Expired raffle finalized | raffle=%s | winner=%s", raffle_id, winner_user_id)


async def sync_raffle_pin(context):
    """Ensure the current active raffle is the only raffle post we track/pin."""
    await _remove_legacy_raffle_notification_pin(context)

    try:
        active = get_active_raffle()
    except Exception:
        logger.exception("Could not load active raffle.")
        return

    if not active:
        state = _load_state()
        if state:
            await _remove_pinned_raffle(context, state)
        await _refresh_games_launcher(context)
        return

    expires = active.get("expires_at") or active.get("end_time") or active.get("ends_at")
    if expires:
        try:
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires <= datetime.now(timezone.utc):
                await _finish_expired_raffle(context, active)
                await _refresh_games_launcher(context)
                return
        except (TypeError, ValueError):
            pass

    raffle_id = int(active["id"])
    chat_id = int(active.get("chat_id") or _main_group_id())
    message_id = int(active.get("message_id") or 0)
    if not message_id:
        logger.warning("Active raffle %s has no message_id; cannot pin.", raffle_id)
        await _refresh_games_launcher(context)
        return

    state = _load_state()
    tracked_id = int(state.get("raffle_id") or 0) if state else 0
    tracked_message_id = int(state.get("message_id") or 0) if state else 0

    if tracked_id and tracked_id != raffle_id and tracked_message_id:
        await _remove_pinned_raffle(context, state)

    state = _load_state()
    if state.get("raffle_id") != raffle_id or state.get("message_id") != message_id:
        try:
            await context.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=message_id,
                disable_notification=True,
            )
        except TelegramError:
            logger.exception("Could not pin active raffle post | raffle=%s", raffle_id)
            return
        _save_state({
            "raffle_id": raffle_id,
            "chat_id": chat_id,
            "message_id": message_id,
        })

    await _refresh_games_launcher(context)


def install_raffle_publish_pin_guard(application):
    """Allow the real raffle post to be pinned while suppressing the legacy notification pin."""
    if getattr(application, "_raffle_publish_pin_guard_installed", False):
        return

    application._raffle_publish_pin_guard_installed = True

    try:
        import raffle
    except Exception:
        logger.exception("Could not import raffle module for pin guard.")
        return

    original_publish = getattr(raffle, "publish_raffle", None)
    if not original_publish:
        logger.warning("raffle.publish_raffle not found; pin guard not installed.")
        return

    async def guarded_publish(*args, **kwargs):
        bot = application.bot
        original_pin = bot.pin_chat_message
        pin_count = 0

        async def guarded_pin(*pin_args, **pin_kwargs):
            nonlocal pin_count
            pin_count += 1
            if pin_count == 1:
                return await original_pin(*pin_args, **pin_kwargs)
            logger.info("Suppressed legacy raffle notification pin.")
            return True

        bot.pin_chat_message = guarded_pin
        try:
            return await original_publish(*args, **kwargs)
        finally:
            bot.pin_chat_message = original_pin

    raffle.publish_raffle = guarded_publish


def start_raffle_pin_manager(application):
    """Start the raffle pin monitor."""
    install_raffle_publish_pin_guard(application)
    if not getattr(application, "job_queue", None):
        logger.warning("JobQueue unavailable; raffle pin manager not started.")
        return

    application.job_queue.run_repeating(
        sync_raffle_pin,
        interval=30,
        first=15,
        name="raffle-pin-manager",
    )
    logger.info("Raffle pin manager started | interval=30s")
