import sqlite3
import logging

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import DB_FILE



async def set_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        if not context.args:

            await update.message.reply_text(
                "🎂 Use:\n\n"
                "/birthday MM/DD\n\n"
                "Example:\n"
                "/birthday 07/15"
            )

            return


        birthday = context.args[0]


        datetime.strptime(
            birthday,
            "%m/%d"
        )


        user = update.effective_user
        chat = update.effective_chat


        conn = sqlite3.connect(
            DB_FILE
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT OR REPLACE INTO birthdays
            (
                user_id,
                chat_id,
                username,
                birthday
            )
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
            "🎉 Birthday saved!\n\n"
            f"📅 {birthday}"
        )


    except Exception as e:

        logging.exception(
            "Birthday save failed"
        )


        await update.message.reply_text(
            f"❌ Birthday error:\n{e}"
        )



async def my_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat


    conn = sqlite3.connect(
        DB_FILE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT birthday
        FROM birthdays
        WHERE user_id=?
        AND chat_id=?
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
            f"🎂 Your birthday is:\n\n"
            f"📅 {result[0]}"
        )

    else:

        await update.message.reply_text(
            "No birthday saved.\n\n"
            "Use:\n"
            "/birthday MM/DD"
        )



async def remove_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat


    conn = sqlite3.connect(
        DB_FILE
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM birthdays
        WHERE user_id=?
        AND chat_id=?
        """,
        (
            user.id,
            chat.id
        )
    )


    conn.commit()
    conn.close()


    await update.message.reply_text(
        "✅ Birthday removed."
    )
