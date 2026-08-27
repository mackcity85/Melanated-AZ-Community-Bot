# ==========================================================

# Melanated AZ Bot

# raffle_database.py

#

# Persistent SQLite database for:

# - Raffles

# - Raffle Entries

# - Birthdays

#

# PRODUCTION STORAGE:

# Render Persistent Disk:

# /var/data

#

# Database:

# /var/data/raffle.db

#

# IMPORTANT:

# This module NEVER falls back to the application filesystem.

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
"Required database location:\n"
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
"Verify your Render service has a Persistent Disk with:\n\n"
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
print("Database path           :", DB_NAME)
print("Database directory      :", DB_DIR)
print("Database exists         :", os.path.exists(DB_NAME))
print(
"Database size           :",
os.path.getsize(DB_NAME)
if os.path.exists(DB_NAME)
else 0,
)
print(
"Persistent directory    :",
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

```
conn.row_factory = sqlite3.Row

# ------------------------------------------------------
# WAL
# ------------------------------------------------------

try:
    conn.execute(
        "PRAGMA journal_mode=WAL"
    )
except Exception as e:
    print(
        "WARNING: Could not enable SQLite WAL mode:",
        e,
    )

# ------------------------------------------------------
# Foreign Keys
# ------------------------------------------------------

conn.execute(
    "PRAGMA foreign_keys=ON"
)

# ------------------------------------------------------
# Busy Timeout
# ------------------------------------------------------

conn.execute(
    "PRAGMA busy_timeout=30000"
)

return conn
```

# ==========================================================

# INITIALIZE DATABASE

# ==========================================================

def initialize_database():
conn = get_connection()

```
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
        idx_raffle_entries_raffle_id
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
        idx_birthdays_chat_id
        ON birthdays(chat_id)
        """
    )

    conn.commit()

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
```

# ==========================================================

# INITIALIZE WHEN MODULE LOADS

# ==========================================================

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

```
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

    raffle_id = cursor.lastrowid

    conn.commit()

    return raffle_id

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
```

# ==========================================================

# GET RAFFLE

# ==========================================================

def get_raffle(
raffle_id,
):
conn = get_connection()

```
try:
    row = conn.execute(
        """
        SELECT *
        FROM raffles
        WHERE id = ?
        """,
        (raffle_id,),
    ).fetchone()

    return dict(row) if row else None

finally:
    conn.close()
```

# ==========================================================

# ACTIVE RAFFLE

# ==========================================================

def get_active_raffle():
conn = get_connection()

```
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
```

# ==========================================================

# PENDING RAFFLE

# ==========================================================

def get_pending_raffle():
conn = get_connection()

```
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
```

# ==========================================================

# APPROVE RAFFLE

# ==========================================================

def approve_raffle(
raffle_id,
):
conn = get_connection()

```
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

    changed = cursor.rowcount > 0

    conn.commit()

    return changed

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
```

# ==========================================================

# CANCEL PENDING RAFFLE

# ==========================================================

def cancel_pending_raffle(
raffle_id,
):
conn = get_connection()

```
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

    changed = cursor.rowcount > 0

    conn.commit()

    return changed

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
```

# ==========================================================

# SET RAFFLE POST

# ==========================================================

def set_raffle_post(
raffle_id,
chat_id,
message_id,
):
conn = get_connection()

```
try:
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

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
```

# ==========================================================

# CLOSE RAFFLE

# ==========================================================

def close_raffle(
raffle_id,
):
conn = get_connection()

```
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

    changed = cursor.rowcount > 0

    conn.commit()

    return changed

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
```

# ==========================================================

# ADD RAFFLE ENTRY

# ==========================================================

def add_raffle_entry(
raffle_id,
user_id,
username,
display_name,
payment_method,
):
conn = get_connection()

```
try:
    # --------------------------------------------------
    # Verify raffle exists and is active.
    # --------------------------------------------------

    raffle = conn.execute(
        """
        SELECT id
        FROM raffles
        WHERE id = ?
        AND status = 'active'
        LIMIT 1
        """,
        (raffle_id,),
    ).fetchone()

    if not raffle:
        return None

    # --------------------------------------------------
    # Prevent duplicate pending/approved entries.
    # --------------------------------------------------

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
            raffle_id,
            user_id,
        ),
    ).fetchone()

    if existing:
        return None

    # --------------------------------------------------
    # Insert entry.
    # --------------------------------------------------

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
            datetime.utcnow().isoformat(),
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
```

# ==========================================================

# GET ENTRY

# ==========================================================

def get_entry(
entry_id,
):
conn = get_connection()

```
try:
    row = conn.execute(
        """
        SELECT *
        FROM raffle_entries
        WHERE id = ?
        """,
        (entry_id,),
    ).fetchone()

    return dict(row) if row else None

finally:
    conn.close()
```

# ==========================================================

# PENDING ENTRIES

# ==========================================================

def get_pending_entries():
conn = get_connection()

```
try:
    rows = conn.execute(
        """
        SELECT *
        FROM raffle_entries
        WHERE status = 'pending'
        ORDER BY id ASC
        """
    ).fetchall()

    return [
        dict(row)
        for row in rows
    ]

finally:
    conn.close()
```

# ==========================================================

# APPROVE ENTRY

# ==========================================================

def approve_entry(
entry_id,
approved_by,
):
conn = get_connection()

```
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
            approved_by,
            entry_id,
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
```

# ==========================================================

# DENY ENTRY

# ==========================================================

def deny_entry(
entry_id,
denied_by,
):
conn = get_connection()

```
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
            denied_by,
            entry_id,
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
```

# ==========================================================

# APPROVED ENTRIES

# ==========================================================

def get_approved_entries(
raffle_id,
):
conn = get_connection()

```
try:
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

    return [
        dict(row)
        for row in rows
    ]

finally:
    conn.close()
```

# ==========================================================

# REMOVE ENTRY

# ==========================================================

def remove_entry(
entry_id,
):
conn = get_connection()

```
try:
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

    return changed

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
```

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

```
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
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
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
```

# ==========================================================

# GET USER BIRTHDAY

# ==========================================================

def get_birthday(
user_id,
chat_id,
):
conn = get_connection()

```
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
```

# ==========================================================

# GET BIRTHDAYS FOR DATE

# ==========================================================

def get_birthdays_for_date(
birthday,
):
conn = get_connection()

```
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
```

# ==========================================================

# GET ALL BIRTHDAYS

# ==========================================================

def get_all_birthdays():
conn = get_connection()

```
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
```

# ==========================================================

# REMOVE USER BIRTHDAY

# ==========================================================

def remove_birthday(
user_id,
chat_id,
):
conn = get_connection()

```
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
```

# ==========================================================

# REMOVE BIRTHDAY BY DATABASE ID

# ==========================================================

def remove_birthday_by_id(
birthday_id,
):
conn = get_connection()

```
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
```

# ==========================================================

# DATABASE STATISTICS

# ==========================================================

def get_database_stats():
conn = get_connection()

```
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

    return {
        "database": DB_NAME,
        "raffles": raffle_count,
        "raffle_entries": entry_count,
        "birthdays": birthday_count,
    }

finally:
    conn.close()
```

# ==========================================================

# DATABASE INTEGRITY CHECK

# ==========================================================

def check_database_integrity():
conn = get_connection()

```
try:
    result = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    return result == "ok"

finally:
    conn.close()
```

# ==========================================================

# STARTUP DIAGNOSTICS

# ==========================================================

try:
stats = get_database_stats()

```
integrity_ok = check_database_integrity()

print("==========================================================")
print("Melanated AZ Bot - Database Statistics")
print("==========================================================")
print("Database      :", stats["database"])
print("Raffles       :", stats["raffles"])
print("Raffle Entries:", stats["raffle_entries"])
print("Birthdays     :", stats["birthdays"])
print(
    "Integrity     :",
    "OK" if integrity_ok else "FAILED",
)
print("==========================================================")

if not integrity_ok:
    raise RuntimeError(
        "SQLite database integrity check FAILED."
    )
```

except Exception as e:
print(
"WARNING: Could not read database statistics."
)
print(
"Database error:",
e,
)

# ==========================================================

# END raffle_database.py

# ==========================================================
