import logging
import threading
import os

from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from config import TOKEN, STARTUP_CHAT_ID

from database import init_db

from birthdays import (
    set_birthday,
    my_birthday,
    remove_birthday
)

from raffles import (
    start_raffle,
    enter_raffle,
    raffle_list,
    draw_raffle,
    close_raffle
)


# ==========================
# LOGGING
# ==========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



# ==========================
# FLASK HEALTH CHECK
# ==========================

web_app = Flask(__name__)


@web_app.route("/")
def home():

    return "Melanated AZ Community Bot is running!"



def run_web():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )


    web_app.run(
        host="0.0.0.0",
        port=port
    )



# ==========================
# BASIC COMMANDS
# ==========================

async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "Melanated AZ Community Bot is online."
    )



async def get_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        f"👤 User ID: {update.effective_user.id}\n"
        f"💬 Chat ID: {update.effective_chat.id}"

    )



# ==========================
# STARTUP MESSAGE
# ==========================

async def startup_message(app):


    logging.info(
        "🤖 Melanated AZ Community Bot started"
    )


    if STARTUP_CHAT_ID:


        await app.bot.send_message(

            chat_id=STARTUP_CHAT_ID,

            text=(

                "💜 Melanated AZ Community Bot Online 💜\n\n"

                "✅ Database Connected\n"
                "✅ Birthday System Active\n"
                "✅ Raffle System Active\n"
                "✅ Admin Controls Enabled\n\n"

                "🚀 Ready to serve the community!"

            )

        )



# ==========================
# MAIN
# ==========================

def main():


    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN missing"
        )


    init_db()



    threading.Thread(

        target=run_web,

        daemon=True

    ).start()



    application = (

        Application

        .builder()

        .token(TOKEN)

        .post_init(startup_message)

        .build()

    )



    # ======================
    # TEST COMMANDS
    # ======================

    application.add_handler(
        CommandHandler(
            "ping",
            ping
        )
    )


    application.add_handler(
        CommandHandler(
            "getid",
            get_id
        )
    )



    # ======================
    # BIRTHDAYS
    # ======================

    application.add_handler(
        CommandHandler(
            "birthday",
            set_birthday
        )
    )


    application.add_handler(
        CommandHandler(
            "mybirthday",
            my_birthday
        )
    )


    application.add_handler(
        CommandHandler(
            "removebirthday",
            remove_birthday
        )
    )



    # ======================
    # RAFFLES
    # ======================

    application.add_handler(
        CommandHandler(
            "raffle_start",
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
            "raffle_list",
            raffle_list
        )
    )


    application.add_handler(
        CommandHandler(
            "raffle_draw",
            draw_raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "raffle_close",
            close_raffle
        )
    )



    logging.info(
        "🚀 Starting Telegram bot..."
    )



    application.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
