# ==========================================================
# Melanated AZ Friends Raffle
# raffle.py
#
# COMPLETE CORRECTED VERSION
#
# Features:
#   - Admin-only raffle creation
#   - FREE raffles supported
#   - Paid raffles supported
#   - Cash App
#   - Zelle
#   - Admin raffle approval
#   - Admin payment approval
#   - Enter Raffle button
#   - Countdown
#   - Automatic expiration
#   - Winner drawing
#   - Reroll
#   - Bonus entries
#   - Remove entries
#   - Database compatibility
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

logger = logging.getLogger("melanated_az_raffle")


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

        FREE
        free
        $0
        0
        $5
        5
        $10.00

    into a float.

    FREE is treated as $0.
    """

    if value is None:
        return None

    value = str(value).strip()

    # FREE raffle
    if value.upper() in (
        "FREE",
        "NO COST",
        "NO CHARGE",
    ):
        return 0.0

    value = value.replace("$", "")
    value = value.replace(",", "")
    value = value.strip()

    if not value:
        return None

    try:
        amount = float(value)

        if amount < 0:
            return None

        return amount

    except (TypeError, ValueError):
        return None


def money(value):
    """
    Format money.

    0 becomes FREE.
    """

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "FREE"

    if value <= 0:
        return "FREE"

    if value.is_integer():
        return f"${int(value)}"

    return f"${value:.2f}"


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
                expires_at.replace(
                    "Z",
                    "+00:00",
                )
            )

        elif isinstance(expires_at, datetime):

            expires = expires_at

        else:

            expires = datetime.fromtimestamp(
                float(expires_at),
                tz=timezone.utc,
            )

        if expires.tzinfo is None:
            expires = expires.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        seconds = int(
            (
                expires - now
            ).total_seconds()
        )

    except Exception:

        logger.exception(
            "Could not format raffle expiration."
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
# EXPIRATION
# ==========================================================

def raffle_expiration():
    """
    Return expiration as UTC ISO string.
    """

    try:
        days = int(
            os.environ.get(
                "RAFFLE_DURATION_DAYS",
                RAFFLE_DURATION_DAYS,
            )
        )
    except (TypeError, ValueError):
        days = 7

    expiration = (
        datetime.now(timezone.utc)
        .timestamp()
        + (
            days * 86400
        )
    )

    return datetime.fromtimestamp(
        expiration,
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
    Support multiple versions of
    raffle_database.py.
    """

    possible_functions = (
        "get_active_raffle",
        "get_current_raffle",
        "get_active",
    )

    for function_name in possible_functions:

        function = getattr(
            db,
            function_name,
            None,
        )

        if not callable(function):
            continue

        try:

            result = function()

            return normalize_raffle(
                result
            )

        except Exception:

            logger.exception(
                "Database error using %s",
                function_name,
            )

    return None


def normalize_raffle(raffle):
    """
    Convert database tuple/list/object
    into a dictionary.

    Supports both newer and older
    database formats.
    """

    if raffle is None:
        return None

    if isinstance(raffle, dict):
        return raffle

    if hasattr(
        raffle,
        "_asdict",
    ):

        try:
            return raffle._asdict()
        except Exception:
            pass

    if isinstance(
        raffle,
        (tuple, list),
    ):

        # New format:
        #
        # id
        # prize
        # entry_price
        # expires_at
        # status
        # created_by
        # chat_id
        # message_id

        if len(raffle) >= 8:

            return {
                "id": raffle[0],
                "prize": raffle[1],
                "entry_price": raffle[2],
                "expires_at": raffle[3],
                "status": raffle[4],
                "created_by": raffle[5],
                "chat_id": raffle[6],
                "message_id": raffle[7],
            }

        # Older database:
        #
        # id
        # prize
        # description
        # active
        # created

        if len(raffle) >= 5:

            description = (
                raffle[2]
                or ""
            )

            entry_price = extract_price_from_description(
                description
            )

            return {
                "id": raffle[0],
                "prize": raffle[1],
                "description": description,
                "entry_price": entry_price,
                "active": raffle[3],
                "created": raffle[4],
                "expires_at": None,
                "chat_id": RAFFLE_CHAT_ID,
                "message_id": None,
            }

    return raffle


def extract_price_from_description(
    description
):
    """
    Attempt to recover an entry price
    from an older database description.
    """

    if not description:
        return 0.0

    text = str(description)

    if "FREE" in text.upper():
        return 0.0

    # Look for Entry: $5
    import re

    match = re.search(
        r"(?:entry|price|cost)\s*[:\-]?\s*\$?\s*([0-9]+(?:\.[0-9]+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if match:

        try:
            return float(
                match.group(1)
            )
        except ValueError:
            pass

    return 0.0


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
                    callback_data="raffle_enter",
                )
            ]
        ]
    )


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


def admin_approval_keyboard(
    raffle_id
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
    entry_id
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
        "FREE raffle example:\n"
        "$100 Cash Prize | FREE\n\n"
        "Paid raffle example:\n"
        "$250 Cash Prize | $10\n\n"
        "Format:\n"
        "PRIZE | ENTRY PRICE\n\n"
        "Use FREE for a free raffle."
    )


# ==========================================================
# RAFFLE SETUP
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
        message.text
        or ""
    ).strip()

    if not text:
        return True

    if "|" not in text:

        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Please use:\n"
            "$100 Cash Prize | $5\n\n"
            "Or:\n"
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
            "⚠️ Please enter a prize."
        )

        return True

    entry_price = money_value(
        entry_text
    )

    if entry_price is None:

        await message.reply_text(
            "⚠️ Invalid entry price.\n\n"
            "Use one of these formats:\n\n"
            "$5\n"
            "$10\n"
            "$10.00\n"
            "FREE\n\n"
            "Example:\n"
            "$100 Cash Prize | FREE"
        )

        return True

    context.user_data[
        "raffle_setup"
    ] = {
        "prize": prize_text,
        "entry_price": entry_price,
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

    expires_at = raffle_expiration()

    raffle_id = None

    # ------------------------------------------------------
    # NEW DATABASE FORMAT
    # ------------------------------------------------------

    create_function = getattr(
        db,
        "create_raffle",
        None,
    )

    if not callable(create_function):

        await message.reply_text(
            "⚠️ The raffle database is missing "
            "the create_raffle function."
        )

        return

    # ------------------------------------------------------
    # Try modern keyword format.
    # ------------------------------------------------------

    try:

        raffle_id = create_function(
            prize=prize,
            entry_price=entry_price,
            expires_at=expires_at,
            status="pending",
            created_by=user.id,
        )

    except TypeError:

        # --------------------------------------------------
        # Try positional modern format.
        # --------------------------------------------------

        try:

            raffle_id = create_function(
                prize,
                entry_price,
                expires_at,
                "pending",
                user.id,
            )

        except TypeError:

            # ----------------------------------------------
            # Older database format.
            # ----------------------------------------------

            try:

                description = (
                    f"Entry Price: "
                    f"{money(entry_price)}\n"
                    f"Expires: {expires_at}"
                )

                raffle_id = create_function(
                    prize,
                    description,
                )

            except Exception:

                logger.exception(
                    "All create_raffle formats failed."
                )

        except Exception:

            logger.exception(
                "Modern positional create_raffle failed."
            )

    except Exception:

        logger.exception(
            "Modern create_raffle failed."
        )

        # --------------------------------------------------
        # Try legacy database format if the newer schema
        # is not available.
        # --------------------------------------------------

        try:

            description = (
                f"Entry Price: "
                f"{money(entry_price)}\n"
                f"Expires: {expires_at}"
            )

            raffle_id = create_function(
                prize,
                description,
            )

        except Exception:

            logger.exception(
                "Legacy create_raffle also failed."
            )

    if raffle_id is None:

        await message.reply_text(
            "⚠️ I could not create the raffle "
            "in the database.\n\n"
            "The database function could not "
            "accept the raffle information.\n\n"
            "No raffle was posted."
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

    raffle_info = None

    try:

        raffle_info = db_call(
            "get_raffle",
            raffle_id,
        )

        raffle_info = normalize_raffle(
            raffle_info
        )

    except Exception:

        logger.warning(
            "get_raffle unavailable for %s",
            raffle_id,
            exc_info=True,
        )

    # ------------------------------------------------------
    # Approve database record.
    # ------------------------------------------------------

    try:

        db_call(
            "approve_raffle",
            raffle_id,
        )

    except Exception:

        # Older databases may use another name.
        try:

            db_call(
                "approve",
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

    if not raffle_info:

        try:

            raffle_info = find_active_raffle()

        except Exception:

            raffle_info = None

    if not raffle_info:

        logger.error(
            "Could not retrieve approved raffle %s",
            raffle_id,
        )

        return

    prize = raffle_info.get(
        "prize",
        "Raffle Prize",
    )

    entry_price = raffle_info.get(
        "entry_price",
        0,
    )

    expires_at = raffle_info.get(
        "expires_at"
    )

    # ------------------------------------------------------
    # Older database may not store expiration.
    # ------------------------------------------------------

    if not expires_at:

        expires_at = raffle_expiration()

    # ------------------------------------------------------
    # Build raffle message.
    # ------------------------------------------------------

    if float(entry_price or 0) <= 0:

        raffle_text = (
            "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
            f"🎁 PRIZE: {prize}\n"
            "💵 ENTRY: FREE\n\n"
            "This raffle is FREE to enter!\n\n"
            "Tap ENTER FREE RAFFLE below.\n\n"
            f"⏱️ Time Remaining: "
            f"{format_countdown(expires_at)}\n\n"
            "👑 Good luck everyone!"
        )

        keyboard = free_raffle_keyboard()

    else:

        raffle_text = (
            "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
            f"🎁 PRIZE: {prize}\n"
            f"💵 ENTRY: {money(entry_price)}\n\n"
            "Ready to join?\n"
            "Tap ENTER RAFFLE below.\n\n"
            "💳 Payment options are available "
            "after selecting your entry.\n\n"
            f"⏱️ Time Remaining: "
            f"{format_countdown(expires_at)}\n\n"
            "👑 Good luck everyone!"
        )

        keyboard = raffle_member_keyboard()

    # ------------------------------------------------------
    # Post raffle.
    # ------------------------------------------------------

    try:

        posted = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=raffle_text,
            reply_markup=keyboard,
        )

    except TelegramError:

        logger.exception(
            "Could not post raffle to group."
        )

        return

    # ------------------------------------------------------
    # Save group post metadata.
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

    entry_price = raffle_info.get(
        "entry_price",
        0,
    )

    # ------------------------------------------------------
    # FREE RAFFLE
    # ------------------------------------------------------

    if float(entry_price or 0) <= 0:

        await query.answer(
            "Free entry!"
        )

        await create_free_entry(
            update,
            context,
            raffle_info,
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

    if not user:
        return

    raffle_id = raffle_info.get(
        "id"
    )

    # ------------------------------------------------------
    # Try current database function.
    # ------------------------------------------------------

    entry_id = None

    create_entry = getattr(
        db,
        "create_raffle_entry",
        None,
    )

    if callable(create_entry):

        try:

            entry_id = create_entry(
                raffle_id=raffle_id,
                user_id=user.id,
                username=user.username,
                display_name=user.full_name,
                payment_method="free",
                status="approved",
            )

        except TypeError:

            try:

                entry_id = create_entry(
                    raffle_id,
                    user.id,
                    user.username,
                    user.full_name,
                    "free",
                    "approved",
                )

            except Exception:

                logger.exception(
                    "Could not create free entry."
                )

        except Exception:

            logger.exception(
                "Could not create free entry."
            )

    # ------------------------------------------------------
    # Older database.
    # ------------------------------------------------------

    if entry_id is None:

        try:

            entry_id = db_call(
                "add_raffle_entry",
                raffle_id,
                user.id,
                user.username,
                "free",
            )

        except Exception:

            logger.exception(
                "Legacy free entry failed."
            )

    if entry_id is None:

        await query.message.reply_text(
            "⚠️ I could not add your raffle entry.\n\n"
            "Please try again or contact an admin."
        )

        return

    await query.message.reply_text(
        "🎉 YOU'RE ENTERED!\n\n"
        "Your FREE raffle entry has been added.\n\n"
        "👑 Good luck!"
    )

    # ------------------------------------------------------
    # Notify admins.
    # ------------------------------------------------------

    admin_text = (
        "🎟️ FREE RAFFLE ENTRY\n\n"
        f"👤 User: {user.full_name}\n"
        f"🆔 User ID: {user.id}\n"
        "💵 Entry: FREE\n"
        f"🎟️ Entry ID: {entry_id}\n\n"
        "The entry was automatically approved."
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
            )

        except TelegramError as exc:

            logger.warning(
                "Could not notify admin %s: %s",
                admin_id,
                exc,
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
        "entry_price",
        0,
    )

    # ------------------------------------------------------
    # Safety: free raffle does not need payment.
    # ------------------------------------------------------

    if float(entry_price or 0) <= 0:

        await query.answer(
            "This raffle is FREE!",
            show_alert=True,
        )

        await create_free_entry(
            update,
            context,
            raffle_info,
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

    entry_price = raffle_info.get(
        "entry_price",
        0,
    )

    # ------------------------------------------------------
    # Free raffle protection.
    # ------------------------------------------------------

    if float(entry_price or 0) <= 0:

        await query.answer(
            "This raffle is FREE!",
            show_alert=True,
        )

        await create_free_entry(
            update,
            context,
            raffle_info,
        )

        return

    # ------------------------------------------------------
    # Create pending entry.
    # ------------------------------------------------------

    entry_id = None

    create_entry = getattr(
        db,
        "create_raffle_entry",
        None,
    )

    if callable(create_entry):

        try:

            entry_id = create_entry(
                raffle_id=raffle_id,
                user_id=user.id,
                username=user.username,
                display_name=user.full_name,
                payment_method=payment_method,
                status="pending",
            )

        except TypeError:

            try:

                entry_id = create_entry(
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

        except Exception:

            logger.exception(
                "Could not create raffle entry."
            )

    # ------------------------------------------------------
    # Legacy database.
    # ------------------------------------------------------

    if entry_id is None:

        try:

            entry_id = db_call(
                "add_raffle_entry",
                raffle_id,
                user.id,
                user.username,
                payment_method,
            )

        except Exception:

            logger.exception(
                "Legacy add_raffle_entry failed."
            )

    if entry_id is None:

        await query.answer(
            "Could not create your entry.",
            show_alert=True,
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
        f"💵 Amount: {money(entry_price)}\n"
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

        entry = None

        try:

            entry = db_call(
                "approve_raffle_entry",
                entry_id,
            )

        except Exception:

            try:

                entry = db_call(
                    "approve_entry",
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

        # --------------------------------------------------
        # Notify member.
        # --------------------------------------------------

        member_id = None

        if isinstance(
            entry,
            dict,
        ):

            member_id = entry.get(
                "user_id"
            )

        elif isinstance(
            entry,
            (tuple, list),
        ):

            if len(entry) >= 3:
                member_id = entry[2]

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

            try:

                db_call(
                    "deny_entry",
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

    entry_price = raffle_info.get(
        "entry_price",
        0,
    )

    if float(entry_price or 0) <= 0:

        await message.reply_text(
            "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
            f"🎁 Prize: {raffle_info.get('prize')}\n"
            "💵 Entry: FREE\n\n"
            "Tap below to enter.",
            reply_markup=free_raffle_keyboard(),
        )

        return

    await message.reply_text(
        "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: {money(entry_price)}\n\n"
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

        if isinstance(
            entry,
            dict,
        ):

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

        try:

            entries = db_call(
                "get_approved_entries",
                raffle_info.get("id"),
            )

        except Exception:

            entries = []

    approved = 0

    for entry in entries or []:

        if isinstance(
            entry,
            dict,
        ):

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

            elif entry.get(
                "approved"
            ) in (
                1,
                True,
            ):

                approved += 1

    await message.reply_text(
        "🎟️ RAFFLE STATUS\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: "
        f"{money(raffle_info.get('entry_price', 0))}\n"
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
            entry.get("display_name")
            or entry.get("username")
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

        try:

            db_call(
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

        approved = entry.get(
            "approved"
        )

        if status in (
            "approved",
            "paid",
            "active",
        ) or approved in (
            1,
            True,
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
        winner.get("display_name")
        or winner.get("username")
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
        f"🎁 Prize: "
        f"{raffle_info.get('prize')}\n\n"
        "👑 Congratulations!"
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
        ) or entry.get(
            "approved"
        ) in (
            1,
            True,
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

    raffle_id = raffle_info.get(
        "id"
    )

    entry_id = None

    try:

        entry_id = db_call(
            "create_raffle_entry",
            raffle_id=raffle_id,
            user_id=target_user_id,
            username=None,
            display_name="Bonus Entry",
            payment_method="bonus",
            status="approved",
        )

    except Exception:

        try:

            entry_id = db_call(
                "add_raffle_entry",
                raffle_id,
                target_user_id,
                None,
                "bonus",
            )

        except Exception:

            logger.exception(
                "Could not create bonus entry."
            )

    if entry_id is None:

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

        try:

            db_call(
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
    # START RAFFLE BUTTON
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
            "Opening raffle setup..."
        )

        # Start the same setup flow used
        # by /startraffle.

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

        await query.message.reply_text(
            "🎟️ START RAFFLE\n\n"
            "Enter the raffle information:\n\n"
            "$100 Cash Prize | $5\n\n"
            "FREE raffle example:\n"
            "$100 Cash Prize | FREE\n\n"
            "Format:\n"
            "PRIZE | ENTRY PRICE"
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
    # ENTER RAFFLE
    # ------------------------------------------------------

    if data == "raffle_enter":

        await raffle_enter_button(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # PAYMENT METHOD
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

    # ------------------------------------------------------
    # Older database may not have expiration.
    # ------------------------------------------------------

    if not expires_at:

        return

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
        "entry_price",
        0,
    )

    if float(entry_price or 0) <= 0:

        text = (
            "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
            f"🎁 PRIZE: {prize}\n"
            "💵 ENTRY: FREE\n\n"
            "This raffle is FREE to enter!\n\n"
            "Tap ENTER FREE RAFFLE below.\n\n"
            f"⏱️ TIME REMAINING: {remaining}\n\n"
            "👑 Good luck everyone!"
        )

        keyboard = free_raffle_keyboard()

    else:

        text = (
            "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
            f"🎁 PRIZE: {prize}\n"
            f"💵 ENTRY: {money(entry_price)}\n\n"
            "Ready to join?\n"
            "Tap ENTER RAFFLE below.\n\n"
            "💳 Payment options are available "
            "after selecting your entry.\n\n"
            f"⏱️ TIME REMAINING: {remaining}\n\n"
            "👑 Good luck everyone!"
        )

        keyboard = raffle_member_keyboard()

    # ------------------------------------------------------
    # Update message.
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
    # Automatically expire raffle.
    # ------------------------------------------------------

    if remaining == "⏰ ENDED":

        try:

            db_call(
                "expire_raffle",
                raffle_id,
            )

        except Exception:

            try:

                db_call(
                    "close_raffle",
                    raffle_id,
                )

            except Exception:

                logger.warning(
                    "Could not mark raffle %s expired.",
                    raffle_id,
                    exc_info=True,
                )
