# ==========================================================
# Melanated AZ Bot - raffle.py
# COMPLETE DROP-IN RAFFLE SYSTEM
#
# Includes:
#   - Raffle creation
#   - Raffle approval
#   - Raffle cancellation
#   - Public raffle entry
#   - FREE raffle auto-approval
#   - PAID raffle pending/admin approval
#   - Cash App / Zelle
#   - Payment method tracking
#   - Pending entry approval
#   - Entry denial
#   - Manual admin entry
#   - Winner drawing
#
# IMPORTANT:
#   raffle_callback() is the ONLY owner of raffle callbacks.
#
# FREE RAFFLE:
#   $0 / 0 / Free / FREE / $0.00 / 0.00
#   -> Automatically approved.
#   -> Payment buttons are NOT displayed.
#
# PAID RAFFLE:
#   Any non-zero price
#   -> Entry remains pending until admin approval.
#   -> Cash App / Zelle payment method is saved.
#
# DATABASE:
#   Uses existing raffle_database.py.
#   No database reset or replacement.
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


logger = logging.getLogger(
    "melanated_az_raffle"
)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_raffle_admin(user_id):

    try:

        return (
            user_id is not None
            and int(user_id)
            in {
                int(x)
                for x in ADMIN_IDS
            }
        )

    except Exception:

        return False


# ==========================================================
# FREE RAFFLE CHECK
# ==========================================================

def is_free_raffle(price):
    """
    Returns True when the raffle is a free-entry raffle.

    Accepted free values include:

        Free
        FREE
        free
        0
        0.00
        $0
        $0.00

    Everything else is treated as a paid raffle.
    """

    if price is None:
        return True

    value = str(price).strip().lower()

    value = value.replace(
        "$",
        "",
    )

    value = value.replace(
        ",",
        "",
    )

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

    except (
        TypeError,
        ValueError,
    ):

        return False


# ==========================================================
# DISPLAY USER
# ==========================================================

def display_user(entry):

    name = (
        entry.get("display_name")
        or entry.get("username")
        or str(entry.get("user_id"))
    )

    username = str(
        entry.get("username")
        or ""
    ).lstrip("@")

    if (
        username
        and username.lower()
        != str(name).lower()
    ):

        return f"{name} (@{username})"

    return str(name)


# ==========================================================
# EXPIRATION FORMAT
# ==========================================================

def format_expiration(value):

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

            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )

        elif message:

            await message.reply_text(
                "⛔ Admins only."
            )

        return

    if query:

        await query.answer()

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

        return

    if not message:
        return

    parts = (
        message.text or ""
    ).split(
        " ",
        1,
    )

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
        for x in payload.split(
            "|",
            1,
        )
    ]

    if not prize or not price:

        await message.reply_text(
            "⚠️ Prize and entry price are required."
        )

        return

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

    expires = (
        datetime.utcnow()
        + timedelta(
            days=int(
                RAFFLE_DURATION_DAYS
                or 7
            )
        )
    )

    raffle_id = create_raffle(
        prize,
        price,
        expires.isoformat(),
    )

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

    raffle_type = (
        "FREE ENTRY"
        if is_free_raffle(price)
        else "PAID ENTRY"
    )

    text = (
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
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

            sent_to_admin.add(
                int(admin_id)
            )

        except TelegramError:

            logger.warning(
                "Could not notify admin %s.",
                admin_id,
            )

    if user.id not in sent_to_admin:

        try:

            await context.bot.send_message(
                chat_id=user.id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            pass

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

    raffle = get_raffle(
        raffle_id
    )

    if not raffle:
        return False

    free = is_free_raffle(
        raffle["price"]
    )

    # ------------------------------------------------------
    # FREE RAFFLE KEYBOARD
    # ------------------------------------------------------

    if free:

        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "🎟️ ENTER RAFFLE",
                    callback_data=(
                        f"enter_{raffle_id}"
                    ),
                )
            ]]
        )

        entry_label = (
            "🆓 <b>FREE ENTRY</b>"
        )

        pending_notice = (
            "🎉 Your entry is automatically "
            "<b>APPROVED</b> because this is "
            "a free raffle."
        )

    # ------------------------------------------------------
    # PAID RAFFLE KEYBOARD
    # ------------------------------------------------------

    else:

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

        entry_label = (
            f"💵 <b>Entry: {raffle['price']}</b>"
        )

        pending_notice = (
            "⚠️ Your entry remains <b>PENDING</b> "
            "until an admin verifies your payment."
        )

    text = (
        "🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b>\n\n"
        f"🎁 <b>Prize:</b> {raffle['prize']}\n"
        f"{entry_label}\n"
        f"⏰ <b>Ends:</b> "
        f"{format_expiration(raffle['expires_at'])}\n\n"
        "👇 Tap below to enter.\n\n"
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

        await query.answer(
            "⛔ Admins only.",
            show_alert=True,
        )

        return

    raffle = get_raffle(
        raffle_id
    )

    if not raffle:

        await query.answer(
            "Raffle not found.",
            show_alert=True,
        )

        return

    if raffle["status"] != "pending":

        await query.answer(
            f"Raffle is already "
            f"{raffle['status']}.",
            show_alert=True,
        )

        return

    if not approve_raffle(
        raffle_id
    ):

        await query.answer(
            "Raffle could not be approved.",
            show_alert=True,
        )

        return

    await query.answer(
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

    if await publish_raffle(
        raffle_id,
        context,
    ):

        try:

            await query.message.reply_text(
                "✅ Raffle is now live in "
                "the raffle group."
            )

        except Exception:

            pass

    else:

        logger.error(
            "Raffle %s approved but publication failed.",
            raffle_id,
        )


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

        await query.answer(
            "⛔ Admins only.",
            show_alert=True,
        )

        return

    raffle = get_raffle(
        raffle_id
    )

    if not raffle:

        await query.answer(
            "Raffle not found.",
            show_alert=True,
        )

        return

    if not cancel_pending_raffle(
        raffle_id
    ):

        await query.answer(
            "Raffle could not be cancelled.",
            show_alert=True,
        )

        return

    await query.answer(
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

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    raffle = get_raffle(
        raffle_id
    )

    if not raffle or raffle["status"] != "active":

        await query.answer(
            "This raffle is no longer active.",
            show_alert=True,
        )

        return

    free = is_free_raffle(
        raffle["price"]
    )

    name = (
        user.full_name
        or user.username
        or str(user.id)
    )

    # ------------------------------------------------------
    # DATABASE PREVENTS:
    #
    # pending + same raffle + same user
    # approved + same raffle + same user
    #
    # Therefore one active entry per user per raffle.
    # ------------------------------------------------------

    entry_id = add_raffle_entry(
        raffle_id,
        user.id,
        user.username,
        name,
        "free" if free else None,
    )

    if entry_id is None:

        await query.answer(
            "You already have an entry "
            "for this raffle.",
            show_alert=True,
        )

        return

    # ======================================================
    # FREE RAFFLE
    # ======================================================

    if free:

        changed = approve_entry(
            entry_id,
            user.id,
        )

        if not changed:

            logger.error(
                "FREE RAFFLE AUTO-APPROVAL FAILED | "
                "entry=%s | raffle=%s | user=%s",
                entry_id,
                raffle_id,
                user.id,
            )

            await query.answer(
                "Your entry was created but "
                "could not be approved. "
                "Please contact an admin.",
                show_alert=True,
            )

            return

        logger.info(
            "FREE RAFFLE ENTRY AUTO-APPROVED | "
            "entry=%s | raffle=%s | user=%s",
            entry_id,
            raffle_id,
            user.id,
        )

        await query.answer(
            "🎉 You're entered! Entry approved.",
            show_alert=True,
        )

        try:

            await query.message.reply_text(
                "🎉 <b>YOU'RE IN!</b>\n\n"
                f"🎁 Prize: <b>{raffle['prize']}</b>\n"
                f"🆓 Entry: <b>FREE</b>\n"
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

    await query.answer(
        "Entry submitted for approval!",
        show_alert=True,
    )

    try:

        await query.message.reply_text(
            f"🎟️ <b>ENTRY SUBMITTED</b>\n\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry Price: <b>{raffle['price']}</b>\n"
            f"🆔 Entry: <code>{entry_id}</code>\n\n"
            "⏳ Your entry is <b>PENDING</b> "
            "until an admin verifies payment.\n\n"
            "💳 Please choose Cash App or Zelle "
            "below and complete your payment.",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.exception(
            "Could not send pending-entry confirmation "
            "for entry %s.",
            entry_id,
        )

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "💵 PAY WITH CASH APP",
                callback_data=(
                    f"pay_cashapp_{raffle_id}"
                ),
            ),
            InlineKeyboardButton(
                "🏦 PAY WITH ZELLE",
                callback_data=(
                    f"pay_zelle_{raffle_id}"
                ),
            ),
        ]]
    )

    try:

        await query.message.reply_text(
            "💳 <b>SELECT PAYMENT METHOD</b>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.exception(
            "Could not send payment selection "
            "for entry %s.",
            entry_id,
        )

    # ------------------------------------------------------
    # Notify admins.
    # ------------------------------------------------------

    admin_keyboard = InlineKeyboardMarkup(
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
        "💳 Payment: <b>Not selected</b>\n"
        "⏳ Status: <b>PENDING</b>\n\n"
        "Choose an action:"
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
                reply_markup=admin_keyboard,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.warning(
                "Could not notify admin %s.",
                admin_id,
            )


# ==========================================================
# UPDATE PAYMENT METHOD
# ==========================================================

def _set_entry_payment_method(
    entry_id,
    payment_method,
):
    """
    Updates the payment method for a pending entry.

    Uses the existing raffle_entries table.
    No schema changes are required because
    payment_method already exists in raffle_database.py.
    """

    import raffle_database

    conn = raffle_database.get_connection()

    try:

        cur = conn.execute(
            """
            UPDATE raffle_entries
            SET payment_method=?
            WHERE id=?
              AND status='pending'
            """,
            (
                payment_method,
                int(entry_id),
            ),
        )

        conn.commit()

        return cur.rowcount == 1

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


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

    raffle = get_raffle(
        raffle_id
    )

    if not raffle or raffle["status"] != "active":

        await query.answer(
            "Raffle is no longer active.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # Payment buttons are not needed for FREE raffles.
    # ------------------------------------------------------

    if is_free_raffle(
        raffle["price"]
    ):

        await query.answer(
            "This is a FREE raffle. "
            "No payment is required.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # Find this user's pending entry.
    # ------------------------------------------------------

    entry = next(
        (
            x
            for x in get_raffle_entries(
                raffle_id
            )
            if (
                int(x["user_id"])
                == int(user.id)
                and x["status"] == "pending"
            )
        ),
        None,
    )

    if not entry:

        await query.answer(
            "Enter the raffle first.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # Validate payment method.
    # ------------------------------------------------------

    method = str(
        method or ""
    ).strip().lower()

    if method not in {
        "cashapp",
        "zelle",
    }:

        await query.answer(
            "Invalid payment method.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # SAVE PAYMENT METHOD
    # ------------------------------------------------------

    try:

        changed = _set_entry_payment_method(
            entry["id"],
            method,
        )

    except Exception:

        logger.exception(
            "Could not save payment method | "
            "entry=%s | method=%s",
            entry["id"],
            method,
        )

        await query.answer(
            "Could not save payment method. "
            "Please try again.",
            show_alert=True,
        )

        return

    if not changed:

        await query.answer(
            "This entry is no longer pending.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # PAYMENT INSTRUCTIONS
    # ------------------------------------------------------

    if method == "cashapp":

        body = (
            "💵 <b>CASH APP</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{CASHAPP_TAG}</code>"
        )

        if CASHAPP_URL:

            body += (
                f"\n\n"
                f"{CASHAPP_URL}"
            )

        method_name = "Cash App"

    else:

        body = (
            "🏦 <b>ZELLE</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{ZELLE_PHONE}</code>"
        )

        method_name = "Zelle"

    await query.answer(
        f"{method_name} selected!"
    )

    try:

        await query.message.reply_text(
            body
            + "\n\n"
            "⏳ After payment, your entry remains "
            "<b>PENDING</b> until an admin verifies it.\n\n"
            f"💳 Payment method recorded: "
            f"<b>{method_name}</b>",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.exception(
            "Could not send payment instructions."
        )

    # ------------------------------------------------------
    # Update admin notifications.
    #
    # We send a NEW notification rather than trying to
    # edit every existing admin message.
    # This makes payment-method tracking reliable.
    # ------------------------------------------------------

    admin_keyboard = InlineKeyboardMarkup(
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

    admin_text = (
        "💳 <b>PAYMENT METHOD SELECTED</b>\n\n"
        f"🆔 Entry: <code>{entry['id']}</code>\n"
        f"🎟️ Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n"
        f"💵 Price: <b>{raffle['price']}</b>\n"
        f"👤 Member: <b>"
        f"{display_user(entry)}"
        f"</b>\n"
        f"💳 Payment: <b>{method_name}</b>\n"
        "⏳ Status: <b>PENDING</b>\n\n"
        "Verify the payment and choose an action:"
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
                reply_markup=admin_keyboard,
                parse_mode=ParseMode.HTML,
            )

        except TelegramError:

            logger.warning(
                "Could not notify admin %s about payment "
                "for entry %s.",
                admin_id,
                entry["id"],
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

        await query.answer(
            "⛔ Admins only.",
            show_alert=True,
        )

        return

    entry = get_entry(
        entry_id
    )

    if not entry:

        await query.answer(
            "Entry not found.",
            show_alert=True,
        )

        return

    if entry["status"] != "pending":

        await query.answer(
            f"Entry is already "
            f"{entry['status']}.",
            show_alert=True,
        )

        return

    changed = approve_entry(
        entry_id,
        user.id,
    )

    if not changed:

        await query.answer(
            "Entry could not be approved. "
            "It may already have been processed.",
            show_alert=True,
        )

        return

    logger.info(
        "ENTRY APPROVED | entry=%s | raffle=%s | admin=%s",
        entry_id,
        entry["raffle_id"],
        user.id,
    )

    await query.answer(
        "✅ Entry approved!"
    )

    payment_display = (
        entry.get("payment_method")
        or "Verified"
    )

    if payment_display == "cashapp":
        payment_display = "Cash App"

    elif payment_display == "zelle":
        payment_display = "Zelle"

    elif payment_display == "manual":
        payment_display = "Manual"

    try:

        await query.edit_message_text(
            "✅ <b>ENTRY APPROVED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: <b>"
            f"{entry.get('prize') or 'Raffle'}"
            f"</b>\n"
            f"👤 Member: <b>"
            f"{display_user(entry)}"
            f"</b>\n"
            f"💳 Payment: <b>"
            f"{payment_display}"
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

    try:

        await context.bot.send_message(
            chat_id=int(entry["user_id"]),
            text=(
                "🎉 <b>YOUR RAFFLE ENTRY "
                "WAS APPROVED!</b>\n\n"
                f"🎁 Prize: <b>"
                f"{entry.get('prize') or 'Raffle'}"
                f"</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "✅ Your payment has been verified "
                "and your entry is approved.\n\n"
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

        await query.answer(
            "⛔ Admins only.",
            show_alert=True,
        )

        return

    entry = get_entry(
        entry_id
    )

    if not entry:

        await query.answer(
            "Entry not found.",
            show_alert=True,
        )

        return

    if entry["status"] != "pending":

        await query.answer(
            f"Entry is already "
            f"{entry['status']}.",
            show_alert=True,
        )

        return

    if not deny_entry(
        entry_id,
        user.id,
    ):

        await query.answer(
            "Entry could not be denied.",
            show_alert=True,
        )

        return

    await query.answer(
        "Entry denied."
    )

    try:

        await query.edit_message_text(
            f"❌ <b>ENTRY DENIED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"👤 Member: <b>"
            f"{display_user(entry)}"
            f"</b>\n"
            f"💳 Payment: <b>"
            f"{entry.get('payment_method') or 'Not selected'}"
            f"</b>\n\n"
            f"Denied by admin "
            f"<code>{user.id}</code>.",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        pass

    # ------------------------------------------------------
    # Notify entrant.
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=int(entry["user_id"]),
            text=(
                "❌ <b>YOUR RAFFLE ENTRY "
                "WAS DENIED</b>\n\n"
                f"🎁 Prize: <b>"
                f"{entry.get('prize') or 'Raffle'}"
                f"</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "Your raffle entry was denied by an admin."
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

    query = update.callback_query
    admin_user = update.effective_user

    if not query or not admin_user:
        return False

    if not is_raffle_admin(
        admin_user.id
    ):

        await query.answer(
            "⛔ Admins only.",
            show_alert=True,
        )

        return False

    raffle = get_active_raffle()

    if not raffle:

        await query.answer(
            "There is no active raffle.",
            show_alert=True,
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>NO ACTIVE RAFFLE</b>\n\n"
                "There is currently no active raffle "
                "to add a manual entry to.\n\n"
                "Start and approve a raffle first.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back",
                                callback_data="admin_back",
                            )
                        ]
                    ]
                ),
            )

        except TelegramError:

            pass

        return False

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

            except (TypeError, ValueError):

                continue

    if not member:

        await query.answer(
            "Member could not be found.",
            show_alert=True,
        )

        return False

    username = member.get(
        "username"
    )

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
    # Prevent duplicate entries.
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

                await query.answer(
                    "This member already has an "
                    "entry in this raffle.",
                    show_alert=True,
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
                            [
                                [
                                    InlineKeyboardButton(
                                        "⬅️ Back",
                                        callback_data="admin_back",
                                    )
                                ]
                            ]
                        ),
                    )

                except TelegramError:

                    pass

                return False

        except (TypeError, ValueError):

            continue

    # ------------------------------------------------------
    # Create entry.
    # ------------------------------------------------------

    entry_id = add_raffle_entry(
        raffle["id"],
        int(member_user_id),
        username,
        display_name,
        "manual",
    )

    if entry_id is None:

        await query.answer(
            "The entry could not be created.",
            show_alert=True,
        )

        return False

    # ------------------------------------------------------
    # Manual entries are always approved immediately.
    # ------------------------------------------------------

    changed = approve_entry(
        entry_id,
        admin_user.id,
    )

    if not changed:

        logger.error(
            "Manual entry created but approval failed | "
            "entry=%s | member=%s | raffle=%s",
            entry_id,
            member_user_id,
            raffle["id"],
        )

        await query.answer(
            "Entry was created but could not be approved.",
            show_alert=True,
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>MANUAL ENTRY WARNING</b>\n\n"
                f"👤 Member: <b>{display_name}</b>\n"
                f"🆔 Entry: <code>{entry_id}</code>\n\n"
                "The entry was created, but the automatic "
                "approval failed.\n\n"
                "Check the raffle entries before trying again.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back",
                                callback_data="admin_back",
                            )
                        ]
                    ]
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

    await query.answer(
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
    # Notify member privately when possible.
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
    Single callback router for ALL raffle callbacks.

    IMPORTANT:
    This function owns:

        raffle_approve_
        raffle_cancel_
        approve_
        deny_
        enter_
        pay_cashapp_
        pay_zelle_
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Raffle callback received: %s",
        data,
    )

    # ------------------------------------------------------
    # APPROVE RAFFLE
    # ------------------------------------------------------

    if data.startswith(
        "raffle_approve_"
    ):

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

            await query.answer(
                "Invalid raffle ID.",
                show_alert=True,
            )

        return

    # ------------------------------------------------------
    # CANCEL RAFFLE
    # ------------------------------------------------------

    if data.startswith(
        "raffle_cancel_"
    ):

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

            await query.answer(
                "Invalid raffle ID.",
                show_alert=True,
            )

        return

    # ------------------------------------------------------
    # APPROVE ENTRY
    # ------------------------------------------------------

    if data.startswith(
        "approve_"
    ):

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

            await query.answer(
                "Invalid entry ID.",
                show_alert=True,
            )

        return

    # ------------------------------------------------------
    # DENY ENTRY
    # ------------------------------------------------------

    if data.startswith(
        "deny_"
    ):

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

            await query.answer(
                "Invalid entry ID.",
                show_alert=True,
            )

        return

    # ------------------------------------------------------
    # ENTER RAFFLE
    # ------------------------------------------------------

    if data.startswith(
        "enter_"
    ):

        value = data[
            len("enter_"):
        ]

        if value.isdigit():

            await enter_raffle(
                update,
                context,
                int(value),
            )

        else:

            await query.answer(
                "Invalid raffle ID.",
                show_alert=True,
            )

        return

    # ------------------------------------------------------
    # CASH APP
    # ------------------------------------------------------

    if data.startswith(
        "pay_cashapp_"
    ):

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

            await query.answer(
                "Invalid raffle ID.",
                show_alert=True,
            )

        return

    # ------------------------------------------------------
    # ZELLE
    # ------------------------------------------------------

    if data.startswith(
        "pay_zelle_"
    ):

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

            await query.answer(
                "Invalid raffle ID.",
                show_alert=True,
            )

        return

    await query.answer()

    logger.warning(
        "Unhandled raffle callback: %s",
        data,
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

    if not user or not is_raffle_admin(
        user.id
    ):

        if query:

            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
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
        await query.answer()

    target = (
        query.message
        if query
        else message
    )

    if target:

        await target.reply_text(
            text,
            parse_mode=ParseMode.HTML,
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

    if not user or not is_raffle_admin(
        user.id
    ):

        if query:

            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
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

        text = (
            f"🎟️ <b>APPROVED ENTRIES "
            f"({raffle_type})</b>\n\n"
            +
            (
                "\n".join(
                    f"{i}. {display_user(e)} "
                    f"(Entry #{e['id']})"
                    for i, e
                    in enumerate(
                        entries,
                        1,
                    )
                )
                if entries
                else
                "No approved entries yet."
            )
        )

    if query:
        await query.answer()

    target = (
        query.message
        if query
        else message
    )

    if target:

        await target.reply_text(
            text,
            parse_mode=ParseMode.HTML,
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

    if not user or not is_raffle_admin(
        user.id
    ):

        if query:

            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )

        return

    pending = get_pending_entries()

    if query:
        await query.answer()

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

        payment_display = (
            entry.get("payment_method")
            or "Not selected"
        )

        if payment_display == "cashapp":
            payment_display = "Cash App"

        elif payment_display == "zelle":
            payment_display = "Zelle"

        elif payment_display == "manual":
            payment_display = "Manual"

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
            f"{payment_display}"
            f"</b>\n"
            f"⏳ Status: <b>PENDING</b>\n\n"
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
                "Could not display pending "
                "entry %s.",
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

    if not user or not is_raffle_admin(
        user.id
    ):

        if query:

            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )

        return

    raffle = (
        get_active_raffle()
        or get_pending_raffle()
    )

    if not raffle:

        if query:

            await query.answer(
                "No raffle to cancel.",
                show_alert=True,
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

        await query.answer(
            "Raffle cancelled."
            if changed
            else "Could not cancel."
        )

    target = (
        query.message
        if query
        else message
    )

    if target:

        await target.reply_text(
            "❌ Raffle cancelled."
            if changed
            else
            "⚠️ Raffle could not be cancelled."
        )


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

    if not user or not is_raffle_admin(
        user.id
    ):

        if query:

            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )

        return

    raffle = get_active_raffle()

    if not raffle:

        if query:

            await query.answer(
                "No active raffle.",
                show_alert=True,
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

            await query.answer(
                "No approved entries.",
                show_alert=True,
            )

        elif message:

            await message.reply_text(
                "⚠️ There are no approved entries."
            )

        return

    winner = random.choice(
        entries
    )

    close_raffle(
        raffle["id"]
    )

    text = (
        "🎉 <b>RAFFLE WINNER!</b>\n\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n\n"
        f"🏆 Winner: <b>"
        f"{display_user(winner)}"
        f"</b>\n"
        f"🆔 Entry: <code>{winner['id']}</code>\n\n"
        "🎉 Congratulations!"
    )

    if query:

        await query.answer(
            "Winner selected!"
        )

    target = (
        query.message
        if query
        else message
    )

    if target:

        await target.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )


# ==========================================================
# END raffle.py
# ==========================================================
