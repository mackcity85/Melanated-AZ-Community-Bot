import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from birthdays import check_birthdays

from pin_cleanup import cleanup_old_pins

from inactivity import check_inactive_members



scheduler = None



# ==========================
# COMMUNITY FEEDBACK
# ==========================

async def run_feedback_poll(app):

    logging.info(
        "60-day community feedback poll check executed"
    )

    # Future poll system will be added here



# ==========================
# START SCHEDULER
# ==========================

async def start_scheduler(app):

    global scheduler


    scheduler = AsyncIOScheduler()



    # --------------------------
    # Daily Birthday Check
    # --------------------------

    scheduler.add_job(

        check_birthdays,

        "cron",

        hour=9,

        minute=0,

        args=[app]

    )



    # --------------------------
    # Community Feedback
    # Every 60 Days
    # --------------------------

    scheduler.add_job(

        run_feedback_poll,

        "interval",

        days=60,

        args=[app]

    )



    # --------------------------
    # Pin Cleanup
    # Daily Check
    # --------------------------

    scheduler.add_job(

        cleanup_old_pins,

        "interval",

        days=1,

        args=[app]

    )



    # --------------------------
    # Inactivity Check
    # Every 30 Days
    # --------------------------

    scheduler.add_job(

        check_inactive_members,

        "interval",

        days=30,

        args=[app]

    )



    scheduler.start()



    logging.info(

        "✅ Scheduler started"

    )
