# ==========================================================
# Melanated AZ Bot
# bot.py
#
# COMPLETE CLEAN DROP-IN LAUNCHER
#
# Includes:
#   - Existing raffle system
#   - Existing birthday system
#   - Existing Game Center
#   - Existing Truth or Dare
#   - Existing media moderation
#   - NEW separate Real Games system
#   - NEW Monopoly web game
#   - NEW Telegram deep-links for Real Games
#
# IMPORTANT:
#   - Existing games/ package is NOT replaced.
#   - Existing raffle database is NOT replaced.
#   - Existing raffle callbacks remain owned by raffle.py.
#   - Real Games lives separately in real_games/.
# ==========================================================

import logging
import os
import threading
import sqlite3
import random
from datetime import datetime, timedelta, timezone

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)

from telegram.constants import ParseMode

from telegram.error import (
    TelegramError,
    BadRequest,
)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ChatMemberHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
)

from admin import (
    admin_menu,
    admin_button,
    admin_birthday_text_handler,
    is_admin,
)

from birthday import (
    birthday,
    my_birthday,
    remove_my_birthday,
    birthday_callback,
    birthday_text_handler,
)

from raffle import (
    start_raffle,
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
    raffle_callback,
)

from raffle_database import (
    get_database_stats,
    check_database_integrity,
)

from truth_dare import (
    truth,
    dare,
    truth_dare_menu,
    truth_dare_callback,
)

# ----------------------------------------------------------
# EXISTING GAME CENTER
# ----------------------------------------------------------

from games.game_center import (
    games_command,
    game_center_callback_router,
    initialize_game_database,
)

# ----------------------------------------------------------
# NEW REAL GAMES
#
# This is completely separate from games/
# ----------------------------------------------------------

from real_games import (
    real_games_bp,
    handle_real_game_deep_link,
)

from real_games.monopoly import (
    monopoly_bp,
)


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(
    "melanated_az_bot"
)


# ==========================================================
# STARTUP INFORMATION
# ==========================================================

logger.info(
    "=========================================================="
)

logger.info(
    "Starting Melanated AZ Bot"
)

logger.info(
    "Loaded Admin IDs: %s",
    list(ADMIN_IDS),
)

logger.info(
    "Raffle Chat ID: %s",
    RAFFLE_CHAT_ID,
)

logger.info(
    "=========================================================="
)


# ==========================================================
# FLASK HEALTH SERVER
# ==========================================================

app = Flask(__name__)


# ----------------------------------------------------------
# EXISTING HEALTH ROUTES
# ----------------------------------------------------------

@app.route("/")
def health_check():

    return (
        "Melanated AZ Bot is running.",
        200,
    )


@app.route("/health")
def health():

    return (
        "OK",
        200,
    )


# ----------------------------------------------------------
# NEW REAL GAMES ROUTES
#
# These do NOT interfere with the existing health routes.
# ----------------------------------------------------------

app.register_blueprint(
    real_games_bp
)

app.register_blueprint(
    monopoly_bp
)

logger.info(
    "Real Games web routes registered."
)

logger.info(
    "Real Games URL: /real-games/"
)

logger.info(
    "Monopoly URL: /real-games/monopoly/"
)


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
    )

    logger.info(
        "Starting Flask on port %s",
        port,
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ==========================================================
# MESSAGE DELETION
# ==========================================================

async def delete_message_later(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:
        return

    data = job.data or {}

    if (
        data.get("chat_id") is None
        or data.get("message_id") is None
    ):
        return

    try:

        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )

    except TelegramError:

        pass


async def delete_after(
    context: ContextTypes.DEFAULT_TYPE,
    message,
    seconds=30,
):

    if message and context.job_queue:

        context.job_queue.run_once(
            delete_message_later,
            when=seconds,
            data={
                "chat_id": message.chat_id,
                "message_id": message.message_id,
            },
        )


# ==========================================================
# BOT USERNAME
# ==========================================================

async def get_bot_username(
    context: ContextTypes.DEFAULT_TYPE,
):

    username = (
        context.application.bot_data.get(
            "bot_username"
        )
    )

    if username:
        return username

    try:

        me = await context.bot.get_me()

        username = me.username

        if username:

            context.application.bot_data[
                "bot_username"
            ] = username

        return username

    except Exception:

        logger.exception(
            "Could not retrieve bot username."
        )

        return None


# ==========================================================
# MEDIA MODERATION
# ==========================================================

MEDIA_WARNING_SECONDS = 30


async def send_media_warning(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    username = await get_bot_username(
        context
    )

    keyboard = (
        InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "🤖 Post with Melanated AZ Bot",
                    url=f"https://t.me/{username}",
                )
            ]]
        )
        if username
        else None
    )

    text = (
        "⚠️ <b>Media Spoiler Required</b>\n\n"
        f"{user.mention_html()}, your photo/video "
        "was removed because it was not marked "
        "as a spoiler.\n\n"
        "Please resend the media using Telegram's "
        "🚫 <b>Spoiler</b> option."
    )

    try:

        warning = await context.bot.send_message(
            chat_id=message.chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        await delete_after(
            context,
            warning,
            MEDIA_WARNING_SECONDS,
        )

    except TelegramError:

        logger.exception(
            "Could not send media warning."
        )


async def send_private_media_warning(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    username = await get_bot_username(
        context
    )

    keyboard = (
        InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "🤖 Open Melanated AZ Bot",
                    url=f"https://t.me/{username}",
                )
            ]]
        )
        if username
        else None
    )

    text = (
        "👋 Hey! This is the Melanated AZ Bot "
        "from the Melanated AZ group.\n\n"
        "Your photo/video was removed because "
        "Telegram's Spoiler option was not enabled.\n\n"
        "📸 <b>How to post it correctly:</b>\n\n"
        "1️⃣ Select your photo or video.\n"
        "2️⃣ Tap the ⋮ menu/options.\n"
        "3️⃣ Select <b>Hide with Spoiler</b>.\n"
        "4️⃣ Send the media."
    )

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.info(
            "Could not send private media warning "
            "to %s.",
            user.id,
        )


async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if message.has_media_spoiler:
        return

    try:

        await message.delete()

    except TelegramError:

        pass

    await send_media_warning(
        update,
        context,
    )

    await send_private_media_warning(
        update,
        context,
    )


async def handle_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if message.has_media_spoiler:
        return

    try:

        await message.delete()

    except TelegramError:

        pass

    await send_media_warning(
        update,
        context,
    )

    await send_private_media_warning(
        update,
        context,
    )


async def handle_animation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    return


async def handle_image_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    return


# ==========================================================
# COMMUNITY HUMAN VERIFICATION + INTRO SYSTEM
# ==========================================================

COMMUNITY_DB = (
    "/var/data/community_security.db"
    if os.path.isdir("/var/data")
    else "./community_security.db"
)

INTRO_HOURS = 48
VERIFICATION_MAX_ATTEMPTS = 3
VERIFICATION_MESSAGE_TTL_MINUTES = 5

HUMAN_CHALLENGES = [
    ("🍎 Apple", ["🍎 Apple", "🚗 Car", "👟 Shoe"]),
    ("🐶 Dog", ["🌳 Tree", "🐶 Dog", "🚲 Bike"]),
    ("🌙 Moon", ["🍕 Pizza", "🌙 Moon", "🎸 Guitar"]),
    ("🚗 Car", ["🚗 Car", "🍌 Banana", "🎧 Headphones"]),
    ("🐟 Fish", ["📱 Phone", "🐟 Fish", "👕 Shirt"]),
    ("☀️ Sun", ["☀️ Sun", "🍔 Burger", "⚽ Ball"]),
    ("🍕 Pizza", ["🪑 Chair", "🍕 Pizza", "🌴 Palm Tree"]),
    ("🎸 Guitar", ["🎸 Guitar", "🥤 Drink", "🧢 Hat"]),
]


def community_db_connect():
    conn = sqlite3.connect(COMMUNITY_DB)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_community_security_database():
    os.makedirs(os.path.dirname(COMMUNITY_DB) or ".", exist_ok=True)
    with community_db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS community_members (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                joined_at TEXT,
                verified_at TEXT,
                intro_deadline TEXT,
                intro_posted_at TEXT,
                last_post_at TEXT,
                verification_attempts INTEGER DEFAULT 0,
                verification_message_id INTEGER,
                verification_challenge TEXT,
                verification_expires_at TEXT,
                status TEXT DEFAULT 'pending_verification',
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        conn.commit()


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def community_member(chat_id, user_id):
    with community_db_connect() as conn:
        return conn.execute(
            "SELECT * FROM community_members WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        ).fetchone()


def save_joining_member(chat_id, user):
    joined = utc_now()
    with community_db_connect() as conn:
        conn.execute("""
            INSERT INTO community_members
                (chat_id, user_id, username, first_name, joined_at, status)
            VALUES (?, ?, ?, ?, ?, 'pending_verification')
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                joined_at=excluded.joined_at,
                verified_at=NULL,
                intro_deadline=NULL,
                intro_posted_at=NULL,
                last_post_at=NULL,
                verification_attempts=0,
                verification_message_id=NULL,
                verification_challenge=NULL,
                verification_expires_at=NULL,
                status='pending_verification'
        """, (
            chat_id,
            user.id,
            user.username,
            user.first_name,
            joined.isoformat(),
        ))
        conn.commit()


def set_verification_challenge(chat_id, user_id, answer, options, message_id):
    expires = utc_now() + timedelta(minutes=VERIFICATION_MESSAGE_TTL_MINUTES)
    payload = "|||".join(options)
    with community_db_connect() as conn:
        conn.execute("""
            UPDATE community_members
            SET verification_challenge=?,
                verification_expires_at=?,
                verification_message_id=?
            WHERE chat_id=? AND user_id=?
        """, (
            answer + "###" + payload,
            expires.isoformat(),
            message_id,
            chat_id,
            user_id,
        ))
        conn.commit()


def increment_verification_attempt(chat_id, user_id):
    with community_db_connect() as conn:
        conn.execute("""
            UPDATE community_members
            SET verification_attempts=verification_attempts+1
            WHERE chat_id=? AND user_id=?
        """, (chat_id, user_id))
        conn.commit()
        row = conn.execute(
            "SELECT verification_attempts FROM community_members WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        ).fetchone()
        return int(row[0]) if row else VERIFICATION_MAX_ATTEMPTS


def mark_verified(chat_id, user_id):
    now = utc_now()
    deadline = now + timedelta(hours=INTRO_HOURS)
    with community_db_connect() as conn:
        conn.execute("""
            UPDATE community_members
            SET verified_at=?,
                intro_deadline=?,
                status='verified_intro_pending',
                verification_challenge=NULL,
                verification_expires_at=NULL
            WHERE chat_id=? AND user_id=?
        """, (
            now.isoformat(),
            deadline.isoformat(),
            chat_id,
            user_id,
        ))
        conn.commit()


def mark_intro_posted(chat_id, user_id):
    now = iso_now()
    with community_db_connect() as conn:
        conn.execute("""
            UPDATE community_members
            SET intro_posted_at=COALESCE(intro_posted_at, ?),
                last_post_at=?,
                status='active'
            WHERE chat_id=? AND user_id=?
        """, (now, now, chat_id, user_id))
        conn.commit()


def mark_member_post(chat_id, user_id):
    row = community_member(chat_id, user_id)
    if not row or row["status"] != "active":
        return False
    with community_db_connect() as conn:
        conn.execute(
            "UPDATE community_members SET last_post_at=? WHERE chat_id=? AND user_id=?",
            (iso_now(), chat_id, user_id),
        )
        conn.commit()
    return True


async def restrict_member(bot, chat_id, user_id):
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
        )
        return True
    except TelegramError:
        logger.exception("Could not restrict member %s in %s", user_id, chat_id)
        return False


async def restore_member(bot, chat_id, user_id):
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
            ),
        )
        return True
    except TelegramError:
        logger.exception("Could not restore member %s in %s", user_id, chat_id)
        return False


async def send_human_challenge(chat_id, user_id, context):
    row = community_member(chat_id, user_id)
    if not row:
        return

    answer, options = random.choice(HUMAN_CHALLENGES)
    shuffled = list(options)
    random.shuffle(shuffled)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(option, callback_data=f"human_verify:{user_id}:{i}")]
        for i, option in enumerate(shuffled)
    ])

    text = (
        "🤖 <b>QUICK HUMAN CHECK</b>\n\n"
        "Before you join the conversation, prove you're human. 👀\n\n"
        f"<b>Which one is {answer.split(' ', 1)[1].lower()}?</b>\n\n"
        "Tap the correct answer below."
    )

    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        set_verification_challenge(
            chat_id,
            user_id,
            answer,
            shuffled,
            message.message_id,
        )
        logger.info("Human verification challenge sent to %s in %s", user_id, chat_id)
    except TelegramError:
        logger.exception("Could not send human verification to %s", user_id)


async def community_exit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Send Melanated AZ's exit message when a member leaves or is removed."""
    event = update.chat_member
    if not event:
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    left = (
        old_status in {"member", "administrator", "creator"}
        and new_status in {"left", "kicked"}
    )
    if not left:
        return

    user = event.old_chat_member.user
    chat = event.chat
    if not user or user.is_bot:
        return

    name = user.first_name or user.username or "Someone"

    # Mark the member as gone so the security monitor no longer processes them.
    try:
        with community_db_connect() as conn:
            conn.execute(
                "UPDATE community_members SET status='left' WHERE chat_id=? AND user_id=?",
                (chat.id, user.id),
            )
            conn.commit()
    except Exception:
        logger.exception("Could not mark departing member %s as left", user.id)

    try:
        exit_message = await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f"👋🏾 <b>{name} has left Melanated AZ.</b> 💜\n\n"
                "We wish you nothing but good vibes wherever you go. 🖤💜\n\n"
                "🔥 The door is always open if you ever decide to come back."
            ),
            parse_mode=ParseMode.HTML,
        )
        # Keep the group clean; remove the exit notice after 5 minutes.
        if context.job_queue:
            context.job_queue.run_once(
                delete_message_job,
                300,
                data=(chat.id, exit_message.message_id),
            )
    except TelegramError:
        logger.exception("Could not send community exit message for %s", user.id)


async def community_welcome(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Two-step join protection: human check, then 48-hour introduction."""
    event = update.chat_member
    if not event:
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    joined = (
        new_status in {"member", "administrator"}
        and old_status in {"left", "kicked"}
    )
    if not joined:
        return

    user = event.new_chat_member.user
    chat = event.chat
    if not user or user.is_bot:
        return

    # Never challenge configured admins.
    if is_admin(user.id):
        return

    save_joining_member(chat.id, user)
    await restrict_member(context.bot, chat.id, user.id)

    name = user.first_name or "there"
    try:
        welcome = await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f"👋🏾 <b>WELCOME TO MELANATED AZ, {name}!</b> 💜🔥\n\n"
                "🛡️ <b>FIRST THINGS FIRST...</b>\n\n"
                "You need to complete a quick human verification before you can post.\n\n"
                "Once you're verified, you'll have <b>48 HOURS</b> to introduce yourself to the community.\n\n"
                "Good energy. Real people. Real connections. 🖤💜"
            ),
            parse_mode=ParseMode.HTML,
        )
        context.job_queue.run_once(
            delete_message_job,
            VERIFICATION_MESSAGE_TTL_MINUTES * 60,
            data=(chat.id, welcome.message_id),
        )
    except TelegramError:
        logger.exception("Could not send community welcome for %s", user.id)

    await send_human_challenge(chat.id, user.id, context)


async def human_verification_callback(update, context):
    query = update.callback_query
    if not query or not query.data:
        return

    try:
        await query.answer()
    except Exception:
        pass

    parts = query.data.split(":")
    if len(parts) != 3:
        return

    try:
        target_user_id = int(parts[1])
        selected_index = int(parts[2])
    except ValueError:
        return

    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or user.id != target_user_id:
        try:
            await query.answer("This verification belongs to another member.", show_alert=True)
        except Exception:
            pass
        return

    row = community_member(chat.id, user.id)
    if not row or row["status"] != "pending_verification":
        try:
            await query.answer("You're already verified.", show_alert=True)
        except Exception:
            pass
        return

    expires = parse_iso(row["verification_expires_at"])
    challenge = row["verification_challenge"] or ""
    if not expires or expires < utc_now() or "###" not in challenge:
        await send_human_challenge(chat.id, user.id, context)
        try:
            await query.answer("That challenge expired. Here's a new one.", show_alert=True)
        except Exception:
            pass
        return

    answer, options_blob = challenge.split("###", 1)
    options = options_blob.split("|||")
    if selected_index < 0 or selected_index >= len(options):
        return

    if options[selected_index] != answer:
        attempts = increment_verification_attempt(chat.id, user.id)
        if attempts >= VERIFICATION_MAX_ATTEMPTS:
            try:
                await query.answer("Verification failed. You have been removed.", show_alert=True)
            except Exception:
                pass
            await remove_unverified_member(context.bot, chat.id, user.id)
            return

        try:
            await query.answer(
                f"❌ Not quite. Attempt {attempts}/{VERIFICATION_MAX_ATTEMPTS}.",
                show_alert=True,
            )
        except Exception:
            pass
        await send_human_challenge(chat.id, user.id, context)
        return

    mark_verified(chat.id, user.id)
    await restore_member(context.bot, chat.id, user.id)

    try:
        await query.edit_message_text(
            "✅ <b>HUMAN VERIFICATION PASSED!</b> 🎉\n\n"
            "You're cleared to participate.\n\n"
            "👋 <b>NOW INTRODUCE YOURSELF.</b>\n"
            "You have <b>48 HOURS</b> to make your introduction post.\n\n"
            "Tell us where you're from, what part of AZ you're in, what brought you here, "
            "what you're into, or whatever you're comfortable sharing. 💜",
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        pass


async def verification_message_guard(update, context):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat or user.is_bot:
        return

    # Only act on the configured main group when one is supplied.
    main_group_id = int(os.environ.get("MAIN_GROUP_ID", "0") or "0")
    if main_group_id and chat.id != main_group_id:
        return

    if is_admin(user.id):
        return

    row = community_member(chat.id, user.id)
    if not row:
        return

    status = row["status"]
    if status == "pending_verification":
        try:
            await message.delete()
        except TelegramError:
            pass
        return

    if status == "verified_intro_pending":
        # First normal message after verification counts as the introduction.
        if message.text and not message.text.startswith("/"):
            mark_intro_posted(chat.id, user.id)
            try:
                confirmation = await message.reply_text(
                    "🎉 <b>INTRO RECEIVED!</b> Welcome to Melanated AZ! 💜🔥",
                    parse_mode=ParseMode.HTML,
                )
                context.job_queue.run_once(
                    delete_message_job,
                    300,
                    data=(chat.id, confirmation.message_id),
                )
            except TelegramError:
                pass
        return

    if status == "active":
        mark_member_post(chat.id, user.id)


async def remove_unverified_member(bot, chat_id, user_id):
    try:
        await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        try:
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
        except TypeError:
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
    except TelegramError:
        logger.exception("Could not remove unverified member %s from %s", user_id, chat_id)

    with community_db_connect() as conn:
        conn.execute(
            "UPDATE community_members SET status='removed' WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        conn.commit()


async def delete_message_job(context):
    data = context.job.data if context.job else None
    if not data:
        return
    chat_id, message_id = data
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass


async def community_security_monitor(context):
    now = utc_now()
    with community_db_connect() as conn:
        rows = conn.execute("""
            SELECT * FROM community_members
            WHERE status IN ('pending_verification', 'verified_intro_pending')
        """).fetchall()

    for row in rows:
        deadline = parse_iso(row["intro_deadline"])
        joined = parse_iso(row["joined_at"])

        if row["status"] == "pending_verification":
            # Give a new join 48 hours to verify; challenge itself expires much sooner.
            if joined and joined + timedelta(hours=INTRO_HOURS) <= now:
                await remove_unverified_member(context.bot, row["chat_id"], row["user_id"])

        elif row["status"] == "verified_intro_pending":
            if deadline and deadline <= now:
                await remove_unverified_member(context.bot, row["chat_id"], row["user_id"])


def start_community_security_monitor(application):
    if not application.job_queue:
        logger.warning("Community security monitor unavailable: JobQueue not installed.")
        return
    application.job_queue.run_repeating(
        community_security_monitor,
        interval=6 * 60 * 60,
        first=60,
        name="community-security-monitor",
    )
    logger.info("Community security monitor started.")


# ==========================================================
# TEXT ROUTER
# ==========================================================

async def text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if await admin_birthday_text_handler(
        update,
        context,
    ):
        return

    if await birthday_text_handler(
        update,
        context,
    ):
        return


# ==========================================================
# /START
#
# IMPORTANT:
# Telegram deep-links also arrive through /start.
#
# Examples:
#
# /start rg_monopoly
# /start rg_join_AB12CD34
#
# We check Real Games FIRST.
# If it is not a Real Games payload,
# normal /start continues.
# ==========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    # ------------------------------------------------------
    # REAL GAMES DEEP-LINK
    # ------------------------------------------------------

    try:

        handled = await handle_real_game_deep_link(
            update,
            context,
        )

        if handled:

            logger.info(
                "Real Games deep-link handled for user %s",
                user.id,
            )

            return

    except Exception:

        logger.exception(
            "Real Games deep-link processing failed."
        )

        await message.reply_text(
            "⚠️ I couldn't open that game link. "
            "Please try again."
        )

        return

    # ------------------------------------------------------
    # NORMAL /START
    # ------------------------------------------------------

    text = (
        "👋 <b>Welcome to Melanated AZ Bot!</b>\n\n"
        "I'm the bot for the Melanated AZ community.\n\n"
        "🎂 Birthdays\n"
        "🎟️ Raffles\n"
        "🔥 Truth or Dare\n"
        "🎮 Game Center\n"
        "🎲 Real Games\n"
        "🛡️ Media protection\n\n"
        "Birthday: <code>/birthday</code>\n"
        "Truth or Dare: <code>/truthdare</code>\n"
        "Game Center: <code>/games</code>\n"
        "Real Games: <code>/realgames</code>"
    )

    if is_admin(user.id):

        text += (
            "\n\n👑 <b>Admin:</b>\n"
            "Use <code>/admin</code> to open "
            "the admin panel."
        )

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "🎮 REAL GAMES",
                callback_data="real_games_menu",
            )
        ]]
    )

    await message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# /STARTGAMES
#
# Opens the Real Games launcher with a large PLAY GAMES
# button.
# ==========================================================

async def startgames_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    games_url = (
        "https://melanatedaz.onrender.com/real-games/"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎮 PLAY GAMES",
                    url=games_url,
                )
            ]
        ]
    )

    text = (
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        "Ready to play?\n\n"
        "Choose from our playable games:\n\n"
        "🎮 <b>Arcade</b>\n"
        "🎲 <b>Board Games</b>\n"
        "🏀 <b>Sports</b>\n"
        "🔫 <b>Shooting</b>\n\n"
        "Tap the button below to enter the Game Center!"
    )

    await message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# /REALGAMES
# ==========================================================

async def real_games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    base_url = (
        context.application.bot_data.get(
            "public_base_url"
        )
        or os.environ.get(
            "PUBLIC_BASE_URL",
            "",
        )
    ).rstrip("/")

    if base_url:

        games_url = (
            f"{base_url}/real-games/"
        )

        monopoly_url = (
            f"{base_url}/real-games/monopoly/"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎮 REAL GAMES",
                        url=games_url,
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🎲 MONOPOLY",
                        url=monopoly_url,
                    )
                ],
            ]
        )

        text = (
            "🎮 <b>Melanated AZ Real Games</b>\n\n"
            "These are the interactive browser games.\n\n"
            "Choose a game below:"
        )

    else:

        keyboard = None

        text = (
            "🎮 <b>Melanated AZ Real Games</b>\n\n"
            "The game server URL has not been configured yet.\n\n"
            "Set the Render environment variable:\n\n"
            "<code>PUBLIC_BASE_URL</code>"
        )

    await message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# /ADMIN
# ==========================================================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    if not is_admin(user.id):

        await update.effective_message.reply_text(
            "⛔ You are not authorized to use "
            "the admin panel."
        )

        return

    await admin_menu(
        update,
        context,
    )


# ==========================================================
# ADMIN CALLBACK ROUTER
# ==========================================================

async def admin_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):

        await query.answer(
            "⛔ You are not authorized.",
            show_alert=True,
        )

        return

    try:

        await admin_button(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Admin callback failed."
        )

        try:

            await query.answer(
                "⚠️ Something went wrong.",
                show_alert=True,
            )

        except Exception:

            pass


# ==========================================================
# BIRTHDAY CALLBACK ROUTER
# ==========================================================

async def birthday_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        await birthday_callback(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Birthday callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.answer(
                    "⚠️ Something went wrong.",
                    show_alert=True,
                )

            except Exception:

                pass


# ==========================================================
# GAME CENTER CALLBACK ROUTER
# ==========================================================

async def game_center_callback_router_wrapper(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        await game_center_callback_router(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Game Center callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.answer(
                    "⚠️ Game Center action failed.",
                    show_alert=True,
                )

            except Exception:

                pass


# ==========================================================
# REAL GAMES CALLBACK ROUTER
#
# This is intentionally separate from games/.
# ==========================================================

async def real_games_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    try:

        await query.answer()

    except Exception:

        pass

    base_url = (
        context.application.bot_data.get(
            "public_base_url"
        )
        or os.environ.get(
            "PUBLIC_BASE_URL",
            "",
        )
    ).rstrip("/")

    if not base_url:

        await query.message.reply_text(
            "⚠️ Real Games are not configured yet.\n\n"
            "The Render PUBLIC_BASE_URL environment "
            "variable needs to be set."
        )

        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎲 MONOPOLY",
                    url=(
                        f"{base_url}"
                        "/real-games/monopoly/"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 ALL REAL GAMES",
                    url=(
                        f"{base_url}"
                        "/real-games/"
                    ),
                )
            ],
        ]
    )

    await query.message.reply_text(
        "🎮 <b>REAL GAMES</b>\n\n"
        "Choose a game:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# TRUTH OR DARE CALLBACK ROUTER
# ==========================================================

async def truth_dare_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        await truth_dare_callback(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Truth or Dare callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.answer(
                    "⚠️ Something went wrong.",
                    show_alert=True,
                )

            except Exception:

                pass


# ==========================================================
# RAFFLE CALLBACK ROUTER
# ==========================================================

async def raffle_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    logger.info(
        "=========================================================="
    )

    logger.info(
        "RAFFLE CALLBACK HANDLER TRIGGERED"
    )

    logger.info(
        "Callback query exists: %s",
        bool(query),
    )

    if query:

        logger.info(
            "Callback data: %s",
            query.data,
        )

        logger.info(
            "Callback user: %s",
            getattr(
                update.effective_user,
                "id",
                None,
            ),
        )

        logger.info(
            "Callback username: %s",
            getattr(
                update.effective_user,
                "username",
                None,
            ),
        )

        callback_message = getattr(
            query,
            "message",
            None,
        )

        logger.info(
            "Callback chat ID: %s",
            getattr(
                callback_message,
                "chat_id",
                None,
            ),
        )

        logger.info(
            "Callback message ID: %s",
            getattr(
                callback_message,
                "message_id",
                None,
            ),
        )

    else:

        logger.warning(
            "RAFFLE CALLBACK HANDLER RECEIVED "
            "WITHOUT callback_query!"
        )

    logger.info(
        "Calling raffle.raffle_callback()..."
    )

    try:

        await raffle_callback(
            update,
            context,
        )

        logger.info(
            "raffle.raffle_callback() completed successfully."
        )

    except Exception:

        logger.exception(
            "Raffle callback failed."
        )

        if query:

            try:

                await query.answer(
                    "⚠️ Raffle action failed.",
                    show_alert=True,
                )

            except Exception:

                logger.exception(
                    "Could not answer failed "
                    "raffle callback."
                )

    logger.info(
        "=========================================================="
    )


# ==========================================================
# DATABASE STARTUP CHECK
# ==========================================================

def database_startup_check():

    try:

        stats = get_database_stats()

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Melanated AZ Bot - Persistent Database"
        )

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Database path       : %s",
            stats.get("database"),
        )

        logger.info(
            "Database directory  : %s",
            stats.get("database_directory"),
        )

        logger.info(
            "Database exists     : %s",
            stats.get("exists"),
        )

        logger.info(
            "Database size       : %s",
            stats.get("size"),
        )

        logger.info(
            "Persistent directory: %s",
            stats.get("persistent"),
        )

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Melanated AZ Bot - Database Statistics"
        )

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Database       : %s",
            stats.get("database"),
        )

        logger.info(
            "Raffles        : %s",
            stats.get("raffles"),
        )

        logger.info(
            "Raffle Entries : %s",
            stats.get("raffle_entries"),
        )

        logger.info(
            "Birthdays      : %s",
            stats.get("birthdays"),
        )

        logger.info(
            "Known Members  : %s",
            stats.get("members"),
        )

        logger.info(
            "Integrity      : %s",
            "OK"
            if check_database_integrity()
            else "FAILED",
        )

        logger.info(
            "=========================================================="
        )

    except Exception:

        logger.exception(
            "Database startup check failed."
        )


# ==========================================================
# GAME DATABASE
# ==========================================================

def game_database_startup_check():

    try:

        initialize_game_database()

        logger.info(
            "Game Center database: READY"
        )

    except Exception:

        logger.exception(
            "Game Center database initialization failed."
        )


# ==========================================================
# REAL GAMES STARTUP CHECK
# ==========================================================

def real_games_startup_check():

    public_url = os.environ.get(
        "PUBLIC_BASE_URL",
        "",
    ).strip().rstrip("/")

    if public_url:

        logger.info(
            "=========================================================="
        )

        logger.info(
            "Real Games: READY"
        )

        logger.info(
            "Public URL: %s",
            public_url,
        )

        logger.info(
            "Real Games: %s/real-games/",
            public_url,
        )

        logger.info(
            "Monopoly: %s/real-games/monopoly/",
            public_url,
        )

        logger.info(
            "=========================================================="
        )

    else:

        logger.warning(
            "=========================================================="
        )

        logger.warning(
            "PUBLIC_BASE_URL is NOT configured."
        )

        logger.warning(
            "Real Games can still run locally, but "
            "Telegram game links will not have a "
            "public Render URL."
        )

        logger.warning(
            "Set PUBLIC_BASE_URL in Render."
        )

        logger.warning(
            "=========================================================="
        )


# ==========================================================
# POST INIT
# ==========================================================

async def post_init(
    application: Application,
):

    # ------------------------------------------------------
    # BOT INFORMATION
    # ------------------------------------------------------

    try:

        me = await application.bot.get_me()

        application.bot_data[
            "bot_username"
        ] = me.username

        logger.info(
            "Bot username: @%s",
            me.username,
        )

    except Exception:

        logger.exception(
            "Could not retrieve bot information."
        )

    # ------------------------------------------------------
    # PUBLIC URL
    # ------------------------------------------------------

    public_url = os.environ.get(
        "PUBLIC_BASE_URL",
        "",
    ).strip().rstrip("/")

    if public_url:

        application.bot_data[
            "public_base_url"
        ] = public_url

        logger.info(
            "Public Base URL loaded: %s",
            public_url,
        )

    else:

        application.bot_data[
            "public_base_url"
        ] = ""

        logger.warning(
            "PUBLIC_BASE_URL is not configured."
        )


# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    error = context.error

    if isinstance(
        error,
        BadRequest,
    ):

        logger.warning(
            "Telegram BadRequest: %s",
            error,
        )

        return

    logger.exception(
        "Unhandled bot exception:",
        exc_info=error,
    )


# ==========================================================
# BUILD APPLICATION
# ==========================================================

def build_application():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN is not configured."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ======================================================
    # COMMANDS
    # ======================================================

    for command, callback in [

        (
            "start",
            start_command,
        ),

        (
            "startgames",
            startgames_command,
        ),

        (
            "realgames",
            real_games_command,
        ),

        (
            "admin",
            admin_command,
        ),

        (
            "startraffle",
            start_raffle,
        ),

        (
            "rafflestatus",
            raffle_status,
        ),

        (
            "entries",
            raffle_entries,
        ),

        (
            "pending",
            pending_entries,
        ),

        (
            "paid",
            paid_entry,
        ),

        (
            "cancelraffle",
            cancel_raffle,
        ),

        (
            "draw",
            draw_raffle,
        ),

        (
            "games",
            games_command,
        ),

        (
            "birthday",
            birthday,
        ),

        (
            "mybirthday",
            my_birthday,
        ),

        (
            "removebirthday",
            remove_my_birthday,
        ),

        (
            "truthdare",
            truth_dare_menu,
        ),

        (
            "truth",
            truth,
        ),

        (
            "dare",
            dare,
        ),

    ]:

        application.add_handler(
            CommandHandler(
                command,
                callback,
            )
        )

    # ======================================================
    # RAFFLE CALLBACKS
    #
    # raffle.py remains the ONLY owner of raffle
    # callback processing.
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_callback_router,
            pattern=(
                r"^(raffle_|"
                r"approve_|"
                r"deny_|"
                r"enter_|"
                r"pay_|"
                r"payment_|"
                r"paid_|"
                r"draw_|"
                r"reroll_|"
                r"bonus_|"
                r"remove_)"
            ),
        )
    )

    # ======================================================
    # ADMIN CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_callback_router,
            pattern=r"^admin_",
        )
    )

    # ======================================================
    # BIRTHDAY CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            birthday_callback_router,
            pattern=r"^birthday_",
        )
    )

    # ======================================================
    # EXISTING GAME CENTER CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            game_center_callback_router_wrapper,
            pattern=r"^games_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            game_center_callback_router_wrapper,
            pattern=r"^game_",
        )
    )

    # ======================================================
    # NEW REAL GAMES CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            real_games_callback_router,
            pattern=r"^real_games_",
        )
    )

    # ======================================================
    # TRUTH OR DARE CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            truth_dare_callback_router,
            pattern=r"^truthdare_",
        )
    )

    # ======================================================
    # HUMAN VERIFICATION CALLBACKS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            human_verification_callback,
            pattern=r"^human_verify:",
        )
    )

    # ======================================================
    # COMMUNITY MESSAGE GUARD
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.ALL,
            verification_message_guard,
        ),
        group=1,
    )

    # ======================================================
    # COMMUNITY EXIT
    # ======================================================

    application.add_handler(
        ChatMemberHandler(
            community_exit,
            ChatMemberHandler.CHAT_MEMBER,
        ),
        group=1,
    )

    # ======================================================
    # COMMUNITY WELCOME
    # ======================================================

    application.add_handler(
        ChatMemberHandler(
            community_welcome,
            ChatMemberHandler.CHAT_MEMBER,
        ),
        group=1,
    )

    # ======================================================
    # MEDIA
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo,
        ),
        group=5,
    )

    application.add_handler(
        MessageHandler(
            filters.VIDEO,
            handle_video,
        ),
        group=5,
    )

    application.add_handler(
        MessageHandler(
            filters.ANIMATION,
            handle_animation,
        ),
        group=5,
    )

    application.add_handler(
        MessageHandler(
            filters.Document.IMAGE,
            handle_image_document,
        ),
        group=5,
    )

    # ======================================================
    # TEXT
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_router,
        ),
        group=10,
    )

    # ======================================================
    # ERROR HANDLER
    # ======================================================

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "All Telegram handlers registered."
    )

    logger.info(
        "Raffle callback handler registered."
    )

    logger.info(
        "Existing Game Center callbacks registered."
    )

    logger.info(
        "Real Games callback handler registered."
    )

    logger.info(
        "Real Games deep-link handler registered."
    )

    return application


# ==========================================================
# MAIN
# ==========================================================

def main():

    logger.info(
        "=========================================================="
    )

    logger.info(
        "Starting Melanated AZ Bot"
    )

    logger.info(
        "=========================================================="
    )

    logger.info(
        "Loaded Admin IDs: %s",
        list(ADMIN_IDS),
    )

    logger.info(
        "Raffle Chat ID: %s",
        RAFFLE_CHAT_ID,
    )

    # ------------------------------------------------------
    # DATABASE
    # ------------------------------------------------------

    database_startup_check()

    # ------------------------------------------------------
    # EXISTING GAME CENTER DATABASE
    # ------------------------------------------------------

    game_database_startup_check()

    # ------------------------------------------------------
    # NEW REAL GAMES
    # ------------------------------------------------------

    real_games_startup_check()

    # ------------------------------------------------------
    # START FLASK
    # ------------------------------------------------------

    threading.Thread(
        target=run_flask,
        daemon=True,
        name="flask-health-server",
    ).start()

    logger.info(
        "Flask health server started."
    )

    # ------------------------------------------------------
    # COMMUNITY SECURITY DATABASE
    # ------------------------------------------------------

    initialize_community_security_database()

    # ------------------------------------------------------
    # BUILD TELEGRAM APPLICATION
    # ------------------------------------------------------

    application = build_application()

    start_community_security_monitor(application)

    logger.info(
        "Telegram application created."
    )

    # ------------------------------------------------------
    # START POLLING
    # ------------------------------------------------------

    logger.info(
        "Starting Telegram polling..."
    )

    # Telegram does not include chat_member updates unless they are explicitly
    # requested in allowed_updates. Keep every normal update type enabled while
    # guaranteeing chat_member is present for joins, leaves, verification, and
    # the community exit message.
    allowed_updates = list(Update.ALL_TYPES)
    if "chat_member" not in allowed_updates:
        allowed_updates.append("chat_member")

    logger.info(
        "Telegram allowed updates configured; chat_member=%s",
        "chat_member" in allowed_updates,
    )

    application.run_polling(
        allowed_updates=allowed_updates,
        drop_pending_updates=False,
        close_loop=False,
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    main()


# ==========================================================
# END bot.py
# ==========================================================
