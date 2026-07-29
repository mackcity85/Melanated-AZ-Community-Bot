# ==========================================================
# Melanated AZ Bot
# bot.py
# Main Launcher
# ==========================================================

import logging

from threading import Thread

from flask import Flask

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters
)


from config import (
    BOT_TOKEN,
    STARTUP_CHAT_ID
)



# ==========================================================
# IMPORTS
# ==========================================================

from admin import admin_commands

from media import check_media

from welcome import welcome


from birthdays import (
    init_birthdays,
    birthday_command,
    birthday_check
)


from rules import rules

from trivia import trivia


from truth_dare import (
    truth,
    dare
)



# ==========================================================
# RAFFLE
# ==========================================================

from raffle import (

    start_raffle,
    paid_entry,
    raffle_status,
    raffle_entries,
    pending_entries,
    approve_raffle_entry,
    deny_raffle_entry,
    draw_raffle,
    reroll_raffle,
    cancel_raffle,
    bonus_entry,
    remove_raffle_entry

)



# ==========================================================
# DATABASE
# ==========================================================

from database import initialize_database

from raffle_database import initialize_raffle_database



# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",

    level=logging.INFO

)


logger = logging.getLogger(__name__)



# ==========================================================
# FLASK KEEP ALIVE
# ==========================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "🔥 Melanated AZ Bot Running"



def run_web():

    app.run(

        host="0.0.0.0",

        port=10000

    )



# ==========================================================
# STARTUP MESSAGE
# ==========================================================

async def startup(application):

    logger.info(
        "🔥 Melanated AZ Bot Online"
    )


    if STARTUP_CHAT_ID:

        try:

            await application.bot.send_message(

                chat_id=int(STARTUP_CHAT_ID),

                text="""
🟢 Melanated AZ Bot Online

🛡 Media Protection: ACTIVE
🎂 Birthday System: ACTIVE
🔥 Truth & Dare: ACTIVE
🎟 Raffle System: ACTIVE

Bot is ready!
"""

            )


        except Exception as e:

            logger.error(
                f"Startup message failed: {e}"
            )



# ==========================================================
# MAIN
# ==========================================================

def main():


    Thread(

        target=run_web,

        daemon=True

    ).start()



    initialize_database()

    initialize_raffle_database()

    init_birthdays()



    application = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .post_init(startup)

        .build()

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



    # ======================================================
    # BIRTHDAYS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "birthday",
            birthday_command
        )
    )


    application.add_handler(
        CommandHandler(
            "birthdaycheck",
            birthday_check
        )
    )



    # ======================================================
    # COMMUNITY
    # ======================================================

    application.add_handler(
        CommandHandler(
            "rules",
            rules
        )
    )


    application.add_handler(
        CommandHandler(
            "trivia",
            trivia
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
    # RAFFLE COMMANDS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "paid",
            paid_entry
        )
    )


    application.add_handler(
        CommandHandler(
            "rafflestatus",
            raffle_status
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
            "pendingraffles",
            pending_entries
        )
    )


    application.add_handler(
        CommandHandler(
            "approveentry",
            approve_raffle_entry
        )
    )


    application.add_handler(
        CommandHandler(
            "denyentry",
            deny_raffle_entry
        )
    )


    application.add_handler(
        CommandHandler(
            "drawraffle",
            draw_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "rerollraffle",
            reroll_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "cancelraffle",
            cancel_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "bonusentry",
            bonus_entry
        )
    )


    application.add_handler(
        CommandHandler(
            "removeentry",
            remove_raffle_entry
        )
    )



    # ======================================================
    # MEDIA
    # ======================================================

    application.add_handler(

        MessageHandler(

            filters.PHOTO | filters.VIDEO,

            check_media

        )

    )



    # ======================================================
    # WELCOME
    # ======================================================

    application.add_handler(

        ChatMemberHandler(

            welcome,

            ChatMemberHandler.CHAT_MEMBER

        )

    )



    print(
        "🔥 Melanated AZ Bot Started"
    )



    application.run_polling(

        drop_pending_updates=True

    )




if __name__ == "__main__":

    main()
