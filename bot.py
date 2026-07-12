import os
import logging
import threading
import asyncio

from dotenv import load_dotenv
from flask import Flask

from database import (
    initialize_database,
    update_member,
    save_birthday
)

from birthday_scheduler import birthday_check
from activity_scheduler import activity_check


from admin import (
    announce,
    botstatus,
    members
)


from pin_cleanup import (
    pinmessage,
    unpinold,
    pin_cleanup_task
)


from welcome import (
    welcome_new_member,
    intro
)


from trivia import (
    trivia,
    trivia_answer
)


from truth_dare import (
    truth,
    dare
)



from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ChatMemberHandler,
    filters
)



# ==========================================================
# CONFIG
# ==========================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)



# ==========================================================
# FLASK HEALTH CHECK
# ==========================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def health():

    return "Melanated AZ Bot is running"



def run_flask():

    port = int(
        os.getenv("PORT", 10000)
    )

    flask_app.run(
        host="0.0.0.0",
        port=port
    )



# ==========================================================
# BASIC COMMANDS
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔥 Melanated AZ Bot Online\n\n"
        "🛡 Spoiler Protection\n"
        "🎂 Birthdays\n"
        "👋 Welcome System\n"
        "🎲 Games Active\n\n"
        "Use /rules"
    )



async def rules(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📜 Melanated AZ Rules\n\n"
        "1. Respect everyone.\n"
        "2. No harassment or drama.\n"
        "3. Adults only community.\n"
        "4. Follow admin instructions.\n"
        "5. Media must use spoiler protection."
    )



# ==========================================================
# BIRTHDAY
# ==========================================================

async def birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "Use:\n/birthday MM/DD"
        )

        return


    update_member(
        update.effective_user.id,
        update.effective_chat.id,
        update.effective_user.username,
        update.effective_user.first_name
    )


    save_birthday(
        update.effective_user.id,
        update.effective_chat.id,
        context.args[0]
    )


    await update.message.reply_text(
        "🎂 Birthday saved!"
    )



# ==========================================================
# ACTIVITY TRACKING
# ==========================================================

async def track_activity(
    update,
    context
):

    if update.effective_user:

        update_member(
            update.effective_user.id,
            update.effective_chat.id,
            update.effective_user.username,
            update.effective_user.first_name
        )



# ==========================================================
# SPOILER PROTECTION
# ==========================================================

async def media_check(
    update,
    context
):

    message = update.message


    if not message:
        return


    media = (

        message.photo or
        message.video or
        message.animation or
        message.document

    )


    if media:

        if not message.has_media_spoiler:

            try:

                await message.delete()

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "⚠️ Media removed.\n"
                        "Please use Telegram spoiler protection."
                    )
                )

            except Exception as e:

                logging.error(e)



# ==========================================================
# STARTUP TASKS
# ==========================================================

async def startup(application):


    asyncio.create_task(
        birthday_check(application)
    )


    asyncio.create_task(
        activity_check(application)
    )


    asyncio.create_task(
        pin_cleanup_task(application)
    )



# ==========================================================
# MAIN
# ==========================================================

def main():


    if not TOKEN:

        raise Exception(
            "BOT_TOKEN missing"
        )


    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()



    initialize_database()



    application = (
        Application
        .builder()
        .token(TOKEN)
        .post_init(startup)
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
            "rules",
            rules
        )
    )


    application.add_handler(
        CommandHandler(
            "birthday",
            birthday
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
            "botstatus",
            botstatus
        )
    )


    application.add_handler(
        CommandHandler(
            "members",
            members
        )
    )


    application.add_handler(
        CommandHandler(
            "pinmessage",
            pinmessage
        )
    )


    application.add_handler(
        CommandHandler(
            "unpinold",
            unpinold
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



    # Welcome new members

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )



    # Trivia answers

    application.add_handler(
        MessageHandler(
            filters.TEXT,
            trivia_answer
        ),
        group=1
    )



    # Media

    application.add_handler(
        MessageHandler(
            filters.PHOTO |
            filters.VIDEO |
            filters.ANIMATION |
            filters.Document.ALL,
            media_check
        )
    )



    # Activity

    application.add_handler(
        MessageHandler(
            filters.ALL,
            track_activity
        ),
        group=2
    )



    print(
        "Melanated AZ Bot is running"
    )


    application.run_polling()



if __name__ == "__main__":

    main()
