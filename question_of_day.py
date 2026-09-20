# ==========================================================
# Melanated AZ Bot - Question of the Day
# question_of_day.py
#
# Persistent Question / Poll bank with one daily release.
# ==========================================================

import json
import logging
import os
import sqlite3
from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger("question_of_day")

QOTD_DB = "/var/data/question_of_day.db" if os.path.isdir("/var/data") else "./question_of_day.db"
QOTD_TZ = ZoneInfo("America/Phoenix")
QOTD_MAX_QUESTION = 3000
QOTD_MAX_OPTION = 100
QOTD_MIN_OPTIONS = 2
QOTD_MAX_OPTIONS = 10
QOTD_PANEL_LOCK_TTL_SECONDS = 120


def _int_env(name, default=0):
    try:
        return int(os.environ.get(name, str(default)) or str(default)
    except (TypeError, ValueError):
        return default


QUESTION_OF_DAY_TOPIC_ID = _int_env("QUESTION_OF_DAY_TOPIC_ID", 0)
QUESTION_OF_DAY_CHAT_ID = _int_env("QUESTION_OF_DAY_CHAT_ID", 0)
QUESTION_OF_DAY_HOUR = max(0, min(23, _int_env("QUESTION_OF_DAY_HOUR", 11)))
QUESTION_OF_DAY_MINUTE = max(0, min(59, _int_env("QUESTION_OF_DAY_MINUTE", 0)))


def qotd_chat_id():
    configured = QUESTION_OF_DAY_CHAT_ID
    if configured:
        return configured
    try:
        return int(os.environ.get("MAIN_GROUP_ID", "0") or "0")
    except (TypeError, ValueError):
        return 0


def qotd_enabled():
    return bool(qotd_chat_id() and QUESTION_OF_DAY_TOPIC_ID)


def db_connect():
    conn = sqlite3.connect(QOTD_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_question_of_day_database():
    os.makedirs(os.path.dirname(QOTD_DB) or ".", exist_ok=True)
    with db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS qotd_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL CHECK(item_type IN ('question','poll')),
                prompt TEXT NOT NULL,
                options_json TEXT,
                submitted_by INTEGER,
                submitted_name TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                posted_at TEXT,
                posted_message_id INTEGER,
                posted_date TEXT,
                voice_file_id TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS qotd_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(qotd_items)").fetchall()}
        if "voice_file_id" not in columns:
            conn.execute("ALTER TABLE qotd_items ADD COLUMN voice_file_id TEXT")
        conn.commit()


def phoenix_now():
    return datetime.now(QOTD_TZ)


def today_key():
    return phoenix_now().date().isoformat()


def get_meta(key):
    with db_connect() as conn:
        row = conn.execute("SELECT value FROM qotd_meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else None


def set_meta(key, value):
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO qotd_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
        conn.commit()


def daily_post_already_done():
    return get_meta("last_daily_post_date") == today_key()


def queued_count():
    with db_connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM qotd_items WHERE status='queued'").fetchone()
        return int(row[0]) if row else 0


def get_next_item(item_id=None):
    with db_connect() as conn:
        if item_id is not None:
            return conn.execute(
                "SELECT * FROM qotd_items WHERE id=? AND status='queued'", (item_id,)
            ).fetchone()
        return conn.execute(
            "SELECT * FROM qotd_items WHERE status='queued' ORDER BY id ASC LIMIT 1"
        ).fetchone()


def add_item(item_type, prompt, options, user, voice_file_id=None):
    now = phoenix_now().isoformat()
    options_json = json.dumps(options, ensure_ascii=False) if options else None
    display_name = None
    if user:
        display_name = user.full_name or user.username or str(user.id)
    with db_connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO qotd_items
                (item_type,prompt,options_json,submitted_by,submitted_name,created_at,status,voice_file_id)
            VALUES (?,?,?,?,?,?,'queued',?)
            """,
            (item_type, prompt, options_json, user.id if user else None, display_name, now, voice_file_id),
        )
        conn.commit()
        return cur.lastrowid


def mark_posted(item_id, message_id):
    now = phoenix_now().isoformat()
    with db_connect() as conn:
        conn.execute(
            """
            UPDATE qotd_items
            SET status='posted', posted_at=?, posted_message_id=?, posted_date=?
            WHERE id=? AND status='queued'
            """,
            (now, message_id, today_key(), item_id),
        )
        conn.commit()
    set_meta("last_daily_post_date", today_key())


def restore_item(item_id):
    with db_connect() as conn:
        conn.execute("UPDATE qotd_items SET status='queued' WHERE id=? AND status='posting'", (item_id,))
        conn.commit()


def claim_item(item_id):
    with db_connect() as conn:
        cur = conn.execute(
            "UPDATE qotd_items SET status='posting' WHERE id=? AND status='queued'",
            (item_id,),
        )
        conn.commit()
        return cur.rowcount == 1


def qotd_menu_markup():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📝 Type a Question", callback_data="qotd_submit_question")],
            [InlineKeyboardButton("🎙️ Record a Question", callback_data="qotd_submit_voice")],
            [InlineKeyboardButton("📊 Build a Poll", callback_data="qotd_submit_poll")],
            [InlineKeyboardButton("📚 Bank Status", callback_data="qotd_status")],
            [InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")],
        ]
    )


async def ensure_qotd_submission_panel(application):
    """Create the permanent QOTD submission panel and pin it in the QOTD topic."""
    if not qotd_enabled():
        return
    chat_id = qotd_chat_id()
    thread_id = QUESTION_OF_DAY_TOPIC_ID
    existing_id = get_meta("qotd_submission_panel_message_id")
    if existing_id:
        try:
            await application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=int(existing_id),
                text=(
                    "💭 <b>QUESTION OF THE DAY</b>\n\n"
                    "Have a question for the community? Want to build a poll?\n\n"
                    "Use the buttons below to submit content to the QOTD bank. "
                    "One item is posted each day at <b>11:00 AM Arizona time</b>.\n\n"
                    "📚 Your submission is saved for a future day unless today's QOTD has not been posted yet."
                ),
                reply_markup=qotd_menu_markup(),
                parse_mode="HTML",
            )
            await application.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=int(existing_id),
                disable_notification=True,
            )
            logger.info(
                "QOTD submission panel refreshed and pinned | chat=%s topic=%s message=%s",
                chat_id, thread_id, existing_id,
            )
            return
        except TelegramError:
            logger.warning(
                "Stored QOTD panel %s could not be refreshed; clearing stale panel ID and creating a replacement.",
                existing_id,
            )
            with db_connect() as conn:
                conn.execute("DELETE FROM qotd_meta WHERE key=?", ("qotd_submission_panel_message_id",))
                conn.commit()
    creation_claimed = False
    now_ts = int(datetime.now().timestamp())
    with db_connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT value FROM qotd_meta WHERE key=?",
            ("qotd_submission_panel_creation_lock",),
        ).fetchone()
        if row:
            try:
                lock_ts = int(row[0])
            except (TypeError, ValueError):
                lock_ts = 0
            if now_ts - lock_ts >= QOTD_PANEL_LOCK_TTL_SECONDS:
                conn.execute(
                    "DELETE FROM qotd_meta WHERE key=?",
                    ("qotd_submission_panel_creation_lock",),
                )
                row = None
        if not row:
            conn.execute(
                "INSERT OR REPLACE INTO qotd_meta(key,value) VALUES(?,?)",
                ("qotd_submission_panel_creation_lock", str(now_ts)),
            )
            creation_claimed = True
        conn.commit()

    if not creation_claimed:
        logger.info(
            "QOTD submission panel creation skipped: another process owns the active creation lock."
        )
        return

    try:
        canonical_id = get_meta("qotd_submission_panel_message_id")
        if canonical_id:
            try:
                await application.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=int(canonical_id),
                    text=(
                        "💭 <b>QUESTION OF THE DAY</b>\n\n"
                        "Have a question for the community? Want to build a poll?\n\n"
                        "Use the buttons below to submit content to the QOTD bank. "
                        "One item is posted each day at <b>11:00 AM Arizona time</b>.\n\n"
                        "📚 Your submission is saved for a future day unless today's QOTD has not been posted yet."
                    ),
                    reply_markup=qotd_menu_markup(),
                    parse_mode="HTML",
                )
                await application.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=int(canonical_id),
                    disable_notification=True,
                )
                logger.info(
                    "QOTD submission panel refreshed after creation-lock recheck | chat=%s topic=%s message=%s",
                    chat_id, thread_id, canonical_id,
                )
                return
            except TelegramError:
                with db_connect() as conn:
                    conn.execute("DELETE FROM qotd_meta WHERE key=?", ("qotd_submission_panel_message_id",))
                    conn.commit()
        panel = await application.bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=(
                "💭 <b>QUESTION OF THE DAY</b>\n\n"
                "Have a question for the community? Want to build a poll?\n\n"
                "Use the buttons below to submit content to the QOTD bank. "
                "One item is posted each day at <b>11:00 AM Arizona time</b>.\n\n"
                "📚 Your submission is saved for a future day unless today's QOTD has not been posted yet."
            ),
            reply_markup=qotd_menu_markup(),
            parse_mode="HTML",
        )

        set_meta("qotd_submission_panel_message_id", panel.message_id)

        try:
            await application.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=panel.message_id,
                disable_notification=True,
            )
            logger.info(
                "QOTD submission panel created and pinned | chat=%s topic=%s message=%s",
                chat_id, thread_id, panel.message_id,
            )
        except TelegramError:
            logger.exception(
                "QOTD panel was posted but could not be pinned | chat=%s topic=%s message=%s",
                chat_id, thread_id, panel.message_id,
            )
    except TelegramError:
        logger.exception(
            "Could not create the QOTD submission panel | chat=%s topic=%s",
            chat_id, thread_id,
        )
    finally:
        with db_connect() as conn:
            conn.execute(
                "DELETE FROM qotd_meta WHERE key=?",
                ("qotd_submission_panel_creation_lock",),
            )
            conn.commit()


async def qotd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not qotd_enabled():
        await update.effective_message.reply_text(
            "💭 Question of the Day is not configured yet. An admin needs to set QUESTION_OF_DAY_TOPIC_ID in Render."
        )
        return
    if update.effective_chat.type in ("group", "supergroup"):
        thread_id = update.effective_message.message_thread_id
        if thread_id != QUESTION_OF_DAY_TOPIC_ID:
            await update.effective_message.reply_text("💭 Please use /qotd inside the Question of the Day topic.")
            return
    sent = await update.effective_message.reply_text(
        "💭 <b>QUESTION OF THE DAY</b>\n\nSubmit something for the community to answer, or build a poll for a future day.",
        reply_markup=qotd_menu_markup(),
        parse_mode="HTML",
        message_thread_id=QUESTION_OF_DAY_TOPIC_ID if update.effective_chat.type in ("group", "supergroup") else None,
    )
    if context.job_queue and update.effective_chat.type in ("group", "supergroup"):
        context.job_queue.run_once(
            _delete_message_job,
            30,
            data=(sent.chat_id, sent.message_id),
            name=f"qotd-temp-{sent.message_id}",
        )


async def qotd_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    action = query.data
    await query.answer()

    if action == "qotd_status":
        count = queued_count()
        await query.answer(f"{count} day{'s' if count != 1 else ''} in the bank.", show_alert=True)
        return

    if action == "qotd_cancel":
        for key in ("qotd_state", "qotd_prompt", "qotd_chat_id", "qotd_thread_id"):
            context.user_data.pop(key, None)
        try:
            await query.edit_message_text("💭 Submission cancelled.")
        except TelegramError:
            pass
        return

    if action == "qotd_submit_voice":
        context.user_data["qotd_state"] = "voice"
        context.user_data["qotd_chat_id"] = None
        context.user_data["qotd_thread_id"] = None
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="🎙️ <b>Record your Question of the Day</b>\n\n🔒 Send me a voice recording here. Your recording stays in this private chat and will not appear in the group until it is posted as the QOTD.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]),
            )
            await query.answer("📩 Check your private chat with Melanated AZ Bot and send your recording there.", show_alert=True)
        except TelegramError:
            await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
        return

    if action == "qotd_submit_question":
        context.user_data["qotd_state"] = "question"
        context.user_data["qotd_chat_id"] = None
        context.user_data["qotd_thread_id"] = None
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="📝 <b>Send your question now.</b>\n\n🔒 Your submission is private and will not appear in the group until it is posted as the QOTD.\n\nKeep it under 3,000 characters.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]),
            )
            await query.answer("📩 Check your private chat with Melanated AZ Bot and send your question there.", show_alert=True)
        except TelegramError:
            await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
        return

    if action == "qotd_submit_poll":
        context.user_data["qotd_state"] = "poll_question"
        context.user_data["qotd_chat_id"] = None
        context.user_data["qotd_thread_id"] = None
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="📊 <b>Build your poll</b>\n\n🔒 Your poll submission is private and will not appear in the group until it is posted as the QOTD.\n\nFirst, send the poll question. Then I'll ask for the answer choices.\n\nQuestion limit: 300 characters.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]),
            )
        except TelegramError:
            await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
        return


class QotdInputFilter(filters.MessageFilter):
    name = "QotdInputFilter"

    def filter(self, message):
        return bool(message and message.from_user)


async def qotd_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("qotd_state")
    if not state:
        return
    message = update.effective_message
    if not message:
        return
    if message.chat.type != "private":
        return

    if state == "voice":
        if not message.voice:
            await message.reply_text("❌ Please send a voice recording.")
            raise ApplicationHandlerStop
        item_id = add_item("question", None, None, update.effective_user, voice_file_id=message.voice.file_id)
        await _finish_submission(update, context, item_id, "🎙️ Voice question saved!")
        raise ApplicationHandlerStop

    if not message.text:
        return
    text = message.text.strip()

    if state == "question":
        if not 1 <= len(text) <= QOTD_MAX_QUESTION:
            await message.reply_text("❌ That question must be between 1 and 3,000 characters.")
            raise ApplicationHandlerStop
        item_id = add_item("question", text, None, update.effective_user)
        await _finish_submission(update, context, item_id, "📝 Question saved!")
        raise ApplicationHandlerStop

    if state == "poll_question":
        if not 1 <= len(text) <= 300:
            await message.reply_text("❌ Poll questions must be between 1 and 300 characters.")
            raise ApplicationHandlerStop
        context.user_data["qotd_state"] = "poll_options"
        context.user_data["qotd_prompt"] = text
        await message.reply_text(
            "📊 Now send the answer choices separated by <b>|</b>.\n\nExample:\n<code>Yes | No | Maybe</code>\n\nUse 2–10 choices, with each choice under 100 characters.",
            parse_mode="HTML",
        )
        raise ApplicationHandlerStop

    if state == "poll_options":
        options = [part.strip() for part in text.split("|") if part.strip()]
        if not QOTD_MIN_OPTIONS <= len(options) <= QOTD_MAX_OPTIONS:
            await message.reply_text("❌ A poll needs 2–10 answer choices separated by |.")
            raise ApplicationHandlerStop
        if any(len(option) > QOTD_MAX_OPTION for option in options):
            await message.reply_text("❌ Each poll choice must be 100 characters or fewer.")
            raise ApplicationHandlerStop
        prompt = context.user_data.get("qotd_prompt", "").strip()
        item_id = add_item("poll", prompt, options, update.effective_user)
        await _finish_submission(update, context, item_id, "📊 Poll saved!")
        raise ApplicationHandlerStop


async def _finish_submission(update, context, item_id, saved_text):
    message = update.effective_message
    chat_id = message.chat_id if message and message.chat.type == "private" else None

    for key in ("qotd_state", "qotd_prompt", "qotd_chat_id", "qotd_thread_id"):
        context.user_data.pop(key, None)

    logger.info("QOTD submission saved to bank | item_id=%s | queued=%s", item_id, queued_count())

    if chat_id:
        try:
            count = queued_count()
            notice = await context.bot.send_message(
                chat_id=chat_id,
                text=f"{saved_text}\n\n📚 Added to the Question of the Day bank.\n<b>{count}</b> day{'s' if count != 1 else ''} currently queued.",
                parse_mode="HTML",
            )
            if context.job_queue:
                context.job_queue.run_once(_delete_message_job, 60, data=(chat_id, notice.message_id))
        except TelegramError:
            logger.exception("Could not send QOTD submission confirmation.")


async def _delete_message_job(context):
    data = context.job.data if context.job else None
    if not data:
        return
    try:
        await context.bot.delete_message(chat_id=data[0], message_id=data[1])
    except TelegramError:
        pass


async def publish_item(context, item_id=None):
    if not qotd_enabled():
        logger.warning("Question of the Day disabled: set QUESTION_OF_DAY_TOPIC_ID and MAIN_GROUP_ID/QUESTION_OF_DAY_CHAT_ID.")
        return False
    item = get_next_item(item_id)
    if not item or not claim_item(item["id"]):
        return False
    chat_id = qotd_chat_id()
    thread_id = QUESTION_OF_DAY_TOPIC_ID
    try:
        if item["voice_file_id"]:
            sent = await context.bot.send_voice(
                chat_id=chat_id,
                message_thread_id=thread_id,
                voice=item["voice_file_id"],
                caption="🎙️ <b>QUESTION OF THE DAY</b>",
                parse_mode="HTML",
            )
        elif item["item_type"] == "question":
            from html import escape
            text = "💭 <b>QUESTION OF THE DAY</b>\n\n" + escape(item["prompt"] or "")
            sent = await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                text=text,
                parse_mode="HTML",
            )
        elif item["item_type"] == "voice":
            sent = await context.bot.send_voice(
                chat_id=chat_id,
                message_thread_id=thread_id,
                voice=item["prompt"],
                caption="🎙️ <b>QUESTION OF THE DAY</b>",
                parse_mode="HTML",
            )
        else:
            options = json.loads(item["options_json"] or "[]")
            poll_question = "📊 Question of the Day\n" + item["prompt"]
            sent = await context.bot.send_poll(
                chat_id=chat_id,
                message_thread_id=thread_id,
                question=poll_question[:300],
                options=options,
                is_anonymous=True,
                type="regular",
                allows_multiple_answers=False,
            )
        mark_posted(item["id"], sent.message_id)
        logger.info("QOTD POSTED | item=%s type=%s date=%s", item["id"], item["item_type"], today_key())
        return True
    except TelegramError:
        restore_item(item["id"])
        logger.exception("Question of the Day post failed for item %s", item["id"])
        return False


async def question_of_day_daily_job(context: ContextTypes.DEFAULT_TYPE):
    if not qotd_enabled() or daily_post_already_done():
        return
    item = get_next_item()
    if not item:
        logger.info("QOTD daily run: bank empty; nothing posted.")
        return
    await publish_item(context, item["id"])


async def question_of_day_startup_job(context: ContextTypes.DEFAULT_TYPE):
    # Startup must NEVER publish a QOTD. Publishing here caused every bot
    # restart after the scheduled time to consume another queued entry.
    # The daily scheduler is the only normal publishing path.
    if qotd_enabled():
        await ensure_qotd_submission_panel(context.application)
    logger.info(
        "QOTD startup check complete | panel ensured | no QOTD publish on startup | queued=%s",
        queued_count(),
    )


def start_question_of_day_scheduler(application):
    initialize_question_of_day_database()
    if not application.job_queue:
        logger.warning("QOTD disabled: JobQueue is not available.")
        return
    if not qotd_enabled():
        logger.info("QOTD scheduler waiting for QUESTION_OF_DAY_TOPIC_ID.")
        return
    scheduled_time = time(QUESTION_OF_DAY_HOUR, QUESTION_OF_DAY_MINUTE, tzinfo=QOTD_TZ)
    application.job_queue.run_daily(
        question_of_day_daily_job,
        time=scheduled_time,
        name="question-of-day-daily",
    )
    application.job_queue.run_once(
        question_of_day_startup_job,
        when=5,
        name="question-of-day-startup-check",
    )
    logger.info(
        "QOTD scheduler enabled | chat=%s topic=%s | daily=%02d:%02d America/Phoenix | queued=%s",
        qotd_chat_id(),
        QUESTION_OF_DAY_TOPIC_ID,
        QUESTION_OF_DAY_HOUR,
        QUESTION_OF_DAY_MINUTE,
        queued_count(),
    )


def register_question_of_day_handlers(application):
    initialize_question_of_day_database()
    application.add_handler(CommandHandler("qotd", qotd_command), group=0)
    application.add_handler(
        CallbackQueryHandler(
            qotd_callback,
            pattern=r"^qotd_(submit_question|submit_voice|submit_poll|status|cancel)$",
        ),
        group=0,
    )
    application.add_handler(
        MessageHandler(QotdInputFilter() & filters.TEXT & ~filters.COMMAND, qotd_text_handler),
        group=-1,
    )
    application.add_handler(
        MessageHandler(QotdInputFilter() & filters.VOICE, qotd_text_handler),
        group=-1,
    )
