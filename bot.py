# ==========================================================
# Melanated AZ Bot
# bot.py
# ==========================================================
# PATCH: Raffle topic repair / single-post behavior
# ==========================================================

import logging
import os
import html
import threading
import sqlite3
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.constants import ParseMode
from telegram.error import TelegramError, BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, ChatMemberHandler, filters

from config import BOT_TOKEN, ADMIN_IDS, RAFFLE_CHAT_ID
from admin import admin_menu, admin_button, admin_birthday_text_handler, is_admin
from birthday import birthday, my_birthday, remove_my_birthday, birthday_callback, birthday_text_handler
from raffle import (
    start_raffle,
    handle_raffle_setup,
    raffle_status,
    start_daily_raffle_status,
    start_raffle_cleanup_recovery,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
    raffle_callback,
    publish_raffle,
)
from raffle_database import get_database_stats, check_database_integrity, get_active_raffle, set_raffle_post
from truth_dare import truth, dare, truth_dare_menu, truth_dare_callback
from games.game_center import games_command, game_center_callback_router, initialize_game_database, ensure_pinned_game_center
from games_reminder import start_weekly_game_center_reminder
from real_games import real_games_bp, handle_real_game_deep_link
from real_games.monopoly import monopoly_bp

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
logger = logging.getLogger("melanated_az_bot")

app = Flask(__name__)
app.register_blueprint(real_games_bp)
app.register_blueprint(monopoly_bp)

@app.route("/")
def health_check():
    return "Melanated AZ Bot is running.", 200

@app.route("/health")
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

async def delete_message_later(context):
    job = context.job
    if not job:
        return
    data = job.data or {}
    if data.get("chat_id") is None or data.get("message_id") is None:
        return
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except TelegramError:
        pass

async def delete_after(context, message, seconds=30):
    if message and context.job_queue:
        context.job_queue.run_once(delete_message_later, when=seconds, data={"chat_id": message.chat_id, "message_id": message.message_id})

async def get_bot_username(context):
    username = context.application.bot_data.get("bot_username")
    if username:
        return username
    try:
        me = await context.bot.get_me()
        username = me.username
        if username:
            context.application.bot_data["bot_username"] = username
        return username
    except Exception:
        logger.exception("Could not retrieve bot username.")
        return None

MEDIA_WARNING_SECONDS = 30

async def send_media_warning(update, context):
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return
    username = await get_bot_username(context)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🤖 Post with Melanated AZ Bot", url=f"https://t.me/{username}")]]) if username else None
    text = "⚠️ <b>Media Spoiler Required</b>\n\n" + f"{user.mention_html()}, your photo/video was removed because it was not marked as a spoiler.\n\nPlease resend the media using Telegram's 🚫 <b>Spoiler</b> option."
    try:
        warning = await context.bot.send_message(chat_id=message.chat_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await delete_after(context, warning, MEDIA_WARNING_SECONDS)
    except TelegramError:
        logger.exception("Could not send media warning.")

async def send_private_media_warning(update, context):
    user = update.effective_user
    if not user:
        return
    username = await get_bot_username(context)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🤖 Open Melanated AZ Bot", url=f"https://t.me/{username}")]]) if username else None
    text = "👋 Hey! This is the Melanated AZ Bot from the Melanated AZ group.\n\nYour photo/video was removed because Telegram's Spoiler option was not enabled.\n\n📸 <b>How to post it correctly:</b>\n\n1️⃣ Select your photo or video.\n2️⃣ Tap the ⋮ menu/options.\n3️⃣ Select <b>Hide with Spoiler</b>.\n4️⃣ Send the media."
    try:
        await context.bot.send_message(chat_id=user.id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except TelegramError:
        logger.info("Could not send private media warning to %s.", user.id)

async def handle_photo(update, context):
    message = update.effective_message
    if not message or message.has_media_spoiler:
        return
    try:
        await message.delete()
    except TelegramError:
        pass
    await send_media_warning(update, context)
    await send_private_media_warning(update, context)

async def handle_video(update, context):
    message = update.effective_message
    if not message or message.has_media_spoiler:
        return
    try:
        await message.delete()
    except TelegramError:
        pass
    await send_media_warning(update, context)
    await send_private_media_warning(update, context)

async def handle_animation(update, context):
    return

async def handle_image_document(update, context):
    return

# ==========================================================
# COMMUNITY HUMAN VERIFICATION + INTRO SYSTEM
# ==========================================================
COMMUNITY_DB = "/var/data/community_security.db" if os.path.isdir("/var/data") else "./community_security.db"
INTRO_HOURS = 48
INTRO_TOPIC_ID = int(os.environ.get("INTRO_TOPIC_ID", "11570") or "11570")
INTRO_MAX_CHARS = 3500
VERIFICATION_MAX_ATTEMPTS = 3
VERIFICATION_MESSAGE_TTL_MINUTES = 5
MEMBER_INACTIVITY_DAYS = int(os.environ.get("MEMBER_INACTIVITY_DAYS", "30") or "30")
ADMIN_INACTIVITY_DAYS = int(os.environ.get("ADMIN_INACTIVITY_DAYS", "14") or "14")
ADMIN_GROUP_ID_ENV = os.environ.get("ADMIN_GROUP_ID", "") or ""
INACTIVITY_CHECK_HOURS = int(os.environ.get("INACTIVITY_CHECK_HOURS", "6") or "6")
INTRO_VIDEO_PATH = os.environ.get("INTRO_VIDEO_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "melanated_az_intro.mp4")).strip()
INTRO_VIDEO_FILE_ID = os.environ.get("INTRO_VIDEO_FILE_ID", "").strip()
INTRO_VIDEO_DELETE_SECONDS = int(os.environ.get("INTRO_VIDEO_DELETE_SECONDS", "300") or "300")
HUMAN_CHALLENGES = [("🍎 Apple", ["🍎 Apple", "🚗 Car", "👟 Shoe"]),("🐶 Dog", ["🌳 Tree", "🐶 Dog", "🚲 Bike"]),("🌙 Moon", ["🍕 Pizza", "🌙 Moon", "🎸 Guitar"]),("🚗 Car", ["🚗 Car", "🍌 Banana", "🎧 Headphones"]),("🐟 Fish", ["📱 Phone", "🐟 Fish", "👕 Shirt"]),("☀️ Sun", ["☀️ Sun", "🍔 Burger", "⚽ Ball"]),("🍕 Pizza", ["🪑 Chair", "🍕 Pizza", "🌴 Palm Tree"]),("🎸 Guitar", ["🎸 Guitar", "🥤 Drink", "🧢 Hat"])]

def community_db_connect():
    conn = sqlite3.connect(COMMUNITY_DB); conn.row_factory = sqlite3.Row; return conn

def initialize_community_security_database():
    os.makedirs(os.path.dirname(COMMUNITY_DB) or ".", exist_ok=True)
    with community_db_connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS community_members (chat_id INTEGER NOT NULL,user_id INTEGER NOT NULL,username TEXT,first_name TEXT,joined_at TEXT,verified_at TEXT,intro_deadline TEXT,intro_posted_at TEXT,intro_text TEXT,intro_message_id INTEGER,last_post_at TEXT,verification_attempts INTEGER DEFAULT 0,verification_message_id INTEGER,verification_challenge TEXT,verification_expires_at TEXT,inactivity_notice_at TEXT,inactivity_notice_message_id INTEGER,status TEXT DEFAULT 'pending_verification',PRIMARY KEY (chat_id,user_id))""")
        columns={row[1] for row in conn.execute("PRAGMA table_info(community_members)").fetchall()}
        for col, definition in [("intro_text","TEXT"),("intro_message_id","INTEGER"),("inactivity_notice_at","TEXT"),("inactivity_notice_message_id","INTEGER"),("monthly_intro_reminder_at","TEXT")]:
            if col not in columns: conn.execute(f"ALTER TABLE community_members ADD COLUMN {col} {definition}")
        conn.commit()

def utc_now(): return datetime.now(timezone.utc)
def iso_now(): return utc_now().isoformat()
def parse_iso(value):
    if not value: return None
    try: return datetime.fromisoformat(value)
    except Exception: return None

def community_member(chat_id,user_id):
    with community_db_connect() as conn: return conn.execute("SELECT * FROM community_members WHERE chat_id=? AND user_id=?",(chat_id,user_id)).fetchone()

def save_joining_member(chat_id,user):
    with community_db_connect() as conn:
        conn.execute("""INSERT INTO community_members (chat_id,user_id,username,first_name,joined_at,status) VALUES (?,?,?,?,?,'pending_verification') ON CONFLICT(chat_id,user_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name,joined_at=excluded.joined_at,verified_at=NULL,intro_deadline=NULL,intro_posted_at=NULL,intro_text=NULL,intro_message_id=NULL,last_post_at=NULL,verification_attempts=0,verification_message_id=NULL,verification_challenge=NULL,verification_expires_at=NULL,inactivity_notice_at=NULL,inactivity_notice_message_id=NULL,status='pending_verification'""",(chat_id,user.id,user.username,user.first_name,iso_now())); conn.commit()

def set_verification_challenge(chat_id,user_id,answer,options,message_id):
    expires=utc_now()+timedelta(minutes=VERIFICATION_MESSAGE_TTL_MINUTES)
    with community_db_connect() as conn: conn.execute("UPDATE community_members SET verification_challenge=?,verification_expires_at=?,verification_message_id=? WHERE chat_id=? AND user_id=?",(answer+"###"+"|||".join(options),expires.isoformat(),message_id,chat_id,user_id)); conn.commit()

def increment_verification_attempt(chat_id,user_id):
    with community_db_connect() as conn:
        conn.execute("UPDATE community_members SET verification_attempts=verification_attempts+1 WHERE chat_id=? AND user_id=?",(chat_id,user_id)); conn.commit(); row=conn.execute("SELECT verification_attempts FROM community_members WHERE chat_id=? AND user_id=?",(chat_id,user_id)).fetchone(); return int(row[0]) if row else VERIFICATION_MAX_ATTEMPTS

def mark_verified(chat_id,user_id):
    now=utc_now(); deadline=now+timedelta(hours=INTRO_HOURS)
    with community_db_connect() as conn: conn.execute("UPDATE community_members SET verified_at=?,intro_deadline=?,status='verified_intro_pending',verification_challenge=NULL,verification_expires_at=NULL WHERE chat_id=? AND user_id=?",(now.isoformat(),deadline.isoformat(),chat_id,user_id)); conn.commit()

def save_intro(chat_id,user_id,intro_text,intro_message_id=None):
    now=iso_now()
    with community_db_connect() as conn: conn.execute("UPDATE community_members SET intro_posted_at=COALESCE(intro_posted_at,?),intro_text=?,intro_message_id=?,last_post_at=?,status='active' WHERE chat_id=? AND user_id=?",(now,intro_text,intro_message_id,now,chat_id,user_id)); conn.commit()

def ensure_tracked_member(chat_id,user):
    if not user or user.is_bot:return
    now=iso_now()
    with community_db_connect() as conn: conn.execute("INSERT INTO community_members (chat_id,user_id,username,first_name,joined_at,verified_at,last_post_at,status) VALUES (?,?,?,?,?,?,?,'active') ON CONFLICT(chat_id,user_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name",(chat_id,user.id,user.username,user.first_name,now,now,now)); conn.commit()

def mark_member_post(chat_id,user_id):
    row=community_member(chat_id,user_id)
    if not row or row["status"]!="active": return False
    with community_db_connect() as conn: conn.execute("UPDATE community_members SET last_post_at=?,inactivity_notice_at=NULL,inactivity_notice_message_id=NULL WHERE chat_id=? AND user_id=?",(iso_now(),chat_id,user_id)); conn.commit()
    return True

def seed_admin_activity():
    main_group_id=configured_main_group_id()
    if not main_group_id:return
    now=iso_now()
    with community_db_connect() as conn:
        for admin_id in ADMIN_IDS: conn.execute("INSERT INTO community_members (chat_id,user_id,joined_at,verified_at,last_post_at,status) VALUES (?,?,?,?,?,'active') ON CONFLICT(chat_id,user_id) DO UPDATE SET status=CASE WHEN community_members.status IN ('left','removed') THEN 'active' ELSE community_members.status END",(main_group_id,int(admin_id),now,now,now))
        conn.commit()

def configured_main_group_id():
    try:return int(os.environ.get("MAIN_GROUP_ID","0") or "0")
    except (TypeError,ValueError):return 0

def configured_admin_group_id():
    try:return int(ADMIN_GROUP_ID_ENV.strip() or "0")
    except (TypeError,ValueError):return 0

def community_chat_is_allowed(chat_id):
    main=configured_main_group_id(); return not main or chat_id==main

def inactivity_keyboard(user_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("💜 I'M STAYING",callback_data=f"inactive:stay:{user_id}")],[InlineKeyboardButton("🚪 LEAVE GROUP",callback_data=f"inactive:leave:{user_id}")]])

async def send_inactivity_notice(context,row):
    try:
        message=await context.bot.send_message(chat_id=int(row["user_id"]),text=f"👋🏾 <b>Hey! We haven't seen you around Melanated AZ lately.</b> 💜\n\nIt's been about <b>{MEMBER_INACTIVITY_DAYS} days</b> since your last post.\n\nIf you're still rocking with us, tap <b>💜 I'M STAYING</b>.\n\nIf you're ready to move on, tap <b>🚪 LEAVE GROUP</b>.",reply_markup=inactivity_keyboard(int(row["user_id"])),parse_mode=ParseMode.HTML)
        with community_db_connect() as conn: conn.execute("UPDATE community_members SET inactivity_notice_at=?,inactivity_notice_message_id=? WHERE chat_id=? AND user_id=?",(iso_now(),message.message_id,row["chat_id"],row["user_id"])); conn.commit()
    except TelegramError: pass

async def inactivity_callback(update,context):
    query=update.callback_query; user=update.effective_user
    if not query or not query.data or not user:return
    parts=query.data.split(":")
    if len(parts)!=3:return
    try: target=int(parts[2])
    except ValueError:return
    if user.id!=target: await query.answer("This button belongs to another member.",show_alert=True); return
    main=configured_main_group_id()
    if parts[1]=="stay":
        with community_db_connect() as conn: conn.execute("UPDATE community_members SET last_post_at=?,inactivity_notice_at=NULL,inactivity_notice_message_id=NULL,status='active' WHERE chat_id=? AND user_id=?",(iso_now(),main,target)); conn.commit()
        await query.answer("You're staying! 💜 Timer reset.")
        try: await query.edit_message_text("💜 <b>You're staying!</b>\n\nYour activity timer has been reset.",parse_mode=ParseMode.HTML)
        except TelegramError: pass
    elif parts[1]=="leave":
        try:
            await context.bot.ban_chat_member(chat_id=main,user_id=target); await context.bot.unban_chat_member(chat_id=main,user_id=target,only_if_banned=True)
            with community_db_connect() as conn: conn.execute("UPDATE community_members SET status='left',inactivity_notice_at=NULL,inactivity_notice_message_id=NULL WHERE chat_id=? AND user_id=?",(main,target)); conn.commit()
            await query.answer("You have been removed from Melanated AZ.")
        except TelegramError: await query.answer("I couldn't remove you automatically. Please contact an admin.",show_alert=True)

async def remove_inactive_admin_from_admin_group(context,user_id,admin_group_id):
    try: await context.bot.ban_chat_member(chat_id=admin_group_id,user_id=user_id); await context.bot.unban_chat_member(chat_id=admin_group_id,user_id=user_id,only_if_banned=True); return True
    except TelegramError:return False

async def restrict_member(bot,chat_id,user_id):
    try: await bot.restrict_chat_member(chat_id=chat_id,user_id=user_id,permissions=ChatPermissions(can_send_messages=False)); return True
    except TelegramError:return False

async def restore_member(bot,chat_id,user_id):
    try: await bot.restrict_chat_member(chat_id=chat_id,user_id=user_id,permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_invite_users=True)); return True
    except TelegramError:return False

async def send_human_challenge(chat_id,user_id,context):
    row=community_member(chat_id,user_id)
    if not row:return
    answer,options=random.choice(HUMAN_CHALLENGES); shuffled=list(options); random.shuffle(shuffled)
    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton(option,callback_data=f"human_verify:{user_id}:{i}")] for i,option in enumerate(shuffled)])
    try:
        message=await context.bot.send_message(chat_id=chat_id,text=f"🤖 <b>QUICK HUMAN CHECK</b>\n\nBefore you join the conversation, prove you're human. 👀\n\n<b>Which one is {answer.split(' ',1)[1].lower()}?</b>\n\nTap the correct answer below.",reply_markup=keyboard,parse_mode=ParseMode.HTML)
        set_verification_challenge(chat_id,user_id,answer,shuffled,message.message_id)
    except TelegramError: logger.exception("Could not send human verification to %s",user_id)

async def community_chat_member_diagnostic(update,context): return

async def community_exit(update,context):
    event=update.chat_member
    if not event or not community_chat_is_allowed(event.chat.id):return
    old=event.old_chat_member.status; new=event.new_chat_member.status
    if old not in {"member","administrator","creator"} or new not in {"left","kicked"}:return
    user=event.old_chat_member.user
    if not user or user.is_bot:return
    with community_db_connect() as conn: conn.execute("UPDATE community_members SET status='left' WHERE chat_id=? AND user_id=?",(event.chat.id,user.id)); conn.commit()
    try:
        msg=await context.bot.send_message(chat_id=event.chat.id,text=f"👋🏾 <b>{user.first_name or user.username or 'Someone'} has left Melanated AZ.</b> 💜\n\nWe wish you nothing but good vibes wherever you go. 🖤💜",parse_mode=ParseMode.HTML)
        if context.job_queue: context.job_queue.run_once(delete_message_job,300,data=(event.chat.id,msg.message_id))
    except TelegramError: pass

async def send_community_intro_video(chat_id,context,member_name):
    if not INTRO_VIDEO_FILE_ID and not os.path.isfile(INTRO_VIDEO_PATH): return None
    video_file=INTRO_VIDEO_FILE_ID or open(INTRO_VIDEO_PATH,"rb")
    try:
        intro_video=await context.bot.send_video(chat_id=chat_id,video=video_file,caption=f"🎬 <b>WELCOME TO MELANATED AZ, {member_name}!</b> 💜\n\nTurn it up. 🔥🖤💜",parse_mode=ParseMode.HTML,supports_streaming=True)
        if context.job_queue: context.job_queue.run_once(delete_message_job,INTRO_VIDEO_DELETE_SECONDS,data=(chat_id,intro_video.message_id))
        return intro_video
    except (TelegramError,OSError): return None
    finally:
        if hasattr(video_file,"close"):
            try: video_file.close()
            except Exception: pass

async def community_welcome(update,context):
    event=update.chat_member
    if not event or not community_chat_is_allowed(event.chat.id):return
    old=event.old_chat_member.status; new=event.new_chat_member.status
    if new not in {"member","administrator"} or old not in {"left","kicked"}:return
    user=event.new_chat_member.user
    if not user or user.is_bot or await is_admin(user.id,context):return
    save_joining_member(event.chat.id,user); await restrict_member(context.bot,event.chat.id,user.id); name=user.first_name or "there"; await send_community_intro_video(event.chat.id,context,name)
    try:
        welcome=await context.bot.send_message(chat_id=event.chat.id,text=f"👋🏾 <b>WELCOME TO MELANATED AZ, {name}!</b> 💜🔥\n\n🛡️ <b>FIRST THINGS FIRST...</b>\n\nYou need to complete a quick human verification before you can post.\n\nOnce you're verified, you'll have <b>48 HOURS</b> to introduce yourself to the community.\n\nGood energy. Real people. Real connections. 🖤💜",parse_mode=ParseMode.HTML); context.job_queue.run_once(delete_message_job,VERIFICATION_MESSAGE_TTL_MINUTES*60,data=(event.chat.id,welcome.message_id))
    except TelegramError: pass
    await send_human_challenge(event.chat.id,user.id,context)

async def human_verification_callback(update,context):
    query=update.callback_query
    if not query or not query.data:return
    try: await query.answer()
    except Exception: pass
    parts=query.data.split(":")
    if len(parts)!=3:return
    try: target=int(parts[1]); selected=int(parts[2])
    except ValueError:return
    user=update.effective_user; chat=update.effective_chat
    if not user or not chat or user.id!=target:return
    row=community_member(chat.id,user.id)
    if not row or row["status"]!="pending_verification":return
    expires=parse_iso(row["verification_expires_at"]); challenge=row["verification_challenge"] or ""
    if not expires or expires<utc_now() or "###" not in challenge: await send_human_challenge(chat.id,user.id,context); return
    answer,blob=challenge.split("###",1); options=blob.split("|||")
    if selected<0 or selected>=len(options):return
    if options[selected]!=answer:
        attempts=increment_verification_attempt(chat.id,user.id)
        if attempts>=VERIFICATION_MAX_ATTEMPTS: await remove_unverified_member(context.bot,chat.id,user.id); return
        await send_human_challenge(chat.id,user.id,context); return
    mark_verified(chat.id,user.id); await restore_member(context.bot,chat.id,user.id); private_opened=await send_private_intro_prompt(user,context)
    try: await query.edit_message_text("✅ <b>HUMAN VERIFICATION PASSED!</b> 🎉\n\nYou're cleared to participate. 💜\n\n👋🏾 I've sent your introduction instructions privately.\nYour intro submission will stay private until the finished introduction is posted in the 👋 Introductions topic.",parse_mode=ParseMode.HTML)
    except TelegramError: pass

def intro_private_keyboard(user_id): return InlineKeyboardMarkup([[InlineKeyboardButton("👋🏾 Submit My Introduction",callback_data=f"intro_submit_{user_id}")]])
def intro_view_keyboard(user_id): return InlineKeyboardMarkup([[InlineKeyboardButton("✏️ Update My Intro",callback_data=f"intro_submit_{user_id}")],[InlineKeyboardButton("❌ Close",callback_data=f"intro_close_{user_id}")]])
def intro_topic_text(user,intro_text,updated=False): return f"👋🏾 <b>{'UPDATED INTRODUCTION' if updated else 'INTRODUCTION'}</b>\n\n👤 <b>{html.escape(user.full_name or user.first_name or 'Melanated AZ Member')}</b>\n\n{html.escape(intro_text)}"

async def send_private_intro_prompt(user,context,update_existing=False):
    if not user:return False
    context.user_data["awaiting_intro_submission"]=True; context.user_data["intro_submission_user_id"]=user.id
    text=("✏️ <b>Update Your Melanated AZ Introduction</b>\n\n" if update_existing else "👋🏾 <b>Let's Get Your Introduction Saved</b>\n\n")+("Your current intro is saved. Send your new intro below and I'll replace it.\n\n" if update_existing else "Your introduction will be saved to your Melanated AZ member profile and posted in the 👋 Introductions topic.\n\n")+"🔒 <b>This submission stays private.</b> The group will only see the finished introduction after you submit it.\n\nTell us what you go by, your relationship / dynamic status, where you're from, what city & state you're in, what brought you to Melanated AZ, what you're into, and what you're looking for — or whatever you're comfortable sharing.\n\n"+f"Keep it under <b>{INTRO_MAX_CHARS} characters</b>.\n\n👇🏾 <b>Send your introduction as your next message.</b>"
    try: await context.bot.send_message(chat_id=user.id,text=text,parse_mode=ParseMode.HTML,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel",callback_data=f"intro_close_{user.id}")]])); return True
    except TelegramError:return False

async def intro_callback(update,context):
    query=update.callback_query; user=update.effective_user
    if not query or not user or not query.data:return
    try: target=int(query.data.split("_")[-1])
    except ValueError:return
    if user.id!=target:return
    if query.data.startswith("intro_close_"):
        context.user_data.pop("awaiting_intro_submission",None); context.user_data.pop("intro_submission_user_id",None); await query.answer("Intro submission closed."); return
    if query.data.startswith("intro_submit_"):
        row=community_member(configured_main_group_id(),user.id)
        if not row or not row["verified_at"]: await query.answer("You need to be verified in Melanated AZ first.",show_alert=True); return
        await query.answer(); await send_private_intro_prompt(user,context,update_existing=bool(row["intro_text"]))

async def private_intro_text_handler(update,context):
    message=update.effective_message; user=update.effective_user; chat=update.effective_chat
    if not message or not user or not chat or chat.type!="private" or user.is_bot or not context.user_data.get("awaiting_intro_submission") or context.user_data.get("intro_submission_user_id")!=user.id or not message.text or message.text.startswith("/"):return
    intro_text=message.text.strip()
    if not intro_text or len(intro_text)>INTRO_MAX_CHARS:return
    main=configured_main_group_id(); row=community_member(main,user.id) if main else None
    if not row or not row["verified_at"]:return
    try: topic_message=await context.bot.send_message(chat_id=main,message_thread_id=INTRO_TOPIC_ID,text=intro_topic_text(user,intro_text,updated=bool(row["intro_text"])),parse_mode=ParseMode.HTML)
    except TelegramError: return
    save_intro(main,user.id,intro_text,topic_message.message_id); context.user_data.pop("awaiting_intro_submission",None); context.user_data.pop("intro_submission_user_id",None)
    await message.reply_text("🎉 <b>INTRO SAVED!</b> 💜\n\nYour introduction is now posted in the 👋 Introductions topic.",parse_mode=ParseMode.HTML,reply_markup=intro_view_keyboard(user.id))

async def private_intro_view_callback(update,context):
    query=update.callback_query; user=update.effective_user
    if not query or not user or not query.data:return
    try: target=int(query.data.split("_")[-1])
    except ValueError:return
    if user.id!=target:return
    row=community_member(configured_main_group_id(),user.id); intro=row["intro_text"] if row else None
    if not intro:return
    await query.answer()
    if query.data.startswith("intro_view_"): await query.message.reply_text("👋🏾 <b>Your Saved Introduction</b>\n\n"+html.escape(intro),parse_mode=ParseMode.HTML,reply_markup=intro_view_keyboard(user.id))

async def verification_message_guard(update,context):
    message=update.effective_message; user=update.effective_user; chat=update.effective_chat
    if not message or not user or not chat or user.is_bot:return
    main=configured_main_group_id()
    if main and chat.id!=main:return
    if await is_admin(user.id,context):
        if not community_member(chat.id,user.id):ensure_tracked_member(chat.id,user)
        mark_member_post(chat.id,user.id); return
    row=community_member(chat.id,user.id)
    if not row:ensure_tracked_member(chat.id,user); mark_member_post(chat.id,user.id); return
    if row["status"]=="pending_verification":
        try: await message.delete()
        except TelegramError:pass
    elif row["status"]=="active":mark_member_post(chat.id,user.id)

async def remove_unverified_member(bot,chat_id,user_id):
    try: await bot.ban_chat_member(chat_id=chat_id,user_id=user_id); await bot.unban_chat_member(chat_id=chat_id,user_id=user_id,only_if_banned=True)
    except TelegramError:pass
    with community_db_connect() as conn: conn.execute("UPDATE community_members SET status='removed' WHERE chat_id=? AND user_id=?",(chat_id,user_id)); conn.commit()

async def delete_message_job(context):
    data=context.job.data if context.job else None
    if not data:return
    try: await context.bot.delete_message(chat_id=data[0],message_id=data[1])
    except TelegramError:pass

async def send_monthly_intro_reminders(context):
    main=configured_main_group_id()
    if not main:return
    now=utc_now(); cutoff=now-timedelta(days=30)
    with community_db_connect() as conn:
        rows=conn.execute("SELECT * FROM community_members WHERE chat_id=? AND status NOT IN ('left','removed') AND (intro_text IS NULL OR TRIM(intro_text)='') AND (monthly_intro_reminder_at IS NULL OR monthly_intro_reminder_at<=?)",(main,cutoff.isoformat())).fetchall()
    bot_username=context.application.bot_data.get("bot_username")
    for row in rows:
        uid=int(row["user_id"])
        try:
            live=await context.bot.get_chat_member(main,uid)
            if getattr(live,"status","") not in {"member","administrator","creator"}:continue
            if await is_admin(uid,context):continue
            first_name=getattr(getattr(live,"user",None),"first_name",None) or row["first_name"] or "there"
            url=f"https://t.me/{bot_username}?start=intro" if bot_username else None
            keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("👋🏾 Complete My Intro",url=url)]]) if url else None
            text=f"👋🏾 <b>Hey {html.escape(first_name)}!</b> 💜\n\nWe’d love to get to know you a little better. Your introduction is still missing, and it’s required for everyone in the Melanated AZ community.\n\nIt only takes a few minutes and helps everyone know who’s part of the community.\n\n🎂 <b>Birthday is optional</b>, but if you add yours, we’ll make sure you get a birthday shoutout! 🎉\n\nWhenever you’re ready, tap below to complete your intro. 👇🏾"
            await context.bot.send_message(chat_id=uid,text=text,reply_markup=keyboard,parse_mode=ParseMode.HTML)
            with community_db_connect() as conn:
                conn.execute("UPDATE community_members SET monthly_intro_reminder_at=? WHERE chat_id=? AND user_id=?",(now.isoformat(),main,uid)); conn.commit()
        except TelegramError:pass
        except Exception:logger.exception("Monthly intro reminder failed for %s",uid)

def start_monthly_intro_reminders(application):
    if not application.job_queue:return
    application.job_queue.run_once(send_monthly_intro_reminders,when=10,name="monthly-intro-reminders-initial")
    application.job_queue.run_repeating(send_monthly_intro_reminders,interval=86400,first=86400,name="monthly-intro-reminders")
    logger.info("Monthly private intro reminders enabled | first run now | cadence 30 days per member")

async def community_security_monitor(context):
    now=utc_now()
    with community_db_connect() as conn: rows=conn.execute("SELECT * FROM community_members WHERE status IN ('pending_verification','verified_intro_pending')").fetchall()
    for row in rows:
        deadline=parse_iso(row["intro_deadline"]); joined=parse_iso(row["joined_at"])
        if row["status"]=="pending_verification" and joined and joined+timedelta(hours=INTRO_HOURS)<=now: await remove_unverified_member(context.bot,row["chat_id"],row["user_id"])
        elif row["status"]=="verified_intro_pending" and deadline and deadline<=now: await remove_unverified_member(context.bot,row["chat_id"],row["user_id"])
    main=configured_main_group_id()
    if not main:return
    cutoff=now-timedelta(days=MEMBER_INACTIVITY_DAYS)
    with community_db_connect() as conn: inactive=conn.execute("SELECT * FROM community_members WHERE chat_id=? AND status='active' AND last_post_at IS NOT NULL AND last_post_at<=? AND inactivity_notice_at IS NULL",(main,cutoff.isoformat())).fetchall()
    for row in inactive:
        if not await is_admin(int(row["user_id"]),context): await send_inactivity_notice(context,row)
    admin_group=configured_admin_group_id()
    if not admin_group:return
    cutoff=now-timedelta(days=ADMIN_INACTIVITY_DAYS)
    with community_db_connect() as conn: admins=conn.execute("SELECT * FROM community_members WHERE chat_id=? AND status='active' AND last_post_at IS NOT NULL AND last_post_at<=?",(main,cutoff.isoformat())).fetchall()
    for row in admins:
        if await is_admin(int(row["user_id"]),context): await remove_inactive_admin_from_admin_group(context,int(row["user_id"]),admin_group)

def start_community_security_monitor(application):
    if application.job_queue: application.job_queue.run_repeating(community_security_monitor,interval=INACTIVITY_CHECK_HOURS*60*60,first=60,name="community-security-monitor")

async def text_router(update,context):
    try:
        from member_bank import member_bank_message_handler
        if await member_bank_message_handler(update,context):return
    except Exception:
        logger.exception("Member bank message handler failed.")
    if await admin_birthday_text_handler(update,context):return
    await birthday_text_handler(update,context)

async def start_command(update,context):
    message=update.effective_message; user=update.effective_user
    if not message or not user:return
    try:
        if await handle_real_game_deep_link(update,context):return
    except Exception: logger.exception("Real Games deep-link processing failed."); return
    if context.args and context.args[0].lower()=="intro":
        row=community_member(configured_main_group_id(),user.id)
        if not row or not row["verified_at"]: await message.reply_text("👋🏾 <b>You need to complete Melanated AZ verification first.</b>",parse_mode=ParseMode.HTML); return
        await send_private_intro_prompt(user,context,update_existing=bool(row["intro_text"])); return
    text="👋 <b>Welcome to Melanated AZ Bot!</b>\n\n🎂 Birthdays\n🎟️ Raffles\n🔥 Truth or Dare\n🎮 Game Center\n🎲 Real Games\n🛡️ Media protection"
    if await is_admin(user.id,context):text+="\n\n👑 <b>Admin:</b> <code>/admin</code>"
    await message.reply_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 REAL GAMES",callback_data="real_games_menu")]]),parse_mode=ParseMode.HTML)

async def my_intro_command(update,context):
    message=update.effective_message; user=update.effective_user
    if not message or not user or message.chat.type!="private":return
    row=community_member(configured_main_group_id(),user.id); intro=row["intro_text"] if row else None
    if not intro: await message.reply_text("👋🏾 <b>You don't have a saved introduction yet.</b>",parse_mode=ParseMode.HTML,reply_markup=intro_private_keyboard(user.id)); return
    await message.reply_text("👋🏾 <b>Your Saved Introduction</b>\n\n"+html.escape(intro),parse_mode=ParseMode.HTML,reply_markup=intro_view_keyboard(user.id))

async def startgames_command(update,context):
    if update.effective_message: await update.effective_message.reply_text("🎮 <b>MELANATED AZ GAME CENTER</b>\n\nTap below to enter the Game Center!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 PLAY GAMES",url="https://melanatedaz.onrender.com/real-games/")]]),parse_mode=ParseMode.HTML)

async def real_games_command(update,context):
    if update.effective_message: await update.effective_message.reply_text("🎮 <b>Melanated AZ Real Games</b>\n\nChoose a game below:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 REAL GAMES",url="https://melanatedaz.onrender.com/real-games/")],[InlineKeyboardButton("🎲 MONOPOLY",url="https://melanatedaz.onrender.com/real-games/monopoly/")]]),parse_mode=ParseMode.HTML)

async def admin_command(update,context):
    if update.effective_user and await is_admin(update.effective_user.id,context): await admin_menu(update,context)
    elif update.effective_message: await update.effective_message.reply_text("⛔ You are not authorized to use the admin panel.")

async def admin_callback_router(update,context):
    if update.effective_user and await is_admin(update.effective_user.id,context): await admin_button(update,context)

async def birthday_callback_router(update,context): await birthday_callback(update,context)
async def game_center_callback_router_wrapper(update,context): await game_center_callback_router(update,context)
async def real_games_callback_router(update,context):
    query=update.callback_query
    if not query:return
    await query.answer()
    await query.message.reply_text("🎮 <b>REAL GAMES</b>\n\nChoose a game:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 MONOPOLY",url="https://melanatedaz.onrender.com/real-games/monopoly/")],[InlineKeyboardButton("🎮 ALL REAL GAMES",url="https://melanatedaz.onrender.com/real-games/")]]),parse_mode=ParseMode.HTML)
async def truth_dare_callback_router(update,context): await truth_dare_callback(update,context)
async def raffle_callback_router(update,context): await raffle_callback(update,context)

def database_startup_check():
    try:
        stats=get_database_stats(); logger.info("Database: %s | Raffles=%s | Entries=%s | Birthdays=%s | Integrity=%s",stats.get("database"),stats.get("raffles"),stats.get("raffle_entries"),stats.get("birthdays"),"OK" if check_database_integrity() else "FAILED")
    except Exception:logger.exception("Database startup check failed.")

def game_database_startup_check():
    try:initialize_game_database(); logger.info("Game Center database: READY")
    except Exception:logger.exception("Game Center database initialization failed.")

def real_games_startup_check():
    logger.info("Real Games URL: %s",os.environ.get("PUBLIC_BASE_URL","").strip().rstrip("/")+"/real-games/")

async def repair_active_raffle_post(context):
    """One-time repair: publish the existing active raffle once in topic 11883.
    No repeating manager. No new raffle. A persistent marker prevents reposts on restarts.
    """
    marker="/var/data/raffle_topic_11883_repair_v1.done" if os.path.isdir("/var/data") else "./raffle_topic_11883_repair_v1.done"
    if os.path.exists(marker):
        logger.info("Raffle topic 11883 one-time repair already completed.")
        return
    raffle=get_active_raffle()
    if not raffle:
        logger.info("Raffle topic repair skipped: no active raffle.")
        return
    raffle_id=int(raffle["id"])
    try:
        # Do not write None into the raffle post fields. publish_raffle()
        # creates the replacement post and saves its real Telegram IDs.
        if await publish_raffle(raffle_id,context):
            os.makedirs(os.path.dirname(marker) or ".",exist_ok=True)
            with open(marker,"w",encoding="utf-8") as fh: fh.write(f"raffle={raffle_id}\n")
            logger.info("ONE-TIME RAFFLE REPAIR COMPLETE | raffle=%s | topic=11883",raffle_id)
        else:
            logger.error("ONE-TIME RAFFLE REPAIR FAILED | raffle=%s | topic=11883",raffle_id)
    except Exception:
        logger.exception("One-time raffle topic repair failed.")

# ==========================================================
# RAFFLE MAIN REPOST TEST CHECKER
# Single owner: bot.py
# ==========================================================
RAFFLE_MAIN_REPOST_HOUR = 18
RAFFLE_MAIN_REPOST_MINUTE = 20
RAFFLE_MAIN_REPOST_TZ = ZoneInfo("America/Phoenix")

async def _raffle_main_chat_repost_checker(context):
    now = datetime.now(RAFFLE_MAIN_REPOST_TZ)
    if now.hour != RAFFLE_MAIN_REPOST_HOUR or now.minute != RAFFLE_MAIN_REPOST_MINUTE:
        return

    today = now.date().isoformat()
    if context.application.bot_data.get("raffle_main_repost_date") == today:
        return

    logger.info(
        "RAFFLE MAIN REPOST TRIGGER MATCHED | local_time=%s | configured=%02d:%02d Arizona",
        now.strftime("%Y-%m-%d %H:%M:%S"),
        RAFFLE_MAIN_REPOST_HOUR,
        RAFFLE_MAIN_REPOST_MINUTE,
    )

    try:
        from raffle import post_raffle_status_to_main_chat
        posted = await post_raffle_status_to_main_chat(context)
        if posted:
            context.application.bot_data["raffle_main_repost_date"] = today
            logger.info(
                "RAFFLE MAIN REPOST COMPLETE | time=%02d:%02d Arizona",
                RAFFLE_MAIN_REPOST_HOUR,
                RAFFLE_MAIN_REPOST_MINUTE,
            )
        else:
            logger.warning(
                "RAFFLE MAIN REPOST DID NOT POST | no active raffle or send failure"
            )
    except Exception:
        logger.exception("RAFFLE MAIN REPOST FAILED")

def build_application():
    if not BOT_TOKEN:raise RuntimeError("BOT_TOKEN is not configured.")
    application=Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    if application.job_queue:
        for job in application.job_queue.get_jobs_by_name("raffle-main-chat-repost-checker"):
            job.schedule_removal()
        application.job_queue.run_repeating(
            _raffle_main_chat_repost_checker,
            interval=30,
            first=5,
            name="raffle-main-chat-repost-checker",
        )
        logger.info(
            "RAFFLE MAIN REPOST SCHEDULER REGISTERED | checker=30s | target=%02d:%02d Arizona",
            RAFFLE_MAIN_REPOST_HOUR,
            RAFFLE_MAIN_REPOST_MINUTE,
        )

    # QOTD and After Dark are separate startup paths.
    try:
        from topic_routing import install_all_topic_routing
        install_all_topic_routing()
        from question_of_day import register_question_of_day_handlers, start_question_of_day_scheduler
        register_question_of_day_handlers(application)
        start_question_of_day_scheduler(application)
    except Exception:
        logger.exception("Unable to initialize Question of the Day scheduler.")

    try:
        from topic_routing import start_after_dark_scheduler
        start_after_dark_scheduler(application)
        jobs = application.job_queue.get_jobs_by_name("melanated-after-dark-message") if application.job_queue else []
        if jobs:
            logger.info("After Dark scheduler REGISTERED | jobs=%s | schedule=23:00 Arizona | chat=-1002697105809 topic=11999", len(jobs))
        else:
            logger.error("After Dark scheduler NOT REGISTERED | JobQueue job missing during build_application.")
    except Exception:
        logger.exception("Unable to initialize After Dark scheduler.")
    for command,callback in [("start",start_command),("startgames",startgames_command),("myintro",my_intro_command),("realgames",real_games_command),("admin",admin_command),("startraffle",start_raffle),("rafflestatus",raffle_status),("entries",raffle_entries),("pending",pending_entries),("paid",paid_entry),("cancelraffle",cancel_raffle),("draw",draw_raffle),("games",games_command),("birthday",birthday),("mybirthday",my_birthday),("removebirthday",remove_my_birthday),("truthdare",truth_dare_menu),("truth",truth),("dare",dare),("postintro",post_intro_topic_command)]: application.add_handler(CommandHandler(command,callback))
    application.add_handler(CallbackQueryHandler(raffle_callback_router,pattern=r"^(raffle_|approve_|deny_|enter_|pay_|payment_|paid_|draw_|reroll_|bonus_|remove_)"))
    application.add_handler(CallbackQueryHandler(admin_callback_router,pattern=r"^admin_"))
    application.add_handler(CallbackQueryHandler(birthday_callback_router,pattern=r"^birthday_"))
    application.add_handler(CallbackQueryHandler(game_center_callback_router_wrapper,pattern=r"^(games_|game_)"))
    application.add_handler(CallbackQueryHandler(real_games_callback_router,pattern=r"^real_games_"))
    application.add_handler(CallbackQueryHandler(truth_dare_callback_router,pattern=r"^truthdare_"))
    application.add_handler(CallbackQueryHandler(intro_callback,pattern=r"^intro_(submit|close)_"))
    application.add_handler(CallbackQueryHandler(inactivity_callback,pattern=r"^inactive:"))
    application.add_handler(CallbackQueryHandler(human_verification_callback,pattern=r"^human_verify:"))
    application.add_handler(MessageHandler(filters.ALL,verification_message_guard),group=1)
    application.add_handler(ChatMemberHandler(community_chat_member_diagnostic,ChatMemberHandler.CHAT_MEMBER),group=0)
    application.add_handler(ChatMemberHandler(community_welcome,ChatMemberHandler.CHAT_MEMBER),group=1)
    application.add_handler(ChatMemberHandler(community_exit,ChatMemberHandler.CHAT_MEMBER),group=2)
    application.add_handler(MessageHandler(filters.PHOTO,handle_photo),group=5)
    application.add_handler(MessageHandler(filters.VIDEO,handle_video),group=5)
    application.add_handler(MessageHandler(filters.ANIMATION,handle_animation),group=5)
    application.add_handler(MessageHandler(filters.Document.IMAGE,handle_image_document),group=5)
    application.add_handler(CallbackQueryHandler(private_intro_view_callback,pattern=r"^intro_view_"),group=0)
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,private_intro_text_handler),group=0)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_raffle_setup),group=0)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text_router),group=10)
    application.add_error_handler(error_handler)
    return application

async def post_init(application):
    try:
        me=await application.bot.get_me(); application.bot_data["bot_username"]=me.username
    except Exception:logger.exception("Could not retrieve bot information.")
    main=configured_main_group_id()
    if main:
        try:
            member=await application.bot.get_chat_member(main,application.bot.id)
            logger.info("Community bot membership: status=%s | can_restrict_members=%s | can_delete_messages=%s",member.status,getattr(member,"can_restrict_members",None),getattr(member,"can_delete_messages",None))
        except TelegramError:logger.exception("Could not inspect bot membership.")
    application.bot_data["public_base_url"]=os.environ.get("PUBLIC_BASE_URL","").strip().rstrip("/")

async def error_handler(update,context):
    if isinstance(context.error,BadRequest):logger.warning("Telegram BadRequest: %s",context.error); return
    logger.exception("Unhandled bot exception:",exc_info=context.error)

def main():
    database_startup_check(); game_database_startup_check(); real_games_startup_check()
    threading.Thread(target=run_flask,daemon=True,name="flask-health-server").start()
    initialize_community_security_database(); seed_admin_activity()
    application=build_application()
    start_community_security_monitor(application)
    start_monthly_intro_reminders(application)
    start_weekly_game_center_reminder(application)
    # Daily raffle status is intentionally disabled: the raffle should be one post, not recurring status messages.
    logger.info("Daily raffle status scheduler disabled; raffle uses one permanent post in topic 11883.")
    start_raffle_cleanup_recovery(application)
    # One-time repair of the existing active raffle. This does NOT create a raffle and does NOT repeat.
    if application.job_queue:
        application.job_queue.run_once(repair_active_raffle_post,when=10,name="one-time-raffle-topic-repair")
    logger.info("Raffle topic configured: chat=%s topic=11883 | one-time repair enabled",RAFFLE_CHAT_ID)
    allowed_updates=list(Update.ALL_TYPES)
    if "chat_member" not in allowed_updates:allowed_updates.append("chat_member")
    application.run_polling(allowed_updates=allowed_updates,drop_pending_updates=False,close_loop=False)

if __name__=="__main__":main()
