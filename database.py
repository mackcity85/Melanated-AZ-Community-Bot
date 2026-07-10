import sqlite3

from config import DB_FILE



def get_connection():

    return sqlite3.connect(
        DB_FILE
    )



def init_db():

    conn = get_connection()

    cursor = conn.cursor()


    # Birthdays

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


    # Suggestions

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS suggestions
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            suggestion TEXT,
            created TEXT
        )
        """
    )


    # Pin tracking

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pinned_messages
        (
            chat_id INTEGER,
            message_id INTEGER,
            pinned_date TEXT
        )
        """
    )


    conn.commit()

    conn.close()
