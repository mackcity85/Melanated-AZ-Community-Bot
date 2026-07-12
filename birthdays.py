# ==========================================================
# Melanated AZ Bot
# birthdays.py
# Birthday System - MM/DD Format
# ==========================================================

import sqlite3
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import DATABASE


logger = logging.getLogger(__name__)


# ==========================================================
# DATABASE INIT
# ==========================================================

def init_birthdays():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays
    (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        birthday TEXT
    )
    """)

    conn.commit()
    conn.close()



# ==========================================================
# /birthday MM/DD
# ==========================================================

async def birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not context.args:

        await update.message.reply_text(
            """
🎂 Birthday Setup

Use:

/birthday MM/DD

Example:

/birthday 07/25
"""
        )

        return



    birthday_date = context.args[0]


    try:

        datetime.strptime(
            birthday_date,
            "%m/%d"
        )

    except ValueError:

        await update.message.reply_text(
            """
❌ Invalid format.

Please use:

/birthday 07/25
"""
        )

        return



    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO birthdays
    (
        user_id,
        username,
        first_name,
        birthday
    )

    VALUES (?,?,?,?)

    ON CONFLICT(user_id)

    DO UPDATE SET

        username=excluded.username,
        first_name=excluded.first_name,
        birthday=excluded.birthday

    """,
    (
        user.id,
        user.username,
        user.first_name,
        birthday_date
    ))


    conn.commit()
    conn.close()



    await update.message.reply_text(
        f"""
🎂 Birthday Saved!

Your birthday: {birthday_date}

Thank you for sharing with Melanated AZ ❤️
"""
    )



# ==========================================================
# CHECK TODAY'S BIRTHDAYS
# ==========================================================

async def birthdaycheck(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    today = datetime.now().strftime(
        "%m/%d"
    )


    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()


    cursor.execute("""
    SELECT first_name, username
    FROM birthdays
    WHERE birthday = ?
    """,
    (today,))


    results = cursor.fetchall()

    conn.close()



    if not results:

        await update.message.reply_text(
            "🎂 No birthdays today."
        )

        return



    message = "🎉 Today's Birthdays 🎉\n\n"


    for user in results:

        name = (
            user[0]
            or user[1]
            or "Member"
        )

        message += f"🎂 {name}\n"



    await update.message.reply_text(
        message
    )
