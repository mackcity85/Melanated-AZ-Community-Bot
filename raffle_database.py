# ==========================================================
# Melanated AZ Bot
# raffle_database.py
# ==========================================================

import os
import sqlite3
from datetime import datetime


DB_NAME = os.environ.get(
    "RAFFLE_DB_NAME",
    "raffle.db",
)


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():

    conn = sqlite3.connect(
        DB_NAME,
        timeout=30,
    )

    conn.row_factory = sqlite3.Row

    # Better concurrent SQLite behavior.
    try:
        conn.execute(
            "PRAGMA journal_mode=WAL"
        )
    except Exception:
        pass

    conn.execute(
        "PRAGMA foreign_keys=ON"
    )

    return conn


# ==========================================================
# INITIALIZE
# ==========================================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    # ======================================================
    # RAFFLES
    # ======================================================

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

    # ======================================================
    # ENTRIES
    # ======================================================

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

    # ======================================================
    # BIRTHDAYS
    # ======================================================

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

    conn.commit()

    conn.close()


initialize_database()


# ==========================================================
# RAFFLE CREATION
# ==========================================================

def create_raffle(
    prize,
    price,
    expires_at,
):

    conn = get_connection()

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
            datetime.utcnow().isoformat(),
        ),
    )

    raffle_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return raffle_id


# ==========================================================
# GET RAFFLE
# ==========================================================

def get_raffle(
    raffle_id,
):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM raffles
        WHERE id = ?
        """,
        (raffle_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

def get_active_raffle():

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM raffles
        WHERE status = 'active'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    return dict(row) if row else None


# ==========================================================
# PENDING RAFFLE
# ==========================================================

def get_pending_raffle():

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM raffles
        WHERE status = 'pending'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    return dict(row) if row else None


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

def approve_raffle(
    raffle_id,
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE raffles

        SET status = 'active'

        WHERE id = ?

        AND status = 'pending'
        """,
        (raffle_id,),
    )

    changed = cursor.rowcount > 0

    conn.commit()

    conn.close()

    return changed


# ==========================================================
# CANCEL PENDING
# ==========================================================

def cancel_pending_raffle(
    raffle_id,
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE raffles

        SET status = 'cancelled'

        WHERE id = ?

        AND status = 'pending'
        """,
        (raffle_id,),
    )

    changed = cursor.rowcount > 0

    conn.commit()

    conn.close()

    return changed


# ==========================================================
# SET RAFFLE POST
# ==========================================================

def set_raffle_post(
    raffle_id,
    chat_id,
    message_id,
):

    conn = get_connection()

    conn.execute(
        """
        UPDATE raffles

        SET chat_id = ?,
            message_id = ?

        WHERE id = ?
        """,
        (
            chat_id,
            message_id,
            raffle_id,
        ),
    )

    conn.commit()

    conn.close()


# ==========================================================
# CLOSE RAFFLE
# ==========================================================

def close_raffle(
    raffle_id,
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE raffles

        SET status = 'closed'

        WHERE id = ?

        AND status = 'active'
        """,
        (raffle_id,),
    )

    changed = cursor.rowcount > 0

    conn.commit()

    conn.close()

    return changed


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

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT id

        FROM raffle_entries

        WHERE raffle_id = ?

        AND user_id = ?

        AND status IN (
            'pending',
            'approved'
        )

        LIMIT 1
        """,
        (
            raffle_id,
            user_id,
        ),
    ).fetchone()

    if existing:

        conn.close()

        return None

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

        VALUES (
            ?, ?, ?, ?, ?, 'pending', ?
        )
        """,
        (
            raffle_id,
            user_id,
            username,
            display_name,
            payment_method,
            datetime.utcnow().isoformat(),
        ),
    )

    entry_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return entry_id


# ==========================================================
# GET ENTRY
# ==========================================================

def get_entry(
    entry_id,
):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM raffle_entries
        WHERE id = ?
        """,
        (entry_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


# ==========================================================
# PENDING ENTRIES
# ==========================================================

def get_pending_entries():

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM raffle_entries
        WHERE status = 'pending'
        ORDER BY id ASC
        """
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# APPROVE ENTRY
# ==========================================================

def approve_entry(
    entry_id,
    approved_by,
):

    conn = get_connection()

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
            approved_by,
            entry_id,
        ),
    )

    changed = cursor.rowcount > 0

    conn.commit()

    conn.close()

    return changed


# ==========================================================
# DENY ENTRY
# ==========================================================

def deny_entry(
    entry_id,
    denied_by,
):

    conn = get_connection()

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
            denied_by,
            entry_id,
        ),
    )

    changed = cursor.rowcount > 0

    conn.commit()

    conn.close()

    return changed


# ==========================================================
# APPROVED ENTRIES
# ==========================================================

def get_approved_entries(
    raffle_id,
):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM raffle_entries

        WHERE raffle_id = ?

        AND status = 'approved'

        ORDER BY id ASC
        """,
        (raffle_id,),
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# REMOVE ENTRY
# ==========================================================

def remove_entry(
    entry_id,
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM raffle_entries
        WHERE id = ?
        """,
        (entry_id,),
    )

    changed = cursor.rowcount > 0

    conn.commit()

    conn.close()

    return changed


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

    now = datetime.utcnow().isoformat()

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

            VALUES (
                ?, ?, ?, ?, ?, ?, ?
            )

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

    conn.close()

    return dict(row) if row else None


# ==========================================================
# GET BIRTHDAYS FOR DATE
# ==========================================================

def get_birthdays_for_date(
    birthday,
):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM birthdays

        WHERE birthday = ?

        ORDER BY
            display_name COLLATE NOCASE ASC
        """,
        (birthday,),
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# GET ALL BIRTHDAYS
# ==========================================================

def get_all_birthdays():

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM birthdays

        ORDER BY
            CAST(
                substr(birthday, 1, 2)
                AS INTEGER
            ),

            CAST(
                substr(birthday, 4, 2)
                AS INTEGER
            ),

            display_name COLLATE NOCASE
        """
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# REMOVE USER BIRTHDAY
# ==========================================================

def remove_birthday(
    user_id,
    chat_id,
):

    conn = get_connection()

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

    conn.close()

    return changed


# ==========================================================
# REMOVE BIRTHDAY BY DATABASE ID
# ==========================================================

def remove_birthday_by_id(
    birthday_id,
):

    conn = get_connection()

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

    conn.close()

    return changed
