# ==========================================================
# Melanated AZ Bot - raffle.py
# COMPLETE DROP-IN RAFFLE SYSTEM
# ==========================================================

import logging
import random
import os
import html
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
    RAFFLE_DURATION_DAYS,
    CASHAPP_TAG,
    CASHAPP_URL,
    ZELLE_PHONE,
    MAIN_GROUP_ID,
)

from raffle_database import (
    create_raffle, get_raffle, get_active_raffle, get_pending_raffle,
    approve_raffle, cancel_pending_raffle, set_raffle_post, close_raffle,
    add_raffle_entry, get_entry, get_pending_entries, get_raffle_entries,
    approve_entry, deny_entry, get_approved_entries, remove_entry,
    get_connection,
    update_raffle_expires_at,
)

logger = logging.getLogger("melanated_az_raffle")


def format_expiration(value):
    if not value:
        return "Unknown"
    try:
        return datetime.fromisoformat(str(value)).strftime("%b %d, %Y at %I:%M %p")
    except (TypeError, ValueError):
        return str(value)


def is_raffle_admin(user_id):
    try:
        return user_id is not None and int(user_id) in {int(x) for x in ADMIN_IDS}
    except Exception:
        return False


def display_user(entry):
    username = entry.get("username")
    name = entry.get("display_name") or entry.get("name")
    if name:
        return html.escape(str(name))
    if username:
        username = str(username)
        return html.escape(username if username.startswith("@") else f"@{username}")
    return html.escape(str(entry.get("user_id") or "Unknown"))


async def is_raffle_admin_access(update, context):
    user = update.effective_user
    if not user:
        return False
    if is_raffle_admin(user.id):
        return True
    try:
        admin_group_id = int(os.environ.get("ADMIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        admin_group_id = 0
    if not admin_group_id:
        return False
    effective_message = update.effective_message
    if effective_message and effective_message.chat and effective_message.chat.id == admin_group_id:
        return True
    try:
        member = await context.bot.get_chat_member(admin_group_id, user.id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
        logger.exception("Could not verify admin-group membership for user %s", user.id)
        return False


def ensure_raffle_description_column():
    conn = get_connection()
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(raffles)").fetchall()}
        if "description" not in columns:
            conn.execute("ALTER TABLE raffles ADD COLUMN description TEXT")
            conn.commit()
    finally:
        conn.close()


def save_raffle_description(raffle_id, description):
    conn = get_connection()
    try:
        conn.execute("UPDATE raffles SET description=? WHERE id=?", (description or None, raffle_id))
        conn.commit()
    finally:
        conn.close()


def is_free_raffle(price):
    if price is None:
        return True
    value = str(price).strip().lower().replace("$", "").replace(",", "").strip()
    if value in {"", "free", "0", "0.0", "0.00"}:
        return True
    try:
        return float(value) == 0
    except (TypeError, ValueError):
        return False


def parse_raffle_setup(payload):
    payload = str(payload or "").strip()
    if payload.startswith("/startraffle"):
        payload = payload[len("/startraffle"):].strip()
    if "|" not in payload:
        return None, None
    prize, price = payload.rsplit("|", 1)
    prize, price = prize.strip(), price.strip()
    return (prize, price) if prize and price else (None, None)


async def start_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    query = update.callback_query
    if not user or not await is_raffle_admin_access(update, context):
        if query:
            await query.answer("⛔ Admins only.", show_alert=True)
        elif message:
            await message.reply_text("⛔ Admins only.")
        return
    if query:
        await query.answer()
        context.user_data["awaiting_raffle_setup"] = True
        await query.message.reply_text(
            "🎟️ <b>Start a Raffle</b>\n\nSend the raffle information in this format:\n\n"
            "<code>$100 Cash Prize | $5</code>\n\nFormat: <b>Prize | Entry Price</b>",
            parse_mode=ParseMode.HTML,
        )
        return
    if not message:
        return
    parts = (message.text or "").split(" ", 1)
    if len(parts) < 2:
        await message.reply_text("Use:\n<code>/startraffle Prize | Entry Price</code>", parse_mode=ParseMode.HTML)
        return
    prize, price = parse_raffle_setup(parts[1].strip())
    if not prize or not price:
        await message.reply_text("⚠️ Invalid format. Use: <code>Raffle item/details | Entry Price</code>", parse_mode=ParseMode.HTML)
        return
    active, pending = get_active_raffle(), get_pending_raffle()
    if active:
        await message.reply_text(f"⚠️ Active raffle already exists.\n🎁 {html.escape(str(active['prize']))}\n💵 {html.escape(str(active['price']))}")
        return
    if pending:
        await message.reply_text(f"⚠️ Raffle already awaiting approval.\n🎁 {html.escape(str(pending['prize']))}\n💵 {html.escape(str(pending['price']))}")
        return
    expires = datetime.utcnow() + timedelta(days=int(RAFFLE_DURATION_DAYS or 7))
    raffle_id = create_raffle(prize, price, expires.isoformat())
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve Raffle", callback_data=f"raffle_approve_{raffle_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"raffle_cancel_{raffle_id}"),
    ]])
    text = (
        "🎟️ <b>RAFFLE AWAITING APPROVAL</b>\n\n"
        f"🆔 Raffle: <code>{raffle_id}</code>\n🎁 Prize: <b>{html.escape(str(prize))}</b>\n"
        f"💵 Entry: <b>{html.escape(str(price))}</b>\n⏰ Ends: <b>{format_expiration(expires.isoformat())}</b>\n\nChoose an action:"
    )
    sent_to_admin = set()
    for admin_id in ADMIN_IDS:
        try:
            target_id = int(admin_id)
            sent = await context.bot.send_message(chat_id=target_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            sent_to_admin.add(target_id)
            logger.info("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_ID:%s | SENT | message=%s", raffle_id, target_id, sent.message_id)
        except Exception as exc:
            logger.exception("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_ID:%s | FAILED | %s", raffle_id, admin_id, exc)
    try:
        admin_group_id = int(os.environ.get("ADMIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        admin_group_id = 0
    if admin_group_id:
        try:
            sent_group = await context.bot.send_message(chat_id=admin_group_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            sent_to_admin.add(admin_group_id)
            logger.info("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | SENT | message=%s", raffle_id, admin_group_id, sent_group.message_id)
        except Exception as exc:
            logger.exception("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | FAILED | %s", raffle_id, admin_group_id, exc)
    if user.id not in sent_to_admin:
        try:
            await context.bot.send_message(chat_id=user.id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except TelegramError:
            pass
    if message.chat.type == "private":
        await message.reply_text(f"✅ Raffle #{raffle_id} created and sent for admin approval.")


async def handle_raffle_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, message = update.effective_user, update.effective_message
    if not user or not message or not context.user_data.get("awaiting_raffle_setup"):
        return
    if not await is_raffle_admin_access(update, context):
        context.user_data.pop("awaiting_raffle_setup", None)
        await message.reply_text("⛔ You are not authorized to create raffles.")
        return
    payload = (message.text or "").strip()
    prize, price = parse_raffle_setup(payload)
    if not prize or not price:
        await message.reply_text("⚠️ Invalid format. Use: <code>Raffle item/details | Entry Price</code>", parse_mode=ParseMode.HTML)
        return
    active, pending = get_active_raffle(), get_pending_raffle()
    if active:
        context.user_data.pop("awaiting_raffle_setup", None)
        await message.reply_text(f"⚠️ Active raffle already exists.\n🎁 {html.escape(str(active['prize']))}\n💵 {html.escape(str(active['price']))}")
        return
    if pending:
        context.user_data.pop("awaiting_raffle_setup", None)
        await message.reply_text(f"⚠️ Raffle already awaiting approval.\n🎁 {html.escape(str(pending['prize']))}\n💵 {html.escape(str(pending['price']))}")
        return
    expires = datetime.utcnow() + timedelta(days=int(RAFFLE_DURATION_DAYS or 7))
    raffle_id = create_raffle(prize, price, expires.isoformat())
    context.user_data.pop("awaiting_raffle_setup", None)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve Raffle", callback_data=f"raffle_approve_{raffle_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"raffle_cancel_{raffle_id}"),
    ]])
    text = (
        "🎟️ <b>RAFFLE AWAITING APPROVAL</b>\n\n"
        f"🆔 Raffle: <code>{raffle_id}</code>\n🎁 Prize: <b>{html.escape(str(prize))}</b>\n"
        f"💵 Entry: <b>{html.escape(str(price))}</b>\n⏰ Ends: <b>{format_expiration(expires.isoformat())}</b>\n\nChoose an action:"
    )
    sent_to_admin = set()
    for admin_id in ADMIN_IDS:
        try:
            target_id = int(admin_id)
            sent = await context.bot.send_message(chat_id=target_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            sent_to_admin.add(target_id)
            logger.info("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_ID:%s | SENT | message=%s", raffle_id, target_id, sent.message_id)
        except Exception as exc:
            logger.exception("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_ID:%s | FAILED | %s", raffle_id, admin_id, exc)
    try:
        admin_group_id = int(os.environ.get("ADMIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        admin_group_id = 0
    if admin_group_id:
        try:
            sent_group = await context.bot.send_message(chat_id=admin_group_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            sent_to_admin.add(admin_group_id)
            logger.info("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | SENT | message=%s", raffle_id, admin_group_id, sent_group.message_id)
        except Exception as exc:
            logger.exception("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | FAILED | %s", raffle_id, admin_group_id, exc)
    if user.id not in sent_to_admin:
        try:
            await context.bot.send_message(chat_id=user.id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except TelegramError:
            pass
    await message.reply_text(f"✅ Raffle #{raffle_id} created and sent for admin approval.")


async def admin_edit_raffle_end_date(update, context):
    """Prompt an authorized admin for a new raffle end date."""
    raffle = get_active_raffle() or get_pending_raffle()
    query = update.callback_query
    if not raffle:
        if query:
            await query.answer("No active or pending raffle found.", show_alert=True)
        return
    if query:
        try:
            await query.answer()
        except Exception:
            pass
    context.user_data["awaiting_raffle_end_date"] = int(raffle["id"])
    target = update.effective_user.id if update.effective_user else None
    if not target:
        return
    await context.bot.send_message(
        chat_id=target,
        text=(
            "📅 <b>Edit Raffle End Date</b>\n\n"
            f"🎁 <b>{html.escape(str(raffle.get('prize') or 'Raffle'))}</b>\n"
            f"Current end: <b>{format_expiration(raffle.get('expires_at'))}</b>\n\n"
            "Send the new end date as <code>MM/DD/YYYY</code>.\n"
            "The raffle will end at <b>7:00 PM Arizona time</b> on that date."
        ),
        parse_mode=ParseMode.HTML,
    )


async def handle_raffle_end_date(update, context):
    """Save an admin-entered raffle end date and refresh the live post."""
    raffle_id = context.user_data.get("awaiting_raffle_end_date")
    message = update.effective_message
    if not raffle_id or not message or not message.text:
        return False
    if not await is_raffle_admin_access(update, context):
        context.user_data.pop("awaiting_raffle_end_date", None)
        return False
    raw = message.text.strip()
    parsed = None
    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        await message.reply_text("⚠️ Invalid date. Use <code>MM/DD/YYYY</code>.", parse_mode=ParseMode.HTML)
        return True
    try:
        arizona = ZoneInfo("America/Phoenix")
        expires_at = parsed.replace(hour=19, minute=0, second=0, microsecond=0, tzinfo=arizona).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        raffle = get_raffle(raffle_id)
        if not raffle:
            context.user_data.pop("awaiting_raffle_end_date", None)
            await message.reply_text("⚠️ Raffle not found.")
            return True
        update_raffle_expires_at(raffle_id, expires_at.isoformat())
        context.user_data.pop("awaiting_raffle_end_date", None)
        raffle = get_raffle(raffle_id)
        if raffle.get("status") == "active":
            old_message_id = raffle.get("message_id")
            if old_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=int(raffle.get("chat_id") or RAFFLE_CHAT_ID),
                        message_id=int(old_message_id),
                    )
                except TelegramError:
                    logger.info("Could not delete previous raffle post during end-date edit | raffle=%s", raffle_id)
            if not await publish_raffle(raffle_id, context):
                raise RuntimeError("Raffle repost failed after end-date update")
        await message.reply_text(
            f"✅ Raffle end date updated to <b>{parsed.strftime('%B %d, %Y')}</b>.\n"
            f"⏰ Ends: <b>{format_expiration(expires_at.isoformat())}</b>",
            parse_mode=ParseMode.HTML,
        )
        return True
    except Exception:
        logger.exception("Failed to update raffle end date | raffle=%s", raffle_id)
        await message.reply_text("❌ Could not update the raffle end date. Check the Render logs.")
        return True


# Telegram forum topic where active raffles are published.
RAFFLE_TOPIC_ID = 11883
RAFFLE_ENTRY_MESSAGE_DELETE_SECONDS = 60 * 60
RAFFLE_STATUS_HOUR = 16
RAFFLE_STATUS_MINUTE = 30
RAFFLE_STATUS_TIMEZONE = ZoneInfo("America/Phoenix")


async def send_daily_raffle_status(context: ContextTypes.DEFAULT_TYPE):
    raffle = get_active_raffle()
    if not raffle:
        logger.info("Daily raffle status skipped: no active raffle.")
        return False
    free = is_free_raffle(raffle.get("price"))
    approved = get_approved_entries(raffle["id"])
    rows = [[InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle['id']}")]]
    if not free:
        rows.extend([
            [InlineKeyboardButton("💵 PAY WITH CASH APP", callback_data=f"pay_cashapp_{raffle['id']}")],
            [InlineKeyboardButton("🏦 PAY WITH ZELLE", callback_data=f"pay_zelle_{raffle['id']}")],
        ])
    text = (
        "🎟️ <b>RAFFLE STATUS</b>\n\n"
        f"🎁 <b>Prize:</b> {html.escape(str(raffle.get('prize') or 'Unknown'))}\n"
        f"💵 <b>Entry:</b> {html.escape(str(raffle.get('price') or 'Unknown'))}\n"
        f"👥 <b>Total Entries:</b> {len(approved)}\n"
        f"🔢 <b>Entry Numbers:</b> {html.escape(entry_numbers)}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle.get('expires_at'))}\n\n"
        "👇 <b>Tap ENTER RAFFLE to join!</b>"
    )
    try:
        sent = await context.bot.send_message(
            chat_id=int(RAFFLE_CHAT_ID), message_thread_id=RAFFLE_TOPIC_ID,
            text=text, reply_markup=InlineKeyboardMarkup(rows), parse_mode=ParseMode.HTML,
        )
        logger.info("DAILY RAFFLE STATUS POSTED | raffle=%s | chat=%s | topic=%s | message=%s", raffle["id"], RAFFLE_CHAT_ID, RAFFLE_TOPIC_ID, sent.message_id)
        return True
    except TelegramError:
        logger.exception("Could not post daily raffle status | raffle=%s", raffle["id"])
        return False


def start_daily_raffle_status(application):
    if not getattr(application, "job_queue", None):
        logger.warning("Daily raffle status unavailable: JobQueue not installed.")
        return
    for job in application.job_queue.get_jobs_by_name("daily-raffle-status"):
        job.schedule_removal()
    application.job_queue.run_daily(
        send_daily_raffle_status,
        time(hour=RAFFLE_STATUS_HOUR, minute=RAFFLE_STATUS_MINUTE, tzinfo=RAFFLE_STATUS_TIMEZONE),
        days=tuple(range(7)), name="daily-raffle-status",
    )
    logger.info("Daily raffle status scheduled | time=%02d:%02d | timezone=%s | chat=%s | topic=%s", RAFFLE_STATUS_HOUR, RAFFLE_STATUS_MINUTE, RAFFLE_STATUS_TIMEZONE.key, RAFFLE_CHAT_ID, RAFFLE_TOPIC_ID)


async def recover_raffle_cleanup_jobs(context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Raffle cleanup recovery heartbeat executed.")


def start_raffle_cleanup_recovery(application):
    if not getattr(application, "job_queue", None):
        logger.warning("Raffle cleanup recovery unavailable: JobQueue not installed.")
        return
    for job in application.job_queue.get_jobs_by_name("raffle-entry-cleanup-recovery"):
        job.schedule_removal()
    application.job_queue.run_repeating(recover_raffle_cleanup_jobs, interval=30, first=5, name="raffle-entry-cleanup-recovery")
    logger.info("Raffle entry cleanup recovery scheduled | interval=30s | chat=%s | topic=%s", RAFFLE_CHAT_ID, RAFFLE_TOPIC_ID)


def _telegram_message_link(chat_id, message_id):
    chat_id = int(chat_id)
    if chat_id < 0:
        internal_id = str(abs(chat_id))
        if internal_id.startswith("100"):
            internal_id = internal_id[3:]
        return f"https://t.me/c/{internal_id}/{message_id}"
    return None


async def _delete_raffle_message_job(context):
    data = context.job.data or {}
    if not data:
        return
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except TelegramError:
        logger.info("Raffle temporary message already gone or could not be deleted | chat=%s message=%s", data.get("chat_id"), data.get("message_id"))


async def auto_draw_raffle(context):
    """Automatically draw the active raffle when its configured end time arrives."""
    raffle = get_active_raffle()
    if not raffle:
        logger.info("Automatic raffle draw skipped: no active raffle.")
        return
    try:
        expires = datetime.fromisoformat(str(raffle.get("expires_at")))
    except (TypeError, ValueError):
        logger.error("Automatic raffle draw skipped: invalid expiration | raffle=%s", raffle.get("id"))
        return
    now_utc = datetime.utcnow()
    if expires > now_utc:
        logger.info("Automatic raffle draw called early; rescheduling | raffle=%s | expires=%s", raffle["id"], expires.isoformat())
        schedule_raffle_auto_draw(context, int(raffle["id"]), expires)
        return
    entries = get_approved_entries(int(raffle["id"]))
    if not entries:
        close_raffle(int(raffle["id"]))
        text = (
            "🎟️ <b>RAFFLE CLOSED</b>\n\n"
            f"🎁 <b>Prize:</b> {html.escape(str(raffle.get('prize') or 'Raffle'))}\n\n"
            "⏰ The raffle ended with no approved entries.\n"
            "No winner was selected."
        )
    else:
        winner = random.choice(entries)
        close_raffle(int(raffle["id"]))
        text = (
            "🎉🎉🎉 <b>WE HAVE A WINNER!!!</b> 🎉🎉🎉\n\n"
            f"🏆 <b>CONGRATULATIONS, {display_user(winner)}!</b> 🏆\n\n"
            f"🎁 <b>You just WON {html.escape(str(raffle.get('prize') or 'Raffle'))}!</b> 🔥🔥🔥\n\n"
            f"🎟️ <b>Winning Entry:</b> #{winner['id']}\n\n"
            "💰 <b>YOU DID THAT!!!</b> 🙌🏾🥳\n"
            "Thank you for being part of the Melanated AZ community and getting in on the fun!\n\n"
            "🔥 <b>DON'T STOP HERE!</b>\n"
            "Another raffle could be coming up next, and <b>YOU COULD BE OUR NEXT WINNER!</b> 👀💰\n\n"
            "🎟️ <b>Keep entering. Keep playing. Keep winning!</b>\n\n"
            f"❤️ Congratulations again, {display_user(winner)}!\n"
            "Enjoy your prize — <b>YOU EARNED THAT WIN!</b> 🥳🏆"
        )
    try:
        await context.bot.send_message(
            chat_id=int(RAFFLE_CHAT_ID),
            message_thread_id=RAFFLE_TOPIC_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
        logger.info("AUTOMATIC RAFFLE DRAW COMPLETE | raffle=%s | entries=%s", raffle["id"], len(entries))
    except TelegramError:
        logger.exception("Automatic raffle draw announcement failed | raffle=%s", raffle["id"])


def schedule_raffle_auto_draw(context, raffle_id, expires_at=None):
    """Schedule exactly one persistent-in-process automatic draw for a raffle."""
    if not context or not getattr(context, "job_queue", None):
        logger.warning("Automatic raffle draw unavailable: JobQueue not installed.")
        return
    for job in context.job_queue.get_jobs_by_name(f"raffle-auto-draw-{int(raffle_id)}"):
        job.schedule_removal()
    if expires_at is None:
        raffle = get_raffle(int(raffle_id))
        if not raffle:
            return
        try:
            expires_at = datetime.fromisoformat(str(raffle.get("expires_at")))
        except (TypeError, ValueError):
            logger.error("Could not schedule automatic draw: invalid expiration | raffle=%s", raffle_id)
            return
    delay = max(0, (expires_at - datetime.utcnow()).total_seconds())
    context.job_queue.run_once(
        auto_draw_raffle,
        when=delay,
        name=f"raffle-auto-draw-{int(raffle_id)}",
    )
    logger.info("Automatic raffle draw scheduled | raffle=%s | expires=%s | delay=%.0fs", raffle_id, expires_at.isoformat(), delay)


def schedule_active_raffle_auto_draws(application):
    """Restore the active raffle draw timer after every bot restart."""
    if not getattr(application, "job_queue", None):
        return
    raffle = get_active_raffle()
    if raffle:
        schedule_raffle_auto_draw(application, int(raffle["id"]), None)


async def publish_raffle(raffle_id, context):
    raffle = get_raffle(raffle_id)
    if not raffle:
        return False
    free = is_free_raffle(raffle.get("price"))
    if free:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle_id}")]])
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle_id}")],
            [InlineKeyboardButton("💵 PAY WITH CASH APP", callback_data=f"pay_cashapp_{raffle_id}")],
            [InlineKeyboardButton("🏦 PAY WITH ZELLE", callback_data=f"pay_zelle_{raffle_id}")],
        ])
    payment_notice = "🎟️ Entry is FREE — no payment is required." if free else "⚠️ Your entry remains pending until an admin verifies your payment."
    text = (
        "🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b>\n\n"
        f"🎁 <b>Prize:</b> {html.escape(str(raffle['prize']))}\n"
        f"💵 <b>Entry:</b> {html.escape(str(raffle['price']))}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle['expires_at'])}\n\n👇 Tap below to enter.\n\n{payment_notice}"
    )
    main_chat_id = int(RAFFLE_CHAT_ID)
    try:
        if len(text) > 4096:
            logger.error("Raffle %s is too long to publish as one Telegram message | chars=%s", raffle_id, len(text))
            return False
        sent = await context.bot.send_message(chat_id=main_chat_id, message_thread_id=RAFFLE_TOPIC_ID, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        set_raffle_post(raffle_id, main_chat_id, sent.message_id)
        try:
            await context.bot.pin_chat_message(chat_id=main_chat_id, message_id=sent.message_id, disable_notification=True)
        except TelegramError:
            logger.exception("Raffle %s posted but could not be pinned.", raffle_id)
        # The pin manager owns the permanent main-chat navigation message.
        return True
    except TelegramError:
        logger.exception("Could not publish raffle %s to Raffles & Giveaways topic.", raffle_id)
        return False


async def approve_raffle_callback(update, context, raffle_id):
    query, user = update.callback_query, update.effective_user
    if not query or not user:
        return
    if not await is_raffle_admin_access(update, context):
        await query.answer("⛔ Admins only.", show_alert=True)
        return
    raffle = get_raffle(raffle_id)
    if not raffle:
        await query.answer("Raffle not found.", show_alert=True)
        return
    if raffle["status"] != "pending":
        await query.answer(f"Raffle is already {raffle['status']}.", show_alert=True)
        return
    if not approve_raffle(raffle_id):
        await query.answer("Raffle could not be approved.", show_alert=True)
        return
    await query.answer("Raffle approved!")
    try:
        await query.edit_message_text(f"✅ <b>RAFFLE APPROVED</b>\n\n🎁 {html.escape(str(raffle['prize']))}\n💵 {html.escape(str(raffle['price']))}\n\nPublishing...", parse_mode=ParseMode.HTML)
    except TelegramError:
        pass
    if await publish_raffle(raffle_id, context):
        schedule_raffle_auto_draw(context, raffle_id)
        try:
            await query.message.reply_text("✅ Raffle is now live in the Raffles & Giveaways topic.")
        except Exception:
            pass
    else:
        logger.error("Raffle %s approved but publication failed.", raffle_id)


async def cancel_raffle_callback(update, context, raffle_id):
    query, user = update.callback_query, update.effective_user
    if not query or not user:
        return
    if not await is_raffle_admin_access(update, context):
        await query.answer("⛔ Admins only.", show_alert=True)
        return
    raffle = get_raffle(raffle_id)
    if not raffle:
        await query.answer("Raffle not found.", show_alert=True)
        return
    if not cancel_pending_raffle(raffle_id):
        await query.answer("Raffle could not be cancelled.", show_alert=True)
        return
    await query.answer("Raffle cancelled.")
    try:
        await query.edit_message_text(f"❌ <b>RAFFLE CANCELLED</b>\n\n🎁 {html.escape(str(raffle['prize']))}\n💵 {html.escape(str(raffle['price']))}", parse_mode=ParseMode.HTML)
    except TelegramError:
        pass


async def enter_raffle(update, context, raffle_id):
    query, user = update.callback_query, update.effective_user
    if not query or not user:
        return
    raffle = get_raffle(raffle_id)
    if not raffle or raffle["status"] != "active":
        await query.answer("This raffle is no longer active.", show_alert=True)
        return
    name = user.full_name or user.username or str(user.id)
    free = is_free_raffle(raffle["price"])
    entry_id = add_raffle_entry(raffle_id, user.id, user.username, name, "free" if free else None)
    if entry_id is None:
        await query.answer("You already have an entry for this raffle.", show_alert=True)
        return
    if free:
        if not approve_entry(entry_id, user.id):
            await query.answer("Free entry could not be approved.", show_alert=True)
            return
        await query.answer("🎟️ Free entry approved!", show_alert=True)
        # Refresh the public raffle status immediately after a successful entry.
        await post_raffle_status_to_main_chat(context, announce_new_entry=True)
        entry_message = await query.message.reply_text(
            f"🎟️ <b>ENTRY APPROVED</b>\n\n🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n💵 Entry Price: <b>{html.escape(str(raffle['price']))}</b>\n🆔 Entry: <code>{entry_id}</code>\n\n✅ <b>FREE ENTRY — no payment required.</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await query.answer("Entry submitted!", show_alert=True)
        entry_message = await query.message.reply_text(
            f"🎟️ <b>ENTRY SUBMITTED</b>\n\n🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n💵 Entry Price: <b>{html.escape(str(raffle['price']))}</b>\n🆔 Entry: <code>{entry_id}</code>\n\n⚠️ Your entry is <b>PENDING</b> until an admin verifies payment.",
            parse_mode=ParseMode.HTML,
        )
    if context.job_queue and entry_message and entry_message.chat_id == int(RAFFLE_CHAT_ID):
        context.job_queue.run_once(_delete_raffle_message_job, RAFFLE_ENTRY_MESSAGE_DELETE_SECONDS, data={"chat_id": entry_message.chat_id, "message_id": entry_message.message_id})
    keyboard = None if free else InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{entry_id}"),
        InlineKeyboardButton("❌ DENY", callback_data=f"deny_{entry_id}"),
    ]])
    admin_text = (
        ("🎟️ <b>FREE RAFFLE ENTRY — AUTO APPROVED</b>" if free else "🎟️ <b>NEW RAFFLE ENTRY</b>") + "\n\n"
        f"🆔 Entry: <code>{entry_id}</code>\n🎟️ Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n👤 Member: <b>{html.escape(str(name))}</b>\n"
        + ("💳 Payment: <b>FREE</b>\n\n" if free else "💳 Payment: <b>Not selected</b>\n\nChoose an action:")
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=int(admin_id), text=admin_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except TelegramError:
            logger.warning("Could not notify admin %s.", admin_id)
    try:
        admin_group_id = int(os.environ.get("ADMIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        admin_group_id = 0
    if admin_group_id:
        try:
            sent_group = await context.bot.send_message(chat_id=admin_group_id, text=admin_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_notification=False)
            logger.info("RAFFLE ENTRY NOTIFICATION | entry=%s | raffle=%s | destination=ADMIN_GROUP:%s | SENT | message=%s", entry_id, raffle_id, admin_group_id, sent_group.message_id)
        except TelegramError:
            logger.exception("RAFFLE ENTRY NOTIFICATION | entry=%s | raffle=%s | destination=ADMIN_GROUP:%s | FAILED", entry_id, raffle_id, admin_group_id)
    else:
        logger.warning("RAFFLE ENTRY NOTIFICATION | entry=%s | raffle=%s | ADMIN_GROUP_ID is not configured", entry_id, raffle_id)


async def payment_method(update, context, raffle_id, method):
    query, user = update.callback_query, update.effective_user
    if not query or not user:
        return
    raffle = get_raffle(raffle_id)
    if not raffle or raffle["status"] != "active":
        await query.answer("Raffle is no longer active.", show_alert=True)
        return
    entry = next((x for x in get_raffle_entries(raffle_id) if int(x["user_id"]) == int(user.id) and x["status"] == "pending"), None)
    if not entry:
        await query.answer("Enter the raffle first.", show_alert=True)
        return
    if is_free_raffle(raffle.get("price")):
        await query.answer("This raffle is free — no payment is required.", show_alert=True)
        return
    body = (f"💵 <b>CASH APP</b>\n\nSend <b>{html.escape(str(raffle['price']))}</b> to:\n<code>{CASHAPP_TAG}</code>\n\n{CASHAPP_URL or ''}" if method == "cashapp" else f"🏦 <b>ZELLE</b>\n\nSend <b>{html.escape(str(raffle['price']))}</b> to:\n<code>{ZELLE_PHONE}</code>")
    await query.answer()
    payment_message = await query.message.reply_text(body + "\n\nAfter payment, your entry remains pending until an admin verifies it.", parse_mode=ParseMode.HTML)
    if context.job_queue and payment_message and payment_message.chat_id == int(RAFFLE_CHAT_ID):
        context.job_queue.run_once(_delete_raffle_message_job, RAFFLE_ENTRY_MESSAGE_DELETE_SECONDS, data={"chat_id": payment_message.chat_id, "message_id": payment_message.message_id})


async def approve_entry_callback(update, context, entry_id):
    query, user = update.callback_query, update.effective_user
    if not query or not user:
        return
    if not await is_raffle_admin_access(update, context):
        await query.answer("⛔ Admins only.", show_alert=True)
        return
    entry = get_entry(entry_id)
    if not entry:
        await query.answer("Entry not found.", show_alert=True)
        return
    if entry["status"] != "pending":
        await query.answer(f"Entry is already {entry['status']}.", show_alert=True)
        return
    if not approve_entry(entry_id, user.id):
        await query.answer("Entry could not be approved. It may already have been processed.", show_alert=True)
        return
    await query.answer("✅ Entry approved!")
    try:
        await query.edit_message_text(
            "✅ <b>ENTRY APPROVED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: <b>{entry.get('prize') or 'Raffle'}</b>\n👤 Member: <b>{display_user(entry)}</b>\n"
            f"💳 Payment: <b>{entry.get('payment_method') or 'Verified'}</b>\n\nApproved by admin <code>{user.id}</code>.",
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        pass
    try:
        await context.bot.send_message(chat_id=int(entry["user_id"]), text=("🎉 <b>YOUR RAFFLE ENTRY WAS APPROVED!</b>\n\n" f"🎁 Prize: <b>{entry.get('prize') or 'Raffle'}</b>\n" f"🆔 Entry: <code>{entry_id}</code>\n\nGood luck! 🍀"), parse_mode=ParseMode.HTML)
    except TelegramError:
        pass


async def deny_entry_callback(update, context, entry_id):
    query, user = update.callback_query, update.effective_user
    if not query or not user:
        return
    if not await is_raffle_admin_access(update, context):
        await query.answer("⛔ Admins only.", show_alert=True)
        return
    entry = get_entry(entry_id)
    if not entry:
        await query.answer("Entry not found.", show_alert=True)
        return
    if entry["status"] != "pending":
        await query.answer(f"Entry is already {entry['status']}.", show_alert=True)
        return
    if not deny_entry(entry_id, user.id):
        await query.answer("Entry could not be denied.", show_alert=True)
        return
    await query.answer("Entry denied.")
    try:
        await query.edit_message_text(f"❌ <b>ENTRY DENIED</b>\n\n🆔 Entry: <code>{entry_id}</code>\n🎟️ Raffle: <code>{entry['raffle_id']}</code>\n👤 Member: <b>{display_user(entry)}</b>\n\nDenied by admin <code>{user.id}</code>.", parse_mode=ParseMode.HTML)
    except TelegramError:
        pass


async def safe_answer(query, text="", show_alert=False):
    if not query:
        return
    try:
        await query.answer(text, show_alert=show_alert)
    except TelegramError:
        pass


async def temporary_reply(message, context, text, parse_mode=None, delete_after=300):
    if not message:
        return None
    try:
        sent = await message.reply_text(text, parse_mode=parse_mode)
    except TelegramError:
        return None
    if context and context.job_queue and delete_after:
        try:
            context.job_queue.run_once(_delete_raffle_message_job, delete_after, data={"chat_id": sent.chat_id, "message_id": sent.message_id}, name=f"raffle-temp-{sent.chat_id}-{sent.message_id}")
        except Exception:
            pass
    return sent


async def manual_raffle_entry(update, context, member_user_id):
    query, admin_user = update.callback_query, update.effective_user
    if not query or not admin_user:
        return False
    if not await is_raffle_admin_access(update, context):
        await safe_answer(query, "⛔ Admins only.", True)
        return False
    raffle = get_active_raffle()
    if not raffle:
        await safe_answer(query, "There is no active raffle.", True)
        return False
    try:
        member_user_id = int(member_user_id)
    except (TypeError, ValueError):
        await safe_answer(query, "Invalid member.", True)
        return False
    member = None
    try:
        from raffle_database import get_members
        for item in get_members(int(RAFFLE_CHAT_ID)) or []:
            if int(item.get("user_id", 0)) == member_user_id:
                member = item
                break
    except Exception:
        logger.exception("Could not load raffle-group members for manual entry.")
    if not member:
        for item in context.user_data.get("admin_manual_raffle_members", []) or []:
            if int(item.get("user_id", 0)) == member_user_id:
                member = item
                break
    if not member:
        await safe_answer(query, "Member could not be found.", True)
        return False
    username = member.get("username")
    display_name = member.get("display_name") or (f"@{username}" if username else None) or str(member_user_id)
    for existing in get_raffle_entries(raffle["id"]):
        if int(existing["user_id"]) == member_user_id:
            await safe_answer(query, "This member already has an entry in this raffle.", True)
            return False
    entry_id = add_raffle_entry(raffle["id"], member_user_id, username, display_name, "manual")
    if entry_id is None:
        await safe_answer(query, "The entry could not be created.", True)
        return False
    if not approve_entry(entry_id, admin_user.id):
        await safe_answer(query, "Entry was created but could not be approved.", True)
        return False
    await safe_answer(query, "✅ Manual entry added!")
    try:
        await query.edit_message_text(
            "✅ <b>MANUAL ENTRY ADDED</b>\n\n"
            f"🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n💵 Entry Price: <b>{raffle['price']}</b>\n"
            f"👤 Member: <b>{html.escape(str(display_name))}</b>\n🆔 User ID: <code>{member_user_id}</code>\n"
            f"🎟️ Entry: <code>{entry_id}</code>\n💳 Payment: <b>Manual</b>\n✅ Status: <b>APPROVED</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Another", callback_data="admin_manual_entry")], [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]),
        )
    except TelegramError:
        pass
    try:
        await context.bot.send_message(chat_id=member_user_id, text=("🎟️ <b>YOU HAVE BEEN ADDED TO THE RAFFLE</b>\n\n" f"🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n" f"🆔 Entry: <code>{entry_id}</code>\n\nYour raffle entry has been <b>APPROVED</b> by an admin.\n\nGood luck! 🍀"), parse_mode=ParseMode.HTML)
    except TelegramError:
        pass
    return True


async def post_raffle_status_to_main_chat(context, announce_new_entry=False):
    """Post the same public raffle status used by the admin repost button."""
    raffle = get_active_raffle()
    if not raffle:
        logger.info("Scheduled raffle status repost skipped: no active raffle.")
        return False

    approved = get_approved_entries(int(raffle["id"]))
    free = is_free_raffle(raffle.get("price"))

    rows = [
        [InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle['id']}")]
    ]
    if not free:
        rows.extend([
            [InlineKeyboardButton("💵 PAY WITH CASH APP", callback_data=f"pay_cashapp_{raffle['id']}")],
            [InlineKeyboardButton("🏦 PAY WITH ZELLE", callback_data=f"pay_zelle_{raffle['id']}")],
        ])

    text = (
        "🎟️ <b>RAFFLE STATUS</b>\n\n"
        f"🎁 <b>Raffle Item:</b> {html.escape(str(raffle.get('prize') or 'Unknown'))}\n"
        f"💵 <b>Entry:</b> {html.escape(str(raffle.get('price') or 'Unknown'))}\n"
        f"👥 <b>Total Entries:</b> {len(approved)}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle.get('expires_at'))}\n\n"
        + ("🔥 <b>Someone just joined the raffle!</b>\n\n" if announce_new_entry else "")
        + "👇 <b>Tap ENTER RAFFLE to join!</b>"
    )

    target_chat = int(MAIN_GROUP_ID or RAFFLE_CHAT_ID)
    try:
        sent = await context.bot.send_message(
            chat_id=target_chat,
            text=text,
            reply_markup=InlineKeyboardMarkup(rows),
            parse_mode=ParseMode.HTML,
        )
        logger.info(
            "RAFFLE STATUS REPOSTED | raffle=%s | destination=MAIN_CHAT:%s | message=%s | total_entries=%s",
            raffle["id"], target_chat, sent.message_id, len(approved)
        )
        return True
    except TelegramError:
        logger.exception(
            "Could not repost raffle status to main chat | raffle=%s | chat=%s",
            raffle["id"], target_chat
        )
        return False


async def repost_raffle(update, context):
    """Repost the public raffle status into the MAIN CHAT from the admin panel."""
    query, message, user = update.callback_query, update.effective_message, update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query:
            await safe_answer(query, "⛔ Admins only.", True)
        elif message:
            await temporary_reply(message, context, "⛔ Admins only.")
        return False

    posted = await post_raffle_status_to_main_chat(context)
    if not posted:
        if query:
            raffle = get_active_raffle()
            await safe_answer(
                query,
                "There is no active raffle." if not raffle else "⚠️ Could not post the raffle status to the main chat.",
                True,
            )
        elif message:
            raffle = get_active_raffle()
            await temporary_reply(
                message,
                context,
                "⚠️ There is no active raffle to repost." if not raffle
                else "⚠️ Could not post the raffle status to the main chat.",
            )
        return False

    if query:
        await safe_answer(query, "✅ Raffle status reposted to the main chat.")
    if message and not query:
        await temporary_reply(
            message, context, "✅ <b>RAFFLE STATUS REPOSTED</b>",
            parse_mode=ParseMode.HTML
        )
    return True

async def raffle_callback(update, context):
    query = update.callback_query
    if not query:
        return
    data = query.data or ""
    logger.info("Raffle callback received: %s", data)
    if data.startswith("raffle_approve_"):
        value = data[len("raffle_approve_"):]
        if value.isdigit(): await approve_raffle_callback(update, context, int(value))
        else: await query.answer("Invalid raffle ID.", show_alert=True)
        return
    if data.startswith("raffle_cancel_"):
        value = data[len("raffle_cancel_"):]
        if value.isdigit(): await cancel_raffle_callback(update, context, int(value))
        else: await query.answer("Invalid raffle ID.", show_alert=True)
        return
    if data.startswith("approve_"):
        value = data[len("approve_"):]
        if value.isdigit(): await approve_entry_callback(update, context, int(value))
        else: await query.answer("Invalid entry ID.", show_alert=True)
        return
    if data.startswith("deny_"):
        value = data[len("deny_"):]
        if value.isdigit(): await deny_entry_callback(update, context, int(value))
        else: await query.answer("Invalid entry ID.", show_alert=True)
        return
    if data.startswith("enter_"):
        value = data[len("enter_"):]
        if value.isdigit(): await enter_raffle(update, context, int(value))
        else: await query.answer("Invalid raffle ID.", show_alert=True)
        return
    if data.startswith("pay_cashapp_"):
        value = data[len("pay_cashapp_"):]
        if value.isdigit(): await payment_method(update, context, int(value), "cashapp")
        else: await query.answer("Invalid raffle ID.", show_alert=True)
        return
    if data.startswith("pay_zelle_"):
        value = data[len("pay_zelle_"):]
        if value.isdigit(): await payment_method(update, context, int(value), "zelle")
        else: await query.answer("Invalid raffle ID.", show_alert=True)
        return
    await query.answer()


async def raffle_status(update, context):
    """Admin action: post the current raffle status into the public Raffles/Giveaway topic."""
    query, message, user = update.callback_query, update.effective_message, update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query:
            await query.answer("⛔ Admins only.", show_alert=True)
        return

    raffle = get_active_raffle()
    if not raffle:
        text = "🎟️ <b>RAFFLE STATUS</b>\n\nThere is currently no active raffle."
        if query:
            await query.answer("No active raffle.", show_alert=True)
        target = query.message if query else message
        if target:
            await target.reply_text(text, parse_mode=ParseMode.HTML)
        return

    approved = get_approved_entries(raffle["id"])
    pending = get_pending_entries(raffle["id"])
    free = is_free_raffle(raffle.get("price"))

    entry_numbers = ", ".join(
        f"#{entry['id']}" for entry in approved
    ) or "None yet"

    rows = [[
        InlineKeyboardButton(
            "🎟️ ENTER RAFFLE",
            callback_data=f"enter_{raffle['id']}",
        )
    ]]
    if not free:
        rows.extend([
            [InlineKeyboardButton("💵 PAY WITH CASH APP", callback_data=f"pay_cashapp_{raffle['id']}")],
            [InlineKeyboardButton("🏦 PAY WITH ZELLE", callback_data=f"pay_zelle_{raffle['id']}")],
        ])

    text = (
        "🎟️ <b>RAFFLE STATUS</b>\n\n"
        f"🎁 <b>Prize:</b> {html.escape(str(raffle.get('prize') or 'Unknown'))}\n"
        f"💵 <b>Entry:</b> {html.escape(str(raffle.get('price') or 'Unknown'))}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle.get('expires_at'))}\n\n"
        f"✅ <b>Approved Entries:</b> {len(approved)}\n"
        f"🔢 <b>Entry Numbers:</b> {html.escape(entry_numbers)}\n"
        f"⏳ <b>Pending Payments:</b> {len(pending)}\n\n"
        "👇 <b>Tap ENTER RAFFLE to join!</b>"
    )

    try:
        sent = await context.bot.send_message(
            chat_id=int(RAFFLE_CHAT_ID),
            message_thread_id=RAFFLE_TOPIC_ID,
            text=text,
            reply_markup=InlineKeyboardMarkup(rows),
            parse_mode=ParseMode.HTML,
        )
        if query:
            await query.answer("✅ Raffle status posted.")
        if query and query.message:
            await query.message.reply_text(
                f"✅ <b>Raffle status posted.</b>\n\n"
                f"Approved entries: <b>{len(approved)}</b>\n"
                f"Entry numbers: <b>{html.escape(entry_numbers)}</b>",
                parse_mode=ParseMode.HTML,
            )
        logger.info(
            "ADMIN RAFFLE STATUS POSTED | raffle=%s | approved=%s | pending=%s | topic=%s | message=%s",
            raffle["id"], len(approved), len(pending), RAFFLE_TOPIC_ID, sent.message_id,
        )
    except TelegramError:
        logger.exception("Could not post admin-requested raffle status | raffle=%s", raffle["id"])
        if query:
            await query.answer("❌ Could not post raffle status. Check Render logs.", show_alert=True)


async def raffle_entries(update, context):
    query, message, user = update.callback_query, update.effective_message, update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query: await query.answer("⛔ Admins only.", show_alert=True)
        return
    raffle = get_active_raffle()
    if not raffle:
        text = "🎟️ <b>RAFFLE ENTRIES</b>\n\nNo active raffle."
    else:
        entries = get_approved_entries(raffle["id"])
        text = "🎟️ <b>APPROVED ENTRIES</b>\n\n" + ("\n".join(f"{i}. {display_user(e)} (Entry #{e['id']})" for i, e in enumerate(entries, 1)) if entries else "No approved entries yet.")
    if query: await query.answer()
    target = query.message if query else message
    if target: await target.reply_text(text, parse_mode=ParseMode.HTML)


async def pending_entries(update, context):
    query, message, user = update.callback_query, update.effective_message, update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query: await query.answer("⛔ Admins only.", show_alert=True)
        return
    pending = get_pending_entries()
    if query: await query.answer()
    target = query.message if query else message
    if not target: return
    if not pending:
        await target.reply_text("⏳ <b>PENDING RAFFLE ENTRIES</b>\n\nThere are no pending entries.", parse_mode=ParseMode.HTML)
        return
    for entry in pending:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{entry['id']}"), InlineKeyboardButton("❌ DENY", callback_data=f"deny_{entry['id']}")]])
        text = ("⏳ <b>PENDING RAFFLE ENTRY</b>\n\n" f"🆔 Entry: <code>{entry['id']}</code>\n🎟️ Raffle: <code>{entry['raffle_id']}</code>\n" f"🎁 Prize: <b>{entry.get('prize') or 'Unknown'}</b>\n💵 Price: <b>{entry.get('price') or 'Unknown'}</b>\n👤 Member: <b>{display_user(entry)}</b>\n💳 Payment: <b>{entry.get('payment_method') or 'Not selected'}</b>\n\nChoose an action:")
        try: await target.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except TelegramError: logger.exception("Could not display pending entry %s.", entry["id"])


async def paid_entry(update, context):
    return await raffle_entries(update, context)


async def cancel_raffle(update, context):
    query, message, user = update.callback_query, update.effective_message, update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query: await query.answer("⛔ Admins only.", show_alert=True)
        return
    raffle = get_active_raffle() or get_pending_raffle()
    if not raffle:
        if query: await query.answer("No raffle to cancel.", show_alert=True)
        elif message: await message.reply_text("⚠️ There is no raffle to cancel.")
        return
    changed = cancel_pending_raffle(raffle["id"]) if raffle["status"] == "pending" else close_raffle(raffle["id"])
    if query: await query.answer("Raffle cancelled." if changed else "Could not cancel.")
    target = query.message if query else message
    if target: await target.reply_text("❌ Raffle cancelled." if changed else "⚠️ Raffle could not be cancelled.")


async def draw_raffle(update, context):
    query, message, user = update.callback_query, update.effective_message, update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query: await query.answer("⛔ Admins only.", show_alert=True)
        return
    raffle = get_active_raffle()
    if not raffle:
        if query: await query.answer("No active raffle.", show_alert=True)
        elif message: await message.reply_text("⚠️ There is no active raffle.")
        return
    entries = get_approved_entries(raffle["id"])
    if not entries:
        if query: await query.answer("No approved entries.", show_alert=True)
        elif message: await message.reply_text("⚠️ There are no approved entries.")
        return
    winner = random.choice(entries)
    close_raffle(raffle["id"])
    text = ("🎉 <b>RAFFLE WINNER!</b>\n\n" f"🎁 Prize: <b>{raffle['prize']}</b>\n\n" f"🏆 Winner: <b>{display_user(winner)}</b>\n" f"🆔 Entry: <code>{winner['id']}</code>\n\n🎉 Congratulations!")
    if query: await query.answer("Winner selected!")
    target = query.message if query else message
    if target: await target.reply_text(text, parse_mode=ParseMode.HTML)
