import sqlite3
import logging

from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import DB_FILE



# ==========================
# HELP COMMAND
# ==========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "💜 Melanated AZ Bot Commands 💜\n\n"

        "🎂 Birthdays\n"
        "/birthday MM/DD\n"
        "/mybirthday\n"
        "/removebirthday\n\n"

        "🎟 Raffles\n"
        "/raffle_start\n"
        "/enter\n"
        "/raffle_list\n"
        "/raffle_draw\n"
        "/raffle_close\n\n"

        "⚙️ General\n"
        "/ping\n"
        "/getid\n"
        "/help"

    )



# ==========================
# ACTIVITY TRACKING
# ==========================

async def track_activity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:

        return


    user = update.effective_user
    chat = update.effective_chat


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity (

            user_id INTEGER,
            chat_id INTEGER,
            username TEXT,
            last_active TEXT,

            PRIMARY KEY(
                user_id,
                chat_id
            )

        )
        """
    )


    cursor.execute(
        """
        INSERT OR REPLACE INTO activity
        VALUES (?, ?, ?, ?)
        """,
        (
            user.id,
            chat.id,
            user.first_name,
            datetime.now().isoformat()
        )
    )


    conn.commit()

    conn.close()



# ==========================
# MONTHLY COMMUNITY CHECK
# ==========================

async def monthly_activity_check(
    app
):

    cutoff = datetime.now() - timedelta(
        days=30
    )


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT username, chat_id, last_active
        FROM activity
        """
    )


    members = cursor.fetchall()


    conn.close()


    active = []

    inactive = []


    for username, chat_id, last in members:

        last_date = datetime.fromisoformat(last)


        if last_date >= cutoff:

            active.append(
                (username, chat_id)
            )

        else:

            inactive.append(
                (username, chat_id)
            )



    # Thank active members

    for username, chat_id in active:

        try:

            await app.bot.send_message(

                chat_id,

                f"💜 Thank you {username}!\n\n"
                "We appreciate you being active "
                "in Melanated AZ! 🙌"

            )


        except Exception as e:

            logging.error(e)



    # Check inactive members

    for username, chat_id in inactive:

        try:

            await app.bot.send_message(

                chat_id,

                f"👋 Hey {username},\n\n"
                "We haven't seen you around lately.\n\n"
                "Just checking in to see how you are "
                "and if you would like to stay connected "
                "with Melanated AZ 💜"

            )


        except Exception as e:

            logging.error(e)



# ==========================
# RAFFLE HISTORY
# ==========================

async def raffle_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raffle_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prize TEXT,
            winner TEXT,
            date TEXT

        )
        """
    )


    cursor.execute(
        """
        SELECT prize, winner, date
        FROM raffle_history
        ORDER BY id DESC
        LIMIT 10
        """
    )


    results = cursor.fetchall()


    conn.close()



    if not results:

        await update.message.reply_text(

            "No raffle history yet."

        )

        return



    message = "🏆 Raffle History 🏆\n\n"


    for prize, winner, date in results:

        message += (

            f"🎁 {prize}\n"
            f"👑 {winner}\n"
            f"📅 {date}\n\n"

        )


    await update.message.reply_text(
        message
    )



# ==========================
# BIRTHDAY CHECK
# ==========================

async def birthday_check(
    app
):

    today = datetime.now().strftime(
        "%m/%d"
    )


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

        await app.bot.send_message(

            chat_id,

            "🎂🎉 HAPPY BIRTHDAY 🎉🎂\n\n"

            f"Today we celebrate {username}!\n\n"

            "Everyone show them some love 💜"

        )
