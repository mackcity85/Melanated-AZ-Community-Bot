# ==========================================================
# Melanated AZ Bot - Shared Question Topic Routing
# topic_routing.py
#
# Forces QOTD and After Dark daily content into the same forum
# topic without changing their separate content banks.
#
# Destination:
#   Chat  : -1002697105809
#   Topic : 11999
#
# Schedule:
#   Question of the Day: 11:00 AM Arizona time
#   Daily Community Message: 10:00 AM Arizona time
#   After Dark: 10:00 PM Arizona time
# ==========================================================

import os

from types import MethodType

TARGET_CHAT_ID = -1002697105809
TARGET_TOPIC_ID = 11999

# QOTD reads these values at import time.
os.environ["QUESTION_OF_DAY_CHAT_ID"] = str(TARGET_CHAT_ID)
os.environ["QUESTION_OF_DAY_TOPIC_ID"] = str(TARGET_TOPIC_ID)
os.environ["QUESTION_OF_DAY_HOUR"] = "11"
os.environ["QUESTION_OF_DAY_MINUTE"] = "0"

# Daily Community Messages use their own daytime schedule.
# Do NOT override DAILY_MESSAGE_HOUR here for After Dark.
os.environ["DAILY_MESSAGE_HOUR"] = "10"
os.environ["DAILY_MESSAGE_MINUTE"] = "0"


def install_after_dark_topic_routing():
    """Route the daily community message bank to topic 11999.

    The shared daily_messages scheduler remains at 10:00 AM Arizona.
    After Dark content is selected from the same bank, but this routing
    layer must not change the scheduler's time to 10:00 PM.
    """
    import daily_messages

    # Keep the daytime Daily Community Message schedule independent.
    # The old implementation forced this to 22:00, which incorrectly
    # moved the entire daily_messages scheduler to 10 PM.
    daily_messages.DAILY_MESSAGE_HOUR = 10
    daily_messages.DAILY_MESSAGE_MINUTE = 0

    # The existing content bank contains several categories. For the
    # dedicated After Dark routing, only prompts explicitly labeled
    # AFTER DARK / AFTER-DARK are selected.
    after_dark_messages = [
        item for item in daily_messages.DAILY_MESSAGES
        if isinstance(item, (tuple, list))
        and len(item) >= 1
        and isinstance(item[0], str)
        and ("AFTER DARK" in item[0].upper() or "AFTER-DARK" in item[0].upper())
    ]

    # Only replace the active bank when matching prompts were found.
    # If the bank is empty or temporarily malformed, leave the original
    # bank untouched instead of replacing it with an empty list.
    if after_dark_messages:
        daily_messages.DAILY_MESSAGES = after_dark_messages

    if getattr(daily_messages, "_after_dark_topic_routing_installed", False):
        return

    original = daily_messages.send_daily_community_message

    async def routed_daily_message(context):
        bot = context.bot
        original_send = bot.send_message

        async def routed_send(self, *args, **kwargs):
            kwargs["chat_id"] = TARGET_CHAT_ID
            kwargs["message_thread_id"] = TARGET_TOPIC_ID
            return await original_send(*args, **kwargs)

        bot.send_message = MethodType(routed_send, bot)
        try:
            return await original(context)
        finally:
            bot.send_message = original_send

    daily_messages.send_daily_community_message = routed_daily_message
    daily_messages._after_dark_topic_routing_installed = True


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
                # Startup must continue even if Telegram temporarily rejects
                # the panel operation. The next bot restart can retry it.
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
    """Install shared QOTD / After Dark routing."""
    install_after_dark_topic_routing()
    install_qotd_startup_panel()

    try:
        import notification_policy
        notification_policy.PERMANENT_TOPIC_IDS.add(TARGET_TOPIC_ID)
    except Exception:
        pass
