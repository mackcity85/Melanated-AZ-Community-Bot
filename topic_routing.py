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
# After Dark:
#   Daily post time: 10:30 AM Arizona time
# ==========================================================

import os
from types import MethodType

TARGET_CHAT_ID = -1002697105809
TARGET_TOPIC_ID = 11999

# QOTD reads these values at import time.
os.environ["QUESTION_OF_DAY_CHAT_ID"] = str(TARGET_CHAT_ID)
os.environ["QUESTION_OF_DAY_TOPIC_ID"] = str(TARGET_TOPIC_ID)


def install_after_dark_topic_routing():
    """Route After Dark content to topic 11999 and schedule it for 10:30 AM."""
    import daily_messages

    daily_messages.DAILY_MESSAGE_HOUR = 10
    daily_messages.DAILY_MESSAGE_MINUTE = 30

    # The existing content bank contains several categories. For the
    # dedicated After Dark schedule, only prompts explicitly labeled
    # AFTER DARK / AFTER-DARK are selected.
    after_dark_messages = [
        item for item in daily_messages.DAILY_MESSAGES
        if "AFTER DARK" in item[0].upper() or "AFTER-DARK" in item[0].upper()
    ]

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


def install_all_topic_routing():
    """Install shared QOTD / After Dark routing."""
    install_after_dark_topic_routing()

    try:
        import notification_policy
        notification_policy.PERMANENT_TOPIC_IDS.add(TARGET_TOPIC_ID)
    except Exception:
        pass
