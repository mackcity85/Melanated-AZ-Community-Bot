# Melanated AZ Bot launcher
# Install topic routing before any QOTD module is imported so its
# America/Phoenix topic/schedule configuration is loaded correctly.

import bot
import topic_routing
import media_router
import dirty_minds_admin_override
import grand_rising
import html
from datetime import time
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from raffle import (
    get_active_raffle,
    get_pending_entries,
    get_approved_entries,
    is_free_raffle,
    format_expiration,
)


topic_routing.install_all_topic_routing()
media_router.install(bot)

import runtime_fixes  # noqa: F401
import qotd_td_user  # noqa: F401
import admin_truth_dare_qotd  # noqa: F401
import event_admin_panel
import intro_persistence
import intro_reminder_fix
import raffle_manual_nav_fix
from games.game_topic_pins import ensure_game_topic_pins

event_admin_panel.install()
raffle_manual_nav_fix.install()


# ==========================================================
# ADMIN PANEL — CENTRAL CALLBACK ROUTER REPAIR
# ==========================================================
_original_admin_callback_router = bot.admin_callback_router


async def _verified_admin_callback_router(update, context):
    query = update.callback_query
    user = update.effective_user
    data = query.data if query else None

    if not query:
        return

    bot.logger.info(
        "ADMIN CALLBACK RECEIVED | data=%s | user_id=%s | chat_id=%s",
        data,
        user.id if user else None,
        update.effective_chat.id if update.effective_chat else None,
    )

    try:
        await bot.admin_button(update, context)
    except Exception:
        bot.logger.exception(
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


bot.admin_callback_router = _verified_admin_callback_router


_original_build_application = bot.build_application


async def _run_games_topic_pin_maintenance(context):
    """Run the Games-topic launcher maintenance after PTB JobQueue starts."""
    bot.logger.info(
        "Games-topic pin maintenance START | chat=%s topic=%s",
        -1002697105809,
        11999,
    )
    try:
        await ensure_game_topic_pins(context.bot)
        bot.logger.info(
            "Games-topic pin maintenance COMPLETE | chat=%s topic=%s",
            -1002697105809,
            11999,
        )
    except Exception:
        bot.logger.exception(
            "Games-topic pin maintenance FAILED | chat=%s topic=%s",
            -1002697105809,
            11999,
        )


async def _daily_raffle_status_public(context):
    """Post the public 2 PM raffle status with counts only, never entry details."""
    raffle = get_active_raffle()
    if not raffle:
        bot.logger.info("Daily raffle status skipped: no active raffle.")
        return

    free = is_free_raffle(raffle.get("price"))
    approved = get_approved_entries(raffle["id"])
    pending = get_pending_entries(raffle["id"])
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
        f"⏰ <b>Ends:</b> {format_expiration(raffle.get('expires_at'))}\n\n"
        f"✅ <b>Approved Entries:</b> {len(approved)}\n"
        f"⏳ <b>Pending Entries:</b> {len(pending)}\n\n"
        "👇 <b>Tap ENTER RAFFLE to join!</b>"
    )

    try:
        sent = await context.bot.send_message(
            chat_id=-1002697105809,
            message_thread_id=11883,
            text=text,
            reply_markup=InlineKeyboardMarkup(rows),
            parse_mode=ParseMode.HTML,
        )
        bot.logger.info(
            "DAILY RAFFLE STATUS POSTED | raffle=%s | chat=%s | topic=%s | message=%s",
            raffle["id"],
            -1002697105809,
            11883,
            sent.message_id,
        )
    except Exception:
        bot.logger.exception(
            "Could not post daily raffle status | raffle=%s",
            raffle["id"],
        )


# ==========================================================
# BUILD APPLICATION
# ==========================================================

def build_application(*args, **kwargs):
    application = _original_build_application(*args, **kwargs)

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(
            _daily_raffle_status_public,
            time(hour=14, minute=0, tzinfo=ZoneInfo("America/Phoenix")),
            name="daily-raffle-status",
        )
        bot.logger.info(
            "Daily raffle status scheduler VERIFIED | time=14:00 Arizona | chat=-1002697105809 topic=11883"
        )
        job_queue.run_once(
            _run_games_topic_pin_maintenance,
            when=5,
            name="games-topic-pin-maintenance-startup",
        )

    return application


bot.build_application = build_application


# ==========================================================
# LAUNCH
# ==========================================================
if __name__ == "__main__":
    bot.run_bot()
