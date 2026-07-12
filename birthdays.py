# ==========================================================
# Melanated AZ Bot
# birthdays.py
# Birthday Management (MM/DD)
# ==========================================================

import sqlite3
from datetime import datetime

DB_FILE = "melanatedaz.db"


# ==========================================================
# DATABASE SETUP
# ==========================================================

def init_birthdays():

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        birthday TEXT
    )
    """)

    conn.commit()
    conn.close()



# ==========================================================
# SAVE BIRTHDAY
# Format: MM/DD
# ==========================================================

def save_birthday(
    user_id,
    username,
    first_name,
    birthday
):

    try:

        datetime.strptime(
            birthday,
            "%m/%d"
        )

    except ValueError:

        return False



    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO birthdays
    (
        user_id,
        username,
        first_name,
        birthday
    )
    VALUES (?,?,?,?)

    ON CONFLICT(user_id)
    DO UPDATE SET

        username=excluded.username,
        first_name=excluded.first_name,
        birthday=excluded.birthday

    """,
    (
        user_id,
        username,
        first_name,
        birthday
    ))


    conn.commit()
    conn.close()

    return True



# ==========================================================
# GET TODAY'S BIRTHDAYS
# ==========================================================

def get_today_birthdays():

    today = datetime.now().strftime("%m/%d")


    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        user_id,
        username,
        first_name
    FROM birthdays
    WHERE birthday = ?
    """,
    (
        today,
    ))


    results = cursor.fetchall()


    conn.close()


    return results



# ==========================================================
# GET USER BIRTHDAY
# ==========================================================

def get_birthday(user_id):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()


    cursor.execute("""
    SELECT birthday
    FROM birthdays
    WHERE user_id = ?
    """,
    (
        user_id,
    ))


    result = cursor.fetchone()


    conn.close()


    if result:
        return result[0]


    return None



# ==========================================================
# DELETE BIRTHDAY
# ==========================================================

def delete_birthday(user_id):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()


    cursor.execute("""
    DELETE FROM birthdays
    WHERE user_id = ?
    """,
    (
        user_id,
    ))


    conn.commit()
    conn.close()
