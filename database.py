import sqlite3
import logging

from config import DB_FILE


def init_db():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    # ==========================
    # BIRTHDAYS
    # ==========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS birthdays (

            user_id INTEGER,
            chat_id INTEGER,
            username TEXT,
            birthday TEXT,

            PRIMARY KEY (
                user_id,
                chat_id
            )

        )
        """
    )


    # ==========================
    # RAFFLES
    # ==========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raffles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id INTEGER,

            prize TEXT,

            amount TEXT,

            active INTEGER DEFAULT 1

        )
        """
    )


    # ==========================
    # RAFFLE ENTRIES
    # ==========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raffle_entries (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            raffle_id INTEGER,

            user_id INTEGER,

            username TEXT,

            UNIQUE(
                raffle_id,
                user_id
            )

        )
        """
    )


    conn.commit()

    conn.close()


    logging.info(
        "✅ Database initialized"
    )
