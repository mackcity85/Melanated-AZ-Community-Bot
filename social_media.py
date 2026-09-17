# ==========================================================
# Melanated AZ Bot - Social Media / Friends Directory
# Topic: -1002697105809_9513
# ==========================================================

import html
import os
import re
import sqlite3
from urllib.parse import urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram.error import TelegramError

CHAT_ID = -1002697105809
TOPIC_ID = 9513
DB_PATH = os.environ.get("SOCIAL_MEDIA_DB", "/var/data/social_media.db").strip()
PANEL_STATE = os.path.join("/var/data" if os.path.isdir("/var/data") else ".", "social_media_panel_9513.txt")

PLATFORMS = {
    "instagram": ("📸 Instagram", "instagram.com"),
    "facebook": ("📘 Facebook", "facebook.com"),
    "tiktok": ("🎵 TikTok", "tiktok.com"),
    "youtube": ("▶️ YouTube", "youtube.com"),
    "snapchat": ("👻 Snapchat", "snapchat.com"),
    "x": ("𝕏 X", "x.com"),
    "threads": ("🧵 Threads", "threads.net"),
    "reddit": ("👽 Reddit", "reddit.com"),
    "linkedin": ("💼 LinkedIn", "linkedin.com"),
    "pinterest": ("📌 Pinterest", "pinterest.com"),
    "whatsapp": ("💬 WhatsApp", "wa.me"),
    "telegram": ("✈️ Telegram", "t.me"),
}

PLATFORM_ALIASES = {
    "instagram": "https://instagram.com/",
    "facebook": "https://facebook.com/",
    "tiktok": "https://tiktok.com/@",
    "youtube": "https://youtube.com/@",
    "snapchat": "https://snapchat.com/add/",
    "x": "https://x.com/",
    "threads": "https://threads.net/@",
    "reddit": "https://reddit.com/u/",
    "linkedin": "https://linkedin.com/in/",
    "pinterest": "https://pinterest.com/",
    "whatsapp": "https://wa.me/",
    "telegram": "https://t.me/",
}

ADD_PLATFORM, ENTER_LINK = range(2)


def _connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_social_media_database():
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS social_links (
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                url TEXT NOT NULL,
                display_name TEXT,
                username TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, platform)
            )"""
        )
        conn.commit()


def _normalize(platform, raw):
    value = (raw or "").strip()
    if not value:
        return None
    if not re.match(r"^https?://", value, re.I):
        value = PLATFORM_ALIASES[platform] + value.lstrip("@/")
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return None
    host = parsed.netloc.lower().split(":", 1)[0]
    expected = PLATFORMS[platform][1]
    if not (host == expected or host.endswith("." + expected)):
        return None
    if len(value) > 500:
        return None
    return value


def _save_link(user_id, platform, url, display_name, username):
    with _connect() as conn:
        conn.execute(
            """INSERT INTO social_links(user_id,platform,url,display_name,username,updated_at)
               VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(user_id,platform) DO UPDATE SET
                 url=excluded.url,
                 display_name=excluded.display_name,
                 username=excluded.username,
                 updated_at=CURRENT_TIMESTAMP""",
            (user_id, platform, url, display_name, username),
        )
        conn.commit()


def _get_user_links(user_id):
    with _connect() as conn:
        return conn.execute(
            "SELECT platform,url,display_name,username FROM social_links WHERE user_id=? ORDER BY platform",
            (user_id,),
        ).fetchall()


def _get_members():
    with _connect() as conn:
        return conn.execute(
            "SELECT DISTINCT user_id, display_name FROM social_links ORDER BY COALESCE(display_name,''), user_id"
        ).fetchall()


def _platform_keyboard():
    keys = list(PLATFORMS)
    rows = []
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i + 2]:
            row.append(InlineKeyboardButton(PLATFORMS[key][0], callback_data=f"social_platform:{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Cancel", callback_data="social_cancel")])
    return InlineKeyboardMarkup(rows)


def _my_links_keyboard(rows):
    buttons = []
    for row in rows:
        buttons.append([
            InlineKeyboardButton(
                f"{PLATFORMS[row['platform']][0]} 🔗",
                url=row["url"],
            ),
            InlineKeyboardButton(
                "✏️ Edit",
                callback_data=f"social_platform:{row['platform']}",
            ),
            InlineKeyboardButton(
                "🗑",
                callback_data=f"social_delete:{row['platform']}",
            ),
        ])
    buttons.append([InlineKeyboardButton("➕ Add Another", callback_data="social_add")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="social_close")])
    return InlineKeyboardMarkup(buttons)


def _topic_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add My Social Links", callback_data="social_add")],
        [InlineKeyboardButton("👥 Browse Friends", callback_data="social_browse")],
        [InlineKeyboardButton("🔗 My Links", callback_data="social_mine")],
    ])


async def send_social_panel(bot):
    initialize_social_media_database()
    text = (
        "📱 <b>MELANATED AZ — CONNECT &amp; ADD FRIENDS</b>\n\n"
        "Want people in the community to find you on social media?\n\n"
        "Add your social links, then browse other members who have shared theirs. "
        "Only links you choose to add are displayed.\n\n"
        "👇🏾 Choose an option below."
    )
    try:
        message_id = None
        if os.path.exists(PANEL_STATE):
            try:
                message_id = int(open(PANEL_STATE, "r", encoding="utf-8").read().strip())
            except Exception:
                message_id = None
        if message_id:
            try:
                await bot.edit_message_text(
                    chat_id=CHAT_ID,
                    message_id=message_id,
                    text=text,
                    reply_markup=_topic_panel_keyboard(),
                    parse_mode="HTML",
                )
                return message_id
            except TelegramError:
                pass

        message = await bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=TOPIC_ID,
            text=text,
            reply_markup=_topic_panel_keyboard(),
            parse_mode="HTML",
        )
        with open(PANEL_STATE, "w", encoding="utf-8") as fh:
            fh.write(str(message.message_id))
        try:
            await bot.pin_chat_message(CHAT_ID, message.message_id, disable_notification=True)
        except TelegramError:
            pass
        return message.message_id
    except TelegramError:
        return None


async def socials_command(update, context):
    if not update.effective_user or update.effective_chat.type != "private":
        return
    initialize_social_media_database()
    await update.effective_message.reply_text(
        "📱 <b>Your Melanated AZ Social Links</b>\n\nChoose a platform to add or update.",
        reply_markup=_platform_keyboard(),
        parse_mode="HTML",
    )


async def social_add_callback(update, context):
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()
    user = update.effective_user
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text="📱 <b>Add Your Social Links</b>\n\nChoose a platform. I'll ask you for the profile link in a private chat.",
            reply_markup=_platform_keyboard(),
            parse_mode="HTML",
        )
        if update.effective_chat and update.effective_chat.id == CHAT_ID:
            await query.answer("Check your private chat with the bot.", show_alert=True)
    except TelegramError:
        username = (await context.bot.get_me()).username
        await query.answer("Open the bot in private first, then tap Add My Social Links again.", show_alert=True)
        try:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                message_thread_id=TOPIC_ID,
                text="👋🏾 Tap the button below to open Melanated AZ Bot, then come back and tap <b>➕ Add My Social Links</b> again.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🤖 Open Melanated AZ Bot", url=f"https://t.me/{username}")]]),
                parse_mode="HTML",
            )
        except TelegramError:
            pass
        return ConversationHandler.END
    return ADD_PLATFORM


async def social_platform_callback(update, context):
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    platform = query.data.split(":", 1)[1]
    if platform not in PLATFORMS:
        await query.answer("Invalid platform.", show_alert=True)
        return ADD_PLATFORM
    context.user_data["social_platform"] = platform
    await query.answer()
    label = PLATFORMS[platform][0]
    await query.edit_message_text(
        f"{label}\n\nSend your <b>profile link</b> in this private chat.\n\nExample:\n<code>{PLATFORM_ALIASES[platform]}yourname</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Cancel", callback_data="social_cancel")]]),
    )
    return ENTER_LINK


async def social_link_message(update, context):
    if not update.effective_message or update.effective_chat.type != "private":
        return ENTER_LINK
    platform = context.user_data.get("social_platform")
    if platform not in PLATFORMS:
        return ConversationHandler.END
    raw = update.effective_message.text or ""
    url = _normalize(platform, raw)
    if not url:
        await update.effective_message.reply_text(
            f"❌ That doesn't look like a valid {PLATFORMS[platform][0]} link.\n\n"
            f"Send the full profile URL, such as:\n{PLATFORM_ALIASES[platform]}yourname"
        )
        return ENTER_LINK
    user = update.effective_user
    display_name = user.full_name or user.first_name or f"User {user.id}"
    username = user.username or ""
    _save_link(user.id, platform, url, display_name, username)
    context.user_data.pop("social_platform", None)
    rows = _get_user_links(user.id)
    await update.effective_message.reply_text(
        f"✅ <b>{PLATFORMS[platform][0]} saved.</b>\n\n"
        "Your link is now available in the Melanated AZ friends directory.",
        parse_mode="HTML",
        reply_markup=_my_links_keyboard(rows),
    )
    return ADD_PLATFORM


async def social_delete_callback(update, context):
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    platform = query.data.split(":", 1)[1]
    with _connect() as conn:
        conn.execute("DELETE FROM social_links WHERE user_id=? AND platform=?", (update.effective_user.id, platform))
        conn.commit()
    await query.answer("Link removed.")
    rows = _get_user_links(update.effective_user.id)
    if rows:
        await query.edit_message_text("🔗 <b>Your saved social links</b>", parse_mode="HTML", reply_markup=_my_links_keyboard(rows))
    else:
        await query.edit_message_text("You don't have any social links saved yet.", reply_markup=_platform_keyboard())
    return ADD_PLATFORM


async def social_mine_callback(update, context):
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    rows = _get_user_links(update.effective_user.id)
    await query.answer()
    if rows:
        await query.edit_message_text("🔗 <b>Your saved social links</b>", parse_mode="HTML", reply_markup=_my_links_keyboard(rows))
    else:
        await query.edit_message_text("📱 You haven't added any social links yet.", reply_markup=_platform_keyboard())
    return ADD_PLATFORM


async def social_browse_callback(update, context):
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    members = _get_members()
    await query.answer()
    if not members:
        await query.edit_message_text(
            "👥 <b>FRIENDS DIRECTORY</b>\n\nNobody has added social links yet. Be the first!",
            parse_mode="HTML",
            reply_markup=_topic_panel_keyboard(),
        )
        return ConversationHandler.END
    buttons = []
    for row in members[:40]:
        name = row["display_name"] or f"Member {row['user_id']}"
        buttons.append([InlineKeyboardButton(f"👤 {name[:40]}", callback_data=f"social_member:{row['user_id']}")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="social_close")])
    await query.edit_message_text(
        "👥 <b>FRIENDS DIRECTORY</b>\n\nChoose a member to see the social links they've shared.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return ConversationHandler.END


async def social_member_callback(update, context):
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    try:
        user_id = int(query.data.split(":", 1)[1])
    except Exception:
        await query.answer("Invalid member.", show_alert=True)
        return ConversationHandler.END
    rows = _get_user_links(user_id)
    await query.answer()
    if not rows:
        await query.edit_message_text("No social links are currently shared by this member.", reply_markup=_topic_panel_keyboard())
        return ConversationHandler.END
    name = rows[0]["display_name"] or f"Member {user_id}"
    buttons = [[InlineKeyboardButton(PLATFORMS[r["platform"]][0], url=r["url"])] for r in rows]
    buttons.append([InlineKeyboardButton("⬅️ Friends Directory", callback_data="social_browse")])
    await query.edit_message_text(
        f"👤 <b>{html.escape(name)}</b>\n\nTap a platform to connect or add them.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return ConversationHandler.END


async def social_cancel(update, context):
    query = update.callback_query
    if query:
        await query.answer("Cancelled.")
        try:
            await query.edit_message_text("📱 Social links menu closed.")
        except TelegramError:
            pass
    context.user_data.pop("social_platform", None)
    return ConversationHandler.END


async def social_close(update, context):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "📱 <b>MELANATED AZ — CONNECT &amp; ADD FRIENDS</b>\n\nChoose an option below.",
            parse_mode="HTML",
            reply_markup=_topic_panel_keyboard(),
        )
    return ConversationHandler.END


async def social_start_deep_link(update, context):
    # Optional deep-link entry point for users who open the bot from the topic.
    await socials_command(update, context)


def build_social_conversation():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(social_add_callback, pattern=r"^social_add$")],
        states={
            ADD_PLATFORM: [CallbackQueryHandler(social_platform_callback, pattern=r"^social_platform:")],
            ENTER_LINK: [MessageHandler(filters.PRIVATE & filters.TEXT & ~filters.COMMAND, social_link_message)],
        },
        fallbacks=[
            CallbackQueryHandler(social_cancel, pattern=r"^social_cancel$"),
            CommandHandler("cancel", social_cancel),
        ],
        per_user=True,
        per_chat=False,
        allow_reentry=True,
    )


def register_social_media_handlers(application):
    initialize_social_media_database()
    # Conversation handler first so the Add button and private link entry are isolated.
    application.add_handler(build_social_conversation(), group=-5)
    application.add_handler(CallbackQueryHandler(social_mine_callback, pattern=r"^social_mine$"), group=-4)
    application.add_handler(CallbackQueryHandler(social_browse_callback, pattern=r"^social_browse$"), group=-4)
    application.add_handler(CallbackQueryHandler(social_member_callback, pattern=r"^social_member:\d+$"), group=-4)
    application.add_handler(CallbackQueryHandler(social_delete_callback, pattern=r"^social_delete:"), group=-4)
    application.add_handler(CallbackQueryHandler(social_close, pattern=r"^social_close$"), group=-4)
    application.add_handler(CommandHandler("socials", socials_command, filters=filters.PRIVATE), group=-4)


async def startup_social_media(app):
    register_social_media_handlers(app)
    await send_social_panel(app.bot)
