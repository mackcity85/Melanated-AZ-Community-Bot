# ==========================================================
# bot.py
# Melanated AZ Bot v3
# ==========================================================

import logging
import threading
import asyncio

from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN


# Database
from database import (
    initialize_database,
    create_raffle_tables
)


# Features
from welcome import (
    welcome_new_member,
    profile_check,
    intro
)

from raffle import (
    start_raffle,
    join_raffle,
    raffle_entries,
    raffle_winner,
    end_raffle
)


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================================
# FLASK HEALTH CHECK
# ==========================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "Melanated AZ Bot is running"



def run_flask():

    app.run(
        host="0.0.0.0",
        port=10000
    )



# ==========================================================
# BASIC COMMANDS
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👑 Melanated AZ Bot Online\n\n"
        "Commands:\n"
        "/rules - View community rules\n"
        "/intro - Create introduction\n"
        "/help - Show commands\n"
        "/birthday - Birthday settings\n"
        "/activities - Community activities\n"
    )



async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👑 Melanated AZ Commands\n\n"

        "Community:\n"
        "/rules\n"
        "/intro\n"
        "/birthday\n"
        "/activities\n\n"

        "Raffle:\n"
        "/joinraffle\n"
        "/raffleentries\n\n"

        "Admin:\n"
        "/startraffle\n"
        "/rafflewinner\n"
        "/endraffle"
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
# STARTUP
# ==========================================================

async def post_init(
    application
):

    logger.info(
        "Melanated AZ Bot started"
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    # Database startup

    initialize_database()

    create_raffle_tables()


    # Flask thread

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()



    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
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
            "help",
            help_command
        )
    )


    # Welcome

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



    # Raffle

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "joinraffle",
            join_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "raffleentries",
            raffle_entries
        )
    )


    application.add_handler(
        CommandHandler(
            "rafflewinner",
            raffle_winner
        )
    )


    application.add_handler(
        CommandHandler(
            "endraffle",
            end_raffle
        )
    )



    application.add_error_handler(
        error_handler
    )



    print(
        "Melanated AZ Bot is running"
    )



    application.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
