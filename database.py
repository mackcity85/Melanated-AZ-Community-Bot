# ==========================================================
# RAFFLE DATABASE FUNCTIONS
# Melanated AZ Bot v3
# ==========================================================

import sqlite3


DATABASE = "melanatedaz.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():

    return sqlite3.connect(
        DATABASE
    )


# ==========================================================
# CREATE RAFFLE TABLES
# ==========================================================

def create_raffle_tables():

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        prize TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raffle_id INTEGER,
        user_id INTEGER,
        name TEXT,
        UNIQUE(raffle_id,user_id)
    )
    """)


    conn.commit()
    conn.close()



# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    chat_id,
    prize
):

    conn = get_db()
    cursor = conn.cursor()


    # close old raffles
    cursor.execute("""
    UPDATE raffles
    SET active=0
    WHERE chat_id=?
    """,
    (
        chat_id,
    ))


    cursor.execute("""
    INSERT INTO raffles
    (
        chat_id,
        prize
    )
    VALUES (?,?)
    """,
    (
        chat_id,
        prize
    ))


    conn.commit()
    conn.close()



# ==========================================================
# GET ACTIVE RAFFLE
# ==========================================================

def get_active_raffle(
    chat_id
):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    SELECT *
    FROM raffles
    WHERE chat_id=?
    AND active=1
    ORDER BY id DESC
    LIMIT 1
    """,
    (
        chat_id,
    ))


    row = cursor.fetchone()

    conn.close()


    if row:

        return {
            "id": row[0],
            "chat_id": row[1],
            "prize": row[2]
        }


    return None



# ==========================================================
# ADD ENTRY
# ==========================================================

def add_raffle_entry(
    raffle_id,
    user_id,
    name
):

    try:

        conn = get_db()
        cursor = conn.cursor()


        cursor.execute("""
        INSERT INTO raffle_entries
        (
            raffle_id,
            user_id,
            name
        )
        VALUES (?,?,?)
        """,
        (
            raffle_id,
            user_id,
            name
        ))


        conn.commit()
        conn.close()


        return True


    except sqlite3.IntegrityError:

        return False



# ==========================================================
# GET ENTRIES
# ==========================================================

def get_raffle_entries(
    raffle_id
):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    SELECT user_id,name
    FROM raffle_entries
    WHERE raffle_id=?
    """,
    (
        raffle_id,
    ))


    rows = cursor.fetchall()

    conn.close()


    return [
        {
            "user_id": row[0],
            "name": row[1]
        }
        for row in rows
    ]



# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(
    chat_id
):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    UPDATE raffles
    SET active=0
    WHERE chat_id=?
    """,
    (
        chat_id,
    ))


    conn.commit()
    conn.close()



# ==========================================================
# CLEAR ENTRIES
# ==========================================================

def clear_raffle():

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    DELETE FROM raffle_entries
    """)


    conn.commit()
    conn.close()
