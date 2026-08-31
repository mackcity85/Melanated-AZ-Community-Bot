# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# COMPLETE RAFFLE SYSTEM
#
# Features:
# - Paid or FREE raffles
# - Admin approval before posting raffle
# - FREE entries automatically approved
# - PAID entries require admin payment approval
# - Admin approval/deny buttons for paid entries
# - Raffle-specific callback buttons
# - Old raffle buttons cannot enter a new raffle
# - ENTER RAFFLE button
# - Cash App / Zelle
# - Persistent SQLite database
# - Countdown
# - Automatic expiration
# - Draw / reroll
# - Bonus entries
# - Manual admin entries
# - Remove entries
# - Temporary messages deleted after 60 seconds
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
from telegram.error import TelegramError, BadRequest
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
# INTEGER HELPER
# ==========================================================

def safe_int(value):

    try:
        return int(value)

    except (TypeError, ValueError):

        return None


# ==========================================================
# TEMPORARY MESSAGE DELETE
# ==========================================================

async def delete_message_later(
    context,
    chat_id,
    message_id,
    delay_seconds=60,
):

    try:

        if not context.job_queue:

            logger.warning(
                "Job queue unavailable; "
                "temporary message will not be scheduled "
                "for deletion."
            )

            return

        context.job_queue.run_once(
            delete_scheduled_message,
            when=delay_seconds,
            data={
                "chat_id": chat_id,
                "message_id": message_id,
            },
            name=(
                f"raffle_delete_"
                f"{chat_id}_"
                f"{message_id}"
            ),
        )

    except Exception:

        logger.exception(
            "Could not schedule raffle message deletion."
        )


async def delete_scheduled_message(
    context,
):

    job = context.job

    if not job or not job.data:
        return

    chat_id = job.data.get(
        "chat_id"
    )

    message_id = job.data.get(
        "message_id"
    )

    if chat_id is None or message_id is None:
        return

    try:

        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

        logger.info(
            "Deleted temporary raffle message %s "
            "in chat %s",
            message_id,
            chat_id,
        )

    except BadRequest as exc:

        logger.debug(
            "Temporary raffle message could not "
            "be deleted: %s",
            exc,
        )

    except TelegramError:

        logger.warning(
            "Telegram error deleting temporary "
            "raffle message.",
            exc_info=True,
        )


async def send_temporary_message(
    context,
    chat_id,
    text,
    reply_markup=None,
    delay_seconds=60,
):

    message = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
    )

    await delete_message_later(
        context,
        chat_id,
        message.message_id,
        delay_seconds,
    )

    return message


# ==========================================================
# MONEY HELPERS
# ==========================================================

def money_value(value):

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    normalized = (
        value
        .replace("$", "")
        .replace(",", "")
        .strip()
        .lower()
    )

    if normalized in (
        "free",
        "no charge",
        "nocharge",
        "0",
        "0.0",
        "0.00",
    ):

        return 0.0

    try:

        return float(normalized)

    except ValueError:

        return None


def money(value):

    try:

        amount = float(value)

    except (TypeError, ValueError):

        return "FREE"

    if amount <= 0:

        return "FREE"

    if amount.is_integer():

        return f"${int(amount)}"

    return f"${amount:.2f}"


# ==========================================================
# COUNTDOWN
# ==========================================================

def format_countdown(
    expires_at,
):

    if not expires_at:
        return "Unknown"

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

    minutes, seconds = divmod(
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

    if minutes:

        return f"{minutes}m"

    return f"{seconds}s"


# ==========================================================
# CHECK EXPIRED RAFFLE
# ==========================================================

def raffle_is_expired(
    raffle_info,
):

    if not raffle_info:
        return True

    expires_at = raffle_info.get(
        "expires_at"
    )

    if not expires_at:
        return False

    try:

        expires = datetime.fromisoformat(
            str(expires_at).replace(
                "Z",
                "+00:00",
            )
        )

        if expires.tzinfo is None:

            expires = expires.replace(
                tzinfo=timezone.utc
            )

        return datetime.now(
            timezone.utc
        ) >= expires

    except Exception:

        logger.warning(
            "Could not parse raffle expiration: %s",
            expires_at,
        )

        return False


# ==========================================================
# CLOSE IF EXPIRED
# ==========================================================

def close_if_expired(
    raffle_info,
):

    if not raffle_info:
        return None

    if raffle_info.get(
        "status"
    ) != "active":

        return raffle_info

    if not raffle_is_expired(
        raffle_info
    ):

        return raffle_info

    raffle_id = raffle_info.get(
        "id"
    )

    if raffle_id:

        try:

            db.close_raffle(
                raffle_id
            )

            raffle_info = db.get_raffle(
                raffle_id
            )

        except Exception:

            logger.exception(
                "Could not close expired raffle %s",
                raffle_id,
            )

    return raffle_info


# ==========================================================
# RAFFLE EXPIRATION
# ==========================================================

def raffle_expiration():

    try:

        days = int(
            os.environ.get(
                "RAFFLE_DURATION_DAYS",
                RAFFLE_DURATION_DAYS,
            )
        )

    except (TypeError, ValueError):

        days = 7

    if days < 1:
        days = 1

    return (
        datetime.now(
            timezone.utc
        ).timestamp()
        + (
            days * 86400
        )
    )


def timestamp_to_iso(
    timestamp,
):

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).isoformat()


# ==========================================================
# DATABASE HELPERS
# ==========================================================

def find_active_raffle():

    try:

        raffle = db.get_active_raffle()

        if not raffle:
            return None

        raffle = close_if_expired(
            raffle
        )

        if not raffle:
            return None

        if raffle.get(
            "status"
        ) != "active":

            return None

        return raffle

    except Exception:

        logger.exception(
            "Could not retrieve active raffle."
        )

        return None


def get_active_raffle_by_id(
    raffle_id,
):

    raffle_id = safe_int(
        raffle_id
    )

    if raffle_id is None:
        return None

    try:

        raffle = db.get_raffle(
            raffle_id
        )

        if not raffle:
            return None

        raffle = close_if_expired(
            raffle
        )

        if not raffle:
            return None

        if raffle.get(
            "status"
        ) != "active":

            return None

        return raffle

    except Exception:

        logger.exception(
            "Could not retrieve raffle %s",
            raffle_id,
        )

        return None


# ==========================================================
# KEYBOARDS
#
# IMPORTANT:
# Callback data contains the raffle ID.
# ==========================================================

def raffle_member_keyboard(
    raffle_id,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER RAFFLE",
                    callback_data=(
                        f"raffle_enter:{raffle_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data=(
                        f"raffle_cashapp:{raffle_id}"
                    ),
                ),
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data=(
                        f"raffle_zelle:{raffle_id}"
                    ),
                ),
            ],
        ]
    )


def free_raffle_keyboard(
    raffle_id,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER FREE RAFFLE",
                    callback_data=(
                        f"raffle_enter:{raffle_id}"
                    ),
                )
            ]
        ]
    )


def payment_keyboard(
    raffle_id,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data=(
                        f"raffle_cashapp:{raffle_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 PAY WITH ZELLE",
                    callback_data=(
                        f"raffle_zelle:{raffle_id}"
                    ),
                )
            ],
        ]
    )


def paid_keyboard(
    raffle_id,
    payment_method,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ I PAID",
                    callback_data=(
                        f"raffle_paid:"
                        f"{payment_method}:"
                        f"{raffle_id}"
                    ),
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
                        f"raffle_payment_approve:"
                        f"{entry_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ DENY ENTRY",
                    callback_data=(
                        f"raffle_payment_deny:"
                        f"{entry_id}"
                    ),
                ),
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

    if not is_admin(
        user.id
    ):

        await message.reply_text(
            "🚫 You are not authorized "
            "to start a raffle."
        )

        return

    # ======================================================
    # CHECK FOR EXISTING ACTIVE RAFFLE
    # ======================================================

    active = find_active_raffle()

    if active:

        await message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {active.get('prize')}\n"
            f"💵 Entry: {active.get('price')}\n"
            f"⏱️ Time Remaining: "
            f"{format_countdown(active.get('expires_at'))}"
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
        "OR\n\n"
        "$100 Cash Prize | FREE\n\n"
        "Examples:\n"
        "$250 Cash Prize | $10\n"
        "$100 Cash Prize | FREE\n\n"
        "Format:\n"
        "PRIZE | ENTRY PRICE"
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

    if not is_admin(
        user.id
    ):

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

    if (
        entry_price is None
        or entry_price < 0
    ):

        await message.reply_text(
            "⚠️ Invalid entry price.\n\n"
            "Use:\n"
            "$5\n\n"
            "or:\n"
            "FREE"
        )

        return True

    # ======================================================
    # CHECK AGAIN BEFORE CREATING
    # ======================================================

    active = find_active_raffle()

    if active:

        context.user_data.pop(
            "awaiting_raffle_setup",
            None,
        )

        await message.reply_text(
            "⚠️ Another raffle is already active.\n\n"
            "I did not create a second raffle."
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

    expires_timestamp = raffle_expiration()

    expires_at = timestamp_to_iso(
        expires_timestamp
    )

    try:

        raffle_id = db.create_raffle(
            prize,
            money(entry_price),
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
# PRIVATE START
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
    user = update.effective_user

    if not query:
        return

    if not user or not is_admin(
        user.id
    ):

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

    raffle_id = safe_int(
        raffle_id_text
    )

    if raffle_id is None:

        await query.answer(
            "Invalid raffle.",
            show_alert=True,
        )

        return

    raffle_info = None

    try:

        raffle_info = db.get_raffle(
            raffle_id
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

    # ======================================================
    # CANCEL
    # ======================================================

    if action == "raffle_cancel":

        try:

            changed = db.cancel_pending_raffle(
                raffle_id
            )

            if not changed:

                await query.answer(
                    "Raffle was already processed.",
                    show_alert=True,
                )

                return

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

    # ======================================================
    # APPROVE
    # ======================================================

    if action != "raffle_approve":

        await query.answer()
        return

    if raffle_info.get(
        "status"
    ) != "pending":

        await query.answer(
            "Raffle was already processed.",
            show_alert=True,
        )

        return

    # ======================================================
    # DO NOT APPROVE AN ALREADY EXPIRED PENDING RAFFLE
    # ======================================================

    if raffle_is_expired(
        raffle_info
    ):

        try:

            db.cancel_pending_raffle(
                raffle_id
            )

        except Exception:

            logger.exception(
                "Could not cancel expired "
                "pending raffle %s",
                raffle_id,
            )

        await query.answer(
            "This raffle has expired.",
            show_alert=True,
        )

        return

    try:

        changed = db.approve_raffle(
            raffle_id
        )

        if not changed:

            await query.answer(
                "Raffle was already processed.",
                show_alert=True,
            )

            return

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

    prize = raffle_info.get(
        "prize",
        "Raffle Prize",
    )

    entry_price = money_value(
        raffle_info.get("price")
    )

    if entry_price is None:
        entry_price = 0.0

    expires_at = raffle_info.get(
        "expires_at"
    )

    # ======================================================
    # KEYBOARD
    # ======================================================

    if entry_price <= 0:

        keyboard = free_raffle_keyboard(
            raffle_id
        )

    else:

        keyboard = raffle_member_keyboard(
            raffle_id
        )

    raffle_text = (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
        f"🎁 PRIZE: {prize}\n"
        f"💵 ENTRY: {money(entry_price)}\n\n"
        "Ready to join?\n"
        "Tap the button below.\n\n"
    )

    if entry_price <= 0:

        raffle_text += (
            "🎉 This raffle is FREE to enter!\n\n"
        )

    else:

        raffle_text += (
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
            reply_markup=keyboard,
        )

    except TelegramError:

        logger.exception(
            "Could not post raffle to group."
        )

        # ==================================================
        # IMPORTANT:
        # If Telegram posting fails, put the raffle back
        # into pending so it is not falsely represented as
        # successfully posted.
        #
        # We cannot safely call a "re-pending" helper with
        # the current DB contract, so log the condition.
        # ==================================================

        return

    # ======================================================
    # SAVE POST
    # ======================================================

    try:

        db.set_raffle_post(
            raffle_id,
            posted.chat_id,
            posted.message_id,
        )

    except Exception:

        logger.exception(
            "Could not save raffle post metadata."
        )

    # ======================================================
    # START COUNTDOWN
    # ======================================================

    try:

        if context.job_queue:

            context.job_queue.run_repeating(
                update_raffle_countdown,
                interval=60,
                first=60,
                data={
                    "raffle_id": raffle_id,
                },
                name=(
                    f"raffle_countdown_"
                    f"{raffle_id}"
                ),
            )

    except Exception:

        logger.exception(
            "Could not start raffle countdown."
        )


# ==========================================================
# ENTER RAFFLE BUTTON
# ==========================================================

async def raffle_enter_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    raffle_id=None,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    # ======================================================
    # GET EXACT RAFFLE
    #
    # This is the important fix.
    # ======================================================

    if raffle_id is not None:

        raffle_info = get_active_raffle_by_id(
            raffle_id
        )

    else:

        # Backward compatibility for old buttons.
        raffle_info = find_active_raffle()

    if not raffle_info:

        await query.answer(
            "This raffle is no longer active.",
            show_alert=True,
        )

        return

    raffle_id = raffle_info.get(
        "id"
    )

    entry_price = money_value(
        raffle_info.get("price")
    )

    if entry_price is None:
        entry_price = 0.0

    # ======================================================
    # FREE RAFFLE
    #
    # FREE entries are automatically approved.
    # ======================================================

    if entry_price <= 0:

        # ==================================================
        # CHECK EXISTING ENTRY FIRST
        # ==================================================

        existing = db.get_user_entry(
            raffle_id,
            user.id,
        )

        if existing:

            await query.answer(
                "You are already entered "
                "in this raffle.",
                show_alert=True,
            )

            return

        try:

            entry_id = db.add_raffle_entry(
                raffle_id=raffle_id,
                user_id=user.id,
                username=user.username,
                display_name=user.full_name,
                payment_method="free",
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

        if entry_id is None:

            await query.answer(
                "You are already entered "
                "in this raffle.",
                show_alert=True,
            )

            return

        # ==================================================
        # AUTOMATICALLY APPROVE
        # ==================================================

        try:

            approved = db.approve_entry(
                entry_id,
                user.id,
            )

            if not approved:

                logger.warning(
                    "Free entry %s was created but "
                    "could not be automatically approved.",
                    entry_id,
                )

                await query.answer(
                    "Entry created but approval failed. "
                    "Please contact an admin.",
                    show_alert=True,
                )

                return

        except Exception:

            logger.exception(
                "Could not automatically approve "
                "free raffle entry %s.",
                entry_id,
            )

            await query.answer(
                "Entry created but approval failed. "
                "Please contact an admin.",
                show_alert=True,
            )

            return

        await query.answer(
            "You're entered!"
        )

        await send_temporary_message(
            context,
            query.message.chat_id,
            (
                "🎉 YOU'RE ENTERED!\n\n"
                "Your FREE raffle entry has been "
                "automatically approved.\n\n"
                "👑 Good luck!"
            ),
            delay_seconds=60,
        )

        logger.info(
            "FREE raffle entry automatically approved: "
            "entry_id=%s user_id=%s raffle_id=%s",
            entry_id,
            user.id,
            raffle_id,
        )

        return

    # ======================================================
    # PAID RAFFLE
    # ======================================================

    # Check if already pending/approved.
    existing = db.get_user_entry(
        raffle_id,
        user.id,
    )

    if existing:

        status = existing.get(
            "status",
            "pending",
        )

        if status == "approved":

            await query.answer(
                "You are already entered "
                "in this raffle.",
                show_alert=True,
            )

        else:

            await query.answer(
                "You already have a pending "
                "entry for this raffle.",
                show_alert=True,
            )

        return

    await query.answer(
        "Raffle entry started."
    )

    await send_temporary_message(
        context,
        query.message.chat_id,
        (
            "🎟️ RAFFLE ENTRY\n\n"
            f"Entry price: {money(entry_price)}\n\n"
            "Choose how you would like to pay:"
        ),
        reply_markup=payment_keyboard(
            raffle_id
        ),
        delay_seconds=60,
    )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    raffle_id=None,
    payment_type=None,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    data = query.data or ""

    # ======================================================
    # GET RAFFLE
    # ======================================================

    if raffle_id is not None:

        raffle_info = get_active_raffle_by_id(
            raffle_id
        )

    else:

        raffle_info = find_active_raffle()

    if not raffle_info:

        await query.answer(
            "This raffle is no longer active.",
            show_alert=True,
        )

        return

    raffle_id = raffle_info.get(
        "id"
    )

    entry_price = money_value(
        raffle_info.get("price")
    )

    if entry_price is None:
        entry_price = 0.0

    if entry_price <= 0:

        await query.answer(
            "This raffle is FREE.",
            show_alert=True,
        )

        return

    # ======================================================
    # CHECK DUPLICATE
    # ======================================================

    existing = db.get_user_entry(
        raffle_id,
        user.id,
    )

    if existing:

        await query.answer(
            "You already have an entry "
            "for this raffle.",
            show_alert=True,
        )

        return

    # ======================================================
    # DETERMINE PAYMENT METHOD
    # ======================================================

    if payment_type:

        payment_method = payment_type.lower()

    elif "cashapp" in data:

        payment_method = "cashapp"

    elif "zelle" in data:

        payment_method = "zelle"

    else:

        await query.answer()
        return

    # ======================================================
    # CASH APP
    # ======================================================

    if payment_method == "cashapp":

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
                        f"raffle_paid:"
                        f"cashapp:"
                        f"{raffle_id}"
                    ),
                )
            ]
        )

        await query.answer()

        await send_temporary_message(
            context,
            query.message.chat_id,
            (
                "💵 CASH APP PAYMENT\n\n"
                f"Send {money(entry_price)} to:\n"
                f"{cashapp}\n\n"
                "After sending your payment, "
                "tap I PAID below.\n\n"
                "Your entry will remain pending "
                "until an admin verifies payment."
            ),
            reply_markup=InlineKeyboardMarkup(
                buttons
            ),
            delay_seconds=60,
        )

        return

    # ======================================================
    # ZELLE
    # ======================================================

    if payment_method == "zelle":

        zelle = (
            ZELLE_PHONE
            or "Zelle information not configured"
        )

        await query.answer()

        await send_temporary_message(
            context,
            query.message.chat_id,
            (
                "💳 ZELLE PAYMENT\n\n"
                f"Send {money(entry_price)} to:\n"
                f"{zelle}\n\n"
                "After sending your payment, "
                "tap I PAID below.\n\n"
                "Your entry will remain pending "
                "until an admin verifies payment."
            ),
            reply_markup=paid_keyboard(
                raffle_id,
                "zelle",
            ),
            delay_seconds=60,
        )

        return

    await query.answer()


# ==========================================================
# PAID ENTRY
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payment_method=None,
    raffle_id=None,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    data = query.data or ""

    if payment_method is None:

        parts = data.split(":")

        if len(parts) >= 2:

            payment_method = parts[1]

        else:

            await query.answer()
            return

    if raffle_id is None:

        parts = data.split(":")

        if len(parts) >= 3:

            raffle_id = safe_int(
                parts[2]
            )

    # ======================================================
    # GET EXACT RAFFLE
    # ======================================================

    if raffle_id is not None:

        raffle_info = get_active_raffle_by_id(
            raffle_id
        )

    else:

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

    entry_price = money_value(
        raffle_info.get("price")
    )

    if entry_price is None:
        entry_price = 0.0

    if entry_price <= 0:

        await query.answer(
            "This raffle is FREE.",
            show_alert=True,
        )

        return

    # ======================================================
    # CHECK EXISTING ENTRY
    # ======================================================

    existing = db.get_user_entry(
        raffle_id,
        user.id,
    )

    if existing:

        status = existing.get(
            "status"
        )

        if status == "approved":

            await query.answer(
                "You are already entered.",
                show_alert=True,
            )

        else:

            await query.answer(
                "You already have a pending "
                "payment for this raffle.",
                show_alert=True,
            )

        return

    # ======================================================
    # CREATE PAID ENTRY
    # ======================================================

    try:

        entry_id = db.add_raffle_entry(
            raffle_id=raffle_id,
            user_id=user.id,
            username=user.username,
            display_name=user.full_name,
            payment_method=payment_method,
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

    if entry_id is None:

        await query.answer(
            "You already have an entry "
            "for this raffle.",
            show_alert=True,
        )

        return

    # ======================================================
    # PAID ENTRIES STAY PENDING
    # ======================================================

    await query.answer(
        "Payment submitted."
    )

    await send_temporary_message(
        context,
        query.message.chat_id,
        (
            "✅ PAYMENT SUBMITTED\n\n"
            "Your raffle entry is pending admin "
            "payment verification.\n\n"
            "You will be notified once your payment "
            "is approved."
        ),
        delay_seconds=60,
    )

    # ======================================================
    # ADMIN NOTIFICATION
    # ======================================================

    admin_text = (
        "💰 RAFFLE PAYMENT PENDING\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Amount: {money(entry_price)}\n"
        f"👤 User: {user.full_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"💳 Method: {payment_method.upper()}\n"
        f"🎟️ Entry ID: {entry_id}\n"
        f"🎟️ Raffle ID: {raffle_id}\n\n"
        "⚠️ VERIFY THE PAYMENT BEFORE APPROVING."
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

            logger.info(
                "Sent paid-entry approval request "
                "to admin %s for entry %s",
                admin_id,
                entry_id,
            )

        except TelegramError as exc:

            logger.warning(
                "Could not notify admin %s about "
                "entry %s: %s",
                admin_id,
                entry_id,
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
    user = update.effective_user

    if not query:
        return

    if not user or not is_admin(
        user.id
    ):

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

    entry_id = safe_int(
        entry_id_text
    )

    if entry_id is None:

        await query.answer(
            "Invalid entry.",
            show_alert=True,
        )

        return

    try:

        entry = db.get_entry(
            entry_id
        )

    except Exception:

        logger.exception(
            "Could not retrieve entry %s",
            entry_id,
        )

        await query.answer(
            "Could not retrieve entry.",
            show_alert=True,
        )

        return

    if not entry:

        await query.answer(
            "Entry no longer exists.",
            show_alert=True,
        )

        return

    # ======================================================
    # APPROVE
    # ======================================================

    if action == "raffle_payment_approve":

        if entry.get(
            "status"
        ) != "pending":

            await query.answer(
                "Entry was already processed.",
                show_alert=True,
            )

            return

        # Make sure the raffle still exists.
        raffle_info = db.get_raffle(
            entry.get("raffle_id")
        )

        if not raffle_info:

            await query.answer(
                "Raffle no longer exists.",
                show_alert=True,
            )

            return

        try:

            changed = db.approve_entry(
                entry_id,
                user.id,
            )

            if not changed:

                await query.answer(
                    "Entry was already processed.",
                    show_alert=True,
                )

                return

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
                "✅ RAFFLE ENTRY APPROVED\n\n"
                f"Entry ID: {entry_id}\n"
                f"Raffle ID: "
                f"{entry.get('raffle_id')}\n"
                f"User: "
                f"{entry.get('display_name', 'Unknown')}"
            )

        except TelegramError:
            pass

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

                logger.warning(
                    "Could not notify member %s "
                    "about approved entry %s.",
                    member_id,
                    entry_id,
                )

        return

    # ======================================================
    # DENY
    # ======================================================

    if action == "raffle_payment_deny":

        if entry.get(
            "status"
        ) != "pending":

            await query.answer(
                "Entry was already processed.",
                show_alert=True,
            )

            return

        try:

            changed = db.deny_entry(
                entry_id,
                user.id,
            )

            if not changed:

                await query.answer(
                    "Entry was already processed.",
                    show_alert=True,
                )

                return

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

        await query.answer(
            "Entry denied."
        )

        try:

            await query.edit_message_text(
                "❌ RAFFLE ENTRY DENIED\n\n"
                f"Entry ID: {entry_id}\n"
                f"Raffle ID: "
                f"{entry.get('raffle_id')}\n"
                f"User: "
                f"{entry.get('display_name', 'Unknown')}"
            )

        except TelegramError:
            pass

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
                        "Your pending raffle entry has "
                        "been denied.\n\n"
                        "Please contact an admin if "
                        "you believe this was an error."
                    ),
                )

            except TelegramError:

                logger.warning(
                    "Could not notify member %s "
                    "about denied entry %s.",
                    member_id,
                    entry_id,
                )

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

    if not message:
        return

    raffle_info = find_active_raffle()

    if not raffle_info:

        await message.reply_text(
            "⚠️ There is currently no active raffle."
        )

        return

    raffle_id = raffle_info.get(
        "id"
    )

    entry_price = money_value(
        raffle_info.get("price")
    )

    if entry_price is None:
        entry_price = 0.0

    if entry_price <= 0:

        keyboard = free_raffle_keyboard(
            raffle_id
        )

    else:

        keyboard = raffle_member_keyboard(
            raffle_id
        )

    await message.reply_text(
        "🎟️ MELANATED AZ FRIENDS RAFFLE\n\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: {money(entry_price)}\n\n"
        "Choose an option below:",
        reply_markup=keyboard,
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

    if not is_admin(
        user.id
    ):

        await message.reply_text(
            "🚫 Admin access required."
        )

        return

    try:

        entries = db.get_pending_entries()

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

        lines.append(
            f"🎟️ Entry ID: {entry.get('id')}"
        )

        lines.append(
            f"🎟️ Raffle ID: "
            f"{entry.get('raffle_id')}"
        )

        lines.append(
            f"🎁 Prize: "
            f"{entry.get('prize', 'Unknown')}"
        )

        lines.append(
            f"👤 "
            f"{entry.get('display_name', 'Unknown')}"
        )

        lines.append(
            f"🆔 User ID: "
            f"{entry.get('user_id')}"
        )

        lines.append(
            f"💳 "
            f"{entry.get('payment_method', 'Unknown')}"
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

    if not message:
        return

    raffle_info = find_active_raffle()

    if not raffle_info:

        await message.reply_text(
            "⚠️ No active raffle."
        )

        return

    try:

        entries = db.get_approved_entries(
            raffle_info.get("id")
        )

    except Exception:

        logger.exception(
            "Could not retrieve approved entries."
        )

        entries = []

    approved = len(
        entries or []
    )

    try:

        pending = db.get_pending_entries(
            raffle_info.get("id")
        )

    except Exception:

        pending = []

    entry_price = money_value(
        raffle_info.get("price")
    )

    if entry_price is None:
        entry_price = 0.0

    await message.reply_text(
        "🎟️ RAFFLE STATUS\n\n"
        f"🎟️ Raffle ID: "
        f"{raffle_info.get('id')}\n"
        f"🎁 Prize: {raffle_info.get('prize')}\n"
        f"💵 Entry: {money(entry_price)}\n"
        f"👥 Approved Entries: {approved}\n"
        f"⏳ Pending Entries: {len(pending)}\n"
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

    if not is_admin(
        user.id
    ):

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

        entries = db.get_approved_entries(
            raffle_info.get("id")
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
        f"🎁 Prize: "
        f"{raffle_info.get('prize')}",
        "",
    ]

    for number, entry in enumerate(
        entries,
        start=1,
    ):

        name = (
            entry.get("display_name")
            or entry.get("username")
            or "Unknown"
        )

        lines.append(
            f"{number}. {name}"
        )

        lines.append(
            f"   🆔 {entry.get('user_id')}"
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

    if not is_admin(
        user.id
    ):

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

        changed = db.close_raffle(
            raffle_id
        )

    except Exception:

        logger.exception(
            "Could not close raffle."
        )

        await message.reply_text(
            "⚠️ Could not cancel raffle."
        )

        return

    if not changed:

        await message.reply_text(
            "⚠️ Raffle was already closed."
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

    if not is_admin(
        user.id
    ):

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

        entries = db.get_approved_entries(
            raffle_id
        )

    except Exception:

        logger.exception(
            "Could not retrieve entries."
        )

        await message.reply_text(
            "⚠️ Could not retrieve entries."
        )

        return

    if not entries:

        await message.reply_text(
            "⚠️ There are no approved "
            "entries to draw from."
        )

        return

    winner = random.choice(
        entries
    )

    winner_name = (
        winner.get("display_name")
        or winner.get("username")
        or "Unknown"
    )

    await message.reply_text(
        "🎉🎉🎉 RAFFLE WINNER 🎉🎉🎉\n\n"
        f"🏆 {winner_name}\n\n"
        f"🎁 Prize: "
        f"{raffle_info.get('prize')}\n\n"
        "👑 Congratulations!"
    )

    winner_id = winner.get(
        "user_id"
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

    if not is_admin(
        user.id
    ):

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

        entries = db.get_approved_entries(
            raffle_info.get("id")
        )

    except Exception:

        logger.exception(
            "Could not retrieve entries."
        )

        await message.reply_text(
            "⚠️ Could not retrieve entries."
        )

        return

    if not entries:

        await message.reply_text(
            "⚠️ No eligible entries."
        )

        return

    winner = random.choice(
        entries
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
#
# Existing command preserved:
# /bonusentry USER_ID
# ==========================================================

async def bonus_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(
        user.id
    ):

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

    target_user_id = safe_int(
        context.args[0]
    )

    if target_user_id is None:

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

    try:

        entry_id = db.add_raffle_entry(
            raffle_id=raffle_id,
            user_id=target_user_id,
            username=None,
            display_name="Bonus Entry",
            payment_method="bonus",
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
            "⚠️ That user already has "
            "an entry."
        )

        return

    try:

        approved = db.approve_entry(
            entry_id,
            user.id,
        )

        if not approved:

            await message.reply_text(
                "⚠️ Bonus entry was created, "
                "but could not be approved."
            )

            return

    except Exception:

        logger.exception(
            "Could not approve bonus entry."
        )

        await message.reply_text(
            "⚠️ Bonus entry was created, "
            "but approval failed."
        )

        return

    await message.reply_text(
        "🎟️ Bonus entry added successfully.\n\n"
        f"👤 User ID: {target_user_id}\n"
        f"🎟️ Entry ID: {entry_id}"
    )


# ==========================================================
# MANUAL ADMIN ENTRY
#
# /addraffleentry USER_ID
#
# Optional:
# /addraffleentry USER_ID NAME
#
# This creates an automatically approved manual entry.
# ==========================================================

async def add_manual_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not is_admin(
        user.id
    ):

        await message.reply_text(
            "🚫 Admin access required."
        )

        return

    if not context.args:

        await message.reply_text(
            "Usage:\n"
            "/addraffleentry USER_ID\n\n"
            "Optional:\n"
            "/addraffleentry USER_ID NAME"
        )

        return

    target_user_id = safe_int(
        context.args[0]
    )

    if target_user_id is None:

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

    # ======================================================
    # OPTIONAL DISPLAY NAME
    # ======================================================

    if len(context.args) > 1:

        display_name = " ".join(
            context.args[1:]
        )

    else:

        display_name = (
            f"Manual Entry "
            f"{target_user_id}"
        )

    # ======================================================
    # TRY TELEGRAM USER INFORMATION
    # ======================================================

    username = None

    try:

        chat = await context.bot.get_chat(
            target_user_id
        )

        username = getattr(
            chat,
            "username",
            None,
        )

        telegram_name = (
            getattr(
                chat,
                "full_name",
                None,
            )
            or getattr(
                chat,
                "first_name",
                None,
            )
        )

        if (
            len(context.args) <= 1
            and telegram_name
        ):

            display_name = telegram_name

    except TelegramError:

        logger.info(
            "Could not retrieve Telegram profile "
            "for manually added user %s.",
            target_user_id,
        )

    # ======================================================
    # ADD ENTRY
    # ======================================================

    try:

        entry_id = db.add_raffle_entry(
            raffle_id=raffle_id,
            user_id=target_user_id,
            username=username,
            display_name=display_name,
            payment_method="manual",
        )

    except Exception:

        logger.exception(
            "Could not create manual raffle entry."
        )

        await message.reply_text(
            "⚠️ Could not add the manual entry."
        )

        return

    if entry_id is None:

        await message.reply_text(
            "⚠️ That user already has "
            "a pending or approved entry "
            "for this raffle."
        )

        return

    # ======================================================
    # AUTOMATICALLY APPROVE
    # ======================================================

    try:

        approved = db.approve_entry(
            entry_id,
            user.id,
        )

        if not approved:

            await message.reply_text(
                "⚠️ Entry was created, "
                "but could not be approved."
            )

            return

    except Exception:

        logger.exception(
            "Could not approve manual entry."
        )

        await message.reply_text(
            "⚠️ Entry was created, "
            "but approval failed."
        )

        return

    await message.reply_text(
        "✅ MANUAL RAFFLE ENTRY ADDED\n\n"
        f"👤 {display_name}\n"
        f"🆔 User ID: {target_user_id}\n"
        f"🎟️ Entry ID: {entry_id}\n"
        "🎟️ Status: APPROVED"
    )

    # ======================================================
    # OPTIONAL MEMBER NOTIFICATION
    # ======================================================

    try:

        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                "🎉 YOU HAVE BEEN ENTERED!\n\n"
                "An admin added you to the "
                "Melanated AZ Friends Raffle.\n\n"
                f"🎁 Prize: "
                f"{raffle_info.get('prize')}\n\n"
                "👑 Good luck!"
            ),
        )

    except TelegramError:

        logger.info(
            "Could not privately notify manually "
            "added user %s.",
            target_user_id,
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

    if not is_admin(
        user.id
    ):

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

    entry_id = safe_int(
        context.args[0]
    )

    if entry_id is None:

        await message.reply_text(
            "⚠️ Invalid entry ID."
        )

        return

    try:

        entry = db.get_entry(
            entry_id
        )

        if not entry:

            await message.reply_text(
                "⚠️ Entry not found."
            )

            return

        changed = db.remove_entry(
            entry_id
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
            "⚠️ Entry not found."
        )

        return

    await message.reply_text(
        "🗑️ Raffle entry removed.\n\n"
        f"🎟️ Entry ID: {entry_id}\n"
        f"👤 User: "
        f"{entry.get('display_name', 'Unknown')}"
    )


# ==========================================================
# RAFFLE CALLBACK ROUTER
#
# Handles:
#
# NEW:
# raffle_enter:123
# raffle_cashapp:123
# raffle_zelle:123
# raffle_paid:cashapp:123
# raffle_paid:zelle:123
#
# ADMIN:
# raffle_approve:123
# raffle_cancel:123
# raffle_payment_approve:456
# raffle_payment_deny:456
#
# OLD CALLBACKS:
# raffle_enter
# raffle_cashapp
# raffle_zelle
# raffle_paid:cashapp
# raffle_paid:zelle
#
# Old buttons are supported for backward compatibility,
# but newly posted raffles always use raffle-specific IDs.
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

    # ======================================================
    # RAFFLE APPROVAL
    # ======================================================

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

    # ======================================================
    # ADMIN PAYMENT APPROVAL
    # ======================================================

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

    # ======================================================
    # NEW ENTER CALLBACK
    # ======================================================

    if data.startswith(
        "raffle_enter:"
    ):

        raffle_id = safe_int(
            data.split(
                ":",
                1,
            )[1]
        )

        await raffle_enter_button(
            update,
            context,
            raffle_id=raffle_id,
        )

        return

    # ======================================================
    # OLD ENTER CALLBACK
    # ======================================================

    if data == "raffle_enter":

        await raffle_enter_button(
            update,
            context,
        )

        return

    # ======================================================
    # NEW CASH APP
    # ======================================================

    if data.startswith(
        "raffle_cashapp:"
    ):

        raffle_id = safe_int(
            data.split(
                ":",
                1,
            )[1]
        )

        await payment_button(
            update,
            context,
            raffle_id=raffle_id,
            payment_type="cashapp",
        )

        return

    # ======================================================
    # NEW ZELLE
    # ======================================================

    if data.startswith(
        "raffle_zelle:"
    ):

        raffle_id = safe_int(
            data.split(
                ":",
                1,
            )[1]
        )

        await payment_button(
            update,
            context,
            raffle_id=raffle_id,
            payment_type="zelle",
        )

        return

    # ======================================================
    # OLD CASH APP
    # ======================================================

    if data == "raffle_cashapp":

        await payment_button(
            update,
            context,
            payment_type="cashapp",
        )

        return

    # ======================================================
    # OLD ZELLE
    # ======================================================

    if data == "raffle_zelle":

        await payment_button(
            update,
            context,
            payment_type="zelle",
        )

        return

    # ======================================================
    # NEW I PAID
    # ======================================================

    if data.startswith(
        "raffle_paid:"
    ):

        parts = data.split(":")

        if len(parts) >= 3:

            payment_method = parts[1]

            raffle_id = safe_int(
                parts[2]
            )

            await paid_entry(
                update,
                context,
                payment_method=payment_method,
                raffle_id=raffle_id,
            )

            return

        # ==================================================
        # OLD:
        # raffle_paid:cashapp
        # raffle_paid:zelle
        # ==================================================

        if len(parts) == 2:

            await paid_entry(
                update,
                context,
                payment_method=parts[1],
            )

            return

    await query.answer()


# ==========================================================
# COUNTDOWN
# ==========================================================

async def update_raffle_countdown(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    raffle_id = None

    if job and job.data:

        raffle_id = job.data.get(
            "raffle_id"
        )

    if raffle_id is None:

        logger.warning(
            "Raffle countdown job has no raffle ID."
        )

        if job:
            job.schedule_removal()

        return

    try:

        raffle_info = db.get_raffle(
            raffle_id
        )

    except Exception:

        logger.exception(
            "Could not retrieve raffle "
            "for countdown."
        )

        return

    if not raffle_info:

        if job:
            job.schedule_removal()

        return

    if raffle_info.get(
        "status"
    ) != "active":

        if job:
            job.schedule_removal()

        return

    expires_at = raffle_info.get(
        "expires_at"
    )

    remaining = format_countdown(
        expires_at
    )

    chat_id = raffle_info.get(
        "chat_id"
    ) or RAFFLE_CHAT_ID

    message_id = raffle_info.get(
        "message_id"
    )

    if not message_id:

        logger.warning(
            "Raffle %s has no Telegram message ID.",
            raffle_id,
        )

        return

    prize = raffle_info.get(
        "prize"
    )

    entry_price = money_value(
        raffle_info.get("price")
    )

    if entry_price is None:
        entry_price = 0.0

    # ======================================================
    # EXPIRED
    # ======================================================

    if remaining == "⏰ ENDED":

        try:

            db.close_raffle(
                raffle_id
            )

        except Exception:

            logger.warning(
                "Could not close expired raffle.",
                exc_info=True,
            )

        expired_text = (
            "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
            f"🎁 PRIZE: {prize}\n"
            f"💵 ENTRY: {money(entry_price)}\n\n"
            "⏰ RAFFLE ENDED\n\n"
            "Entries are closed.\n\n"
            "👑 Thank you for participating!"
        )

        try:

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=expired_text,
            )

        except BadRequest as exc:

            logger.debug(
                "Could not edit expired raffle: %s",
                exc,
            )

        except TelegramError:

            logger.warning(
                "Telegram error updating expired "
                "raffle.",
                exc_info=True,
            )

        if job:

            job.schedule_removal()

        return

    # ======================================================
    # ACTIVE KEYBOARD
    # ======================================================

    if entry_price <= 0:

        keyboard = free_raffle_keyboard(
            raffle_id
        )

    else:

        keyboard = raffle_member_keyboard(
            raffle_id
        )

    text = (
        "🎟️ MELANATED AZ FRIENDS RAFFLE 🎟️\n\n"
        f"🎁 PRIZE: {prize}\n"
        f"💵 ENTRY: {money(entry_price)}\n\n"
        "Ready to join?\n"
        "Tap the button below.\n\n"
    )

    if entry_price <= 0:

        text += (
            "🎉 This raffle is FREE to enter!\n\n"
        )

    else:

        text += (
            "💳 Payment options are available "
            "after selecting your entry.\n\n"
        )

    text += (
        f"⏱️ TIME REMAINING: {remaining}\n\n"
        "👑 Good luck everyone!"
    )

    # ======================================================
    # UPDATE ACTIVE RAFFLE
    # ======================================================

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


# ==========================================================
# END raffle.py
# ==========================================================
