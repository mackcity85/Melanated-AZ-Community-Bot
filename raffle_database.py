# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# Persistent Raffle Database
# ==========================================================

import sqlite3
from datetime import datetime

DB_NAME = "bot.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn



# ==========================================================
# INITIALIZE TABLES
# ==========================================================

def init_raffle_db():

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        prize TEXT NOT NULL,

        active INTEGER DEFAULT 1,

        created_by INTEGER,

        winner_id INTEGER,

        winner_name TEXT,

        created_at TEXT,

        completed_at TEXT

    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        raffle_id INTEGER,

        user_id INTEGER,

        username TEXT,

        display_name TEXT,

        entries INTEGER DEFAULT 1,

        created_at TEXT,

        UNIQUE(raffle_id,user_id)

    )
    """)


    conn.commit()
    conn.close()



# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(prize, admin_id):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

    INSERT INTO raffles
    (
        prize,
        active,
        created_by,
        created_at
    )

    VALUES (?,?,?,?)

    """,

    (
        prize,
        1,
        admin_id,
        datetime.now().isoformat()
    ))


    conn.commit()
    conn.close()



# ==========================================================
# GET ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

    SELECT *

    FROM raffles

    WHERE active = 1

    LIMIT 1

    """)


    raffle = cursor.fetchone()

    conn.close()


    return dict(raffle) if raffle else None



# ==========================================================
# ADD ENTRY
# ==========================================================

def add_entry(
    raffle_id,
    user_id,
    username,
    display_name
):

    conn = get_connection()

    cursor = conn.cursor()


    try:

        cursor.execute("""

        INSERT INTO raffle_entries

        (
            raffle_id,
            user_id,
            username,
            display_name,
            entries,
            created_at
        )

        VALUES (?,?,?,?,?,?)

        """,

        (
            raffle_id,
            user_id,
            username,
            display_name,
            1,
            datetime.now().isoformat()
        ))


        conn.commit()

        result = True


    except sqlite3.IntegrityError:

        result = False



    conn.close()


    return result



# ==========================================================
# GET ENTRIES
# ==========================================================

def get_entries(raffle_id):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

    SELECT *

    FROM raffle_entries

    WHERE raffle_id=?

    """,

    (raffle_id,))


    rows = cursor.fetchall()


    conn.close()


    return [dict(row) for row in rows]



# ==========================================================
# ENTRY COUNT
# ==========================================================

def count_entries(raffle_id):

    entries = get_entries(raffle_id)

    total = 0


    for entry in entries:

        total += entry["entries"]


    return total



# ==========================================================
# ADD BONUS ENTRIES
# ==========================================================

def add_bonus(
    raffle_id,
    user_id,
    amount
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

    UPDATE raffle_entries

    SET entries = entries + ?

    WHERE raffle_id=?

    AND user_id=?

    """,

    (
        amount,
        raffle_id,
        user_id
    ))


    conn.commit()

    conn.close()



# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(
    raffle_id,
    user_id
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

    DELETE FROM raffle_entries

    WHERE raffle_id=?

    AND user_id=?

    """,

    (
        raffle_id,
        user_id
    ))


    conn.commit()

    conn.close()



# ==========================================================
# SAVE WINNER
# ==========================================================

def save_winner(
    raffle_id,
    user_id,
    name
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

    UPDATE raffles

    SET

    winner_id=?,

    winner_name=?,

    active=0,

    completed_at=?

    WHERE id=?

    """,

    (
        user_id,
        name,
        datetime.now().isoformat(),
        raffle_id
    ))


    conn.commit()

    conn.close()



# ==========================================================
# CANCEL RAFFLE
# ==========================================================

def cancel_raffle(
    raffle_id
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""

    UPDATE raffles

    SET active=0

    WHERE id=?

    """,

    (raffle_id,))


    conn.commit()

    conn.close()
