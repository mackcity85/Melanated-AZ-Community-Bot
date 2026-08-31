# ==========================================================
# Melanated AZ Bot
# raffle_database.py
#
# COMPLETE REPLACEMENT
#
# Persistent SQLite database for:
# - Raffles
# - Raffle Entries
# - Birthdays
# - Known Group Members
#
# Render Persistent Disk:
# /var/data
#
# Database:
# /var/data/raffle.db
#
# IMPORTANT:
# - NEVER falls back to application filesystem
# - NEVER deletes existing data
# - NEVER drops existing tables
# - Existing database is preserved
# - Existing rows are preserved
# - Missing tables/indexes are added only when needed
# - Existing raffle/birthday/member data remains intact
# ==========================================================

import os
import sqlite3
from datetime import datetime


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DEFAULT_DB_NAME = "/var/data/raffle.db"

DB_NAME = os.environ.get(
    "RAFFLE_DB_NAME",
    DEFAULT_DB_NAME,
).strip()

DB_NAME = os.path.abspath(DB_NAME)
DB_DIR = os.path.dirname(DB_NAME)


# ==========================================================
# SAFETY CHECK
# ==========================================================

if not DB_NAME.startswith("/var/data/"):
    raise RuntimeError(
        "\n"
        "==========================================================\n"
        "FATAL DATABASE CONFIGURATION ERROR\n"
        "==========================================================\n"
        f"Database path is:\n{DB_NAME}\n\n"
        "The Melanated AZ Bot database MUST be stored on the\n"
        "Render Persistent Disk.\n\n"
        "Required location:\n"
        "/var/data/raffle.db\n\n"
        "Set the Render environment variable:\n"
        "RAFFLE_DB_NAME=/var/data/raffle.db\n\n"
        "The bot will NOT use the application filesystem.\n"
        "==========================================================\n"
    )


if not os.path.isdir(DB_DIR):
    raise RuntimeError(
        "\n"
        "==========================================================\n"
        "FATAL DATABASE ERROR\n"
        "==========================================================\n"
        f"Database directory does not exist:\n{DB_DIR}\n\n"
        "Your Render Persistent Disk must be mounted at:\n"
        "/var/data\n\n"
        "Verify:\n"
        "Mount Path: /var/data\n\n"
        "The bot will NOT create a temporary database.\n"
        "==========================================================\n"
    )


# ==========================================================
# DATABASE INFORMATION
# ==========================================================

print("==========================================================")
print("Melanated AZ Bot - Persistent Database")
print("==========================================================")
print("Database path       :", DB_NAME)
print("Database directory  :", DB_DIR)
print("Database exists     :", os.path.exists(DB_NAME))

if os.path.exists(DB_NAME):
    print(
        "Database size       :",
        os.path.getsize(DB_NAME),
    )
else:
    print("Database size       : 0")

print(
    "Persistent directory:",
    os.path.isdir("/var/data"),
)

print("==========================================================")


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=30,
        check_same_thread=False,
    )

    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception as exc:
        print(
            "WARNING: Could not enable SQLite WAL mode:",
            exc,
        )

    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")

    return conn


# ==========================================================
# HELPERS
# ==========================================================

def utc_now():
    return datetime.utcnow().isoformat()


def table_exists(conn, table_name):
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def column_exists(conn, table_name, column_name):
    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        row["name"] == column_name
        for row in rows
    )


def add_column_if_missing(
    conn,
    table_name,
    column_name,
    column_definition,
):
    if not table_exists(conn, table_name):
        return

    if column_exists(
        conn,
        table_name,
        column_name,
    ):
        return

    conn.execute(
        f"""
        ALTER TABLE {table_name}
        ADD COLUMN {column_name}
        {column_definition}
        """
    )


# ==========================================================
# INITIALIZE DATABASE
#
# IMPORTANT:
# CREATE TABLE IF NOT EXISTS does NOT replace existing data.
# ==========================================================

def initialize_database():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ==================================================
        # RAFFLES
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS raffles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prize TEXT NOT NULL,
                price TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                chat_id INTEGER,
                message_id INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )

        # ==================================================
        # RAFFLE ENTRIES
        # ==================================================

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
                FOREIGN KEY (raffle_id)
                    REFERENCES raffles(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ==================================================
        # BIRTHDAYS
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS birthdays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                birthday TEXT NOT NULL,
                username TEXT,
                display_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, chat_id)
            )
            """
        )

        # ==================================================
        # MEMBERS
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                username TEXT,
                display_name TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                UNIQUE(user_id, chat_id)
            )
            """
        )

        # ==================================================
        # SAFE MIGRATION
        #
        # These only add missing columns.
        # Nothing is removed.
        # ==================================================

        add_column_if_missing(
            conn,
            "raffles",
            "chat_id",
            "INTEGER",
        )

        add_column_if_missing(
            conn,
            "raffles",
            "message_id",
            "INTEGER",
        )

        add_column_if_missing(
            conn,
            "raffles",
            "created_at",
            "TEXT",
        )

        add_column_if_missing(
            conn,
            "raffle_entries",
            "username",
            "TEXT",
        )

        add_column_if_missing(
            conn,
            "raffle_entries",
            "display_name",
            "TEXT",
        )

        add_column_if_missing(
            conn,
            "raffle_entries",
            "payment_method",
            "TEXT",
        )

        add_column_if_missing(
            conn,
            "raffle_entries",
            "status",
            "TEXT NOT NULL DEFAULT 'pending'",
        )

        add_column_if_missing(
            conn,
            "raffle_entries",
            "approved_by",
            "INTEGER",
        )

        add_column_if_missing(
            conn,
            "raffle_entries",
            "created_at",
            "TEXT",
        )

        # ==================================================
        # INDEXES
        # ==================================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_raffles_status
            ON raffles(status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_raffles_expires_at
            ON raffles(expires_at)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_raffles_chat_message
            ON raffles(chat_id, message_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_raffle_entries_raffle_id
            ON raffle_entries(raffle_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_raffle_entries_status
            ON raffle_entries(status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_raffle_entries_user
            ON raffle_entries(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_birthdays_chat_id
            ON birthdays(chat_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_members_chat_id
            ON members(chat_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_members_display_name
            ON members(display_name COLLATE NOCASE)
            """
        )

        # ==================================================
        # DUPLICATE PROTECTION
        #
        # We DO NOT create a UNIQUE index here because an
        # existing database could theoretically contain old
        # duplicate rows. That would cause startup failure.
        #
        # Duplicate protection is handled atomically inside
        # add_raffle_entry().
        # ==================================================

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# INITIALIZE
# ==========================================================

initialize_database()


# ==========================================================
# MEMBER STORAGE
# ==========================================================

def save_member(
    user_id,
    chat_id,
    username=None,
    display_name=None,
):

    if user_id is None or chat_id is None:
        return False

    now = utc_now()

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO members (
                user_id,
                chat_id,
                username,
                display_name,
                first_seen_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id, chat_id)
            DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                last_seen_at = excluded.last_seen_at
            """,
            (
                int(user_id),
                int(chat_id),
                username,
                display_name,
                now,
                now,
            ),
        )

        conn.commit()

        return True

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# GET MEMBERS
# ==========================================================

def get_members(
    chat_id,
    limit=1000,
):

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT
                id,
                user_id,
                chat_id,
                username,
                display_name,
                first_seen_at,
                last_seen_at
            FROM members
            WHERE chat_id = ?
            ORDER BY
                COALESCE(
                    NULLIF(display_name, ''),
                    NULLIF(username, ''),
                    CAST(user_id AS TEXT)
                ) COLLATE NOCASE ASC
            LIMIT ?
            """,
            (
                int(chat_id),
                int(limit),
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


# ==========================================================
# GET MEMBER
# ==========================================================

def get_member(
    user_id,
    chat_id,
):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM members
            WHERE user_id = ?
            AND chat_id = ?
            LIMIT 1
            """,
            (
                int(user_id),
                int(chat_id),
            ),
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# RAFFLE CREATION
# ==========================================================

def create_raffle(
    prize,
    price,
    expires_at,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO raffles (
                prize,
                price,
                expires_at,
                status,
                created_at
            )
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (
                prize,
                price,
                expires_at,
                utc_now(),
            ),
        )

        raffle_id = cursor.lastrowid

        conn.commit()

        return raffle_id

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# GET RAFFLE
# ==========================================================

def get_raffle(raffle_id):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM raffles
            WHERE id = ?
            """,
            (int(raffle_id),),
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM raffles
            WHERE status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# GET RAFFLE BY ID ONLY IF ACTIVE
# ==========================================================

def get_active_raffle_by_id(raffle_id):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM raffles
            WHERE id = ?
            AND status = 'active'
            LIMIT 1
            """,
            (int(raffle_id),),
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# PENDING RAFFLE
# ==========================================================

def get_pending_raffle():

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM raffles
            WHERE status = 'pending'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

def approve_raffle(raffle_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffles
            SET status = 'active'
            WHERE id = ?
            AND status = 'pending'
            """,
            (int(raffle_id),),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# CANCEL PENDING RAFFLE
# ==========================================================

def cancel_pending_raffle(raffle_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffles
            SET status = 'cancelled'
            WHERE id = ?
            AND status = 'pending'
            """,
            (int(raffle_id),),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# SET RAFFLE POST
# ==========================================================

def set_raffle_post(
    raffle_id,
    chat_id,
    message_id,
):

    conn = get_connection()

    try:

        conn.execute(
            """
            UPDATE raffles
            SET chat_id = ?,
                message_id = ?
            WHERE id = ?
            """,
            (
                int(chat_id),
                int(message_id),
                int(raffle_id),
            ),
        )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(raffle_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffles
            SET status = 'closed'
            WHERE id = ?
            AND status = 'active'
            """,
            (int(raffle_id),),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# EXPIRE RAFFLE
# ==========================================================

def expire_raffle(raffle_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffles
            SET status = 'closed'
            WHERE id = ?
            AND status = 'active'
            """,
            (int(raffle_id),),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# ADD RAFFLE ENTRY
#
# IMPORTANT:
# The duplicate check and INSERT happen inside the same
# transaction.
#
# Existing denied/removed entries do NOT block a new entry.
# Pending and approved entries do block duplicates.
# ==========================================================

def add_raffle_entry(
    raffle_id,
    user_id,
    username,
    display_name,
    payment_method,
):

    conn = get_connection()

    try:

        conn.execute("BEGIN IMMEDIATE")

        raffle = conn.execute(
            """
            SELECT
                id,
                expires_at,
                status
            FROM raffles
            WHERE id = ?
            LIMIT 1
            """,
            (int(raffle_id),),
        ).fetchone()

        if not raffle:

            conn.rollback()
            return None

        if raffle["status"] != "active":

            conn.rollback()
            return None

        # ==================================================
        # CHECK EXPIRATION
        # ==================================================

        expires_at = raffle["expires_at"]

        if expires_at:

            try:

                expires = datetime.fromisoformat(
                    str(expires_at).replace(
                        "Z",
                        "+00:00",
                    )
                )

                if expires.tzinfo is None:

                    from datetime import timezone

                    expires = expires.replace(
                        tzinfo=timezone.utc
                    )

                from datetime import timezone

                if datetime.now(
                    timezone.utc
                ) >= expires:

                    conn.execute(
                        """
                        UPDATE raffles
                        SET status = 'closed'
                        WHERE id = ?
                        AND status = 'active'
                        """,
                        (int(raffle_id),),
                    )

                    conn.commit()

                    return None

            except Exception:
                # Do not reject the entry merely because an
                # old/malformed expiration value cannot parse.
                pass

        # ==================================================
        # DUPLICATE CHECK
        # ==================================================

        existing = conn.execute(
            """
            SELECT id
            FROM raffle_entries
            WHERE raffle_id = ?
            AND user_id = ?
            AND status IN ('pending', 'approved')
            LIMIT 1
            """,
            (
                int(raffle_id),
                int(user_id),
            ),
        ).fetchone()

        if existing:

            conn.rollback()
            return None

        # ==================================================
        # INSERT
        # ==================================================

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO raffle_entries (
                raffle_id,
                user_id,
                username,
                display_name,
                payment_method,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                int(raffle_id),
                int(user_id),
                username,
                display_name,
                payment_method,
                utc_now(),
            ),
        )

        entry_id = cursor.lastrowid

        conn.commit()

        return entry_id

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# GET ENTRY
# ==========================================================

def get_entry(entry_id):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE id = ?
            """,
            (int(entry_id),),
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# PENDING ENTRIES
# ==========================================================

def get_pending_entries(
    raffle_id=None,
):

    conn = get_connection()

    try:

        if raffle_id is None:

            rows = conn.execute(
                """
                SELECT
                    e.*,
                    r.prize,
                    r.price
                FROM raffle_entries e
                LEFT JOIN raffles r
                    ON r.id = e.raffle_id
                WHERE e.status = 'pending'
                ORDER BY e.id ASC
                """
            ).fetchall()

        else:

            rows = conn.execute(
                """
                SELECT
                    e.*,
                    r.prize,
                    r.price
                FROM raffle_entries e
                LEFT JOIN raffles r
                    ON r.id = e.raffle_id
                WHERE e.status = 'pending'
                AND e.raffle_id = ?
                ORDER BY e.id ASC
                """,
                (int(raffle_id),),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id,
    approved_by,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffle_entries
            SET status = 'approved',
                approved_by = ?
            WHERE id = ?
            AND status = 'pending'
            """,
            (
                int(approved_by),
                int(entry_id),
            ),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# DENY ENTRY
# ==========================================================

def deny_entry(
    entry_id,
    denied_by,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffle_entries
            SET status = 'denied',
                approved_by = ?
            WHERE id = ?
            AND status = 'pending'
            """,
            (
                int(denied_by),
                int(entry_id),
            ),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# APPROVED ENTRIES
# ==========================================================

def get_approved_entries(
    raffle_id,
):

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE raffle_id = ?
            AND status = 'approved'
            ORDER BY id ASC
            """,
            (int(raffle_id),),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(entry_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM raffle_entries
            WHERE id = ?
            """,
            (int(entry_id),),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# CHECK USER ENTRY
# ==========================================================

def get_user_entry(
    raffle_id,
    user_id,
):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE raffle_id = ?
            AND user_id = ?
            AND status IN ('pending', 'approved')
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                int(raffle_id),
                int(user_id),
            ),
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# COUNT APPROVED ENTRIES
# ==========================================================

def count_approved_entries(raffle_id):

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT COUNT(*)
            FROM raffle_entries
            WHERE raffle_id = ?
            AND status = 'approved'
            """,
            (int(raffle_id),),
        ).fetchone()[0]

    finally:

        conn.close()


# ==========================================================
# SAVE / UPDATE BIRTHDAY
# ==========================================================

def save_birthday(
    user_id,
    chat_id,
    birthday,
    username=None,
    display_name=None,
):

    now = utc_now()

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO birthdays (
                user_id,
                chat_id,
                birthday,
                username,
                display_name,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id, chat_id)
            DO UPDATE SET
                birthday = excluded.birthday,
                username = excluded.username,
                display_name = excluded.display_name,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                chat_id,
                birthday,
                username,
                display_name,
                now,
                now,
            ),
        )

        conn.commit()

        return True

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# GET USER BIRTHDAY
# ==========================================================

def get_birthday(
    user_id,
    chat_id,
):

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM birthdays
            WHERE user_id = ?
            AND chat_id = ?
            LIMIT 1
            """,
            (
                user_id,
                chat_id,
            ),
        ).fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


# ==========================================================
# GET BIRTHDAYS FOR DATE
# ==========================================================

def get_birthdays_for_date(
    birthday,
):

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM birthdays
            WHERE birthday = ?
            ORDER BY display_name COLLATE NOCASE ASC
            """,
            (birthday,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


# ==========================================================
# GET ALL BIRTHDAYS
# ==========================================================

def get_all_birthdays():

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM birthdays
            ORDER BY
                CAST(substr(birthday, 1, 2) AS INTEGER),
                CAST(substr(birthday, 4, 2) AS INTEGER),
                display_name COLLATE NOCASE
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


# ==========================================================
# REMOVE USER BIRTHDAY
# ==========================================================

def remove_birthday(
    user_id,
    chat_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM birthdays
            WHERE user_id = ?
            AND chat_id = ?
            """,
            (
                user_id,
                chat_id,
            ),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# REMOVE BIRTHDAY BY DATABASE ID
# ==========================================================

def remove_birthday_by_id(
    birthday_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM birthdays
            WHERE id = ?
            """,
            (birthday_id,),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        return changed

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# DATABASE STATISTICS
# ==========================================================

def get_database_stats():

    conn = get_connection()

    try:

        raffle_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM raffles
            """
        ).fetchone()[0]

        entry_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM raffle_entries
            """
        ).fetchone()[0]

        birthday_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM birthdays
            """
        ).fetchone()[0]

        member_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM members
            """
        ).fetchone()[0]

        pending_entries = conn.execute(
            """
            SELECT COUNT(*)
            FROM raffle_entries
            WHERE status = 'pending'
            """
        ).fetchone()[0]

        approved_entries = conn.execute(
            """
            SELECT COUNT(*)
            FROM raffle_entries
            WHERE status = 'approved'
            """
        ).fetchone()[0]

        return {
            "database": DB_NAME,
            "raffles": raffle_count,
            "raffle_entries": entry_count,
            "birthdays": birthday_count,
            "members": member_count,
            "pending_entries": pending_entries,
            "approved_entries": approved_entries,
        }

    finally:

        conn.close()


# ==========================================================
# DATABASE INTEGRITY CHECK
# ==========================================================

def check_database_integrity():

    conn = get_connection()

    try:

        result = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        return result == "ok"

    finally:

        conn.close()


# ==========================================================
# STARTUP DIAGNOSTICS
# ==========================================================

try:

    stats = get_database_stats()
    integrity_ok = check_database_integrity()

    print("==========================================================")
    print("Melanated AZ Bot - Database Statistics")
    print("==========================================================")
    print("Database          :", stats["database"])
    print("Raffles           :", stats["raffles"])
    print("Raffle Entries    :", stats["raffle_entries"])
    print("Approved Entries  :", stats["approved_entries"])
    print("Pending Entries   :", stats["pending_entries"])
    print("Birthdays         :", stats["birthdays"])
    print("Known Members     :", stats["members"])
    print(
        "Integrity         :",
        "OK" if integrity_ok else "FAILED",
    )
    print("==========================================================")

    if not integrity_ok:

        raise RuntimeError(
            "SQLite database integrity check FAILED."
        )

except Exception as exc:

    print(
        "WARNING: Could not read database statistics."
    )

    print(
        "Database error:",
        exc,
    )


# ==========================================================
# END raffle_database.py
# ==========================================================
