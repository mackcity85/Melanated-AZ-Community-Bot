# ==========================================================
# Melanated AZ Bot
# database.py
# ==========================================================

import sqlite3
import logging


DATABASE = "melanatedaz.db"



# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():

    return sqlite3.connect(
        DATABASE
    )



# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def initialize_database():

    conn = get_db()

    cursor = conn.cursor()



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members
    (
        user_id INTEGER,
        chat_id INTEGER,
        username TEXT,
        first_name TEXT,
        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, chat_id)
    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays
    (
        user_id INTEGER,
        chat_id INTEGER,
        birthday TEXT,
        first_name TEXT
    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        title TEXT,
        active INTEGER DEFAULT 1,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries
    (
        raffle_id INTEGER,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)



    conn.commit()

    conn.close()


    logging.info(
        "Database initialized"
    )



# ==========================================================
# MEMBER UPDATE
# ==========================================================

def update_member(
    user_id,
    chat_id,
    username,
    first_name
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO members
        (
            user_id,
            chat_id,
            username,
            first_name
        )

        VALUES (?,?,?,?)

        ON CONFLICT(user_id,chat_id)

        DO UPDATE SET

        last_active=CURRENT_TIMESTAMP

        """,

        (
            user_id,
            chat_id,
            username,
            first_name
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# RAFFLE FUNCTIONS
# ==========================================================

def create_raffle(
    chat_id,
    title
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffles

        SET active = 0

        WHERE chat_id=?

        """,
        (
            chat_id,
        )
    )


    cursor.execute(
        """
        INSERT INTO raffles
        (
            chat_id,
            title
        )

        VALUES (?,?)

        """,

        (
            chat_id,
            title
        )
    )


    raffle_id = cursor.lastrowid


    conn.commit()

    conn.close()


    return raffle_id



def get_active_raffle(
    chat_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT id,title

        FROM raffles

        WHERE chat_id=?
        AND active=1

        ORDER BY id DESC

        LIMIT 1

        """,

        (
            chat_id,
        )
    )


    result = cursor.fetchone()


    conn.close()


    return result



def join_raffle(
    raffle_id,
    user_id,
    username,
    first_name
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO raffle_entries
        (
            raffle_id,
            user_id,
            username,
            first_name
        )

        VALUES (?,?,?,?)

        """,

        (
            raffle_id,
            user_id,
            username,
            first_name
        )
    )


    conn.commit()

    conn.close()



def get_raffle_entries(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT user_id,username,first_name

        FROM raffle_entries

        WHERE raffle_id=?

        """,

        (
            raffle_id,
        )
    )


    results = cursor.fetchall()


    conn.close()


    return results



def close_raffle(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffles

        SET active=0

        WHERE id=?

        """,

        (
            raffle_id,
        )
    )


    conn.commit()

    conn.close()
