import sqlite3
from datetime import datetime
from config import DATABASE_NAME


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Members table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_date TEXT,
        last_active TEXT
    )
    """)

    # Birthdays table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays (
        user_id INTEGER PRIMARY KEY,
        birthday TEXT
    )
    """)

    # Moderation logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moderation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        details TEXT,
        timestamp TEXT
    )
    """)

    # Member check-ins
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message_sent TEXT,
        response TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def update_member(user):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO members
    (user_id, username, first_name, joined_date, last_active)
    VALUES (?, ?, ?, ?, ?)

    ON CONFLICT(user_id)
    DO UPDATE SET
        username=?,
        first_name=?,
        last_active=?
    """,
    (
        user.id,
        user.username,
        user.first_name,
        now,
        now,
        user.username,
        user.first_name,
        now
    ))

    conn.commit()
    conn.close()


def log_action(user_id, action, details=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO moderation_logs
    (user_id, action, details, timestamp)
    VALUES (?, ?, ?, ?)
    """,
    (
        user_id,
        action,
        details,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
