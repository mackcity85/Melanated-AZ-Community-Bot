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


# ==========================
# CONFIG
# ==========================

TOKEN = os.getenv("BOT_TOKEN")


WARNING = """⚠️ Media Removed

This group requires all pictures, videos, GIFs, and media files to be sent using Telegram's Hide with Spoiler option.

Please resend your media with the spoiler enabled.

How to do it:

1. Select your photo or video.
2. Tap the ⋮ menu/options.
3. Choose "Hide with Spoiler".
4. Send the media again.

Thank you for helping keep the group comfortable for everyone. 🙏
"""


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==========================
# WEB SERVER (RENDER)
# ==========================

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


# ==========================
# MEDIA CHECK
# ==========================

async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.effective_message

    if not message:
        return


    # Ignore commands/text
    if not (
        message.photo
        or message.video
        or message.animation
        or message.document
    ):
        return


    # ==========================
    # ADMIN BYPASS
    # ==========================

    try:

        member = await context.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )

        if member.status in [
            "administrator",
            "creator"
        ]:
            return

    except Exception:

        pass


    # ==========================
    # ALLOW SPOILER MEDIA
    # ==========================

    if message.has_media_spoiler:
        logging.info(
            "Allowed spoiler media"
        )
        return


    # ==========================
    # DELETE MEDIA
    # ==========================

    try:

        await message.delete()

        await context.bot.send_message(
            chat_id=message.chat.id,
            text=WARNING
        )


        logging.info(
            "Removed non-spoiler media from %s",
            message.from_user.username
            if message.from_user
            else "unknown"
        )


    except Exception as e:

        logging.exception(
            "Unable to remove media: %s",
            e
        )


# ==========================
# START BOT
# ==========================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN environment variable missing"
        )


    threading.Thread(
        target=run_web,
        daemon=True
    ).start()


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    media_filter = (
        filters.PHOTO
        | filters.VIDEO
        | filters.ANIMATION
        | filters.Document.IMAGE
        | filters.Document.VIDEO
    )


    app.add_handler(
        MessageHandler(
            media_filter,
            check_media
        )
    )


    logging.info(
        "Spoiler moderation bot running"
    )


    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
