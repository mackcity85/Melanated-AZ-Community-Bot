import os
import logging

from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from telegram import Update
from telegram.ext import (
    Application,
    ChatMemberHandler,
    MessageHandler,
    filters
)

from commands import get_command_handlers
from welcome import welcome_new_member
from moderation import check_media


# =========================
# LOAD ENVIRONMENT
# =========================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing")


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =========================
# FLASK HEALTH CHECK
# =========================

flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Melanated AZ Bot is running."


def run_flask():

    flask_app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )


# =========================
# WELCOME SYSTEM
# =========================

async def new_member_handler(
    update: Update,
    context
):

    await welcome_new_member(
        update,
        context
    )


# =========================
# STARTUP
# =========================

async def startup(app):

    print("🔥 Melanated AZ Bot Started")

    commands = get_command_handlers()

    print(f"Loaded {len(commands)} commands")

    await app.bot.set_my_commands(
        [
            ("rules", "View community rules"),
            ("intro", "Introduction format"),
            ("spoiler", "Media spoiler instructions"),
            ("help", "Bot help"),
        ]
    )


# =========================
# MAIN
# =========================

def main():

    Thread(
        target=run_flask,
        daemon=True
    ).start()


    app = (
        Application
        .builder()
        .token(TOKEN)
        .post_init(startup)
        .build()
    )


    # =====================
    # COMMANDS
    # =====================

    for handler in get_command_handlers():
        app.add_handler(handler)


    # =====================
    # WELCOME NEW MEMBERS
    # =====================

    app.add_handler(
        ChatMemberHandler(
            new_member_handler,
            ChatMemberHandler.CHAT_MEMBER
        )
    )


    # =====================
    # MEDIA PROTECTION
    # =====================

    app.add_handler(
        MessageHandler(
            filters.PHOTO
            | filters.VIDEO,
            check_media
        )
    )


    print("🚀 Starting Telegram Bot")

    app.run_polling()


if __name__ == "__main__":
    main()
