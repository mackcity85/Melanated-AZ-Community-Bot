"""Ensure every successful raffle publication immediately creates main-chat navigation."""

import logging

logger = logging.getLogger("melanatedaz.raffle_manual_nav_fix")


def install():
    try:
        import raffle
        from raffle_pin_manager import _publish_main_chat_navigation
    except Exception:
        logger.exception("Could not load raffle navigation dependencies.")
        return

    if getattr(raffle, "_manual_nav_fix_installed", False):
        return

    original_publish = raffle.publish_raffle

    async def publish_with_navigation(raffle_id, context):
        published = await original_publish(raffle_id, context)
        if not published:
            return False
        try:
            from raffle_database import get_raffle
            current = get_raffle(raffle_id)
            if current and int(current.get("message_id") or 0):
                await _publish_main_chat_navigation(context, current)
                logger.info(
                    "Manual raffle publication navigation ensured | raffle=%s | message=%s",
                    raffle_id,
                    current.get("message_id"),
                )
        except Exception:
            logger.exception(
                "Raffle %s published but main-chat navigation failed.", raffle_id
            )
        return True

    raffle.publish_raffle = publish_with_navigation
    raffle._manual_nav_fix_installed = True
    logger.info("Manual raffle navigation fix installed.")
