# ==========================================================
# Melanated AZ Bot
# birthday.py
# ==========================================================

import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from raffle_database import (
    save_birthday,
    get_birthday,
    remove_birthday,
)

logger = logging.getLogger(__name__)

BIRTHDAY_INPUT = 9101


def birthday_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎂 Add My Birthday", callback_data="birthday_add")],
        [
            InlineKeyboardButton("📅 My Birthday", callback_data="birthday_view"),
            InlineKeyboardButton("🗑️ Remove", callback_data="birthday_remove"),
        ],
    ])


def birthday_announcement_text():
    return (
        "🎂 **LET US CELEBRATE YOU!** 🎉\n\n"
        "At **Melanated AZ**, we love celebrating our people! 💜👑\n\n"
        "We want to give everyone a special **birthday shout-out** "
        "on their big day! 🥳🎁\n\n"
        "👇 Tap **🎂 Add My Birthday** and enter your birthday as **MM/DD**.\n\n"
        "Let’s make sure nobody in the Melanated AZ family goes "
        "without a little birthday love! 🎉🥳💜\n\n"
        "**🎂 Your birthday. Your shout-out. Your celebration. 👑**"
    )


def birthday_deep_link_keyboard(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🎂 Add My Birthday",
            url=f"https://t.me/{bot_username}?start=birthday",
        )]
    ])


async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return ConversationHandler.END

    context.user_data["birthday_chat_id"] = message.chat_id

    await message.reply_text(
        "🎂 **Birthday Setup**\n\n"
        "Please enter your birthday using **MM/DD**.\n\n"
        "Example: `08/27`\n\n"
        "Your birthday will be saved so Melanated AZ can give you "
        "a shout-out on your special day!",
        parse_mode="Markdown",
    )

    return BIRTHDAY_INPUT


async def birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return ConversationHandler.END

    from config import RAFFLE_CHAT_ID
    context.user_data["birthday_chat_id"] = RAFFLE_CHAT_ID

    await message.reply_text(
        "👑 **Welcome to Melanated AZ!**\n\n"
        "🎂 Let’s get your birthday added so we can celebrate you!\n\n"
        "📅 Please enter your birthday using **MM/DD**.\n\n"
        "Example: `08/27`",
        parse_mode="Markdown",
    )

    return BIRTHDAY_INPUT


async def birthday_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not message or not user or not message.text:
        return BIRTHDAY_INPUT

    birthday_value = message.text.strip()

    try:
        parsed = datetime.strptime(birthday_value, "%m/%d")
        birthday_value = parsed.strftime("%m/%d")
    except ValueError:
        await message.reply_text(
            "❌ That doesn't look like a valid birthday.\n\n"
            "Please enter it as **MM/DD**.\n\n"
            "Example: `08/27`",
            parse_mode="Markdown",
        )
        return BIRTHDAY_INPUT

    from config import RAFFLE_CHAT_ID
    chat_id = context.user_data.get("birthday_chat_id") or RAFFLE_CHAT_ID

    save_birthday(
        user_id=user.id,
        chat_id=chat_id,
        birthday=birthday_value,
        username=user.username,
        display_name=user.full_name,
    )

    context.user_data.pop("birthday_chat_id", None)

    await message.reply_text(
        "🎉 **Birthday Saved!** 🎂\n\n"
        f"Your birthday is saved as **{birthday_value}**.\n\n"
        "💜 On your special day, Melanated AZ will give you a "
        "birthday shout-out in the community!\n\n"
        "👑 We can't wait to celebrate you!",
        parse_mode="Markdown",
        reply_markup=birthday_menu_keyboard(),
    )

    logger.info("Birthday saved for user %s: %s", user.id, birthday_value)
    return ConversationHandler.END


async def birthday_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return ConversationHandler.END

    await query.answer()
    data = query.data or ""

    if data == "birthday_add":
        from config import RAFFLE_CHAT_ID
        context.user_data["birthday_chat_id"] = RAFFLE_CHAT_ID

        await query.message.reply_text(
            "🎂 **Birthday Setup**\n\n"
            "Enter your birthday using **MM/DD**.\n\n"
            "Example: `08/27`",
            parse_mode="Markdown",
        )
        return BIRTHDAY_INPUT

    from config import RAFFLE_CHAT_ID

    if data == "birthday_view":
        record = get_birthday(user_id=user.id, chat_id=RAFFLE_CHAT_ID)

        if not record:
            await query.message.reply_text(
                "🎂 You don't have a birthday saved yet.\n\n"
                "Tap **🎂 Add My Birthday** to add one.",
                parse_mode="Markdown",
                reply_markup=birthday_menu_keyboard(),
            )
            return ConversationHandler.END

        await query.message.reply_text(
            "🎂 **Your Birthday**\n\n"
            f"📅 **{record['birthday']}**\n\n"
            "Your birthday is saved in the Melanated AZ database.",
            parse_mode="Markdown",
            reply_markup=birthday_menu_keyboard(),
        )
        return ConversationHandler.END

    if data == "birthday_remove":
        removed = remove_birthday(user_id=user.id, chat_id=RAFFLE_CHAT_ID)

        await query.message.reply_text(
            "🗑️ Your birthday has been removed."
            if removed else "ℹ️ You don't have a birthday saved.",
            reply_markup=birthday_menu_keyboard(),
        )
        return ConversationHandler.END

    return ConversationHandler.END


async def my_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    from config import RAFFLE_CHAT_ID
    record = get_birthday(user_id=user.id, chat_id=RAFFLE_CHAT_ID)

    if not record:
        await message.reply_text(
            "🎂 You don't have a birthday saved yet.\n\n"
            "Tap **🎂 Add My Birthday** to add one.",
            parse_mode="Markdown",
            reply_markup=birthday_menu_keyboard(),
        )
        return

    await message.reply_text(
        "🎂 **Your Birthday**\n\n"
        f"📅 **{record['birthday']}**",
        parse_mode="Markdown",
        reply_markup=birthday_menu_keyboard(),
    )


async def remove_my_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    from config import RAFFLE_CHAT_ID
    removed = remove_birthday(user_id=user.id, chat_id=RAFFLE_CHAT_ID)

    await message.reply_text(
        "🗑️ Your birthday has been removed."
        if removed else "ℹ️ You don't have a birthday saved.",
        reply_markup=birthday_menu_keyboard(),
    )
