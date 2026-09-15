# ==========================================================
# Melanated AZ - Holiday Exchange
# Reusable holiday gift-exchange system.
# ==========================================================

import logging
import os
import random
import sqlite3
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import RAFFLE_CHAT_ID

logger = logging.getLogger("melanated_az_holiday_exchange")

DB_PATH = (
    "/var/data/holiday_exchange.db"
    if os.path.isdir("/var/data")
    else "./holiday_exchange.db"
)


# ==========================================================
# CENTRALIZED ADMIN AUTHORIZATION
# ==========================================================

async def is_admin(user_id, context):
    """
    Use the centralized Melanated AZ admin authorization.

    ADMIN_GROUP_ID membership is the primary authorization source.
    ADMIN_IDS remains the configured fallback through admin.py.

    This is intentionally imported inside the function to avoid
    a circular import because admin.py imports this module.
    """
    try:
        from admin import is_admin as centralized_is_admin

        return await centralized_is_admin(
            user_id,
            context,
        )

    except Exception:
        logger.exception(
            "Centralized Holiday Exchange admin authorization failed | "
            "user_id=%s",
            user_id,
        )
        return False


# ==========================================================
# DATABASE
# ==========================================================

def db_connect():
    os.makedirs(
        os.path.dirname(DB_PATH) or ".",
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# TIME HELPERS
# ==========================================================

def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_deadline(value):
    if not value:
        return None

    text = str(value).strip()

    try:
        dt = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )

    except ValueError:

        for fmt in (
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%b %d, %Y",
        ):

            try:
                dt = datetime.strptime(
                    text,
                    fmt,
                )

                dt = dt.replace(
                    tzinfo=timezone.utc
                )

                break

            except ValueError:
                continue

        else:
            return None

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(timezone.utc)


def format_deadline(value):

    dt = parse_deadline(value)

    if not dt:
        return str(
            value or "Not set"
        )

    return dt.strftime(
        "%b %d, %Y at %I:%M %p UTC"
    )


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_holiday_exchange_database():

    with db_connect() as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS holiday_exchanges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holiday TEXT NOT NULL,
                name TEXT NOT NULL,
                spending_limit TEXT NOT NULL,
                signup_deadline TEXT NOT NULL,
                gift_deadline TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                closed_at TEXT,
                drawn_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exchange_participants (
                exchange_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                display_name TEXT,
                joined_at TEXT NOT NULL,
                left_at TEXT,
                PRIMARY KEY (exchange_id, user_id),
                FOREIGN KEY (exchange_id)
                    REFERENCES holiday_exchanges(id)
                    ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exchange_matches (
                exchange_id INTEGER NOT NULL,
                giver_user_id INTEGER NOT NULL,
                receiver_user_id INTEGER NOT NULL,
                sent_at TEXT,
                PRIMARY KEY (exchange_id, giver_user_id),
                UNIQUE (exchange_id, receiver_user_id),
                FOREIGN KEY (exchange_id)
                    REFERENCES holiday_exchanges(id)
                    ON DELETE CASCADE
            )
            """
        )

        conn.commit()


# ==========================================================
# EXCHANGE CRUD
# ==========================================================

def create_exchange(
    holiday,
    name,
    spending_limit,
    signup_deadline,
    gift_deadline,
):

    with db_connect() as conn:

        cur = conn.execute(
            """
            INSERT INTO holiday_exchanges
                (
                    holiday,
                    name,
                    spending_limit,
                    signup_deadline,
                    gift_deadline,
                    status,
                    created_at
                )
            VALUES (?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                holiday,
                name,
                spending_limit,
                signup_deadline,
                gift_deadline,
                iso_now(),
            ),
        )

        conn.commit()

        return int(cur.lastrowid)


def get_exchange(exchange_id):

    with db_connect() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM holiday_exchanges
            WHERE id=?
            """,
            (
                int(exchange_id),
            ),
        ).fetchone()

        return (
            dict(row)
            if row
            else None
        )


def get_active_exchange():

    with db_connect() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM holiday_exchanges
            WHERE status='open'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        return (
            dict(row)
            if row
            else None
        )


def list_recent_exchanges(limit=10):

    with db_connect() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM holiday_exchanges
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                int(limit),
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def close_exchange(exchange_id):

    with db_connect() as conn:

        cur = conn.execute(
            """
            UPDATE holiday_exchanges
            SET
                status='closed',
                closed_at=?
            WHERE id=?
              AND status='open'
            """,
            (
                iso_now(),
                int(exchange_id),
            ),
        )

        conn.commit()

        return cur.rowcount > 0


def cancel_exchange(exchange_id):

    with db_connect() as conn:

        cur = conn.execute(
            """
            UPDATE holiday_exchanges
            SET
                status='cancelled',
                closed_at=?
            WHERE id=?
              AND status IN ('open','closed')
            """,
            (
                iso_now(),
                int(exchange_id),
            ),
        )

        conn.commit()

        return cur.rowcount > 0


# ==========================================================
# PARTICIPANTS
# ==========================================================

def add_participant(
    exchange_id,
    user_id,
    username,
    display_name,
):

    with db_connect() as conn:

        event = conn.execute(
            """
            SELECT
                status,
                signup_deadline
            FROM holiday_exchanges
            WHERE id=?
            """,
            (
                int(exchange_id),
            ),
        ).fetchone()

        if not event or event["status"] != "open":
            return False, "Signups are closed."

        deadline = parse_deadline(
            event["signup_deadline"]
        )

        if deadline and utc_now() > deadline:
            return False, "The signup deadline has passed."

        conn.execute(
            """
            INSERT INTO exchange_participants
                (
                    exchange_id,
                    user_id,
                    username,
                    display_name,
                    joined_at,
                    left_at
                )
            VALUES (?, ?, ?, ?, ?, NULL)
            ON CONFLICT(exchange_id, user_id)
            DO UPDATE SET
                username=excluded.username,
                display_name=excluded.display_name,
                left_at=NULL,
                joined_at=excluded.joined_at
            """,
            (
                int(exchange_id),
                int(user_id),
                username,
                display_name,
                iso_now(),
            ),
        )

        conn.commit()

        return True, "You're in!"


def remove_participant(
    exchange_id,
    user_id,
):

    with db_connect() as conn:

        event = conn.execute(
            """
            SELECT status
            FROM holiday_exchanges
            WHERE id=?
            """,
            (
                int(exchange_id),
            ),
        ).fetchone()

        if not event or event["status"] != "open":
            return False, "Signups are closed."

        conn.execute(
            """
            UPDATE exchange_participants
            SET left_at=?
            WHERE exchange_id=?
              AND user_id=?
              AND left_at IS NULL
            """,
            (
                iso_now(),
                int(exchange_id),
                int(user_id),
            ),
        )

        conn.commit()

        return True, "You've been removed from the exchange."


def get_participants(
    exchange_id,
    active_only=True,
):

    with db_connect() as conn:

        sql = """
            SELECT *
            FROM exchange_participants
            WHERE exchange_id=?
        """

        if active_only:
            sql += " AND left_at IS NULL"

        sql += """
            ORDER BY
                display_name COLLATE NOCASE,
                user_id
        """

        rows = conn.execute(
            sql,
            (
                int(exchange_id),
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def participant_count(exchange_id):

    with db_connect() as conn:

        row = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM exchange_participants
            WHERE exchange_id=?
              AND left_at IS NULL
            """,
            (
                int(exchange_id),
            ),
        ).fetchone()

        return int(row["c"])


# ==========================================================
# MATCHES
# ==========================================================

def get_user_match(
    exchange_id,
    user_id,
):

    with db_connect() as conn:

        row = conn.execute(
            """
            SELECT
                m.*,
                p.username,
                p.display_name
            FROM exchange_matches m
            LEFT JOIN exchange_participants p
              ON p.exchange_id=m.exchange_id
             AND p.user_id=m.receiver_user_id
            WHERE m.exchange_id=?
              AND m.giver_user_id=?
            """,
            (
                int(exchange_id),
                int(user_id),
            ),
        ).fetchone()

        return (
            dict(row)
            if row
            else None
        )


def _build_derangement(ids):

    if len(ids) < 2:
        return None

    receivers = list(ids)

    for _ in range(1000):

        random.shuffle(receivers)

        if all(
            giver != receiver
            for giver, receiver
            in zip(ids, receivers)
        ):
            return receivers

    # Deterministic fallback:
    # rotate by one.
    receivers = ids[1:] + ids[:1]

    return receivers


def draw_exchange(exchange_id):

    with db_connect() as conn:

        event = conn.execute(
            """
            SELECT *
            FROM holiday_exchanges
            WHERE id=?
            """,
            (
                int(exchange_id),
            ),
        ).fetchone()

        if not event:
            return False, "Exchange not found.", []

        if event["status"] == "drawn":
            return (
                False,
                "This exchange has already been drawn.",
                [],
            )

        if event["status"] == "cancelled":
            return (
                False,
                "This exchange is cancelled.",
                [],
            )

        participants = conn.execute(
            """
            SELECT user_id
            FROM exchange_participants
            WHERE exchange_id=?
              AND left_at IS NULL
            """,
            (
                int(exchange_id),
            ),
        ).fetchall()

        ids = [
            int(row["user_id"])
            for row in participants
        ]

        if len(ids) < 2:
            return (
                False,
                "You need at least 2 participants to draw matches.",
                [],
            )

        receivers = _build_derangement(ids)

        if receivers is None:
            return (
                False,
                "Unable to create matches.",
                [],
            )

        conn.execute(
            """
            DELETE FROM exchange_matches
            WHERE exchange_id=?
            """,
            (
                int(exchange_id),
            ),
        )

        for giver, receiver in zip(
            ids,
            receivers,
        ):

            conn.execute(
                """
                INSERT INTO exchange_matches
                    (
                        exchange_id,
                        giver_user_id,
                        receiver_user_id
                    )
                VALUES (?, ?, ?)
                """,
                (
                    int(exchange_id),
                    giver,
                    receiver,
                ),
            )

        conn.execute(
            """
            UPDATE holiday_exchanges
            SET
                status='drawn',
                closed_at=COALESCE(
                    closed_at,
                    ?
                ),
                drawn_at=?
            WHERE id=?
            """,
            (
                iso_now(),
                iso_now(),
                int(exchange_id),
            ),
        )

        conn.commit()

        return (
            True,
            "Matches drawn successfully.",
            list(zip(ids, receivers)),
        )


# ==========================================================
# KEYBOARDS
# ==========================================================

def exchange_member_keyboard(exchange_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎁 JOIN EXCHANGE",
                    callback_data=f"hx_join_{exchange_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🚪 LEAVE EXCHANGE",
                    callback_data=f"hx_leave_{exchange_id}",
                )
            ],
        ]
    )


def admin_exchange_keyboard(
    exchange_id,
    status,
):

    rows = []

    if status == "open":

        rows.append(
            [
                InlineKeyboardButton(
                    "🔒 CLOSE SIGNUPS",
                    callback_data=f"admin_hx_close_{exchange_id}",
                ),
                InlineKeyboardButton(
                    "🎲 DRAW MATCHES",
                    callback_data=f"admin_hx_draw_{exchange_id}",
                ),
            ]
        )

    elif status == "closed":

        rows.append(
            [
                InlineKeyboardButton(
                    "🎲 DRAW MATCHES",
                    callback_data=f"admin_hx_draw_{exchange_id}",
                )
            ]
        )

    if status in {
        "open",
        "closed",
    }:

        rows.append(
            [
                InlineKeyboardButton(
                    "❌ CANCEL",
                    callback_data=f"admin_hx_cancel_{exchange_id}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔄 STATUS",
                callback_data=f"admin_hx_status_{exchange_id}",
            )
        ]
    )

    return InlineKeyboardMarkup(rows)


# ==========================================================
# PUBLIC TEXT
# ==========================================================

def exchange_public_text(
    event,
    count,
):

    return (
        f"🎁 <b>{event['name']}</b>\n\n"
        f"🏷️ <b>Holiday / Theme:</b> {event['holiday']}\n"
        f"💵 <b>Spending Limit:</b> {event['spending_limit']}\n"
        f"📅 <b>Sign Up By:</b> "
        f"{format_deadline(event['signup_deadline'])}\n"
        f"🎁 <b>Gift By:</b> "
        f"{format_deadline(event['gift_deadline'])}\n"
        f"👥 <b>Participants:</b> {count}\n\n"
        "🤫 Your match is private. Nobody else will see who you were assigned.\n\n"
        "Ready to participate?"
    )


# ==========================================================
# POST EXCHANGE
# ==========================================================

async def post_exchange(
    context,
    exchange_id=None,
    chat_id=None,
    thread_id=None,
):

    event = (
        get_exchange(exchange_id)
        if exchange_id
        else get_active_exchange()
    )

    if not event:
        return None

    count = participant_count(
        event["id"]
    )

    text = exchange_public_text(
        event,
        count,
    )

    return await context.bot.send_message(
        chat_id=int(
            chat_id or RAFFLE_CHAT_ID
        ),
        message_thread_id=(
            int(thread_id)
            if thread_id
            else None
        ),
        text=text,
        reply_markup=(
            exchange_member_keyboard(
                event["id"]
            )
            if event["status"] == "open"
            else None
        ),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# /HOLIDAYEXCHANGE
# ==========================================================

async def holiday_exchange_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    event = get_active_exchange()

    if not event:

        await update.effective_message.reply_text(
            "🎁 There is no active Holiday Exchange right now."
        )

        return

    try:

        sent = await post_exchange(
            context,
            event["id"],
            update.effective_chat.id,
        )

        if sent:
            await update.effective_message.delete()

    except TelegramError:

        logger.exception(
            "Could not post Holiday Exchange message."
        )


# ==========================================================
# /CREATEEXCHANGE
# ==========================================================

async def create_exchange_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    # ======================================================
    # FIXED:
    # Use centralized admin authorization.
    # ADMIN_GROUP_ID is now honored.
    # ======================================================

    if not user or not await is_admin(
        user.id,
        context,
    ):

        await update.effective_message.reply_text(
            "⛔ Admins only."
        )

        return

    payload = " ".join(
        context.args
    ).strip()

    parts = [
        x.strip()
        for x in payload.split("|")
    ]

    if len(parts) != 5:

        await update.effective_message.reply_text(
            "Use:\n"
            "<code>/createexchange "
            "Holiday | Exchange Name | Spending Limit | "
            "Signup Deadline | Gift Deadline</code>\n\n"
            "Example:\n"
            "<code>/createexchange Christmas | "
            "Melanated AZ Secret Santa | $25 | "
            "2026-12-10 | 2026-12-20</code>",
            parse_mode=ParseMode.HTML,
        )

        return

    (
        holiday,
        name,
        spending_limit,
        signup_deadline,
        gift_deadline,
    ) = parts

    if not all(parts):

        await update.effective_message.reply_text(
            "⚠️ All five fields are required."
        )

        return

    if get_active_exchange():

        await update.effective_message.reply_text(
            "⚠️ There is already an active Holiday Exchange. "
            "Close or cancel it first."
        )

        return

    if (
        not parse_deadline(signup_deadline)
        or not parse_deadline(gift_deadline)
    ):

        await update.effective_message.reply_text(
            "⚠️ Use dates like 2026-12-10 or 12/10/2026."
        )

        return

    exchange_id = create_exchange(
        holiday,
        name,
        spending_limit,
        signup_deadline,
        gift_deadline,
    )

    event = get_exchange(
        exchange_id
    )

    await update.effective_message.reply_text(
        "✅ <b>HOLIDAY EXCHANGE CREATED</b>\n\n"
        + exchange_public_text(
            event,
            0,
        )
        + "\n\n"
        "Use /holidayexchange to post it to the group.",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_exchange_keyboard(
            exchange_id,
            "open",
        ),
    )


# ==========================================================
# MEMBER CALLBACK
# ==========================================================

async def holiday_exchange_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    # ======================================================
    # JOIN
    # ======================================================

    if data.startswith("hx_join_"):

        exchange_id = int(
            data[len("hx_join_"):]
        )

        event = get_exchange(
            exchange_id
        )

        if not event:

            await query.answer(
                "Exchange not found.",
                show_alert=True,
            )

            return

        ok, detail = add_participant(
            exchange_id,
            user.id,
            user.username,
            user.full_name
            or user.first_name
            or str(user.id),
        )

        try:

            await query.answer(
                (
                    "✅ " + detail
                    if ok
                    else "⚠️ " + detail
                ),
                show_alert=True,
            )

        except Exception:
            pass

        if ok:

            try:

                await context.bot.send_message(
                    chat_id=user.id,
                    text=(
                        f"🎁 <b>YOU'RE IN — "
                        f"{event['name']}</b>\n\n"
                        f"🏷️ {event['holiday']}\n"
                        f"💵 Spending limit: "
                        f"<b>{event['spending_limit']}</b>\n"
                        f"📅 Gift by: "
                        f"<b>{format_deadline(event['gift_deadline'])}</b>\n\n"
                        "I'll send your private match after "
                        "the draw. 🤫"
                    ),
                    parse_mode=ParseMode.HTML,
                )

            except TelegramError:

                logger.info(
                    "Could not DM Holiday Exchange "
                    "join confirmation to %s",
                    user.id,
                )

            admin_group = os.environ.get(
                "ADMIN_GROUP_ID",
                "",
            ).strip()

            if admin_group:

                try:

                    await context.bot.send_message(
                        chat_id=int(admin_group),
                        text=(
                            "🎁 <b>HOLIDAY EXCHANGE JOINED</b>\n\n"
                            f"🏷️ <b>{event['holiday']}</b>\n"
                            f"🎁 {event['name']}\n"
                            f"👤 "
                            f"{user.full_name or user.username or user.id}\n"
                            f"🆔 <code>{user.id}</code>\n"
                            f"👥 Participants: "
                            f"<b>{participant_count(exchange_id)}</b>"
                        ),
                        parse_mode=ParseMode.HTML,
                    )

                except TelegramError:

                    logger.info(
                        "Could not send Holiday Exchange "
                        "join notice to admin group"
                    )

        return

    # ======================================================
    # LEAVE
    # ======================================================

    if data.startswith("hx_leave_"):

        exchange_id = int(
            data[len("hx_leave_"):]
        )

        ok, detail = remove_participant(
            exchange_id,
            user.id,
        )

        try:

            await query.answer(
                (
                    "✅ " + detail
                    if ok
                    else "⚠️ " + detail
                ),
                show_alert=True,
            )

        except Exception:
            pass

        return


# ==========================================================
# ADMIN CALLBACK
# ==========================================================

async def holiday_exchange_admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    # ======================================================
    # FIXED:
    # Centralized async admin authorization.
    #
    # IMPORTANT:
    # Do NOT use:
    #     is_admin(user.id)
    #
    # It must be:
    #     await is_admin(user.id, context)
    # ======================================================

    if (
        not query
        or not user
        or not await is_admin(
            user.id,
            context,
        )
    ):

        if query:

            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )

        return

    data = query.data or ""

    # ======================================================
    # MAIN HOLIDAY EXCHANGE ADMIN PAGE
    # ======================================================

    if data == "admin_holiday_exchange":

        event = get_active_exchange()

        if event:

            text = (
                "🎁 <b>HOLIDAY EXCHANGE ADMIN</b>\n\n"
                + exchange_public_text(
                    event,
                    participant_count(
                        event["id"]
                    ),
                )
            )

            await query.answer()

            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=admin_exchange_keyboard(
                    event["id"],
                    event["status"],
                ),
            )

        else:

            await query.answer()

            await query.edit_message_text(
                "🎁 <b>HOLIDAY EXCHANGE</b>\n\n"
                "Create a holiday-specific exchange with:\n"
                "<code>/createexchange "
                "Holiday | Exchange Name | Spending Limit | "
                "Signup Deadline | Gift Deadline</code>\n\n"
                "Example:\n"
                "<code>/createexchange Christmas | "
                "Melanated AZ Secret Santa | $25 | "
                "2026-12-10 | 2026-12-20</code>",
                parse_mode=ParseMode.HTML,
            )

        return

    # ======================================================
    # ADMIN ACTIONS
    # ======================================================

    prefix_map = {
        "admin_hx_close_": "close",
        "admin_hx_draw_": "draw",
        "admin_hx_cancel_": "cancel",
        "admin_hx_status_": "status",
    }

    action = next(
        (
            name
            for prefix, name
            in prefix_map.items()
            if data.startswith(prefix)
        ),
        None,
    )

    if action is None:
        return

    try:

        exchange_id = int(
            data.split("_")[-1]
        )

    except ValueError:

        await query.answer(
            "Invalid exchange ID.",
            show_alert=True,
        )

        return

    event = get_exchange(
        exchange_id
    )

    if not event:

        await query.answer(
            "Exchange not found.",
            show_alert=True,
        )

        return

    # ======================================================
    # CLOSE
    # ======================================================

    if action == "close":

        changed = close_exchange(
            exchange_id
        )

        await query.answer(
            (
                "Signups closed."
                if changed
                else "Signups already closed."
            )
        )

        event = get_exchange(
            exchange_id
        )

    # ======================================================
    # CANCEL
    # ======================================================

    elif action == "cancel":

        changed = cancel_exchange(
            exchange_id
        )

        await query.answer(
            (
                "Exchange cancelled."
                if changed
                else "Exchange already closed."
            )
        )

        event = get_exchange(
            exchange_id
        )

    # ======================================================
    # DRAW
    # ======================================================

    elif action == "draw":

        ok, detail, matches = draw_exchange(
            exchange_id
        )

        await query.answer(
            detail,
            show_alert=True,
        )

        if ok:

            event = get_exchange(
                exchange_id
            )

            for giver_id, _receiver_id in matches:

                match = get_user_match(
                    exchange_id,
                    giver_id,
                )

                if not match:
                    continue

                try:

                    await context.bot.send_message(
                        chat_id=int(giver_id),
                        text=(
                            f"🎁 <b>YOUR "
                            f"{event['name'].upper()} MATCH</b>\n\n"
                            f"🏷️ Holiday / Theme: "
                            f"<b>{event['holiday']}</b>\n"
                            f"💵 Spending limit: "
                            f"<b>{event['spending_limit']}</b>\n"
                            f"📅 Gift by: "
                            f"<b>{format_deadline(event['gift_deadline'])}</b>\n\n"
                            f"🎯 <b>Your recipient:</b> "
                            f"{match.get('display_name') or match['receiver_user_id']}"
                            + (
                                f" (@{match['username']})"
                                if match.get("username")
                                else ""
                            )
                            + "\n\n"
                            "🤫 Keep it secret! "
                            "Have fun with it. 💜"
                        ),
                        parse_mode=ParseMode.HTML,
                    )

                    with db_connect() as conn:

                        conn.execute(
                            """
                            UPDATE exchange_matches
                            SET sent_at=?
                            WHERE exchange_id=?
                              AND giver_user_id=?
                            """,
                            (
                                iso_now(),
                                exchange_id,
                                giver_id,
                            ),
                        )

                        conn.commit()

                except TelegramError:

                    logger.info(
                        "Could not DM Holiday Exchange "
                        "match to %s",
                        giver_id,
                    )

        event = get_exchange(
            exchange_id
        )

    # ======================================================
    # STATUS
    # ======================================================

    else:

        await query.answer()

    # ======================================================
    # REFRESH ADMIN DISPLAY
    # ======================================================

    count = participant_count(
        exchange_id
    )

    text = (
        "🎁 <b>HOLIDAY EXCHANGE ADMIN</b>\n\n"
        + exchange_public_text(
            event,
            count,
        )
    )

    text += (
        f"\n\n<b>Status:</b> "
        f"{event['status'].upper()}"
    )

    if event.get("drawn_at"):

        text += (
            f"\n<b>Drawn:</b> "
            f"{format_deadline(event['drawn_at'])}"
        )

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=(
            admin_exchange_keyboard(
                exchange_id,
                event["status"],
            )
            if event["status"]
            in {"open", "closed"}
            else None
        ),
    )


# ==========================================================
# /MYEXCHANGEMATCH
# ==========================================================

async def my_exchange_match_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if (
        not user
        or update.effective_chat.type != "private"
    ):
        return

    # Most recent exchange with a match for this user.
    with db_connect() as conn:

        row = conn.execute(
            """
            SELECT
                m.exchange_id,
                m.receiver_user_id,
                m.sent_at,
                e.name,
                e.holiday,
                e.spending_limit,
                e.gift_deadline,
                p.display_name,
                p.username
            FROM exchange_matches m
            JOIN holiday_exchanges e
              ON e.id=m.exchange_id
            LEFT JOIN exchange_participants p
              ON p.exchange_id=m.exchange_id
             AND p.user_id=m.receiver_user_id
            WHERE m.giver_user_id=?
            ORDER BY m.exchange_id DESC
            LIMIT 1
            """,
            (
                int(user.id),
            ),
        ).fetchone()

    if not row:

        await update.effective_message.reply_text(
            "🤫 You don't have a Holiday Exchange match yet."
        )

        return

    await update.effective_message.reply_text(
        f"🎁 <b>{row['name']}</b>\n\n"
        f"🏷️ {row['holiday']}\n"
        f"💵 Spending limit: "
        f"<b>{row['spending_limit']}</b>\n"
        f"📅 Gift by: "
        f"<b>{format_deadline(row['gift_deadline'])}</b>\n\n"
        f"🎯 <b>Your recipient:</b> "
        f"{row['display_name'] or row['receiver_user_id']}"
        + (
            f" (@{row['username']})"
            if row["username"]
            else ""
        )
        + "\n\n"
        "🤫 Keep it secret!",
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# END holiday_exchange.py
# ==========================================================
