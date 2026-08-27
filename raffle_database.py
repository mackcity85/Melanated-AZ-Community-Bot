# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# ==========================================================

import os
import sqlite3
from datetime import datetime


# ==========================================================
# CONFIG
# ==========================================================

DB_NAME = os.environ.get(
    "RAFFLE_DB_NAME",
    "raffle.db"
)


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():

    connection = sqlite3.connect(
        DB_NAME,
        check_same_thread=False,
        timeout=30,
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # ------------------------------------------------------
    # Raffles
    # ------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raffles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prize TEXT NOT NULL,
            price TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            closed_at TEXT,
            chat_id INTEGER,
            message_id INTEGER
        )
        """
    )

    # ------------------------------------------------------
    # Entries
    # ------------------------------------------------------

    cursor.execute(
        """
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
        """
    )

    # ------------------------------------------------------
    # Upgrade old raffle databases
    # ------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(raffles)"
    )

    columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    required_columns = {
        "prize": "TEXT NOT NULL DEFAULT ''",
        "price": "TEXT NOT NULL DEFAULT ''",
        "status": "TEXT NOT NULL DEFAULT 'pending'",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "expires_at": "TEXT NOT NULL DEFAULT ''",
        "closed_at": "TEXT",
        "chat_id": "INTEGER",
        "message_id": "INTEGER",
    }

    for column, definition in required_columns.items():

        if column not in columns:

            cursor.execute(
                f"""
                ALTER TABLE raffles
                ADD COLUMN {column} {definition}
                """
            )

    # ------------------------------------------------------
    # Upgrade old entry database
    # ------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(raffle_entries)"
    )

    entry_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    required_entry_columns = {
        "raffle_id": "INTEGER NOT NULL DEFAULT 0",
        "user_id": "INTEGER NOT NULL DEFAULT 0",
        "username": "TEXT",
        "display_name": "TEXT",
        "payment_method": "TEXT",
        "status": "TEXT NOT NULL DEFAULT 'pending'",
        "approved_by": "INTEGER",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "approved_at": "TEXT",
    }

    for column, definition in required_entry_columns.items():

        if column not in entry_columns:

            cursor.execute(
                f"""
                ALTER TABLE raffle_entries
                ADD COLUMN {column} {definition}
                """
            )

    connection.commit()
    connection.close()


initialize_database()


# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    price,
    expires_at,
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
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
        """,
        (
            prize,
            price,
            now,
            expires_at,
        ),
    )

    raffle_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return raffle_id


# ==========================================================
# GET RAFFLE
# ==========================================================

def get_raffle(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM raffles
        WHERE id = ?
        LIMIT 1
        """,
        (raffle_id,),
    )

    raffle = cursor.fetchone()

    connection.close()

    if not raffle:
        return None

    return dict(raffle)


# ==========================================================
# GET ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM raffles
        WHERE LOWER(TRIM(status)) = 'active'
        ORDER BY id DESC
        LIMIT 1
        """
    )

    raffle = cursor.fetchone()

    connection.close()

    if not raffle:
        return None

    return dict(raffle)


# ==========================================================
# GET PENDING RAFFLE
# ==========================================================

def get_pending_raffle():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM raffles
        WHERE LOWER(TRIM(status)) = 'pending'
        ORDER BY id DESC
        LIMIT 1
        """
    )

    raffle = cursor.fetchone()

    connection.close()

    if not raffle:
        return None

    return dict(raffle)


# ==========================================================
# GET ACTIVE OR PENDING
# ==========================================================

def get_current_raffle():

    raffle = get_active_raffle()

    if raffle:
        return raffle

    return get_pending_raffle()


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

def approve_raffle(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE raffles
        SET status = 'active'
        WHERE id = ?
        AND LOWER(TRIM(status)) = 'pending'
        """,
        (raffle_id,),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# CANCEL PENDING RAFFLE
# ==========================================================

def cancel_pending_raffle(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE raffles
        SET
            status = 'cancelled',
            closed_at = ?
        WHERE id = ?
        AND LOWER(TRIM(status)) = 'pending'
        """,
        (
            now,
            raffle_id,
        ),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# SET RAFFLE POST
# ==========================================================

def set_raffle_post(
    raffle_id,
    chat_id,
    message_id,
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE raffles
        SET
            chat_id = ?,
            message_id = ?
        WHERE id = ?
        """,
        (
            chat_id,
            message_id,
            raffle_id,
        ),
    )

    connection.commit()
    connection.close()


# ==========================================================
# ADD RAFFLE ENTRY
# ==========================================================

def add_raffle_entry(
    raffle_id,
    user_id,
    username,
    display_name,
    payment_method,
):

    connection = get_connection()
    cursor = connection.cursor()

    # ------------------------------------------------------
    # Prevent duplicate pending/approved entries
    # ------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM raffle_entries
        WHERE raffle_id = ?
        AND user_id = ?
        AND status IN ('pending', 'approved')
        LIMIT 1
        """,
        (
            raffle_id,
            user_id,
        ),
    )

    existing = cursor.fetchone()

    if existing:

        connection.close()

        return None

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
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
        """,
        (
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            now,
        ),
    )

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

    cursor.execute(
        """
        SELECT *
        FROM raffle_entries
        WHERE id = ?
        LIMIT 1
        """,
        (entry_id,),
    )

    entry = cursor.fetchone()

    connection.close()

    if not entry:
        return None

    return dict(entry)


# ==========================================================
# GET PENDING ENTRIES
# ==========================================================

def get_pending_entries():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            status,
            created_at
        FROM raffle_entries
        WHERE status = 'pending'
        ORDER BY id ASC
        """
    )

    entries = cursor.fetchall()

    connection.close()

    return [dict(entry) for entry in entries]


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id,
    admin_id,
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE raffle_entries
        SET
            status = 'approved',
            approved_by = ?,
            approved_at = ?
        WHERE id = ?
        AND status = 'pending'
        """,
        (
            admin_id,
            now,
            entry_id,
        ),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# DENY ENTRY
# ==========================================================

def deny_entry(
    entry_id,
    admin_id,
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE raffle_entries
        SET
            status = 'denied',
            approved_by = ?,
            approved_at = ?
        WHERE id = ?
        AND status = 'pending'
        """,
        (
            admin_id,
            now,
            entry_id,
        ),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# APPROVED ENTRIES
# ==========================================================

def get_approved_entries(
    raffle_id,
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            created_at
        FROM raffle_entries
        WHERE raffle_id = ?
        AND status = 'approved'
        ORDER BY id ASC
        """,
        (raffle_id,),
    )

    entries = cursor.fetchall()

    connection.close()

    return [dict(entry) for entry in entries]


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(entry_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM raffle_entries
        WHERE id = ?
        """,
        (entry_id,),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(
    raffle_id,
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE raffles
        SET
            status = 'closed',
            closed_at = ?
        WHERE id = ?
        AND LOWER(TRIM(status)) = 'active'
        """,
        (
            now,
            raffle_id,
        ),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# DATABASE DEBUG
# ==========================================================

def get_all_raffles():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM raffles
        ORDER BY id DESC
        """
    )

    raffles = cursor.fetchall()

    connection.close()

    return [dict(raffle) for raffle in raffles]
