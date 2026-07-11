import os
import logging

from flask import Flask
from threading import Thread

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    ChatMemberHandler
)

from commands import get_command_handlers
from welcome import welcome_new_member


# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing")


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
# WELCOME NEW MEMBERS
# =========================

async def new_member_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.chat_member:

        new_member = update.chat_member.new_chat_member

        if new_member.status == "member":

            await welcome_new_member(
                update,
                context
            )


# =========================
# BOT STARTUP
# =========================

async def startup(app):

    print("🔥 Melanated AZ Bot Started")
    print("✅ Rules System Active")
    print("✅ Welcome System Active")
    print("✅ Media Protection Ready")


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


    # Commands
    for handler in get_command_handlers():
        app.add_handler(handler)


    # Welcome system
    app.add_handler(
        ChatMemberHandler(
            new_member_handler,
            ChatMemberHandler.CHAT_MEMBER
        )
    )


    print("🚀 Starting Telegram Bot...")

    app.run_polling(
        allowed_updates=[
            Update.CHAT_MEMBER,
            Update.MESSAGE
        ]
    )


if __name__ == "__main__":
    main()
