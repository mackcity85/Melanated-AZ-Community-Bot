import logging
import threading
import os


from flask import Flask


from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)


from config import TOKEN, STARTUP_CHAT_ID


from database import init_db


from moderation import check_media


from birthdays import (
    set_birthday,
    my_birthday,
    remove_birthday
)


from welcome import welcome_new_member


from admin import (
    get_id,
    announce
)


from polls import suggestion


from scheduler import start_scheduler


from inactivity import track_activity



# ==========================
# LOGGING
# ==========================

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s - %(levelname)s - %(message)s"

)



# ==========================
# FLASK SERVER
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

                "🤖 Melanated AZ Community Bot is running!\n\n"

                "✅ Media Spoiler Protection\n"

                "✅ Birthday Celebrations\n"

                "✅ Member Activity Tracking\n"

                "✅ Welcome System\n"

                "✅ Community Feedback\n"

                "✅ Automation Enabled\n\n"

                "💜 Ready to serve the community!"

            )

        )



# ==========================
# POST INIT
# ==========================

async def post_startup(app):


    logging.info(

        "🚀 Starting scheduler..."

    )


    await start_scheduler(app)


    await startup_message(app)



    logging.info(

        "✅ Startup tasks completed"

    )



# ==========================
# MAIN
# ==========================

def main():


    if not TOKEN:

        raise RuntimeError(

            "BOT_TOKEN is missing"

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

        .post_init(post_startup)

        .build()

    )



    # ======================
    # ACTIVITY TRACKING
    # ======================

    application.add_handler(

        MessageHandler(

            filters.ALL,

            track_activity

        ),

        group=0

    )



    # ======================
    # MEDIA MODERATION
    # ======================

    media_filter = (

        filters.PHOTO

        | filters.VIDEO

        | filters.ANIMATION

        | filters.Document.IMAGE

        | filters.Document.VIDEO

    )


    application.add_handler(

        MessageHandler(

            media_filter,

            check_media

        ),

        group=1

    )



    # ======================
    # COMMANDS
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


    application.add_handler(

        CommandHandler(

            "getid",

            get_id

        )

    )


    application.add_handler(

        CommandHandler(

            "announce",

            announce

        )

    )


    application.add_handler(

        CommandHandler(

            "suggestion",

            suggestion

        )

    )



    # ======================
    # WELCOME
    # ======================

    application.add_handler(

        MessageHandler(

            filters.StatusUpdate.NEW_CHAT_MEMBERS,

            welcome_new_member

        )

    )



    print(

        "🤖 Melanated AZ Community Bot is running!"

    )



    application.run_polling(

        drop_pending_updates=True

    )



if __name__ == "__main__":

    main()
