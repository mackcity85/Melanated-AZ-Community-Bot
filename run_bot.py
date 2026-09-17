# Melanated AZ Bot launcher
# Install topic routing before any QOTD module is imported so its
# America/Phoenix topic/schedule configuration is loaded correctly.

import bot
import topic_routing
import media_router
import dirty_minds_admin_override

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
