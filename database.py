import sqlite3
import os
import logging

from config import DB_FILE


def init_db():

    try:

        # Create folder if needed
        db_folder = os.path.dirname(DB_FILE)

        if db_folder and not os.path.exists(db_folder):

            os.makedirs(
                db_folder,
                exist_ok=True
            )


        conn = sqlite3.connect(DB_FILE)

        cursor = conn.cursor()


        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS birthdays
            (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                username TEXT,
                birthday TEXT,
                PRIMARY KEY(user_id, chat_id)
            )
            """
        )


        conn.commit()
        conn.close()


        logging.info(
            "✅ Database initialized"
        )


    except Exception as e:

        logging.exception(
            "❌ Database initialization failed: %s",
            e
        )

        raise
