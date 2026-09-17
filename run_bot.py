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
from raffle import send_daily_raffle_status


topic_routing.install_all_topic_routing()
@@ -127,6 +130,35 @@
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
                    send_daily_raffle_status,
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
