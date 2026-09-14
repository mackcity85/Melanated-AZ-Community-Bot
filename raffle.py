# ==========================================================
# Melanated AZ Bot - raffle.py
# COMPLETE DROP-IN RAFFLE SYSTEM
#
# Critical fix:
# raffle_callback() is the ONLY owner of raffle callbacks,
# including approve_<entry_id> and deny_<entry_id>.
# bot.py must route those callbacks to this function.
# ==========================================================

import logging
import random
import os
import html
from datetime import datetime, timedelta, time
from types import SimpleNamespace
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
)

from raffle_database import (
    create_raffle,
    get_raffle,
    get_active_raffle,
    get_pending_raffle,
    approve_raffle,
    cancel_pending_raffle,
    set_raffle_post,
    close_raffle,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    get_raffle_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    get_connection,
    record_raffle_entry_message,
    get_raffle_entry_messages,
    mark_raffle_entry_message_cleaned,
    schedule_raffle_entry_message_cleanup,
    get_due_raffle_entry_message_groups,
)

logger = logging.getLogger("melanated_az_raffle")

# ==========================================================
# RAFFLE AUTOMATION / TEMPORARY MESSAGE CLEANUP
# ==========================================================

APPROVED_ENTRY_CLEANUP_SECONDS = 180
RAFFLE_GAMES_TOPIC_ID = int(
    os.environ.get("RAFFLE_GAMES_TOPIC_ID", "8809") or "8809"
)
RAFFLE_STATUS_HOUR = 8
RAFFLE_STATUS_MINUTE = 0
RAFFLE_STATUS_TIMEZONE = ZoneInfo("America/Phoenix")


async def track_entry_message(entry_id, sent_message, kind="entry"):
    """Persist a Telegram message so it can be removed later."""
    if not sent_message:
        return
    try:
        record_raffle_entry_message(
            int(entry_id),
            int(sent_message.chat_id),
            int(sent_message.message_id),
            kind,
        )
    except Exception:
        logger.exception(
            "Could not track raffle entry message | entry=%s | kind=%s",
            entry_id,
            kind,
        )


async def post_public_raffle_status(context, raffle_id):
    """Post a fresh public raffle status in the Games topic."""
    raffle = get_raffle(int(raffle_id))
    if not raffle or raffle.get("status") != "active":
        return None

    approved = get_approved_entries(int(raffle_id))
    pending = get_pending_entries(int(raffle_id))
    free = is_free_raffle(raffle.get("price"))

    keyboard_rows = [
        [InlineKeyboardButton(
            "🎟️ ENTER RAFFLE",
            callback_data=f"enter_{raffle_id}",
        )]
    ]
    if not free:
        keyboard_rows.extend([
            [InlineKeyboardButton(
                "💵 PAY WITH CASH APP",
                callback_data=f"pay_cashapp_{raffle_id}",
            )],
            [InlineKeyboardButton(
                "🏦 PAY WITH ZELLE",
                callback_data=f"pay_zelle_{raffle_id}",
            )],
        ])

    text = (
        "🎟️ <b>RAFFLE STATUS</b>\n\n"
        f"🎁 <b>Prize:</b> {html.escape(str(raffle.get('prize') or 'Unknown'))}\n"
        f"💵 <b>Entry:</b> {html.escape(str(raffle.get('price') or 'Unknown'))}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle.get('expires_at'))}\n\n"
        f"✅ <b>Approved Entries:</b> {len(approved)}\n"
        f"⏳ <b>Pending Entries:</b> {len(pending)}\n\n"
        "👇 <b>Tap ENTER RAFFLE to join!</b>"
    )

    try:
        return await context.bot.send_message(
            chat_id=int(RAFFLE_CHAT_ID),
            message_thread_id=RAFFLE_GAMES_TOPIC_ID,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard_rows),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.exception(
            "Could not post public raffle status | raffle=%s",
            raffle_id,
        )
        return None


async def send_daily_raffle_status(context: ContextTypes.DEFAULT_TYPE):
    """Post the active raffle status every day at 8:00 AM Arizona time."""
    raffle = get_active_raffle()
    if not raffle:
        logger.info("Daily raffle status skipped: no active raffle.")
        return

    sent = await post_public_raffle_status(context, int(raffle["id"]))
    if sent:
        logger.info(
            "DAILY RAFFLE STATUS POSTED | raffle=%s | chat=%s | topic=%s | message=%s",
            raffle["id"],
            RAFFLE_CHAT_ID,
            RAFFLE_GAMES_TOPIC_ID,
            sent.message_id,
        )


def start_daily_raffle_status(application):
    """Schedule the daily 8:00 AM Arizona-time status post."""
    if not application.job_queue:
        logger.warning(
            "Daily raffle status unavailable: JobQueue not installed."
        )
        return

    for job in application.job_queue.get_jobs_by_name("daily-raffle-status"):
        job.schedule_removal()

    application.job_queue.run_daily(
        send_daily_raffle_status,
        time(
            hour=RAFFLE_STATUS_HOUR,
            minute=RAFFLE_STATUS_MINUTE,
            tzinfo=RAFFLE_STATUS_TIMEZONE,
        ),
        days=tuple(range(7)),
        name="daily-raffle-status",
    )
    logger.info(
        "Daily raffle status scheduled | time=08:00 | timezone=America/Phoenix | chat=%s | topic=%s",
        RAFFLE_CHAT_ID,
        RAFFLE_GAMES_TOPIC_ID,
    )


async def cleanup_approved_entry_messages(context):
    """Delete every tracked temporary Telegram message for an approved entry."""
    job = getattr(context, "job", None)
    data = getattr(job, "data", None) or {}
    entry_id = int(data.get("entry_id", 0) or 0)
    raffle_id = int(data.get("raffle_id", 0) or 0)
    if not entry_id:
        return

    records = get_raffle_entry_messages(entry_id)
    for record in records or []:
        try:
            await context.bot.delete_message(
                chat_id=int(record["chat_id"]),
                message_id=int(record["message_id"]),
            )
        except TelegramError:
            pass
        finally:
            try:
                mark_raffle_entry_message_cleaned(record["id"])
            except Exception:
                logger.exception(
                    "Could not mark raffle cleanup record %s.",
                    record.get("id"),
                )

    if raffle_id:
        await post_public_raffle_status(context, raffle_id)

    logger.info(
        "RAFFLE ENTRY CLEANUP COMPLETE | entry=%s | raffle=%s",
        entry_id,
        raffle_id,
    )


async def recover_raffle_entry_cleanups(context):
    """Recover overdue cleanup records after Render or the bot restarts."""
    try:
        due_groups = get_due_raffle_entry_message_groups(
            datetime.utcnow().isoformat()
        )
    except Exception:
        logger.exception("RAFFLE CLEANUP RECOVERY CHECK FAILED")
        return

    if not due_groups:
        return

    logger.info(
        "RAFFLE CLEANUP RECOVERY | due_entries=%s",
        len(due_groups),
    )

    for group in due_groups:
        try:
            entry_id = int(group["entry_id"])
            entry = get_entry(entry_id)
            if not entry:
                logger.warning(
                    "RAFFLE CLEANUP RECOVERY | entry=%s not found; skipping",
                    entry_id,
                )
                continue

            recovery_context = SimpleNamespace(
                bot=context.bot,
                job=SimpleNamespace(
                    data={
                        "entry_id": entry_id,
                        "raffle_id": int(entry["raffle_id"]),
                    }
                ),
            )
            await cleanup_approved_entry_messages(recovery_context)
        except Exception:
            logger.exception(
                "RAFFLE CLEANUP RECOVERY FAILED | entry=%s",
                group.get("entry_id"),
            )


def start_raffle_cleanup_recovery(application):
    """Run a lightweight SQLite-backed cleanup recovery check every 30 seconds."""
    if not application.job_queue:
        logger.warning(
            "Raffle cleanup recovery unavailable: JobQueue not installed."
        )
        return

    for job in application.job_queue.get_jobs_by_name(
        "raffle-entry-cleanup-recovery"
    ):
        job.schedule_removal()

    application.job_queue.run_repeating(
        recover_raffle_entry_cleanups,
        interval=30,
        first=5,
        name="raffle-entry-cleanup-recovery",
    )
    logger.info(
        "Raffle entry cleanup recovery scheduled | interval=30s | chat=%s | topic=%s",
        RAFFLE_CHAT_ID,
        RAFFLE_GAMES_TOPIC_ID,
    )


def schedule_approved_entry_cleanup(entry_id, raffle_id, context):
    """Persist and schedule the exact three-minute approved-entry cleanup."""
    cleanup_at = (
        datetime.utcnow() +
        timedelta(seconds=APPROVED_ENTRY_CLEANUP_SECONDS)
    ).isoformat()

    try:
        schedule_raffle_entry_message_cleanup(entry_id, cleanup_at)
    except Exception:
        logger.exception(
            "Could not persist raffle cleanup deadline | entry=%s",
            entry_id,
        )

    if not getattr(context, "job_queue", None):
        logger.error(
            "Job queue unavailable; raffle cleanup not scheduled | entry=%s",
            entry_id,
        )
        return

    job_name = f"raffle-entry-cleanup-{int(entry_id)}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    context.job_queue.run_once(
        cleanup_approved_entry_messages,
        APPROVED_ENTRY_CLEANUP_SECONDS,
        data={
            "entry_id": int(entry_id),
            "raffle_id": int(raffle_id),
        },
        name=job_name,
    )



async def is_raffle_admin_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True for configured admins or members of the configured Admin Group."""
    user = update.effective_user
    if not user:
        return False

    # Primary admin list.
    try:
        if user.id in {int(admin_id) for admin_id in ADMIN_IDS}:
            return True
    except (TypeError, ValueError):
        pass

    # Optional Admin Group access.
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


def format_expiration(value):
    """Format a stored raffle expiration timestamp for Telegram display."""
    if not value:
        return "Unknown"
    try:
        return datetime.fromisoformat(str(value)).strftime("%b %d, %Y at %I:%M %p")
    except (TypeError, ValueError):
        return str(value)



def ensure_raffle_description_column():
    """Safely add the optional description column to an existing raffle DB."""
    conn = get_connection()
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(raffles)").fetchall()}
        if "description" not in columns:
            conn.execute("ALTER TABLE raffles ADD COLUMN description TEXT")
            conn.commit()
    finally:
        conn.close()


def save_raffle_description(raffle_id, description):
    """Persist the full raffle description without replacing existing raffle data."""
    conn = get_connection()
    try:
        conn.execute("UPDATE raffles SET description=? WHERE id=?", (description or None, raffle_id))
        conn.commit()
    finally:
        conn.close()


def display_user(entry):
    """Return a safe display name for a raffle entry/member record."""
    name = entry.get("display_name") or entry.get("name")
    username = entry.get("username")
    user_id = entry.get("user_id")
    if name:
        return html.escape(str(name))
    if username:
        username = str(username)
        return html.escape(username if username.startswith("@") else f"@{username}")
    return html.escape(str(user_id or "Unknown"))


def is_free_raffle(price):
    """Recognize FREE, 0, $0, 0.00, etc. as a free-entry raffle."""
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
    """Use the FINAL | as the separator: everything before it is the raffle item."""
    payload = str(payload or "").strip()
    if payload.startswith("/startraffle"):
        payload = payload[len("/startraffle"):].strip()
    if "|" not in payload:
        return None, None
    prize, price = payload.rsplit("|", 1)
    prize = prize.strip()
    price = price.strip()
    if not prize or not price:
        return None, None
    return prize, price


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
            "🎟️ <b>Start a Raffle</b>\n\n"
            "Send the raffle information in this format:\n\n"
            "<code>$100 Cash Prize | $5</code>\n\n"
            "Format: <b>Prize | Entry Price</b>\n\n"
            "Example: <code>$100 Cash Prize | $5</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not message:
        return
    parts = (message.text or "").split(" ", 1)
    if len(parts) < 2:
        await message.reply_text(
            "Use:\n<code>/startraffle Prize | Entry Price</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    payload = parts[1].strip()
    prize, price = parse_raffle_setup(payload)
    if not prize or not price:
        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Use:\n"
            "<code>Raffle item/details | Entry Price</code>\n\n"
            "The FINAL <code>|</code> separates the raffle item from the entry cost.",
            parse_mode=ParseMode.HTML,
        )
        return

    active = get_active_raffle()
    pending = get_pending_raffle()
    if active:
        await message.reply_text(
            f"⚠️ Active raffle already exists.\n🎁 {active['prize']}\n💵 {active['price']}"
        )
        return
    if pending:
        await message.reply_text(
            f"⚠️ Raffle already awaiting approval.\n🎁 {pending['prize']}\n💵 {pending['price']}"
        )
        return

    expires = datetime.utcnow() + timedelta(days=int(RAFFLE_DURATION_DAYS or 7))
    raffle_id = create_raffle(prize, price, expires.isoformat())

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve Raffle", callback_data=f"raffle_approve_{raffle_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"raffle_cancel_{raffle_id}"),
    ]])
    text = (
        "🎟️ <b>RAFFLE AWAITING APPROVAL</b>\n\n"
        f"🆔 Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{prize}</b>\n"
        f"💵 Entry: <b>{price}</b>\n"
        f"⏰ Ends: <b>{format_expiration(expires.isoformat())}</b>\n\n"
        + "Choose an action:"
    )

    sent_to_admin = set()
    for admin_id in ADMIN_IDS:
        try:
            target_id = int(admin_id)
            sent = await context.bot.send_message(
                chat_id=target_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
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
            sent_group = await context.bot.send_message(
                chat_id=admin_group_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            sent_to_admin.add(admin_group_id)
            logger.info("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | SENT | message=%s", raffle_id, admin_group_id, sent_group.message_id)
        except Exception as exc:
            logger.exception("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | FAILED | %s", raffle_id, admin_group_id, exc)

    if user.id not in sent_to_admin:
        try:
            await context.bot.send_message(
                chat_id=user.id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
        except TelegramError:
            pass

    if message.chat.type == "private":
        await message.reply_text(f"✅ Raffle #{raffle_id} created and sent for admin approval.")

async def handle_raffle_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process raffle information entered after clicking Start Raffle."""
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    if not context.user_data.get("awaiting_raffle_setup"):
        return

    # Only admins or members of the configured Admin Group can create raffles.
    if not await is_raffle_admin_access(update, context):
        context.user_data.pop("awaiting_raffle_setup", None)
        await message.reply_text("⛔ You are not authorized to create raffles.")
        return

    payload = (message.text or "").strip()
    if not payload:
        await message.reply_text("⚠️ Please enter the raffle information.")
        return

    prize, price = parse_raffle_setup(payload)
    if not prize or not price:
        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Use:\n"
            "<code>Raffle item/details | Entry Price</code>\n\n"
            "The FINAL <code>|</code> separates the raffle item from the entry cost.",
            parse_mode=ParseMode.HTML,
        )
        return

    active = get_active_raffle()
    pending = get_pending_raffle()
    if active:
        context.user_data.pop("awaiting_raffle_setup", None)
        await message.reply_text(
            f"⚠️ Active raffle already exists.\n🎁 {active['prize']}\n💵 {active['price']}"
        )
        return
    if pending:
        context.user_data.pop("awaiting_raffle_setup", None)
        await message.reply_text(
            f"⚠️ Raffle already awaiting approval.\n🎁 {pending['prize']}\n💵 {pending['price']}"
        )
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
        f"🆔 Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{prize}</b>\n"
        f"💵 Entry: <b>{price}</b>\n"
        f"⏰ Ends: <b>{format_expiration(expires.isoformat())}</b>\n\n"
        + "Choose an action:"
    )

    sent_to_admin = set()
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            sent_to_admin.add(int(admin_id))
        except TelegramError:
            logger.warning("Could not notify admin %s.", admin_id)

    try:
        admin_group_id = int(os.environ.get("ADMIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        admin_group_id = 0

    if admin_group_id:
        try:
            sent_group = await context.bot.send_message(
                chat_id=admin_group_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            sent_to_admin.add(admin_group_id)
            logger.info("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | SENT | message=%s", raffle_id, admin_group_id, sent_group.message_id)
        except Exception as exc:
            logger.exception("RAFFLE APPROVAL NOTIFICATION | raffle=%s | destination=ADMIN_GROUP:%s | FAILED | %s", raffle_id, admin_group_id, exc)

    if user.id not in sent_to_admin:
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            pass

    await message.reply_text(
        f"✅ Raffle #{raffle_id} created and sent for admin approval.",
    )


# Generic temporary raffle replies remain one hour unless the approved-entry
# cleanup above handles them sooner.
RAFFLE_ENTRY_MESSAGE_DELETE_SECONDS = 60 * 60


def _telegram_message_link(chat_id, message_id):
    """Build a Telegram message link for a group/supergroup post."""
    chat_id = int(chat_id)
    if chat_id < 0:
        internal_id = str(abs(chat_id))
        if internal_id.startswith("100"):
            internal_id = internal_id[3:]
        return f"https://t.me/c/{internal_id}/{message_id}"
    return None


async def _delete_raffle_message_job(context):
    job = context.job
    data = job.data if job else None
    if not data:
        return
    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )
    except TelegramError:
        logger.info(
            "Raffle temporary message already gone or could not be deleted | chat=%s message=%s",
            data.get("chat_id"), data.get("message_id"),
        )


async def publish_raffle(raffle_id, context):
    raffle = get_raffle(raffle_id)
    if not raffle:
        return False

    free = is_free_raffle(raffle.get("price"))

    if free:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle_id}")]
        ])
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle_id}")],
            [InlineKeyboardButton("💵 PAY WITH CASH APP", callback_data=f"pay_cashapp_{raffle_id}")],
            [InlineKeyboardButton("🏦 PAY WITH ZELLE", callback_data=f"pay_zelle_{raffle_id}")],
        ])

    payment_notice = (
        "🎟️ Entry is FREE — no payment is required."
        if free
        else "⚠️ Your entry remains pending until an admin verifies your payment."
    )

    text = (
        "🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b>\n\n"
        f"🎁 <b>Prize:</b> {html.escape(str(raffle['prize']))}\n"
        f"💵 <b>Entry:</b> {html.escape(str(raffle['price']))}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle['expires_at'])}\n\n"
        "👇 Tap below to enter.\n\n"
        + payment_notice
    )

    main_chat_id = int(RAFFLE_CHAT_ID)

    try:
        # Telegram allows a maximum of 4096 characters per message.
        # Never split or truncate a raffle. If the rendered raffle is too long,
        # fail cleanly and leave the raffle active for the admin to correct/repost.
        if len(text) > 4096:
            logger.error(
                "Raffle %s is too long to publish as one Telegram message | chars=%s",
                raffle_id, len(text),
            )
            return False

        sent = await context.bot.send_message(
            chat_id=main_chat_id,
            message_thread_id=RAFFLE_GAMES_TOPIC_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        # Keep the raffle tied to the actual Telegram post so existing
        # entry/recovery logic continues to work.
        set_raffle_post(raffle_id, main_chat_id, sent.message_id)

        # Pin the active raffle in the Games topic. The bot must have
        # permission to pin messages in the group.
        try:
            await context.bot.pin_chat_message(
                chat_id=main_chat_id,
                message_id=sent.message_id,
                disable_notification=True,
            )
        except TelegramError:
            logger.exception("Raffle %s posted but could not be pinned.", raffle_id)

        # Send a short notification to the main chat with a direct link
        # back to the raffle post in the Games topic.
        raffle_link = _telegram_message_link(main_chat_id, sent.message_id)
        notification_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎟️ VIEW / ENTER RAFFLE", url=raffle_link)]
        ]) if raffle_link else None

        notification = (
            "🎟️ <b>NEW RAFFLE IS LIVE!</b>\n\n"
            f"🎁 <b>{html.escape(str(raffle['prize']))}</b>\n"
            f"💵 Entry: <b>{html.escape(str(raffle['price']))}</b>\n\n"
            "The raffle is pinned in the 🎮 Games topic.\n"
            "👇 Tap below to view it and enter."
        )

        main_notification = await context.bot.send_message(
            chat_id=main_chat_id,
            text=notification,
            reply_markup=notification_keyboard,
            parse_mode=ParseMode.HTML,
            disable_notification=False,
        )

        # Keep the main-chat notification pinned as the quick link to the
        # official raffle post in the Games topic.
        try:
            await context.bot.pin_chat_message(
                chat_id=main_chat_id,
                message_id=main_notification.message_id,
                disable_notification=True,
            )
        except TelegramError:
            logger.exception(
                "Raffle %s published, but the main-chat notification could not be pinned.",
                raffle_id,
            )

        return True
    except TelegramError:
        logger.exception("Could not publish raffle %s to Games topic.", raffle_id)
        return False

async def approve_raffle_callback(update, context, raffle_id):
    query = update.callback_query
    user = update.effective_user
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
        await query.edit_message_text(
            f"✅ <b>RAFFLE APPROVED</b>\n\n🎁 {raffle['prize']}\n💵 {raffle['price']}\n\nPublishing...",
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        pass
    if await publish_raffle(raffle_id, context):
        try:
            await query.message.reply_text("✅ Raffle is now live in the raffle group.")
        except Exception:
            pass
    else:
        logger.error("Raffle %s approved but publication failed.", raffle_id)

async def cancel_raffle_callback(update, context, raffle_id):
    query = update.callback_query
    user = update.effective_user
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
        await query.edit_message_text(
            f"❌ <b>RAFFLE CANCELLED</b>\n\n🎁 {raffle['prize']}\n💵 {raffle['price']}",
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        pass

async def enter_raffle(update, context, raffle_id):
    query = update.callback_query
    user = update.effective_user
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
        entry_message = await query.message.reply_text(
            f"🎟️ <b>ENTRY APPROVED</b>\n\n"
            f"🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n"
            f"💵 Entry Price: <b>{html.escape(str(raffle['price']))}</b>\n"
            f"🆔 Entry: <code>{entry_id}</code>\n\n"
            "✅ <b>FREE ENTRY — no payment required.</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await query.answer("Entry submitted!", show_alert=True)
        entry_message = await query.message.reply_text(
            f"🎟️ <b>ENTRY SUBMITTED</b>\n\n"
            f"🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n"
            f"💵 Entry Price: <b>{html.escape(str(raffle['price']))}</b>\n"
            f"🆔 Entry: <code>{entry_id}</code>\n\n"
            "⚠️ Your entry is <b>PENDING</b> until an admin verifies payment.",
            parse_mode=ParseMode.HTML,
        )
    await track_entry_message(
        entry_id,
        entry_message,
        "entry_confirmation",
    )
    if not free and context.job_queue and entry_message and entry_message.chat_id == int(RAFFLE_CHAT_ID):
        context.job_queue.run_once(
            _delete_raffle_message_job,
            RAFFLE_ENTRY_MESSAGE_DELETE_SECONDS,
            data={"chat_id": entry_message.chat_id, "message_id": entry_message.message_id},
        )
    keyboard = None if free else InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{entry_id}"),
        InlineKeyboardButton("❌ DENY", callback_data=f"deny_{entry_id}"),
    ]])
    admin_text = (
        ("🎟️ <b>FREE RAFFLE ENTRY — AUTO APPROVED</b>" if free else "🎟️ <b>NEW RAFFLE ENTRY</b>") + "\n\n"
        f"🆔 Entry: <code>{entry_id}</code>\n"
        f"🎟️ Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n"
        f"👤 Member: <b>{name}</b>\n"
        + ("💳 Payment: <b>FREE</b>\n\n" if free else "💳 Payment: <b>Not selected</b>\n\nChoose an action:")
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id), text=admin_text,
                reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
        except TelegramError:
            logger.warning("Could not notify admin %s.", admin_id)

async def payment_method(update, context, raffle_id, method):
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    raffle = get_raffle(raffle_id)
    if not raffle or raffle["status"] != "active":
        await query.answer("Raffle is no longer active.", show_alert=True)
        return
    entry = next(
        (x for x in get_raffle_entries(raffle_id)
         if int(x["user_id"]) == int(user.id) and x["status"] == "pending"),
        None
    )
    if not entry:
        await query.answer("Enter the raffle first.", show_alert=True)
        return
    if is_free_raffle(raffle.get("price")):
        await query.answer("This raffle is free — no payment is required.", show_alert=True)
        return
    if method == "cashapp":
        body = f"💵 <b>CASH APP</b>\n\nSend <b>{raffle['price']}</b> to:\n<code>{CASHAPP_TAG}</code>\n\n{CASHAPP_URL or ''}"
    else:
        body = f"🏦 <b>ZELLE</b>\n\nSend <b>{raffle['price']}</b> to:\n<code>{ZELLE_PHONE}</code>"
    await query.answer()
    payment_message = await query.message.reply_text(
        body + "\n\nAfter payment, your entry remains pending until an admin verifies it.",
        parse_mode=ParseMode.HTML
    )
    if context.job_queue and payment_message and payment_message.chat_id == int(RAFFLE_CHAT_ID):
        context.job_queue.run_once(
            _delete_raffle_message_job,
            RAFFLE_ENTRY_MESSAGE_DELETE_SECONDS,
            data={"chat_id": payment_message.chat_id, "message_id": payment_message.message_id},
        )

async def approve_entry_callback(update, context, entry_id):
    query = update.callback_query
    user = update.effective_user
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

    # Critical: actually commit the pending -> approved transition.
    changed = approve_entry(entry_id, user.id)
    if not changed:
        await query.answer(
            "Entry could not be approved. It may already have been processed.",
            show_alert=True
        )
        return

    logger.info("ENTRY APPROVED | entry=%s | raffle=%s | admin=%s",
                entry_id, entry["raffle_id"], user.id)
    await query.answer("✅ Entry approved!")
    try:
        await query.edit_message_text(
            "✅ <b>ENTRY APPROVED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: <b>{entry.get('prize') or 'Raffle'}</b>\n"
            f"👤 Member: <b>{display_user(entry)}</b>\n"
            f"💳 Payment: <b>{entry.get('payment_method') or 'Verified'}</b>\n\n"
            f"Approved by admin <code>{user.id}</code>.",
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.exception("Could not update approval message for entry %s.", entry_id)

    await track_entry_message(entry_id, query.message, "admin_approval")

    try:
        sent_member = await context.bot.send_message(
            chat_id=int(entry["user_id"]),
            text=(
                "🎉 <b>YOUR RAFFLE ENTRY WAS APPROVED!</b>\n\n"
                f"🎁 Prize: <b>{entry.get('prize') or 'Raffle'}</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\nGood luck! 🍀"
            ),
            parse_mode=ParseMode.HTML,
        )
        await track_entry_message(entry_id, sent_member, "approved_notification")
    except TelegramError:
        logger.info("Could not notify entrant %s.", entry["user_id"])

    schedule_approved_entry_cleanup(
        entry_id,
        int(entry["raffle_id"]),
        context,
    )

    return

async def deny_entry_callback(update, context, entry_id):
    query = update.callback_query
    user = update.effective_user
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
        await query.edit_message_text(
            f"❌ <b>ENTRY DENIED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"👤 Member: <b>{display_user(entry)}</b>\n\n"
            f"Denied by admin <code>{user.id}</code>.",
            parse_mode=ParseMode.HTML
        )
    except TelegramError:
        pass


async def safe_answer(query, text="", show_alert=False):
    """Answer a callback query without allowing an expired callback to crash the bot."""
    if not query:
        return
    try:
        await query.answer(text, show_alert=show_alert)
    except TelegramError:
        logger.info("Could not answer raffle callback query; it may have expired.")


async def temporary_reply(message, context, text, parse_mode=None, delete_after=300):
    """Send a short admin response and optionally remove it later."""
    if not message:
        return None
    try:
        sent = await message.reply_text(text, parse_mode=parse_mode)
    except TelegramError:
        logger.exception("Could not send temporary raffle reply.")
        return None

    if context and context.job_queue and delete_after:
        try:
            context.job_queue.run_once(
                _delete_raffle_message_job,
                delete_after,
                data={"chat_id": sent.chat_id, "message_id": sent.message_id},
                name=f"raffle-temp-{sent.chat_id}-{sent.message_id}",
            )
        except Exception:
            logger.exception("Could not schedule temporary raffle reply cleanup.")
    return sent


async def manual_raffle_entry(update, context, member_user_id):
    """Add a selected member directly to the active raffle as an approved entry."""
    query = update.callback_query
    admin_user = update.effective_user

    if not query or not admin_user:
        return False

    if not is_raffle_admin(admin_user.id):
        await safe_answer(query, "⛔ Admins only.", True)
        return False

    raffle = get_active_raffle()
    if not raffle:
        await safe_answer(query, "There is no active raffle.", True)
        try:
            await query.edit_message_text(
                "⚠️ <b>NO ACTIVE RAFFLE</b>\n\n"
                "There is currently no active raffle to add a manual entry to.\n\n"
                "Start and approve a raffle first.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="admin_back")
                ]]),
            )
        except TelegramError:
            pass
        return False

    try:
        member_user_id = int(member_user_id)
    except (TypeError, ValueError):
        await safe_answer(query, "Invalid member.", True)
        return False

    # Resolve the member from the raffle group first, then from the admin selector cache.
    member = None
    try:
        from raffle_database import get_members
        members = get_members(int(RAFFLE_CHAT_ID))
        for item in members or []:
            try:
                if int(item.get("user_id", 0)) == member_user_id:
                    member = item
                    break
            except (TypeError, ValueError):
                continue
    except Exception:
        logger.exception("Could not load raffle-group members for manual entry.")

    if not member:
        for item in context.user_data.get("admin_manual_raffle_members", []) or []:
            try:
                if int(item.get("user_id", 0)) == member_user_id:
                    member = item
                    break
            except (TypeError, ValueError):
                continue

    if not member:
        await safe_answer(query, "Member could not be found.", True)
        return False

    username = member.get("username")
    display_name = member.get("display_name") or (f"@{username}" if username else None) or str(member_user_id)

    for existing in get_raffle_entries(raffle["id"]):
        try:
            if int(existing["user_id"]) == member_user_id:
                await safe_answer(query, "This member already has an entry in this raffle.", True)
                return False
        except (TypeError, ValueError, KeyError):
            continue

    try:
        entry_id = add_raffle_entry(
            raffle["id"], member_user_id, username, display_name, "manual"
        )
    except Exception:
        logger.exception("Could not create manual raffle entry.")
        entry_id = None

    if entry_id is None:
        await safe_answer(query, "The entry could not be created.", True)
        return False

    try:
        changed = approve_entry(entry_id, admin_user.id)
    except Exception:
        logger.exception("Manual entry approval failed | entry=%s", entry_id)
        changed = False

    if not changed:
        logger.error(
            "Manual entry created but approval failed | entry=%s | member=%s | raffle=%s",
            entry_id, member_user_id, raffle["id"],
        )
        await safe_answer(query, "Entry was created but could not be approved.", True)
        return False

    logger.info(
        "MANUAL RAFFLE ENTRY APPROVED | entry=%s | raffle=%s | member=%s | admin=%s",
        entry_id, raffle["id"], member_user_id, admin_user.id,
    )
    await safe_answer(query, "✅ Manual entry added!")

    try:
        await query.edit_message_text(
            "✅ <b>MANUAL ENTRY ADDED</b>\n\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry Price: <b>{raffle['price']}</b>\n"
            f"👤 Member: <b>{html.escape(str(display_name))}</b>\n"
            f"🆔 User ID: <code>{member_user_id}</code>\n"
            f"🎟️ Entry: <code>{entry_id}</code>\n"
            "💳 Payment: <b>Manual</b>\n"
            "✅ Status: <b>APPROVED</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Another", callback_data="admin_manual_entry")],
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")],
            ]),
        )
    except TelegramError:
        logger.exception("Could not display manual entry result.")

    try:
        await context.bot.send_message(
            chat_id=member_user_id,
            text=(
                "🎟️ <b>YOU HAVE BEEN ADDED TO THE RAFFLE</b>\n\n"
                f"🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "Your raffle entry has been <b>APPROVED</b> by an admin.\n\n"
                "Good luck! 🍀"
            ),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.info("Could not notify manually added member %s.", member_user_id)

    return True


async def repost_raffle(update, context):
    """Repost the active raffle using the current raffle keyboard and topic settings."""
    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if not user or not is_raffle_admin(user.id):
        if query:
            await safe_answer(query, "⛔ Admins only.", True)
        elif message:
            await temporary_reply(message, context, "⛔ Admins only.")
        return False

    raffle = get_active_raffle()
    if not raffle:
        if query:
            await safe_answer(query, "There is no active raffle.", True)
        elif message:
            await temporary_reply(message, context, "⚠️ There is no active raffle to repost.")
        return False

    if query:
        await safe_answer(query, "🔄 Reposting raffle...")

    published = await publish_raffle(int(raffle["id"]), context)
    target = query.message if query else message

    if published:
        if target:
            await temporary_reply(
                target,
                context,
                "✅ <b>RAFFLE REPOSTED</b>\n\n"
                f"🎁 Prize: <b>{html.escape(str(raffle['prize']))}</b>\n"
                f"💵 Entry: <b>{html.escape(str(raffle['price']))}</b>",
                parse_mode=ParseMode.HTML,
            )
        return True

    if target:
        await temporary_reply(
            target,
            context,
            "⚠️ I could not repost the active raffle. Check the bot's permissions in the raffle group.",
        )
    return False


async def raffle_callback(update, context):
    """Single callback router for ALL raffle callbacks."""
    query = update.callback_query
    if not query:
        return
    data = query.data or ""
    logger.info("Raffle callback received: %s", data)

    if data.startswith("raffle_approve_"):
        value = data[len("raffle_approve_"):]
        if value.isdigit():
            await approve_raffle_callback(update, context, int(value))
        else:
            await query.answer("Invalid raffle ID.", show_alert=True)
        return

    if data.startswith("raffle_cancel_"):
        value = data[len("raffle_cancel_"):]
        if value.isdigit():
            await cancel_raffle_callback(update, context, int(value))
        else:
            await query.answer("Invalid raffle ID.", show_alert=True)
        return

    if data.startswith("approve_"):
        value = data[len("approve_"):]
        if value.isdigit():
            await approve_entry_callback(update, context, int(value))
        else:
            await query.answer("Invalid entry ID.", show_alert=True)
        return

    if data.startswith("deny_"):
        value = data[len("deny_"):]
        if value.isdigit():
            await deny_entry_callback(update, context, int(value))
        else:
            await query.answer("Invalid entry ID.", show_alert=True)
        return

    if data.startswith("enter_"):
        value = data[len("enter_"):]
        if value.isdigit():
            await enter_raffle(update, context, int(value))
        else:
            await query.answer("Invalid raffle ID.", show_alert=True)
        return

    if data.startswith("pay_cashapp_"):
        value = data[len("pay_cashapp_"):]
        if value.isdigit():
            await payment_method(update, context, int(value), "cashapp")
        else:
            await query.answer("Invalid raffle ID.", show_alert=True)
        return

    if data.startswith("pay_zelle_"):
        value = data[len("pay_zelle_"):]
        if value.isdigit():
            await payment_method(update, context, int(value), "zelle")
        else:
            await query.answer("Invalid raffle ID.", show_alert=True)
        return

    await query.answer()
    logger.warning("Unhandled raffle callback: %s", data)

async def raffle_status(update, context):
    query = update.callback_query
    message = update.effective_message
    user = update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query: await query.answer("⛔ Admins only.", show_alert=True)
        return
    raffle = get_active_raffle()
    if not raffle:
        text = "🎟️ <b>RAFFLE STATUS</b>\n\nThere is currently no active raffle."
    else:
        approved = get_approved_entries(raffle["id"])
        pending = get_pending_entries(raffle["id"])
        text = (
            "🎟️ <b>RAFFLE STATUS</b>\n\n"
            f"🆔 ID: <code>{raffle['id']}</code>\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n"
            f"⏰ Ends: <b>{format_expiration(raffle['expires_at'])}</b>\n\n"
            f"✅ Approved Entries: <b>{len(approved)}</b>\n"
            f"⏳ Pending Entries: <b>{len(pending)}</b>"
        )
    if query: await query.answer()
    target = query.message if query else message
    if target: await target.reply_text(text, parse_mode=ParseMode.HTML)

async def raffle_entries(update, context):
    query = update.callback_query
    message = update.effective_message
    user = update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query: await query.answer("⛔ Admins only.", show_alert=True)
        return
    raffle = get_active_raffle()
    if not raffle:
        text = "🎟️ <b>RAFFLE ENTRIES</b>\n\nNo active raffle."
    else:
        entries = get_approved_entries(raffle["id"])
        text = "🎟️ <b>APPROVED ENTRIES</b>\n\n" + (
            "\n".join(f"{i}. {display_user(e)} (Entry #{e['id']})"
                      for i, e in enumerate(entries, 1))
            if entries else "No approved entries yet."
        )
    if query: await query.answer()
    target = query.message if query else message
    if target: await target.reply_text(text, parse_mode=ParseMode.HTML)

async def pending_entries(update, context):
    query = update.callback_query
    message = update.effective_message
    user = update.effective_user
    if not user or not await is_raffle_admin_access(update, context):
        if query: await query.answer("⛔ Admins only.", show_alert=True)
        return
    pending = get_pending_entries()
    if query: await query.answer()
    target = query.message if query else message
    if not target: return
    if not pending:
        await target.reply_text("⏳ <b>PENDING RAFFLE ENTRIES</b>\n\nThere are no pending entries.",
                                parse_mode=ParseMode.HTML)
        return
    for entry in pending:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{entry['id']}"),
            InlineKeyboardButton("❌ DENY", callback_data=f"deny_{entry['id']}")
        ]])
        text = (
            "⏳ <b>PENDING RAFFLE ENTRY</b>\n\n"
            f"🆔 Entry: <code>{entry['id']}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: <b>{entry.get('prize') or 'Unknown'}</b>\n"
            f"💵 Price: <b>{entry.get('price') or 'Unknown'}</b>\n"
            f"👤 Member: <b>{display_user(entry)}</b>\n"
            f"💳 Payment: <b>{entry.get('payment_method') or 'Not selected'}</b>\n\n"
            "Choose an action:"
        )
        try:
            await target.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except TelegramError:
            logger.exception("Could not display pending entry %s.", entry["id"])

async def paid_entry(update, context):
    # Kept as the admin-menu command expected by bot.py.
    return await raffle_entries(update, context)

async def cancel_raffle(update, context):
    query = update.callback_query
    message = update.effective_message
    user = update.effective_user
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
    query = update.callback_query
    message = update.effective_message
    user = update.effective_user
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
    text = (
        "🎉 <b>RAFFLE WINNER!</b>\n\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n\n"
        f"🏆 Winner: <b>{display_user(winner)}</b>\n"
        f"🆔 Entry: <code>{winner['id']}</code>\n\n🎉 Congratulations!"
    )
    if query: await query.answer("Winner selected!")
    target = query.message if query else message
    if target: await target.reply_text(text, parse_mode=ParseMode.HTML)
