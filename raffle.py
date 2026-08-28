# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Raffle system compatible with raffle_database.py
#
# Features:
# - Admin-only raffle creation
# - FREE raffles supported
# - Paid raffles supported
# - Cash App
# - Zelle
# - Admin approval
# - Entry approval
# - Duplicate-entry protection
# - Countdown
# - Automatic expiration
# - Draw winner
# - Reroll
# - Bonus entries
# - Remove entries
# - Persistent SQLite database
# ==========================================================

import logging
import os
import random
from datetime import datetime, timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
    RAFFLE_DURATION_DAYS,
    CASHAPP_TAG,
    CASHAPP_URL,
    ZELLE_PHONE,
)

import raffle_database as db


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger("melanated_az_raffle")


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):
    try:
        admin_ids = {int(x) for x in ADMIN_IDS}
    except (TypeError, ValueError):
        admin_ids = set()

    return user_id in admin_ids


# ==========================================================
# MONEY HELPERS
# ==========================================================

def money_value(value):
    """
    Convert:
        $5
        5
        $10.00
        FREE
        free

    into a numeric value or 0 for FREE.

    Returns:
        float or None
    """

    if value is None:
        return None

    value = str(value).strip()

    if value.lower() in (
        "free",
        "$0",
        "$0.00",
        "0",
        "0.00",
    ):
        return 0.0

    value = value.replace("$", "")
    value = value.replace(",", "")
    value = value.strip()

    try:
        return float(value)
    except ValueError:
        return None


def is_free_price(value):
    """
    Determine whether a raffle is FREE.
    """

    if value is None:
        return False

    return str(value).strip().lower() == "free"


def money(value):
    """
    Format a raffle price.
    """

    if value is None:
        return "FREE"

    text = str(value).strip()

    if text.lower() == "free":
        return "FREE"

    numeric = money_value(text)

    if numeric is None:
        return text

    if numeric <= 0:
        return "FREE"

    if numeric.is_integer():
        return f"${int(numeric)}"

    return f"${numeric:.2f}"


# ==========================================================
# COUNTDOWN
# ==========================================================

def format_countdown(expires_at):
    """
    Format remaining raffle time.
    """

    if not expires_at:
        return "Unknown"

    try:
        if isinstance(expires_at, str):
            expires = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )
        else:
            expires = expires_at

        if expires.tzinfo is None:
            expires = expires.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        seconds = int(
            (expires - now).total_seconds()
        )

    except Exception:
        logger.exception(
            "Could not calculate raffle countdown."
        )
        return "Unknown"

    if seconds <= 0:
        return "⏰ ENDED"

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

    if days:
        return (
            f"{days}d "
            f"{hours}h "
            f"{minutes}m"
        )

    if hours:
        return (
            f"{hours}h "
            f"{minutes}m"
        )

    return f"{minutes}m"


# ==========================================================
# RAFFLE EXPIRATION
# ==========================================================

def raffle_expiration():
    """
    Return expiration timestamp.
    """

    try:
        days = int(
            os.environ.get(
                "RAFFLE_DURATION_DAYS",
                RAFFLE_DURATION_DAYS,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        days = 7

    return (
        datetime.now(
            timezone.utc
        ).timestamp()
        + (days * 86400)
    )


def timestamp_to_iso(timestamp):
    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).isoformat()


# ==========================================================
# DATABASE HELPERS
# ==========================================================

def db_call(function_name, *args, **kwargs):
    """
    Safely call a database function.
    """

    function = getattr(
        db,
        function_name,
        None,
    )

    if not callable(function):
        raise RuntimeError(
            f"raffle_database.py is missing "
            f"function: {function_name}"
        )

    return function(
        *args,
        **kwargs,
    )


def find_active_raffle():
    """
    Get the currently active raffle.
    """

    try:
        return db_call(
            "get_active_raffle"
        )
    except Exception:
        logger.exception(
            "Could not retrieve active raffle."
        )
        return None


# ==========================================================
# KEYBOARDS
# ==========================================================

def raffle_member_keyboard(free=False):
    """
    Keyboard shown to members.

    FREE raffles do not require payment.
    """

    buttons = [
        [
            InlineKeyboardButton(
                "🎟️ ENTER RAFFLE",
                callback_data="raffle_enter",
            )
        ]
    ]

    if not free:
        buttons.append(
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data="raffle_cashapp",
                ),
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data="raffle_zelle",
                ),
            ]
        )

    return InlineKeyboardMarkup(buttons)


def payment_keyboard():
    return InlineKeyboardMarkup(
        [
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


def paid_keyboard(payment_method):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ I PAID",
                    callback_data=(
                        f"raffle_paid:{payment_method}"
                    ),
                )
            ]
        ]
    )


def admin_approval_keyboard(raffle_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=(
                        f"raffle_approve:{raffle_id}"
                    ),
                ),
                InlineKeyboardButton(
                    "❌ CANCEL",
                    callback_data=(
                        f"raffle_cancel:{raffle_id}"
                    ),
                ),
            ]
        ]
    )


def payment_admin_keyboard(entry_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE ENTRY",
                    callback_data=(
                        f"raffle_payment_approve:{entry_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ DENY ENTRY",
                    callback_data=(
                        f"raffle_payment_deny:{entry_id}"
                    ),
                )
            ],
        ]
    )


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 You are not authorized "
            "to start a raffle."
        )
        return

    context.user_data[
        "awaiting_raffle_setup"
    ] = True

    context.user_data.pop(
        "raffle_setup",
        None,
    )

    context.user_data.pop(
        "pending_raffle",
        None,
    )

    await message.reply_text(
        "🎟️ START RAFFLE\n\n"
        "Enter the raffle information:\n\n"
        "$100 Cash Prize | $5\n\n"
        "FREE raffles are also supported:\n"
        "FREE | FREE\n\n"
        "Or:\n"
        "$250 Cash Prize | FREE\n\n"
        "Format:\n"
        "PRIZE | ENTRY PRICE"
    )


# ==========================================================
# RAFFLE TEXT SETUP
# ==========================================================

async def handle_raffle_setup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return False

    if not context.user_data.get(
        "awaiting_raffle_setup"
    ):
        return False

    if not is_admin(user.id):
        context.user_data.pop(
            "awaiting_raffle_setup",
            None,
        )
        return False

    text = (
        message.text or ""
    ).strip()

    if not text:
        return True

    if "|" not in text:
        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Please use:\n"
            "$100 Cash Prize | $5\n\n"
            "For a free raffle:\n"
            "FREE Prize | FREE"
        )
        return True

    prize_text, entry_text = (
        part.strip()
        for part in text.split(
            "|",
            1,
        )
    )

    if not prize_text:
        await message.reply_text(
            "⚠️ Please enter a prize."
        )
        return True

    # ------------------------------------------------------
    # FREE SUPPORT
    # ------------------------------------------------------

    if is_free_price(entry_text):
        entry_price = 0.0
        display_price = "FREE"

    else:
        entry_price = money_value(
            entry_text
        )

        if (
            entry_price is None
            or entry_price < 0
        ):
            await message.reply_text(
                "⚠️ Invalid entry price.\n\n"
                "Use:\n"
                "$100 Cash Prize | $5\n\n"
                "Or:\n"
                "FREE Prize | FREE"
            )
            return True

        display_price = money(
            entry_price
        )

    context.user_data[
        "raffle_setup"
    ] = {
        "prize": prize_text,
        "entry_price": display_price,
    }

    context.user_data.pop(
        "awaiting_raffle_setup",
        None,
    )

    await create_pending_raffle(
        update,
        context,
        prize_text,
        display_price,
    )

    return True


# ==========================================================
# CREATE PENDING RAFFLE
# ==========================================================

async def create_pending_raffle(
    update,
    context,
    prize,
    entry_price,
):
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    expires_timestamp = raffle_expiration()

    expires_at = timestamp_to_iso(
        expires_timestamp
    )

    # ------------------------------------------------------
    # IMPORTANT:
    #
    # raffle_database.py expects:
    #
    # create_raffle(
    #     prize,
    #     price,
    #     expires_at
    # )
    #
    # ------------------------------------------------------

    try:
        raffle_id = db_call(
            "create_raffle",
            prize,
            entry_price,
            expires_at,
        )

    except Exception as exc:
        logger.exception(
            "Could not create raffle in database."
        )

        await message.reply_text(
            "⚠️ I could not create the raffle "
            "in the database.\n\n"
            f"Database error: {exc}"
        )

        return

    context.user_data[
        "pending_raffle"
    ] = raffle_id

    duration = os.environ.get(
        "RAFFLE_DURATION_DAYS",
        RAFFLE_DURATION_DAYS,
    )

    text = (
        "🎟️ RAFFLE READY FOR APPROVAL\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry: {money(entry_price)}\n"
        f"⏱️ Duration: {duration} days\n\n"
        "Approve this raffle to post it "
        "in the Melanated AZ group."
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=text,
                reply_markup=admin_approval_keyboard(
                    raffle_id
                ),
            )

        except TelegramError as exc:
            logger.warning(
                "Could not notify admin %s: %s",
                admin_id,
                exc,
            )

    await message.reply_text(
        "✅ Raffle information received.\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry: {money(entry_price)}\n\n"
        "The raffle has been sent to the admins "
        "for approval."
    )


# ==========================================================
# PRIVATE RAFFLE START
# ==========================================================

async def raffle_private_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if not message:
        return

    await message.reply_text(
        "👑 Melanated AZ Friends Raffle\n\n"
        "Use the raffle button from the "
        "Melanated AZ group to enter.\n\n"
        "If you were sent here to complete "
        "a raffle entry, follow the instructions "
        "provided by the bot."
    )


# ==========================================================
# RAFFLE APPROVAL
# ==========================================================

async def raffle_approval_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):
        await query.answer(
            "Admin access required.",
            show_alert=True,
        )
        return

    data = query.data or ""

    if ":" not in data:
        await query.answer()
        return

    action, raffle_id_text = data.split(
        ":",
        1,
    )

    try:
        raffle_id = int(
            raffle_id_text
        )
    except ValueError:
        await query.answer(
            "Invalid raffle.",
            show_alert=True,
        )
        return

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    if action == "raffle_cancel":
        try:
            changed = db_call(
                "cancel_pending_raffle",
                raffle_id,
            )

        except Exception:
            logger.exception(
                "Failed to cancel raffle %s",
                raffle_id,
            )

            await query.answer(
                "Could not cancel raffle.",
                show_alert=True,
            )
            return

        if not changed:
            await query.answer(
                "Raffle was already processed.",
                show_alert=True,
            )
            return

        await query.answer(
            "Raffle cancelled."
        )

        try:
            await query.edit_message_text(
                "❌ Raffle cancelled."
            )
        except TelegramError:
            pass

        return

    # ------------------------------------------------------
    # APPROVE
    # ------------------------------------------------------

    if action != "raffle_approve":
        await query.answer()
        return

    raffle_info = None

    try:
        raffle_info = db_call(
            "get_raffle",
            raffle_id,
        )

    except Exception:
        logger.exception(
            "Could not retrieve raffle %s",
            raffle_id,
        )

        await query.answer(
            "Could not retrieve raffle.",
            show_alert=True,
        )
        return

    if not raffle_info:
        await query.answer(
            "Raffle no longer exists.",
            show_alert=True,
        )
        return

    if raffle_info.get("status") != "pending":
        await query.answer(
            "Raffle has already been processed.",
            show_alert=True,
        )
        return

    try:
        changed = db_call(
            "approve_raffle",
            raffle_id,
        )

    except Exception:
        logger.exception(
            "Failed to approve raffle %s",
            raffle_id,
        )

        await query.answer(
            "Could not approve raffle.",
            show_alert=True,
        )
        return

    if not changed:
        await query.answer(
            "Raffle was already processed.",
            show_alert=True,
        )
        return

    await query.answer(
        "Raffle approved!"
    )

    try:
        await query.edit_message_text(
            "✅ Raffle approved.\n\n"
            "Posting raffle to the group..."
        )
    except TelegramError:
        pass

    prize = raffle_info.get(
        "prize"
    )

    entry_price = raffle_info.get(
        "price"
    )

    expires_at = raffle_info.get(
        "expires_at"
    )

    free = money_value(
        entry_price
    ) == 0

    raffle_text = (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
        f"🎁 PRIZE: {prize}\n"
        f"💵 ENTRY: {money(entry_price)}\n\n"
    )

    if free:
        raffle_text += (
            "🎉 This raffle is FREE!\n\n"
            "Tap ENTER RAFFLE below to join.\n\n"
        )
    else:
        raffle_text += (
            "Ready to join?\n"
            "Tap ENTER RAFFLE below.\n\n"
            "💳 Payment options are available "
            "after selecting your entry.\n\n"
        )

    raffle_text += (
        f"⏱️ TIME REMAINING: "
        f"{format_countdown(expires_at)}\n\n"
        "👑 Good luck everyone!"
    )

    try:
        posted = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=raffle_text,
            reply_markup=raffle_member_keyboard(
                free=free
            ),
        )

    except TelegramError:
        logger.exception(
            "Could not post raffle to group."
        )

        # The database remains active.
        # Admin can use status/repost manually.
        return

    # ------------------------------------------------------
    # Save Telegram post metadata.
    # ------------------------------------------------------

    try:
        db_call(
            "set_raffle_post",
            raffle_id,
            posted.chat_id,
            posted.message_id,
        )

    except Exception:
        logger.exception(
            "Could not save raffle post metadata."
        )

    try:
        await query.edit_message_text(
            "✅ Raffle approved and posted "
            "to the group."
        )
    except TelegramError:
        pass


# ==========================================================
# ENTER RAFFLE BUTTON
# ==========================================================

async def raffle_enter_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        await query.answer()
        return

    raffle_info = find_active_raffle()

    if not raffle_info:
        await query.answer(
            "There is currently no active raffle.",
            show_alert=True,
        )
        return

    entry_price = raffle_info.get(
        "price"
    )

    # ------------------------------------------------------
    # FREE RAFFLE
    # ------------------------------------------------------

    if money_value(entry_price) == 0:
        await query.answer(
            "Free raffle entry!"
        )

        try:
            await create_free_entry(
                update,
                context,
                raffle_info,
            )
        except Exception:
            logger.exception(
                "Could not create free raffle entry."
            )

        return

    # ------------------------------------------------------
    # PAID RAFFLE
    # ------------------------------------------------------

    await query.answer(
        "Raffle entry started."
    )

    await query.message.reply_text(
        "🎟️ RAFFLE ENTRY\n\n"
        f"Entry price: {money(entry_price)}\n\n"
        "Choose how you would like to pay:",
        reply_markup=payment_keyboard(),
    )


# ==========================================================
# FREE ENTRY
# ==========================================================

async def create_free_entry(
    update,
    context,
    raffle_info,
):
    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    raffle_id = raffle_info.get(
        "id"
    )

    try:
        entry_id = db_call(
            "add_raffle_entry",
            raffle_id,
            user.id,
            user.username,
            user.full_name,
            "free",
        )

    except Exception as exc:
        logger.exception(
            "Could not create FREE raffle entry."
        )

        await query.message.reply_text(
            "⚠️ I could not create your raffle entry.\n\n"
            f"Database error: {exc}"
        )
        return

    if entry_id is None:
        await query.message.reply_text(
            "⚠️ You are already entered in this raffle "
            "or the raffle is no longer active."
        )
        return

    # ------------------------------------------------------
    # FREE entries are immediately approved.
    # ------------------------------------------------------

    try:
        db_call(
            "approve_entry",
            entry_id,
            0,
        )

    except Exception:
        logger.exception(
            "Could not approve FREE entry %s",
            entry_id,
        )

        await query.message.reply_text(
            "⚠️ Your entry was created, but I could "
            "not complete the approval."
        )
        return

    await query.message.reply_text(
        "🎉 YOU'RE IN!\n\n"
        "Your FREE raffle entry has been accepted.\n\n"
        "👑 Good luck!"
    )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        await query.answer()
        return

    data = query.data or ""

    raffle_info = find_active_raffle()

    if not raffle_info:
        await query.answer(
            "No active raffle.",
            show_alert=True,
        )
        return

    entry_price = raffle_info.get(
        "price"
    )

    if money_value(entry_price) == 0:
        await query.answer(
            "This raffle is FREE!",
            show_alert=True,
        )
        return

    # ------------------------------------------------------
    # CASH APP
    # ------------------------------------------------------

    if data == "raffle_cashapp":
        cashapp = (
            CASHAPP_TAG
            or "Cash App not configured"
        )

        cashapp_url = (
            CASHAPP_URL
            or ""
        )

        buttons = []

        if cashapp_url:
            buttons.append(
                [
                    InlineKeyboardButton(
                        "💵 OPEN CASH APP",
                        url=cashapp_url,
                    )
                ]
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    "✅ I PAID",
                    callback_data=(
                        "raffle_paid:cashapp"
                    ),
                )
            ]
        )

        await query.answer()

        await query.message.reply_text(
            "💵 CASH APP PAYMENT\n\n"
            f"Send {money(entry_price)} to:\n"
            f"{cashapp}\n\n"
            "After sending your payment, "
            "tap I PAID below.\n\n"
            "Your entry will remain pending "
            "until an admin verifies payment.",
            reply_markup=InlineKeyboardMarkup(
                buttons
            ),
        )

        return

    # ------------------------------------------------------
    # ZELLE
    # ------------------------------------------------------

    if data == "raffle_zelle":
        zelle = (
            ZELLE_PHONE
            or "Zelle information not configured"
        )

        await query.answer()

        await query.message.reply_text(
            "💳 ZELLE PAYMENT\n\n"
            f"Send {money(entry_price)} to:\n"
            f"{zelle}\n\n"
            "After sending your payment, "
            "tap I PAID below.\n\n"
            "Your entry will remain pending "
            "until an admin verifies payment.",
            reply_markup=paid_keyboard(
                "zelle"
            ),
        )

        return

    await query.answer()


# ==========================================================
# PAID ENTRY
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        await query.answer()
        return

    data = query.data or ""

    if not data.startswith(
        "raffle_paid:"
    ):
        await query.answer()
        return

    payment_method = data.split(
        ":",
        1,
    )[1]

    raffle_info = find_active_raffle()

    if not raffle_info:
        await query.answer(
            "There is no active raffle.",
            show_alert=True,
        )
        return

    raffle_id = raffle_info.get(
        "id"
    )

    # ------------------------------------------------------
    # Prevent FREE raffle from going through payment.
    # ------------------------------------------------------

    if money_value(
        raffle_info.get("price")
    ) == 0:
        await query.answer(
            "This raffle is FREE!",
            show_alert=True,
        )
        return

    try:
        entry_id = db_call(
            "add_raffle_entry",
            raffle_id,
            user.id,
            user.username,
            user.full_name,
            payment_method,
        )

    except Exception as exc:
        logger.exception(
            "Could not create raffle entry."
        )

        await query.answer(
            "Could not create your entry.",
            show_alert=True,
        )

        await query.message.reply_text(
            "⚠️ I could not create your raffle entry.\n\n"
            f"Database error: {exc}"
        )

        return

    if entry_id is None:
        await query.answer(
            "You are already entered.",
            show_alert=True,
        )

        await query.message.reply_text(
            "⚠️ You already have an active or pending "
            "entry for this raffle."
        )

        return

    await query.answer(
        "Payment submitted."
    )

    await query.message.reply_text(
        "✅ PAYMENT SUBMITTED\n\n"
        "Your raffle entry is pending admin "
        "payment verification.\n\n"
        "You will be notified once your payment "
        "is approved."
    )

    # ------------------------------------------------------
    # Notify admins.
    # ------------------------------------------------------

    admin_text = (
        "💰 RAFFLE PAYMENT PENDING\n\n"
        f"👤 User: {user.full_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"💳 Method: {payment_method.upper()}\n"
        f"🎟️ Entry ID: {entry_id}\n"
        f"💵 Amount: {money(raffle_info.get('price'))}\n\n"
        "Verify the payment before approving."
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
                reply_markup=payment_admin_keyboard(
                    entry_id
                ),
            )

        except TelegramError as exc:
            logger.warning(
                "Could not notify admin %s: %s",
                admin_id,
                exc,
            )


# ==========================================================
# ADMIN PAYMENT APPROVAL
# ==========================================================

async def admin_payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):
        await query.answer(
            "Admin access required.",
            show_alert=True,
        )
        return

    data = query.data or ""

    if ":" not in data:
        await query.answer()
        return

    action, entry_id_text = data.split(
        ":",
        1,
    )

    try:
        entry_id = int(
            entry_id_text
        )
    except ValueError:
        await query.answer(
            "Invalid entry.",
            show_alert=True,
        )
        return

    # ------------------------------------------------------
    # APPROVE ENTRY
    # ------------------------------------------------------

    if action == "raffle_payment_approve":
        try:
            changed = db_call(
                "approve_entry",
                entry_id,
                user.id,
            )

        except Exception:
            logger.exception(
                "Failed to approve entry %s",
                entry_id,
            )

            await query.answer(
                "Could not approve entry.",
                show_alert=True,
            )
            return

        if not changed:
            await query.answer(
                "Entry was already processed.",
                show_alert=True,
            )
            return

        entry = None

        try:
            entry = db_call(
                "get_entry",
                entry_id,
            )
        except Exception:
            logger.exception(
                "Could not retrieve approved entry."
            )

        await query.answer(
            "Entry approved."
        )

        try:
            await query.edit_message_text(
                "✅ Raffle entry approved.\n\n"
                f"Entry ID: {entry_id}"
            )
        except TelegramError:
            pass

        # --------------------------------------------------
        # Notify member.
        # --------------------------------------------------

        if isinstance(entry, dict):
            member_id = entry.get(
                "user_id"
            )

            if member_id:
                try:
                    await context.bot.send_message(
                        chat_id=member_id,
                        text=(
                            "🎉 YOUR RAFFLE ENTRY IS APPROVED!\n\n"
                            "Your payment has been verified "
                            "and your raffle entry is active.\n\n"
                            "👑 Good luck!"
                        ),
                    )
                except TelegramError:
                    pass

        return

    # ------------------------------------------------------
    # DENY ENTRY
    # ------------------------------------------------------

    if action == "raffle_payment_deny":
        try:
            changed = db_call(
                "deny_entry",
                entry_id,
                user.id,
            )

        except Exception:
            logger.exception(
                "Failed to deny entry %s",
                entry_id,
            )

            await query.answer(
                "Could not deny entry.",
                show_alert=True,
            )
            return

        if not changed:
            await query.answer(
                "Entry was already processed.",
                show_alert=True,
            )
            return

        entry = None

        try:
            entry = db_call(
                "get_entry",
                entry_id,
            )
        except Exception:
            logger.exception(
                "Could not retrieve denied entry."
            )

        await query.answer(
            "Entry denied."
        )

        try:
            await query.edit_message_text(
                "❌ Raffle entry denied.\n\n"
                f"Entry ID: {entry_id}"
            )
        except TelegramError:
            pass

        if isinstance(entry, dict):
            member_id = entry.get(
                "user_id"
            )

            if member_id:
                try:
                    await context.bot.send_message(
                        chat_id=member_id,
                        text=(
                            "❌ Your raffle payment "
                            "was not approved.\n\n"
                            "Please contact an admin "
                            "if you believe this was "
                            "an error."
                        ),
                    )
                except TelegramError:
                    pass

        return

    await query.answer()


# ==========================================================
# ENTER RAFFLE COMMAND
# ==========================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    raffle_info = find_active_raffle()

    if not raffle_info:
        await message.reply_text(
            "⚠️ There is currently no active raffle."
        )
        return

    entry_price = raffle_info.get(
        "price"
    )

    free = money_value(
        entry_price
    ) == 0

    await message.reply_text(
        "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: {money(entry_price)}\n\n"
        "Choose an option below:",
        reply_markup=raffle_member_keyboard(
            free=free
        ),
    )


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 Admin access required."
        )
        return

    try:
        entries = db_call(
            "get_pending_entries"
        )
    except Exception:
        logger.exception(
            "Could not retrieve pending entries."
        )

        await message.reply_text(
            "⚠️ Could not retrieve pending entries."
        )
        return

    if not entries:
        await message.reply_text(
            "✅ There are no pending raffle entries."
        )
        return

    lines = [
        "💰 PENDING RAFFLE ENTRIES",
        "",
    ]

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        lines.append(
            f"🎟️ ID: {entry.get('id')}"
        )

        lines.append(
            f"👤 {entry.get('display_name', 'Unknown')}"
        )

        lines.append(
            f"💳 {entry.get('payment_method', 'Unknown')}"
        )

        lines.append(
            f"🎟️ Raffle ID: {entry.get('raffle_id')}"
        )

        lines.append("")

    await message.reply_text(
        "\n".join(lines)
    )


# ==========================================================
# RAFFLE STATUS
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    raffle_info = find_active_raffle()

    if not raffle_info:
        await message.reply_text(
            "⚠️ No active raffle."
        )
        return

    try:
        entries = db_call(
            "get_approved_entries",
            raffle_info.get("id"),
        )
    except Exception:
        logger.exception(
            "Could not retrieve approved entries."
        )
        entries = []

    approved = len(
        entries or []
    )

    await message.reply_text(
        "🎟️ RAFFLE STATUS\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: {money(raffle_info.get('price'))}\n"
        f"👥 Approved Entries: {approved}\n"
        f"⏱️ Time Remaining: "
        f"{format_countdown(raffle_info.get('expires_at'))}"
    )


# ==========================================================
# RAFFLE ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 Admin access required."
        )
        return

    raffle_info = find_active_raffle()

    if not raffle_info:
        await message.reply_text(
            "⚠️ No active raffle."
        )
        return

    try:
        entries = db_call(
            "get_approved_entries",
            raffle_info.get("id"),
        )

    except Exception:
        logger.exception(
            "Could not retrieve raffle entries."
        )

        await message.reply_text(
            "⚠️ Could not retrieve entries."
        )
        return

    if not entries:
        await message.reply_text(
            "🎟️ No approved raffle entries yet."
        )
        return

    lines = [
        "🎟️ RAFFLE ENTRIES",
        "",
    ]

    for number, entry in enumerate(
        entries,
        start=1,
    ):
        if not isinstance(entry, dict):
            continue

        name = (
            entry.get("display_name")
            or entry.get("username")
            or "Unknown"
        )

        lines.append(
            f"{number}. {name}"
        )

        lines.append(
            f"   ID: {entry.get('id')}"
        )

    await message.reply_text(
        "\n".join(lines)
    )


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 Admin access required."
        )
        return

    raffle_info = find_active_raffle()

    if not raffle_info:
        await message.reply_text(
            "⚠️ No active raffle."
        )
        return

    raffle_id = raffle_info.get(
        "id"
    )

    try:
        changed = db_call(
            "close_raffle",
            raffle_id,
        )

    except Exception:
        logger.exception(
            "Could not cancel raffle."
        )

        await message.reply_text(
            "⚠️ Could not cancel raffle."
        )
        return

    if not changed:
        await message.reply_text(
            "⚠️ The raffle could not be closed. "
            "It may already be closed."
        )
        return

    await message.reply_text(
        "❌ Raffle cancelled."
    )


# ==========================================================
# DRAW RAFFLE
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 Admin access required."
        )
        return

    raffle_info = find_active_raffle()

    if not raffle_info:
        await message.reply_text(
            "⚠️ No active raffle."
        )
        return

    raffle_id = raffle_info.get(
        "id"
    )

    try:
        entries = db_call(
            "get_approved_entries",
            raffle_id,
        )

    except Exception:
        logger.exception(
            "Could not retrieve entries."
        )

        await message.reply_text(
            "⚠️ Could not retrieve entries."
        )
        return

    eligible = [
        entry
        for entry in (entries or [])
        if isinstance(entry, dict)
    ]

    if not eligible:
        await message.reply_text(
            "⚠️ There are no approved "
            "entries to draw from."
        )
        return

    winner = random.choice(
        eligible
    )

    winner_name = (
        winner.get("display_name")
        or winner.get("username")
        or "Unknown"
    )

    winner_id = winner.get(
        "user_id"
    )

    await message.reply_text(
        "🎉🎉🎉 RAFFLE WINNER 🎉🎉🎉\n\n"
        f"🏆 {winner_name}\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n\n"
        "👑 Congratulations!"
    )

    # ------------------------------------------------------
    # Close raffle after draw.
    #
    # raffle_database.py does not have a winner column,
    # so the winner is announced but not stored in the
    # database.
    # ------------------------------------------------------

    try:
        db_call(
            "close_raffle",
            raffle_id,
        )
    except Exception:
        logger.warning(
            "Could not close raffle after draw.",
            exc_info=True,
        )

    if winner_id:
        try:
            await context.bot.send_message(
                chat_id=winner_id,
                text=(
                    "🎉 CONGRATULATIONS!\n\n"
                    "You won the Melanated AZ "
                    "Friends Raffle!\n\n"
                    f"🎁 Prize: "
                    f"{raffle_info.get('prize')}\n\n"
                    "An admin will contact you "
                    "with the next steps."
                ),
            )

        except TelegramError:
            pass


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 Admin access required."
        )
        return

    # ------------------------------------------------------
    # Reroll works against the most recently closed raffle.
    # ------------------------------------------------------

    raffle_info = None

    try:
        active = db_call(
            "get_active_raffle"
        )

        if active:
            raffle_info = active

    except Exception:
        logger.exception(
            "Could not retrieve active raffle."
        )

    if not raffle_info:
        try:
            raffle_info = db_call(
                "get_pending_raffle"
            )
        except Exception:
            raffle_info = None

    if not raffle_info:
        await message.reply_text(
            "⚠️ There is no active raffle "
            "available for a reroll."
        )
        return

    try:
        entries = db_call(
            "get_approved_entries",
            raffle_info.get("id"),
        )
    except Exception:
        await message.reply_text(
            "⚠️ Could not retrieve entries."
        )
        return

    eligible = [
        entry
        for entry in (entries or [])
        if isinstance(entry, dict)
    ]

    if not eligible:
        await message.reply_text(
            "⚠️ No eligible entries."
        )
        return

    winner = random.choice(
        eligible
    )

    winner_name = (
        winner.get("display_name")
        or winner.get("username")
        or "Unknown"
    )

    await message.reply_text(
        "🔄 RAFFLE REROLL\n\n"
        f"🏆 New Winner: {winner_name}\n\n"
        f"🎁 Prize: "
        f"{raffle_info.get('prize')}"
    )


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 Admin access required."
        )
        return

    if not context.args:
        await message.reply_text(
            "Usage:\n"
            "/bonusentry USER_ID"
        )
        return

    try:
        target_user_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "⚠️ Invalid user ID."
        )
        return

    raffle_info = find_active_raffle()

    if not raffle_info:
        await message.reply_text(
            "⚠️ No active raffle."
        )
        return

    try:
        entry_id = db_call(
            "add_raffle_entry",
            raffle_info.get("id"),
            target_user_id,
            None,
            "Bonus Entry",
            "bonus",
        )

    except Exception:
        logger.exception(
            "Could not create bonus entry."
        )

        await message.reply_text(
            "⚠️ Could not add bonus entry."
        )
        return

    if entry_id is None:
        await message.reply_text(
            "⚠️ Could not add bonus entry.\n\n"
            "The user may already have an entry."
        )
        return

    try:
        db_call(
            "approve_entry",
            entry_id,
            user.id,
        )

    except Exception:
        logger.exception(
            "Could not approve bonus entry."
        )

        await message.reply_text(
            "⚠️ Bonus entry was created but "
            "could not be approved."
        )
        return

    await message.reply_text(
        "🎟️ Bonus entry added successfully.\n\n"
        f"Entry ID: {entry_id}"
    )


# ==========================================================
# REMOVE RAFFLE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(user.id):
        await message.reply_text(
            "🚫 Admin access required."
        )
        return

    if not context.args:
        await message.reply_text(
            "Usage:\n"
            "/removeentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "⚠️ Invalid entry ID."
        )
        return

    try:
        changed = db_call(
            "remove_entry",
            entry_id,
        )

    except Exception:
        logger.exception(
            "Could not remove entry."
        )

        await message.reply_text(
            "⚠️ Could not remove entry."
        )
        return

    if not changed:
        await message.reply_text(
            "⚠️ Entry was not found."
        )
        return

    await message.reply_text(
        f"🗑️ Entry {entry_id} removed."
    )


# ==========================================================
# RAFFLE CALLBACK ROUTER
# ==========================================================

async def raffle_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Raffle callback: %s",
        data,
    )

    # ------------------------------------------------------
    # START RAFFLE
    # ------------------------------------------------------

    if data in (
        "start_raffle",
        "raffle_start",
        "raffle_start_raffle",
        "startraffle",
        "raffle_start_button",
        "start_raffle_button",
    ):
        await query.answer(
            "Starting raffle setup..."
        )

        # IMPORTANT:
        # The button itself needs to trigger the same
        # setup flow as /startraffle.
        #
        # Create a simple setup state here.
        #
        user = update.effective_user

        if not user or not is_admin(user.id):
            await query.message.reply_text(
                "🚫 Admin access required."
            )
            return

        context.user_data[
            "awaiting_raffle_setup"
        ] = True

        context.user_data.pop(
            "raffle_setup",
            None,
        )

        context.user_data.pop(
            "pending_raffle",
            None,
        )

        await query.message.reply_text(
            "🎟️ START RAFFLE\n\n"
            "Enter the raffle information:\n\n"
            "$100 Cash Prize | $5\n\n"
            "FREE raffles are supported:\n"
            "FREE Prize | FREE\n\n"
            "Format:\n"
            "PRIZE | ENTRY PRICE"
        )

        return

    # ------------------------------------------------------
    # APPROVAL
    # ------------------------------------------------------

    if data.startswith(
        "raffle_approve:"
    ) or data.startswith(
        "raffle_cancel:"
    ):
        await raffle_approval_button(
            update,
            context,
        )
        return

    # ------------------------------------------------------
    # ENTER
    # ------------------------------------------------------

    if data == "raffle_enter":
        await raffle_enter_button(
            update,
            context,
        )
        return

    # ------------------------------------------------------
    # PAYMENT
    # ------------------------------------------------------

    if data in (
        "raffle_cashapp",
        "raffle_zelle",
    ):
        await payment_button(
            update,
            context,
        )
        return

    # ------------------------------------------------------
    # PAID
    # ------------------------------------------------------

    if data.startswith(
        "raffle_paid:"
    ):
        await paid_entry(
            update,
            context,
        )
        return

    # ------------------------------------------------------
    # ADMIN PAYMENT
    # ------------------------------------------------------

    if data.startswith(
        "raffle_payment_approve:"
    ) or data.startswith(
        "raffle_payment_deny:"
    ):
        await admin_payment_button(
            update,
            context,
        )
        return

    await query.answer()


# ==========================================================
# RAFFLE COUNTDOWN
# ==========================================================

async def update_raffle_countdown(
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        raffle_info = find_active_raffle()

    except Exception:
        logger.exception(
            "Could not retrieve active raffle "
            "for countdown."
        )
        return

    if not raffle_info:
        return

    expires_at = raffle_info.get(
        "expires_at"
    )

    remaining = format_countdown(
        expires_at
    )

    raffle_id = raffle_info.get(
        "id"
    )

    chat_id = raffle_info.get(
        "chat_id"
    ) or RAFFLE_CHAT_ID

    message_id = raffle_info.get(
        "message_id"
    )

    if not message_id:
        return

    prize = raffle_info.get(
        "prize"
    )

    entry_price = raffle_info.get(
        "price"
    )

    free = money_value(
        entry_price
    ) == 0

    text = (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
        f"🎁 PRIZE: {prize}\n"
        f"💵 ENTRY: {money(entry_price)}\n\n"
    )

    if free:
        text += (
            "🎉 This raffle is FREE!\n\n"
            "Tap ENTER RAFFLE below to join.\n\n"
        )
    else:
        text += (
            "Ready to join?\n"
            "Tap ENTER RAFFLE below.\n\n"
            "💳 Payment options are available "
            "after selecting your entry.\n\n"
        )

    text += (
        f"⏱️ TIME REMAINING: {remaining}\n\n"
        "👑 Good luck everyone!"
    )

    # ------------------------------------------------------
    # Expired
    # ------------------------------------------------------

    if remaining == "⏰ ENDED":
        try:
            db_call(
                "close_raffle",
                raffle_id,
            )
        except Exception:
            logger.warning(
                "Could not close expired raffle %s.",
                raffle_id,
                exc_info=True,
            )

        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=(
                    "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
                    f"🎁 PRIZE: {prize}\n"
                    f"💵 ENTRY: {money(entry_price)}\n\n"
                    "⏰ RAFFLE ENDED\n\n"
                    "👑 Thank you for participating!"
                ),
            )
        except TelegramError:
            logger.warning(
                "Could not close raffle message.",
                exc_info=True,
            )

        return

    # ------------------------------------------------------
    # Update countdown
    # ------------------------------------------------------

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=raffle_member_keyboard(
                free=free
            ),
        )

    except TelegramError as exc:
        if "Message is not modified" not in str(exc):
            logger.warning(
                "Could not update raffle countdown: %s",
                exc,
            )


# ==========================================================
# END raffle.py
# ==========================================================
