import os
import threading
import logging
import sqlite3

from datetime import datetime

from flask import Flask

from telegram import Update

from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler


# ==========================
# CONFIG
# ==========================

TOKEN = os.getenv("BOT_TOKEN")

DB_FILE = "birthdays.db"


WARNING = """⚠️ Media Removed

This group requires all pictures, videos, GIFs, and media files to be sent using Telegram's Hide with Spoiler option.

Please resend your media with the spoiler enabled.

Thank you for helping keep the group comfortable for everyone. 🙏
"""


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



# ==========================
# DATABASE
# ==========================

def init_db():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays (
        user_id INTEGER,
        chat_id INTEGER,
        username TEXT,
        birthday TEXT,
        PRIMARY KEY(user_id, chat_id)
    )
    """)

    conn.commit()
    conn.close()



# ==========================
# WEB SERVER (RENDER)
# ==========================

web_app = Flask(__name__)


@web_app.route("/")
def home():

    return "Melanated AZ Bot is running!"



def run_web():

    port = int(os.environ.get("PORT", 10000))

    web_app.run(
        host="0.0.0.0",
        port=port
    )



# ==========================
# GET CHAT ID
# ==========================

async def get_id(update, context):

    await update.message.reply_text(
        f"Chat ID: {update.effective_chat.id}"
    )



# ==========================
# BIRTHDAY SYSTEM
# ==========================

async def set_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "Usage:\n/birthday MM/DD\nExample:\n/birthday 07/15"
        )

        return


    birthday = context.args[0]


    try:

        datetime.strptime(
            birthday,
            "%m/%d"
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid date format. Use MM/DD"
        )

        return


    user = update.effective_user
    chat = update.effective_chat


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT OR REPLACE INTO birthdays
        VALUES (?, ?, ?, ?)
        """,
        (
            user.id,
            chat.id,
            user.first_name,
            birthday
        )
    )


    conn.commit()
    conn.close()


    await update.message.reply_text(
        f"🎂 Birthday saved for {birthday}!"
    )



async def my_birthday(update, context):

    user = update.effective_user
    chat = update.effective_chat


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT birthday
        FROM birthdays
        WHERE user_id=? AND chat_id=?
        """,
        (
            user.id,
            chat.id
        )
    )


    result = cursor.fetchone()

    conn.close()


    if result:

        await update.message.reply_text(
            f"🎂 Your birthday is {result[0]}"
        )

    else:

        await update.message.reply_text(
            "You have not set your birthday yet."
        )



async def remove_birthday(update, context):

    user = update.effective_user
    chat = update.effective_chat


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM birthdays
        WHERE user_id=? AND chat_id=?
        """,
        (
            user.id,
            chat.id
        )
    )


    conn.commit()
    conn.close()


    await update.message.reply_text(
        "✅ Your birthday has been removed."
    )



async def check_birthdays(context):

    today = datetime.now().strftime("%m/%d")


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT username, chat_id
        FROM birthdays
        WHERE birthday=?
        """,
        (today,)
    )


    birthdays = cursor.fetchall()

    conn.close()


    for username, chat_id in birthdays:

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🎉🎂 Happy Birthday {username}! 🎂🎉\n\n"
                "Everyone help us wish them a wonderful birthday!\n"
                "May your day be filled with happiness and good energy. 🥳"
            )
        )



# ==========================
# MEDIA CHECK
# ==========================

async def check_media(update, context):

    message = update.effective_message

    if not message:
        return


    if not (
        message.photo
        or message.video
        or message.animation
        or message.document
    ):
        return


    try:

        member = await context.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )


        if member.status in [
            "administrator",
            "creator"
        ]:
            return


    except Exception:

        pass



    if message.has_media_spoiler:
        return


    try:

        await message.delete()

        await context.bot.send_message(
            chat_id=message.chat.id,
            text=WARNING
        )


        logging.info(
            "Removed non-spoiler media"
        )


    except Exception as e:

        logging.exception(e)



# ==========================
# START BOT
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


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    # Media

    app.add_handler(
        MessageHandler(
            filters.PHOTO
            | filters.VIDEO
            | filters.ANIMATION
            | filters.Document.IMAGE
            | filters.Document.VIDEO,
            check_media
        )
    )


    # Commands

    app.add_handler(
        CommandHandler(
            "getid",
            get_id
        )
    )

    app.add_handler(
        CommandHandler(
            "birthday",
            set_birthday
        )
    )

    app.add_handler(
        CommandHandler(
            "mybirthday",
            my_birthday
        )
    )

    app.add_handler(
        CommandHandler(
            "removebirthday",
            remove_birthday
        )
    )


    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        check_birthdays,
        "cron",
        hour=9,
        minute=0,
        args=[app]
    )

    scheduler.start()


    logging.info(
        "🎉 Melanated AZ Bot is running!"
    )


    app.run_polling(
        drop_pending_updates=True
    )



if __name__ == "__main__":
    main()
