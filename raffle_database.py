# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# Raffle SQLite Database
# ==========================================================

import sqlite3
from datetime import datetime

from config import DB_NAME



# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():

    return sqlite3.connect(DB_NAME)



# ==========================================================
# INITIALIZE
# ==========================================================

def init_raffle_database():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prize TEXT,
        end_time TEXT,
        chat_id INTEGER,
        active INTEGER DEFAULT 1
    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raffle_id INTEGER,
        user_id INTEGER,
        username TEXT,
        payment_method TEXT,
        approved INTEGER DEFAULT 0,
        created TEXT
    )
    """)


    conn.commit()

    conn.close()



# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    end_time,
    chat_id
):

    init_raffle_database()

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO raffles
        (
            prize,
            end_time,
            chat_id
        )
        VALUES (?,?,?)
        """,
        (
            prize,
            end_time,
            chat_id
        )
    )


    raffle_id = cursor.lastrowid


    conn.commit()

    conn.close()


    return raffle_id



# ==========================================================
# GET ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    init_raffle_database()

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT id, prize, end_time
        FROM raffles
        WHERE active=1
        ORDER BY id DESC
        LIMIT 1
        """
    )


    raffle = cursor.fetchone()


    conn.close()


    return raffle



# ==========================================================
# ADD PAYMENT ENTRY
# ==========================================================

def add_payment_entry(
    raffle_id,
    user_id,
    username,
    payment_method
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO raffle_entries
        (
            raffle_id,
            user_id,
            username,
            payment_method,
            approved,
            created
        )

        VALUES (?,?,?,?,?,?)
        """,
        (
            raffle_id,
            user_id,
            username,
            payment_method,
            0,
            datetime.now().isoformat()
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# GET PENDING
# ==========================================================

def get_pending_entries():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            id,
            username,
            payment_method

        FROM raffle_entries

        WHERE approved=0

        ORDER BY id
        """
    )


    results = cursor.fetchall()


    conn.close()


    return results



# ==========================================================
# APPROVE PAYMENT
# ==========================================================

def approve_entry(
    entry_id
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffle_entries

        SET approved=1

        WHERE id=?
        """,
        (
            entry_id,
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# GET APPROVED ENTRIES
# ==========================================================

def get_entries(
    raffle_id
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            id,
            username

        FROM raffle_entries

        WHERE raffle_id=?

        AND approved=1
        """,
        (
            raffle_id,
        )
    )


    entries = cursor.fetchall()


    conn.close()


    return entries



# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(
    raffle_id
):

    conn = get_connection()

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



# ==========================================================
# EXPIRED RAFFLES
# ==========================================================

def get_expired_raffles():

    conn = get_connection()

    cursor = conn.cursor()


    now = datetime.now().isoformat()


    cursor.execute(
        """
        SELECT id, prize

        FROM raffles

        WHERE active=1

        AND end_time <= ?

        """,
        (
            now,
        )
    )


    results = cursor.fetchall()


    conn.close()


    return results
