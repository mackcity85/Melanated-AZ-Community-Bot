import sqlite3
from config import DB_FILE


def init_db():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS birthdays
        (
            user_id INTEGER,
            chat_id INTEGER,
            username TEXT,
            birthday TEXT,
            PRIMARY KEY(user_id, chat_id)
        )
        """
    )


    conn.commit()
    conn.close()
