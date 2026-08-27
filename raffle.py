# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Complete raffle system
#
# IMPORTANT:
# - Uses the existing raffle_database.py
# - Does NOT delete or recreate existing raffle data
# - Works with Telegram callback_query AND normal messages
# - Fixes "update.message is None" for admin buttons
# - Compatible with python-telegram-bot 21.x
# ==========================================================

import logging
import random
from datetime import datetime, timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

import raffle_database as db


logger = logging.getLogger(__name__)


# ==========================================================
# CONSTANTS
# ==========================================================

WAITING_FOR_RAFFLE = 1


# ==========================================================
# SAFE TELEGRAM RESPONSE HELPERS
# ==========================================================

async def reply_or_edit(
    update: Update,
    text: str,
    reply_markup=None,
    parse_mode=None,
):
    """
    Send/edit a response regardless of whether the update came
    from a message or an inline callback button.

    This is the important fix for:
        update.message is None
    """

    try:

        # --------------------------------------------------
        # NORMAL MESSAGE
        # --------------------------------------------------

        if update.message is not None:

            return await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )

        # --------------------------------------------------
        # CALLBACK QUERY
        # --------------------------------------------------

        if update.callback_query is not None:

            query = update.callback_query

            try:
                await query.answer()
            except Exception:
                pass

            # Try editing the existing admin message first.
            try:

                return await query.edit_message_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )

            except Exception:

                pass

            # If editing fails, send a new message.
            try:

                return await query.message.reply_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )

            except Exception:

                pass

            # Last fallback.
            return await query.get_bot().send_message(
                chat_id=query.from_user.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )

    except Exception:

        logger.exception("Unable to send raffle response")

    return None


async def send_to_user(
    update: Update,
    text: str,
    reply_markup=None,
    parse_mode=None,
):
    """
    Safely send a private/admin response.
    """

    try:

        if update.callback_query is not None:

            user_id = update.callback_query.from_user.id

            return await update.callback_query.get_bot().send_message(
                chat_id=user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )

        if update.effective_user is not None:

            return await update.get_bot().send_message(
                chat_id=update.effective_user.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )

    except Exception:

        logger.exception("Unable to send private raffle message")

    return None


# ==========================================================
# ADMIN CHECK
# ==========================================================

def _get_admin_ids():

    try:

        from config import ADMIN_IDS

        return [
            int(x)
            for x in ADMIN_IDS
        ]

    except Exception:

        pass

    try:

        import os

        value = os.environ.get(
            "ADMIN_IDS",
            "",
        )

        if not value:
            return []

        return [
            int(x.strip())
            for x in value.split(",")
            if x.strip()
        ]

    except Exception:

        return []


def is_admin_user(user_id):

    try:

        return int(user_id) in _get_admin_ids()

    except Exception:

        return False


def is_admin(update: Update):

    if update.effective_user is None:
        return False

    return is_admin_user(
        update.effective_user.id
    )


# ==========================================================
# FORMATTING
# ==========================================================

def format_countdown(expires_at):

    if not expires_at:
        return "Unknown"

    try:

        expires = datetime.fromisoformat(
            expires_at.replace("Z", "+00:00")
        )

        if expires.tzinfo is None:
            expires = expires.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        seconds = int(
            (expires - now).total_seconds()
        )

        if seconds <= 0:
            return "Expired"

        days, remainder = divmod(
            seconds,
            86400,
        )

        hours, remainder = divmod(
            remainder,
            3600,
        )

        minutes, _ = divmod(
            remainder,
            60,
        )

        parts = []

        if days:
            parts.append(f"{days}d")

        if hours:
            parts.append(f"{hours}h")

        if minutes:
            parts.append(f"{minutes}m")

        if not parts:
            return "Less than 1 minute"

        return " ".join(parts)

    except Exception:

        return str(expires_at)


def format_raffle(raffle):

    if not raffle:
        return "No raffle found."

    raffle_id = raffle.get("id")

    prize = raffle.get(
        "prize",
        "Unknown",
    )

    price = raffle.get(
        "price",
        "Unknown",
    )

    status = raffle.get(
        "status",
        "unknown",
    )

    expires = format_countdown(
        raffle.get("expires_at")
    )

    return (
        f"🎟️ <b>Melanated AZ Friends Raffle</b>\n\n"
        f"💰 <b>Prize:</b> {prize}\n"
        f"💵 <b>Entry:</b> {price}\n"
        f"📌 <b>Status:</b> {status.title()}\n"
        f"⏳ <b>Time Remaining:</b> {expires}\n"
        f"🆔 <b>Raffle ID:</b> {raffle_id}"
    )


def display_name_from_entry(entry):

    name = entry.get("display_name")

    if name:
        return str(name)

    username = entry.get("username")

    if username:
        return f"@{username}"

    return str(
        entry.get(
            "user_id",
            "Unknown",
        )
    )


# ==========================================================
# KEYBOARDS
# ==========================================================

def raffle_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER RAFFLE",
                    callback_data="raffle_enter",
                )
            ],
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data="raffle_cashapp",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data="raffle_zelle",
                )
            ],
        ]
    )


def payment_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 Cash App",
                    callback_data="raffle_cashapp",
                ),
                InlineKeyboardButton(
                    "💳 Zelle",
                    callback_data="raffle_zelle",
                ),
            ],
        ]
    )


def admin_entry_keyboard(entry_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"raffle_approve:{entry_id}",
                ),
                InlineKeyboardButton(
                    "❌ DENY",
                    callback_data=f"raffle_deny:{entry_id}",
                ),
            ]
        ]
    )


def admin_raffle_keyboard(raffle_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE RAFFLE",
                    callback_data=f"raffle_approve_raffle:{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ CANCEL RAFFLE",
                    callback_data=f"raffle_cancel_raffle:{raffle_id}",
                )
            ],
        ]
    )


# ==========================================================
# CREATE RAFFLE
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ You are not authorized to start a raffle."
        )

        return ConversationHandler.END

    await reply_or_edit(
        update,
        (
            "🎟️ <b>Start a New Raffle</b>\n\n"
            "Send the raffle information in this format:\n\n"
            "<code>$100 Cash Prize | $5</code>\n\n"
            "Example:\n"
            "<code>$100 Cash Prize | $5</code>"
        ),
        parse_mode="HTML",
    )

    return WAITING_FOR_RAFFLE


# ==========================================================
# RECEIVE RAFFLE SETUP
# ==========================================================

async def receive_raffle_setup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        return ConversationHandler.END

    if update.message is None:

        return ConversationHandler.END

    text = (
        update.message.text or ""
    ).strip()

    if "|" not in text:

        await update.message.reply_text(
            (
                "❌ Invalid format.\n\n"
                "Use:\n"
                "<code>$100 Cash Prize | $5</code>"
            ),
            parse_mode="HTML",
        )

        return WAITING_FOR_RAFFLE

    try:

        prize, price = [
            x.strip()
            for x in text.split(
                "|",
                1,
            )
        ]

        if not prize or not price:
            raise ValueError

    except Exception:

        await update.message.reply_text(
            (
                "❌ Invalid raffle format.\n\n"
                "Use:\n"
                "<code>$100 Cash Prize | $5</code>"
            ),
            parse_mode="HTML",
        )

        return WAITING_FOR_RAFFLE

    # ------------------------------------------------------
    # RAFFLE DURATION
    # ------------------------------------------------------

    try:

        import os

        duration_days = float(
            os.environ.get(
                "RAFFLE_DURATION_DAYS",
                "7",
            )
        )

    except Exception:

        duration_days = 7

    from datetime import timedelta

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=duration_days)
    ).isoformat()

    # ------------------------------------------------------
    # CREATE DATABASE RECORD
    # ------------------------------------------------------

    raffle_id = db.create_raffle(
        prize=prize,
        price=price,
        expires_at=expires_at,
    )

    raffle = db.get_raffle(
        raffle_id
    )

    # ------------------------------------------------------
    # ADMIN APPROVAL
    # ------------------------------------------------------

    await update.message.reply_text(
        (
            "🎟️ <b>RAFFLE CREATED</b>\n\n"
            f"💰 <b>Prize:</b> {prize}\n"
            f"💵 <b>Entry:</b> {price}\n"
            f"⏳ <b>Duration:</b> {duration_days:g} days\n"
            f"🆔 <b>Raffle ID:</b> {raffle_id}\n\n"
            "The raffle is currently <b>pending approval</b>.\n"
            "Approve it below to post it in the group."
        ),
        reply_markup=admin_raffle_keyboard(
            raffle_id
        ),
        parse_mode="HTML",
    )

    return ConversationHandler.END


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

async def approve_raffle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    if not is_admin(update):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    try:

        raffle_id = int(
            query.data.split(":")[1]
        )

    except Exception:

        await query.answer(
            "Invalid raffle.",
            show_alert=True,
        )

        return

    raffle = db.get_raffle(
        raffle_id
    )

    if not raffle:

        await query.answer(
            "Raffle not found.",
            show_alert=True,
        )

        return

    changed = db.approve_raffle(
        raffle_id
    )

    if not changed:

        await query.answer(
            "Raffle is no longer pending.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # GET RAFFLE CHAT ID
    # ------------------------------------------------------

    try:

        import os

        chat_id = int(
            os.environ.get(
                "RAFFLE_CHAT_ID"
            )
        )

    except Exception:

        chat_id = None

    if not chat_id:

        await query.message.reply_text(
            (
                "⚠️ Raffle approved, but "
                "RAFFLE_CHAT_ID is not configured."
            )
        )

        return

    # ------------------------------------------------------
    # POST RAFFLE
    # ------------------------------------------------------

    try:

        message = await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🎟️ <b>Melanated AZ Friends Raffle</b>\n\n"
                f"💰 <b>Prize:</b> {raffle['prize']}\n"
                f"💵 <b>Entry:</b> {raffle['price']}\n"
                f"⏳ <b>Time Remaining:</b> "
                f"{format_countdown(raffle['expires_at'])}\n\n"
                "Want to join?\n"
                "Click <b>ENTER RAFFLE</b> below.\n\n"
                "Your payment and entry will be "
                "verified by Melanated AZ before "
                "your entry is approved."
            ),
            reply_markup=raffle_keyboard(),
            parse_mode="HTML",
        )

        db.set_raffle_post(
            raffle_id,
            chat_id,
            message.message_id,
        )

    except Exception:

        logger.exception(
            "Unable to post approved raffle"
        )

        await query.message.reply_text(
            "❌ Raffle approved but could not be posted."
        )

        return

    try:

        await query.edit_message_text(
            (
                "✅ <b>RAFFLE APPROVED</b>\n\n"
                f"Raffle #{raffle_id} is now active "
                "and has been posted in the group."
            ),
            parse_mode="HTML",
        )

    except Exception:

        pass


# ==========================================================
# CANCEL RAFFLE CALLBACK
# ==========================================================

async def cancel_raffle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    if not is_admin(update):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    try:

        raffle_id = int(
            query.data.split(":")[1]
        )

    except Exception:

        return

    changed = db.cancel_pending_raffle(
        raffle_id
    )

    if changed:

        text = (
            "❌ <b>RAFFLE CANCELLED</b>\n\n"
            f"Raffle #{raffle_id} has been cancelled."
        )

    else:

        text = (
            "⚠️ Raffle could not be cancelled.\n\n"
            "It may already be active, closed, "
            "or cancelled."
        )

    try:

        await query.edit_message_text(
            text,
            parse_mode="HTML",
        )

    except Exception:

        await query.message.reply_text(
            text,
            parse_mode="HTML",
        )


# ==========================================================
# ENTER RAFFLE BUTTON
# ==========================================================

async def enter_raffle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    raffle = db.get_active_raffle()

    if not raffle:

        await query.answer(
            "There is no active raffle right now.",
            show_alert=True,
        )

        return

    await query.message.reply_text(
        (
            "🎟️ <b>Melanated AZ Friends Raffle</b>\n\n"
            f"💰 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n\n"
            "Your entry is completed privately in "
            "your inbox so other members do not "
            "see your payment or entry information.\n\n"
            "Choose your payment method:"
        ),
        reply_markup=payment_keyboard(),
        parse_mode="HTML",
    )


# ==========================================================
# CASH APP
# ==========================================================

async def raffle_cashapp(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    raffle = db.get_active_raffle()

    if not raffle:

        await query.answer(
            "There is no active raffle.",
            show_alert=True,
        )

        return

    try:

        import os

        cashapp_tag = os.environ.get(
            "CASHAPP_TAG",
            "",
        )

        cashapp_url = os.environ.get(
            "CASHAPP_URL",
            "",
        )

    except Exception:

        cashapp_tag = ""
        cashapp_url = ""

    payment_text = (
        "💵 <b>CASH APP PAYMENT</b>\n\n"
        f"Raffle: #{raffle['id']}\n"
        f"Entry Price: <b>{raffle['price']}</b>\n\n"
    )

    if cashapp_tag:
        payment_text += (
            f"Cash App: <b>{cashapp_tag}</b>\n"
        )

    if cashapp_url:
        payment_text += (
            f"\n{cashapp_url}\n"
        )

    payment_text += (
        "\nAfter sending payment, reply here "
        "with your payment confirmation/screenshot.\n\n"
        "⚠️ Your payment will be verified by "
        "Melanated AZ before your raffle entry "
        "is approved."
    )

    await send_to_user(
        update,
        payment_text,
        parse_mode="HTML",
    )


# ==========================================================
# ZELLE
# ==========================================================

async def raffle_zelle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    raffle = db.get_active_raffle()

    if not raffle:

        await query.answer(
            "There is no active raffle.",
            show_alert=True,
        )

        return

    try:

        import os

        zelle_phone = os.environ.get(
            "ZELLE_PHONE",
            "",
        )

    except Exception:

        zelle_phone = ""

    payment_text = (
        "💳 <b>ZELLE PAYMENT</b>\n\n"
        f"Raffle: #{raffle['id']}\n"
        f"Entry Price: <b>{raffle['price']}</b>\n\n"
    )

    if zelle_phone:
        payment_text += (
            f"Zelle: <b>{zelle_phone}</b>\n"
        )

    payment_text += (
        "\nAfter sending payment, reply here "
        "with your payment confirmation/screenshot.\n\n"
        "⚠️ Your payment will be verified by "
        "Melanated AZ before your raffle entry "
        "is approved."
    )

    await send_to_user(
        update,
        payment_text,
        parse_mode="HTML",
    )


# ==========================================================
# ENTER RAFFLE COMMAND
# ==========================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    raffle = db.get_active_raffle()

    if not raffle:

        await reply_or_edit(
            update,
            "❌ There is no active raffle right now."
        )

        return

    await reply_or_edit(
        update,
        (
            "🎟️ <b>Melanated AZ Friends Raffle</b>\n\n"
            f"💰 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n\n"
            "Choose your payment method below.\n\n"
            "Your payment and entry are handled privately "
            "and verified by Melanated AZ."
        ),
        reply_markup=payment_keyboard(),
        parse_mode="HTML",
    )


# ==========================================================
# ADD PAYMENT ENTRY
# ==========================================================

async def create_payment_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payment_method,
):

    raffle = db.get_active_raffle()

    if not raffle:

        await reply_or_edit(
            update,
            "❌ There is no active raffle."
        )

        return

    user = update.effective_user

    if user is None:

        return

    username = user.username

    display_name = user.full_name

    entry_id = db.add_raffle_entry(
        raffle_id=raffle["id"],
        user_id=user.id,
        username=username,
        display_name=display_name,
        payment_method=payment_method,
    )

    if entry_id is None:

        await reply_or_edit(
            update,
            (
                "⚠️ You already have a pending or "
                "approved entry for this raffle."
            )
        )

        return

    # ------------------------------------------------------
    # ADMIN NOTIFICATION
    # ------------------------------------------------------

    for admin_id in _get_admin_ids():

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "🎟️ <b>NEW RAFFLE ENTRY</b>\n\n"
                    f"Raffle: #{raffle['id']}\n"
                    f"Entry ID: #{entry_id}\n"
                    f"Name: {display_name}\n"
                    f"Username: @{username}"
                    if username
                    else f"Name: {display_name}"
                )
                + (
                    f"\nPayment: {payment_method}\n"
                    f"Amount: {raffle['price']}\n\n"
                    "Verify the payment before approving."
                ),
                reply_markup=admin_entry_keyboard(
                    entry_id
                ),
                parse_mode="HTML",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin of raffle entry"
            )

    await reply_or_edit(
        update,
        (
            "✅ <b>ENTRY SUBMITTED</b>\n\n"
            f"Entry #{entry_id} has been submitted.\n\n"
            f"Payment method: <b>{payment_method}</b>\n"
            f"Amount: <b>{raffle['price']}</b>\n\n"
            "Your payment will be verified by "
            "Melanated AZ before your entry is approved.\n\n"
            "You will receive a private confirmation "
            "when your entry is approved."
        ),
        parse_mode="HTML",
    )


# ==========================================================
# PAYMENT CALLBACK ROUTER
# ==========================================================

async def payment_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if query.data == "raffle_cashapp":

        await raffle_cashapp(
            update,
            context,
        )

        return

    if query.data == "raffle_zelle":

        await raffle_zelle(
            update,
            context,
        )

        return


# ==========================================================
# APPROVE ENTRY
# ==========================================================

async def approve_entry_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    if not is_admin(update):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    try:

        entry_id = int(
            query.data.split(":")[1]
        )

    except Exception:

        return

    entry = db.get_entry(
        entry_id
    )

    if not entry:

        await query.answer(
            "Entry not found.",
            show_alert=True,
        )

        return

    changed = db.approve_entry(
        entry_id,
        update.effective_user.id,
    )

    if not changed:

        await query.answer(
            "Entry is no longer pending.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # NOTIFY USER
    # ------------------------------------------------------

    try:

        raffle = db.get_raffle(
            entry["raffle_id"]
        )

        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "🎉 <b>RAFFLE ENTRY APPROVED!</b>\n\n"
                f"Raffle: #{entry['raffle_id']}\n"
                f"Prize: <b>{raffle['prize']}</b>\n\n"
                "Your payment has been verified and "
                "your entry is officially in the raffle.\n\n"
                "Good luck! 🍀"
            ),
            parse_mode="HTML",
        )

    except Exception:

        logger.exception(
            "Unable to notify approved raffle user"
        )

    try:

        await query.edit_message_text(
            (
                "✅ <b>ENTRY APPROVED</b>\n\n"
                f"Entry #{entry_id}\n"
                f"User: {display_name_from_entry(entry)}\n"
                f"Payment: {entry.get('payment_method')}\n\n"
                "Payment verified."
            ),
            parse_mode="HTML",
        )

    except Exception:

        pass


# ==========================================================
# DENY ENTRY
# ==========================================================

async def deny_entry_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    if not is_admin(update):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    try:

        entry_id = int(
            query.data.split(":")[1]
        )

    except Exception:

        return

    entry = db.get_entry(
        entry_id
    )

    if not entry:

        return

    changed = db.deny_entry(
        entry_id,
        update.effective_user.id,
    )

    if not changed:

        await query.answer(
            "Entry is no longer pending.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # NOTIFY USER
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=entry["user_id"],
            text=(
                "❌ <b>RAFFLE ENTRY NOT APPROVED</b>\n\n"
                f"Entry #{entry_id}\n\n"
                "Your raffle entry was not approved.\n"
                "If you believe this is an error, "
                "please contact Melanated AZ."
            ),
            parse_mode="HTML",
        )

    except Exception:

        logger.exception(
            "Unable to notify denied raffle user"
        )

    try:

        await query.edit_message_text(
            (
                "❌ <b>ENTRY DENIED</b>\n\n"
                f"Entry #{entry_id}\n"
                f"User: {display_name_from_entry(entry)}"
            ),
            parse_mode="HTML",
        )

    except Exception:

        pass


# ==========================================================
# RAFFLE ENTRIES
#
# THIS FIXES YOUR CURRENT ERROR.
#
# admin.py calls this from an inline callback.
# Therefore update.message is None.
#
# We use reply_or_edit(), which handles BOTH.
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ You are not authorized to view raffle entries."
        )

        return

    raffle = db.get_active_raffle()

    # ------------------------------------------------------
    # IF NO ACTIVE RAFFLE, LOOK FOR MOST RECENT RAFFLE
    # ------------------------------------------------------

    if not raffle:

        pending = db.get_pending_raffle()

        if pending:

            raffle = pending

        else:

            # ------------------------------------------------
            # RECOVERY:
            # FIND MOST RECENT RAFFLE DIRECTLY
            # ------------------------------------------------

            try:

                import sqlite3
                import os

                db_name = os.environ.get(
                    "RAFFLE_DB_NAME",
                    "raffle.db",
                )

                conn = sqlite3.connect(
                    db_name
                )

                conn.row_factory = sqlite3.Row

                row = conn.execute(
                    """
                    SELECT *
                    FROM raffles
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ).fetchone()

                conn.close()

                if row:
                    raffle = dict(row)

            except Exception:

                logger.exception(
                    "Unable to recover most recent raffle"
                )

    if not raffle:

        await reply_or_edit(
            update,
            (
                "📋 <b>RAFFLE ENTRIES</b>\n\n"
                "No raffle records were found in "
                "the current database."
            ),
            parse_mode="HTML",
        )

        return

    # ------------------------------------------------------
    # GET ENTRIES
    # ------------------------------------------------------

    try:

        approved = db.get_approved_entries(
            raffle["id"]
        )

    except Exception:

        approved = []

    try:

        pending = [
            x
            for x in db.get_pending_entries()
            if x.get("raffle_id") == raffle["id"]
        ]

    except Exception:

        pending = []

    # ------------------------------------------------------
    # BUILD RESPONSE
    # ------------------------------------------------------

    lines = [
        "📋 <b>RAFFLE ENTRIES</b>",
        "",
        f"🎟️ Raffle #{raffle['id']}",
        f"💰 Prize: {raffle['prize']}",
        f"💵 Entry: {raffle['price']}",
        f"📌 Status: {raffle['status'].title()}",
        "",
        f"✅ Approved Entries: {len(approved)}",
        f"⏳ Pending Entries: {len(pending)}",
        "",
    ]

    if approved:

        lines.append(
            "<b>APPROVED</b>"
        )

        for number, entry in enumerate(
            approved,
            1,
        ):

            name = display_name_from_entry(
                entry
            )

            payment = entry.get(
                "payment_method",
                "Unknown",
            )

            lines.append(
                f"{number}. {name} — {payment}"
            )

        lines.append("")

    if pending:

        lines.append(
            "<b>PENDING PAYMENT VERIFICATION</b>"
        )

        for entry in pending:

            name = display_name_from_entry(
                entry
            )

            payment = entry.get(
                "payment_method",
                "Unknown",
            )

            entry_id = entry.get(
                "id"
            )

            lines.append(
                f"⏳ #{entry_id} — {name} — {payment}"
            )

        lines.append("")

    if not approved and not pending:

        lines.append(
            "No entries have been recorded for this raffle."
        )

    # ------------------------------------------------------
    # SEND
    # ------------------------------------------------------

    await reply_or_edit(
        update,
        "\n".join(lines),
        parse_mode="HTML",
    )


# ==========================================================
# ALL RAFFLES / HISTORY
# ==========================================================

async def list_raffles(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    try:

        import sqlite3
        import os

        db_name = os.environ.get(
            "RAFFLE_DB_NAME",
            "raffle.db",
        )

        conn = sqlite3.connect(
            db_name
        )

        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT *
            FROM raffles
            ORDER BY id DESC
            """
        ).fetchall()

        conn.close()

    except Exception as exc:

        logger.exception(
            "Unable to retrieve raffle history"
        )

        await reply_or_edit(
            update,
            f"❌ Database error: {exc}"
        )

        return

    if not rows:

        await reply_or_edit(
            update,
            (
                "📚 <b>RAFFLE HISTORY</b>\n\n"
                "No raffle records were found."
            ),
            parse_mode="HTML",
        )

        return

    lines = [
        "📚 <b>RAFFLE HISTORY</b>",
        "",
    ]

    for raffle in rows:

        lines.append(
            (
                f"#{raffle['id']} — "
                f"{raffle['prize']} — "
                f"{raffle['price']} — "
                f"{raffle['status'].upper()}"
            )
        )

    await reply_or_edit(
        update,
        "\n".join(lines),
        parse_mode="HTML",
    )


# ==========================================================
# RAFFLE STATUS
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    raffle = db.get_active_raffle()

    if not raffle:

        raffle = db.get_pending_raffle()

    if not raffle:

        await reply_or_edit(
            update,
            "❌ No active or pending raffle found."
        )

        return

    try:

        approved = db.get_approved_entries(
            raffle["id"]
        )

    except Exception:

        approved = []

    try:

        pending = [
            e
            for e in db.get_pending_entries()
            if e.get("raffle_id") == raffle["id"]
        ]

    except Exception:

        pending = []

    await reply_or_edit(
        update,
        (
            f"{format_raffle(raffle)}\n\n"
            f"✅ Approved Entries: <b>{len(approved)}</b>\n"
            f"⏳ Pending Entries: <b>{len(pending)}</b>"
        ),
        parse_mode="HTML",
    )


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    entries = db.get_pending_entries()

    if not entries:

        await reply_or_edit(
            update,
            "✅ There are no pending raffle entries."
        )

        return

    lines = [
        "⏳ <b>PENDING RAFFLE ENTRIES</b>",
        "",
    ]

    for entry in entries:

        lines.extend(
            [
                f"🎟️ Entry #{entry['id']}",
                f"👤 {display_name_from_entry(entry)}",
                f"💳 {entry.get('payment_method', 'Unknown')}",
                f"Raffle #{entry['raffle_id']}",
                "",
            ]
        )

    await reply_or_edit(
        update,
        "\n".join(lines),
        parse_mode="HTML",
    )


# ==========================================================
# APPROVED ENTRIES FOR ACTIVE RAFFLE
# ==========================================================

async def approved_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    raffle = db.get_active_raffle()

    if not raffle:

        await reply_or_edit(
            update,
            "❌ No active raffle."
        )

        return

    entries = db.get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await reply_or_edit(
            update,
            "No approved entries yet."
        )

        return

    lines = [
        f"🎟️ <b>APPROVED ENTRIES — RAFFLE #{raffle['id']}</b>",
        "",
    ]

    for number, entry in enumerate(
        entries,
        1,
    ):

        lines.append(
            f"{number}. {display_name_from_entry(entry)}"
        )

    await reply_or_edit(
        update,
        "\n".join(lines),
        parse_mode="HTML",
    )


# ==========================================================
# CANCEL ACTIVE RAFFLE
# ==========================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    raffle = db.get_active_raffle()

    if not raffle:

        await reply_or_edit(
            update,
            "❌ No active raffle found."
        )

        return

    try:

        import sqlite3
        import os

        db_name = os.environ.get(
            "RAFFLE_DB_NAME",
            "raffle.db",
        )

        conn = sqlite3.connect(
            db_name
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE raffles
            SET status = 'cancelled'
            WHERE id = ?
            AND status = 'active'
            """,
            (raffle["id"],),
        )

        changed = cursor.rowcount > 0

        conn.commit()

        conn.close()

    except Exception:

        logger.exception(
            "Unable to cancel active raffle"
        )

        await reply_or_edit(
            update,
            "❌ Unable to cancel raffle."
        )

        return

    if changed:

        await reply_or_edit(
            update,
            (
                "❌ <b>RAFFLE CANCELLED</b>\n\n"
                f"Raffle #{raffle['id']} has been cancelled."
            ),
            parse_mode="HTML",
        )

    else:

        await reply_or_edit(
            update,
            "⚠️ Raffle could not be cancelled."
        )


# ==========================================================
# DRAW RAFFLE
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    raffle = db.get_active_raffle()

    if not raffle:

        await reply_or_edit(
            update,
            "❌ There is no active raffle to draw."
        )

        return

    entries = db.get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await reply_or_edit(
            update,
            (
                "❌ Cannot draw the raffle.\n\n"
                "There are no approved entries."
            )
        )

        return

    winner = random.choice(
        entries
    )

    # ------------------------------------------------------
    # CLOSE RAFFLE
    # ------------------------------------------------------

    db.close_raffle(
        raffle["id"]
    )

    winner_name = display_name_from_entry(
        winner
    )

    # ------------------------------------------------------
    # GROUP RESULT
    # ------------------------------------------------------

    try:

        chat_id = raffle.get(
            "chat_id"
        )

        if not chat_id:

            import os

            chat_id = int(
                os.environ.get(
                    "RAFFLE_CHAT_ID"
                )
            )

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🎉🎉🎉 <b>RAFFLE WINNER!</b> 🎉🎉🎉\n\n"
                "🎟️ <b>Melanated AZ Friends Raffle</b>\n\n"
                f"💰 Prize: <b>{raffle['prize']}</b>\n\n"
                f"🏆 Winner: <b>{winner_name}</b>\n\n"
                "Congratulations! 🎉"
            ),
            parse_mode="HTML",
        )

    except Exception:

        logger.exception(
            "Unable to announce raffle winner"
        )

    await reply_or_edit(
        update,
        (
            "🎉 <b>RAFFLE DRAWN</b>\n\n"
            f"Raffle #{raffle['id']}\n"
            f"Prize: {raffle['prize']}\n\n"
            f"🏆 Winner: <b>{winner_name}</b>\n"
            f"Entry #{winner['id']}"
        ),
        parse_mode="HTML",
    )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    # ------------------------------------------------------
    # FIND MOST RECENT CLOSED RAFFLE
    # ------------------------------------------------------

    try:

        import sqlite3
        import os

        db_name = os.environ.get(
            "RAFFLE_DB_NAME",
            "raffle.db",
        )

        conn = sqlite3.connect(
            db_name
        )

        conn.row_factory = sqlite3.Row

        raffle = conn.execute(
            """
            SELECT *
            FROM raffles
            WHERE status = 'closed'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        conn.close()

    except Exception:

        logger.exception(
            "Unable to find raffle for reroll"
        )

        await reply_or_edit(
            update,
            "❌ Unable to locate a raffle for reroll."
        )

        return

    if not raffle:

        await reply_or_edit(
            update,
            "❌ No closed raffle found for reroll."
        )

        return

    raffle = dict(raffle)

    entries = db.get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await reply_or_edit(
            update,
            "❌ No approved entries available for reroll."
        )

        return

    winner = random.choice(
        entries
    )

    winner_name = display_name_from_entry(
        winner
    )

    try:

        chat_id = raffle.get(
            "chat_id"
        )

        if not chat_id:

            import os

            chat_id = int(
                os.environ.get(
                    "RAFFLE_CHAT_ID"
                )
            )

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🔄 <b>RAFFLE REROLL</b>\n\n"
                f"🎟️ Raffle #{raffle['id']}\n"
                f"💰 Prize: <b>{raffle['prize']}</b>\n\n"
                f"🏆 New Winner: <b>{winner_name}</b>\n\n"
                "Congratulations! 🎉"
            ),
            parse_mode="HTML",
        )

    except Exception:

        logger.exception(
            "Unable to announce reroll"
        )

    await reply_or_edit(
        update,
        (
            "🔄 <b>REROLL COMPLETE</b>\n\n"
            f"🏆 New Winner: <b>{winner_name}</b>\n"
            f"Entry #{winner['id']}"
        ),
        parse_mode="HTML",
    )


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    if not context.args:

        await reply_or_edit(
            update,
            (
                "Usage:\n"
                "<code>/bonusentry USER_ID</code>"
            ),
            parse_mode="HTML",
        )

        return

    try:

        user_id = int(
            context.args[0]
        )

    except Exception:

        await reply_or_edit(
            update,
            "❌ Invalid user ID."
        )

        return

    raffle = db.get_active_raffle()

    if not raffle:

        await reply_or_edit(
            update,
            "❌ No active raffle."
        )

        return

    entry_id = db.add_raffle_entry(
        raffle_id=raffle["id"],
        user_id=user_id,
        username=None,
        display_name=str(user_id),
        payment_method="BONUS",
    )

    if entry_id is None:

        await reply_or_edit(
            update,
            "⚠️ User already has an entry."
        )

        return

    # Automatically approve bonus entry.
    db.approve_entry(
        entry_id,
        update.effective_user.id,
    )

    await reply_or_edit(
        update,
        (
            "🎟️ <b>BONUS ENTRY ADDED</b>\n\n"
            f"User ID: {user_id}\n"
            f"Entry: #{entry_id}\n"
            f"Raffle: #{raffle['id']}"
        ),
        parse_mode="HTML",
    )


# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    if not context.args:

        await reply_or_edit(
            update,
            (
                "Usage:\n"
                "<code>/removeentry ENTRY_ID</code>"
            ),
            parse_mode="HTML",
        )

        return

    try:

        entry_id = int(
            context.args[0]
        )

    except Exception:

        await reply_or_edit(
            update,
            "❌ Invalid entry ID."
        )

        return

    changed = db.remove_entry(
        entry_id
    )

    if changed:

        await reply_or_edit(
            update,
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await reply_or_edit(
            update,
            f"❌ Entry #{entry_id} was not found."
        )


# ==========================================================
# ENTRY LOOKUP
# ==========================================================

async def entry_lookup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    if not context.args:

        await reply_or_edit(
            update,
            (
                "Usage:\n"
                "<code>/entry ENTRY_ID</code>"
            ),
            parse_mode="HTML",
        )

        return

    try:

        entry_id = int(
            context.args[0]
        )

    except Exception:

        await reply_or_edit(
            update,
            "❌ Invalid entry ID."
        )

        return

    entry = db.get_entry(
        entry_id
    )

    if not entry:

        await reply_or_edit(
            update,
            "❌ Entry not found."
        )

        return

    await reply_or_edit(
        update,
        (
            "🎟️ <b>RAFFLE ENTRY</b>\n\n"
            f"Entry ID: #{entry['id']}\n"
            f"Raffle ID: #{entry['raffle_id']}\n"
            f"User ID: {entry['user_id']}\n"
            f"Name: {display_name_from_entry(entry)}\n"
            f"Username: @{entry['username']}"
            if entry.get("username")
            else
            f"Entry ID: #{entry['id']}\n"
            f"Raffle ID: #{entry['raffle_id']}\n"
            f"User ID: {entry['user_id']}\n"
            f"Name: {display_name_from_entry(entry)}"
        )
        + (
            f"\nPayment: {entry.get('payment_method')}"
            f"\nStatus: {entry.get('status')}"
            f"\nCreated: {entry.get('created_at')}"
        ),
        parse_mode="HTML",
    )


# ==========================================================
# RECOVER / INSPECT OLD RAFFLES
# ==========================================================

async def recover_raffles(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    try:

        import sqlite3
        import os

        db_name = os.environ.get(
            "RAFFLE_DB_NAME",
            "raffle.db",
        )

        conn = sqlite3.connect(
            db_name
        )

        conn.row_factory = sqlite3.Row

        # --------------------------------------------------
        # CHECK TABLES
        # --------------------------------------------------

        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        table_names = [
            row["name"]
            for row in tables
        ]

        # --------------------------------------------------
        # RAFFLES
        # --------------------------------------------------

        raffles = []

        if "raffles" in table_names:

            raffles = conn.execute(
                """
                SELECT *
                FROM raffles
                ORDER BY id DESC
                """
            ).fetchall()

        # --------------------------------------------------
        # ENTRIES
        # --------------------------------------------------

        entry_count = 0

        if "raffle_entries" in table_names:

            row = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM raffle_entries
                """
            ).fetchone()

            entry_count = row["total"]

        conn.close()

    except Exception as exc:

        logger.exception(
            "Raffle recovery inspection failed"
        )

        await reply_or_edit(
            update,
            f"❌ Recovery inspection failed:\n{exc}"
        )

        return

    lines = [
        "🔎 <b>RAFFLE DATABASE RECOVERY</b>",
        "",
        f"📁 Database: <code>{db_name}</code>",
        "",
        "<b>Tables Found:</b>",
    ]

    for table in table_names:

        lines.append(
            f"• {table}"
        )

    lines.extend(
        [
            "",
            f"🎟️ Raffle Records: <b>{len(raffles)}</b>",
            f"👤 Entry Records: <b>{entry_count}</b>",
            "",
        ]
    )

    if raffles:

        lines.append(
            "<b>RAFFLE HISTORY</b>"
        )

        for raffle in raffles:

            lines.append(
                (
                    f"#{raffle['id']} — "
                    f"{raffle['prize']} — "
                    f"{raffle['price']} — "
                    f"{raffle['status'].upper()}"
                )
            )

    else:

        lines.append(
            "⚠️ No raffle records were found."
        )

    await reply_or_edit(
        update,
        "\n".join(lines),
        parse_mode="HTML",
    )


# ==========================================================
# DATABASE DEBUG
# ==========================================================

async def raffle_database_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(update):

        await reply_or_edit(
            update,
            "❌ Not authorized."
        )

        return

    try:

        import sqlite3
        import os

        db_name = os.environ.get(
            "RAFFLE_DB_NAME",
            "raffle.db",
        )

        conn = sqlite3.connect(
            db_name
        )

        conn.row_factory = sqlite3.Row

        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        ).fetchall()

        lines = [
            "🗄️ <b>RAFFLE DATABASE</b>",
            "",
            f"Database: <code>{db_name}</code>",
            "",
        ]

        for table in tables:

            table_name = table["name"]

            try:

                count = conn.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM "{table_name}"
                    """
                ).fetchone()[0]

            except Exception:

                count = "?"

            lines.append(
                f"• {table_name}: {count} records"
            )

        conn.close()

        await reply_or_edit(
            update,
            "\n".join(lines),
            parse_mode="HTML",
        )

    except Exception as exc:

        await reply_or_edit(
            update,
            f"❌ Database error: {exc}"
        )


# ==========================================================
# ACTIVE RAFFLE COUNTDOWN
# ==========================================================

async def update_raffle_countdown(
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        raffle = db.get_active_raffle()

        if not raffle:
            return

        remaining = format_countdown(
            raffle["expires_at"]
        )

        # --------------------------------------------------
        # AUTO CLOSE
        # --------------------------------------------------

        if remaining == "Expired":

            db.close_raffle(
                raffle["id"]
            )

            try:

                if raffle.get("chat_id") and raffle.get("message_id"):

                    await context.bot.edit_message_text(
                        chat_id=raffle["chat_id"],
                        message_id=raffle["message_id"],
                        text=(
                            "🎟️ <b>Melanated AZ Friends Raffle</b>\n\n"
                            f"💰 Prize: <b>{raffle['prize']}</b>\n"
                            f"💵 Entry: <b>{raffle['price']}</b>\n\n"
                            "⛔ <b>RAFFLE CLOSED</b>\n\n"
                            "Entries are no longer being accepted."
                        ),
                        parse_mode="HTML",
                    )

            except Exception:

                pass

            return

        # --------------------------------------------------
        # UPDATE RAFFLE POST
        # --------------------------------------------------

        if raffle.get("chat_id") and raffle.get("message_id"):

            try:

                await context.bot.edit_message_text(
                    chat_id=raffle["chat_id"],
                    message_id=raffle["message_id"],
                    text=(
                        "🎟️ <b>Melanated AZ Friends Raffle</b>\n\n"
                        f"💰 <b>Prize:</b> {raffle['prize']}\n"
                        f"💵 <b>Entry:</b> {raffle['price']}\n"
                        f"⏳ <b>Time Remaining:</b> {remaining}\n\n"
                        "Want to join?\n"
                        "Click <b>ENTER RAFFLE</b> below.\n\n"
                        "Your payment and entry will be "
                        "verified by Melanated AZ before "
                        "your entry is approved."
                    ),
                    reply_markup=raffle_keyboard(),
                    parse_mode="HTML",
                )

            except Exception:

                # Telegram can return "message is not modified"
                # or fail if the message was deleted.
                pass

    except Exception:

        logger.exception(
            "Raffle countdown update failed"
        )


# ==========================================================
# CALLBACK ROUTER
# ==========================================================

async def raffle_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    data = query.data or ""

    # ------------------------------------------------------
    # ENTER
    # ------------------------------------------------------

    if data == "raffle_enter":

        await enter_raffle_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # CASH APP
    # ------------------------------------------------------

    if data == "raffle_cashapp":

        await raffle_cashapp(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # ZELLE
    # ------------------------------------------------------

    if data == "raffle_zelle":

        await raffle_zelle(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # APPROVE ENTRY
    # ------------------------------------------------------

    if data.startswith(
        "raffle_approve:"
    ):

        await approve_entry_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # DENY ENTRY
    # ------------------------------------------------------

    if data.startswith(
        "raffle_deny:"
    ):

        await deny_entry_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # APPROVE RAFFLE
    # ------------------------------------------------------

    if data.startswith(
        "raffle_approve_raffle:"
    ):

        await approve_raffle_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # CANCEL RAFFLE
    # ------------------------------------------------------

    if data.startswith(
        "raffle_cancel_raffle:"
    ):

        await cancel_raffle_callback(
            update,
            context,
        )

        return


# ==========================================================
# COMMAND ALIASES
# ==========================================================

async def raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await raffle_status(
        update,
        context,
    )


async def entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await raffle_entries(
        update,
        context,
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await raffle_status(
        update,
        context,
    )


async def draw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await draw_raffle(
        update,
        context,
    )


async def reroll(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await reroll_raffle(
        update,
        context,
    )


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await cancel_raffle(
        update,
        context,
    )


# ==========================================================
# STARTUP
# ==========================================================

def initialize_raffle_system():

    try:

        db.initialize_database()

        logger.info(
            "🎟️ Raffle database initialized."
        )

    except Exception:

        logger.exception(
            "Unable to initialize raffle database"
        )


initialize_raffle_system()
