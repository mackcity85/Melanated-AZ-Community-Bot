import os
import threading

from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters


TOKEN = os.getenv("BOT_TOKEN")

WARNING = """⚠️ Media Removed

Please resend your picture or video using Telegram's Hide with Spoiler option.

How to do it:

1. Select your photo or video.
2. Before sending, tap the ⋮ menu (or options button).
3. Choose Hide with Spoiler.
4. Send the media again.

Thank you for helping keep the group comfortable for everyone. 🙏
"""


# Render web service health check
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Spoiler bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


async def check_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    # Check photos and videos
    if message.photo or message.video:

        # Allow only spoiler media
        if not message.has_media_spoiler:
            try:
                await message.delete()
                await update.effective_chat.send_message(WARNING)

            except Exception as e:
                print("Delete error:", e)


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is missing")

    # Start Render web listener
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO,
            check_media
        )
    )

    print("Spoiler moderation bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
