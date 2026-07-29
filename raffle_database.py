# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# ==========================================================

from datetime import datetime

from database import get_db



# ==========================================================
# INIT TABLES
# ==========================================================

def initialize_raffle_database():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prize TEXT,
        active INTEGER DEFAULT 1,
        created TEXT,
        end_time TEXT
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
        entered_date TEXT
    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_winners
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raffle_id INTEGER,
        user_id INTEGER,
        username TEXT,
        won_date TEXT
    )
    """)



    conn.commit()

    conn.close()



# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    end_time
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO raffles
    (
        prize,
        created,
        end_time
    )

    VALUES (?,?,?)
    """,

    (
        prize,
        datetime.now().isoformat(),
        end_time
    ))


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


    cursor.execute("""
    SELECT
        id,
        prize

    FROM raffles

    WHERE active=1

    ORDER BY id DESC

    LIMIT 1
    """)


    result = cursor.fetchone()


    conn.close()


    return result



# ==========================================================
# ADD PAYMENT ENTRY
# ==========================================================

def add_payment_entry(
    raffle_id,
    user_id,
    username,
    method
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO raffle_entries
    (
        raffle_id,
        user_id,
        username,
        payment_method,
        entered_date
    )

    VALUES (?,?,?,?,?)
    """,

    (
        raffle_id,
        user_id,
        username,
        method,
        datetime.now().isoformat()
    ))


    conn.commit()

    conn.close()



# ==========================================================
# PENDING ENTRIES
# ==========================================================

def get_pending_entries():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        id,
        username,
        payment_method

    FROM raffle_entries

    WHERE approved=0
    """)


    rows = cursor.fetchall()


    conn.close()


    return rows



# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    UPDATE raffle_entries

    SET approved=1

    WHERE id=?
    """,

    (
        entry_id,
    ))


    conn.commit()

    conn.close()



# ==========================================================
# GET APPROVED ENTRIES
# ==========================================================

def get_entries(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        user_id,
        username

    FROM raffle_entries

    WHERE raffle_id=?
    AND approved=1
    """,

    (
        raffle_id,
    ))


    rows = cursor.fetchall()


    conn.close()


    return rows



# ==========================================================
# EXPIRED RAFFLES
# ==========================================================

def get_expired_raffles():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        id,
        prize

    FROM raffles

    WHERE active=1
    AND end_time <= ?

    """,

    (
        datetime.now().isoformat(),
    ))


    rows = cursor.fetchall()


    conn.close()


    return rows



# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(
    raffle_id
):

    conn = get_db()

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
