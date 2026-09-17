# ==========================================================
# Melanated AZ Bot - Event Topic Privacy Guard
# ==========================================================
# The Events topic is NOT an Event submission form.
# Members must interact with the bot privately.
# ==========================================================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, CommandHandler, ContextTypes

import event_router

EVENT_CHAT_ID = event_router.EVENT_CHAT_ID
EVENT_TOPIC_ID = event_router.EVENT_TOPIC_ID


async def _private_event_button(update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    if not message or not user or user.is_bot:
        return
    if message.chat_id != EVENT_CHAT_ID:
        return
    if getattr(message, "message_thread_id", None) != EVENT_TOPIC_ID:
        return

    # The command itself is removed. Only a private-chat button is shown.
    try:
        await message.delete()
    except TelegramError:
        pass

    try:
        bot = await context.bot.get_me()
        if not bot.username:
            return
        link = f"https://t.me/{bot.username}?start=event"
        sent = await context.bot.send_message(
            chat_id=EVENT_CHAT_ID,
            message_thread_id=EVENT_TOPIC_ID,
            text="📩 <b>Submit your Event privately with the bot.</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔒 OPEN PRIVATE EVENT SUBMISSION", url=link)]
            ]),
        )
        # The button is only an entry point; it does not contain or display
        # any Event information. Remove it after 2 minutes to keep the topic clean.
        try:
            context.job_queue.run_once(
                _delete_message_job,
                when=120,
                data={"chat_id": EVENT_CHAT_ID, "message_id": sent.message_id},
                name=f"event_private_entry_{sent.message_id}",
            )
        except Exception:
            pass
    except Exception:
        pass

    raise ApplicationHandlerStop


async def _delete_message_job(context):
    data = context.job.data or {}
    try:
        await context.bot.delete_message(
            chat_id=data.get("chat_id"),
            message_id=data.get("message_id"),
        )
    except Exception:
        pass


async def handle_event_topic_text(update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user or user.is_bot:
        return
    if message.chat_id != EVENT_CHAT_ID:
        return
    if getattr(message, "message_thread_id", None) != EVENT_TOPIC_ID:
        return

    # No Event details, captions, or field responses are ever handled publicly.
    try:
        await message.delete()
    except TelegramError:
        pass

    # Do not send a public form or public status message.
    raise ApplicationHandlerStop


def install_application(application):
    if getattr(application, "_melanated_event_text_guard_installed", False):
        return

    # /event in the Events topic is only an entry point to the private bot chat.
    application.add_handler(
        CommandHandler("event", _private_event_button),
        group=-9,
    )

    # All normal public Event-topic text is silently deleted.
    handler = __import__("telegram.ext", fromlist=["MessageHandler"]).MessageHandler(
        __import__("telegram.ext", fromlist=["filters"]).filters.TEXT & ~__import__("telegram.ext", fromlist=["filters"]).filters.COMMAND,
        handle_event_topic_text,
    )
    handlers = application.handlers.setdefault(0, [])
    handlers.insert(0, handler)
    application._melanated_event_text_guard_installed = True
