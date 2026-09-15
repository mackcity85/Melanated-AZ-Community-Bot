import json
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from telegram.error import TelegramError

from games.game_center import GAMES_CHAT_ID, GAMES_TOPIC_ID
from raffle_database import get_active_raffle, get_approved_entries, close_raffle

logger = logging.getLogger("melanatedaz.raffle_pin_manager")

@@ -156,6 +157,90 @@ async def _refresh_games_launcher(context):
logger.exception("Could not refresh Games-topic launcher after raffle state change.")


async def _finish_expired_raffle(context, raffle):
    """Close an expired raffle, announce the winner, and clear its pinned post."""
    raffle_id = int(raffle["id"])
    chat_id = int(raffle.get("chat_id") or _main_group_id())
    message_id = int(raffle.get("message_id") or 0)
    state = _load_state()

    # Prevent duplicate processing if the monitor runs twice around expiry.
    if raffle.get("status") != "active":
        return

    entries = get_approved_entries(raffle_id)
    winner = random.choice(entries) if entries else None

    close_raffle(raffle_id)

    if winner:
        winner_user_id = int(winner.get("user_id"))
        winner_name = winner.get("display_name") or winner.get("username") or str(winner_user_id)
        winner_text = (
            "🎉 <b>RAFFLE WINNER!</b> 🎉\n\n"
            f"🎁 <b>Prize:</b> {html_escape(str(raffle.get('prize') or 'Raffle'))}\n"
            f"👑 <b>Winner:</b> {html_escape(str(winner_name))}\n\n"
            "Congratulations! 🔥🎊"
        )
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=GAMES_TOPIC_ID,
                text=winner_text,
                parse_mode="HTML",
            )
        except TelegramError:
            logger.exception("Could not post expired raffle winner announcement | raffle=%s", raffle_id)

        try:
            await context.bot.send_message(
                chat_id=winner_user_id,
                text=(
                    "🎉 <b>CONGRATULATIONS!</b> 🎉\n\n"
                    f"You won the Melanated AZ raffle!\n\n"
                    f"🎁 <b>Prize:</b> {html_escape(str(raffle.get('prize') or 'Raffle'))}\n\n"
                    "An administrator will contact you regarding your prize."
                ),
                parse_mode="HTML",
            )
        except TelegramError:
            logger.info("Could not privately notify raffle winner %s.", winner_user_id)
    else:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=GAMES_TOPIC_ID,
                text=(
                    "⚠️ <b>RAFFLE CLOSED</b>\n\n"
                    f"🎁 <b>Prize:</b> {html_escape(str(raffle.get('prize') or 'Raffle'))}\n\n"
                    "No approved entries were received."
                ),
                parse_mode="HTML",
            )
        except TelegramError:
            logger.exception("Could not post expired raffle closure notice | raffle=%s", raffle_id)

    if state and state.get("raffle_id") == raffle_id:
        await _remove_pinned_raffle(context, state)
    elif message_id:
        try:
            await context.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        except TelegramError:
            pass
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except TelegramError:
            pass

    logger.info("Expired raffle finalized | raffle=%s | winner=%s", raffle_id, winner_user_id if winner else None)


# HTML helper kept local so this manager does not depend on raffle.py internals.
def html_escape(value):
    import html
    return html.escape(str(value))


async def sync_raffle_pin(context):
    """Ensure the current active raffle is the only raffle post we track/pin."""
    await _remove_legacy_raffle_notification_pin(context)
    # Existing implementation continues below.
