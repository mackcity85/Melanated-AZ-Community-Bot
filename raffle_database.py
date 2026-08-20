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

    conn = sqlite3.connect(
        DB_NAME
    )

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

            chat_id INTEGER,

            active INTEGER DEFAULT 1,

            created TEXT
        )
    """)

    # ------------------------------------------------------
    # Upgrade existing database
    # ------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(raffles)"
    )

    raffle_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    if "description" not in raffle_columns:

        cursor.execute("""
            ALTER TABLE raffles
            ADD COLUMN description TEXT
        """)

    if "chat_id" not in raffle_columns:

        cursor.execute("""
            ALTER TABLE raffles
            ADD COLUMN chat_id INTEGER
        """)

    if "active" not in raffle_columns:

        cursor.execute("""
            ALTER TABLE raffles
            ADD COLUMN active INTEGER DEFAULT 1
        """)

    if "created" not in raffle_columns:

        cursor.execute("""
            ALTER TABLE raffles
            ADD COLUMN created TEXT
        """)

    # ======================================================
    # RAFFLE ENTRIES TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raffle_entries
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            raffle_id INTEGER NOT NULL,

            entry_number INTEGER,

            user_id INTEGER NOT NULL,

            username TEXT,

            display_name TEXT,

            payment_method TEXT,

            payment_status TEXT DEFAULT 'PENDING',

            approved INTEGER DEFAULT 0,

            approved_by INTEGER,

            approved_at TEXT,

            created TEXT
        )
    """)

    # ------------------------------------------------------
    # Upgrade existing database
    # ------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(raffle_entries)"
    )

    entry_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    if "entry_number" not in entry_columns:

        cursor.execute("""
            ALTER TABLE raffle_entries
            ADD COLUMN entry_number INTEGER
        """)

    if "display_name" not in entry_columns:

        cursor.execute("""
            ALTER TABLE raffle_entries
            ADD COLUMN display_name TEXT
        """)

    if "approved_by" not in entry_columns:

        cursor.execute("""
            ALTER TABLE raffle_entries
            ADD COLUMN approved_by INTEGER
        """)

    if "approved_at" not in entry_columns:

        cursor.execute("""
            ALTER TABLE raffle_entries
            ADD COLUMN approved_at TEXT
        """)

    # ======================================================
    # INDEXES
    # ======================================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_raffle_entries_raffle
        ON raffle_entries(raffle_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_raffle_entries_user
        ON raffle_entries(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_raffle_entries_status
        ON raffle_entries(payment_status)
    """)

    conn.commit()

    conn.close()


# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    description="",
    chat_id=None
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO raffles
        (
            prize,
            description,
            chat_id,
            active,
            created
        )

        VALUES (?, ?, ?, 1, ?)
    """, (
        prize,
        description,
        chat_id,
        datetime.now().isoformat()
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
            prize,
            description,
            chat_id

        FROM raffles

        WHERE active = 1

        ORDER BY id DESC

        LIMIT 1
    """)

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================================
# GET RAFFLE
# ==========================================================

def get_raffle(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            prize,
            description,
            chat_id,
            active,
            created

        FROM raffles

        WHERE id = ?
    """, (
        raffle_id,
    ))

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================================
# GET NEXT ENTRY NUMBER
# ==========================================================

def get_next_entry_number(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(
                MAX(entry_number),
                0
            ) + 1

        FROM raffle_entries

        WHERE raffle_id = ?
    """, (
        raffle_id,
    ))

    result = cursor.fetchone()

    conn.close()

    return result[0]


# ==========================================================
# CHECK USER ENTRY
# ==========================================================

def get_user_entry(
    raffle_id,
    user_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *

        FROM raffle_entries

        WHERE raffle_id = ?

        AND user_id = ?

        AND payment_status IN
        (
            'PENDING',
            'PAID'
        )

        ORDER BY id DESC

        LIMIT 1
    """, (
        raffle_id,
        user_id,
    ))

    result = cursor.fetchone()

    conn.close()

    return result


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

    # ------------------------------------------------------
    # Prevent duplicate active entries
    # ------------------------------------------------------

    cursor.execute("""
        SELECT id

        FROM raffle_entries

        WHERE raffle_id = ?

        AND user_id = ?

        AND payment_status IN
        (
            'PENDING',
            'PAID'
        )

        LIMIT 1
    """, (
        raffle_id,
        user_id,
    ))

    existing = cursor.fetchone()

    if existing:

        conn.close()

        return None

    # ------------------------------------------------------
    # Get next entry number
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            COALESCE(
                MAX(entry_number),
                0
            ) + 1

        FROM raffle_entries

        WHERE raffle_id = ?
    """, (
        raffle_id,
    ))

    entry_number = cursor.fetchone()[0]

    # ------------------------------------------------------
    # Insert entry
    # ------------------------------------------------------

    cursor.execute("""
        INSERT INTO raffle_entries
        (
            raffle_id,
            entry_number,
            user_id,
            username,
            display_name,
            payment_method,
            payment_status,
            approved,
            created
        )

        VALUES
        (
            ?, ?, ?, ?, ?, ?, 'PENDING', 0, ?
        )
    """, (
        raffle_id,
        entry_number,
        user_id,
        username,
        display_name,
        payment_method,
        datetime.now().isoformat()
    ))

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

    cursor.execute("""
        SELECT *

        FROM raffle_entries

        WHERE id = ?
    """, (
        entry_id,
    ))

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================================
# PENDING ENTRIES
# ==========================================================

def get_pending_entries(
    raffle_id=None
):

    conn = get_db()

    cursor = conn.cursor()

    if raffle_id:

        cursor.execute("""
            SELECT *

            FROM raffle_entries

            WHERE raffle_id = ?

            AND payment_status = 'PENDING'

            ORDER BY id ASC
        """, (
            raffle_id,
        ))

    else:

        cursor.execute("""
            SELECT *

            FROM raffle_entries

            WHERE payment_status = 'PENDING'

            ORDER BY id ASC
        """)

    results = cursor.fetchall()

    conn.close()

    return results


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id,
    approved_by=None
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE raffle_entries

        SET
            approved = 1,
            payment_status = 'PAID',
            approved_by = ?,
            approved_at = ?

        WHERE id = ?

        AND payment_status = 'PENDING'
    """, (
        approved_by,
        datetime.now().isoformat(),
        entry_id,
    ))

    changed = cursor.rowcount

    conn.commit()

    conn.close()

    return changed > 0


# ==========================================================
# DENY ENTRY
# ==========================================================

def deny_entry(
    entry_id,
    denied_by=None
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE raffle_entries

        SET
            approved = 0,
            payment_status = 'DENIED',
            approved_by = ?,
            approved_at = ?

        WHERE id = ?

        AND payment_status = 'PENDING'
    """, (
        denied_by,
        datetime.now().isoformat(),
        entry_id,
    ))

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

    cursor.execute("""
        SELECT *

        FROM raffle_entries

        WHERE raffle_id = ?

        AND approved = 1

        AND payment_status = 'PAID'

        ORDER BY entry_number ASC
    """, (
        raffle_id,
    ))

    results = cursor.fetchall()

    conn.close()

    return results


# ==========================================================
# ENTRY COUNT
# ==========================================================

def get_entry_count(
    raffle_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)

        FROM raffle_entries

        WHERE raffle_id = ?

        AND approved = 1

        AND payment_status = 'PAID'
    """, (
        raffle_id,
    ))

    result = cursor.fetchone()

    conn.close()

    return result[0]


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(
    entry_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM raffle_entries

        WHERE id = ?
    """, (
        entry_id,
    ))

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

    cursor.execute("""
        UPDATE raffles

        SET active = 0

        WHERE id = ?
    """, (
        raffle_id,
    ))

    conn.commit()

    conn.close()


# ==========================================================
# ACTIVE RAFFLES
# ==========================================================

def get_expired_raffles():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            prize,
            description,
            chat_id

        FROM raffles

        WHERE active = 1
    """)

    results = cursor.fetchall()

    conn.close()

    return results
