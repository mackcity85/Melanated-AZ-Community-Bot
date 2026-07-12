import os
import logging
import threading

from dotenv import load_dotenv
from flask import Flask

from database import (
    initialize_database,
    update_member,
    save_birthday
)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# ==========================================================
# CONFIG
# ==========================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# ==========================================================
# FLASK HEALTH CHECK
# ==========================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def health():

    return "Melanated AZ Bot is running. Media Spoiler and Birthdays"



def run_flask():

    port = int(os.getenv("PORT", 10000))

    flask_app.run(
        host="0.0.0.0",
        port=port
    )


# ==========================================================
# COMMANDS
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔥 Melanated AZ Bot is online.\n\n"
        "Media spoiler protection is active.\n"
        "Use /rules for group rules.\n"
        "Use /birthday MM/DD to save your birthday."
    )



async def rules(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📜 Melanated AZ Rules\n\n"
        "1. Respect everyone.\n"
        "2. No harassment, bullying, or drama.\n"
        "3. Adults only community.\n"
        "4. Follow admin instructions.\n"
        "5. Photos/videos must use Telegram spoiler protection."
    )



# ==========================================================
# BIRTHDAY COMMAND
# ==========================================================

async def birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "🎂 Usage:\n/birthday MM/DD\n\nExample:\n/birthday 07/12"
        )

        return


    birthday_date = context.args[0]


    save_birthday(
        update.effective_user.id,
        update.effective_chat.id,
        birthday_date
    )


    await update.message.reply_text(
        "🎂 Birthday saved!"
    )


# ==========================================================
# MEMBER ACTIVITY TRACKING
# ==========================================================

async def track_activity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user and update.effective_chat:

        update_member(
            update.effective_user.id,
            update.effective_chat.id,
            update.effective_user.username,
            update.effective_user.first_name
        )


# ==========================================================
# MEDIA SPOILER PROTECTION
# ==========================================================

async def media_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return


    has_media = (
        message.photo or
        message.video or
        message.animation or
        message.document
    )


    if has_media:

        if not message.has_media_spoiler:

            try:

                await message.delete()

                await context.bot.send_message(
                    chat_id=message.chat.id,
                    text=(
                        f"⚠️ {message.from_user.first_name}, "
                        "media must be posted using Telegram spoiler protection."
                    )
                )


            except Exception as e:

                logging.error(
                    f"Media removal error: {e}"
                )


# ==========================================================
# START BOT
# ==========================================================

def main():

    if not TOKEN:

        raise Exception(
            "BOT_TOKEN is missing"
        )


    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()


    initialize_database()


    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    # Commands

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    application.add_handler(
        CommandHandler(
            "rules",
            rules
        )
    )


    application.add_handler(
        CommandHandler(
            "birthday",
            birthday
        )
    )


    # Media protection

    application.add_handler(
        MessageHandler(
            filters.PHOTO |
            filters.VIDEO |
            filters.ANIMATION |
            filters.Document.ALL,
            media_check
        )
    )


    # Activity tracking

    application.add_handler(
        MessageHandler(
            filters.ALL,
            track_activity
        ),
        group=1
    )


    print(
        "Melanated AZ Bot is running. Media Spoiler and Birthdays"
    )


    application.run_polling()



if __name__ == "__main__":

    main()

