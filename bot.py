# ==========================================================
# Melanated AZ Bot
# bot.py
# Main Controller
# ==========================================================

import os
import logging
import threading
import asyncio

from flask import Flask

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN

from database import initialize_database

from welcome import (
    welcome_new_member,
    profile_check,
    intro
)

from rules import rules

from admin import admin_commands

from raffle import (
    start_raffle,
    enter_raffle,
    draw_raffle,
    raffle_status
)

from birthdays import (
    birthday,
    birthday_check
)

from trivia import (
    trivia,
    trivia_answer
)

from truth_dare import (
    truth,
    dare
)

from media import media_protection

from moderation import delete_message

from activity_scheduler import start_activity_scheduler
from birthday_scheduler import start_birthday_scheduler
from pin_cleanup import pin_cleanup_task


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ==========================================================
# FLASK HEALTH CHECK
# ==========================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "Melanated AZ Bot Online"


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# ==========================================================
# STARTUP
# ==========================================================

async def startup(
    application: Application
):

    await application.bot.delete_webhook(
        drop_pending_updates=True
    )


    logger.info(
        "Melanated AZ Bot Started"
    )


    asyncio.create_task(
        start_activity_scheduler(
            application
        )
    )


    asyncio.create_task(
        start_birthday_scheduler(
            application
        )
    )


    asyncio.create_task(
        pin_cleanup_task(
            application
        )
    )



# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Bot Error",
        exc_info=context.error
    )



# ==========================================================
# MAIN
# ==========================================================

def main():


    initialize_database()


    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()



    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(startup)
        .build()
    )



    # ======================================================
    # WELCOME
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )


    application.add_handler(
        CommandHandler(
            "intro",
            intro
        )
    )


    application.add_handler(
        CommandHandler(
            "rules",
            rules
        )
    )



    # ======================================================
    # MEDIA PROTECTION
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.PHOTO |
            filters.VIDEO |
            filters.Document.VIDEO |
            filters.ANIMATION,
            media_protection
        ),
        group=1
    )



    # ======================================================
    # PROFILE TRACKING
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            profile_check
        )
    )



    # ======================================================
    # RAFFLES
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "enter",
            enter_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "raffle",
            raffle_status
        )
    )


    application.add_handler(
        CommandHandler(
            "drawraffle",
            draw_raffle
        )
    )



    # ======================================================
    # BIRTHDAYS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "birthday",
            birthday
        )
    )


    application.add_handler(
        CommandHandler(
            "birthdaycheck",
            birthday_check
        )
    )



    # ======================================================
    # GAMES
    # ======================================================

    application.add_handler(
        CommandHandler(
            "trivia",
            trivia
        )
    )


    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            trivia_answer
        )
    )


    application.add_handler(
        CommandHandler(
            "truth",
            truth
        )
    )


    application.add_handler(
        CommandHandler(
            "dare",
            dare
        )
    )



    # ======================================================
    # ADMIN
    # ======================================================

    application.add_handler(
        CommandHandler(
            "admin",
            admin_commands
        )
    )


    application.add_handler(
        CommandHandler(
            "delete",
            delete_message
        )
    )



    application.add_error_handler(
        error_handler
    )



    logger.info(
        "Melanated AZ Bot is running"
    )


    application.run_polling(
        drop_pending_updates=True
    )



# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()
