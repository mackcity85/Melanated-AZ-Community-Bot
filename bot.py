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

# ... existing bot.py implementation remains unchanged ...

async def admin_command(update,context):
    if update.effective_user and await is_admin(update.effective_user.id,context): await admin_menu(update,context)
    elif update.effective_message: await update.effective_message.reply_text("⛔ You are not authorized to use the admin panel.")


# ==========================================================
# ADMIN CALLBACK ROUTER — PANEL-WIDE REPAIR
# ==========================================================

async def admin_callback_router(update, context):
    """
    Single entry point for EVERY callback beginning with admin_.

    Do not perform a second authorization gate here.  admin_button()
    owns the centralized authorization check.  The old router silently
    discarded callbacks whenever its preliminary is_admin() call failed,
    which made every admin-panel button appear dead and gave no useful
    Telegram feedback or exception logging.

    Keeping one authorization owner also prevents the router and the
    admin-panel implementation from getting out of sync when ADMIN_GROUP_ID
    membership or ADMIN_IDS configuration changes.
    """
    query = update.callback_query
    user = update.effective_user

    if not query:
        return

    data = query.data or ""

    logger.info(
        "ADMIN CALLBACK RECEIVED | data=%s | user_id=%s | chat_id=%s",
        data,
        user.id if user else None,
        update.effective_chat.id if update.effective_chat else None,
    )

    try:
        # admin_button() performs the authoritative authorization check and
        # dispatches the complete admin callback tree, including dynamic
        # member/birthday/Dirty Minds/manual-entry callbacks.
        await admin_button(update, context)
    except Exception:
        logger.exception(
            "ADMIN CALLBACK FAILED | data=%s | user_id=%s",
            data,
            user.id if user else None,
        )

        try:
            await query.answer(
                "⚠️ Admin panel error. Check the Render logs.",
                show_alert=True,
            )
        except Exception:
            pass


async def birthday_callback_router(update,context): await birthday_callback(update,context)
async def game_center_callback_router_wrapper(update,context): await game_center_callback_router(update,context)
async def real_games_callback_router(update,context):
    query=update.callback_query
    if not query:return
    await query.answer()
    await query.message.reply_text("🎮 <b>REAL GAMES</b>\n\nChoose a game:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 MONOPOLY",url="https://melanatedaz.onrender.com/real-games/monopoly/")],[InlineKeyboardButton("🎮 ALL REAL GAMES",url="https://melanatedaz.onrender.com/real-games/")]]),parse_mode=ParseMode.HTML)
async def truth_dare_callback_router(update,context): await truth_dare_callback(update,context)
async def raffle_callback_router(update,context): await raffle_callback(update,context)

# ... remainder of existing bot.py implementation remains unchanged ...
