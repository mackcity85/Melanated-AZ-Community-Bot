import os
import logging

from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from telegram.ext import Application

from commands import get_command_handlers


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN missing")


logging.basicConfig(
    level=logging.INFO
)


# Render health check

flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Melanated AZ Bot Running"


def run_flask():
    flask_app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )


async def startup(app):

    print("🔥 Melanated AZ Bot Started")

    commands = get_command_handlers()

    print(f"Loaded {len(commands)} commands")

    await app.bot.set_my_commands([
        ("rules", "View community rules"),
        ("intro", "Introduction format"),
        ("spoiler", "Media instructions"),
        ("help", "Bot help"),
    ])


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


    for handler in get_command_handlers():
        app.add_handler(handler)


    print("🚀 Starting Telegram Bot")

    app.run_polling()


if __name__ == "__main__":
    main()
