# Melanated AZ Bot launcher
# Install topic routing before any QOTD module is imported so its
# America/Phoenix topic/schedule configuration is loaded correctly.

import bot
import topic_routing
import media_router
import dirty_minds_admin_override
import grand_rising
import html
from datetime import datetime, time
from zoneinfo import ZoneInfo
from pathlib import Path
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


RAFFLE_STATUS_TZ = ZoneInfo("America/Phoenix")
RAFFLE_STATUS_HOUR = 14
RAFFLE_STATUS_MINUTE = 0
RAFFLE_STATUS_STATE_FILE = Path("/var/data/daily_raffle_status.json")


def _raffle_status_already_posted(today):
    try:
        if not RAFFLE_STATUS_STATE_FILE.exists():
            return False
        import json
        with RAFFLE_STATUS_STATE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return isinstance(data, dict) and data.get("posted_date") == today.isoformat()
    except Exception:
        bot.logger.exception("Could not read raffle status state.")
        return False


def _save_raffle_status_posted(today, message_id):
    try:
        RAFFLE_STATUS_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        import json
        temp = RAFFLE_STATUS_STATE_FILE.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump({"posted_date": today.isoformat(), "message_id": int(message_id)}, handle)
        temp.replace(RAFFLE_STATUS_STATE_FILE)
    except Exception:
        bot.logger.exception("Could not save raffle status state.")


async def _daily_raffle_status_public(context):
    """Post the public 2 PM Arizona raffle status once per Arizona calendar day."""
    today = datetime.now(RAFFLE_STATUS_TZ).date()
    if _raffle_status_already_posted(today):
        bot.logger.info("Daily raffle status already posted | date=%s", today)
        return
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
        _save_raffle_status_posted(today, sent.message_id)
        bot.logger.info(
            "DAILY RAFFLE STATUS POSTED | raffle=%s | date=%s | chat=%s | topic=%s | message=%s",
            raffle["id"], today, -1002697105809, 11883, sent.message_id,
        )
    except Exception:
        bot.logger.exception(
            "Could not post daily raffle status | raffle=%s",
            raffle["id"],
        )



async def _daily_raffle_status_recovery(context):
    """Recover today's 2 PM raffle reminder after a restart/missed scheduler run."""
    now = datetime.now(RAFFLE_STATUS_TZ)
    scheduled = time(RAFFLE_STATUS_HOUR, RAFFLE_STATUS_MINUTE)
    if now.time().replace(tzinfo=None) < scheduled:
        bot.logger.info("Raffle status recovery not needed yet | now=%s", now)
        return
    today = now.date()
    if _raffle_status_already_posted(today):
        bot.logger.info("Raffle status recovery found today's post already recorded | date=%s", today)
        return
    bot.logger.warning("Raffle status missed before startup; posting recovery now | date=%s", today)
    await _daily_raffle_status_public(context)


def _build_application_with_verified_startup_hooks():
    application = _original_build_application()
    dirty_minds_admin_override.install_application(application)

    original_post_init = getattr(application, "_post_init", None)

    async def verified_startup(application_instance):
        if original_post_init:
            try:
                await original_post_init(application_instance)
            except Exception:
                bot.logger.exception(
                    "Original post_init failed; continuing with verified startup hooks."
                )

        try:
            job_queue = application_instance.job_queue
            if job_queue:
                for job in job_queue.get_jobs_by_name("daily-raffle-status"):
                    job.schedule_removal()
                job_queue.run_daily(
                    _daily_raffle_status_public,
                    time(hour=RAFFLE_STATUS_HOUR, minute=RAFFLE_STATUS_MINUTE, tzinfo=RAFFLE_STATUS_TZ),
                    name="daily-raffle-status",
                )
                # Recovery: if Render restarts after 2:00 PM, check shortly after startup
                # and post today's reminder if it was missed. Persistent state prevents duplicates.
                job_queue.run_once(
                    _daily_raffle_status_recovery,
                    when=10,
                    name="daily-raffle-status-recovery",
                )
                bot.logger.info(
                    "Daily raffle status scheduler VERIFIED | time=14:00 Arizona | chat=%s topic=%s | recovery=enabled",
                    -1002697105809, 11883,
                )
            else:
                bot.logger.error(
                    "Daily raffle status NOT scheduled: JobQueue unavailable."
                )
        except Exception:
            bot.logger.exception("Daily raffle status 2 PM scheduler setup failed.")

        try:
            grand_rising.start(application_instance)
        except Exception:
            bot.logger.exception("Grand Rising scheduler startup hook failed.")

        try:
            topic_routing.start_after_dark_scheduler(application_instance)
            jobs = application_instance.job_queue.get_jobs_by_name(
                "melanated-after-dark-message"
            ) if application_instance.job_queue else []
            if jobs:
                bot.logger.info(
                    "After Dark scheduler VERIFIED | jobs=%s | schedule=23:00 Arizona | chat=%s topic=%s",
                    len(jobs),
                    -1002697105809,
                    11999,
                )
            else:
                bot.logger.error(
                    "After Dark scheduler NOT VERIFIED | JobQueue job missing after startup."
                )
        except Exception:
            bot.logger.exception("After Dark scheduler startup hook failed.")

        try:
            job_queue = application_instance.job_queue
            if not job_queue:
                bot.logger.error(
                    "Games-topic pin maintenance NOT scheduled: JobQueue unavailable."
                )
            else:
                for job in job_queue.get_jobs_by_name("games-topic-pins-startup"):
                    job.schedule_removal()
                job_queue.run_once(
                    _run_games_topic_pin_maintenance,
                    when=5,
                    name="games-topic-pins-startup",
                )
                bot.logger.info(
                    "Games-topic pin maintenance scheduled | delay=5s | chat=%s topic=%s",
                    -1002697105809,
                    11999,
                )
        except Exception:
            bot.logger.exception("Games-topic pin maintenance scheduling FAILED.")

        try:
            await intro_persistence.recover_saved_introductions(application_instance)
        except Exception:
            bot.logger.exception("Verified intro recovery startup hook failed.")

        try:
            job_queue = application_instance.job_queue
            if not job_queue:
                bot.logger.error("Verified intro reminders NOT started: JobQueue unavailable.")
                return

            for job_name in (
                "monthly-intro-reminders",
                "monthly-intro-reminders-initial",
                intro_reminder_fix.JOB_NAME,
                intro_reminder_fix.INITIAL_JOB_NAME,
            ):
                for job in job_queue.get_jobs_by_name(job_name):
                    job.schedule_removal()

            job_queue.run_once(
                intro_reminder_fix.send_intro_reminders,
                when=15,
                name=intro_reminder_fix.INITIAL_JOB_NAME,
            )
            job_queue.run_repeating(
                intro_reminder_fix.send_intro_reminders,
                interval=60 * 60,
                first=60 * 60,
                name=intro_reminder_fix.JOB_NAME,
            )
            bot.logger.info(
                "Verified intro reminder startup hook enabled | initial=15s | sweep=hourly | per-member=30d"
            )
        except Exception:
            bot.logger.exception("Verified intro reminder startup hook failed.")

    application._post_init = verified_startup
    return application


bot.build_application = _build_application_with_verified_startup_hooks


if __name__ == "__main__":
    bot.main()
