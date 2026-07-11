import asyncio
import threading

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN
from database import initialize_database, update_member
from moderation import check_media


# -----------------------------
# Flask Health Check (Render)
# -----------------------------

app = Flask(__name__)


@app.route("/")
def home():
    return "🔥 Melanated AZ Community Bot v4 is running."


def run_flask():
    app.run(
        host="0.0.0.0",
        port=8080
    )


# -----------------------------
# Commands
# -----------------------------

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "🔥 Melanated AZ Community Bot v4 is online!\n\n"
        "Community protection features are active."
    )


async def get_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat = update.effective_chat

    await update.message.reply_text(
        f"Chat ID:\n{chat.id}"
    )


# -----------------------------
# Member Activity Tracking
# -----------------------------

async def track_activity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user:
        update_member(
            update.effective_user
        )


# -----------------------------
# Main Bot
# -----------------------------

async def main():

    initialize_database()

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
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
            "getid",
            get_id
        )
    )


    # Track users
    application.add_handler(
        MessageHandler(
            filters.ALL,
            track_activity
        ),
        group=1
    )


    # Media protection
    application.add_handler(
        MessageHandler(
            filters.ALL,
            check_media
        ),
        group=2
    )


    print(
        "🔥 Melanated AZ Community Bot v4 is running"
    )


    await application.run_polling()



if __name__ == "__main__":

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()


    asyncio.run(
        main()
    )
