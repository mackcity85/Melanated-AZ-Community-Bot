# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# ==========================================================

import os
import sqlite3
from datetime import datetime


# ==========================================================
# DATABASE LOCATION
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


DB_NAME = os.environ.get(
    "RAFFLE_DB_NAME",
    os.path.join(
        DATA_DIR,
        "raffle.db"
    )
)


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():

    connection = sqlite3.connect(
        DB_NAME,
        check_same_thread=False,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

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

    # ======================================================
    # UPGRADE RAFFLES TABLE
    # ======================================================

    cursor.execute(
        "PRAGMA table_info(raffles)"
    )

    columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    required_columns = {
        "price": "TEXT NOT NULL DEFAULT ''",
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

    # ======================================================
    # UPGRADE ENTRIES TABLE
    # ======================================================

    cursor.execute(
        "PRAGMA table_info(raffle_entries)"
    )

    entry_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    required_entry_columns = {
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


# ==========================================================
# CREATE DATABASE
# ==========================================================

initialize_database()


# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    price,
    expires_at
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
            expires_at
        )
    )

    raffle_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return raffle_id


# ==========================================================
# GET RAFFLE
# ==========================================================

def get_raffle(
    raffle_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM raffles
        WHERE id = ?
        LIMIT 1
        """,
        (
            raffle_id,
        )
    )

    raffle = cursor.fetchone()

    connection.close()

    return raffle


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
        WHERE status = 'active'
        ORDER BY id DESC
        LIMIT 1
        """
    )

    raffle = cursor.fetchone()

    connection.close()

    return raffle


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
        WHERE status = 'pending'
        ORDER BY id DESC
        LIMIT 1
        """
    )

    raffle = cursor.fetchone()

    connection.close()

    return raffle


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

def approve_raffle(
    raffle_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE raffles

        SET status = 'active'

        WHERE id = ?

        AND status = 'pending'
        """,
        (
            raffle_id,
        )
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# CANCEL PENDING RAFFLE
# ==========================================================

def cancel_pending_raffle(
    raffle_id
):

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

        AND status = 'pending'
        """,
        (
            now,
            raffle_id
        )
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
    message_id
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
            raffle_id
        )
    )

    connection.commit()
    connection.close()


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

    cursor.execute(
        """
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
        """,
        (
            raffle_id,
            user_id
        )
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
            now
        )
    )

    entry_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return entry_id


# ==========================================================
# GET ENTRY
# ==========================================================

def get_entry(
    entry_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM raffle_entries
        WHERE id = ?
        LIMIT 1
        """,
        (
            entry_id,
        )
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
            raffle_entries.id,
            raffle_entries.raffle_id,
            raffle_entries.user_id,
            raffle_entries.username,
            raffle_entries.display_name,
            raffle_entries.payment_method,
            raffle_entries.created_at

        FROM raffle_entries

        WHERE raffle_entries.status = 'pending'

        ORDER BY raffle_entries.id ASC
        """
    )

    entries = cursor.fetchall()

    connection.close()

    return entries


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id,
    admin_id
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
            entry_id
        )
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
    admin_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE raffle_entries

        SET
            status = 'denied',
            approved_by = ?

        WHERE id = ?

        AND status = 'pending'
        """,
        (
            admin_id,
            entry_id
        )
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# APPROVED ENTRIES
# ==========================================================

def get_approved_entries(
    raffle_id
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
        (
            raffle_id,
        )
    )

    entries = cursor.fetchall()

    connection.close()

    return entries


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(
    entry_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM raffle_entries
        WHERE id = ?
        """,
        (
            entry_id,
        )
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(
    raffle_id
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

        AND status = 'active'
        """,
        (
            now,
            raffle_id
        )
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1
