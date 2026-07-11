import logging
import threading
import os

from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from config import TOKEN, STARTUP_CHAT_ID
from database import init_db


# ==========================
# LOGGING
# ==========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==========================
# FLASK HEALTH CHECK
# ==========================

web_app = Flask(__name__)


@web_app.route("/")
def home():

    return "Melanated AZ Bot v2 is running!"


def run_web():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )


# ==========================
# COMMANDS
# ==========================

async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "Melanated AZ Bot v2 is online."
    )


async def get_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat


    await update.message.reply_text(
        f"👤 User ID: {user.id}\n"
        f"💬 Chat ID: {chat.id}"
    )


async def startup_message(
    app
):

    logging.info(
        "🤖 Melanated AZ Bot v2 started"
    )


    if STARTUP_CHAT_ID:

        await app.bot.send_message(
            chat_id=STARTUP_CHAT_ID,
            text=(
                "🤖 Melanated AZ Bot v2 is online!\n\n"
                "✅ Core System Running\n"
                "✅ Database Connected\n"
                "✅ Ready for features"
            )
        )


# ==========================
# MAIN
# ==========================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN missing"
        )


    init_db()


    threading.Thread(
        target=run_web,
        daemon=True
    ).start()


    application = (
        Application
        .builder()
        .token(TOKEN)
        .post_init(startup_message)
        .build()
    )


    # Commands

    application.add_handler(
        CommandHandler(
            "ping",
            ping
        )
    )


    application.add_handler(
        CommandHandler(
            "getid",
            get_id
        )
    )


    logging.info(
        "🚀 Starting Telegram bot..."
    )


    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
