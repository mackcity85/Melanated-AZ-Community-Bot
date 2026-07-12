# ==========================================================
# Melanated AZ Bot
# bot.py
# ==========================================================

import os
import logging
import threading


from flask import Flask
from dotenv import load_dotenv


from telegram import Update


from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)



from database import (
    initialize_database,
    update_member
)



from welcome import (
    welcome_new_member,
    intro,
    help_command
)



from rules import rules



from raffle import (
    raffle,
    join_raffle_command,
    create_raffle_command,
    draw_raffle
)



# ==========================================================
# CONFIG
# ==========================================================

load_dotenv()


TOKEN = os.getenv(
    "BOT_TOKEN"
)



# Admin Telegram IDs
# Add yours in .env

ADMIN_IDS = [
    int(x)
    for x in os.getenv(
        "ADMIN_IDS",
        ""
    ).split(",")
    if x
]



logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)



# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(
    user_id
):

    return user_id in ADMIN_IDS



# ==========================================================
# FLASK HEALTH CHECK
# ==========================================================

flask_app = Flask(__name__)



@flask_app.route("/")
def health():

    return (
        "Melanated AZ Bot is running"
    )



def run_flask():

    port = int(
        os.getenv(
            "PORT",
            10000
        )
    )


    flask_app.run(
        host="0.0.0.0",
        port=port
    )



# ==========================================================
# START
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
🔥 Melanated AZ Bot Online 🔥

Welcome!

Commands:

/rules
/help
/intro

🎲 Activities
🎂 Birthdays
🎟️ Raffles
"""
    )



# ==========================================================
# MEMBER ACTIVITY TRACKING
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
# MEDIA SPOILER PROTECTION
# ==========================================================

async def media_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message


    if not message:
        return



    has_media = (

        message.photo
        or message.video
        or message.animation
        or message.document

    )


    if has_media:


        if not message.has_media_spoiler:


            try:

                await message.delete()


                await context.bot.send_message(
                    chat_id=message.chat.id,
                    text=(
                        f"⚠️ {message.from_user.first_name}, "
                        "please use Telegram Spoiler protection "
                        "for photos and videos."
                    )
                )


            except Exception as e:

                logging.error(
                    f"Media error: {e}"
                )



# ==========================================================
# MAIN
# ==========================================================

def main():


    if not TOKEN:

        raise Exception(
            "BOT_TOKEN missing"
        )



    initialize_database()



    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()



    application = (

        Application
        .builder()
        .token(TOKEN)
        .build()

    )



    # --------------------------
    # Commands
    # --------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start
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
            "help",
            help_command
        )
    )


    application.add_handler(
        CommandHandler(
            "intro",
            intro
        )
    )



    # --------------------------
    # Raffles
    # --------------------------

    application.add_handler(
        CommandHandler(
            "raffle",
            raffle
        )
    )


    application.add_handler(
        CommandHandler(
            "joinraffle",
            join_raffle_command
        )
    )


    application.add_handler(
        CommandHandler(
            "createraffle",
            create_raffle_command
        )
    )


    application.add_handler(
        CommandHandler(
            "drawraffle",
            draw_raffle
        )
    )



    # --------------------------
    # Welcome New Members
    # --------------------------

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )



    # --------------------------
    # Media Protection
    # --------------------------

    application.add_handler(
        MessageHandler(
            filters.PHOTO |
            filters.VIDEO |
            filters.ANIMATION |
            filters.Document.ALL,
            media_check
        )
    )



    # --------------------------
    # Activity Tracking
    # --------------------------

    application.add_handler(
        MessageHandler(
            filters.ALL,
            activity_tracker
        ),
        group=10
    )



    print(
        "Melanated AZ Bot is running"
    )



    application.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":

    main()
