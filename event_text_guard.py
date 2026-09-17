# ==========================================================
# Melanated AZ Bot - Event Topic Text Guard
# ==========================================================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, ContextTypes, MessageHandler, filters

import event_router
import event_private_flow

EVENT_CHAT_ID = event_router.EVENT_CHAT_ID
EVENT_TOPIC_ID = event_router.EVENT_TOPIC_ID


async def handle_event_topic_text(update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user or user.is_bot:
        return
    if message.chat_id != EVENT_CHAT_ID:
        return
    if getattr(message, "message_thread_id", None) != EVENT_TOPIC_ID:
        return

    # Never allow members to enter Event details publicly in the Events topic.
    try:
        await message.delete()
    except TelegramError:
        pass

    submission_id = context.user_data.get("event_private_submission_id")
    if submission_id:
        try:
            row = event_router._get_submission(int(submission_id))
            if row and row["user_id"] == user.id and row["status"] in {"member_input", "awaiting_confirmation"}:
                await event_private_flow._send_private_form(
                    context,
                    user.id,
                    int(submission_id),
                    intro=False,
                )
                raise ApplicationHandlerStop
        except ApplicationHandlerStop:
            raise
        except Exception:
            pass

    # If the member has no active private form, silently redirect them to the
    # bot. The flyer itself must be submitted first so a private submission can
    # be created.
    try:
        bot = await context.bot.get_me()
        if bot.username:
            link = f"https://t.me/{bot.username}?start=event"
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    "🔒 <b>Event submissions are private.</b>\n\n"
                    "Please submit the Event flyer in the Events topic first. "
                    "I will move the rest of the Event form into our private chat."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔒 OPEN PRIVATE EVENT CHAT", url=link)]
                ]),
            )
    except Exception:
        pass

    raise ApplicationHandlerStop


def install_application(application):
    if getattr(application, "_melanated_event_text_guard_installed", False):
        return

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_event_topic_text),
        group=0,
    )
    application._melanated_event_text_guard_installed = True
