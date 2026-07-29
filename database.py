# ==========================================================
# Melanated AZ Bot
# database.py
# SQLite Database Manager
# ==========================================================

import sqlite3

from datetime import datetime, timedelta

from config import DB_NAME



# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():

    conn = sqlite3.connect(
        DB_NAME
    )

    conn.row_factory = sqlite3.Row

    return conn



# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def initialize_database():

    conn = get_db()

    cursor = conn.cursor()


    # --------------------------
    # Members
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members
    (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        chat_id INTEGER,
        joined_date TEXT,
        last_active TEXT,
        birthday TEXT
    )
    """)



    # --------------------------
    # Raffles
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
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



    # --------------------------
    # Raffle Entries
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries
    (
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



    # --------------------------
    # Activities
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activities
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        event_date TEXT
    )
    """)



    conn.commit()

    conn.close()



# ==========================================================
# UPDATE MEMBER
# ==========================================================

def update_member(
    user_id,
    chat_id,
    username,
    first_name
):

    conn = get_db()

    cursor = conn.cursor()


    now = datetime.now().isoformat()


    cursor.execute("""

    INSERT INTO members
    (
        user_id,
        username,
        first_name,
        chat_id,
        joined_date,
        last_active
    )

    VALUES (?,?,?,?,?,?)

    ON CONFLICT(user_id)

    DO UPDATE SET

        username=?,
        first_name=?,
        last_active=?

    """,

    (
        user_id,
        username,
        first_name,
        chat_id,
        now,
        now,

        username,
        first_name,
        now
    ))


    conn.commit()

    conn.close()



# ==========================================================
# UPDATE ACTIVITY
# ==========================================================

def update_activity(
    user_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""

    UPDATE members

    SET last_active=?

    WHERE user_id=?

    """,

    (
        datetime.now().isoformat(),
        user_id
    ))


    conn.commit()

    conn.close()



# ==========================================================
# GET ACTIVE MEMBERS
# ==========================================================

def get_active_members(days=30):

    cutoff = (
        datetime.now()
        -
        timedelta(days=days)
    ).isoformat()


    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""

    SELECT user_id,
           first_name

    FROM members

    WHERE last_active >= ?

    """,

    (
        cutoff,
    ))


    rows = cursor.fetchall()

    conn.close()


    return [

        dict(row)

        for row in rows

    ]



# ==========================================================
# SAVE BIRTHDAY
# ==========================================================

def save_birthday(
    user_id,
    birthday
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""

    UPDATE members

    SET birthday=?

    WHERE user_id=?

    """,

    (
        birthday,
        user_id
    ))


    conn.commit()

    conn.close()



# ==========================================================
# GET TODAY BIRTHDAYS
# ==========================================================

def get_todays_birthdays():

    today = datetime.now().strftime(
        "%m-%d"
    )


    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""

    SELECT first_name,
           birthday

    FROM members

    WHERE birthday LIKE ?

    """,

    (
        f"%{today}",
    ))


    rows = cursor.fetchall()

    conn.close()


    return [

        dict(row)

        for row in rows

    ]



# ==========================================================
# RAFFLE FUNCTIONS
# ==========================================================

def create_raffle(
    prize,
    admin_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""

    INSERT INTO raffles

    (
        prize,
        created_by,
        created_at
    )

    VALUES (?,?,?)

    """,

    (
        prize,
        admin_id,
        datetime.now().isoformat()
    ))


    conn.commit()

    conn.close()



def get_active_raffle():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""

    SELECT *

    FROM raffles

    WHERE active=1

    LIMIT 1

    """)


    raffle = cursor.fetchone()

    conn.close()


    return dict(raffle) if raffle else None



def add_raffle_entry(
    raffle_id,
    user_id,
    username,
    display_name
):

    conn = get_db()

    cursor = conn.cursor()


    try:

        cursor.execute("""

        INSERT INTO raffle_entries

        (
            raffle_id,
            user_id,
            username,
            display_name,
            created_at
        )

        VALUES (?,?,?,?,?)

        """,

        (
            raffle_id,
            user_id,
            username,
            display_name,
            datetime.now().isoformat()
        ))


        conn.commit()

        result = True


    except sqlite3.IntegrityError:

        result = False


    conn.close()


    return result
