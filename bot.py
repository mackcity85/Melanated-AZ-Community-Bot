# ==========================================================
# bot.py
# Melanated AZ Bot v3
# ==========================================================

import logging
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


# Database
from database import (
    initialize_database,
    create_raffle_tables
)


# Welcome
from welcome import (
    welcome_new_member,
    intro
)


# Rules
from rules import rules


# Raffle
from raffle import (
    start_raffle,
    join_raffle,
    raffle_entries,
    raffle_winner,
    end_raffle
)


# Admin
from admin import (
    announce,
    purge,
    kick,
    ban,
    mute,
    unmute
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
# COMMANDS
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👑 Welcome to Melanated AZ\n\n"

        "Commands:\n\n"

        "/rules - Community guidelines\n"
        "/intro - Introduce yourself\n"
        "/help - Show commands\n\n"

        "Activities:\n"
        "/birthday\n"
        "/activities\n\n"

        "Raffle:\n"
        "/joinraffle\n"
        "/raffleentries"
    )



async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
👑 Melanated AZ Commands

Community:
 /rules
 /intro
 /birthday
 /activities

Raffle:
 /joinraffle
 /raffleentries

Admin:
 /announce
 /purge
 /kick
 /ban
 /mute
 /unmute

Admin Raffle:
 /startraffle
 /rafflewinner
 /endraffle
"""
    )



# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update,
    context
):

    logger.error(
        "Bot Error:",
        exc_info=context.error
    )



# ==========================================================
# MAIN
# ==========================================================

def main():


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
        .build()
    )


    # Basic commands

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


    # Welcome

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )


    # ======================================================
    # RAFFLE
    # ======================================================

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



    # ======================================================
    # ADMIN
    # ======================================================

    application.add_handler(
        CommandHandler(
            "announce",
            announce
        )
    )


    application.add_handler(
        CommandHandler(
            "purge",
            purge
        )
    )


    application.add_handler(
        CommandHandler(
            "kick",
            kick
        )
    )


    application.add_handler(
        CommandHandler(
            "ban",
            ban
        )
    )


    application.add_handler(
        CommandHandler(
            "mute",
            mute
        )
    )


    application.add_handler(
        CommandHandler(
            "unmute",
            unmute
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
