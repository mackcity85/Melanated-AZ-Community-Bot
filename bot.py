# ==========================================================
# Melanated AZ Bot
# Main Bot Controller
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


# ==========================================================
# MODULE IMPORTS
# ==========================================================

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
    register_admin_commands
)

from raffle import (
    start_raffle,
    enter_raffle,
    raffle_status,
    draw_raffle
)

from trivia import (
    trivia,
    trivia_answer
)

from truth_dare import (
    truth,
    dare
)

from birthday_scheduler import (
    start_birthday_scheduler
)

from activity_scheduler import (
    start_activity_scheduler
)

from pin_cleanup import (
    pin_cleanup_task
)


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
# STARTUP
# ==========================================================

async def startup(
    application: Application
):

    # Clear stale Telegram polling sessions

    try:

        await application.bot.get_updates(
            offset=-1,
            timeout=1
        )

    except Exception:

        pass



    await application.bot.delete_webhook(
        drop_pending_updates=True
    )


    logger.info(
        "🔥 Melanated AZ Bot is running"
    )


    # Start background tasks

    asyncio.create_task(
        pin_cleanup_task(
            application
        )
    )



# ==========================================================
# TRACK MEMBER ACTIVITY
# ==========================================================

async def activity_tracker(
    update,
    context
):

    if update.effective_user and update.effective_chat:

        update_member(
            update.effective_user.id,
            update.effective_chat.id,
            update.effective_user.username,
            update.effective_user.first_name
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


    # --------------------------
    # Member Activity
    # --------------------------

    application.add_handler(
        MessageHandler(
            filters.ALL,
            activity_tracker
        ),
        group=-1
    )


    # --------------------------
    # Welcome
    # --------------------------

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


    # --------------------------
    # Profile Check
    # --------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            profile_check
        )
    )


    # --------------------------
    # Admin
    # --------------------------

    register_admin_commands(
        application
    )


    # --------------------------
    # Raffle
    # --------------------------

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
            "draw",
            draw_raffle
        )
    )


    # --------------------------
    # Trivia
    # --------------------------

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


    # --------------------------
    # Truth / Dare
    # --------------------------

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


    application.add_error_handler(
        error_handler
    )


    application.run_polling(
        drop_pending_updates=True
    )



# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()
