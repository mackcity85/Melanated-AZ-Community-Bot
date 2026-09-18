# ==========================================================
# Melanated AZ Bot
# config.py
# ==========================================================

import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

ADMIN_IDS = []
_admin_ids = os.environ.get("ADMIN_IDS", "").strip()
if _admin_ids:
    try:
        ADMIN_IDS = [int(x.strip()) for x in _admin_ids.split(",") if x.strip()]
    except ValueError:
        ADMIN_IDS = []

MAIN_GROUP_ID = None
_main_group_id = os.environ.get("MAIN_GROUP_ID", "").strip()
if _main_group_id:
    try:
        MAIN_GROUP_ID = int(_main_group_id)
    except ValueError:
        MAIN_GROUP_ID = None

RAFFLE_CHAT_ID = MAIN_GROUP_ID
_raffle_chat_id = os.environ.get("RAFFLE_CHAT_ID", "").strip()
if _raffle_chat_id:
    try:
        RAFFLE_CHAT_ID = int(_raffle_chat_id)
    except ValueError:
        RAFFLE_CHAT_ID = MAIN_GROUP_ID

RAFFLE_DURATION_DAYS = int(os.environ.get("RAFFLE_DURATION_DAYS", "7"))
CASHAPP_TAG = os.environ.get("CASHAPP_TAG", "").strip()
CASHAPP_URL = os.environ.get("CASHAPP_URL", "").strip()
ZELLE_PHONE = os.environ.get("ZELLE_PHONE", "").strip()

print(f"Loaded Admin IDs: {ADMIN_IDS}")
print(f"Main Group ID: {MAIN_GROUP_ID}")
print(f"Raffle Chat ID: {RAFFLE_CHAT_ID}")
print("Cash App: Loaded" if CASHAPP_TAG else "Cash App: NOT configured")
print("Zelle: Loaded" if ZELLE_PHONE else "Zelle: NOT configured")


# ==========================================================
# COMPATIBILITY: /postintro COMMAND
# ==========================================================

async def post_intro_topic_command(update, context):
    """Admin-only manual post for the Introductions topic."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.constants import ParseMode
    from telegram.error import TelegramError
    from admin import is_admin

    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return

    if not await is_admin(user.id, context):
        await message.reply_text("⛔ You are not authorized to use /postintro.")
        return

    main_group_id = MAIN_GROUP_ID
    if not main_group_id:
        await message.reply_text("❌ MAIN_GROUP_ID is not configured.")
        return

    bot_username = context.application.bot_data.get("bot_username")
    keyboard = None
    if bot_username:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "👋🏾 Submit My Introduction",
                url=f"https://t.me/{bot_username}?start=intro",
            )],
            [InlineKeyboardButton(
                "🎂 Add My Birthday",
                callback_data="birthday_intro_add",
            )],
        ])

    text = (
        "👋🏾 <b>INTRODUCTIONS REMINDER</b>\n\n"
        "We’re updating the <b>👋 Introductions</b> page and would love for you to help us out. "
        "The admins and everyone in the community would love to get to know you and know a little about who you are. 💜\n\n"
        "<b>Your introduction is required.</b> We want to know who is part of our community.\n\n"
        "Take a few minutes and tell us:\n\n"
        "• What do you go by?\n"
        "• Relationship / dynamic status?\n"
        "• Where are you from?\n"
        "• What city &amp; state are you in?\n"
        "• What brings you to Melanated AZ?\n"
        "• What are you into?\n"
        "• What are you looking for?\n\n"
        "🎂 <b>Want to add your birthday too?</b>\n"
        "We give our members <b>birthday shoutouts</b> in the group, so add your birthday if you’d like us to celebrate you! 🎉\n\n"
        "Nothing formal — <b>just be yourself, have fun with it, and let us get to know you!</b> 😏🔥"
    )

    try:
        sent = await context.bot.send_message(
            chat_id=main_group_id,
            message_thread_id=int(os.environ.get("INTRO_TOPIC_ID", "11570") or "11570"),
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
        await message.reply_text(
            "✅ Intro reminder posted successfully.\n\n"
            f"Posted to chat {main_group_id}, topic {os.environ.get('INTRO_TOPIC_ID', '11570')}, message {sent.message_id}."
        )
    except TelegramError as exc:
        await message.reply_text(
            "❌ Intro reminder FAILED.\n\n"
            f"Telegram error: {exc}"
        )


# ==========================================================
# OPTIONAL BIRTHDAY STEP FOR THE MANDATORY INTRO FLOW
# ==========================================================

async def _intro_birthday_callback_bridge(update, context):
    query = update.callback_query
    user = update.effective_user
    if not query or not user or not query.data:
        return
    if query.data != "birthday_intro_add":
        return

    await query.answer()
    context.user_data["awaiting_birthday"] = True
    context.user_data["return_to_intro_after_birthday"] = True

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "🎂 <b>Add Your Birthday</b>\n\n"
                "We give our members <b>birthday shoutouts</b> in Melanated AZ, "
                "so if you'd like us to celebrate you, add your birthday! 🎉💜\n\n"
                "Enter your birthday using <b>MM/DD</b>.\n\n"
                "Example: <b>08/27</b>"
            ),
            parse_mode="HTML",
        )
    except Exception:
        return


def _install_intro_birthday_bridge():
    """Patch the existing birthday handlers before bot.py imports them."""
    try:
        import birthday as _birthday
        if getattr(_birthday, "_intro_birthday_bridge_installed", False):
            return

        _original_callback = _birthday.birthday_callback
        _original_text_handler = _birthday.birthday_text_handler

        async def callback_wrapper(update, context):
            query = update.callback_query
            if query and query.data == "birthday_intro_add":
                return await _intro_birthday_callback_bridge(update, context)
            return await _original_callback(update, context)

        async def text_wrapper(update, context):
            returning_to_intro = bool(context.user_data.get("return_to_intro_after_birthday"))
            handled = await _original_text_handler(update, context)
            if not returning_to_intro:
                return handled

            if context.user_data.get("awaiting_birthday"):
                return handled

            context.user_data.pop("return_to_intro_after_birthday", None)
            user = update.effective_user
            if not user:
                return handled

            bot_username = context.application.bot_data.get("bot_username")
            if not bot_username:
                try:
                    me = await context.bot.get_me()
                    bot_username = me.username
                    if bot_username:
                        context.application.bot_data["bot_username"] = bot_username
                except Exception:
                    bot_username = None

            keyboard = None
            if bot_username:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "👋🏾 Complete My Intro",
                        url=f"https://t.me/{bot_username}?start=intro",
                    )]
                ])

            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=(
                        "👋🏾 <b>Birthday saved!</b> 🎉💜\n\n"
                        "Your birthday is now on the Melanated AZ birthday list, and we'll give you a "
                        "<b>birthday shoutout</b> when your day comes around. 🎂🥳\n\n"
                        "Your introduction is still <b>required</b>. We need to know who is in our community, "
                        "so let's finish your intro now."
                    ),
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception:
                pass

            return handled

        _birthday.birthday_callback = callback_wrapper
        _birthday.birthday_text_handler = text_wrapper
        _birthday._intro_birthday_bridge_installed = True
    except Exception:
        pass


_install_intro_birthday_bridge()


# ==========================================================
# GLOBAL NOTIFICATION POLICY
# ==========================================================

import notification_policy  # noqa: E402,F401


import builtins as _builtins
_builtins.post_intro_topic_command = post_intro_topic_command
