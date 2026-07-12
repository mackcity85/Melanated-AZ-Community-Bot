# ==========================================================
# Melanated AZ Bot
# Database Management
# ==========================================================

import sqlite3
from datetime import datetime


DATABASE = "bot.db"


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


    # Members table

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members
    (
        user_id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        username TEXT,
        first_name TEXT,
        joined_date TEXT,
        last_active TEXT
    )
    """)



    # Birthdays table

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays
    (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        birthday TEXT
    )
    """)



    # Activity table

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity
    (
        user_id INTEGER PRIMARY KEY,
        last_seen TEXT
    )
    """)



    conn.commit()
    conn.close()



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


    now = datetime.now().isoformat()


    cursor.execute("""
    INSERT INTO members
    (
        user_id,
        chat_id,
        username,
        first_name,
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
        chat_id,
        username,
        first_name,
        now,
        now,
        username,
        first_name,
        now
    ))


    conn.commit()
    conn.close()



# ==========================================================
# SAVE BIRTHDAY
# ==========================================================

def save_birthday(
    user_id,
    first_name,
    username,
    birthday
):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO birthdays
    (
        user_id,
        first_name,
        username,
        birthday
    )

    VALUES (?,?,?,?)

    ON CONFLICT(user_id)
    DO UPDATE SET

    first_name=?,
    username=?,
    birthday=?

    """,
    (
        user_id,
        first_name,
        username,
        birthday,
        first_name,
        username,
        birthday
    ))


    conn.commit()
    conn.close()



# ==========================================================
# GET TODAY BIRTHDAYS
# ==========================================================

def get_birthdays_today(
    today
):

    conn = get_db()
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute("""
    SELECT *
    FROM birthdays
    WHERE birthday=?
    """,
    (
        today,
    ))


    results = cursor.fetchall()


    conn.close()


    return results



# ==========================================================
# ACTIVITY UPDATE
# ==========================================================

def update_activity(
    user_id
):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO activity
    (
        user_id,
        last_seen
    )

    VALUES (?,?)

    ON CONFLICT(user_id)
    DO UPDATE SET

    last_seen=?

    """,
    (
        user_id,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))


    conn.commit()
    conn.close()
