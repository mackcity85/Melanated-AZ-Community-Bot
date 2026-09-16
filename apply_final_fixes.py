from pathlib import Path
import re


def replace_once(text, pattern, replacement, label):
    text2, count = re.subn(pattern, replacement, text, count=1, flags=re.M | re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text2


# QOTD private submissions.
p = Path("question_of_day.py")
s = p.read_text(encoding="utf-8")
s = replace_once(
    s,
    r'^    if action == "qotd_submit_question":\n.*?^        return\n(?=    if action == "qotd_submit_poll":)',
    '''    if action == "qotd_submit_question":
        context.user_data["qotd_state"] = "question"
        context.user_data["qotd_chat_id"] = None
        context.user_data["qotd_thread_id"] = None
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="📝 <b>Send your question now.</b>\\n\\n🔒 Your submission is private and will not appear in the group until it is posted as the QOTD.\\n\\nKeep it under 3,000 characters.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]),
            )
        except TelegramError:
            await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
        return
''',
    "QOTD question",
)
s = replace_once(
    s,
    r'^    if action == "qotd_submit_poll":\n.*?^        return\n(?=\n\nclass QotdInputFilter)',
    '''    if action == "qotd_submit_poll":
        context.user_data["qotd_state"] = "poll_question"
        context.user_data["qotd_chat_id"] = None
        context.user_data["qotd_thread_id"] = None
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="📊 <b>Build your poll</b>\\n\\n🔒 Your poll submission is private and will not appear in the group until it is posted as the QOTD.\\n\\nFirst, send the poll question. Then I'll ask for the answer choices.\\n\\nQuestion limit: 300 characters.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="qotd_cancel")]]),
            )
        except TelegramError:
            await query.answer("Open the bot privately and press Start first, then try again.", show_alert=True)
        return
''',
    "QOTD poll",
)
s = replace_once(
    s,
    r'^    expected_chat = context\.user_data\.get\("qotd_chat_id"\)\n.*?^    text = message\.text\.strip\(\)',
    '''    if message.chat.type != "private":
        return
    text = message.text.strip()''',
    "QOTD input routing",
)
s = replace_once(
    s,
    r'^async def _finish_submission\(update, context, item_id, saved_text\):\n.*?(?=^async def _delete_message_job)',
    '''async def _finish_submission(update, context, item_id, saved_text):
    message = update.effective_message
    chat_id = message.chat_id if message and message.chat.type == "private" else None
    for key in ("qotd_state", "qotd_prompt", "qotd_chat_id", "qotd_thread_id"):
        context.user_data.pop(key, None)
    if message and message.chat.type == "private":
        try:
            await message.delete()
        except TelegramError:
            pass
    if queued_count() == 1 and not daily_post_already_done():
        posted = await publish_item(context, item_id)
        if posted:
            return
    if chat_id:
        try:
            count = queued_count()
            notice = await context.bot.send_message(
                chat_id=chat_id,
                text=f"{saved_text}\\n\\n📚 Added to the Question of the Day bank.\\n<b>{count}</b> day{'s' if count != 1 else ''} currently queued.",
                parse_mode="HTML",
            )
            if context.job_queue:
                context.job_queue.run_once(_delete_message_job, 15, data=(chat_id, notice.message_id))
        except TelegramError:
            logger.exception("Could not send QOTD submission confirmation.")


''',
    "QOTD finish",
)
p.write_text(s, encoding="utf-8")


# Private onboarding + admin verification notification + raffle repost protection.
p = Path("bot.py")
s = p.read_text(encoding="utf-8")
if 'send_message(chat_id=user_id,text=f"🤖 <b>QUICK HUMAN CHECK</b>' not in s:
    s = s.replace('send_message(chat_id=chat_id,text=f"🤖 <b>QUICK HUMAN CHECK</b>', 'send_message(chat_id=user_id,text=f"🤖 <b>QUICK HUMAN CHECK</b>', 1)
    if 'send_message(chat_id=user_id,text=f"🤖 <b>QUICK HUMAN CHECK</b>' not in s:
        raise RuntimeError("Human verification target not found")
if 'send_community_intro_video(user.id,context,name)' not in s:
    if 'send_community_intro_video(event.chat.id,context,name)' not in s:
        raise RuntimeError("Intro video caller not found")
    s = s.replace('send_community_intro_video(event.chat.id,context,name)', 'send_community_intro_video(user.id,context,name)', 1)

s = replace_once(
    s,
    r'^    user=update\.effective_user; chat=update\.effective_chat\n    if not user or not chat or user\.id!=target:return\n    row=community_member\(chat\.id,user\.id\).*?^    mark_verified\(chat\.id,user\.id\); await restore_member\(context\.bot,chat\.id,user\.id\); private_opened=await send_private_intro_prompt\(user,context\)',
    '''    user=update.effective_user; chat=update.effective_chat
    if not user or not chat or user.id!=target:return
    main=configured_main_group_id()
    if not main:return
    row=community_member(main,user.id)
    if not row or row["status"]!="pending_verification":return
    expires=parse_iso(row["verification_expires_at"]); challenge=row["verification_challenge"] or ""
    if not expires or expires<utc_now() or "###" not in challenge: await send_human_challenge(main,user.id,context); return
    answer,blob=challenge.split("###",1); options=blob.split("|||")
    if selected<0 or selected>=len(options):return
    if options[selected]!=answer:
        attempts=increment_verification_attempt(main,user.id)
        if attempts>=VERIFICATION_MAX_ATTEMPTS: await remove_unverified_member(context.bot,main,user.id); return
        await send_human_challenge(main,user.id,context); return
    mark_verified(main,user.id); await restore_member(context.bot,main,user.id); await notify_admin_group_verification(context,user); private_opened=await send_private_intro_prompt(user,context)''',
    "verification callback",
)
if 'async def notify_admin_group_verification' not in s:
    marker='async def human_verification_callback(update,context):\n'
    fn='''async def notify_admin_group_verification(context,user):
    admin_group=configured_admin_group_id()
    if not admin_group or not user:
        return
    username=f"@{html.escape(user.username)}" if getattr(user,"username",None) else "No username"
    name=html.escape(user.full_name or user.first_name or "Unknown member")
    timestamp=utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        await context.bot.send_message(
            chat_id=admin_group,
            text=f"🛡️ <b>MEMBER VERIFIED</b>\\n\\n👤 <b>{name}</b>\\n🔹 Username: {username}\\n🆔 User ID: <code>{user.id}</code>\\n🕒 Verified: <code>{timestamp}</code>\\n\\n👋🏾 The member is now cleared to participate, but their mandatory introduction is still required.",
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.exception("Could not notify Admin Group about verified member %s",user.id)

'''
    if marker not in s: raise RuntimeError("Verification callback marker not found")
    s=s.replace(marker,fn+marker,1)

old='''    raffle_id=int(raffle["id"])
    try:
        # Do not write None into the raffle post fields. publish_raffle()
        # creates the replacement post and saves its real Telegram IDs.
        if await publish_raffle(raffle_id,context):'''
new='''    raffle_id=int(raffle["id"])
    if raffle["message_id"]:
        logger.info("Raffle topic repair skipped: active raffle already has Telegram message_id=%s.",raffle["message_id"])
        try:
            os.makedirs(os.path.dirname(marker) or ".",exist_ok=True)
            with open(marker,"w",encoding="utf-8") as fh: fh.write(f"raffle={raffle_id}\\nexisting_message_id={raffle[\"message_id\"]}\\n")
        except Exception:
            pass
        return
    try:
        # Only publish when the active raffle has no Telegram post recorded.
        if await publish_raffle(raffle_id,context):'''
if old not in s: raise RuntimeError("Raffle repair target not found")
s=s.replace(old,new,1)
p.write_text(s, encoding="utf-8")

print("Final source patch applied successfully.")
