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
    post_raffle_status_to_main_chat,
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


RAFFLE_MAIN_REPOST_HOUR = 18
RAFFLE_MAIN_REPOST_MINUTE = 10
RAFFLE_STATUS_TZ = ZoneInfo("America/Phoenix")

async def _raffle_main_chat_repost_checker(context):
    """Check every 30 seconds and post once at the configured Arizona time."""
    now = datetime.now(RAFFLE_STATUS_TZ)
    if now.hour != RAFFLE_MAIN_REPOST_HOUR or now.minute != RAFFLE_MAIN_REPOST_MINUTE:
        return

    last_post_date = context.application.bot_data.get("raffle_main_repost_date")
    if last_post_date == now.date().isoformat():
        return

    bot.logger.info(
        "Raffle main-chat repost trigger matched | local_time=%s | configured=%02d:%02d Arizona | chat=%s",
        now.strftime("%Y-%m-%d %H:%M:%S"),
        RAFFLE_MAIN_REPOST_HOUR,
        RAFFLE_MAIN_REPOST_MINUTE,
        -1002697105809,
    )

    posted = await post_raffle_status_to_main_chat(context)
    if posted:
        context.application.bot_data["raffle_main_repost_date"] = now.date().isoformat()
        bot.logger.info(
            "Scheduled raffle main-chat repost COMPLETE | time=%02d:%02d Arizona | chat=%s",
            RAFFLE_MAIN_REPOST_HOUR,
            RAFFLE_MAIN_REPOST_MINUTE,
            -1002697105809,
        )
    else:
        bot.logger.warning(
            "Scheduled raffle main-chat repost did not post | time=%02d:%02d Arizona | reason=no active raffle or send failure",
            RAFFLE_MAIN_REPOST_HOUR,
            RAFFLE_MAIN_REPOST_MINUTE,
        )


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
                for job in job_queue.get_jobs_by_name("raffle-main-chat-repost-checker"):
                    job.schedule_removal()
                job_queue.run_repeating(
                    _raffle_main_chat_repost_checker,
                    interval=30,
                    first=5,
                    name="raffle-main-chat-repost-checker",
                )
                bot.logger.info(
                    "Raffle scheduler VERIFIED | checker=every 30s | target=%02d:%02d Arizona | chat=%s",
                    RAFFLE_MAIN_REPOST_HOUR,
                    RAFFLE_MAIN_REPOST_MINUTE,
                    -1002697105809,
                )
            else:
                bot.logger.error(
                    "Daily raffle status NOT scheduled: JobQueue unavailable."
                )
        except Exception:
            bot.logger.exception("Raffle scheduler setup failed.")

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
