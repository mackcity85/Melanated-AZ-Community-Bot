# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# COMPLETE PRODUCTION VERSION
#
# FEATURES:
#   - Start raffle button support
#   - Admin raffle approval
#   - Paid raffles
#   - FREE raffles
#   - Cash App payments
#   - Zelle payments
#   - Payment approval workflow
#   - Raffle countdown
#   - Winner drawing
#   - Reroll
#   - Bonus entries
#   - Entry removal
#   - Database persistence
#
# FREE RAFFLE FORMAT:
#
#   $100 Cash Prize | FREE
#
# PAID RAFFLE FORMAT:
#
#   $100 Cash Prize | $5
#
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

from telegram.error import (
    BadRequest,
    TelegramError,
)

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

logger = logging.getLogger(
    "melanated_az_raffle"
)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):
    try:
        admin_ids = {
            int(x)
            for x in ADMIN_IDS
        }
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
        10.50

    into a float.

    Returns None if invalid.
    """

    if value is None:
        return None

    value = str(value).strip()

    value = value.replace(
        "$",
        "",
    )

    value = value.replace(
        ",",
        "",
    )

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def money(value):
    """
    Format a monetary value.

    Examples:

        5      -> $5
        10.50  -> $10.50
        0      -> FREE
    """

    if value is None:
        return "$0.00"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "$0.00"

    if value <= 0:
        return "FREE"

    if value.is_integer():
        return f"${int(value)}"

    return f"${value:.2f}"


def is_free_raffle(raffle_info):
    """
    Determine whether a raffle is FREE.

    Supports database records containing:

        entry_price = 0
        entry_price = "0"
        entry_price = "FREE"

    """

    if not raffle_info:
        return False

    value = raffle_info.get(
        "entry_price"
    )

    if value is None:
        return False

    if isinstance(value, str):

        if value.strip().upper() == "FREE":
            return True

    numeric = money_value(value)

    return numeric is not None and numeric <= 0


# ==========================================================
# COUNTDOWN
# ==========================================================

def format_countdown(expires_at):
    """
    Format remaining raffle time.
    """

    if not expires_at:
        return "Expired"

    try:

        if isinstance(
            expires_at,
            str,
        ):

            expires = datetime.fromisoformat(
                expires_at.replace(
                    "Z",
                    "+00:00",
                )
            )

        else:

            expires = expires_at

        if expires.tzinfo is None:

            expires = expires.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(
            timezone.utc
        )

        seconds = int(
            (
                expires - now
            ).total_seconds()
        )

    except Exception:

        logger.exception(
            "Could not format raffle countdown."
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
    Return expiration timestamp in UTC.
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

        days = int(
            RAFFLE_DURATION_DAYS
        )

    return (
        datetime.now(
            timezone.utc
        ).timestamp()
        + (
            days * 86400
        )
    )


def timestamp_to_iso(timestamp):
    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).isoformat()


# ==========================================================
# DATABASE COMPATIBILITY
# ==========================================================

def db_call(
    function_name,
    *args,
    **kwargs,
):
    """
    Call a database function while providing
    a clear error when it does not exist.
    """

    function = getattr(
        db,
        function_name,
        None,
    )

    if not callable(function):

        raise RuntimeError(
            "raffle_database.py is missing "
            f"function: {function_name}"
        )

    return function(
        *args,
        **kwargs,
    )


def find_active_raffle():
    """
    Locate the active raffle.

    Supports several database function names.
    """

    for name in (
        "get_active_raffle",
        "get_current_raffle",
        "get_active",
    ):

        function = getattr(
            db,
            name,
            None,
        )

        if callable(function):

            return function()

    return None


# ==========================================================
# KEYBOARDS
# ==========================================================

def raffle_member_keyboard():

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
                ),
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data="raffle_zelle",
                ),
            ],
        ]
    )


def free_raffle_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER FREE RAFFLE",
                    callback_data="raffle_free_enter",
                )
            ]
        ]
    )


def admin_approval_keyboard(
    raffle_id,
):

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


def payment_admin_keyboard(
    entry_id,
):

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
# START RAFFLE COMMAND
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
        "PAID RAFFLE:\n"
        "$100 Cash Prize | $5\n\n"
        "FREE RAFFLE:\n"
        "$100 Cash Prize | FREE\n\n"
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
    """
    Handles the admin's next text message after
    pressing Start Raffle.
    """

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
        message.text
        or ""
    ).strip()

    if not text:
        return True

    # ------------------------------------------------------
    # EXPECT:
    #
    # $100 Cash Prize | $5
    #
    # OR
    #
    # $100 Cash Prize | FREE
    # ------------------------------------------------------

    if "|" not in text:

        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Paid raffle:\n"
            "$100 Cash Prize | $5\n\n"
            "Free raffle:\n"
            "$100 Cash Prize | FREE"
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
            "⚠️ Please enter a prize.\n\n"
            "Example:\n"
            "$100 Cash Prize | $5"
        )

        return True

    # ------------------------------------------------------
    # FREE RAFFLE
    # ------------------------------------------------------

    if entry_text.strip().upper() == "FREE":

        entry_price = 0
        free_raffle = True

    else:

        # --------------------------------------------------
        # PAID RAFFLE
        # --------------------------------------------------

        entry_price = money_value(
            entry_text
        )

        free_raffle = False

        if (
            entry_price is None
            or entry_price <= 0
        ):

            await message.reply_text(
                "⚠️ Invalid entry price.\n\n"
                "Use either:\n\n"
                "$100 Cash Prize | $5\n\n"
                "or:\n\n"
                "$100 Cash Prize | FREE"
            )

            return True

    # ------------------------------------------------------
    # SAVE SETUP
    # ------------------------------------------------------

    context.user_data[
        "raffle_setup"
    ] = {
        "prize": prize_text,
        "entry_price": entry_price,
        "free": free_raffle,
    }

    context.user_data.pop(
        "awaiting_raffle_setup",
        None,
    )

    await create_pending_raffle(
        update,
        context,
        prize_text,
        entry_price,
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

    try:

        raffle_id = db_call(
            "create_raffle",
            prize=prize,
            entry_price=entry_price,
            expires_at=expires_at,
            status="pending",
            created_by=user.id,
        )

    except TypeError:

        try:

            raffle_id = db_call(
                "create_raffle",
                prize,
                entry_price,
                expires_at,
                "pending",
                user.id,
            )

        except Exception:

            logger.exception(
                "Could not create pending raffle."
            )

            await message.reply_text(
                "⚠️ I could not create the raffle "
                "in the database.\n\n"
                "Check the raffle database configuration."
            )

            return

    except Exception:

        logger.exception(
            "Could not create pending raffle."
        )

        await message.reply_text(
            "⚠️ I could not create the raffle "
            "in the database.\n\n"
            "Check the raffle database configuration."
        )

        return

    context.user_data[
        "pending_raffle"
    ] = raffle_id

    duration = os.environ.get(
        "RAFFLE_DURATION_DAYS",
        RAFFLE_DURATION_DAYS,
    )

    if entry_price <= 0:

        entry_display = "FREE"

    else:

        entry_display = money(
            entry_price
        )

    text = (
        "🎟️ RAFFLE READY FOR APPROVAL\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry: {entry_display}\n"
        f"⏱️ Duration: {duration} days\n\n"
        "Approve this raffle to post it "
        "in the Melanated AZ group."
    )

    # ------------------------------------------------------
    # SEND APPROVAL TO ADMINS
    # ------------------------------------------------------

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
        f"💵 Entry: {entry_display}\n\n"
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

    action, raffle_id = data.split(
        ":",
        1,
    )

    try:

        raffle_id = int(
            raffle_id
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

            db_call(
                "cancel_raffle",
                raffle_id,
            )

        except Exception:

            logger.exception(
                "Failed to cancel raffle %s",
                raffle_id,
            )

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

    try:

        db_call(
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

    await query.answer(
        "Raffle approved!"
    )

    try:

        await query.edit_message_text(
            "✅ Raffle approved and posted "
            "to the group."
        )

    except TelegramError:
        pass

    # ------------------------------------------------------
    # GET VALUES
    # ------------------------------------------------------

    prize = raffle_info.get(
        "prize"
    )

    entry_price = raffle_info.get(
        "entry_price"
    )

    expires_at = raffle_info.get(
        "expires_at"
    )

    free_raffle = is_free_raffle(
        raffle_info
    )

    if free_raffle:

        entry_display = "FREE"

    else:

        entry_display = money(
            entry_price
        )

    # ------------------------------------------------------
    # RAFFLE MESSAGE
    # ------------------------------------------------------

    raffle_text = (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
        f"🎁 PRIZE: {prize}\n"
        f"💵 ENTRY: {entry_display}\n\n"
        "Ready to join?\n"
        "Tap the button below.\n\n"
    )

    if free_raffle:

        raffle_text += (
            "🎉 This raffle is FREE to enter!\n\n"
        )

    else:

        raffle_text += (
            "💳 Payment options are available "
            "after selecting your entry.\n\n"
        )

    raffle_text += (
        f"⏱️ Time Remaining: "
        f"{format_countdown(expires_at)}\n\n"
        "👑 Good luck everyone!"
    )

    try:

        if free_raffle:

            posted = await context.bot.send_message(
                chat_id=RAFFLE_CHAT_ID,
                text=raffle_text,
                reply_markup=free_raffle_keyboard(),
            )

        else:

            posted = await context.bot.send_message(
                chat_id=RAFFLE_CHAT_ID,
                text=raffle_text,
                reply_markup=raffle_member_keyboard(),
            )

    except TelegramError:

        logger.exception(
            "Could not post raffle to group."
        )

        return

    # ------------------------------------------------------
    # SAVE GROUP POST METADATA
    # ------------------------------------------------------

    try:

        db_call(
            "set_raffle_message",
            raffle_id,
            posted.chat_id,
            posted.message_id,
        )

    except Exception:

        logger.warning(
            "Could not save raffle group message metadata.",
            exc_info=True,
        )


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

    if is_free_raffle(
        raffle_info
    ):

        await free_raffle_entry(
            update,
            context,
        )

        return

    await query.answer(
        "Raffle entry started."
    )

    entry_price = raffle_info.get(
        "entry_price"
    )

    try:

        await query.message.reply_text(
            "🎟️ RAFFLE ENTRY\n\n"
            f"Entry price: {money(entry_price)}\n\n"
            "Choose how you would like to pay:",
            reply_markup=InlineKeyboardMarkup(
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
            ),
        )

    except TelegramError:

        logger.exception(
            "Could not send raffle payment options."
        )


# ==========================================================
# FREE RAFFLE ENTRY
# ==========================================================

async def free_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    raffle_info = find_active_raffle()

    if not raffle_info:

        await query.answer(
            "There is currently no active raffle.",
            show_alert=True,
        )

        return

    raffle_id = raffle_info.get(
        "id"
    )

    # ------------------------------------------------------
    # CHECK FOR EXISTING ENTRY
    # ------------------------------------------------------

    try:

        existing_entries = db_call(
            "get_raffle_entries",
            raffle_id,
        )

    except Exception:

        existing_entries = []

    for entry in existing_entries or []:

        if not isinstance(
            entry,
            dict,
        ):
            continue

        if entry.get(
            "user_id"
        ) != user.id:

            continue

        status = str(
            entry.get(
                "status",
                "",
            )
        ).lower()

        if status not in (
            "denied",
            "removed",
            "cancelled",
        ):

            await query.answer(
                "You already have an entry in this raffle.",
                show_alert=True,
            )

            return

    # ------------------------------------------------------
    # CREATE FREE ENTRY
    # ------------------------------------------------------

    try:

        entry_id = db_call(
            "create_raffle_entry",
            raffle_id=raffle_id,
            user_id=user.id,
            username=user.username,
            display_name=user.full_name,
            payment_method="free",
            status="approved",
        )

    except TypeError:

        try:

            entry_id = db_call(
                "create_raffle_entry",
                raffle_id,
                user.id,
                user.username,
                user.full_name,
                "free",
                "approved",
            )

        except Exception:

            logger.exception(
                "Could not create free raffle entry."
            )

            await query.answer(
                "Could not create your entry.",
                show_alert=True,
            )

            return

    except Exception:

        logger.exception(
            "Could not create free raffle entry."
        )

        await query.answer(
            "Could not create your entry.",
            show_alert=True,
        )

        return

    await query.answer(
        "You're entered!"
    )

    try:

        await query.message.reply_text(
            "🎉 YOU'RE IN!\n\n"
            "Your FREE raffle entry has been "
            "successfully added.\n\n"
            f"🎟️ Entry ID: {entry_id}\n\n"
            "👑 Good luck!"
        )

    except TelegramError:

        logger.exception(
            "Could not confirm free raffle entry."
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

    # ------------------------------------------------------
    # FREE RAFFLE
    # ------------------------------------------------------

    if is_free_raffle(
        raffle_info
    ):

        await query.answer(
            "This raffle is FREE. No payment is required.",
            show_alert=True,
        )

        return

    entry_price = raffle_info.get(
        "entry_price"
    )

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
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ I PAID",
                            callback_data=(
                                "raffle_paid:zelle"
                            ),
                        )
                    ]
                ]
            ),
        )

        return

    await query.answer()


# ==========================================================
# PAID ENTRY BUTTON
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

    # ------------------------------------------------------
    # PREVENT PAYMENT ON FREE RAFFLE
    # ------------------------------------------------------

    if is_free_raffle(
        raffle_info
    ):

        await query.answer(
            "This raffle is FREE. No payment is required.",
            show_alert=True,
        )

        return

    raffle_id = raffle_info.get(
        "id"
    )

    # ------------------------------------------------------
    # PREVENT DUPLICATE ENTRIES
    # ------------------------------------------------------

    try:

        existing_entries = db_call(
            "get_raffle_entries",
            raffle_id,
        )

    except Exception:

        existing_entries = []

    for entry in existing_entries or []:

        if not isinstance(
            entry,
            dict,
        ):
            continue

        if entry.get(
            "user_id"
        ) != user.id:

            continue

        status = str(
            entry.get(
                "status",
                "",
            )
        ).lower()

        if status not in (
            "denied",
            "removed",
            "cancelled",
        ):

            await query.answer(
                "You already have an entry in this raffle.",
                show_alert=True,
            )

            return

    # ------------------------------------------------------
    # CREATE ENTRY
    # ------------------------------------------------------

    try:

        entry_id = db_call(
            "create_raffle_entry",
            raffle_id=raffle_id,
            user_id=user.id,
            username=user.username,
            display_name=user.full_name,
            payment_method=payment_method,
            status="pending",
        )

    except TypeError:

        try:

            entry_id = db_call(
                "create_raffle_entry",
                raffle_id,
                user.id,
                user.username,
                user.full_name,
                payment_method,
                "pending",
            )

        except Exception:

            logger.exception(
                "Could not create raffle entry."
            )

            await query.answer(
                "Could not create your entry.",
                show_alert=True,
            )

            return

    except Exception:

        logger.exception(
            "Could not create raffle entry."
        )

        await query.answer(
            "Could not create your entry.",
            show_alert=True,
        )

        return

    await query.answer(
        "Payment submitted."
    )

    try:

        await query.message.reply_text(
            "✅ PAYMENT SUBMITTED\n\n"
            "Your raffle entry is pending admin "
            "payment verification.\n\n"
            "You will be notified once your payment "
            "is approved."
        )

    except TelegramError:
        pass

    # ------------------------------------------------------
    # NOTIFY ADMINS
    # ------------------------------------------------------

    admin_text = (
        "💰 RAFFLE PAYMENT PENDING\n\n"
        f"👤 User: {user.full_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"💳 Method: {payment_method.upper()}\n"
        f"🎟️ Entry ID: {entry_id}\n\n"
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

    parts = data.split(
        ":",
        1,
    )

    if len(parts) != 2:

        await query.answer()

        return

    action, entry_id = parts

    try:

        entry_id = int(
            entry_id
        )

    except ValueError:

        await query.answer(
            "Invalid entry.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # APPROVE
    # ------------------------------------------------------

    if action == "raffle_payment_approve":

        try:

            entry = db_call(
                "approve_raffle_entry",
                entry_id,
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

        if isinstance(
            entry,
            dict,
        ):

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
    # DENY
    # ------------------------------------------------------

    if action == "raffle_payment_deny":

        try:

            db_call(
                "deny_raffle_entry",
                entry_id,
            )

        except Exception:

            logger.exception(
                "Failed to deny entry %s",
                entry_id,
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

    free_raffle = is_free_raffle(
        raffle_info
    )

    if free_raffle:

        await message.reply_text(
            "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
            f"🎁 Prize: {raffle_info.get('prize')}\n"
            "💵 Entry: FREE\n\n"
            "No payment is required.\n\n"
            "Tap the button below to enter.",
            reply_markup=free_raffle_keyboard(),
        )

        return

    await message.reply_text(
        "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: "
        f"{money(raffle_info.get('entry_price'))}\n\n"
        "Choose an option below:",
        reply_markup=raffle_member_keyboard(),
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

        if not isinstance(
            entry,
            dict,
        ):
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
            "get_raffle_entries",
            raffle_info.get("id"),
        )

    except Exception:

        entries = []

    approved = 0

    for entry in entries or []:

        if not isinstance(
            entry,
            dict,
        ):
            continue

        status = str(
            entry.get(
                "status",
                "",
            )
        ).lower()

        if status in (
            "approved",
            "paid",
            "active",
        ):

            approved += 1

    if is_free_raffle(
        raffle_info
    ):

        entry_display = "FREE"

    else:

        entry_display = money(
            raffle_info.get(
                "entry_price"
            )
        )

    await message.reply_text(
        "🎟️ RAFFLE STATUS\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: {entry_display}\n"
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
            "get_raffle_entries",
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
            "🎟️ No raffle entries yet."
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

        if not isinstance(
            entry,
            dict,
        ):
            continue

        name = (
            entry.get(
                "display_name"
            )
            or entry.get(
                "username"
            )
            or "Unknown"
        )

        status = entry.get(
            "status",
            "unknown",
        )

        lines.append(
            f"{number}. {name} — {status}"
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

        db_call(
            "cancel_raffle",
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
            "get_raffle_entries",
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

    eligible = []

    for entry in entries or []:

        if not isinstance(
            entry,
            dict,
        ):
            continue

        status = str(
            entry.get(
                "status",
                "",
            )
        ).lower()

        if status in (
            "approved",
            "paid",
            "active",
        ):

            eligible.append(
                entry
            )

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
        winner.get(
            "display_name"
        )
        or winner.get(
            "username"
        )
        or "Unknown"
    )

    winner_id = winner.get(
        "user_id"
    )

    try:

        db_call(
            "set_raffle_winner",
            raffle_id,
            winner.get("id"),
        )

    except Exception:

        logger.warning(
            "Could not save raffle winner.",
            exc_info=True,
        )

    await message.reply_text(
        "🎉🎉🎉 RAFFLE WINNER 🎉🎉🎉\n\n"
        f"🏆 {winner_name}\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n\n"
        "👑 Congratulations!"
    )

    if winner_id:

        try:

            await context.bot.send_message(
                chat_id=winner_id,
                text=(
                    "🎉 CONGRATULATIONS!\n\n"
                    "You won the Melanated AZ Friends Raffle!\n\n"
                    f"🎁 Prize: {raffle_info.get('prize')}\n\n"
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

    raffle_info = find_active_raffle()

    if not raffle_info:

        await message.reply_text(
            "⚠️ No active raffle."
        )

        return

    try:

        entries = db_call(
            "get_raffle_entries",
            raffle_info.get("id"),
        )

    except Exception:

        await message.reply_text(
            "⚠️ Could not retrieve entries."
        )

        return

    eligible = []

    for entry in entries or []:

        if not isinstance(
            entry,
            dict,
        ):
            continue

        if str(
            entry.get(
                "status",
                "",
            )
        ).lower() in (
            "approved",
            "paid",
            "active",
        ):

            eligible.append(
                entry
            )

    if not eligible:

        await message.reply_text(
            "⚠️ No eligible entries."
        )

        return

    winner = random.choice(
        eligible
    )

    winner_name = (
        winner.get(
            "display_name"
        )
        or winner.get(
            "username"
        )
        or "Unknown"
    )

    await message.reply_text(
        "🔄 RAFFLE REROLL\n\n"
        f"🏆 New Winner: {winner_name}\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}"
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

        db_call(
            "create_raffle_entry",
            raffle_id=raffle_info.get(
                "id"
            ),
            user_id=target_user_id,
            username=None,
            display_name="Bonus Entry",
            payment_method="bonus",
            status="approved",
        )

    except Exception:

        logger.exception(
            "Could not create bonus entry."
        )

        await message.reply_text(
            "⚠️ Could not add bonus entry."
        )

        return

    await message.reply_text(
        "🎟️ Bonus entry added successfully."
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

        db_call(
            "remove_raffle_entry",
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
    #
    # bot.py handles this.
    # ------------------------------------------------------

    start_callbacks = {
        "start_raffle",
        "raffle_start",
        "raffle_start_raffle",
        "startraffle",
        "raffle_start_button",
        "start_raffle_button",
    }

    if data in start_callbacks:

        await query.answer(
            "Please use the Start Raffle setup."
        )

        return

    # ------------------------------------------------------
    # RAFFLE APPROVAL
    # ------------------------------------------------------

    if (
        data.startswith(
            "raffle_approve:"
        )
        or data.startswith(
            "raffle_cancel:"
        )
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
    # FREE ENTRY
    # ------------------------------------------------------

    if data == "raffle_free_enter":

        await free_raffle_entry(
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

    if (
        data.startswith(
            "raffle_payment_approve:"
        )
        or data.startswith(
            "raffle_payment_deny:"
        )
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
        "chat_id",
        RAFFLE_CHAT_ID,
    )

    message_id = raffle_info.get(
        "message_id"
    )

    if not message_id:
        return

    prize = raffle_info.get(
        "prize"
    )

    entry_price = raffle_info.get(
        "entry_price"
    )

    free_raffle = is_free_raffle(
        raffle_info
    )

    if free_raffle:

        entry_display = "FREE"

    else:

        entry_display = money(
            entry_price
        )

    # ------------------------------------------------------
    # BUILD MESSAGE
    # ------------------------------------------------------

    text = (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
        f"🎁 PRIZE: {prize}\n"
        f"💵 ENTRY: {entry_display}\n\n"
        "Ready to join?\n"
        "Tap the button below.\n\n"
    )

    if free_raffle:

        text += (
            "🎉 This raffle is FREE to enter!\n\n"
        )

        keyboard = free_raffle_keyboard()

    else:

        text += (
            "💳 Payment options are available "
            "after selecting your entry.\n\n"
        )

        keyboard = raffle_member_keyboard()

    text += (
        f"⏱️ TIME REMAINING: {remaining}\n\n"
        "👑 Good luck everyone!"
    )

    # ------------------------------------------------------
    # UPDATE GROUP MESSAGE
    # ------------------------------------------------------

    try:

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=keyboard,
        )

    except BadRequest as exc:

        if (
            "Message is not modified"
            not in str(exc)
        ):

            logger.warning(
                "Could not update raffle countdown: %s",
                exc,
            )

    except TelegramError:

        logger.warning(
            "Telegram error updating raffle countdown.",
            exc_info=True,
        )

    # ------------------------------------------------------
    # EXPIRE RAFFLE
    # ------------------------------------------------------

    if remaining == "⏰ ENDED":

        try:

            db_call(
                "expire_raffle",
                raffle_id,
            )

            logger.info(
                "Raffle %s automatically expired.",
                raffle_id,
            )

        except Exception:

            logger.warning(
                "Could not mark raffle %s expired.",
                raffle_id,
                exc_info=True,
            )
