# ==========================================================
# Melanated AZ Bot - raffle_database.py
# DROP-IN / DATABASE-SAFE VERSION
#
# IMPORTANT:
# - Uses /var/data/raffle.db only
# - NEVER deletes, resets, or replaces the database
# - CREATE TABLE IF NOT EXISTS preserves existing data
# - Adds missing columns/tables/indexes when needed
# ==========================================================

import os
import sqlite3
from datetime import datetime

DEFAULT_DB_NAME = "/var/data/raffle.db"
DB_NAME = os.environ.get("RAFFLE_DB_NAME", DEFAULT_DB_NAME).strip()
DB_NAME = os.path.abspath(DB_NAME)
DB_DIR = os.path.dirname(DB_NAME)

if not DB_NAME.startswith("/var/data/"):
    raise RuntimeError(
        "FATAL: RAFFLE_DB_NAME must point to /var/data/raffle.db"
    )

if not os.path.isdir(DB_DIR):
    raise RuntimeError(
        "FATAL: Render Persistent Disk must be mounted at /var/data"
    )

print("==========================================================")
print("Melanated AZ Bot - Persistent Database")
print("==========================================================")
print("Database path       :", DB_NAME)
print("Database directory  :", DB_DIR)
print("Database exists     :", os.path.exists(DB_NAME))
print("Database size       :", os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0)
print("Persistent directory:", os.path.isdir("/var/data"))
print("==========================================================")

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception as exc:
        print("WARNING: WAL unavailable:", exc)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def _columns(conn, table):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}

def _add_column_if_missing(conn, table, column, definition):
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def initialize_database():
    conn = get_connection()
    try:
        c = conn.cursor()

        c.execute("""
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
        """)

        c.execute("""
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
                FOREIGN KEY (raffle_id) REFERENCES raffles(id) ON DELETE CASCADE
            )
        """)

        c.execute("""
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
        """)

        c.execute("""
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
        """)

        # Safe migrations for older versions of the bot.
        _add_column_if_missing(c.connection, "raffles", "chat_id", "INTEGER")
        _add_column_if_missing(c.connection, "raffles", "message_id", "INTEGER")
        _add_column_if_missing(c.connection, "raffles", "created_at", "TEXT")
        _add_column_if_missing(c.connection, "raffle_entries", "username", "TEXT")
        _add_column_if_missing(c.connection, "raffle_entries", "display_name", "TEXT")
        _add_column_if_missing(c.connection, "raffle_entries", "payment_method", "TEXT")
        _add_column_if_missing(c.connection, "raffle_entries", "status", "TEXT NOT NULL DEFAULT 'pending'")
        _add_column_if_missing(c.connection, "raffle_entries", "approved_by", "INTEGER")
        _add_column_if_missing(c.connection, "raffle_entries", "created_at", "TEXT")

        for sql in (
            "CREATE INDEX IF NOT EXISTS idx_raffles_status ON raffles(status)",
            "CREATE INDEX IF NOT EXISTS idx_raffle_entries_raffle_id ON raffle_entries(raffle_id)",
            "CREATE INDEX IF NOT EXISTS idx_raffle_entries_status ON raffle_entries(status)",
            "CREATE INDEX IF NOT EXISTS idx_birthdays_chat_id ON birthdays(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_members_chat_id ON members(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_members_display_name ON members(display_name COLLATE NOCASE)",
        ):
            c.execute(sql)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

initialize_database()

def save_member(user_id, chat_id, username=None, display_name=None):
    if user_id is None or chat_id is None:
        return False
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO members
                (user_id, chat_id, username, display_name, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET
                username=excluded.username,
                display_name=excluded.display_name,
                last_seen_at=excluded.last_seen_at
        """, (int(user_id), int(chat_id), username, display_name, now, now))
        conn.commit()
        return True
    finally:
        conn.close()

def get_members(chat_id, limit=1000):
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM members
            WHERE chat_id=?
            ORDER BY COALESCE(NULLIF(display_name,''), NULLIF(username,''), CAST(user_id AS TEXT)) COLLATE NOCASE
            LIMIT ?
        """, (int(chat_id), int(limit))).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_member(user_id, chat_id):
    conn = get_connection()
    try:
        r = conn.execute(
            "SELECT * FROM members WHERE user_id=? AND chat_id=? LIMIT 1",
            (int(user_id), int(chat_id))
        ).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def create_raffle(prize, price, expires_at):
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO raffles (prize, price, expires_at, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (prize, price, expires_at, datetime.utcnow().isoformat()))
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_raffle(raffle_id):
    conn = get_connection()
    try:
        r = conn.execute("SELECT * FROM raffles WHERE id=?", (int(raffle_id),)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def get_active_raffle():
    conn = get_connection()
    try:
        r = conn.execute("""
            SELECT * FROM raffles WHERE status='active'
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def get_pending_raffle():
    conn = get_connection()
    try:
        r = conn.execute("""
            SELECT * FROM raffles WHERE status='pending'
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def approve_raffle(raffle_id):
    conn = get_connection()
    try:
        cur = conn.execute("""
            UPDATE raffles SET status='active'
            WHERE id=? AND status='pending'
        """, (int(raffle_id),))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def cancel_pending_raffle(raffle_id):
    conn = get_connection()
    try:
        cur = conn.execute("""
            UPDATE raffles SET status='cancelled'
            WHERE id=? AND status='pending'
        """, (int(raffle_id),))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def set_raffle_post(raffle_id, chat_id, message_id):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE raffles SET chat_id=?, message_id=? WHERE id=?
        """, (int(chat_id), int(message_id), int(raffle_id)))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def close_raffle(raffle_id):
    conn = get_connection()
    try:
        cur = conn.execute("""
            UPDATE raffles SET status='closed'
            WHERE id=? AND status='active'
        """, (int(raffle_id),))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def add_raffle_entry(raffle_id, user_id, username, display_name, payment_method=None):
    conn = get_connection()
    try:
        raffle = conn.execute(
            "SELECT id FROM raffles WHERE id=? AND status='active' LIMIT 1",
            (int(raffle_id),)
        ).fetchone()
        if not raffle:
            return None

        existing = conn.execute("""
            SELECT id FROM raffle_entries
            WHERE raffle_id=? AND user_id=?
              AND status IN ('pending','approved')
            LIMIT 1
        """, (int(raffle_id), int(user_id))).fetchone()
        if existing:
            return None

        cur = conn.execute("""
            INSERT INTO raffle_entries
                (raffle_id, user_id, username, display_name, payment_method, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """, (
            int(raffle_id), int(user_id), username, display_name,
            payment_method, datetime.utcnow().isoformat()
        ))
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_entry(entry_id):
    conn = get_connection()
    try:
        r = conn.execute("""
            SELECT e.*, r.prize, r.price, r.expires_at, r.status AS raffle_status
            FROM raffle_entries e
            LEFT JOIN raffles r ON r.id=e.raffle_id
            WHERE e.id=?
        """, (int(entry_id),)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def get_raffle_entries(raffle_id):
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT e.*, r.prize, r.price, r.expires_at, r.status AS raffle_status
            FROM raffle_entries e
            LEFT JOIN raffles r ON r.id=e.raffle_id
            WHERE e.raffle_id=?
            ORDER BY e.id ASC
        """, (int(raffle_id),)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_pending_entries(raffle_id=None):
    conn = get_connection()
    try:
        sql = """
            SELECT e.*, r.prize, r.price, r.expires_at, r.status AS raffle_status
            FROM raffle_entries e
            LEFT JOIN raffles r ON r.id=e.raffle_id
            WHERE e.status='pending'
        """
        params = []
        if raffle_id is not None:
            sql += " AND e.raffle_id=?"
            params.append(int(raffle_id))
        sql += " ORDER BY e.id ASC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def approve_entry(entry_id, approved_by):
    # Atomic state transition. This is the critical approval fix.
    conn = get_connection()
    try:
        cur = conn.execute("""
            UPDATE raffle_entries
            SET status='approved', approved_by=?
            WHERE id=? AND status='pending'
        """, (int(approved_by), int(entry_id)))
        conn.commit()
        return cur.rowcount == 1
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def deny_entry(entry_id, denied_by):
    conn = get_connection()
    try:
        cur = conn.execute("""
            UPDATE raffle_entries
            SET status='denied', approved_by=?
            WHERE id=? AND status='pending'
        """, (int(denied_by), int(entry_id)))
        conn.commit()
        return cur.rowcount == 1
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_approved_entries(raffle_id):
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT e.*, r.prize, r.price, r.expires_at, r.status AS raffle_status
            FROM raffle_entries e
            LEFT JOIN raffles r ON r.id=e.raffle_id
            WHERE e.raffle_id=? AND e.status='approved'
            ORDER BY e.id ASC
        """, (int(raffle_id),)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def remove_entry(entry_id):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM raffle_entries WHERE id=?", (int(entry_id),))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def save_birthday(user_id, chat_id, birthday, username=None, display_name=None):
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO birthdays
                (user_id, chat_id, birthday, username, display_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET
                birthday=excluded.birthday,
                username=excluded.username,
                display_name=excluded.display_name,
                updated_at=excluded.updated_at
        """, (user_id, chat_id, birthday, username, display_name, now, now))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_birthday(user_id, chat_id):
    conn = get_connection()
    try:
        r = conn.execute(
            "SELECT * FROM birthdays WHERE user_id=? AND chat_id=? LIMIT 1",
            (user_id, chat_id)
        ).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def get_birthdays_for_date(birthday):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM birthdays WHERE birthday=? ORDER BY display_name COLLATE NOCASE",
            (birthday,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_all_birthdays():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM birthdays
            ORDER BY
                CAST(substr(birthday,1,2) AS INTEGER),
                CAST(substr(birthday,4,2) AS INTEGER),
                display_name COLLATE NOCASE
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def remove_birthday(user_id, chat_id):
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM birthdays WHERE user_id=? AND chat_id=?",
            (user_id, chat_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def remove_birthday_by_id(birthday_id):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM birthdays WHERE id=?", (birthday_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def get_database_stats():
    conn = get_connection()
    try:
        return {
            "database": DB_NAME,
            "raffles": conn.execute("SELECT COUNT(*) FROM raffles").fetchone()[0],
            "raffle_entries": conn.execute("SELECT COUNT(*) FROM raffle_entries").fetchone()[0],
            "birthdays": conn.execute("SELECT COUNT(*) FROM birthdays").fetchone()[0],
            "members": conn.execute("SELECT COUNT(*) FROM members").fetchone()[0],
        }
    finally:
        conn.close()

def check_database_integrity():
    conn = get_connection()
    try:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()

try:
    stats = get_database_stats()
    print("==========================================================")
    print("Melanated AZ Bot - Database Statistics")
    print("==========================================================")
    print("Database       :", stats["database"])
    print("Raffles        :", stats["raffles"])
    print("Raffle Entries :", stats["raffle_entries"])
    print("Birthdays      :", stats["birthdays"])
    print("Known Members  :", stats["members"])
    print("Integrity      :", "OK" if check_database_integrity() else "FAILED")
    print("==========================================================")
except Exception as exc:
    print("WARNING: Could not read database statistics:", exc)
