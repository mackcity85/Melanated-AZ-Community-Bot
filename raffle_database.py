# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# ==========================================================

import sqlite3

from datetime import datetime

from config import DB_NAME



def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn



def init_raffle_db():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prize TEXT,
        chat_id INTEGER,
        created_by INTEGER,
        end_time TEXT,
        active INTEGER DEFAULT 1,
        winner_id INTEGER,
        winner_name TEXT,
        created_at TEXT,
        completed_at TEXT
    )
    """)



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


    conn.commit()

    conn.close()



def create_raffle(
    prize,
    chat_id,
    admin_id,
    end_time
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO raffles
    (
        prize,
        chat_id,
        created_by,
        end_time,
        created_at
    )

    VALUES (?,?,?,?,?)
    """,
    (
        prize,
        chat_id,
        admin_id,
        end_time,
        datetime.now().isoformat()
    ))


    raffle_id = cursor.lastrowid


    conn.commit()

    conn.close()


    return raffle_id



def get_active_raffle():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT *
    FROM raffles
    WHERE active=1
    LIMIT 1
    """)


    row = cursor.fetchone()

    conn.close()


    return dict(row) if row else None



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



def get_entries(
    raffle_id
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT *
    FROM raffle_entries
    WHERE raffle_id=?
    """,
    (
        raffle_id,
    ))


    rows = cursor.fetchall()

    conn.close()


    return [
        dict(row)
        for row in rows
    ]



def get_expired_raffles():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT *
    FROM raffles
    WHERE active=1
    AND end_time <= ?
    """,
    (
        datetime.now().isoformat(),
    ))


    rows = cursor.fetchall()

    conn.close()


    return [
        dict(row)
        for row in rows
    ]



def save_winner(
    raffle_id,
    user_id,
    name
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
    UPDATE raffles

    SET active=0,
        winner_id=?,
        winner_name=?,
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
    (
        raffle_id,
    ))


    conn.commit()

    conn.close()
