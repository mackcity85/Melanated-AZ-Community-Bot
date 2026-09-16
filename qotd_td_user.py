"""User-facing Truth/Dare submissions for QOTD."""
import html
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, CallbackQueryHandler
import question_of_day as qotd

log = logging.getLogger("qotd_td_user")
PREFIX = "__TD__"
MAX_CHARS = 3000

def encode(kind, text):
    return f"{PREFIX}{kind.upper()}__{text}"

def decode(prompt):
    if not isinstance(prompt, str) or not prompt.startswith(PREFIX):
        return None, prompt
    rest = prompt[len(PREFIX):]
    if "__" not in rest:
        return None, prompt
    kind, text = rest.split("__", 1)
    return (kind.lower(), text) if kind in ("TRUTH", "DARE") else (None, prompt)

def menu():
    rows = list(qotd.qotd_menu_markup().inline_keyboard)
    rows.insert(2, [InlineKeyboardButton("🔥 Submit Truth or Dare", callback_data="qotd_submit_truthdare")])
    return InlineKeyboardMarkup(rows)

async def td_callback(update, context):
    query = update.callback_query
    data = query.data if query else ""
    if not query or data not in {"qotd_submit_truthdare", "qotd_td_truth", "qotd_td_dare"}:
        return False
    await query.answer()
    user = update.effective_user
    if not user:
        return True
    if data == "qotd_submit_truthdare":
        context.user_data["qotd_state"] = "td_choice"
        try:
            await context.bot.send_message(chat_id=user.id, text="🔥 <b>TRUTH OR DARE — QOTD</b>\n\nChoose what you want to submit.\n\n🔒 Your submission stays private until posted.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Truth", callback_data="qotd_td_truth"), InlineKeyboardButton("😈 Dare", callback_data="qotd_td_dare")],[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]), parse_mode=ParseMode.HTML)
        except TelegramError:
            await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
        return True
    kind = "truth" if data.endswith("truth") else "dare"
    context.user_data["qotd_state"] = "td_prompt"
    context.user_data["qotd_td_kind"] = kind
    try:
        await context.bot.send_message(chat_id=user.id, text=f"{'🔥 TRUTH' if kind == 'truth' else '😈 DARE'} — <b>QOTD SUBMISSION</b>\n\nSend it now.\n\n🔒 It stays private until posted.\nKeep it under 3,000 characters.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]), parse_mode=ParseMode.HTML)
    except TelegramError:
        await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
    return True

def install():
    original_menu = qotd.qotd_menu_markup
    original_callback = qotd.qotd_callback
    original_text = qotd.qotd_text_handler
    original_publish = qotd.publish_item
    original_register = qotd.register_question_of_day_handlers
    def patched_menu():
        base = list(original_menu().inline_keyboard)
        base.insert(2, [InlineKeyboardButton("🔥 Submit Truth or Dare", callback_data="qotd_submit_truthdare")])
        return InlineKeyboardMarkup(base)
    async def patched_callback(update, context):
        if await td_callback(update, context):
            return
        if update.callback_query and update.callback_query.data == "qotd_cancel":
            context.user_data.pop("qotd_td_kind", None)
        await original_callback(update, context)
    async def patched_text(update, context):
        state = context.user_data.get("qotd_state")
        message = update.effective_message
        if state == "td_choice":
            if message and message.chat.type == "private":
                await message.reply_text("Use the 🔥 Truth or 😈 Dare buttons above.")
                raise ApplicationHandlerStop
            return
        if state == "td_prompt":
            if not message or not message.text or message.chat.type != "private":
                return
            text = message.text.strip()
            if not 1 <= len(text) <= MAX_CHARS:
                await message.reply_text("❌ Your Truth/Dare must be between 1 and 3,000 characters.")
                raise ApplicationHandlerStop
            kind = context.user_data.get("qotd_td_kind")
            if kind not in ("truth", "dare"):
                await message.reply_text("⚠️ I lost the submission type. Please start again from QOTD.")
                raise ApplicationHandlerStop
            item_id = qotd.add_item("question", encode(kind, text), None, update.effective_user)
            context.user_data.pop("qotd_td_kind", None)
            await qotd._finish_submission(update, context, item_id, f"{'🔥 Truth' if kind == 'truth' else '😈 Dare'} saved!")
            raise ApplicationHandlerStop
        return await original_text(update, context)
    async def patched_publish(context, item_id=None):
        item = qotd.get_next_item(item_id)
        if not item:
            return False
        kind, text = decode(item["prompt"])
        if not kind:
            return await original_publish(context, item_id)
        if not qotd.qotd_enabled() or not qotd.claim_item(item["id"]):
            return False
        try:
            emoji = "🔥" if kind == "truth" else "😈"
            title = "TRUTH OF THE DAY" if kind == "truth" else "DARE OF THE DAY"
            sent = await context.bot.send_message(chat_id=qotd.qotd_chat_id(), message_thread_id=qotd.QUESTION_OF_DAY_TOPIC_ID, text=f"{emoji} <b>{title}</b>\n\n{html.escape(text)}", parse_mode=ParseMode.HTML)
            qotd.mark_posted(item["id"], sent.message_id)
            return True
        except TelegramError:
            qotd.restore_item(item["id"])
            log.exception("Truth/Dare QOTD post failed")
            return False
    def patched_register(application):
        original_register(application)
        application.add_handler(CallbackQueryHandler(qotd.qotd_callback, pattern=r"^qotd_(submit_truthdare|td_truth|td_dare)$"), group=0)
    qotd.qotd_menu_markup = patched_menu
    qotd.qotd_callback = patched_callback
    qotd.qotd_text_handler = patched_text
    qotd.publish_item = patched_publish
    qotd.register_question_of_day_handlers = patched_register

install()
