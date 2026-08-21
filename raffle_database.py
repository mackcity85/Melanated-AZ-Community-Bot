# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# ==========================================================

import sqlite3
from datetime import datetime, timedelta

DB_NAME = "raffle.db"


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():
    connection = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raffles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            prize TEXT NOT NULL,

            price REAL NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'pending',

            created_at TEXT NOT NULL,

            approved_at TEXT,

            expires_at TEXT,

            closed_at TEXT

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raffle_entries (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            raffle_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            username TEXT,

            display_name TEXT,

            payment_method TEXT,

            status TEXT NOT NULL DEFAULT 'pending',

            approved_by INTEGER,

            created_at TEXT NOT NULL,

            approved_at TEXT,

            FOREIGN KEY (raffle_id)
                REFERENCES raffles(id)

        )
    """)

    # ------------------------------------------------------
    # Add columns if upgrading an existing database
    # ------------------------------------------------------

    existing_columns = {
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(raffles)"
        ).fetchall()
    }

    if "price" not in existing_columns:
        cursor.execute(
            "ALTER TABLE raffles ADD COLUMN price REAL NOT NULL DEFAULT 0"
        )

    if "approved_at" not in existing_columns:
        cursor.execute(
            "ALTER TABLE raffles ADD COLUMN approved_at TEXT"
        )

    if "expires_at" not in existing_columns:
        cursor.execute(
            "ALTER TABLE raffles ADD COLUMN expires_at TEXT"
        )

    connection.commit()
    connection.close()


initialize_database()


# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(prize, price):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow()

    # One-week expiration
    expires = now + timedelta(days=7)

    cursor.execute("""
        INSERT INTO raffles
        (
            prize,
            price,
            status,
            created_at,
            expires_at
        )
        VALUES
        (
            ?,
            ?,
            'pending',
            ?,
            ?
        )
    """, (
        prize,
        price,
        now.isoformat(),
        expires.isoformat()
    ))

    raffle_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return raffle_id


# ==========================================================
# GET ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            prize,
            price,
            status,
            created_at,
            approved_at,
            expires_at,
            closed_at

        FROM raffles

        WHERE status = 'active'

        ORDER BY id DESC

        LIMIT 1
    """)

    raffle = cursor.fetchone()

    connection.close()

    return raffle


# ==========================================================
# GET PENDING RAFFLE
# ==========================================================

def get_pending_raffle():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            prize,
            price,
            status,
            created_at,
            approved_at,
            expires_at,
            closed_at

        FROM raffles

        WHERE status = 'pending'

        ORDER BY id DESC

        LIMIT 1
    """)

    raffle = cursor.fetchone()

    connection.close()

    return raffle


# ==========================================================
# GET RAFFLE
# ==========================================================

def get_raffle(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM raffles
        WHERE id = ?
        LIMIT 1
    """, (raffle_id,))

    raffle = cursor.fetchone()

    connection.close()

    return raffle


# ==========================================================
# APPROVE / ACTIVATE RAFFLE
# ==========================================================

def approve_raffle(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow()

    cursor.execute("""
        UPDATE raffles

        SET
            status = 'active',
            approved_at = ?,
            expires_at = ?

        WHERE id = ?

        AND status = 'pending'
    """, (
        now.isoformat(),
        (now + timedelta(days=7)).isoformat(),
        raffle_id
    ))

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# ADD ENTRY
# ==========================================================

def add_raffle_entry(
    raffle_id,
    user_id,
    username,
    display_name,
    payment_method
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id

        FROM raffle_entries

        WHERE raffle_id = ?

        AND user_id = ?

        AND status IN
        (
            'pending',
            'approved'
        )

        LIMIT 1
    """, (
        raffle_id,
        user_id
    ))

    existing = cursor.fetchone()

    if existing:

        connection.close()
        return None

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO raffle_entries
        (
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            status,
            created_at
        )

        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            'pending',
            ?
        )
    """, (
        raffle_id,
        user_id,
        username,
        display_name,
        payment_method,
        now
    ))

    entry_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return entry_id


# ==========================================================
# GET ENTRY
# ==========================================================

def get_entry(entry_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM raffle_entries
        WHERE id = ?
        LIMIT 1
    """, (entry_id,))

    entry = cursor.fetchone()

    connection.close()

    return dict(entry) if entry else None


# ==========================================================
# PENDING ENTRIES
# ==========================================================

def get_pending_entries():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            created_at

        FROM raffle_entries

        WHERE status = 'pending'

        ORDER BY id ASC
    """)

    entries = cursor.fetchall()

    connection.close()

    return entries


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(entry_id, admin_id):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        UPDATE raffle_entries

        SET
            status = 'approved',
            approved_by = ?,
            approved_at = ?

        WHERE id = ?

        AND status = 'pending'
    """, (
        admin_id,
        now,
        entry_id
    ))

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# DENY ENTRY
# ==========================================================

def deny_entry(entry_id, admin_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE raffle_entries

        SET
            status = 'denied',
            approved_by = ?

        WHERE id = ?

        AND status = 'pending'
    """, (
        admin_id,
        entry_id
    ))

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# APPROVED ENTRIES
# ==========================================================

def get_approved_entries(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            display_name,
            user_id,
            username,
            payment_method,
            created_at

        FROM raffle_entries

        WHERE raffle_id = ?

        AND status = 'approved'

        ORDER BY id ASC
    """, (raffle_id,))

    entries = cursor.fetchall()

    connection.close()

    return entries


# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        UPDATE raffles

        SET
            status = 'closed',
            closed_at = ?

        WHERE id = ?

        AND status = 'active'
    """, (
        now,
        raffle_id
    ))

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# EXPIRE RAFFLE
# ==========================================================

def expire_raffle(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        UPDATE raffles

        SET
            status = 'expired',
            closed_at = ?

        WHERE id = ?

        AND status = 'active'
    """, (
        now,
        raffle_id
    ))

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(entry_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM raffle_entries
        WHERE id = ?
    """, (entry_id,))

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1
