# ==========================================================
# Melanated AZ Bot - raffle.py
# COMPLETE DROP-IN RAFFLE SYSTEM
#
# Compatible with:
#   - Existing raffle_database.py
#   - Existing bot.py
#   - python-telegram-bot v21+
#
# IMPORTANT:
#   - DOES NOT reset the database.
#   - DOES NOT replace the database.
#   - raffle_callback() is the ONLY owner of raffle callbacks.
#   - Supports CURRENT, LEGACY, and OLD NO-ID callbacks.
#
# CURRENT CALLBACKS:
#   raffle_approve_
#   raffle_cancel_
#   enter_
#   pay_cashapp_
#   pay_zelle_
#   payment_
#   paid_
#   approve_
#   deny_
#   draw_
#   reroll_
#   bonus_
#   remove_
#
# LEGACY CALLBACKS:
#   raffle_enter_
#   raffle_pay_cashapp_
#   raffle_pay_zelle_
#
# OLD BUTTON CALLBACKS:
#   raffle_enter
#   raffle_pay_cashapp
#   raffle_pay_zelle
#
# OLD NO-ID BUTTONS ARE RESOLVED AGAINST THE CURRENT
# ACTIVE RAFFLE. THIS ALLOWS EXISTING RAFFLE POSTS TO
# CONTINUE WORKING WITHOUT CREATING A NEW RAFFLE.
#
# FEATURES:
#   - Raffle creation
#   - Raffle approval
#   - Raffle cancellation
#   - Public raffle entry
#   - FREE raffle auto-approval
#   - PAID raffle pending/admin approval
#   - Cash App / Zelle
#   - Pending entry approval
#   - Entry denial
#   - Manual admin entry
#   - Winner drawing
#   - Duplicate-entry protection
#   - Admins can enter normally
#   - Existing raffle buttons remain usable
# ==========================================================

import logging
import random

from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.constants import ParseMode
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

from raffle_database import (
    create_raffle,
    get_raffle,
    get_active_raffle,
    get_pending_raffle,
    approve_raffle,
    cancel_pending_raffle,
    set_raffle_post,
    close_raffle,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    get_raffle_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    get_member,
)


logger = logging.getLogger("melanated_az_raffle")


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_raffle_admin(user_id):
    """
    Return True when user_id is configured as an admin.
    """

    try:

        if user_id is None:
            return False

        admin_ids = {
            int(x)
            for x in ADMIN_IDS
        }

        return int(user_id) in admin_ids

    except Exception:

        return False


# ==========================================================
# FREE RAFFLE CHECK
# ==========================================================

def is_free_raffle(price):
    """
    Returns True when the raffle is a free-entry raffle.

    Accepted examples:

        Free
        FREE
        free
        0
        0.0
        0.00
        $0
        $0.00
    """

    if price is None:
        return True

    value = str(price).strip().lower()

    value = value.replace("$", "")
    value = value.replace(",", "")
    value = value.strip()

    if value in {
        "",
        "free",
        "0",
        "0.0",
        "0.00",
    }:
        return True

    try:

        return float(value) == 0

    except (TypeError, ValueError):

        return False


# ==========================================================
# DISPLAY USER
# ==========================================================

def display_user(entry):
    """
    Safely display an entry/member name.
    """

    if not entry:
        return "Unknown"

    name = (
        entry.get("display_name")
        or entry.get("username")
        or str(entry.get("user_id", "Unknown"))
    )

    username = str(
        entry.get("username") or ""
    ).lstrip("@")

    if (
        username
        and username.lower() != str(name).lower()
    ):
        return f"{name} (@{username})"

    return str(name)


# ==========================================================
# EXPIRATION FORMAT
# ==========================================================

def format_expiration(value):
    """
    Convert ISO expiration timestamp into readable text.
    """

    if not value:
        return "Unknown"

    try:

        return datetime.fromisoformat(
            str(value)
        ).strftime(
            "%b %d, %Y at %I:%M %p"
        )

    except Exception:

        return str(value)


# ==========================================================
# SAFE CALLBACK ANSWER
# ==========================================================

async def safe_answer(
    query,
    text=None,
    show_alert=False,
):
    """
    Safely answer a Telegram callback.
    """

    if not query:
        return

    try:

        if text is None:

            await query.answer()

        else:

            await query.answer(
                text,
                show_alert=show_alert,
            )

    except TelegramError:

        pass


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message
    query = update.callback_query

    if not user or not is_raffle_admin(user.id):

        if query:

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

        elif message:

            await message.reply_text(
                "⛔ Admins only."
            )

        return

    # ------------------------------------------------------
    # BUTTON / CALLBACK ENTRY
    # ------------------------------------------------------

    if query:

        await safe_answer(query)

        try:

            await query.message.reply_text(
                "🎟️ <b>Start a Raffle</b>\n\n"
                "Use:\n"
                "<code>/startraffle Prize | Entry Price</code>\n\n"
                "FREE raffle example:\n"
                "<code>/startraffle $100 Cash Prize | FREE</code>\n\n"
                "PAID raffle example:\n"
                "<code>/startraffle $100 Cash Prize | $5</code>",
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.exception(
                "Could not send start raffle instructions."
            )

        return

    # ------------------------------------------------------
    # COMMAND ENTRY
    # ------------------------------------------------------

    if not message:
        return

    text = message.text or ""

    parts = text.split(" ", 1)

    if len(parts) < 2:

        await message.reply_text(
            "Use:\n"
            "<code>/startraffle Prize | Entry Price</code>\n\n"
            "FREE:\n"
            "<code>/startraffle Prize | FREE</code>\n\n"
            "PAID:\n"
            "<code>/startraffle Prize | $5</code>",
            parse_mode=ParseMode.HTML,
        )

        return

    payload = parts[1].strip()

    if "|" not in payload:

        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Use:\n"
            "<code>/startraffle Prize | Entry Price</code>",
            parse_mode=ParseMode.HTML,
        )

        return

    prize, price = [
        x.strip()
        for x in payload.split("|", 1)
    ]

    if not prize or not price:

        await message.reply_text(
            "⚠️ Prize and entry price are required."
        )

        return

    # ------------------------------------------------------
    # PREVENT MULTIPLE RAFFLES
    # ------------------------------------------------------

    active = get_active_raffle()
    pending = get_pending_raffle()

    if active:

        await message.reply_text(
            f"⚠️ Active raffle already exists.\n"
            f"🎁 {active['prize']}\n"
            f"💵 {active['price']}"
        )

        return

    if pending:

        await message.reply_text(
            f"⚠️ Raffle already awaiting approval.\n"
            f"🎁 {pending['prize']}\n"
            f"💵 {pending['price']}"
        )

        return

    # ------------------------------------------------------
    # EXPIRATION
    # ------------------------------------------------------

    expires = (
        datetime.utcnow()
        + timedelta(
            days=int(
                RAFFLE_DURATION_DAYS or 7
            )
        )
    )

    # ------------------------------------------------------
    # CREATE DATABASE RECORD
    # ------------------------------------------------------

    raffle_id = create_raffle(
        prize,
        price,
        expires.isoformat(),
    )

    raffle_type = (
        "FREE ENTRY"
        if is_free_raffle(price)
        else "PAID ENTRY"
    )

    # ------------------------------------------------------
    # ADMIN APPROVAL BUTTON
    # ------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "✅ Approve Raffle",
                callback_data=(
                    f"raffle_approve_{raffle_id}"
                ),
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=(
                    f"raffle_cancel_{raffle_id}"
                ),
            ),
        ]]
    )

    approval_text = (
        "🎟️ <b>RAFFLE AWAITING APPROVAL</b>\n\n"
        f"🆔 Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{prize}</b>\n"
        f"💵 Entry: <b>{price}</b>\n"
        f"📋 Type: <b>{raffle_type}</b>\n"
        f"⏰ Ends: <b>"
        f"{format_expiration(expires.isoformat())}"
        f"</b>\n\n"
        "Choose an action:"
    )

    sent_to_admin = set()

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=approval_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

            sent_to_admin.add(int(admin_id))

        except TelegramError:

            logger.warning(
                "Could not notify admin %s.",
                admin_id,
            )

    # ------------------------------------------------------
    # FALLBACK TO CREATOR
    # ------------------------------------------------------

    if user.id not in sent_to_admin:

        try:

            await context.bot.send_message(
                chat_id=user.id,
                text=approval_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.warning(
                "Could not send raffle approval "
                "message to creator %s.",
                user.id,
            )

    # ------------------------------------------------------
    # PRIVATE CONFIRMATION
    # ------------------------------------------------------

    if message.chat.type == "private":

        await message.reply_text(
            f"✅ Raffle #{raffle_id} "
            "created and sent for admin approval."
        )


# ==========================================================
# PUBLISH RAFFLE
# ==========================================================

async def publish_raffle(
    raffle_id,
    context,
):
    """
    Publish an approved raffle to RAFFLE_CHAT_ID.
    """

    raffle = get_raffle(raffle_id)

    if not raffle:

        logger.error(
            "Cannot publish raffle %s: not found.",
            raffle_id,
        )

        return False

    if raffle["status"] != "active":

        logger.warning(
            "Cannot publish raffle %s: status=%s.",
            raffle_id,
            raffle["status"],
        )

        return False

    free = is_free_raffle(
        raffle["price"]
    )

    if free:

        entry_label = "🆓 <b>FREE ENTRY</b>"

        pending_notice = (
            "🎉 Your entry is automatically "
            "<b>APPROVED</b> because this is "
            "a free raffle."
        )

    else:

        entry_label = (
            f"💵 <b>Entry: {raffle['price']}</b>"
        )

        pending_notice = (
            "⚠️ Your entry remains <b>PENDING</b> "
            "until an admin verifies your payment."
        )

    # ------------------------------------------------------
    # NEW BUTTON FORMAT
    #
    # New raffles use the raffle ID.
    # Existing old raffle buttons are also supported
    # by raffle_callback().
    # ------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER RAFFLE",
                    callback_data=(
                        f"enter_{raffle_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data=(
                        f"pay_cashapp_{raffle_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🏦 PAY WITH ZELLE",
                    callback_data=(
                        f"pay_zelle_{raffle_id}"
                    ),
                )
            ],
        ]
    )

    text = (
        "🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b>\n\n"
        f"🎁 <b>Prize:</b> {raffle['prize']}\n"
        f"{entry_label}\n"
        f"⏰ <b>Ends:</b> "
        f"{format_expiration(raffle['expires_at'])}\n\n"
        "👇 <b>Tap ENTER RAFFLE below to enter.</b>\n\n"
        f"{pending_notice}"
    )

    try:

        sent = await context.bot.send_message(
            chat_id=int(RAFFLE_CHAT_ID),
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        set_raffle_post(
            raffle_id,
            RAFFLE_CHAT_ID,
            sent.message_id,
        )

        logger.info(
            "RAFFLE PUBLISHED | raffle=%s | "
            "chat=%s | message=%s",
            raffle_id,
            RAFFLE_CHAT_ID,
            sent.message_id,
        )

        return True

    except TelegramError:

        logger.exception(
            "Could not publish raffle %s.",
            raffle_id,
        )

        return False


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

async def approve_raffle_callback(
    update,
    context,
    raffle_id,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    if not is_raffle_admin(user.id):

        await safe_answer(
            query,
            "⛔ Admins only.",
            True,
        )

        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await safe_answer(
            query,
            "Raffle not found.",
            True,
        )

        return

    if raffle["status"] != "pending":

        await safe_answer(
            query,
            f"Raffle is already {raffle['status']}.",
            True,
        )

        return

    if not approve_raffle(raffle_id):

        await safe_answer(
            query,
            "Raffle could not be approved.",
            True,
        )

        return

    await safe_answer(
        query,
        "Raffle approved!"
    )

    try:

        await query.edit_message_text(
            f"✅ <b>RAFFLE APPROVED</b>\n\n"
            f"🎁 {raffle['prize']}\n"
            f"💵 {raffle['price']}\n\n"
            "Publishing...",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        pass

    published = await publish_raffle(
        raffle_id,
        context,
    )

    if published:

        try:

            await query.message.reply_text(
                "✅ Raffle is now live in "
                "the raffle group."
            )

        except TelegramError:

            pass

    else:

        logger.error(
            "Raffle %s approved but publication failed.",
            raffle_id,
        )

        try:

            await query.message.reply_text(
                "⚠️ Raffle was approved, but I could "
                "not publish it to the raffle group. "
                "Check RAFFLE_CHAT_ID and bot permissions."
            )

        except TelegramError:

            pass


# ==========================================================
# CANCEL PENDING RAFFLE
# ==========================================================

async def cancel_raffle_callback(
    update,
    context,
    raffle_id,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    if not is_raffle_admin(user.id):

        await safe_answer(
            query,
            "⛔ Admins only.",
            True,
        )

        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await safe_answer(
            query,
            "Raffle not found.",
            True,
        )

        return

    if raffle["status"] != "pending":

        await safe_answer(
            query,
            f"Raffle is already {raffle['status']}.",
            True,
        )

        return

    if not cancel_pending_raffle(raffle_id):

        await safe_answer(
            query,
            "Raffle could not be cancelled.",
            True,
        )

        return

    await safe_answer(
        query,
        "Raffle cancelled."
    )

    try:

        await query.edit_message_text(
            f"❌ <b>RAFFLE CANCELLED</b>\n\n"
            f"🎁 {raffle['prize']}\n"
            f"💵 {raffle['price']}",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        pass


# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(
    update,
    context,
    raffle_id,
):
    """
    Handles the ENTER RAFFLE button.

    NO ADMIN RESTRICTION.

    Regular members and admins can both enter.
    """

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    logger.info(
        "ENTER RAFFLE CALLBACK | raffle=%s | user=%s",
        raffle_id,
        user.id,
    )

    raffle = get_raffle(raffle_id)

    if not raffle:

        logger.warning(
            "ENTER FAILED: raffle %s not found.",
            raffle_id,
        )

        await safe_answer(
            query,
            "This raffle could not be found.",
            True,
        )

        return

    # ------------------------------------------------------
    # RAFFLE MUST BE ACTIVE
    # ------------------------------------------------------

    if raffle["status"] != "active":

        logger.warning(
            "ENTER FAILED: raffle=%s status=%s",
            raffle_id,
            raffle["status"],
        )

        await safe_answer(
            query,
            "This raffle is no longer active.",
            True,
        )

        return

    # ------------------------------------------------------
    # EXPIRATION CHECK
    # ------------------------------------------------------

    try:

        expires_at = datetime.fromisoformat(
            str(raffle["expires_at"])
        )

        if datetime.utcnow() >= expires_at:

            close_raffle(raffle_id)

            await safe_answer(
                query,
                "This raffle has expired.",
                True,
            )

            return

    except Exception:

        logger.warning(
            "Could not evaluate expiration "
            "for raffle %s.",
            raffle_id,
        )

    free = is_free_raffle(
        raffle["price"]
    )

    name = (
        user.full_name
        or user.username
        or str(user.id)
    )

    username = user.username

    # ------------------------------------------------------
    # ADD ENTRY
    # ------------------------------------------------------

    try:

        entry_id = add_raffle_entry(
            raffle_id,
            user.id,
            username,
            name,
            "free" if free else None,
        )

    except Exception:

        logger.exception(
            "Could not create raffle entry | "
            "raffle=%s | user=%s",
            raffle_id,
            user.id,
        )

        await safe_answer(
            query,
            "There was a problem creating your entry.",
            True,
        )

        return

    # ------------------------------------------------------
    # DUPLICATE
    # ------------------------------------------------------

    if entry_id is None:

        logger.info(
            "DUPLICATE ENTRY | raffle=%s | user=%s",
            raffle_id,
            user.id,
        )

        await safe_answer(
            query,
            "You already have an entry for this raffle.",
            True,
        )

        return

    logger.info(
        "RAFFLE ENTRY CREATED | entry=%s | "
        "raffle=%s | user=%s | free=%s",
        entry_id,
        raffle_id,
        user.id,
        free,
    )

    # ======================================================
    # FREE RAFFLE
    # ======================================================

    if free:

        try:

            changed = approve_entry(
                entry_id,
                user.id,
            )

        except Exception:

            logger.exception(
                "FREE ENTRY APPROVAL ERROR | "
                "entry=%s | raffle=%s | user=%s",
                entry_id,
                raffle_id,
                user.id,
            )

            changed = False

        if not changed:

            logger.error(
                "FREE RAFFLE AUTO-APPROVAL FAILED | "
                "entry=%s | raffle=%s | user=%s",
                entry_id,
                raffle_id,
                user.id,
            )

            await safe_answer(
                query,
                "Your entry was created but could "
                "not be approved. Please contact an admin.",
                True,
            )

            return

        logger.info(
            "FREE ENTRY AUTO-APPROVED | "
            "entry=%s | raffle=%s | user=%s",
            entry_id,
            raffle_id,
            user.id,
        )

        await safe_answer(
            query,
            "🎉 You're entered! Entry approved.",
            True,
        )

        try:

            await query.message.reply_text(
                "🎉 <b>YOU'RE IN!</b>\n\n"
                f"🎁 Prize: <b>{raffle['prize']}</b>\n"
                "🆓 Entry: <b>FREE</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "✅ Your entry has been "
                "<b>APPROVED</b> automatically.\n\n"
                "Good luck! 🍀",
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.exception(
                "Could not send free-entry confirmation "
                "for entry %s.",
                entry_id,
            )

        return

    # ======================================================
    # PAID RAFFLE
    # ======================================================

    await safe_answer(
        query,
        "Entry submitted for approval!",
        True,
    )

    try:

        await query.message.reply_text(
            "🎟️ <b>ENTRY SUBMITTED</b>\n\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry Price: <b>{raffle['price']}</b>\n"
            f"🆔 Entry: <code>{entry_id}</code>\n\n"
            "⏳ Your entry is <b>PENDING</b> "
            "until an admin verifies payment.",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.exception(
            "Could not send pending-entry confirmation "
            "for entry %s.",
            entry_id,
        )

    # ------------------------------------------------------
    # ADMIN APPROVAL BUTTONS
    # ------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "✅ APPROVE",
                callback_data=(
                    f"approve_{entry_id}"
                ),
            ),
            InlineKeyboardButton(
                "❌ DENY",
                callback_data=(
                    f"deny_{entry_id}"
                ),
            ),
        ]]
    )

    admin_text = (
        "🎟️ <b>NEW RAFFLE ENTRY</b>\n\n"
        f"🆔 Entry: <code>{entry_id}</code>\n"
        f"🎟️ Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n"
        f"💵 Price: <b>{raffle['price']}</b>\n"
        f"👤 Member: <b>{name}</b>\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        "💳 Payment: <b>Not selected</b>\n"
        "⏳ Status: <b>PENDING</b>\n\n"
        "Choose an action:"
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.warning(
                "Could not notify admin %s "
                "about entry %s.",
                admin_id,
                entry_id,
            )


# ==========================================================
# PAYMENT METHOD
# ==========================================================

async def payment_method(
    update,
    context,
    raffle_id,
    method,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    raffle = get_raffle(raffle_id)

    if not raffle or raffle["status"] != "active":

        await safe_answer(
            query,
            "Raffle is no longer active.",
            True,
        )

        return

    # ------------------------------------------------------
    # FREE RAFFLE
    # ------------------------------------------------------

    if is_free_raffle(
        raffle["price"]
    ):

        await safe_answer(
            query,
            "This is a FREE raffle. No payment is required.",
            True,
        )

        return

    # ------------------------------------------------------
    # USER MUST HAVE PENDING ENTRY
    # ------------------------------------------------------

    entries = get_raffle_entries(
        raffle_id
    )

    entry = next(
        (
            x
            for x in entries
            if (
                int(x["user_id"]) == int(user.id)
                and x["status"] == "pending"
            )
        ),
        None,
    )

    if not entry:

        await safe_answer(
            query,
            "Enter the raffle first.",
            True,
        )

        return

    # ------------------------------------------------------
    # CASH APP
    # ------------------------------------------------------

    if method == "cashapp":

        body = (
            "💵 <b>CASH APP</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{CASHAPP_TAG}</code>"
        )

        if CASHAPP_URL:

            body += (
                f"\n\n{CASHAPP_URL}"
            )

    # ------------------------------------------------------
    # ZELLE
    # ------------------------------------------------------

    else:

        body = (
            "🏦 <b>ZELLE</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{ZELLE_PHONE}</code>"
        )

    await safe_answer(query)

    try:

        await query.message.reply_text(
            body
            + "\n\nAfter payment, your entry remains "
            "pending until an admin verifies it.",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.exception(
            "Could not send payment instructions."
        )


# ==========================================================
# APPROVE ENTRY
# ==========================================================

async def approve_entry_callback(
    update,
    context,
    entry_id,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    if not is_raffle_admin(user.id):

        await safe_answer(
            query,
            "⛔ Admins only.",
            True,
        )

        return

    entry = get_entry(entry_id)

    if not entry:

        await safe_answer(
            query,
            "Entry not found.",
            True,
        )

        return

    if entry["status"] != "pending":

        await safe_answer(
            query,
            f"Entry is already {entry['status']}.",
            True,
        )

        return

    raffle_id = entry.get("raffle_id")

    if not raffle_id:

        await safe_answer(
            query,
            "Entry has no raffle associated with it.",
            True,
        )

        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await safe_answer(
            query,
            "The raffle associated with this entry "
            "could not be found.",
            True,
        )

        return

    try:

        changed = approve_entry(
            entry_id,
            user.id,
        )

    except Exception:

        logger.exception(
            "Entry approval database error | entry=%s",
            entry_id,
        )

        changed = False

    if not changed:

        await safe_answer(
            query,
            "Entry could not be approved. "
            "It may already have been processed.",
            True,
        )

        return

    logger.info(
        "ENTRY APPROVED | entry=%s | raffle=%s | admin=%s",
        entry_id,
        raffle_id,
        user.id,
    )

    await safe_answer(
        query,
        "✅ Entry approved!"
    )

    try:

        await query.edit_message_text(
            "✅ <b>ENTRY APPROVED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{raffle_id}</code>\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"👤 Member: <b>{display_user(entry)}</b>\n"
            f"💳 Payment: <b>"
            f"{entry.get('payment_method') or 'Verified'}"
            f"</b>\n\n"
            f"Approved by admin "
            f"<code>{user.id}</code>.",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.exception(
            "Could not update approval message "
            "for entry %s.",
            entry_id,
        )

    # ------------------------------------------------------
    # NOTIFY MEMBER
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=int(entry["user_id"]),
            text=(
                "🎉 <b>YOUR RAFFLE ENTRY "
                "WAS APPROVED!</b>\n\n"
                f"🎁 Prize: <b>{raffle['prize']}</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "Good luck! 🍀"
            ),
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.info(
            "Could not notify entrant %s.",
            entry["user_id"],
        )


# ==========================================================
# DENY ENTRY
# ==========================================================

async def deny_entry_callback(
    update,
    context,
    entry_id,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    if not is_raffle_admin(user.id):

        await safe_answer(
            query,
            "⛔ Admins only.",
            True,
        )

        return

    entry = get_entry(entry_id)

    if not entry:

        await safe_answer(
            query,
            "Entry not found.",
            True,
        )

        return

    if entry["status"] != "pending":

        await safe_answer(
            query,
            f"Entry is already {entry['status']}.",
            True,
        )

        return

    try:

        changed = deny_entry(
            entry_id,
            user.id,
        )

    except Exception:

        logger.exception(
            "Entry denial database error | entry=%s",
            entry_id,
        )

        changed = False

    if not changed:

        await safe_answer(
            query,
            "Entry could not be denied.",
            True,
        )

        return

    logger.info(
        "ENTRY DENIED | entry=%s | raffle=%s | admin=%s",
        entry_id,
        entry["raffle_id"],
        user.id,
    )

    await safe_answer(
        query,
        "Entry denied."
    )

    try:

        await query.edit_message_text(
            f"❌ <b>ENTRY DENIED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"👤 Member: <b>{display_user(entry)}</b>\n\n"
            f"Denied by admin "
            f"<code>{user.id}</code>.",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        pass

    # ------------------------------------------------------
    # NOTIFY MEMBER
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=int(entry["user_id"]),
            text=(
                "❌ <b>YOUR RAFFLE ENTRY "
                "WAS NOT APPROVED</b>\n\n"
                f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "Please contact an admin if you believe "
                "this was a mistake."
            ),
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.info(
            "Could not notify denied entrant %s.",
            entry["user_id"],
        )


# ==========================================================
# MANUAL RAFFLE ENTRY
# ==========================================================

async def manual_raffle_entry(
    update,
    context,
    member_user_id,
):
    """
    Add a member manually as an approved raffle entry.

    Intended to be called by the admin panel.
    """

    query = update.callback_query
    admin_user = update.effective_user

    if not query or not admin_user:
        return False

    if not is_raffle_admin(admin_user.id):

        await safe_answer(
            query,
            "⛔ Admins only.",
            True,
        )

        return False

    raffle = get_active_raffle()

    if not raffle:

        await safe_answer(
            query,
            "There is no active raffle.",
            True,
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>NO ACTIVE RAFFLE</b>\n\n"
                "There is currently no active raffle "
                "to add a manual entry to.\n\n"
                "Start and approve a raffle first.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin_back",
                        )
                    ]]
                ),
            )

        except TelegramError:

            pass

        return False

    # ------------------------------------------------------
    # FIND MEMBER
    # ------------------------------------------------------

    member = get_member(
        member_user_id,
        int(RAFFLE_CHAT_ID),
    )

    if not member:

        members = context.user_data.get(
            "admin_manual_raffle_members",
            [],
        )

        for item in members:

            try:

                if (
                    int(item.get("user_id", 0))
                    == int(member_user_id)
                ):

                    member = item
                    break

            except (
                TypeError,
                ValueError,
            ):

                continue

    if not member:

        await safe_answer(
            query,
            "Member could not be found.",
            True,
        )

        return False

    username = member.get("username")

    display_name = (
        member.get("display_name")
        or (
            f"@{username}"
            if username
            else None
        )
        or str(member_user_id)
    )

    # ------------------------------------------------------
    # DUPLICATE CHECK
    # ------------------------------------------------------

    existing_entries = get_raffle_entries(
        raffle["id"]
    )

    for existing in existing_entries:

        try:

            if (
                int(existing["user_id"])
                == int(member_user_id)
            ):

                await safe_answer(
                    query,
                    "This member already has an entry "
                    "in this raffle.",
                    True,
                )

                try:

                    await query.edit_message_text(
                        "⚠️ <b>ENTRY ALREADY EXISTS</b>\n\n"
                        f"👤 Member: <b>{display_name}</b>\n"
                        f"🆔 User ID: "
                        f"<code>{member_user_id}</code>\n\n"
                        "This member already has an entry "
                        "in the active raffle.",
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(
                            [[
                                InlineKeyboardButton(
                                    "⬅️ Back",
                                    callback_data="admin_back",
                                )
                            ]]
                        ),
                    )

                except TelegramError:

                    pass

                return False

        except (
            TypeError,
            ValueError,
        ):

            continue

    # ------------------------------------------------------
    # CREATE MANUAL ENTRY
    # ------------------------------------------------------

    try:

        entry_id = add_raffle_entry(
            raffle["id"],
            int(member_user_id),
            username,
            display_name,
            "manual",
        )

    except Exception:

        logger.exception(
            "Could not create manual raffle entry."
        )

        entry_id = None

    if entry_id is None:

        await safe_answer(
            query,
            "The entry could not be created.",
            True,
        )

        return False

    # ------------------------------------------------------
    # APPROVE IMMEDIATELY
    # ------------------------------------------------------

    try:

        changed = approve_entry(
            entry_id,
            admin_user.id,
        )

    except Exception:

        logger.exception(
            "Manual entry approval failed | entry=%s",
            entry_id,
        )

        changed = False

    if not changed:

        logger.error(
            "Manual entry created but approval failed | "
            "entry=%s | member=%s | raffle=%s",
            entry_id,
            member_user_id,
            raffle["id"],
        )

        await safe_answer(
            query,
            "Entry was created but could not be approved.",
            True,
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>MANUAL ENTRY WARNING</b>\n\n"
                f"👤 Member: <b>{display_name}</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "The entry was created, but automatic "
                "approval failed.\n\n"
                "Check the raffle entries before trying again.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin_back",
                        )
                    ]]
                ),
            )

        except TelegramError:

            pass

        return False

    logger.info(
        "MANUAL RAFFLE ENTRY APPROVED | "
        "entry=%s | raffle=%s | member=%s | admin=%s",
        entry_id,
        raffle["id"],
        member_user_id,
        admin_user.id,
    )

    await safe_answer(
        query,
        "✅ Manual entry added!"
    )

    try:

        await query.edit_message_text(
            "✅ <b>MANUAL ENTRY ADDED</b>\n\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry Price: <b>{raffle['price']}</b>\n"
            f"👤 Member: <b>{display_name}</b>\n"
            f"🆔 User ID: "
            f"<code>{member_user_id}</code>\n"
            f"🎟️ Entry: <code>{entry_id}</code>\n"
            "💳 Payment: <b>Manual</b>\n"
            "✅ Status: <b>APPROVED</b>\n\n"
            f"Added by admin "
            f"<code>{admin_user.id}</code>.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➕ Add Another",
                            callback_data="admin_manual_entry",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin_back",
                        )
                    ],
                ]
            ),
        )

    except TelegramError:

        logger.exception(
            "Could not display manual entry result."
        )

    # ------------------------------------------------------
    # NOTIFY MEMBER
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=int(member_user_id),
            text=(
                "🎟️ <b>YOU HAVE BEEN ADDED "
                "TO THE RAFFLE</b>\n\n"
                f"🎁 Prize: <b>{raffle['prize']}</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "Your raffle entry has been "
                "<b>APPROVED</b> by an admin.\n\n"
                "Good luck! 🍀"
            ),
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.info(
            "Could not notify manually added member %s.",
            member_user_id,
        )

    return True


# ==========================================================
# RAFFLE CALLBACK ROUTER
# ==========================================================

async def raffle_callback(
    update,
    context,
):
    """
    SINGLE OWNER OF ALL RAFFLE CALLBACKS.

    Supports:

        raffle_enter
        raffle_enter_123
        enter_123

    and all other current/legacy raffle callbacks.

    IMPORTANT:

        NO ADMIN CHECK IS DONE HERE.

    Individual handlers perform their own permission checks.
    """

    query = update.callback_query

    if not query:
        return

    data = str(
        query.data or ""
    ).strip()

    logger.info(
        "=========================================================="
    )

    logger.info(
        "RAFFLE CALLBACK RECEIVED | data=%s | user=%s",
        data,
        getattr(
            update.effective_user,
            "id",
            None,
        ),
    )

    # ======================================================
    # OLD NO-ID ENTER RAFFLE BUTTON
    #
    # IMPORTANT:
    #
    # Your current failing button sends:
    #
    #     raffle_enter
    #
    # There is NO raffle ID attached.
    #
    # We resolve it against the current active raffle.
    # This allows the EXISTING BUTTON to keep working.
    # ======================================================

    if data == "raffle_enter":

        logger.info(
            "OLD NO-ID ENTER CALLBACK RECEIVED"
        )

        raffle = get_active_raffle()

        if not raffle:

            logger.warning(
                "OLD NO-ID ENTER FAILED: "
                "no active raffle exists."
            )

            await safe_answer(
                query,
                "There is no active raffle.",
                True,
            )

            return

        logger.info(
            "OLD NO-ID ENTER RESOLVED | raffle=%s",
            raffle["id"],
        )

        await enter_raffle(
            update,
            context,
            int(raffle["id"]),
        )

        return

    # ======================================================
    # OLD NO-ID CASH APP BUTTON
    # ======================================================

    if data == "raffle_pay_cashapp":

        logger.info(
            "OLD NO-ID CASH APP CALLBACK RECEIVED"
        )

        raffle = get_active_raffle()

        if not raffle:

            await safe_answer(
                query,
                "There is no active raffle.",
                True,
            )

            return

        logger.info(
            "OLD NO-ID CASH APP RESOLVED | raffle=%s",
            raffle["id"],
        )

        await payment_method(
            update,
            context,
            int(raffle["id"]),
            "cashapp",
        )

        return

    # ======================================================
    # OLD NO-ID ZELLE BUTTON
    # ======================================================

    if data == "raffle_pay_zelle":

        logger.info(
            "OLD NO-ID ZELLE CALLBACK RECEIVED"
        )

        raffle = get_active_raffle()

        if not raffle:

            await safe_answer(
                query,
                "There is no active raffle.",
                True,
            )

            return

        logger.info(
            "OLD NO-ID ZELLE RESOLVED | raffle=%s",
            raffle["id"],
        )

        await payment_method(
            update,
            context,
            int(raffle["id"]),
            "zelle",
        )

        return

    # ======================================================
    # LEGACY ENTER RAFFLE BUTTON
    #
    # raffle_enter_123
    # ======================================================

    if data.startswith("raffle_enter_"):

        value = data[
            len("raffle_enter_"):
        ]

        logger.info(
            "LEGACY ENTER RAFFLE CALLBACK | value=%s",
            value,
        )

        if value.isdigit():

            await enter_raffle(
                update,
                context,
                int(value),
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # LEGACY CASH APP BUTTON
    #
    # raffle_pay_cashapp_123
    # ======================================================

    if data.startswith("raffle_pay_cashapp_"):

        value = data[
            len("raffle_pay_cashapp_"):
        ]

        logger.info(
            "LEGACY CASH APP CALLBACK | value=%s",
            value,
        )

        if value.isdigit():

            await payment_method(
                update,
                context,
                int(value),
                "cashapp",
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # LEGACY ZELLE BUTTON
    #
    # raffle_pay_zelle_123
    # ======================================================

    if data.startswith("raffle_pay_zelle_"):

        value = data[
            len("raffle_pay_zelle_"):
        ]

        logger.info(
            "LEGACY ZELLE CALLBACK | value=%s",
            value,
        )

        if value.isdigit():

            await payment_method(
                update,
                context,
                int(value),
                "zelle",
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # APPROVE RAFFLE
    # ======================================================

    if data.startswith("raffle_approve_"):

        value = data[
            len("raffle_approve_"):
        ]

        if value.isdigit():

            await approve_raffle_callback(
                update,
                context,
                int(value),
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # CANCEL RAFFLE
    # ======================================================

    if data.startswith("raffle_cancel_"):

        value = data[
            len("raffle_cancel_"):
        ]

        if value.isdigit():

            await cancel_raffle_callback(
                update,
                context,
                int(value),
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # APPROVE ENTRY
    # ======================================================

    if data.startswith("approve_"):

        value = data[
            len("approve_"):
        ]

        if value.isdigit():

            await approve_entry_callback(
                update,
                context,
                int(value),
            )

        else:

            await safe_answer(
                query,
                "Invalid entry ID.",
                True,
            )

        return

    # ======================================================
    # DENY ENTRY
    # ======================================================

    if data.startswith("deny_"):

        value = data[
            len("deny_"):
        ]

        if value.isdigit():

            await deny_entry_callback(
                update,
                context,
                int(value),
            )

        else:

            await safe_answer(
                query,
                "Invalid entry ID.",
                True,
            )

        return

    # ======================================================
    # CURRENT ENTER RAFFLE BUTTON
    #
    # enter_123
    # ======================================================

    if data.startswith("enter_"):

        value = data[
            len("enter_"):
        ]

        logger.info(
            "ENTER CALLBACK ROUTE | value=%s",
            value,
        )

        if value.isdigit():

            await enter_raffle(
                update,
                context,
                int(value),
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # CASH APP
    # ======================================================

    if data.startswith("pay_cashapp_"):

        value = data[
            len("pay_cashapp_"):
        ]

        if value.isdigit():

            await payment_method(
                update,
                context,
                int(value),
                "cashapp",
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # ZELLE
    # ======================================================

    if data.startswith("pay_zelle_"):

        value = data[
            len("pay_zelle_"):
        ]

        if value.isdigit():

            await payment_method(
                update,
                context,
                int(value),
                "zelle",
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # LEGACY PAYMENT CALLBACK
    # ======================================================

    if data.startswith("payment_"):

        value = data[
            len("payment_"):
        ]

        if value.isdigit():

            await payment_method(
                update,
                context,
                int(value),
                "cashapp",
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # LEGACY PAID CALLBACK
    # ======================================================

    if data.startswith("paid_"):

        value = data[
            len("paid_"):
        ]

        if value.isdigit():

            await payment_method(
                update,
                context,
                int(value),
                "cashapp",
            )

        else:

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

        return

    # ======================================================
    # DRAW CALLBACK
    # ======================================================

    if data.startswith("draw_"):

        value = data[
            len("draw_"):
        ]

        if not value.isdigit():

            await safe_answer(
                query,
                "Invalid raffle ID.",
                True,
            )

            return

        user = update.effective_user

        if not user or not is_raffle_admin(user.id):

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

            return

        await safe_answer(query)

        await draw_raffle(
            update,
            context,
        )

        return

    # ======================================================
    # REROLL CALLBACK
    # ======================================================

    if data.startswith("reroll_"):

        user = update.effective_user

        if not user or not is_raffle_admin(user.id):

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

            return

        await safe_answer(
            query,
            "Use /draw to select the raffle winner.",
            True,
        )

        return

    # ======================================================
    # BONUS ENTRY CALLBACK
    # ======================================================

    if data.startswith("bonus_"):

        user = update.effective_user

        if not user or not is_raffle_admin(user.id):

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

            return

        await safe_answer(
            query,
            "Use the admin manual-entry option to add a bonus entry.",
            True,
        )

        return

    # ======================================================
    # REMOVE ENTRY CALLBACK
    # ======================================================

    if data.startswith("remove_"):

        value = data[
            len("remove_"):
        ]

        if not value.isdigit():

            await safe_answer(
                query,
                "Invalid entry ID.",
                True,
            )

            return

        user = update.effective_user

        if not user or not is_raffle_admin(user.id):

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

            return

        try:

            removed = remove_entry(
                int(value)
            )

        except Exception:

            logger.exception(
                "Could not remove entry %s.",
                value,
            )

            removed = False

        await safe_answer(
            query,
            "Entry removed."
            if removed
            else "Entry could not be removed.",
            True,
        )

        return

    # ======================================================
    # UNKNOWN RAFFLE CALLBACK
    # ======================================================

    logger.warning(
        "UNHANDLED RAFFLE CALLBACK | %s",
        data,
    )

    await safe_answer(
        query,
        "⚠️ This raffle button is no longer available.",
        True,
    )


# ==========================================================
# RAFFLE STATUS
# ==========================================================

async def raffle_status(
    update,
    context,
):

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if not user or not is_raffle_admin(user.id):

        if query:

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

        return

    raffle = get_active_raffle()

    if not raffle:

        text = (
            "🎟️ <b>RAFFLE STATUS</b>\n\n"
            "There is currently no active raffle."
        )

    else:

        approved = get_approved_entries(
            raffle["id"]
        )

        pending = get_pending_entries(
            raffle["id"]
        )

        raffle_type = (
            "FREE"
            if is_free_raffle(
                raffle["price"]
            )
            else "PAID"
        )

        text = (
            "🎟️ <b>RAFFLE STATUS</b>\n\n"
            f"🆔 ID: <code>{raffle['id']}</code>\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n"
            f"📋 Type: <b>{raffle_type}</b>\n"
            f"⏰ Ends: <b>"
            f"{format_expiration(raffle['expires_at'])}"
            f"</b>\n\n"
            f"✅ Approved Entries: <b>"
            f"{len(approved)}</b>\n"
            f"⏳ Pending Entries: <b>"
            f"{len(pending)}</b>"
        )

    if query:

        await safe_answer(query)

    target = (
        query.message
        if query
        else message
    )

    if target:

        try:

            await target.reply_text(
                text,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.exception(
                "Could not send raffle status."
            )


# ==========================================================
# RAFFLE ENTRIES
# ==========================================================

async def raffle_entries(
    update,
    context,
):

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if not user or not is_raffle_admin(user.id):

        if query:

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

        return

    raffle = get_active_raffle()

    if not raffle:

        text = (
            "🎟️ <b>RAFFLE ENTRIES</b>\n\n"
            "No active raffle."
        )

    else:

        entries = get_approved_entries(
            raffle["id"]
        )

        raffle_type = (
            "FREE"
            if is_free_raffle(
                raffle["price"]
            )
            else "PAID"
        )

        if entries:

            lines = []

            for i, entry in enumerate(
                entries,
                1,
            ):

                lines.append(
                    f"{i}. {display_user(entry)} "
                    f"(Entry #{entry['id']})"
                )

            entries_text = "\n".join(lines)

        else:

            entries_text = (
                "No approved entries yet."
            )

        text = (
            f"🎟️ <b>APPROVED ENTRIES "
            f"({raffle_type})</b>\n\n"
            f"{entries_text}"
        )

    if query:

        await safe_answer(query)

    target = (
        query.message
        if query
        else message
    )

    if target:

        try:

            await target.reply_text(
                text,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.exception(
                "Could not display raffle entries."
            )


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(
    update,
    context,
):

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if not user or not is_raffle_admin(user.id):

        if query:

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

        return

    pending = get_pending_entries()

    if query:

        await safe_answer(query)

    target = (
        query.message
        if query
        else message
    )

    if not target:
        return

    if not pending:

        await target.reply_text(
            "⏳ <b>PENDING RAFFLE ENTRIES</b>\n\n"
            "There are no pending entries.",
            parse_mode=ParseMode.HTML,
        )

        return

    for entry in pending:

        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=(
                        f"approve_{entry['id']}"
                    ),
                ),
                InlineKeyboardButton(
                    "❌ DENY",
                    callback_data=(
                        f"deny_{entry['id']}"
                    ),
                ),
            ]]
        )

        text = (
            "⏳ <b>PENDING RAFFLE ENTRY</b>\n\n"
            f"🆔 Entry: <code>{entry['id']}</code>\n"
            f"🎟️ Raffle: "
            f"<code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: <b>"
            f"{entry.get('prize') or 'Unknown'}"
            f"</b>\n"
            f"💵 Price: <b>"
            f"{entry.get('price') or 'Unknown'}"
            f"</b>\n"
            f"👤 Member: <b>"
            f"{display_user(entry)}"
            f"</b>\n"
            f"💳 Payment: <b>"
            f"{entry.get('payment_method') or 'Not selected'}"
            f"</b>\n\n"
            "Choose an action:"
        )

        try:

            await target.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.exception(
                "Could not display pending entry %s.",
                entry["id"],
            )


# ==========================================================
# COMPLETED PAYMENTS
# ==========================================================

async def paid_entry(
    update,
    context,
):

    return await raffle_entries(
        update,
        context,
    )


# ==========================================================
# CANCEL ACTIVE RAFFLE
# ==========================================================

async def cancel_raffle(
    update,
    context,
):

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if not user or not is_raffle_admin(user.id):

        if query:

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

        return

    raffle = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if not raffle:

        if query:

            await safe_answer(
                query,
                "No raffle to cancel.",
                True,
            )

        elif message:

            await message.reply_text(
                "⚠️ There is no raffle to cancel."
            )

        return

    if raffle["status"] == "pending":

        changed = cancel_pending_raffle(
            raffle["id"]
        )

    else:

        changed = close_raffle(
            raffle["id"]
        )

    if query:

        await safe_answer(
            query,
            "Raffle cancelled."
            if changed
            else "Could not cancel.",
        )

    target = (
        query.message
        if query
        else message
    )

    if target:

        try:

            await target.reply_text(
                "❌ Raffle cancelled."
                if changed
                else
                "⚠️ Raffle could not be cancelled."
            )

        except TelegramError:

            pass


# ==========================================================
# DRAW RAFFLE
# ==========================================================

async def draw_raffle(
    update,
    context,
):

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if not user or not is_raffle_admin(user.id):

        if query:

            await safe_answer(
                query,
                "⛔ Admins only.",
                True,
            )

        return

    raffle = get_active_raffle()

    if not raffle:

        if query:

            await safe_answer(
                query,
                "No active raffle.",
                True,
            )

        elif message:

            await message.reply_text(
                "⚠️ There is no active raffle."
            )

        return

    entries = get_approved_entries(
        raffle["id"]
    )

    if not entries:

        if query:

            await safe_answer(
                query,
                "No approved entries.",
                True,
            )

        elif message:

            await message.reply_text(
                "⚠️ There are no approved entries."
            )

        return

    winner = random.choice(entries)

    closed = close_raffle(
        raffle["id"]
    )

    if not closed:

        logger.warning(
            "Winner selected but raffle could not "
            "be closed. raffle=%s",
            raffle["id"],
        )

    text = (
        "🎉 <b>RAFFLE WINNER!</b>\n\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n\n"
        f"🏆 Winner: <b>{display_user(winner)}</b>\n"
        f"🆔 Entry: <code>{winner['id']}</code>\n\n"
        "🎉 Congratulations!"
    )

    if query:

        await safe_answer(
            query,
            "Winner selected!"
        )

    target = (
        query.message
        if query
        else message
    )

    if target:

        try:

            await target.reply_text(
                text,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.exception(
                "Could not post raffle winner."
            )

    # ------------------------------------------------------
    # PRIVATE WINNER NOTIFICATION
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=int(winner["user_id"]),
            text=(
                "🏆 <b>CONGRATULATIONS!</b>\n\n"
                "🎉 You won the "
                "<b>Melanated AZ Friends Raffle!</b>\n\n"
                f"🎁 Prize: <b>{raffle['prize']}</b>\n"
                f"🆔 Entry: <code>{winner['id']}</code>\n\n"
                "Congratulations! 🎉"
            ),
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.info(
            "Could not privately notify winner %s.",
            winner["user_id"],
        )


# ==========================================================
# END raffle.py
# ==========================================================
