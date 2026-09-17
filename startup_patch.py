"""Guaranteed startup integration for deployments that launch bot.py directly."""

import logging

from telegram.ext import ApplicationBuilder

logger = logging.getLogger("melanated_az_startup_patch")

_ORIGINAL_BUILD = ApplicationBuilder.build
_MARKER = "_melanated_az_startup_patch_installed"


async def _run_games_topic_pin_maintenance(context):
    """Create/repair the three permanent Games-topic launcher pins once at startup."""
    try:
        from games.game_topic_pins import ensure_game_topic_pins
        await ensure_game_topic_pins(context.bot)
        logger.info("Games-topic pin maintenance COMPLETE | chat=%s topic=%s", -1002697105809, 8809)
    except Exception:
        logger.exception("Games-topic pin maintenance FAILED | chat=%s topic=%s", -1002697105809, 8809)


async def _run_social_media_panel_maintenance(context):
    """Keep the single Social Media/Friends add panel available in topic 9513."""
    try:
        from social_media import send_social_panel
        message_id = await send_social_panel(context.bot)
        logger.info("Social Media panel maintenance COMPLETE | chat=%s topic=%s message=%s", -1002697105809, 9513, message_id)
    except Exception:
        logger.exception("Social Media panel maintenance FAILED | chat=%s topic=%s", -1002697105809, 9513)


async def _run_social_media_recovery(context):
    """Recover saved member social profiles only when their stored post is missing."""
    try:
        from social_media_recovery import recover_social_profiles
        recovered = await recover_social_profiles(context.bot)
        logger.info("Social Media profile recovery COMPLETE | recovered=%s | chat=%s topic=%s", recovered, -1002697105809, 9513)
    except Exception:
        logger.exception("Social Media profile recovery FAILED | chat=%s topic=%s", -1002697105809, 9513)


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

            # Install safe social profile publishing/recovery before the
            # scheduled recovery job runs. It never duplicates a profile on
            # transient API/network/permission failures.
            try:
                import social_media_recovery_patch  # noqa: F401
                logger.info("Safe Social Media profile recovery enabled")
            except Exception:
                logger.exception("Safe Social Media recovery patch failed")

            # Install admin-only manual social repost controls.
            try:
                import social_admin_patch  # noqa: F401
                logger.info("Social admin manual-repost controls enabled")
            except Exception:
                logger.exception("Social admin manual-repost patch failed")

            try:
                if app.job_queue:
                    for job in app.job_queue.get_jobs_by_name("games-topic-pins-startup"):
                        job.schedule_removal()
                    app.job_queue.run_once(_run_games_topic_pin_maintenance, when=5, name="games-topic-pins-startup")
                    logger.info("Games-topic pin maintenance scheduled ONCE | delay=5s | chat=%s topic=%s", -1002697105809, 8809)
                else:
                    logger.error("Games-topic pin maintenance NOT scheduled: JobQueue unavailable.")
            except Exception:
                logger.exception("Games-topic pin maintenance scheduling FAILED.")

            try:
                from social_media import startup_social_media
                await startup_social_media(app)
                if app.job_queue:
                    for job in app.job_queue.get_jobs_by_name("social-media-panel-maintenance"):
                        job.schedule_removal()
                    app.job_queue.run_repeating(
                        _run_social_media_panel_maintenance,
                        interval=300,
                        first=60,
                        name="social-media-panel-maintenance",
                    )
                    logger.info("Social Media panel maintenance scheduled | every=300s | chat=%s topic=%s", -1002697105809, 9513)
                else:
                    logger.error("Social Media panel maintenance NOT scheduled: JobQueue unavailable.")
                logger.info("Social media friends directory enabled | chat=%s topic=%s", -1002697105809, 9513)
            except Exception:
                logger.exception("Social media friends directory startup failed.")

            # Recover saved member profiles automatically. The safe publisher
            # only creates a new post when Telegram explicitly reports that
            # the stored profile message is gone.
            try:
                if app.job_queue:
                    for job_name in ("social-media-profile-recovery", "social-media-profile-recovery-startup"):
                        for job in app.job_queue.get_jobs_by_name(job_name):
                            job.schedule_removal()
                    app.job_queue.run_once(
                        _run_social_media_recovery,
                        when=10,
                        name="social-media-profile-recovery-startup",
                    )
                    app.job_queue.run_repeating(
                        _run_social_media_recovery,
                        interval=600,
                        first=600,
                        name="social-media-profile-recovery",
                    )
                    logger.info("Social Media profile recovery scheduled | startup=10s | every=600s | chat=%s topic=%s", -1002697105809, 9513)
                else:
                    logger.error("Social Media profile recovery NOT scheduled: JobQueue unavailable.")
            except Exception:
                logger.exception("Social Media profile recovery scheduling FAILED.")

            try:
                import intro_persistence
                await intro_persistence.recover_saved_introductions(app)
            except Exception:
                logger.exception("Guaranteed intro recovery startup failed.")

            try:
                import intro_reminder_fix
                cancelled = intro_reminder_fix._cancel_old_jobs(app)
                if app.job_queue:
                    for job_name in (intro_reminder_fix.JOB_NAME, intro_reminder_fix.INITIAL_JOB_NAME):
                        for job in app.job_queue.get_jobs_by_name(job_name):
                            job.schedule_removal()
                    app.job_queue.run_once(intro_reminder_fix.send_intro_reminders, when=15, name=intro_reminder_fix.INITIAL_JOB_NAME)
                    app.job_queue.run_repeating(intro_reminder_fix.send_intro_reminders, interval=60 * 60, first=60 * 60, name=intro_reminder_fix.JOB_NAME)
                    logger.info("GUARANTEED intro startup enabled | cancelled_old_jobs=%s | recovery=on | initial=15s | sweep=hourly | per-member=30d", cancelled)
                else:
                    logger.error("Guaranteed intro reminders NOT started: JobQueue unavailable.")
            except Exception:
                logger.exception("Guaranteed intro reminder startup failed.")

            try:
                from social_profile_sync import sync_social_profiles
                sync_social_profiles()
            except Exception:
                logger.exception("Social member profile sync startup failed.")

        application.post_init = patched_post_init
        setattr(application, _MARKER, True)
        return application

    ApplicationBuilder.build = patched_build
    setattr(ApplicationBuilder, _MARKER, True)
    logger.info("Guaranteed startup patch installed for direct bot.py launches")


_install()
