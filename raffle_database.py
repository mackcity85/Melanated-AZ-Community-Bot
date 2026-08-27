# ==========================================================
# Melanated AZ Bot
# raffle_database.py
#
# Persistent SQLite raffle database for Render
#
# IMPORTANT:
# Render persistent disk is currently mounted as:
#
#     /var/data
#
# Your current container exposes it as:
#
#     /var/data<SPACE>
#
# This file detects both automatically.
# ==========================================================

import os
import sqlite3
import shutil
from datetime import datetime


# ==========================================================
# DATABASE LOCATION
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Possible Render disk paths.
# The second one accounts for the trailing-space directory
# currently visible in your Render container.

PERSISTENT_PATHS = [
    "/var/data",
    "/var/data ",
]

# Normal application fallback.
LOCAL_DATA_DIR = os.path.join(BASE_DIR, "data")


# ==========================================================
# FIND DATABASE DIRECTORY
# ==========================================================

def get_database_directory():
    """
    Find the best available persistent database directory.

    Priority:
        1. Render persistent disk
        2. Render persistent disk with trailing-space path
        3. Local application data directory
    """

    for path in PERSISTENT_PATHS:

        try:
            if os.path.isdir(path) and os.access(path, os.W_OK):

                print(f"RAFFLE DATABASE STORAGE: {repr(path)}")

                return path

        except Exception:
            pass

    # ------------------------------------------------------
    # Fallback to local project storage
    # ------------------------------------------------------

    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

    print(
        "WARNING: Render persistent disk was not accessible."
    )

    print(
        f"Using local database storage: {LOCAL_DATA_DIR}"
    )

    return LOCAL_DATA_DIR


# ==========================================================
# DATABASE PATH
# ==========================================================

DATA_DIR = get_database_directory()

DB_PATH = os.path.join(
    DATA_DIR,
    "raffle.db"
)

BACKUP_DIR = os.path.join(
    DATA_DIR,
    "backups"
)


# ==========================================================
# ENSURE BACKUP DIRECTORY
# ==========================================================

try:

    os.makedirs(
        BACKUP_DIR,
        exist_ok=True
    )

except Exception as error:

    print(
        f"WARNING: Could not create backup directory: {error}"
    )


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():
    """
    Return a SQLite connection to the raffle database.
    """

    connection = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    # SQLite reliability settings
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        "PRAGMA busy_timeout = 30000"
    )

    return connection


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():
    """
    Create the raffle database and all required tables.
    """

    # Make sure the selected directory exists.
    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    os.makedirs(
        BACKUP_DIR,
        exist_ok=True
    )

    connection = get_connection()

    try:

        # ==================================================
        # RAFFLES
        # ==================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS raffles (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                prize TEXT NOT NULL,

                entry_price REAL NOT NULL DEFAULT 0,

                status TEXT NOT NULL DEFAULT 'pending',

                created_at TEXT NOT NULL,

                expires_at TEXT,

                approved_at TEXT,

                closed_at TEXT,

                chat_id INTEGER,

                message_id INTEGER,

                winner_id INTEGER,

                winner_username TEXT,

                winner_name TEXT,

                created_by INTEGER,

                created_by_username TEXT
            )
        """)

        # ==================================================
        # RAFFLE ENTRIES
        # ==================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS raffle_entries (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                raffle_id INTEGER NOT NULL,

                user_id INTEGER NOT NULL,

                username TEXT,

                first_name TEXT,

                last_name TEXT,

                payment_method TEXT,

                payment_status TEXT NOT NULL DEFAULT 'pending',

                entry_status TEXT NOT NULL DEFAULT 'pending',

                payment_reference TEXT,

                approved_by INTEGER,

                approved_at TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (raffle_id)
                    REFERENCES raffles(id)
                    ON DELETE CASCADE
            )
        """)

        # ==================================================
        # INDEXES
        # ==================================================

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_raffles_status
            ON raffles(status)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_raffle_entries_raffle
            ON raffle_entries(raffle_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_raffle_entries_user
            ON raffle_entries(user_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_raffle_entries_payment
            ON raffle_entries(payment_status)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_raffle_entries_status
            ON raffle_entries(entry_status)
        """)

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# DATABASE BACKUP
# ==========================================================

def backup_database():
    """
    Create a timestamped backup of the database.
    """

    if not os.path.exists(DB_PATH):
        return None

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = os.path.join(
        BACKUP_DIR,
        f"raffle_{timestamp}.db"
    )

    try:

        shutil.copy2(
            DB_PATH,
            backup_path
        )

        return backup_path

    except Exception as error:

        print(
            f"WARNING: Could not backup raffle database: {error}"
        )

        return None


# ==========================================================
# CREATE RAFFLE
# ==========================================================

def create_raffle(
    prize,
    entry_price,
    created_by=None,
    created_by_username=None,
    status="pending",
    chat_id=None,
    message_id=None,
    expires_at=None
):

    connection = get_connection()

    try:

        created_at = datetime.now().isoformat()

        cursor = connection.execute("""
            INSERT INTO raffles (
                prize,
                entry_price,
                status,
                created_at,
                expires_at,
                chat_id,
                message_id,
                created_by,
                created_by_username
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prize,
            entry_price,
            status,
            created_at,
            expires_at,
            chat_id,
            message_id,
            created_by,
            created_by_username
        ))

        connection.commit()

        return cursor.lastrowid

    finally:

        connection.close()


# ==========================================================
# GET RAFFLE
# ==========================================================

def get_raffle(raffle_id):

    connection = get_connection()

    try:

        row = connection.execute("""
            SELECT *
            FROM raffles
            WHERE id = ?
        """, (
            raffle_id,
        )).fetchone()

        return dict(row) if row else None

    finally:

        connection.close()


# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    connection = get_connection()

    try:

        row = connection.execute("""
            SELECT *
            FROM raffles
            WHERE status = 'active'
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

        return dict(row) if row else None

    finally:

        connection.close()


# ==========================================================
# PENDING RAFFLE
# ==========================================================

def get_pending_raffle():

    connection = get_connection()

    try:

        row = connection.execute("""
            SELECT *
            FROM raffles
            WHERE status = 'pending'
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

        return dict(row) if row else None

    finally:

        connection.close()


# ==========================================================
# ALL PENDING RAFFLES
# ==========================================================

def get_pending_raffles():

    connection = get_connection()

    try:

        rows = connection.execute("""
            SELECT *
            FROM raffles
            WHERE status = 'pending'
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]

    finally:

        connection.close()


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

def approve_raffle(
    raffle_id,
    chat_id=None,
    message_id=None,
    expires_at=None
):

    connection = get_connection()

    try:

        approved_at = datetime.now().isoformat()

        connection.execute("""
            UPDATE raffles

            SET
                status = 'active',
                approved_at = ?,

                chat_id =
                    COALESCE(?, chat_id),

                message_id =
                    COALESCE(?, message_id),

                expires_at =
                    COALESCE(?, expires_at)

            WHERE id = ?
        """, (
            approved_at,
            chat_id,
            message_id,
            expires_at,
            raffle_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# UPDATE RAFFLE MESSAGE
# ==========================================================

def update_raffle_message(
    raffle_id,
    chat_id,
    message_id
):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE raffles

            SET
                chat_id = ?,
                message_id = ?

            WHERE id = ?
        """, (
            chat_id,
            message_id,
            raffle_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# UPDATE EXPIRATION
# ==========================================================

def update_raffle_expiration(
    raffle_id,
    expires_at
):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE raffles

            SET expires_at = ?

            WHERE id = ?
        """, (
            expires_at,
            raffle_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(raffle_id):

    connection = get_connection()

    try:

        closed_at = datetime.now().isoformat()

        connection.execute("""
            UPDATE raffles

            SET
                status = 'closed',
                closed_at = ?

            WHERE id = ?
        """, (
            closed_at,
            raffle_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

def cancel_raffle(raffle_id):

    connection = get_connection()

    try:

        closed_at = datetime.now().isoformat()

        connection.execute("""
            UPDATE raffles

            SET
                status = 'cancelled',
                closed_at = ?

            WHERE id = ?
        """, (
            closed_at,
            raffle_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# SET WINNER
# ==========================================================

def set_winner(
    raffle_id,
    winner_id,
    winner_username=None,
    winner_name=None
):

    connection = get_connection()

    try:

        closed_at = datetime.now().isoformat()

        connection.execute("""
            UPDATE raffles

            SET
                winner_id = ?,
                winner_username = ?,
                winner_name = ?,
                status = 'closed',
                closed_at = ?

            WHERE id = ?
        """, (
            winner_id,
            winner_username,
            winner_name,
            closed_at,
            raffle_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# ADD RAFFLE ENTRY
# ==========================================================

def add_raffle_entry(
    raffle_id,
    user_id,
    username=None,
    first_name=None,
    last_name=None,
    payment_method=None,
    payment_status="pending",
    entry_status="pending",
    payment_reference=None
):

    connection = get_connection()

    try:

        created_at = datetime.now().isoformat()

        cursor = connection.execute("""
            INSERT INTO raffle_entries (

                raffle_id,
                user_id,
                username,
                first_name,
                last_name,
                payment_method,
                payment_status,
                entry_status,
                payment_reference,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            raffle_id,
            user_id,
            username,
            first_name,
            last_name,
            payment_method,
            payment_status,
            entry_status,
            payment_reference,
            created_at
        ))

        connection.commit()

        return cursor.lastrowid

    finally:

        connection.close()


# ==========================================================
# GET USER ENTRY
# ==========================================================

def get_user_entry(
    raffle_id,
    user_id
):

    connection = get_connection()

    try:

        row = connection.execute("""
            SELECT *
            FROM raffle_entries

            WHERE raffle_id = ?
              AND user_id = ?

            ORDER BY id DESC
            LIMIT 1
        """, (
            raffle_id,
            user_id
        )).fetchone()

        return dict(row) if row else None

    finally:

        connection.close()


# ==========================================================
# GET ENTRY
# ==========================================================

def get_entry(entry_id):

    connection = get_connection()

    try:

        row = connection.execute("""
            SELECT *
            FROM raffle_entries
            WHERE id = ?
        """, (
            entry_id,
        )).fetchone()

        return dict(row) if row else None

    finally:

        connection.close()


# ==========================================================
# GET RAFFLE ENTRIES
# ==========================================================

def get_raffle_entries(
    raffle_id,
    approved_only=False
):

    connection = get_connection()

    try:

        if approved_only:

            rows = connection.execute("""
                SELECT *
                FROM raffle_entries

                WHERE raffle_id = ?
                  AND entry_status = 'approved'

                ORDER BY id ASC
            """, (
                raffle_id,
            )).fetchall()

        else:

            rows = connection.execute("""
                SELECT *
                FROM raffle_entries

                WHERE raffle_id = ?

                ORDER BY id ASC
            """, (
                raffle_id,
            )).fetchall()

        return [dict(row) for row in rows]

    finally:

        connection.close()


# ==========================================================
# GET PENDING ENTRIES
# ==========================================================

def get_pending_entries(
    raffle_id=None
):

    connection = get_connection()

    try:

        if raffle_id is not None:

            rows = connection.execute("""
                SELECT *
                FROM raffle_entries

                WHERE raffle_id = ?
                  AND entry_status = 'pending'

                ORDER BY id ASC
            """, (
                raffle_id,
            )).fetchall()

        else:

            rows = connection.execute("""
                SELECT
                    raffle_entries.*,
                    raffles.prize,
                    raffles.entry_price

                FROM raffle_entries

                JOIN raffles
                    ON raffles.id =
                       raffle_entries.raffle_id

                WHERE raffle_entries.entry_status = 'pending'

                ORDER BY raffle_entries.id ASC
            """).fetchall()

        return [dict(row) for row in rows]

    finally:

        connection.close()


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id,
    approved_by=None
):

    connection = get_connection()

    try:

        approved_at = datetime.now().isoformat()

        connection.execute("""
            UPDATE raffle_entries

            SET
                entry_status = 'approved',
                payment_status = 'verified',
                approved_by = ?,
                approved_at = ?

            WHERE id = ?
        """, (
            approved_by,
            approved_at,
            entry_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# DENY ENTRY
# ==========================================================

def deny_entry(
    entry_id,
    approved_by=None
):

    connection = get_connection()

    try:

        approved_at = datetime.now().isoformat()

        connection.execute("""
            UPDATE raffle_entries

            SET
                entry_status = 'denied',
                payment_status = 'rejected',
                approved_by = ?,
                approved_at = ?

            WHERE id = ?
        """, (
            approved_by,
            approved_at,
            entry_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# UPDATE PAYMENT STATUS
# ==========================================================

def update_payment_status(
    entry_id,
    payment_status
):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE raffle_entries

            SET payment_status = ?

            WHERE id = ?
        """, (
            payment_status,
            entry_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# UPDATE ENTRY STATUS
# ==========================================================

def update_entry_status(
    entry_id,
    entry_status
):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE raffle_entries

            SET entry_status = ?

            WHERE id = ?
        """, (
            entry_status,
            entry_id
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(entry_id):

    connection = get_connection()

    try:

        connection.execute("""
            DELETE FROM raffle_entries
            WHERE id = ?
        """, (
            entry_id,
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# COUNT ENTRIES
# ==========================================================

def count_entries(
    raffle_id,
    approved_only=True
):

    connection = get_connection()

    try:

        if approved_only:

            row = connection.execute("""
                SELECT COUNT(*) AS count

                FROM raffle_entries

                WHERE raffle_id = ?
                  AND entry_status = 'approved'
            """, (
                raffle_id,
            )).fetchone()

        else:

            row = connection.execute("""
                SELECT COUNT(*) AS count

                FROM raffle_entries

                WHERE raffle_id = ?
            """, (
                raffle_id,
            )).fetchone()

        return row["count"]

    finally:

        connection.close()


# ==========================================================
# RAFFLE HISTORY
# ==========================================================

def get_raffle_history(
    limit=20
):

    connection = get_connection()

    try:

        rows = connection.execute("""
            SELECT *
            FROM raffles

            ORDER BY id DESC

            LIMIT ?
        """, (
            limit,
        )).fetchall()

        return [dict(row) for row in rows]

    finally:

        connection.close()


# ==========================================================
# DATABASE STATUS
# ==========================================================

def database_status():

    exists = os.path.exists(DB_PATH)

    size = (
        os.path.getsize(DB_PATH)
        if exists
        else 0
    )

    connection = get_connection()

    try:

        raffle_count = connection.execute("""
            SELECT COUNT(*) AS count
            FROM raffles
        """).fetchone()["count"]

        entry_count = connection.execute("""
            SELECT COUNT(*) AS count
            FROM raffle_entries
        """).fetchone()["count"]

    finally:

        connection.close()

    return {
        "path": DB_PATH,
        "exists": exists,
        "size": size,
        "raffles": raffle_count,
        "entries": entry_count
    }


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

initialize_database()


# ==========================================================
# STARTUP INFORMATION
# ==========================================================

print(
    f"RAFFLE DATABASE PATH: {DB_PATH}"
)

print(
    f"RAFFLE DATABASE STORAGE: {repr(DATA_DIR)}"
)

print(
    "RAFFLE DATABASE INITIALIZED SUCCESSFULLY"
)
