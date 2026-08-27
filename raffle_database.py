# ==========================================================
# Melanated AZ Bot
# raffle_database.py
#
# IMPORTANT:
# - Raffle data and birthday data are separate.
# - Closing/deleting a raffle NEVER deletes birthdays.
# - Birthday records are permanent until the user removes
#   or changes their own birthday.
# ==========================================================

import os
import sqlite3
from datetime import datetime


# ==========================================================
# DATABASE LOCATION
# ==========================================================

DB_NAME = os.environ.get(
    "RAFFLE_DB_NAME",
    "raffle.db"
)


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

    return conn


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def init_database():

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
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                approved_by INTEGER,
                created_at TEXT NOT NULL,
                approved_at TEXT,
                FOREIGN KEY (raffle_id)
                    REFERENCES raffles(id)
            )
            """
        )

        # ==================================================
        # BIRTHDAYS
        #
        # THIS TABLE IS COMPLETELY SEPARATE FROM RAFFLES.
        #
        # Nothing in raffle cleanup touches this table.
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS birthdays (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                username TEXT,
                display_name TEXT,
                birthday TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                PRIMARY KEY (
                    user_id,
                    chat_id
                )
            )
            """
        )

        # ==================================================
        # INDEXES
        # ==================================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_raffles_status
            ON raffles(status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_raffle_entries_raffle
            ON raffle_entries(raffle_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_raffle_entries_status
            ON raffle_entries(status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_birthdays_date
            ON birthdays(birthday)
            """
        )

        conn.commit()

    finally:

        conn.close()


# ==========================================================
# RAFFLE FUNCTIONS
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
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

        return cursor.lastrowid

    finally:

        conn.close()


def get_raffle(
    raffle_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM raffles
            WHERE id = ?
            """,
            (raffle_id,),
        )

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


def get_active_raffle():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM raffles
            WHERE status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


def get_pending_raffle():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM raffles
            WHERE status = 'pending'
            ORDER BY id DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


def approve_raffle(
    raffle_id,
):

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
            (raffle_id,),
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


def cancel_pending_raffle(
    raffle_id,
):

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
            (raffle_id,),
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


def close_raffle(
    raffle_id,
):

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
            (raffle_id,),
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


def set_raffle_post(
    raffle_id,
    chat_id,
    message_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
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

    finally:

        conn.close()


# ==========================================================
# RAFFLE ENTRY FUNCTIONS
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

        cursor = conn.cursor()

        # Prevent duplicate pending/approved entry.
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

            return None

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
                raffle_id,
                user_id,
                username,
                display_name,
                payment_method,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

        return cursor.lastrowid

    finally:

        conn.close()


def get_entry(
    entry_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE id = ?
            """,
            (entry_id,),
        )

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


def get_pending_entries():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE status = 'pending'
            ORDER BY id ASC
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        conn.close()


def approve_entry(
    entry_id,
    admin_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffle_entries
            SET status = 'approved',
                approved_by = ?,
                approved_at = ?
            WHERE id = ?
            AND status = 'pending'
            """,
            (
                admin_id,
                datetime.utcnow().isoformat(),
                entry_id,
            ),
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


def deny_entry(
    entry_id,
    admin_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffle_entries
            SET status = 'denied',
                approved_by = ?,
                approved_at = ?
            WHERE id = ?
            AND status = 'pending'
            """,
            (
                admin_id,
                datetime.utcnow().isoformat(),
                entry_id,
            ),
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


def get_approved_entries(
    raffle_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM raffle_entries
            WHERE raffle_id = ?
            AND status = 'approved'
            ORDER BY id ASC
            """,
            (raffle_id,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        conn.close()


def remove_entry(
    entry_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM raffle_entries
            WHERE id = ?
            """,
            (entry_id,),
        )

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


# ==========================================================
# BIRTHDAY FUNCTIONS
#
# IMPORTANT:
# These functions NEVER modify raffle tables.
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

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO birthdays (
                user_id,
                chat_id,
                username,
                display_name,
                birthday,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id, chat_id)
            DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                birthday = excluded.birthday,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                chat_id,
                username,
                display_name,
                birthday,
                now,
                now,
            ),
        )

        conn.commit()

        return True

    finally:

        conn.close()


def get_birthday(
    user_id,
    chat_id,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM birthdays
            WHERE user_id = ?
            AND chat_id = ?
            """,
            (
                user_id,
                chat_id,
            ),
        )

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:

        conn.close()


def get_birthdays_for_date(
    month_day,
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM birthdays
            WHERE birthday = ?
            ORDER BY display_name COLLATE NOCASE
            """,
            (month_day,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        conn.close()


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

        conn.commit()

        return cursor.rowcount > 0

    finally:

        conn.close()


def get_all_birthdays():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM birthdays
            ORDER BY birthday, display_name
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        conn.close()


# ==========================================================
# INITIALIZE DATABASE
#
# This only CREATES missing tables.
# It does NOT delete or reset anything.
# ==========================================================

init_database()
