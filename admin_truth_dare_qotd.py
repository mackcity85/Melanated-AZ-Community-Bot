"""Admin Truth/Dare -> QOTD topic posting."""
import html
import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop
import admin
import bot
import truth_dare

log = logging.getLogger("admin_truth_dare_qotd")
MAX_CHARS = 3000

async def td_admin_menu(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user or not await admin.is_admin(user.id, context):
        return
    status = "🟢 ENABLED" if truth_dare.TRUTH_DARE_ENABLED else "🔴 DISABLED"
    await query.edit_message_text(
        "🔥 <b>TRUTH OR DARE SETTINGS</b>\n\n"
        f"Status: {status}\n\n"
        "Members can use /truthdare, /truth and /dare.\n\n"
        "Admins can also post a custom Truth or Dare directly to QOTD topic <code>11999</code>.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔥 Truth or Dare: {status}", callback_data="admin_truthdare_toggle")],
            [InlineKeyboardButton("📣 Post Truth or Dare to QOTD", callback_data="admin_td_qotd")],
            [InlineKeyboardButton("❓ View Help", callback_data="admin_truthdare_help")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")],
        ]),
        parse_mode=ParseMode.HTML,
    )

async def start_post(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user or not await admin.is_admin(user.id, context):
        return
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text="📣 <b>POST TRUTH OR DARE TO QOTD</b>\n\nChoose what you want to post to topic <code>11999</code>.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Truth", callback_data="admin_td_truth"), InlineKeyboardButton("😈 Dare", callback_data="admin_td_dare")],
                [InlineKeyboardButton("❌ Cancel", callback_data="admin_td_cancel")],
            ]),
            parse_mode=ParseMode.HTML,
        )
        await query.answer("Check your private messages.")
    except TelegramError:
        await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)

async def choose_kind(update, context, kind):
    query = update.callback_query
    user = update.effective_user
    if not query or not user or not await admin.is_admin(user.id, context):
        return
    context.user_data["admin_td_state"] = "prompt"
    context.user_data["admin_td_kind"] = kind
    await query.answer()
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"{'🔥 TRUTH' if kind == 'truth' else '😈 DARE'} — <b>QOTD POST</b>\n\nSend the text to post immediately to topic <code>11999</code>.\n\nKeep it under 3,000 characters.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_td_cancel")]]),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)

async def admin_td_text(update, context):
    if context.user_data.get("admin_td_state") != "prompt":
        return False
    message = update.effective_message
    user = update.effective_user
    if not message or not message.text or message.chat.type != "private" or not user:
        return False
    if not await admin.is_admin(user.id, context):
        context.user_data.pop("admin_td_state", None)
        context.user_data.pop("admin_td_kind", None)
        return True
    text = message.text.strip()
    if not 1 <= len(text) <= MAX_CHARS:
        await message.reply_text("❌ Keep the Truth/Dare between 1 and 3,000 characters.")
        return True
    kind = context.user_data.get("admin_td_kind")
    if kind not in {"truth", "dare"}:
        await message.reply_text("⚠️ I lost the Truth/Dare type. Start again from the admin panel.")
        return True
    try:
        chat_id = int(os.environ.get("MAIN_GROUP_ID", "0") or "0")
        topic_id = int(os.environ.get("QUESTION_OF_DAY_TOPIC_ID", "11999") or "11999")
    except ValueError:
        chat_id, topic_id = 0, 0
    if not chat_id or not topic_id:
        await message.reply_text("❌ QOTD topic is not configured.")
        return True
    emoji = "🔥" if kind == "truth" else "😈"
    title = "TRUTH" if kind == "truth" else "DARE"
    try:
        sent = await context.bot.send_message(chat_id=chat_id, message_thread_id=topic_id, text=f"{emoji} <b>{title}</b>\n\n{html.escape(text)}", parse_mode=ParseMode.HTML)
        await message.reply_text(f"✅ {title} posted to QOTD topic <code>{topic_id}</code>.\nMessage ID: <code>{sent.message_id}</code>", parse_mode=ParseMode.HTML)
    except TelegramError:
        log.exception("Admin Truth/Dare QOTD post failed")
        await message.reply_text("❌ I could not post that to the QOTD topic. Check the Render logs.")
    context.user_data.pop("admin_td_state", None)
    context.user_data.pop("admin_td_kind", None)
    raise ApplicationHandlerStop

async def button_wrapper(update, context):
    data = update.callback_query.data if update.callback_query else ""
    if data == "admin_td_qotd":
        await start_post(update, context)
        return
    if data == "admin_td_truth":
        await choose_kind(update, context, "truth")
        return
    if data == "admin_td_dare":
        await choose_kind(update, context, "dare")
        return
    if data == "admin_td_cancel":
        user = update.effective_user
        if not user or not await admin.is_admin(user.id, context):
            return
        context.user_data.pop("admin_td_state", None)
        context.user_data.pop("admin_td_kind", None)
        await update.callback_query.answer("Cancelled")
        await update.callback_query.edit_message_text("📣 Truth/Dare QOTD posting cancelled.")
        return
    # Chain to the admin button handler that existed immediately before this
    # patch was installed. Do NOT use admin._original_admin_button here,
    # because another patch (social_admin_patch) may already own that slot.
    await admin._truth_dare_previous_admin_button(update, context)

def install():
    # Preserve the currently installed admin handler instead of overwriting a
    # shared _original_admin_button reference. This prevents wrapper recursion
    # when multiple admin patches are installed in sequence.
    if not hasattr(admin, "_truth_dare_previous_admin_button"):
        admin._truth_dare_previous_admin_button = admin.admin_button
    admin.admin_button = button_wrapper
    bot.admin_button = button_wrapper
    truth_dare.truth_dare_admin_menu = td_admin_menu
    if not hasattr(bot, "_original_text_router"):
        bot._original_text_router = bot.text_router
        async def router(update, context):
            if await admin_td_text(update, context):
                return
            await bot._original_text_router(update, context)
        bot.text_router = router

install()
