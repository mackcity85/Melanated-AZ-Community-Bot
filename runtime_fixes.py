"""Runtime compatibility fixes applied before bot.main().

Keeps the current bot.py/QOTD source intact while correcting the five requested
behaviors without touching existing Telegram topic content.
"""

import html
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop

import bot

logger = logging.getLogger("melanated_az_runtime_fixes")


def install():
    _patch_qotd()
    _patch_onboarding()
    _patch_raffle_repair()


def _patch_qotd():
    import question_of_day as qotd

    async def private_qotd_callback(update, context):
        query = update.callback_query
        if not query or not query.data:
            return
        action = query.data
        await query.answer()
        if action == "qotd_status":
            count = qotd.queued_count()
            await query.answer(f"{count} day{'s' if count != 1 else ''} in the bank.", show_alert=True)
            return
        if action == "qotd_cancel":
            for key in ("qotd_state", "qotd_prompt", "qotd_chat_id", "qotd_thread_id"):
                context.user_data.pop(key, None)
            try:
                await query.edit_message_text("💭 Submission cancelled.")
            except TelegramError:
                pass
            return
        if action == "qotd_submit_question":
            context.user_data["qotd_state"] = "question"
            context.user_data["qotd_chat_id"] = None
            context.user_data["qotd_thread_id"] = None
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="📝 <b>Send your question now.</b>\n\n🔒 Your submission is private and will not appear in the group until it is posted as the QOTD.\n\nKeep it under 3,000 characters.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]),
                )
            except TelegramError:
                await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
            return
        if action == "qotd_submit_poll":
            context.user_data["qotd_state"] = "poll_question"
            context.user_data["qotd_chat_id"] = None
            context.user_data["qotd_thread_id"] = None
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="📊 <b>Build your poll</b>\n\n🔒 Your poll submission is private and will not appear in the group until it is posted as the QOTD.\n\nFirst, send the poll question. Then I'll ask for the answer choices.\n\nQuestion limit: 300 characters.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]),
                )
            except TelegramError:
                await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
            return

    async def private_qotd_text_handler(update, context):
        state = context.user_data.get("qotd_state")
        if not state:
            return
        message = update.effective_message
        if not message or not message.text or message.chat.type != "private":
            return
        text = message.text.strip()
        if state == "question":
            if not 1 <= len(text) <= qotd.QOTD_MAX_QUESTION:
                await message.reply_text("❌ That question must be between 1 and 3,000 characters.")
                raise ApplicationHandlerStop
            item_id = qotd.add_item("question", text, None, update.effective_user)
            await private_finish_submission(update, context, item_id, "📝 Question saved!")
            raise ApplicationHandlerStop
        if state == "poll_question":
            if not 1 <= len(text) <= 300:
                await message.reply_text("❌ Poll questions must be between 1 and 300 characters.")
                raise ApplicationHandlerStop
            context.user_data["qotd_state"] = "poll_options"
            context.user_data["qotd_prompt"] = text
            await message.reply_text(
                "📊 Now send the answer choices separated by <b>|</b>.\n\nExample:\n<code>Yes | No | Maybe</code>\n\nUse 2–10 choices, with each choice under 100 characters.",
                parse_mode=ParseMode.HTML,
            )
            raise ApplicationHandlerStop
        if state == "poll_options":
            options = [part.strip() for part in text.split("|") if part.strip()]
            if not qotd.QOTD_MIN_OPTIONS <= len(options) <= qotd.QOTD_MAX_OPTIONS:
                await message.reply_text("❌ A poll needs 2–10 answer choices separated by |.")
                raise ApplicationHandlerStop
            if any(len(option) > qotd.QOTD_MAX_OPTION for option in options):
                await message.reply_text("❌ Each poll choice must be 100 characters or fewer.")
                raise ApplicationHandlerStop
            prompt = context.user_data.get("qotd_prompt", "").strip()
            item_id = qotd.add_item("poll", prompt, options, update.effective_user)
            await private_finish_submission(update, context, item_id, "📊 Poll saved!")
            raise ApplicationHandlerStop

    async def private_finish_submission(update, context, item_id, saved_text):
        message = update.effective_message
        chat_id = message.chat_id if message and message.chat.type == "private" else None
        for key in ("qotd_state", "qotd_prompt", "qotd_chat_id", "qotd_thread_id"):
            context.user_data.pop(key, None)
        if message and message.chat.type == "private":
            try:
                await message.delete()
            except TelegramError:
                pass
        # Keep every submission in the persistent QOTD bank.
        # The scheduled daily-post job owns publishing; submissions must not
        # disappear from the queue just because they were the first entry.
        logger.info("QOTD submission saved to bank | item_id=%s | queued=%s", item_id, qotd.queued_count())
        if chat_id:
            try:
                count = qotd.queued_count()
                notice = await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{saved_text}\n\n📚 Added to the Question of the Day bank.\n<b>{count}</b> day{'s' if count != 1 else ''} currently queued.",
                    parse_mode=ParseMode.HTML,
                )
                if context.job_queue:
                    context.job_queue.run_once(qotd._delete_message_job, 15, data=(chat_id, notice.message_id))
            except TelegramError:
                logger.exception("Could not send QOTD private confirmation.")

    qotd.qotd_callback = private_qotd_callback
    qotd.qotd_text_handler = private_qotd_text_handler
    qotd._finish_submission = private_finish_submission


def _patch_onboarding():
    async def private_human_challenge(chat_id, user_id, context):
        row = bot.community_member(chat_id, user_id)
        if not row:
            return
        import random
        answer, options = random.choice(bot.HUMAN_CHALLENGES)
        shuffled = list(options)
        random.shuffle(shuffled)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(option, callback_data=f"human_verify:{user_id}:{i}")] for i, option in enumerate(shuffled)])
        try:
            message = await context.bot.send_message(
                chat_id=user_id,
                text=f"🤖 <b>QUICK HUMAN CHECK</b>\n\nBefore you join the conversation, prove you're human. 👀\n\n<b>Which one is {answer.split(' ',1)[1].lower()}?</b>\n\nTap the correct answer below.",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            bot.set_verification_challenge(chat_id, user_id, answer, shuffled, message.message_id)
        except TelegramError:
            logger.exception("Could not send private human verification to %s", user_id)

    async def verification_callback(update, context):
        query = update.callback_query
        if not query or not query.data:
            return
        try:
            await query.answer()
        except Exception:
            pass
        parts = query.data.split(":")
        if len(parts) != 3:
            return
        try:
            target = int(parts[1])
            selected = int(parts[2])
        except ValueError:
            return
        user = update.effective_user
        if not user or user.id != target:
            return
        main = bot.configured_main_group_id()
        if not main:
            return
        row = bot.community_member(main, user.id)
        if not row or row["status"] != "pending_verification":
            return
        expires = bot.parse_iso(row["verification_expires_at"])
        challenge = row["verification_challenge"] or ""
        if not expires or expires < bot.utc_now() or "###" not in challenge:
            await private_human_challenge(main, user.id, context)
            return
        answer, blob = challenge.split("###", 1)
        options = blob.split("|||")
        if selected < 0 or selected >= len(options):
            return
        if options[selected] != answer:
            attempts = bot.increment_verification_attempt(main, user.id)
            if attempts >= bot.VERIFICATION_MAX_ATTEMPTS:
                await bot.remove_unverified_member(context.bot, main, user.id)
            else:
                await private_human_challenge(main, user.id, context)
            return
        bot.mark_verified(main, user.id)
        await bot.restore_member(context.bot, main, user.id)
        await notify_admin_group_verification(context, user)
        await bot.send_private_intro_prompt(user, context)
        try:
            await query.edit_message_text(
                "✅ <b>HUMAN VERIFICATION PASSED!</b> 🎉\n\nYou're cleared to participate. 💜\n\n👋🏾 I've sent your introduction instructions privately.\nYour intro submission will stay private until the finished introduction is posted in the 👋 Introductions topic.",
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            pass

    async def notify_admin_group_verification(context, user):
        admin_group = bot.configured_admin_group_id()
        if not admin_group:
            return
        username = f"@{html.escape(user.username)}" if getattr(user, "username", None) else "No username"
        name = html.escape(user.full_name or user.first_name or "Unknown member")
        timestamp = bot.utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            await context.bot.send_message(
                chat_id=admin_group,
                text=f"🛡️ <b>MEMBER VERIFIED</b>\n\n👤 <b>{name}</b>\n🔹 Username: {username}\n🆔 User ID: <code>{user.id}</code>\n🕒 Verified: <code>{timestamp}</code>\n\n👋🏾 The member is now cleared to participate, but their mandatory introduction is still required.",
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            logger.exception("Could not notify Admin Group about verified member %s", user.id)

    async def private_community_welcome(update, context):
        event = update.chat_member
        if not event or not bot.community_chat_is_allowed(event.chat.id):
            return
        old = event.old_chat_member.status
        new = event.new_chat_member.status
        if new not in {"member", "administrator"} or old not in {"left", "kicked"}:
            return
        user = event.new_chat_member.user
        if not user or user.is_bot or await bot.is_admin(user.id, context):
            return
        bot.save_joining_member(event.chat.id, user)
        await bot.restrict_member(context.bot, event.chat.id, user.id)
        name = user.first_name or "there"
        await bot.send_community_intro_video(user.id, context, name)
        try:
            welcome = await context.bot.send_message(
                chat_id=event.chat.id,
                text=f"👋🏾 <b>WELCOME TO MELANATED AZ, {name}!</b> 💜🔥\n\n🛡️ <b>FIRST THINGS FIRST...</b>\n\nYou need to complete a quick human verification before you can post.\n\nOnce you're verified, you'll have <b>48 HOURS</b> to introduce yourself to the community.\n\nGood energy. Real people. Real connections. 🖤💜",
                parse_mode=ParseMode.HTML,
            )
            if context.job_queue:
                context.job_queue.run_once(bot.delete_message_job, bot.VERIFICATION_MESSAGE_TTL_MINUTES * 60, data=(event.chat.id, welcome.message_id))
        except TelegramError:
            pass
        await private_human_challenge(event.chat.id, user.id, context)

    bot.send_human_challenge = private_human_challenge
    bot.human_verification_callback = verification_callback
    bot.community_welcome = private_community_welcome


def _patch_raffle_repair():
    async def safe_repair_active_raffle_post(context):
        marker = "/var/data/raffle_topic_11883_repair_v1.done" if os.path.isdir("/var/data") else "./raffle_topic_11883_repair_v1.done"
        if os.path.exists(marker):
            logger.info("Raffle topic 11883 one-time repair already completed.")
            return
        raffle = bot.get_active_raffle()
        if not raffle:
            logger.info("Raffle topic repair skipped: no active raffle.")
            return
        raffle_id = int(raffle["id"])
        existing_message_id = raffle["message_id"] if "message_id" in raffle.keys() else None
        if existing_message_id:
            logger.info("Raffle topic repair skipped: active raffle already has message_id=%s.", existing_message_id)
            try:
                os.makedirs(os.path.dirname(marker) or ".", exist_ok=True)
                with open(marker, "w", encoding="utf-8") as fh:
                    fh.write(f"raffle={raffle_id}\nexisting_message_id={existing_message_id}\n")
            except Exception:
                pass
            return
        try:
            if await bot.publish_raffle(raffle_id, context):
                os.makedirs(os.path.dirname(marker) or ".", exist_ok=True)
                with open(marker, "w", encoding="utf-8") as fh:
                    fh.write(f"raffle={raffle_id}\n")
                logger.info("ONE-TIME RAFFLE REPAIR COMPLETE | raffle=%s | topic=11883", raffle_id)
            else:
                logger.error("ONE-TIME RAFFLE REPAIR FAILED | raffle=%s | topic=11883", raffle_id)
        except Exception:
            logger.exception("One-time raffle topic repair failed.")

    bot.repair_active_raffle_post = safe_repair_active_raffle_post


install()
