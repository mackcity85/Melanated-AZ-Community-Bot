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
# ==========================================================

import os
from types import MethodType

TARGET_CHAT_ID = -1002697105809
TARGET_TOPIC_ID = 11999

# Make the QOTD module deterministic even if Render environment values
# are missing or stale. question_of_day.py reads these at import time.
os.environ["QUESTION_OF_DAY_CHAT_ID"] = str(TARGET_CHAT_ID)
os.environ["QUESTION_OF_DAY_TOPIC_ID"] = str(TARGET_TOPIC_ID)


def install_after_dark_topic_routing():
    """Route the existing After Dark daily-message publisher to topic 11999."""
    import daily_messages

    if getattr(daily_messages, "_after_dark_topic_routing_installed", False):
        return

    original = daily_messages.send_daily_community_message

    async def routed_daily_message(context):
        bot = context.bot
        original_send = bot.send_message

        async def routed_send(self, *args, **kwargs):
            # The daily_messages module has a dedicated After Dark content bank.
            # Only its destination is being changed here.
            kwargs["chat_id"] = TARGET_CHAT_ID
            kwargs["message_thread_id"] = TARGET_TOPIC_ID
            return await original_send(*args, **kwargs)

        # Patch only for the duration of this one scheduled publisher call.
        bot.send_message = MethodType(routed_send, bot)
        try:
            return await original(context)
        finally:
            bot.send_message = original_send

    daily_messages.send_daily_community_message = routed_daily_message
    daily_messages._after_dark_topic_routing_installed = True


def install_all_topic_routing():
    """Install all routing required for the shared QOTD/After Dark topic."""
    install_after_dark_topic_routing()

    # QOTD and After Dark posts are permanent community content. Prevent the
    # notification cleanup policy from treating topic 11999 as a temporary
    # bot-notification topic.
    try:
        import notification_policy
        notification_policy.PERMANENT_TOPIC_IDS.add(TARGET_TOPIC_ID)
    except Exception:
        pass
