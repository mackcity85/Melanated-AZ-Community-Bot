# Melanated AZ Bot launcher
# Install topic routing before any QOTD module is imported so its
# America/Phoenix topic/schedule configuration is loaded correctly.

import bot
import topic_routing
import media_router
import dirty_minds_admin_override
import grand_rising
from datetime import time
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from raffle import (
    get_active_raffle,
    get_pending_entries,
    is_free_raffle,
    format_expiration,
)


topic_routing.install_all_topic_routing()
media_router.install(bot)

import runtime_fixes  # noqa: F401
import qotd_td_user  # noqa: F401
import admin_truth_dare_qotd  # noqa: F401
import intro_persistence
import intro_reminder_fix
import raffle_manual_nav_fix
from games.game_topic_pins import ensure_game_topic_pins

raffle_manual_nav_fix.install()


# ==========================================================
# ADMIN PANEL — CENTRAL CALLBACK ROUTER REPAIR
# ==========================================================
# bot.py historically performed an authorization check BEFORE calling
# admin_button(). That made every admin_* callback silently disappear when
# the preliminary live ADMIN_GROUP_ID check failed, even though admin.py has
# its own centralized authorization/error handling. Patch the router here so
# every admin callback reaches the authoritative admin dispatcher.
#
# This intentionally patches the function before build_application() creates
# the CallbackQueryHandler, so the running application uses this router for
# the entire admin panel, including dynamic callbacks.
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
        # Call admin_button directly. It owns the authoritative admin gate,
        # and this avoids the old router's silent pre-authentication drop.
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


# PTB stores ApplicationBuilder.post_init() on the Application as the
# internal _post_init callback. Assigning application.post_init does not
# replace the callback used by run_polling(), so the startup wrapper below
# replaces the actual _post_init callback.
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
    """Post the public 5 PM raffle status without exposing approved-entry count."""
    raffle = get_active_raffle()
    if not raffle:
        bot.logger.info("Daily raffle status skipped: no active raffle.")
        return

    free = is_free_raffle(raffle.get("price"))
    pending = get_pending_entries(raffle["id"])
    rows = [[InlineKeyboardButton("🎟️ ENTER RAFFLE", callback_data=f"enter_{raffle['id']}")]]
    if not free:
        rows.extend([
            [InlineKeyboardButton("💵 PAY WITH CASH APP", callback_data=f"pay_cashapp_{raffle['id']}")],
            [InlineKeyboardButton("🏦 PAY WITH ZELLE", callback_data=f"pay_zelle_{raffle['id']}")],
        ])

    text = (
        "🎟️ <b>RAFFLE STATUS</b>\n\n"
        f"🎁 <b>Prize:</b> {str(raffle.get('prize') or 'Unknown')}\n"
        f"💵 <b>Entry:</b> {str(raffle.get('price') or 'Unknown')}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle.get('expires_at'))}\n\n"
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


def _build_application_with_verified_startup_hooks():
    application = _original_build_application()

    # Dirty Minds approval/start override runs in handler group -1 so admins
    # can start an approved room even when the host never presses START.
    dirty_minds_admin_override.install_application(application)

    original_post_init = getattr(application, "_post_init", None)

    async def verified_startup(application_instance):
        # A Telegram/API failure in the original post_init must not prevent
        # the independent schedulers from being installed. Keep the original
        # startup work best-effort, then always continue into scheduler setup.
        if original_post_init:
            try:
                await original_post_init(application_instance)
            except Exception:
                bot.logger.exception(
                    "Original post_init failed; continuing with verified startup hooks."
                )

        # ==========================================================
        # DAILY RAFFLE STATUS — 5:00 PM ARIZONA
        # ==========================================================
        # The existing raffle scheduler is intentionally overridden here so
        # the public status/repost runs once every day at 5 PM Arizona time.
        # Remove any previously registered daily-raffle-status jobs first to
        # prevent the old noon schedule from producing a duplicate post.
        try:
            job_queue = application_instance.job_queue
            if job_queue:
                for job in job_queue.get_jobs_by_name("daily-raffle-status"):
                    job.schedule_removal()
                job_queue.run_daily(
                    _daily_raffle_status_public,
                    time(hour=17, minute=0, tzinfo=ZoneInfo("America/Phoenix")),
                    name="daily-raffle-status",
                )
                bot.logger.info(
                    "Daily raffle status scheduler VERIFIED | time=17:00 Arizona | chat=%s topic=%s",
                    -1002697105809,
                    11883,
                )
            else:
                bot.logger.error(
                    "Daily raffle status NOT scheduled: JobQueue unavailable."
                )
        except Exception:
            bot.logger.exception("Daily raffle status 5 PM scheduler setup failed.")

        # Grand Rising is a separate 6 AM Arizona weekday-themed greeting.
        # It is independent from the 10 AM Daily Community question and the
        # 11 PM After Dark schedule.
        try:
            grand_rising.start(application_instance)
        except Exception:
            bot.logger.exception("Grand Rising scheduler startup hook failed.")

        # After Dark is an independent 11 PM Arizona job. Install it even if
        # another startup task above failed, and log the resulting JobQueue job
        # so Render startup logs prove that it is actually registered.
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

        # Schedule Games-topic maintenance through the JobQueue instead of
        # doing Telegram API work inline during post_init. This guarantees the
        # task runs after PTB's scheduler is fully started and gives us an
        # explicit startup log if anything fails.
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

    # IMPORTANT: run_polling() executes Application._post_init. Replace that
    # callback directly instead of assigning the read-only post_init property.
    application._post_init = verified_startup
    return application


bot.build_application = _build_application_with_verified_startup_hooks


if __name__ == "__main__":
    bot.main()
