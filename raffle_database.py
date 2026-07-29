# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# Paid Raffle Database
# ==========================================================

import sqlite3

from datetime import datetime

from config import DB_NAME



# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():

    return sqlite3.connect(
        DB_NAME
    )



# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def initialize_raffle_database():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prize TEXT NOT NULL,
        description TEXT,
        active INTEGER DEFAULT 1,
        created TEXT
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

        payment_status TEXT DEFAULT 'PENDING',

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
    description=""
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO raffles
        (
            prize,
            description,
            created
        )

        VALUES (?,?,?)
        """,
        (
            prize,
            description,
            datetime.now().isoformat()
        )
    )


    raffle_id = cursor.lastrowid


    conn.commit()

    conn.close()


    return raffle_id



# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        prize,
        description

        FROM raffles

        WHERE active=1

        ORDER BY id DESC

        LIMIT 1
        """
    )


    result = cursor.fetchone()


    conn.close()


    return result



# ==========================================================
# ADD PAYMENT ENTRY
# ==========================================================

def add_raffle_entry(
    raffle_id,
    user_id,
    username,
    payment_method
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
            payment_method,
            created
        )

        VALUES (?,?,?,?,?)
        """,
        (
            raffle_id,
            user_id,
            username,
            payment_method,
            datetime.now().isoformat()
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# PENDING PAYMENTS
# ==========================================================

def get_pending_entries():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        username,
        payment_method,
        created

        FROM raffle_entries

        WHERE approved=0

        ORDER BY id ASC
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

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffle_entries

        SET

        approved=1,

        payment_status='PAID'

        WHERE id=?
        """,
        (
            entry_id
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# DENY PAYMENT
# ==========================================================

def deny_entry(
    entry_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffle_entries

        SET

        payment_status='DENIED'

        WHERE id=?
        """,
        (
            entry_id
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# APPROVED ENTRIES
# ==========================================================

def get_approved_entries(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        username,
        user_id

        FROM raffle_entries

        WHERE raffle_id=?

        AND approved=1
        """,
        (
            raffle_id
        )
    )


    results = cursor.fetchall()


    conn.close()


    return results



# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(
    entry_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM raffle_entries

        WHERE id=?
        """,
        (
            entry_id
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# CLOSE RAFFLE
# ==========================================================

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
            raffle_id
        )
    )


    conn.commit()

    conn.close()



# ==========================================================
# EXPIRED RAFFLES
# ==========================================================

def get_expired_raffles():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        prize

        FROM raffles

        WHERE active=1
        """
    )


    results = cursor.fetchall()


    conn.close()


    return results
