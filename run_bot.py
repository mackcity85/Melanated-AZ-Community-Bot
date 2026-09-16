# Melanated AZ Bot launcher
# Install topic routing before any QOTD module is imported so its
# America/Phoenix topic/schedule configuration is loaded correctly.

import bot
import topic_routing

topic_routing.install_all_topic_routing()

import runtime_fixes  # noqa: F401
import qotd_td_user  # noqa: F401
import admin_truth_dare_qotd  # noqa: F401
import intro_persistence  # noqa: F401
import intro_reminder_fix  # noqa: F401
import raffle_manual_nav_fix

raffle_manual_nav_fix.install()


# PTB's ApplicationBuilder stores the post_init callback on the Application
# object when build_application() runs. The earlier monkey-patches changed
# bot.post_init, but the Render logs proved that the running Application was
# still using the original startup callback. Wrap the actual Application
# callback after the application is built so these fixes are guaranteed to
# execute before polling starts.
_original_build_application = bot.build_application


def _build_application_with_verified_startup_hooks():
    application = _original_build_application()
    original_post_init = getattr(application, "post_init", None)

    async def verified_startup(application_instance):
        if original_post_init:
            await original_post_init(application_instance)

        # Run the saved-introduction recovery directly. This does not delete,
        # clean, migrate, or overwrite existing topic content.
        try:
            await intro_persistence.recover_saved_introductions(application_instance)
        except Exception:
            bot.logger.exception("Verified intro recovery startup hook failed.")

        # Replace any legacy/fixed reminder jobs with exactly one reliable
        # hourly sweep. Each member is still limited to one successful DM per
        # 30 days by monthly_intro_reminder_at.
        try:
            if application_instance.job_queue:
                for job_name in (
                    "monthly-intro-reminders",
                    "monthly-intro-reminders-initial",
                    intro_reminder_fix.JOB_NAME,
                    intro_reminder_fix.INITIAL_JOB_NAME,
                ):
                    for job in application_instance.job_queue.get_jobs_by_name(job_name):
                        job.schedule_removal()

                application_instance.job_queue.run_once(
                    intro_reminder_fix.send_intro_reminders,
                    when=15,
                    name=intro_reminder_fix.INITIAL_JOB_NAME,
                )
                application_instance.job_queue.run_repeating(
                    intro_reminder_fix.send_intro_reminders,
                    interval=60 * 60,
                    first=60 * 60,
                    name=intro_reminder_fix.JOB_NAME,
                )
                bot.logger.info(
                    "Verified intro reminder startup hook enabled | initial=15s | sweep=hourly | per-member=30d"
                )
            else:
                bot.logger.error("Verified intro reminders NOT started: JobQueue unavailable.")
        except Exception:
            bot.logger.exception("Verified intro reminder startup hook failed.")

    application.post_init = verified_startup
    return application


bot.build_application = _build_application_with_verified_startup_hooks


if __name__ == "__main__":
    bot.main()
