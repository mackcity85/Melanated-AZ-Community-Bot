# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# Raffle Payment Database
# ==========================================================

from datetime import datetime

from database import get_db



# ==========================================================
# INITIALIZE RAFFLE TABLES
# ==========================================================

def initialize_raffle_database():

    conn = get_db()

    cursor = conn.cursor()



    # --------------------------
    # Pending Payments
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_pending
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        payment_method TEXT,
        raffle TEXT,
        status TEXT DEFAULT 'PENDING',
        submitted_date TEXT
    )
    """)



    # --------------------------
    # Approved Entries
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_approved
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        raffle TEXT,
        entered_date TEXT
    )
    """)



    # --------------------------
    # Winner History
    # --------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_winners
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        raffle TEXT,
        won_date TEXT
    )
    """)



    conn.commit()

    conn.close()





# ==========================================================
# ADD PENDING PAYMENT
# ==========================================================

def add_pending_payment(
    user_id,
    username,
    payment_method,
    raffle
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO raffle_pending
    (
        user_id,
        username,
        payment_method,
        raffle,
        submitted_date
    )

    VALUES (?,?,?,?,?)
    """,

    (
        user_id,
        username,
        payment_method,
        raffle,
        datetime.now().isoformat()
    ))



    conn.commit()

    conn.close()





# ==========================================================
# GET PENDING PAYMENTS
# ==========================================================

def get_pending_payments():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        id,
        user_id,
        username,
        payment_method,
        raffle

    FROM raffle_pending

    WHERE status='PENDING'
    """)


    rows = cursor.fetchall()


    conn.close()


    return rows





# ==========================================================
# APPROVE PAYMENT
# ==========================================================

def approve_payment(
    pending_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        user_id,
        username,
        raffle

    FROM raffle_pending

    WHERE id=?
    """,

    (
        pending_id,
    ))


    entry = cursor.fetchone()


    if not entry:

        conn.close()

        return None



    cursor.execute("""
    UPDATE raffle_pending

    SET status='APPROVED'

    WHERE id=?
    """,

    (
        pending_id,
    ))



    cursor.execute("""
    INSERT INTO raffle_approved
    (
        user_id,
        username,
        raffle,
        entered_date
    )

    VALUES (?,?,?,?)
    """,

    (
        entry[0],
        entry[1],
        entry[2],
        datetime.now().isoformat()
    ))



    conn.commit()

    conn.close()


    return entry





# ==========================================================
# DENY PAYMENT
# ==========================================================

def deny_payment(
    pending_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    UPDATE raffle_pending

    SET status='DENIED'

    WHERE id=?
    """,

    (
        pending_id,
    ))



    conn.commit()

    conn.close()





# ==========================================================
# GET APPROVED ENTRIES
# ==========================================================

def get_approved_entries(
    raffle
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        user_id,
        username

    FROM raffle_approved

    WHERE raffle=?
    """,

    (
        raffle,
    ))



    rows = cursor.fetchall()


    conn.close()


    return rows





# ==========================================================
# SAVE WINNER
# ==========================================================

def save_winner(
    user_id,
    username,
    raffle
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO raffle_winners
    (
        user_id,
        username,
        raffle,
        won_date
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
