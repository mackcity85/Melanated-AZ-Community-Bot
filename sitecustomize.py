# ==========================================================
# Melanated AZ - Python startup reliability hooks
# ==========================================================
# Python imports sitecustomize automatically when it is present
# on the application path. This hook makes the existing daily
# community scheduler resilient to Render restarts without
# changing the large daily_messages.py question bank.
# ==========================================================

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger("melanatedaz.sitecustomize")

try:
    from telegram.ext import JobQueue

    _original_run_daily = JobQueue.run_daily
    _PATCHED = False

    def _reliable_run_daily(self, callback, time, days=(0, 1, 2, 3, 4, 5, 6),
                            data=None, name=None, chat_id=None, user_id=None,
                            job_kwargs=None):
        if name != "melanated-daily-community-message":
            return _original_run_daily(
                self, callback, time, days=days, data=data, name=name,
                chat_id=chat_id, user_id=user_id, job_kwargs=job_kwargs,
            )

        # Import only when the daily job is being registered, avoiding a
        # circular import during application startup.
        from daily_message_scheduler import (
            send_daily_community_message_reliable,
            _startup_recovery,
        )

        logger.info("Intercepting daily community scheduler with reliable wrapper.")

        # Remove any prior copies of the two reliability jobs.
        for job_name in (
            "melanated-daily-community-message",
            "melanated-daily-community-message-recovery",
        ):
            for job in self.get_jobs_by_name(job_name):
                job.schedule_removal()

        # Preserve the configured daily time, while using the reliable
        # callback that records successful posts persistently.
        job = _original_run_daily(
            self,
            send_daily_community_message_reliable,
            time,
            days=days,
            data=data,
            name=name,
            chat_id=chat_id,
            user_id=user_id,
            job_kwargs=job_kwargs,
        )

        # A short startup check catches a missed 10 AM post when Render
        # starts/restarts after the scheduled time.
        self.run_once(
            _startup_recovery,
            when=8,
            name="melanated-daily-community-message-recovery",
        )
        return job

    if not getattr(JobQueue.run_daily, "_melanated_reliable_patch", False):
        _reliable_run_daily._melanated_reliable_patch = True
        JobQueue.run_daily = _reliable_run_daily
        _PATCHED = True
        logger.info("Daily community scheduler reliability hook installed.")

except Exception:
    # Never prevent the bot from starting if the optional reliability hook
    # cannot be installed. The original scheduler remains available.
    logger.exception("Could not install daily scheduler reliability hook.")
