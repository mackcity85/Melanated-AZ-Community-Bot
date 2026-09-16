# Melanated AZ Bot launcher
# Install topic routing before any QOTD module is imported so its
# America/Phoenix topic/schedule configuration is loaded correctly.

import bot
import topic_routing

topic_routing.install_all_topic_routing()

import runtime_fixes  # noqa: F401
import qotd_td_user  # noqa: F401
import admin_truth_dare_qotd  # noqa: F401
import intro_persistence
import intro_reminder_fix
import raffle_manual_nav_fix

raffle_manual_nav_fix.install()


# PTB stores ApplicationBuilder.post_init() on the Application as the
# internal _post_init callback. Assigning application.post_init does not
# replace the callback used by run_polling(), so the previous startup wrapper
# never executed. Wrap the actual callback before polling starts.
_original_build_application = bot.build_application


def _build_application_with_verified_startup_hooks():
    application = _original_build_application()
    original_post_init = getattr(application, "_post_init", None)

    async def verified_startup(application_instance):
        if original_post_init:
            await original_post_init(application_instance)

        # Recover every real saved introduction that still exists in the
        # community DB. This only adds missing/current intro posts; it never
        # deletes, cleans, migrates, or overwrites existing topic content.
        try:
            await intro_persistence.recover_saved_introductions(application_instance)
        except Exception:
            bot.logger.exception("Verified intro recovery startup hook failed.")

        # The original bot startup schedules legacy reminder jobs. Remove
        # those and install one reliable fixed scheduler. Delivery remains
        # limited to one successful reminder per member every 30 days.
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
