# bot.py
# Telegram Spoiler Moderation Bot
# python-telegram-bot v21+

import os
import threading
import logging

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")


WARNING = """⚠️ Media Removed

This group requires all photos, videos, GIFs, and media files to be sent using Telegram's Hide with Spoiler option.

Please resend your media with the spoiler enabled.

How to do it:

1. Select your photo or video.
2. Tap the ⋮ menu/options button.
3. Select "Hide with Spoiler".
4. Send it again.

Thank you for helping keep the group comfortable and safe. 🙏
"""


# -------------------------
# Render Keep Alive
# -------------------------

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Spoiler bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(
        host="0.0.0.0",
        port=port
    )


# -------------------------
# Media Detection
# -------------------------

async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return


    is_media = False


    # Photo
    if message.photo:
        is_media = True


    # Video
    elif message.video:
        is_media = True


    # GIF
    elif message.animation:
        is_media = True


    # Files
    elif message.document:

        mime = message.document.mime_type

        if mime:
            if (
                mime.startswith("image/")
                or
                mime.startswith("video/")
            ):
                is_media = True


    if not is_media:
        return


    # Allow spoiler media
    if message.has_media_spoiler:
        return


    try:

        await message.delete()

        await context.bot.send_message(
            chat_id=message.chat.id,
            text=WARNING
        )

        logging.info(
            "Removed non-spoiler media from %s",
            message.from_user.id
        )


    except Exception as e:

        logging.exception(
            "Failed removing media: %s",
            e
        )


# -------------------------
# Start Bot
# -------------------------

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN missing"
        )


    threading.Thread(
        target=run_web,
        daemon=True
    ).start()


    app = Application.builder()\
        .token(TOKEN)\
        .build()


    # Catch all messages
    app.add_handler(
        MessageHandler(
            filters.ALL,
            check_media
        )
    )


    logging.info(
        "Spoiler moderation bot running..."
    )


    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
