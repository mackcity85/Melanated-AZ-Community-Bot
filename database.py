# ==========================================================
# Melanated AZ Bot
# database.py
# SQLite Database Manager
# ==========================================================

import sqlite3
from datetime import datetime, timedelta


DB_NAME = "melanatedaz.db"



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


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        raffle TEXT,
        entered_date TEXT
    )
    """)


    conn.commit()
    conn.close()



# ==========================================================
# UPDATE MEMBER ACTIVITY
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
# GET INACTIVE MEMBERS
# ==========================================================

def get_inactive_members(
    days=30
):

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

    WHERE last_active < ?

    """,

    (cutoff,))


    rows = cursor.fetchall()

    conn.close()



    return [

        {
            "user_id": r[0],
            "first_name": r[1]
        }

        for r in rows

    ]



# ==========================================================
# GET ACTIVE MEMBERS
# ==========================================================

def get_active_members(
    days=30
):

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

    (cutoff,))


    rows = cursor.fetchall()

    conn.close()



    return [

        {
            "user_id": r[0],
            "first_name": r[1]
        }

        for r in rows

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
            "first_name": r[0],
            "birthday": r[1]
        }

        for r in rows

    ]
