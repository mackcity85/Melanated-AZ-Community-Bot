# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# Paid Raffle Database
# ==========================================================

import sqlite3

from datetime import datetime

from config import DB_NAME


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def initialize_raffle_database():

    conn = get_db()

    cursor = conn.cursor()


    # ======================================================
    # RAFFLES TABLE
    # ======================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        prize TEXT NOT NULL,

        description TEXT,

        active INTEGER DEFAULT 1,

        created TEXT
    )
    """)


    # ======================================================
    # RAFFLE ENTRIES TABLE
    # ======================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        raffle_id INTEGER,

        user_id INTEGER,

        username TEXT,

        display_name TEXT,

        payment_method TEXT,

        payment_status TEXT DEFAULT 'PENDING',

        approved INTEGER DEFAULT 0,

        created TEXT
    )
    """)


    # ======================================================
    # DATABASE MIGRATION
    # ======================================================

    cursor.execute(
        "PRAGMA table_info(raffle_entries)"
    )

    columns = [

        row["name"]

        for row in cursor.fetchall()

    ]


    # ------------------------------------------------------
    # Add display_name if missing
    # ------------------------------------------------------

    if "display_name" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffle_entries

            ADD COLUMN display_name TEXT
            """
        )


    # ------------------------------------------------------
    # Add payment_method if missing
    # ------------------------------------------------------

    if "payment_method" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffle_entries

            ADD COLUMN payment_method TEXT
            """
        )


    # ------------------------------------------------------
    # Add payment_status if missing
    # ------------------------------------------------------

    if "payment_status" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffle_entries

            ADD COLUMN payment_status TEXT
            """
        )


    # ------------------------------------------------------
    # Add approved if missing
    # ------------------------------------------------------

    if "approved" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffle_entries

            ADD COLUMN approved INTEGER DEFAULT 0
            """
        )


    # ------------------------------------------------------
    # Add created if missing
    # ------------------------------------------------------

    if "created" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffle_entries

            ADD COLUMN created TEXT
            """
        )


    conn.commit()

    conn.close()


# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    description=""
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO raffles
        (
            prize,
            description,
            active,
            created
        )

        VALUES (?,?,?,?)
        """,

        (
            prize,
            description,
            1,
            datetime.now().isoformat()
        )
    )


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


    cursor.execute(
        """
        SELECT

        id,
        prize,
        description

        FROM raffles

        WHERE active=1

        ORDER BY id DESC

        LIMIT 1
        """
    )


    result = cursor.fetchone()


    conn.close()


    if not result:

        return None


    return (
        result["id"],
        result["prize"],
        result["description"]
    )


# ==========================================================
# ADD RAFFLE ENTRY
# ==========================================================

def add_raffle_entry(
    raffle_id,
    user_id,
    username,
    display_name,
    payment_method
):

    conn = get_db()

    cursor = conn.cursor()


    # ======================================================
    # CHECK FOR EXISTING ENTRY
    # ======================================================

    cursor.execute(
        """
        SELECT id

        FROM raffle_entries

        WHERE raffle_id=?

        AND user_id=?

        AND payment_status IN (
            'PENDING',
            'PAID'
        )

        LIMIT 1
        """,

        (
            raffle_id,
            user_id
        )
    )


    existing = cursor.fetchone()


    if existing:

        conn.close()

        return None


    # ======================================================
    # CREATE ENTRY
    # ======================================================

    cursor.execute(
        """
        INSERT INTO raffle_entries
        (
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            payment_status,
            approved,
            created
        )

        VALUES (?,?,?,?,?,?,?,?)
        """,

        (
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            "PENDING",
            0,
            datetime.now().isoformat()
        )
    )


    entry_id = cursor.lastrowid


    conn.commit()

    conn.close()


    return entry_id


# ==========================================================
# GET ENTRY
# ==========================================================

def get_entry(
    entry_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        raffle_id,
        user_id,
        username,
        display_name,
        payment_method,
        payment_status,
        approved,
        created

        FROM raffle_entries

        WHERE id=?

        LIMIT 1
        """,

        (
            entry_id
        )
    )


    result = cursor.fetchone()


    conn.close()


    if not result:

        return None


    return dict(result)


# ==========================================================
# PENDING ENTRIES
# ==========================================================

def get_pending_entries():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        username,
        payment_method,
        created

        FROM raffle_entries

        WHERE approved=0

        AND payment_status='PENDING'

        ORDER BY id ASC
        """
    )


    results = cursor.fetchall()


    conn.close()


    return [

        tuple(row)

        for row in results

    ]


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id,
    admin_id=None
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffle_entries

        SET

        approved=1,

        payment_status='PAID'

        WHERE id=?

        AND approved=0

        AND payment_status='PENDING'
        """,

        (
            entry_id
        )
    )


    changed = cursor.rowcount


    conn.commit()

    conn.close()


    return changed > 0


# ==========================================================
# DENY ENTRY
# ==========================================================

def deny_entry(
    entry_id,
    admin_id=None
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffle_entries

        SET

        approved=0,

        payment_status='DENIED'

        WHERE id=?

        AND approved=0

        AND payment_status='PENDING'
        """,

        (
            entry_id
        )
    )


    changed = cursor.rowcount


    conn.commit()

    conn.close()


    return changed > 0


# ==========================================================
# APPROVED ENTRIES
# ==========================================================

def get_approved_entries(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        username,
        user_id

        FROM raffle_entries

        WHERE raffle_id=?

        AND approved=1

        AND payment_status='PAID'

        ORDER BY id ASC
        """,

        (
            raffle_id
        )
    )


    results = cursor.fetchall()


    conn.close()


    return [

        tuple(row)

        for row in results

    ]


# ==========================================================
# GET ENTRIES
# ==========================================================

def get_entries(
    raffle_id
):

    return get_approved_entries(
        raffle_id
    )


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(
    entry_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM raffle_entries

        WHERE id=?
        """,

        (
            entry_id
        )
    )


    changed = cursor.rowcount


    conn.commit()

    conn.close()


    return changed > 0


# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffles

        SET active=0

        WHERE id=?
        """,

        (
            raffle_id
        )
    )


    conn.commit()

    conn.close()


# ==========================================================
# ACTIVE RAFFLES
# ==========================================================

def get_expired_raffles():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        id,
        prize

        FROM raffles

        WHERE active=1
        """
    )


    results = cursor.fetchall()


    conn.close()


    return [

        tuple(row)

        for row in results

    ]
