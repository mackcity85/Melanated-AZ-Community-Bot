"""Read-only Event OCR database diagnostics for the existing admin panel.

This module never creates, updates, deletes, or republishes Event records.
"""

import html
import logging
import os
import sqlite3
import sys
from urllib.parse import quote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import admin
import event_ocr

logger = logging.getLogger("event_database_diagnostic")
DB_PATH = event_ocr.DB_PATH
EVENT_TOPIC_ID = event_ocr.EVENT_TOPIC_ID


def _readonly_connection():
    # mode=ro is intentional: a missing database must be reported as missing,
    # never silently created as a new empty SQLite file.
    uri = "file:" + quote(os.path.abspath(DB_PATH), safe="/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=5)


def collect_diagnostics():
    result = {
        "path": DB_PATH,
        "exists": os.path.isfile(DB_PATH),
        "size": None,
        "integrity": "NOT CHECKED",
        "table_exists": False,
        "total": 0,
        "statuses": {},
        "missing_file_id": 0,
        "approved_missing_published_id": 0,
        "error": None,
    }

    if not result["exists"]:
        result["integrity"] = "DATABASE FILE NOT FOUND"
        return result

    try:
        result["size"] = os.path.getsize(DB_PATH)
        with _readonly_connection() as conn:
            check = conn.execute("PRAGMA quick_check").fetchone()
            result["integrity"] = str(check[0]) if check else "NO RESULT"

            table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='event_submissions'"
            ).fetchone()
            if not table:
                result["integrity"] = result["integrity"] + " | event_submissions TABLE MISSING"
                return result

            result["table_exists"] = True
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(event_submissions)")
            }
            required = {"id", "status", "file_id", "published_message_id"}
            missing_columns = sorted(required - columns)
            if missing_columns:
                result["error"] = "Missing expected columns: " + ", ".join(missing_columns)
                return result

            result["total"] = int(
                conn.execute("SELECT COUNT(*) FROM event_submissions").fetchone()[0]
            )
            for status, count in conn.execute(
                "SELECT status, COUNT(*) FROM event_submissions GROUP BY status ORDER BY status"
            ):
                result["statuses"][str(status or "(blank)")] = int(count)

            result["missing_file_id"] = int(conn.execute(
                "SELECT COUNT(*) FROM event_submissions "
                "WHERE file_id IS NULL OR TRIM(file_id)=''"
            ).fetchone()[0])
            result["approved_missing_published_id"] = int(conn.execute(
                "SELECT COUNT(*) FROM event_submissions "
                "WHERE status='approved' AND published_message_id IS NULL"
            ).fetchone()[0])

    except sqlite3.Error as exc:
        result["integrity"] = "CHECK FAILED"
        result["error"] = f"SQLite: {exc}"
        logger.exception("Read-only Event database diagnostic failed")
    except Exception as exc:
        result["integrity"] = "CHECK FAILED"
        result["error"] = str(exc)
        logger.exception("Event database diagnostic failed")

    return result


def _diagnostic_text(data):
    if not data["exists"]:
        return (
            "🧰 <b>EVENT DATABASE DIAGNOSTIC</b>\n\n"
            "🔴 <b>Database file not found</b>\n"
            f"Path: <code>{html.escape(str(data['path']))}</code>\n\n"
            "No database was created. Check the Render persistent-disk mount and deployment configuration."
        )

    statuses = data["statuses"]
    status_lines = [
        f"• {html.escape(str(name))}: <b>{count}</b>"
        for name, count in sorted(statuses.items())
    ] or ["• No submissions found"]

    integrity_ok = data["integrity"].strip().lower() == "ok"
    integrity_label = "🟢 OK" if integrity_ok else "🔴 " + html.escape(str(data["integrity"]))
    size_label = f"{data['size']:,} bytes" if isinstance(data["size"], int) else "Unavailable"

    lines = [
        "🧰 <b>EVENT DATABASE DIAGNOSTIC</b>",
        "",
        f"Database: <code>{html.escape(str(data['path']))}</code>",
        f"File size: <b>{size_label}</b>",
        f"SQLite integrity: <b>{integrity_label}</b>",
        f"Submission table: <b>{'Present' if data['table_exists'] else 'Missing'}</b>",
        f"Total submissions: <b>{data['total']}</b>",
        "",
        "<b>Records by status</b>",
        *status_lines,
        "",
        f"Missing flyer file IDs: <b>{data['missing_file_id']}</b>",
        f"Approved without published message ID: <b>{data['approved_missing_published_id']}</b>",
        "",
        f"Telegram destination: topic <code>{EVENT_TOPIC_ID}</code>",
        "",
        "🔒 Read-only check. No records or Telegram posts were changed.",
        "Note: this checks saved message IDs, not whether Telegram still has each message.",
    ]
    if data["error"]:
        lines.extend(["", "⚠️ <b>Additional detail:</b> " + html.escape(str(data["error"]))])
    return "\n".join(lines)


async def show_event_database_diagnostic(update, context):
    if not await admin.require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer("Checking Event database...")
    data = collect_diagnostics()
    await query.edit_message_text(
        _diagnostic_text(data),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Run Check Again", callback_data="admin_event_db_diagnostic")],
            [InlineKeyboardButton("📅 Events Controls", callback_data="admin_events")],
            [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
        ]),
    )


def install():
    """Add one admin button and route its callback without replacing other handlers."""
    if getattr(admin, "_event_db_diagnostic_installed", False):
        return

    previous_keyboard = admin.admin_main_keyboard

    def patched_admin_main_keyboard(*args, **kwargs):
        keyboard = previous_keyboard(*args, **kwargs)
        rows = [list(row) for row in (keyboard.inline_keyboard or [])]
        if not any(
            getattr(button, "callback_data", None) == "admin_event_db_diagnostic"
            for row in rows for button in row
        ):
            rows.append([
                InlineKeyboardButton("🧰 Event Database Diagnostic", callback_data="admin_event_db_diagnostic")
            ])
        return InlineKeyboardMarkup(rows)

    bot_module = sys.modules.get("bot")
    previous_handler = getattr(bot_module, "admin_button", None) if bot_module else None
    if previous_handler is None:
        previous_handler = admin.admin_button

    async def patched_admin_button(update, context):
        query = update.callback_query
        if query and query.data == "admin_event_db_diagnostic":
            await show_event_database_diagnostic(update, context)
            return
        await previous_handler(update, context)

    admin.admin_main_keyboard = patched_admin_main_keyboard
    admin.admin_button = patched_admin_button
    if bot_module is not None:
        bot_module.admin_button = patched_admin_button

    admin._event_db_diagnostic_installed = True
    logger.info(
        "Read-only Event database diagnostic installed | database=%s | topic=%s",
        DB_PATH, EVENT_TOPIC_ID,
    )
