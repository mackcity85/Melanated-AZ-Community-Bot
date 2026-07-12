# ==========================================================
# Melanated AZ Bot
# bot.py
# Main Integration File
# ==========================================================

import os
import asyncio
import logging
from threading import Thread

from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN

from database import (
    initialize_database,
    update_member
)

from welcome import (
    welcome_new_member,
    profile_check,
    intro
)

from rules import rules

from admin import (
    admin_help,
    remove_member,
    ban_member
)

from raffle import (
    start_raffle,
    enter_raffle,
    raffle_status,
    draw_raffle
)

from activity_scheduler import activity_check

from birthday_scheduler import birthday_check



# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    __name__
)



# ==========================================================
# FLASK HEALTH CHECK
# ==========================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "Melanated AZ Bot is running"



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
# TRACK ALL MESSAGES
# ==========================================================

async def activity_tracker(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user:

        update_member(
            update.effective_user.id,
            update.effective_chat.id,
            update.effective_user.username,
            update.effective_user.first_name
        )



# ==========================================================
# STARTUP TASKS
# ==========================================================

async def post_init(
    application: Application
):

    print(
        "Melanated AZ Bot is running"
    )


    application.create_task(
        birthday_check(
            application
        )
    )


    application.create_task(
        activity_check(
            application
        )
    )



# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update,
    context
):

    logger.error(
        "Exception:",
        exc_info=context.error
    )



# ==========================================================
# MAIN
# ==========================================================

def main():

    initialize_database()


    Thread(
        target=run_flask,
        daemon=True
    ).start()



    application = (

        ApplicationBuilder()

        .token(
            BOT_TOKEN
        )

        .post_init(
            post_init
        )

        .build()

    )



    # ------------------------------
    # Member Events
    # ------------------------------

    application.add_handler(

        MessageHandler(

            filters.StatusUpdate.NEW_CHAT_MEMBERS,

            welcome_new_member

        )

    )



    application.add_handler(

        MessageHandler(

            filters.ALL,

            activity_tracker

        )

    )



    # ------------------------------
    # Commands
    # ------------------------------

    application.add_handler(

        CommandHandler(
            "rules",
            rules
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
            "admin",
            admin_help
        )

    )


    application.add_handler(

        CommandHandler(
            "remove",
            remove_member
        )

    )


    application.add_handler(

        CommandHandler(
            "ban",
            ban_member
        )

    )



    # ------------------------------
    # Raffle
    # ------------------------------

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



    application.add_error_handler(
        error_handler
    )



    # ------------------------------
    # Start Bot
    # ------------------------------

    application.run_polling(
        drop_pending_updates=True
    )



# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()
