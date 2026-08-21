# ==========================================================
# Melanated AZ Bot
# raffle_database.py
#
# Self-contained raffle database
# ==========================================================

import sqlite3
from datetime import datetime


# ==========================================================
# DATABASE
# ==========================================================

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
# CREATE TABLES
# ==========================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # ------------------------------------------------------
    # RAFFLES
    # ------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raffles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            prize TEXT NOT NULL,

            entry_price TEXT NOT NULL DEFAULT '$0',

            status TEXT NOT NULL DEFAULT 'pending',

            chat_id INTEGER,

            message_id INTEGER,

            created_at TEXT NOT NULL,

            approved_by INTEGER,

            approved_at TEXT,

            closed_at TEXT

        )
        """
    )

    # ------------------------------------------------------
    # DATABASE MIGRATION
    # ------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(raffles)"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "entry_price" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN entry_price TEXT
            NOT NULL DEFAULT '$0'
            """
        )

    if "chat_id" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN chat_id INTEGER
            """
        )

    if "message_id" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN message_id INTEGER
            """
        )

    if "approved_by" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN approved_by INTEGER
            """
        )

    if "approved_at" not in columns:

        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN approved_at TEXT
            """
        )

    # ------------------------------------------------------
    # RAFFLE ENTRIES
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

    connection.commit()

    connection.close()


initialize_database()


# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    entry_price,
    chat_id
):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO raffles
        (
            prize,
            entry_price,
            status,
            chat_id,
            created_at
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
            entry_price,
            chat_id,
            now
        )
    )

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

    cursor.execute(
        """
        SELECT
            id,
            prize,
            entry_price,
            status,
            chat_id,
            message_id,
            created_at,
            approved_by,
            approved_at,
            closed_at

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
        SELECT
            id,
            prize,
            entry_price,
            status,
            chat_id,
            message_id,
            created_at,
            approved_by,
            approved_at,
            closed_at

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
# GET RAFFLE
# ==========================================================

def get_raffle(raffle_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            prize,
            entry_price,
            status,
            chat_id,
            message_id,
            created_at,
            approved_by,
            approved_at,
            closed_at

        FROM raffles

        WHERE id = ?

        LIMIT 1
        """,
        (raffle_id,)
    )

    raffle = cursor.fetchone()

    connection.close()

    return raffle


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

def approve_raffle(
    raffle_id,
    admin_id
):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE raffles

        SET
            status = 'active',
            approved_by = ?,
            approved_at = ?

        WHERE id = ?

        AND status = 'pending'
        """,
        (
            admin_id,
            now,
            raffle_id
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

    cursor.execute(
        """
        UPDATE raffles

        SET
            status = 'cancelled'

        WHERE id = ?

        AND status = 'pending'
        """,
        (raffle_id,)
    )

    changed = cursor.rowcount

    connection.commit()

    connection.close()

    return changed == 1


# ==========================================================
# SAVE RAFFLE MESSAGE
# ==========================================================

def save_raffle_message(
    raffle_id,
    message_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE raffles

        SET
            message_id = ?

        WHERE id = ?
        """,
        (
            message_id,
            raffle_id
        )
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

def get_entry(entry_id):

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
            approved_by,
            created_at,
            approved_at

        FROM raffle_entries

        WHERE id = ?

        LIMIT 1
        """,
        (entry_id,)
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
            created_at

        FROM raffle_entries

        WHERE status = 'pending'

        ORDER BY id ASC
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
# GET APPROVED ENTRIES
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
            display_name,
            user_id,
            username,
            payment_method,
            created_at

        FROM raffle_entries

        WHERE raffle_id = ?

        AND status = 'approved'

        ORDER BY id ASC
        """,
        (raffle_id,)
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
        (entry_id,)
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
