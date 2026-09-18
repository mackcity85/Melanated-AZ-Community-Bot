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
        8809,
    )
    try:
        await ensure_game_topic_pins(context.bot)
        bot.logger.info(
            "Games-topic pin maintenance COMPLETE | chat=%s topic=%s",
            -1002697105809,
            8809,
        )
    except Exception:
        bot.logger.exception(
            "Games-topic pin maintenance FAILED | chat=%s topic=%s",
            -1002697105809,
            8809,
        )


RAFFLE_STATUS_TZ = ZoneInfo("America/Phoenix")
RAFFLE_STATUS_HOUR = 16
RAFFLE_STATUS_MINUTE = 30

async def _daily_raffle_status_public(context):
    """Run the single shared raffle-status formatter at 4:30 PM Arizona time."""
    today = datetime.now(RAFFLE_STATUS_TZ).date()
    await send_daily_raffle_status(context)
    # Mark success only after the shared sender returns without raising.
    state_file = Path("/var/data/daily_raffle_status.json")
    try:
        import json
        state_file.parent.mkdir(parents=True, exist_ok=True)
        temp = state_file.with_suffix(".tmp")
        temp.write_text(json.dumps({"posted_date": today.isoformat()}), encoding="utf-8")
        temp.replace(state_file)
    except Exception:
        bot.logger.exception("Could not save raffle status recovery state.")

async def _daily_raffle_status_recovery(context):
    """Recover a missed 4:30 PM raffle status without creating duplicates."""
    now = datetime.now(RAFFLE_STATUS_TZ)
    scheduled = time(RAFFLE_STATUS_HOUR, RAFFLE_STATUS_MINUTE)

    if now.time().replace(tzinfo=None) < scheduled:
        return

    # The shared raffle status function is intentionally lightweight; recovery
    # is only invoked once per five-minute interval after the scheduled time.
    # Do not duplicate the post if today's scheduled run already succeeded.
    state_file = Path("/var/data/daily_raffle_status.json")
    try:
        import json
        if state_file.exists():
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("posted_date") == now.date().isoformat():
                return
    except Exception:
        bot.logger.exception("Could not read raffle status recovery state.")

    bot.logger.warning(
        "Raffle status recovery detected a missing post | date=%s | now=%s",
        now.date(),
        now,
    )
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
                # Recovery runs continuously after 2 PM so a missed reminder is
                # recovered even when the bot never restarted. Persistent state
                # prevents duplicate posts on the same Arizona calendar day.
                for job in job_queue.get_jobs_by_name("daily-raffle-status-recovery"):
                    job.schedule_removal()
                job_queue.run_repeating(
                    _daily_raffle_status_recovery,
                    interval=300,
                    first=10,
                    name="daily-raffle-status-recovery",
                )
                bot.logger.info(
                    "Daily raffle status scheduler VERIFIED | time=16:30 Arizona | chat=%s topic=%s | recovery=enabled | recovery_interval=5m",
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
                    8809,
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
