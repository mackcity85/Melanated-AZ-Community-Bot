# ==========================================================
# Melanated AZ Bot
# raffle_database.py
#
# Raffle database
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
# DATABASE INITIALIZATION
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
            entry_price REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            chat_id INTEGER,
            message_id INTEGER,
            created_at TEXT NOT NULL,
            approved_at TEXT,
            expires_at TEXT,
            closed_at TEXT
        )
        """
    )

    # ------------------------------------------------------
    # Migrate older databases
    # ------------------------------------------------------

    cursor.execute("PRAGMA table_info(raffles)")
    columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    migrations = {
        "entry_price": "ALTER TABLE raffles ADD COLUMN entry_price REAL NOT NULL DEFAULT 0",
        "chat_id": "ALTER TABLE raffles ADD COLUMN chat_id INTEGER",
        "message_id": "ALTER TABLE raffles ADD COLUMN message_id INTEGER",
        "approved_at": "ALTER TABLE raffles ADD COLUMN approved_at TEXT",
        "expires_at": "ALTER TABLE raffles ADD COLUMN expires_at TEXT",
    }

    for column, statement in migrations.items():

        if column not in columns:

            try:
                cursor.execute(statement)
            except sqlite3.OperationalError:
                pass

    # ------------------------------------------------------
    # ENTRIES
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
    chat_id=None
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
            float(entry_price),
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
    chat_id=None
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow()
    expires = now + timedelta(days=7)

    cursor.execute(
        """
        UPDATE raffles

        SET
            status = 'active',
            chat_id = COALESCE(?, chat_id),
            approved_at = ?,
            expires_at = ?

        WHERE id = ?
        AND status = 'pending'
        """,
        (
            chat_id,
            now.isoformat(),
            expires.isoformat(),
            raffle_id
        )
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
        SET message_id = ?
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
# CLOSE RAFFLE
# ==========================================================

def close_raffle(raffle_id):

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
        (entry_id,)
    )

    entry = cursor.fetchone()

    connection.close()

    if not entry:
        return None

    return dict(entry)


# ==========================================================
# PENDING ENTRIES
# ==========================================================

def get_pending_entries():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            e.*,
            r.prize,
            r.entry_price
        FROM raffle_entries e
        JOIN raffles r
            ON r.id = e.raffle_id
        WHERE e.status = 'pending'
        ORDER BY e.id ASC
        """
    )

    entries = cursor.fetchall()

    connection.close()

    return entries


# ==========================================================
# APPROVED / COMPLETED ENTRIES
# ==========================================================

def get_approved_entries(raffle_id=None):

    connection = get_connection()
    cursor = connection.cursor()

    if raffle_id is None:

        cursor.execute(
            """
            SELECT
                e.*,
                r.prize,
                r.entry_price
            FROM raffle_entries e
            JOIN raffles r
                ON r.id = e.raffle_id
            WHERE e.status = 'approved'
            ORDER BY e.id ASC
            """
        )

    else:

        cursor.execute(
            """
            SELECT
                e.*,
                r.prize,
                r.entry_price
            FROM raffle_entries e
            JOIN raffles r
                ON r.id = e.raffle_id
            WHERE e.status = 'approved'
            AND e.raffle_id = ?
            ORDER BY e.id ASC
            """,
            (raffle_id,)
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
        (entry_id,)
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1


# ==========================================================
# COUNTS
# ==========================================================

def get_entry_counts(raffle_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            SUM(
                CASE
                    WHEN status = 'pending'
                    THEN 1 ELSE 0
                END
            ) AS pending,

            SUM(
                CASE
                    WHEN status = 'approved'
                    THEN 1 ELSE 0
                END
            ) AS approved,

            SUM(
                CASE
                    WHEN status = 'denied'
                    THEN 1 ELSE 0
                END
            ) AS denied

        FROM raffle_entries

        WHERE raffle_id = ?
        """,
        (raffle_id,)
    )

    row = cursor.fetchone()

    connection.close()

    return {
        "pending": row["pending"] or 0,
        "approved": row["approved"] or 0,
        "denied": row["denied"] or 0,
    }
