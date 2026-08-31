# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# COMPLETE DROP-IN RAFFLE SYSTEM
#
# Features:
# - Start raffle
# - Pending raffle approval
# - Active raffle
# - Enter raffle
# - Cash App payment option
# - Zelle payment option
# - Pending entry approval
# - Approve entry button
# - Deny entry button
# - View pending entries
# - View approved entries
# - Draw winner
# - Reroll winner
# - Remove entry
# - Bonus entry
# - Cancel raffle
# - Persistent SQLite database
#
# IMPORTANT:
# - Does NOT delete database
# - Does NOT reset database
# - Uses /var/data/raffle.db
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
    approve_entry,
    deny_entry,
    get_approved_entries,
    get_raffle_entries,
    remove_entry,
)


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger("melanated_az_raffle")


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_raffle_admin(user_id):
    if user_id is None:
        return False

    try:
        return int(user_id) in [
            int(admin_id)
            for admin_id in ADMIN_IDS
        ]
    except Exception:
        return False


# ==========================================================
# SAFE DISPLAY
# ==========================================================

def display_user(entry):
    name = (
        entry.get("display_name")
        or entry.get("username")
        or str(entry.get("user_id"))
    )

    if entry.get("username"):
        username = str(entry["username"]).lstrip("@")

        if username and username.lower() != str(name).lower():
            return f"{name} (@{username})"

    return str(name)


# ==========================================================
# FORMAT DATE
# ==========================================================

def format_expiration(expires_at):
    if not expires_at:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(expires_at)

        return dt.strftime(
            "%b %d, %Y at %I:%M %p"
        )

    except Exception:
        return str(expires_at)


# ==========================================================
# GET ACTIVE RAFFLE
# ==========================================================

def active_raffle():
    return get_active_raffle()


# ==========================================================
# START RAFFLE
#
# Command:
#
# /startraffle Prize | Price
#
# Example:
#
# /startraffle $100 Cash Prize | $5
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message
    query = update.callback_query

    if not user:
        return

    if not is_raffle_admin(user.id):
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

    # ------------------------------------------------------
    # Callback from admin panel
    # ------------------------------------------------------

    if query:
        await query.answer()

        await query.message.reply_text(
            "🎟️ <b>Start a Raffle</b>\n\n"
            "Use this format:\n\n"
            "<code>/startraffle Prize | Entry Price</code>\n\n"
            "Example:\n"
            "<code>/startraffle $100 Cash Prize | $5</code>\n\n"
            "The raffle will be created as <b>pending</b> "
            "until an admin approves it.",
            parse_mode=ParseMode.HTML,
        )
        return

    # ------------------------------------------------------
    # Command
    # ------------------------------------------------------

    if not message:
        return

    text = message.text or ""

    command_parts = text.split(
        " ",
        1,
    )

    if len(command_parts) < 2:
        await message.reply_text(
            "🎟️ <b>Start Raffle</b>\n\n"
            "Use:\n"
            "<code>/startraffle Prize | Entry Price</code>\n\n"
            "Example:\n"
            "<code>/startraffle $100 Cash Prize | $5</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    payload = command_parts[1].strip()

    if "|" not in payload:
        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Use:\n"
            "<code>/startraffle Prize | Entry Price</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    prize, price = payload.split(
        "|",
        1,
    )

    prize = prize.strip()
    price = price.strip()

    if not prize or not price:
        await message.reply_text(
            "⚠️ Prize and entry price are required."
        )
        return

    # ------------------------------------------------------
    # Prevent duplicate pending/active raffles
    # ------------------------------------------------------

    existing_active = get_active_raffle()

    if existing_active:
        await message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {existing_active['prize']}\n"
            f"💵 Entry: {existing_active['price']}"
        )
        return

    existing_pending = get_pending_raffle()

    if existing_pending:
        await message.reply_text(
            "⚠️ There is already a raffle waiting "
            "for admin approval.\n\n"
            f"🎁 Prize: {existing_pending['prize']}\n"
            f"💵 Entry: {existing_pending['price']}"
        )
        return

    # ------------------------------------------------------
    # Create pending raffle
    # ------------------------------------------------------

    expires = datetime.utcnow() + timedelta(
        days=int(RAFFLE_DURATION_DAYS or 7)
    )

    raffle_id = create_raffle(
        prize=prize,
        price=price,
        expires_at=expires.isoformat(),
    )

    logger.info(
        "Created pending raffle %s",
        raffle_id,
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve Raffle",
                    callback_data=f"raffle_approve_{raffle_id}",
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f"raffle_cancel_{raffle_id}",
                ),
            ]
        ]
    )

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "🎟️ <b>Raffle Created — Pending Approval</b>\n\n"
                f"🆔 Raffle ID: <code>{raffle_id}</code>\n"
                f"🎁 Prize: <b>{prize}</b>\n"
                f"💵 Entry Price: <b>{price}</b>\n"
                f"⏰ Expires: <b>{format_expiration(expires.isoformat())}</b>"
            ),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:
        logger.exception(
            "Could not send raffle approval message to admin."
        )

    # ------------------------------------------------------
    # Notify all admins
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=(
                    "🎟️ <b>Raffle Awaiting Approval</b>\n\n"
                    f"🆔 Raffle ID: <code>{raffle_id}</code>\n"
                    f"🎁 Prize: <b>{prize}</b>\n"
                    f"💵 Entry: <b>{price}</b>\n"
                    f"⏰ Expires: <b>{format_expiration(expires.isoformat())}</b>"
                ),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            logger.warning(
                "Could not notify admin %s.",
                admin_id,
            )


# ==========================================================
# PUBLISH RAFFLE
# ==========================================================

async def publish_raffle(
    raffle_id,
    context,
):
    raffle = get_raffle(raffle_id)

    if not raffle:
        return False

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ ENTER RAFFLE",
                    callback_data=f"enter_{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "💵 PAY WITH CASH APP",
                    callback_data=f"pay_cashapp_{raffle_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏦 PAY WITH ZELLE",
                    callback_data=f"pay_zelle_{raffle_id}",
                ),
            ],
        ]
    )

    text = (
        "🎟️ <b>MELANATED AZ FRIENDS RAFFLE</b>\n\n"
        f"🎁 <b>Prize:</b> {raffle['prize']}\n"
        f"💵 <b>Entry:</b> {raffle['price']}\n"
        f"⏰ <b>Ends:</b> {format_expiration(raffle['expires_at'])}\n\n"
        "👇 Tap below to enter.\n\n"
        "⚠️ Your entry remains pending until "
        "an admin verifies your payment."
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
# APPROVE RAFFLE CALLBACK
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

    raffle = get_raffle(raffle_id)

    if not raffle:
        await query.answer(
            "Raffle no longer exists.",
            show_alert=True,
        )
        return

    if raffle["status"] != "pending":
        await query.answer(
            f"Raffle is already {raffle['status']}.",
            show_alert=True,
        )
        return

    changed = approve_raffle(
        raffle_id
    )

    if not changed:
        await query.answer(
            "Raffle could not be approved.",
            show_alert=True,
        )
        return

    await query.answer(
        "Raffle approved!",
        show_alert=False,
    )

    await query.edit_message_text(
        (
            "✅ <b>RAFFLE APPROVED</b>\n\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n\n"
            "Publishing raffle to the group..."
        ),
        parse_mode=ParseMode.HTML,
    )

    published = await publish_raffle(
        raffle_id,
        context,
    )

    if published:
        try:
            await query.message.reply_text(
                "✅ Raffle is now live in the raffle group."
            )
        except Exception:
            pass
    else:
        logger.error(
            "Raffle %s approved but could not be published.",
            raffle_id,
        )


# ==========================================================
# CANCEL RAFFLE CALLBACK
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

    raffle = get_raffle(raffle_id)

    if not raffle:
        await query.answer(
            "Raffle not found.",
            show_alert=True,
        )
        return

    changed = cancel_pending_raffle(
        raffle_id
    )

    if not changed:
        await query.answer(
            "Raffle could not be cancelled.",
            show_alert=True,
        )
        return

    await query.answer(
        "Raffle cancelled.",
        show_alert=False,
    )

    await query.edit_message_text(
        (
            "❌ <b>RAFFLE CANCELLED</b>\n\n"
            f"🎁 Prize: {raffle['prize']}\n"
            f"💵 Entry: {raffle['price']}"
        ),
        parse_mode=ParseMode.HTML,
    )


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

    raffle = get_raffle(raffle_id)

    if not raffle or raffle["status"] != "active":
        await query.answer(
            "This raffle is no longer active.",
            show_alert=True,
        )
        return

    display_name = (
        user.full_name
        or user.username
        or str(user.id)
    )

    entry_id = add_raffle_entry(
        raffle_id=raffle_id,
        user_id=user.id,
        username=user.username,
        display_name=display_name,
        payment_method=None,
    )

    if entry_id is None:
        await query.answer(
            "You already have an entry for this raffle.",
            show_alert=True,
        )
        return

    await query.answer(
        "Entry submitted!",
        show_alert=True,
    )

    await query.message.reply_text(
        (
            "🎟️ <b>ENTRY SUBMITTED</b>\n\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry Price: <b>{raffle['price']}</b>\n"
            f"🆔 Entry: <code>{entry_id}</code>\n\n"
            "⚠️ Your entry is <b>PENDING</b> until "
            "an admin verifies your payment.\n\n"
            "Please complete payment using Cash App or Zelle."
        ),
        parse_mode=ParseMode.HTML,
    )

    # Notify admins immediately
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"approve_{entry_id}",
                ),
                InlineKeyboardButton(
                    "❌ DENY",
                    callback_data=f"deny_{entry_id}",
                ),
            ]
        ]
    )

    admin_text = (
        "🎟️ <b>NEW RAFFLE ENTRY</b>\n\n"
        f"🆔 Entry: <code>{entry_id}</code>\n"
        f"🎟️ Raffle: <code>{raffle_id}</code>\n"
        f"👤 Member: <b>{display_name}</b>\n"
        f"💵 Payment: <b>Not selected</b>\n\n"
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
                "Could not notify admin %s about entry.",
                admin_id,
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
        await query.answer(
            "Raffle is no longer active.",
            show_alert=True,
        )
        return

    entries = get_raffle_entries(
        raffle_id
    )

    entry = None

    for item in entries:
        if (
            int(item["user_id"]) == int(user.id)
            and item["status"] == "pending"
        ):
            entry = item
            break

    if not entry:
        await query.answer(
            "Enter the raffle first.",
            show_alert=True,
        )
        return

    payment = str(method).lower()

    if payment == "cashapp":
        payment_text = (
            "💵 <b>CASH APP</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{CASHAPP_TAG}</code>\n\n"
            f"{CASHAPP_URL or ''}"
        )

    else:
        payment_text = (
            "🏦 <b>ZELLE</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{ZELLE_PHONE}</code>"
        )

    await query.answer()

    await query.message.reply_text(
        payment_text
        + "\n\n"
        "After payment, your entry remains pending "
        "until an admin verifies it.",
        parse_mode=ParseMode.HTML,
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
            f"Entry is already {entry['status']}.",
            show_alert=True,
        )
        return

    changed = approve_entry(
        entry_id,
        user.id,
    )

    if not changed:
        await query.answer(
            "Entry could not be approved.",
            show_alert=True,
        )
        return

    await query.answer(
        "Entry approved!",
        show_alert=False,
    )

    member_name = display_user(entry)

    await query.edit_message_text(
        (
            "✅ <b>ENTRY APPROVED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"👤 Member: <b>{member_name}</b>\n"
            f"💳 Payment: <b>{entry.get('payment_method') or 'Verified'}</b>\n\n"
            f"Approved by admin <code>{user.id}</code>."
        ),
        parse_mode=ParseMode.HTML,
    )

    # Notify entrant
    try:
        await context.bot.send_message(
            chat_id=int(entry["user_id"]),
            text=(
                "🎉 <b>YOUR RAFFLE ENTRY WAS APPROVED!</b>\n\n"
                f"🎁 Prize: <b>{entry.get('prize', 'Raffle')}</b>\n"
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
            f"Entry is already {entry['status']}.",
            show_alert=True,
        )
        return

    changed = deny_entry(
        entry_id,
        user.id,
    )

    if not changed:
        await query.answer(
            "Entry could not be denied.",
            show_alert=True,
        )
        return

    await query.answer(
        "Entry denied.",
        show_alert=False,
    )

    member_name = display_user(entry)

    await query.edit_message_text(
        (
            "❌ <b>ENTRY DENIED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"👤 Member: <b>{member_name}</b>\n\n"
            f"Denied by admin <code>{user.id}</code>."
        ),
        parse_mode=ParseMode.HTML,
    )

    # Notify entrant
    try:
        await context.bot.send_message(
            chat_id=int(entry["user_id"]),
            text=(
                "⚠️ <b>RAFFLE ENTRY UPDATE</b>\n\n"
                f"Your entry <code>{entry_id}</code> "
                "was not approved.\n\n"
                "Please contact an admin if you believe "
                "this was done in error."
            ),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError:
        logger.info(
            "Could not notify entrant %s.",
            entry["user_id"],
        )


# ==========================================================
# RAFFLE CALLBACK ROUTER
#
# This function is called by bot.py.
# ==========================================================

async def raffle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Processing raffle callback: %s",
        data,
    )

    # ------------------------------------------------------
    # APPROVE RAFFLE
    # ------------------------------------------------------

    if data.startswith("raffle_approve_"):
        raffle_id = data.replace(
            "raffle_approve_",
            "",
            1,
        )

        if raffle_id.isdigit():
            await approve_raffle_callback(
                update,
                context,
                int(raffle_id),
            )
        return

    # ------------------------------------------------------
    # CANCEL RAFFLE
    # ------------------------------------------------------

    if data.startswith("raffle_cancel_"):
        raffle_id = data.replace(
            "raffle_cancel_",
            "",
            1,
        )

        if raffle_id.isdigit():
            await cancel_raffle_callback(
                update,
                context,
                int(raffle_id),
            )
        return

    # ------------------------------------------------------
    # APPROVE ENTRY
    # ------------------------------------------------------

    if data.startswith("approve_"):
        entry_id = data.replace(
            "approve_",
            "",
            1,
        )

        if entry_id.isdigit():
            await approve_entry_callback(
                update,
                context,
                int(entry_id),
            )
        return

    # ------------------------------------------------------
    # DENY ENTRY
    # ------------------------------------------------------

    if data.startswith("deny_"):
        entry_id = data.replace(
            "deny_",
            "",
            1,
        )

        if entry_id.isdigit():
            await deny_entry_callback(
                update,
                context,
                int(entry_id),
            )
        return

    # ------------------------------------------------------
    # ENTER RAFFLE
    # ------------------------------------------------------

    if data.startswith("enter_"):
        raffle_id = data.replace(
            "enter_",
            "",
            1,
        )

        if raffle_id.isdigit():
            await enter_raffle(
                update,
                context,
                int(raffle_id),
            )
        return

    # ------------------------------------------------------
    # CASH APP
    # ------------------------------------------------------

    if data.startswith("pay_cashapp_"):
        raffle_id = data.replace(
            "pay_cashapp_",
            "",
            1,
        )

        if raffle_id.isdigit():
            await payment_method(
                update,
                context,
                int(raffle_id),
                "cashapp",
            )
        return

    # ------------------------------------------------------
    # ZELLE
    # ------------------------------------------------------

    if data.startswith("pay_zelle_"):
        raffle_id = data.replace(
            "pay_zelle_",
            "",
            1,
        )

        if raffle_id.isdigit():
            await payment_method(
                update,
                context,
                int(raffle_id),
                "zelle",
            )
        return

    # ------------------------------------------------------
    # GENERIC PAYMENT CALLBACKS
    # ------------------------------------------------------

    if data.startswith("payment_"):
        await query.answer()
        return

    # ------------------------------------------------------
    # UNKNOWN RAFFLE CALLBACK
    # ------------------------------------------------------

    logger.warning(
        "Unknown raffle callback: %s",
        data,
    )

    await query.answer()


# ==========================================================
# RAFFLE STATUS
# ==========================================================

async def raffle_status(
    update,
    context,
):
    query = update.callback_query
    message = update.effective_message

    if query:
        user = update.effective_user

        if not user or not is_raffle_admin(user.id):
            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )
            return

        await query.answer()
        target = query.message

    else:
        target = message

    raffle = get_active_raffle()

    if not raffle:
        text = (
            "🎟️ <b>RAFFLE STATUS</b>\n\n"
            "There is currently no active raffle."
        )
    else:
        entries = get_approved_entries(
            raffle["id"]
        )

        pending = get_pending_entries(
            raffle["id"]
        )

        text = (
            "🎟️ <b>RAFFLE STATUS</b>\n\n"
            f"🆔 ID: <code>{raffle['id']}</code>\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n"
            f"⏰ Ends: <b>{format_expiration(raffle['expires_at'])}</b>\n\n"
            f"✅ Approved Entries: <b>{len(entries)}</b>\n"
            f"⏳ Pending Entries: <b>{len(pending)}</b>"
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

    if not user or not is_raffle_admin(user.id):
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

        if not entries:
            text = (
                "🎟️ <b>RAFFLE ENTRIES</b>\n\n"
                "No approved entries yet."
            )

        else:
            lines = [
                "🎟️ <b>APPROVED ENTRIES</b>",
                "",
            ]

            for index, entry in enumerate(
                entries,
                start=1,
            ):
                lines.append(
                    f"{index}. {display_user(entry)} "
                    f"(Entry #{entry['id']})"
                )

            text = "\n".join(lines)

    if query:
        await query.answer()
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    elif message:
        await message.reply_text(
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

    if not user or not is_raffle_admin(user.id):
        if query:
            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )
        return

    pending = get_pending_entries()

    if query:
        await query.answer()

    if not pending:
        text = (
            "⏳ <b>PENDING RAFFLE ENTRIES</b>\n\n"
            "There are no pending entries."
        )

        if query:
            await query.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
            )
        elif message:
            await message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
            )

        return

    for entry in pending:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ APPROVE",
                        callback_data=f"approve_{entry['id']}",
                    ),
                    InlineKeyboardButton(
                        "❌ DENY",
                        callback_data=f"deny_{entry['id']}",
                    ),
                ]
            ]
        )

        text = (
            "⏳ <b>PENDING RAFFLE ENTRY</b>\n\n"
            f"🆔 Entry: <code>{entry['id']}</code>\n"
            f"🎟️ Raffle: <code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: <b>{entry.get('prize', 'Unknown')}</b>\n"
            f"💵 Price: <b>{entry.get('price', 'Unknown')}</b>\n"
            f"👤 Member: <b>{display_user(entry)}</b>\n"
            f"💳 Payment: <b>{entry.get('payment_method') or 'Not selected'}</b>\n"
            f"📅 Submitted: {entry.get('created_at', 'Unknown')}\n\n"
            "Choose an action:"
        )

        try:
            if query:
                await query.message.reply_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            elif message:
                await message.reply_text(
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
# PAID / COMPLETED ENTRIES
# ==========================================================

async def paid_entry(
    update,
    context,
):
    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if not user or not is_raffle_admin(user.id):
        if query:
            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )
        return

    raffle = get_active_raffle()

    if not raffle:
        text = (
            "💰 <b>APPROVED / PAID ENTRIES</b>\n\n"
            "No active raffle."
        )
    else:
        entries = get_approved_entries(
            raffle["id"]
        )

        if not entries:
            text = (
                "💰 <b>APPROVED / PAID ENTRIES</b>\n\n"
                "No approved entries yet."
            )
        else:
            lines = [
                "💰 <b>APPROVED / PAID ENTRIES</b>",
                "",
            ]

            for entry in entries:
                lines.append(
                    f"#{entry['id']} — "
                    f"{display_user(entry)}"
                )

            text = "\n".join(lines)

    if query:
        await query.answer()
        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    elif message:
        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )


# ==========================================================
# CANCEL RAFFLE COMMAND
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
            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )
        return

    raffle = get_active_raffle()

    if not raffle:
        raffle = get_pending_raffle()

    if not raffle:
        text = (
            "⚠️ There is no raffle to cancel."
        )

        if query:
            await query.answer(
                "No raffle to cancel.",
                show_alert=True,
            )
            await query.message.reply_text(text)
        elif message:
            await message.reply_text(text)

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
            "Raffle cancelled.",
            show_alert=False,
        )

        await query.message.reply_text(
            "❌ Raffle cancelled."
        )

    elif message:
        await message.reply_text(
            "❌ Raffle cancelled."
        )

    logger.info(
        "Raffle %s cancelled: %s",
        raffle["id"],
        changed,
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

    if not user or not is_raffle_admin(user.id):
        if query:
            await query.answer(
                "⛔ Admins only.",
                show_alert=True,
            )
        return

    raffle = get_active_raffle()

    if not raffle:
        text = (
            "⚠️ There is no active raffle."
        )

        if query:
            await query.answer(
                "No active raffle.",
                show_alert=True,
            )
            await query.message.reply_text(text)
        elif message:
            await message.reply_text(text)

        return

    entries = get_approved_entries(
        raffle["id"]
    )

    if not entries:
        text = (
            "⚠️ There are no approved entries."
        )

        if query:
            await query.answer(
                "No approved entries.",
                show_alert=True,
            )
            await query.message.reply_text(text)
        elif message:
            await message.reply_text(text)

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
        f"🏆 Winner: <b>{display_user(winner)}</b>\n"
        f"🆔 Entry: <code>{winner['id']}</code>\n\n"
        "🎉 Congratulations!"
    )

    if query:
        await query.answer(
            "Winner selected!",
            show_alert=False,
        )

        await query.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    elif message:
        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )


# ==========================================================
# END raffle.py
# ==========================================================
