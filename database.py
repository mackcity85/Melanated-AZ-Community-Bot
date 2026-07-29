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

    return sqlite3.connect(
        DB_NAME
    )



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
    # Raffle Entries
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        raffle TEXT,
        entered_date TEXT
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



    # --------------------------
    # Truth Dare Settings
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS truth_dare_settings
    (
        id INTEGER PRIMARY KEY,
        enabled INTEGER DEFAULT 1
    )
    """)



    cursor.execute("""
    INSERT OR IGNORE INTO truth_dare_settings
    (
        id,
        enabled
    )

    VALUES
    (
        1,
        1
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

def get_active_members(
    days=30
):

    cutoff = (

        datetime.now()

        -
        timedelta(
            days=days
        )

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

        {
            "user_id": row[0],
            "first_name": row[1]
        }

        for row in rows

    ]





# ==========================================================
# GET INACTIVE MEMBERS
# ==========================================================

def get_inactive_members(
    days=30
):

    cutoff = (

        datetime.now()

        -
        timedelta(
            days=days
        )

    ).isoformat()



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute("""

    SELECT user_id,
           first_name

    FROM members

    WHERE last_active < ?

    """,

    (
        cutoff,
    ))



    rows = cursor.fetchall()

    conn.close()



    return [

        {
            "user_id": row[0],
            "first_name": row[1]
        }

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

        {
            "first_name": row[0],
            "birthday": row[1]
        }

        for row in rows

    ]





# ==========================================================
# ADD RAFFLE ENTRY
# ==========================================================

def add_raffle_entry(
    user_id,
    username,
    raffle
):

    conn = get_db()

    cursor = conn.cursor()



    cursor.execute("""

    INSERT INTO raffle_entries
    (
        user_id,
        username,
        raffle,
        entered_date
    )

    VALUES (?,?,?,?)

    """,

    (
        user_id,
        username,
        raffle,
        datetime.now().isoformat()
    ))



    conn.commit()

    conn.close()
