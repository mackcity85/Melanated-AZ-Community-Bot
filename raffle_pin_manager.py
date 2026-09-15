import json
import logging
import os
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError

from games.game_center import GAMES_CHAT_ID, GAMES_TOPIC_ID
from raffle_database import get_active_raffle, get_approved_entries, close_raffle

logger = logging.getLogger("melanatedaz.raffle_pin_manager")

PIN_STATE_FILE = Path("/var/data/raffle_pin.json")
NAV_STATE_FILE = Path("/var/data/raffle_nav.json")


def _main_group_id():
    raw = os.environ.get("MAIN_GROUP_ID", "") or ""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return GAMES_CHAT_ID


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_json(path, state):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        logger.exception("Could not save raffle state: %s", path)


def _clear_file(path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.exception("Could not clear raffle state: %s", path)


def _load_state():
    return _load_json(PIN_STATE_FILE)


def _save_state(state):
    _save_json(PIN_STATE_FILE, state)


def _clear_state():
    _clear_file(PIN_STATE_FILE)


def _load_nav_state():
    return _load_json(NAV_STATE_FILE)


def _save_nav_state(state):
    _save_json(NAV_STATE_FILE, state)


def _clear_nav_state():
    _clear_file(NAV_STATE_FILE)


def _raffle_message_link(message_id):
    """Return a direct link to the raffle message in the Games forum topic."""
    internal_chat_id = str(abs(_main_group_id())).removeprefix("100")
    return f"https://t.me/c/{internal_chat_id}/{int(message_id)}?thread={GAMES_TOPIC_ID}"


async def _remove_pinned_raffle(context, state):
    chat_id = _main_group_id()
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


async def _remove_main_chat_navigation(context):
    state = _load_nav_state()
    message_id = int(state.get("message_id") or 0)
    if not message_id:
        _clear_nav_state()
        return
    main_group_id = _main_group_id()
    try:
        await context.bot.unpin_chat_message(chat_id=main_group_id, message_id=message_id)
    except TelegramError:
        pass
    try:
        await context.bot.delete_message(chat_id=main_group_id, message_id=message_id)
    except TelegramError:
        pass
    _clear_nav_state()


async def _publish_main_chat_navigation(context, raffle):
    """Keep one permanent pinned main-chat message linking to the active Games-topic raffle."""
    raffle_id = int(raffle["id"])
    raffle_message_id = int(raffle.get("message_id") or 0)
    if not raffle_message_id:
        logger.warning("Active raffle %s has no message_id; cannot create main-chat navigation.", raffle_id)
        return

    main_group_id = _main_group_id()
    link = _raffle_message_link(raffle_message_id)
    current = _load_nav_state()
    if int(current.get("raffle_id") or 0) == raffle_id and int(current.get("message_id") or 0) > 0:
        return
    if current:
        await _remove_main_chat_navigation(context)

    text = (
        "📌 <b>RAFFLE NAVIGATION</b>\n\n"
        "🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b> is live!\n\n"
        f"🎁 <b>Prize:</b> {html_escape(str(raffle.get('prize') or 'Raffle'))}\n"
        f"💵 <b>Entry:</b> {html_escape(str(raffle.get('price') or 'See raffle post'))}\n\n"
        "👇🏾 Tap below to open the official raffle post in the Games topic."
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎟️ GO TO RAFFLE", url=link)]])

    try:
        sent = await context.bot.send_message(
            chat_id=main_group_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        try:
            await context.bot.pin_chat_message(
                chat_id=main_group_id,
                message_id=sent.message_id,
                disable_notification=True,
            )
        except TelegramError:
            logger.exception("Could not pin main-chat raffle navigation | raffle=%s", raffle_id)
            try:
                await context.bot.delete_message(chat_id=main_group_id, message_id=sent.message_id)
            except TelegramError:
                pass
            return
        _save_nav_state({
            "raffle_id": raffle_id,
            "message_id": sent.message_id,
            "chat_id": main_group_id,
            "raffle_message_id": raffle_message_id,
        })
        logger.info("Main-chat raffle navigation pinned | raffle=%s | message=%s", raffle_id, sent.message_id)
    except TelegramError:
        logger.exception("Could not publish main-chat raffle navigation | raffle=%s", raffle_id)


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


def html_escape(value):
    import html
    return html.escape(str(value))


def _clear_raffle_post_reference(raffle_id):
    """Clear a stale Telegram message reference without changing raffle status or entries."""
    db_name = os.environ.get("RAFFLE_DB_NAME", "/var/data/raffle.db").strip() or "/var/data/raffle.db"
    db_name = os.path.abspath(db_name)
    if not db_name.startswith("/var/data/"):
        logger.error("Refusing to modify unexpected raffle database path: %s", db_name)
        return False
    conn = None
    try:
        conn = sqlite3.connect(db_name, timeout=30, check_same_thread=False)
        conn.execute("UPDATE raffles SET chat_id=NULL, message_id=NULL WHERE id=?", (int(raffle_id),))
        conn.commit()
        logger.warning("Cleared stale Telegram post reference | raffle=%s", raffle_id)
        return True
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("Could not clear stale Telegram post reference | raffle=%s", raffle_id)
        return False
    finally:
        if conn:
            conn.close()


async def _publish_existing_raffle(context, raffle):
    """Publish an existing active raffle that has no valid Telegram post; never creates a new raffle."""
    raffle_id = int(raffle["id"])
    if int(raffle.get("message_id") or 0):
        return True

    free = str(raffle.get("price") or "").strip().lower().replace("$", "") in {"", "free", "0", "0.0", "0.00"}
    if free:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle_id}")]])
        payment_notice = "🎟️ Entry is FREE — no payment is required."
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle_id}")],
            [InlineKeyboardButton("💵 PAY WITH CASH APP", callback_data=f"pay_cashapp_{raffle_id}")],
            [InlineKeyboardButton("🏦 PAY WITH ZELLE", callback_data=f"pay_zelle_{raffle_id}")],
        ])
        payment_notice = "⚠️ Your entry remains pending until an admin verifies your payment."

    text = (
        "🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b>\n\n"
        f"🎁 <b>Prize:</b> {html_escape(raffle.get('prize') or 'Raffle')}\n"
        f"💵 <b>Entry:</b> {html_escape(raffle.get('price') or 'See raffle details')}\n"
        f"⏰ <b>Ends:</b> {html_escape(raffle.get('expires_at') or 'Unknown')}\n\n"
        "👇 Tap below to enter.\n\n"
        f"{payment_notice}"
    )

    chat_id = _main_group_id()
    try:
        sent = await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=GAMES_TOPIC_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        from raffle_database import set_raffle_post
        set_raffle_post(raffle_id, chat_id, sent.message_id)
        logger.info(
            "EXISTING RAFFLE REPUBLISHED | raffle=%s | chat=%s | topic=%s | message=%s",
            raffle_id, chat_id, GAMES_TOPIC_ID, sent.message_id,
        )
        return True
    except TelegramError:
        logger.exception("Could not republish existing active raffle | raffle=%s", raffle_id)
        return False


async def _finish_expired_raffle(context, raffle):
    """Close an expired raffle, announce the winner, and clear both raffle/navigation pins."""
    raffle_id = int(raffle["id"])
    chat_id = _main_group_id()
    message_id = int(raffle.get("message_id") or 0)
    state = _load_state()
    if raffle.get("status") != "active":
        return
    entries = get_approved_entries(raffle_id)
    winner = random.choice(entries) if entries else None
    winner_user_id = None
    close_raffle(raffle_id)
    if winner:
        winner_user_id = int(winner.get("user_id"))
        winner_name = winner.get("display_name") or winner.get("username") or str(winner_user_id)
        try:
            await context.bot.send_message(
                chat_id=chat_id, message_thread_id=GAMES_TOPIC_ID,
                text=("🎉 <b>RAFFLE WINNER!</b> 🎉\n\n"
                      f"🎁 <b>Prize:</b> {html_escape(raffle.get('prize') or 'Raffle')}\n"
                      f"👑 <b>Winner:</b> {html_escape(winner_name)}\n\n"
                      "Congratulations! 🔥🎊"), parse_mode="HTML")
        except TelegramError:
            logger.exception("Could not post expired raffle winner announcement | raffle=%s", raffle_id)
        try:
            await context.bot.send_message(
                chat_id=winner_user_id,
                text=("🎉 <b>CONGRATULATIONS!</b> 🎉\n\n"
                      "You won the Melanated AZ raffle!\n\n"
                      f"🎁 <b>Prize:</b> {html_escape(raffle.get('prize') or 'Raffle')}\n\n"
                      "An administrator will contact you regarding your prize."), parse_mode="HTML")
        except TelegramError:
            logger.info("Could not privately notify raffle winner %s.", winner_user_id)
    else:
        try:
            await context.bot.send_message(
                chat_id=chat_id, message_thread_id=GAMES_TOPIC_ID,
                text=("⚠️ <b>RAFFLE CLOSED</b>\n\n"
                      f"🎁 <b>Prize:</b> {html_escape(raffle.get('prize') or 'Raffle')}\n\n"
                      "No approved entries were received."), parse_mode="HTML")
        except TelegramError:
            logger.exception("Could not post expired raffle closure notice | raffle=%s", raffle_id)
    if state and int(state.get("raffle_id") or 0) == raffle_id:
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
    await _remove_main_chat_navigation(context)
    logger.info("Expired raffle finalized | raffle=%s | winner=%s", raffle_id, winner_user_id)


async def sync_raffle_pin(context):
    """Keep the official raffle pinned in Games topic and a navigation pin in main chat."""
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
        await _remove_main_chat_navigation(context)
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
    chat_id = _main_group_id()
    message_id = int(active.get("message_id") or 0)

    # The persistent DB can contain a Telegram message_id for a message that was
    # deleted during an earlier cleanup/deploy. If pinning says "Message to pin
    # not found", invalidate only that stale reference and republish the SAME raffle.
    state = _load_state()
    tracked_id = int(state.get("raffle_id") or 0) if state else 0
    tracked_message_id = int(state.get("message_id") or 0) if state else 0
    if tracked_id and tracked_id != raffle_id and tracked_message_id:
        await _remove_pinned_raffle(context, state)

    if message_id:
        state = _load_state()
        if state.get("raffle_id") != raffle_id or state.get("message_id") != message_id:
            try:
                await context.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=message_id,
                    disable_notification=True,
                )
            except BadRequest as exc:
                if "message to pin not found" in str(exc).lower():
                    logger.warning(
                        "Active raffle %s references a missing Telegram message=%s; republishing SAME raffle.",
                        raffle_id, message_id,
                    )
                    _clear_state()
                    if _clear_raffle_post_reference(raffle_id):
                        active = get_active_raffle() or active
                        published = await _publish_existing_raffle(context, active)
                        if not published:
                            await _refresh_games_launcher(context)
                            return
                        active = get_active_raffle() or active
                        message_id = int(active.get("message_id") or 0)
                        if not message_id:
                            logger.error("Raffle %s was republished but message_id is still missing.", raffle_id)
                            return
                    else:
                        return
                else:
                    logger.exception("Could not pin active raffle post in Games topic | raffle=%s", raffle_id)
                    return
            except TelegramError:
                logger.exception("Could not pin active raffle post in Games topic | raffle=%s", raffle_id)
                return

    if not message_id:
        published = await _publish_existing_raffle(context, active)
        if not published:
            await _refresh_games_launcher(context)
            return
        active = get_active_raffle() or active
        message_id = int(active.get("message_id") or 0)
        if not message_id:
            logger.error("Existing raffle %s was published but database message_id is still missing.", raffle_id)
            return

    # Always verify/pin the current message after any stale-reference recovery.
    state = _load_state()
    if state.get("raffle_id") != raffle_id or state.get("message_id") != message_id:
        try:
            await context.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=message_id,
                disable_notification=True,
            )
        except TelegramError:
            logger.exception("Could not pin active raffle post in Games topic | raffle=%s", raffle_id)
            return
        _save_state({
            "raffle_id": raffle_id,
            "chat_id": chat_id,
            "message_id": message_id,
            "thread_id": GAMES_TOPIC_ID,
        })

    await _publish_main_chat_navigation(context, active)
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
