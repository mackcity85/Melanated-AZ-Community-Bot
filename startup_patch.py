"""Guaranteed startup integration for deployments that launch bot.py directly.

Render is currently starting `python bot.py`, so run_bot.py is not part of the
startup path. This module is imported from config.py, which bot.py imports
before it builds the Telegram Application. We patch ApplicationBuilder.build()
so the intro recovery/reminder startup work is attached to the actual
Application instance regardless of the Render start command.
"""

import logging

from telegram.ext import ApplicationBuilder

logger = logging.getLogger("melanated_az_startup_patch")

_ORIGINAL_BUILD = ApplicationBuilder.build
_MARKER = "_melanated_az_startup_patch_installed"


def _install():
    if getattr(ApplicationBuilder, _MARKER, False):
        return

    def patched_build(self, *args, **kwargs):
        application = _ORIGINAL_BUILD(self, *args, **kwargs)

        if getattr(application, _MARKER, False):
            return application

        original_post_init = getattr(application, "post_init", None)

        async def patched_post_init(app):
            if original_post_init:
                await original_post_init(app)

            try:
                import intro_persistence
                await intro_persistence.recover_saved_introductions(app)
            except Exception:
                logger.exception("Guaranteed intro recovery startup failed.")

            try:
                import intro_reminder_fix

                cancelled = intro_reminder_fix._cancel_old_jobs(app)
                if not app.job_queue:
                    logger.error("Guaranteed intro reminders NOT started: JobQueue unavailable.")
                else:
                    # Remove any duplicate fixed jobs before scheduling.
                    for job_name in (
                        intro_reminder_fix.JOB_NAME,
                        intro_reminder_fix.INITIAL_JOB_NAME,
                    ):
                        for job in app.job_queue.get_jobs_by_name(job_name):
                            job.schedule_removal()

                    app.job_queue.run_once(
                        intro_reminder_fix.send_intro_reminders,
                        when=15,
                        name=intro_reminder_fix.INITIAL_JOB_NAME,
                    )
                    app.job_queue.run_repeating(
                        intro_reminder_fix.send_intro_reminders,
                        interval=60 * 60,
                        first=60 * 60,
                        name=intro_reminder_fix.JOB_NAME,
                    )
                    logger.info(
                        "GUARANTEED intro startup enabled | cancelled_old_jobs=%s | recovery=on | initial=15s | sweep=hourly | per-member=30d",
                        cancelled,
                    )
            except Exception:
                logger.exception("Guaranteed intro reminder startup failed.")

        application.post_init = patched_post_init
        setattr(application, _MARKER, True)
        return application

    ApplicationBuilder.build = patched_build
    setattr(ApplicationBuilder, _MARKER, True)
    logger.info("Guaranteed startup patch installed for direct bot.py launches")


_install()
