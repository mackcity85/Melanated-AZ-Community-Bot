"""Truth or Dare <-> QOTD integration.

Adds:
- Truth/Dare submissions to the private QOTD bank.
- Admin-only immediate Truth/Dare posts to QOTD topic 11999.
- Keeps existing topic content intact; only sends new messages.
"""

import html
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, CallbackQueryHandler

import bot
import admin
import question_of_day as qotd
import truth_dare

logger = logging.getLogger("truth_dare_qotd")

TD_PREFIX = "__TD__"
TD_MAX_CHARS = 3000


def _td_prompt(kind, prompt):
    return f"{TD_PREFIX}{kind.upper()}__{prompt}"


def _decode_td(prompt):
    if not isinstance(prompt, str) or not prompt.startswith(TD_PREFIX):
        return None, prompt
    rest = prompt[len(TD_PREFIX):]
    if "__" not in rest:
        return None, prompt
    kind, text = rest.split("__", 1)
    if kind not in {"TRUTH", "DARE"}:
        return None, prompt
    return kind.lower(), text


def _qotd_menu_markup_with_td():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📝 Submit a Question", callback_data="qotd_submit_question")],
            [InlineKeyboardButton("📊 Build a Poll", callback_data="qotd_submit_poll")],
            [InlineKeyboardButton("🔥 Submit Truth or Dare", callback_data="qotd_submit_truthdare")],
            [InlineKeyboardButton("📚 Bank Status", callback_data="qotd_status")],
            [InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")],
        ]
    )


async def _send_private_td_choice(update, context):
    user = update.effective_user
    if not user:
        return
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "🔥 <b>TRUTH OR DARE — QOTD SUBMISSION</b>\n\n"
                "Choose what you want to submit.\n\n"
                "🔒 Your submission stays private until it is posted."
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔥 Truth", callback_data="qotd_td_truth"),
                        InlineKeyboardButton("😈 Dare", callback_data="qotd_td_dare"),
                    ],
                    [InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")],
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        query = update.callback_query
        if query:
            await query.answer(
                "Open the bot privately and press Start first, then try again.",
                show_alert=True,
            )


async def _qotd_td_callback(update, context):
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    data = query.data

    if data == "qotd_submit_truthdare":
        context.user_data["qotd_state"] = "truth_dare_choice"
        context.user_data["qotd_chat_id"] = None
        context.user_data["qotd_thread_id"] = None
        await _send_private_td_choice(update, context)
        return

    if data in {"qotd_td_truth", "qotd_td_dare"}:
        kind = "truth" if data.endswith("truth") else "dare"
        context.user_data["qotd_state"] = "truth_dare_prompt"
        context.user_data["qotd_td_kind"] = kind
        context.user_data["qotd_chat_id"] = None
        context.user_data["qotd_thread_id"] = None
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=(
                    f"{'🔥 TRUTH' if kind == 'truth' else '😈 DARE'} — <b>QOTD SUBMISSION</b>\n\n"
                    "Send the Truth/Dare now.\n\n"
                    "🔒 It stays private until it is posted.\n"
                    "Keep it under 3,000 characters."
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]
                ),
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            await query.answer(
                "Open the bot privately and press Start first, then try again.",
                show_alert=True,
            )


def _patch_qotd_menu():
    qotd.qotd_menu_markup = _qotd_menu_markup_with_td


def _patch_qotd_callbacks_and_text():
    original_callback = qotd.qotd_callback
    original_text = qotd.qotd_text_handler

    async def patched_callback(update, context):
        data = update.callback_query.data if update.callback_query else ""
        if data in {"qotd_submit_truthdare", "qotd_td_truth", "qotd_td_dare"}:
            await _qotd_td_callback(update, context)
            return
        if data == "qotd_cancel":
            context.user_data.pop("qotd_td_kind", None)
        await original_callback(update, context)

    async def patched_text(update, context):
        state = context.user_data.get("qotd_state")
        message = update.effective_message

        if state == "truth_dare_choice":
            if message and message.chat.type == "private":
                await message.reply_text(
                    "Use the 🔥 Truth or 😈 Dare buttons from the private QOTD prompt."
                )
                raise ApplicationHandlerStop
            return

        if state == "truth_dare_prompt":
            if not message or not message.text or message.chat.type != "private":
                return
            text = message.text.strip()
            if not 1 <= len(text) <= TD_MAX_CHARS:
                await message.reply_text("❌ Your Truth/Dare must be between 1 and 3,000 characters.")
                raise ApplicationHandlerStop
            kind = context.user_data.get("qotd_td_kind")
            if kind not in {"truth", "dare"}:
                context.user_data.pop("qotd_state", None)
                context.user_data.pop("qotd_td_kind", None)
                await message.reply_text("⚠️ I lost track of the submission. Please start again from QOTD.")
                raise ApplicationHandlerStop
            item_id = qotd.add_item(
                "question",
                _td_prompt(kind, text),
                None,
                update.effective_user,
            )
            context.user_data.pop("qotd_td_kind", None)
            await qotd._finish_submission(update, context, item_id, f"{'🔥 Truth' if kind == 'truth' else '😈 Dare'} saved!")
            raise ApplicationHandlerStop

        return await original_text(update, context)

    qotd.qotd_callback = patched_callback
    qotd.qotd_text_handler = patched_text


def _patch_publish_item():
    original_publish = qotd.publish_item

    async def patched_publish(context, item_id=None):
        item = qotd.get_next_item(item_id)
        if not item:
            return False
        kind, text = _decode_td(item["prompt"])
        if not kind:
            return await original_publish(context, item_id)

        if not qotd.qotd_enabled():
            return False
        if not qotd.claim_item(item["id"]):
            return False

        try:
            emoji = "🔥" if kind == "truth" else "😈"
            title = "TRUTH OF THE DAY" if kind == "truth" else "DARE OF THE DAY"
            sent = await context.bot.send_message(
                chat_id=qotd.qotd_chat_id(),
                message_thread_id=qotd.QUESTION_OF_DAY_TOPIC_ID,
                text=f"{emoji} <b>{title}</b>\n\n{html.escape(text)}",
                parse_mode=ParseMode.HTML,
            )
            qotd.mark_posted(item["id"], sent.message_id)
            logger.info(
                "QOTD TRUTH/DARE POSTED | item=%s type=%s date=%s",
                item["id"], kind, qotd.today_key(),
            )
            return True
        except TelegramError:
            qotd.restore_item(item["id"])
            logger.exception("Truth/Dare QOTD post failed | item=%s", item["id"])
            return False

    qotd.publish_item = patched_publish


def _patch_qotd_registration():
    original_register = qotd.register_question_of_day_handlers

    def patched_register(application):
        original_register(application)
        application.add_handler(
            CallbackQueryHandler(
                qotd.qotd_callback,
                pattern=r"^qotd_(submit_truthdare|td_truth|td_dare)$",
            ),
            group=0,
        )

    qotd.register_question_of_day_handlers = patched_register


async def _admin_td_menu(update, context):
    user = update.effective_user
    query = update.callback_query
    if not user or not await admin.is_admin(user.id, context) or not query:
        return
    status = "🟢 ENABLED" if truth_dare.TRUTH_DARE_ENABLED else "🔴 DISABLED"
    await query.edit_message_text(
        "🔥 <b>TRUTH OR DARE SETTINGS</b>\n\n"
        f"Status: {status}\n\n"
        "Members can use:\n"
        "/truthdare\n"
        "/truth\n"
        "/dare\n\n"
        "You can also post a custom Truth or Dare directly into the QOTD topic.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"🔥 Truth or Dare: {status}", callback_data="admin_truthdare_toggle")],
                [InlineKeyboardButton("📣 Post Truth or Dare to QOTD", callback_data="admin_truthdare_qotd")],
                [InlineKeyboardButton("❓ View Help", callback_data="admin_truthdare_help")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_back")],
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


async def _admin_td_start(update, context):
    query = update.callback_query
    if not query or not await admin.is_admin(update.effective_user.id, context):
        return
    await query.answer()
    try:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "📣 <b>POST TRUTH OR DARE TO QOTD</b>\n\n"
                "Choose what you want to post to topic <code>11999</code>."
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔥 Truth", callback_data="admin_truthdare_qotd_truth"),
                        InlineKeyboardButton("😈 Dare", callback_data="admin_truthdare_qotd_dare"),
                    ],
                    [InlineKeyboardButton("❌ Cancel", callback_data="admin_truthdare_qotd_cancel")],
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        await query.answer(
            "Open the bot privately and press Start first, then try again.",
            show_alert=True,
        )
        return


async def _admin_td_kind(update, context, kind):
    query = update.callback_query
    if not query or not await admin.is_admin(update.effective_user.id, context):
        return
    context.user_data["admin_td_qotd_state"] = "prompt"
    context.user_data["admin_td_qotd_kind"] = kind
    await query.answer()
    try:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                f"{'🔥 TRUTH' if kind == 'truth' else '😈 DARE'} — <b>QOTD POST</b>\n\n"
                "Send the text you want posted to the QOTD topic.\n\n"
                "This will post immediately to topic <code>11999</code>.\n"
                "Keep it under 3,000 characters."
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Cancel", callback_data="admin_truthdare_qotd_cancel")]]
            ),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        await query.answer(
            "Open the bot privately and press Start first, then try again.",
            show_alert=True,
        )


async def _admin_td_text(update, context):
    state = context.user_data.get("admin_td_qotd_state")
    if state != "prompt":
        return False
    message = update.effective_message
    user = update.effective_user
    if not message or not message.text or message.chat.type != "private" or not user:
        return False
    if not await admin.is_admin(user.id, context):
        context.user_data.pop("admin_td_qotd_state", None)
        context.user_data.pop("admin_td_qotd_kind", None)
        return True

    text = message.text.strip()
    if not 1 <= len(text) <= TD_MAX_CHARS:
        await message.reply_text("❌ Keep the Truth/Dare between 1 and 3,000 characters.")
        return True

    kind = context.user_data.get("admin_td_qotd_kind")
    if kind not in {"truth", "dare"}:
        await message.reply_text("⚠️ I lost the Truth/Dare type. Please start again from the admin panel.")
        return True

    chat_id = int(os.environ.get("MAIN_GROUP_ID", "0") or "0")
    topic_id = int(os.environ.get("QUESTION_OF_DAY_TOPIC_ID", "11999") or "11999")
    if not chat_id or not topic_id:
        await message.reply_text("❌ QOTD topic is not configured.")
        return True

    emoji = "🔥" if kind == "truth" else "😈"
    title = "TRUTH" if kind == "truth' else "DARE"
    try:
        posted = await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=topic_id,
            text=f"{emoji} <b>{title}</b>\n\n{html.escape(text)}",
            parse_mode=ParseMode.HTML,
        )
        await message.reply_text(
            f"✅ {title} posted to QOTD topic <code>{topic_id}</code>.\nMessage ID: <code>{posted.message_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.exception("Admin Truth/Dare QOTD post failed.")
        await message.reply_text("❌ I could not post that to the QOTD topic. Check the Render logs.")

    context.user_data.pop("admin_td_qotd_state", None)
    context.user_data.pop("admin_td_qotd_kind", None)
    return True


async def _admin_button_wrapper(update, context):
    data = update.callback_query.data if update.callback_query else ""
    if data == "admin_truthdare_qotd":
        await _admin_td_start(update, context)
        return
    if data == "admin_truthdare_qotd_truth":
        await _admin_td_kind(update, context, "truth")
        return
    if data == "admin_truthdare_qotd_dare":
        await _admin_td_kind(update, context, "dare")
        return
    if data == "admin_truthdare_qotd_cancel":
        if not update.effective_user or not await admin.is_admin(update.effective_user.id, context):
            return
        for key in ("admin_td_qotd_state", "admin_td_qotd_kind"):
            context.user_data.pop(key, None)
        query = update.callback_query
        if query:
            await query.answer("Cancelled")
            await query.edit_message_text("📣 Truth/Dare QOTD posting cancelled.")
        return
    return await admin._original_admin_button(update, context)


def _patch_admin():
    admin._original_admin_button = getattr(admin, "admin_button")
    admin.admin_button = _admin_button_wrapper
    bot.admin_button = _admin_button_wrapper
    truth_dare.truth_dare_admin_menu = _admin_td_menu


def install():
    _patch_qotd_menu()
    _patch_qotd_callbacks_and_text()
    _patch_publish_item()
    _patch_qotd_registration()
    _patch_admin()


install()
