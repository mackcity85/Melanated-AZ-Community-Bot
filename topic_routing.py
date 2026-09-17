# ==========================================================
# Melanated AZ Bot - Shared Question Topic Routing
# ==========================================================

import os
from datetime import time
from types import MethodType

TARGET_CHAT_ID = -1002697105809
TARGET_TOPIC_ID = 11999

# QOTD configuration.
os.environ["QUESTION_OF_DAY_CHAT_ID"] = str(TARGET_CHAT_ID)
os.environ["QUESTION_OF_DAY_TOPIC_ID"] = str(TARGET_TOPIC_ID)
os.environ["QUESTION_OF_DAY_HOUR"] = "11"
os.environ["QUESTION_OF_DAY_MINUTE"] = "0"

# Daily Community remains independent at 10 AM.
os.environ["DAILY_MESSAGE_HOUR"] = "10"
os.environ["DAILY_MESSAGE_MINUTE"] = "0"


def install_after_dark_topic_routing():
    """Route Daily Community and After Dark independently."""
    import daily_messages

    if getattr(daily_messages, "_after_dark_topic_routing_installed", False):
        return

    original = daily_messages.send_daily_community_message
    full_daily_bank = list(daily_messages.DAILY_MESSAGES)

    after_dark_messages = [
        item for item in full_daily_bank
        if isinstance(item, (tuple, list))
        and len(item) >= 1
        and isinstance(item[0], str)
        and (
            "AFTER DARK" in item[0].upper()
            or "AFTER-DARK" in item[0].upper()
        )
    ]

    if not after_dark_messages:
        return

    async def routed_send_message(context, message_bank):
        bot = context.bot
        original_send = bot.send_message
        original_bank = daily_messages.DAILY_MESSAGES

        async def routed_send(self, *args, **kwargs):
            kwargs["chat_id"] = TARGET_CHAT_ID
            kwargs["message_thread_id"] = TARGET_TOPIC_ID
            return await original_send(*args, **kwargs)

        bot.send_message = MethodType(routed_send, bot)
        daily_messages.DAILY_MESSAGES = message_bank
        try:
            return await original(context)
        finally:
            daily_messages.DAILY_MESSAGES = original_bank
            bot.send_message = original_send

    async def routed_daily_message(context):
        return await routed_send_message(context, full_daily_bank)

    async def routed_after_dark_message(context):
        return await routed_send_message(context, after_dark_messages)

    daily_messages.send_daily_community_message = routed_daily_message
    daily_messages.DAILY_MESSAGE_HOUR = 10
    daily_messages.DAILY_MESSAGE_MINUTE = 0

    daily_messages._after_dark_message_handler = routed_after_dark_message
    daily_messages._after_dark_topic_routing_installed = True


def start_after_dark_scheduler(application):
    """Start the independent 11 PM Arizona After Dark scheduler."""
    import daily_messages

    if not getattr(application, "job_queue", None):
        return

    handler = getattr(daily_messages, "_after_dark_message_handler", None)
    if handler is None:
        return

    for job in application.job_queue.get_jobs_by_name("melanated-after-dark-message"):
        job.schedule_removal()

    application.job_queue.run_daily(
        handler,
        time(hour=23, minute=0, tzinfo=daily_messages.ARIZONA_TZ),
        name="melanated-after-dark-message",
    )

    import logging
    logging.getLogger("topic_routing").info(
        "After Dark scheduled | 23:00 Arizona | topic=%s",
        TARGET_TOPIC_ID,
    )


def install_qotd_startup_panel():
    """Wrap the QOTD scheduler so the permanent member panel is checked at startup."""
    import question_of_day

    if getattr(question_of_day, "_qotd_startup_panel_wrapped", False):
        return

    original_scheduler = question_of_day.start_question_of_day_scheduler

    def wrapped_scheduler(application):
        original_scheduler(application)

        if not application.job_queue or not question_of_day.qotd_enabled():
            return

        async def ensure_panel_job(context):
            try:
                await question_of_day.ensure_qotd_submission_panel(context.application)
            except Exception:
                import logging
                logging.getLogger("topic_routing").exception(
                    "QOTD submission panel startup check failed."
                )

        application.job_queue.run_once(
            ensure_panel_job,
            when=1,
            name="qotd_submission_panel_startup",
        )

    question_of_day.start_question_of_day_scheduler = wrapped_scheduler
    question_of_day._qotd_startup_panel_wrapped = True


def install_all_topic_routing():
    """Install shared QOTD / Daily Community / After Dark routing."""
    install_after_dark_topic_routing()
    install_qotd_startup_panel()

    try:
        import notification_policy
        notification_policy.PERMANENT_TOPIC_IDS.add(TARGET_TOPIC_ID)
    except Exception:
        pass
