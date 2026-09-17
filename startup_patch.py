"""Guaranteed startup integration for deployments that launch bot.py directly.

Render is currently starting `python bot.py`, so run_bot.py is not part of the
startup path. This module is imported from config.py, which bot.py imports
before it builds the Telegram Application. We patch ApplicationBuilder.build()
so startup work is attached to the actual Application instance regardless of
the Render start command.
"""

import logging

from telegram.ext import ApplicationBuilder

logger = logging.getLogger("melanated_az_startup_patch")

_ORIGINAL_BUILD = ApplicationBuilder.build
_MARKER = "_melanated_az_startup_patch_installed"


async def _run_games_topic_pin_maintenance(context):
    """Create/repair the three permanent Games-topic launcher pins."""
    try:
        from games.game_topic_pins import ensure_game_topic_pins

        logger.info(
            "Games-topic pin maintenance START | chat=%s topic=%s",
            -1002697105809,
            11999,
        )
        await ensure_game_topic_pins(context.bot)
        logger.info(
            "Games-topic pin maintenance COMPLETE | chat=%s topic=%s",
            -1002697105809,
            11999,
        )
    except Exception:
        logger.exception(
            "Games-topic pin maintenance FAILED | chat=%s topic=%s",
            -1002697105809,
            11999,
        )


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

            # Render launches bot.py directly, so schedule the Games launcher
            # maintenance here rather than relying on run_bot.py.
            try:
                if not app.job_queue:
                    logger.error(
                        "Games-topic pin maintenance NOT scheduled: JobQueue unavailable."
                    )
                else:
                    for job in app.job_queue.get_jobs_by_name("games-topic-pins-startup"):
                        job.schedule_removal()

                    app.job_queue.run_once(
                        _run_games_topic_pin_maintenance,
                        when=5,
                        name="games-topic-pins-startup",
                    )
                    logger.info(
                        "Games-topic pin maintenance scheduled | delay=5s | chat=%s topic=%s",
                        -1002697105809,
                        11999,
                    )
            except Exception:
                logger.exception("Games-topic pin maintenance scheduling FAILED.")

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

            # Social-media / Friends directory for topic 9513.
            # Handlers are installed during post_init so this works when Render
            # launches bot.py directly without requiring bot.py edits.
            try:
                from social_media import startup_social_media
                await startup_social_media(app)
                logger.info(
                    "Social media friends directory enabled | chat=%s topic=%s",
                    -1002697105809,
                    9513,
                )
            except Exception:
                logger.exception("Social media friends directory startup failed.")

        application.post_init = patched_post_init
        setattr(application, _MARKER, True)
        return application

    ApplicationBuilder.build = patched_build
    setattr(ApplicationBuilder, _MARKER, True)
    logger.info("Guaranteed startup patch installed for direct bot.py launches")


_install()
