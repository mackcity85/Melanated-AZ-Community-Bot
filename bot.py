# ==========================================================
# Melanated AZ Bot
# bot.py
# Main Launcher
# ==========================================================

import os
import logging

from threading import Thread

from dotenv import load_dotenv
from flask import Flask


from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters
)


# ==========================================================
# ENV
# ==========================================================

load_dotenv()


TOKEN = os.getenv(
    "BOT_TOKEN"
)


STARTUP_CHAT_ID = os.getenv(
    "STARTUP_CHAT_ID"
)


if not TOKEN:

    raise ValueError(
        "BOT_TOKEN missing"
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
# RAFFLE IMPORTS
# ==========================================================


from raffle import (

    start_raffle,

    enter_raffle,

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



from raffle_scheduler import (
    start_raffle_scheduler
)



# ==========================================================
# DATABASE INIT
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
# KEEP ALIVE
# ==========================================================


app = Flask(__name__)



@app.route("/")

def home():

    return "Melanated AZ Bot Running"




def run_web():

    app.run(

        host="0.0.0.0",

        port=int(

            os.getenv(
                "PORT",
                10000
            )

        )

    )




# ==========================================================
# STARTUP MESSAGE
# ==========================================================


async def startup_message(application):


    if STARTUP_CHAT_ID:


        try:


            await application.bot.send_message(

                chat_id=int(
                    STARTUP_CHAT_ID
                ),


                text=

                """
🟢 Melanated AZ Bot Online

🛡 Media Protection Active
🎂 Birthday System Active
🔥 Truth or Dare Active
🎟 Raffle System Active
                """

            )


        except Exception as e:


            logger.warning(
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

        .token(TOKEN)

        .post_init(startup_message)

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
    # COMMUNITY COMMANDS
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
            "enter",
            enter_raffle
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



    # Start automatic raffle checking

    start_raffle_scheduler(
        application
    )



    # ======================================================
    # MEDIA PROTECTION
    # ======================================================


    application.add_handler(

        MessageHandler(

            filters.PHOTO | filters.VIDEO,

            check_media

        ),

        group=0

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
        "🟢 Melanated AZ Bot Started"
    )



    application.run_polling(

        allowed_updates=None,

        drop_pending_updates=True

    )




if __name__ == "__main__":

    main()
