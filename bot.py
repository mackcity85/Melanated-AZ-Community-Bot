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

async def start_flask_and_bot(*args, **kwargs):
    pass

# ... existing bot implementation ...


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
        if await publish_raffle(raffle_id,context):
            os.makedirs(os.path.dirname(marker) or ".",exist_ok=True)
            with open(marker,"w",encoding="utf-8") as fh: fh.write(f"raffle={raffle_id}\n")
            logger.info("ONE-TIME RAFFLE REPAIR COMPLETE | raffle=%s | topic=11883",raffle_id)
        else:
            logger.error("ONE-TIME RAFFLE REPAIR FAILED | raffle=%s",raffle_id)
    except Exception:
        logger.exception("One-time raffle topic repair failed.")

def build_application():
    if not BOT_TOKEN:raise RuntimeError("BOT_TOKEN is not configured.")
    application=Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Direct QOTD integration belongs to the real bot application.
    try:
        from topic_routing import install_all_topic_routing, start_after_dark_scheduler
        install_all_topic_routing()
        from question_of_day import register_question_of_day_handlers, start_question_of_day_scheduler
        register_question_of_day_handlers(application)
        start_question_of_day_scheduler(application)

        # Register After Dark directly on the real application JobQueue.
        # This is intentionally independent of QOTD and Daily Community so a
        # failure in a QOTD startup hook cannot prevent the 11 PM job from
        # existing. The helper removes/replaces any duplicate by name.
        start_after_dark_scheduler(application)
        after_dark_jobs = application.job_queue.get_jobs_by_name("melanated-after-dark-message") if application.job_queue else []
        if after_dark_jobs:
            logger.info(
                "After Dark scheduler REGISTERED | jobs=%s | schedule=23:00 Arizona | chat=-1002697105809 topic=11999",
                len(after_dark_jobs),
            )
        else:
            logger.error(
                "After Dark scheduler NOT REGISTERED | JobQueue job missing during build_application."
            )
    except Exception:
        logger.exception("Unable to initialize Question of the Day / After Dark schedulers.")
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

def error_handler(update,context):
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
    logger.info("Daily raffle status scheduler disabled; raffle uses one permanent post in topic 11883.")
    start_raffle_cleanup_recovery(application)
    if application.job_queue:
        application.job_queue.run_once(repair_active_raffle_post,when=10,name="one-time-raffle-topic-repair")
    logger.info("Raffle topic configured: chat=%s topic=11883 | one-time repair enabled",RAFFLE_CHAT_ID)
    allowed_updates=list(Update.ALL_TYPES)
    if "chat_member" not in allowed_updates:allowed_updates.append("chat_member")
    application.run_polling(allowed_updates=allowed_updates,drop_pending_updates=False,close_loop=False)

if __name__=="__main__":main()
