# ==========================================================
# Melanated AZ Bot
# raffle_database.py
#
# Raffle database
# ==========================================================

import sqlite3
from datetime import datetime


DB_NAME = "raffle.db"


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():

    connection = sqlite3.connect(
        DB_NAME,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================================
# INITIALIZE DATABASE
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

            created_at TEXT NOT NULL,

            approved_at TEXT,

            expires_at TEXT,

            closed_at TEXT,

            chat_id INTEGER,

            message_id INTEGER,

            approved_by INTEGER

        )
        """
    )

    # ------------------------------------------------------
    # ADD COLUMNS TO OLD DATABASES
    # ------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(raffles)"
    )

    columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    if "entry_price" not in columns:
        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN entry_price TEXT NOT NULL DEFAULT '$0'
            """
        )

    if "approved_at" not in columns:
        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN approved_at TEXT
            """
        )

    if "expires_at" not in columns:
        cursor.execute(
            """
            ALTER TABLE raffles
            ADD COLUMN expires_at TEXT
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
    chat_id=None,
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
            created_at,
            chat_id
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
            now,
            chat_id,
        ),
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

def get_raffle(
    raffle_id,
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
        ),
    )

    raffle = cursor.fetchone()

    connection.close()

    return raffle


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

def approve_raffle(
    raffle_id,
    admin_id,
    chat_id,
    message_id,
    expires_at,
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE raffles

        SET
            status = 'active',
            approved_at = ?,
            expires_at = ?,
            chat_id = ?,
            message_id = ?,
            approved_by = ?

        WHERE id = ?

        AND status = 'pending'
        """,
        (
            now,
            expires_at,
            chat_id,
            message_id,
            admin_id,
            raffle_id,
        ),
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

        AND status = 'active'
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
# DENY / CANCEL PENDING RAFFLE
# ==========================================================

def deny_raffle(
    raffle_id,
    admin_id,
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE raffles

        SET
            status = 'denied',
            closed_at = ?,
            approved_by = ?

        WHERE id = ?

        AND status = 'pending'
        """,
        (
            now,
            admin_id,
            raffle_id,
        ),
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
# ADD ENTRY
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

def get_entry(
    entry_id,
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
        ),
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
            raffle_entries.*,
            raffles.prize,
            raffles.entry_price

        FROM raffle_entries

        JOIN raffles
        ON raffles.id = raffle_entries.raffle_id

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
        SELECT *

        FROM raffle_entries

        WHERE raffle_id = ?

        AND status = 'approved'

        ORDER BY id ASC
        """,
        (
            raffle_id,
        ),
    )

    entries = cursor.fetchall()

    connection.close()

    return entries


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(
    entry_id,
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
        ),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed == 1
