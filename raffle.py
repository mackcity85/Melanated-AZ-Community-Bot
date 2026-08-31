# ==========================================================
# Melanated AZ Bot - raffle.py
# COMPLETE DROP-IN RAFFLE SYSTEM
#
# Includes:
#   - Raffle creation
#   - Raffle approval
#   - Raffle cancellation
#   - Raffle publishing
#   - Member entry
#   - Cash App / Zelle
#   - Admin approval / denial
#   - Manual admin entries
#   - Approved entry list
#   - Pending entry list
#   - Winner drawing
#
# Critical fix:
# raffle_callback() is the ONLY owner of raffle callbacks.
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
# DISPLAY USER
# ==========================================================

def display_user(entry):

    name = (
        entry.get("display_name")
        or entry.get("username")
        or str(entry.get("user_id"))
    )

    username = str(
        entry.get("username") or ""
    ).lstrip("@")

    if (
        username
        and username.lower()
        != str(name).lower()
    ):

        return f"{name} (@{username})"

    return str(name)


# ==========================================================
# FORMAT EXPIRATION
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

    if (
        not user
        or not is_raffle_admin(user.id)
    ):

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
            "Example:\n"
            "<code>/startraffle "
            "$100 Cash Prize | $5</code>",
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
            "<code>/startraffle "
            "Prize | Entry Price</code>",
            parse_mode=ParseMode.HTML,
        )

        return

    payload = parts[1].strip()

    if "|" not in payload:

        await message.reply_text(
            "⚠️ Invalid format.\n\n"
            "Use:\n"
            "<code>/startraffle "
            "Prize | Entry Price</code>",
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

    text = (
        "🎟️ <b>RAFFLE AWAITING APPROVAL</b>\n\n"
        f"🆔 Raffle: <code>{raffle_id}</code>\n"
        f"🎁 Prize: <b>{prize}</b>\n"
        f"💵 Entry: <b>{price}</b>\n"
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
        f"🎁 <b>Prize:</b> "
        f"{raffle['prize']}\n"
        f"💵 <b>Entry:</b> "
        f"{raffle['price']}\n"
        f"⏰ <b>Ends:</b> "
        f"{format_expiration(raffle['expires_at'])}\n\n"
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
            "✅ <b>RAFFLE APPROVED</b>\n\n"
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
                "✅ Raffle is now live "
                "in the raffle group."
            )

        except Exception:

            pass

    else:

        logger.error(
            "Raffle %s approved but "
            "publication failed.",
            raffle_id,
        )


# ==========================================================
# CANCEL PENDING RAFFLE CALLBACK
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
            "❌ <b>RAFFLE CANCELLED</b>\n\n"
            f"🎁 {raffle['prize']}\n"
            f"💵 {raffle['price']}",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        pass


# ==========================================================
# MEMBER ENTERS RAFFLE
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

    if (
        not raffle
        or raffle["status"] != "active"
    ):

        await query.answer(
            "This raffle is no longer active.",
            show_alert=True,
        )

        return

    name = (
        user.full_name
        or user.username
        or str(user.id)
    )

    entry_id = add_raffle_entry(
        raffle_id,
        user.id,
        user.username,
        name,
        None,
    )

    if entry_id is None:

        await query.answer(
            "You already have an entry "
            "for this raffle.",
            show_alert=True,
        )

        return

    await query.answer(
        "Entry submitted!",
        show_alert=True,
    )

    await query.message.reply_text(
        "🎟️ <b>ENTRY SUBMITTED</b>\n\n"
        f"🎁 Prize: <b>{raffle['prize']}</b>\n"
        f"💵 Entry Price: <b>{raffle['price']}</b>\n"
        f"🆔 Entry: <code>{entry_id}</code>\n\n"
        "⚠️ Your entry is <b>PENDING</b> until "
        "an admin verifies payment.",
        parse_mode=ParseMode.HTML,
    )

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
        f"👤 Member: <b>{name}</b>\n"
        "💳 Payment: <b>Not selected</b>\n\n"
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
                "Could not notify admin %s.",
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

    raffle = get_raffle(
        raffle_id
    )

    if (
        not raffle
        or raffle["status"] != "active"
    ):

        await query.answer(
            "Raffle is no longer active.",
            show_alert=True,
        )

        return

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

    if method == "cashapp":

        body = (
            "💵 <b>CASH APP</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{CASHAPP_TAG}</code>\n\n"
            f"{CASHAPP_URL or ''}"
        )

    else:

        body = (
            "🏦 <b>ZELLE</b>\n\n"
            f"Send <b>{raffle['price']}</b> to:\n"
            f"<code>{ZELLE_PHONE}</code>"
        )

    await query.answer()

    await query.message.reply_text(
        body
        + "\n\nAfter payment, your entry remains "
        "pending until an admin verifies it.",
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
        "ENTRY APPROVED | entry=%s | "
        "raffle=%s | admin=%s",
        entry_id,
        entry["raffle_id"],
        user.id,
    )

    await query.answer(
        "✅ Entry approved!"
    )

    try:

        await query.edit_message_text(
            "✅ <b>ENTRY APPROVED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: "
            f"<code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: "
            f"<b>{entry.get('prize') or 'Raffle'}</b>\n"
            f"👤 Member: "
            f"<b>{display_user(entry)}</b>\n"
            f"💳 Payment: "
            f"<b>{entry.get('payment_method') or 'Verified'}</b>\n\n"
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
                f"🎁 Prize: "
                f"<b>{entry.get('prize') or 'Raffle'}</b>\n"
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
            "❌ <b>ENTRY DENIED</b>\n\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"🎟️ Raffle: "
            f"<code>{entry['raffle_id']}</code>\n"
            f"👤 Member: "
            f"<b>{display_user(entry)}</b>\n\n"
            f"Denied by admin "
            f"<code>{user.id}</code>.",
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        pass


# ==========================================================
# MANUAL ADMIN RAFFLE ENTRY
# ==========================================================

async def manual_raffle_entry(
    update,
    context,
    member_user_id,
):

    message = update.effective_message
    admin = update.effective_user

    if not admin or not is_raffle_admin(
        admin.id
    ):

        if message:

            await message.reply_text(
                "⛔ Admins only."
            )

        return False

    raffle = get_active_raffle()

    if not raffle:

        if message:

            await message.reply_text(
                "⚠️ There is no active raffle.\n\n"
                "Start and approve a raffle first."
            )

        return False

    # ------------------------------------------------------
    # Get member information from Telegram.
    # ------------------------------------------------------

    username = None
    display_name = None

    try:

        member = await context.bot.get_chat(
            chat_id=int(member_user_id)
        )

        username = getattr(
            member,
            "username",
            None,
        )

        display_name = getattr(
            member,
            "full_name",
            None,
        )

        if not display_name:

            display_name = (
                member.first_name
                if getattr(
                    member,
                    "first_name",
                    None,
                )
                else None
            )

    except TelegramError:

        logger.info(
            "Could not retrieve Telegram profile "
            "for user %s.",
            member_user_id,
        )

    if not display_name:

        display_name = str(
            member_user_id
        )

    # ------------------------------------------------------
    # Add as pending first.
    #
    # This uses the exact same database entry system
    # as normal raffle entries.
    # ------------------------------------------------------

    entry_id = add_raffle_entry(
        raffle["id"],
        int(member_user_id),
        username,
        display_name,
        None,
    )

    if entry_id is None:

        if message:

            await message.reply_text(
                "⚠️ That member already has "
                "an entry in this raffle.\n\n"
                f"👤 {display_name}\n"
                f"🆔 User ID: `{member_user_id}`",
                parse_mode=ParseMode.Markdown,
            )

        return False

    # ------------------------------------------------------
    # Immediately approve the manually added entry.
    # ------------------------------------------------------

    changed = approve_entry(
        entry_id,
        admin.id,
    )

    if not changed:

        logger.error(
            "Manual entry %s was created but "
            "could not be approved.",
            entry_id,
        )

        if message:

            await message.reply_text(
                "⚠️ The manual entry was created, "
                "but I could not approve it.\n\n"
                f"Entry: `{entry_id}`\n"
                "Check the Render logs.",
                parse_mode=ParseMode.Markdown,
            )

        return False

    logger.info(
        "MANUAL RAFFLE ENTRY | "
        "entry=%s | raffle=%s | member=%s | admin=%s",
        entry_id,
        raffle["id"],
        member_user_id,
        admin.id,
    )

    if message:

        await message.reply_text(
            "✅ <b>MANUAL ENTRY ADDED</b>\n\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n"
            f"🆔 Entry: <code>{entry_id}</code>\n"
            f"👤 Member: <b>{display_name}</b>\n"
            f"🆔 User ID: "
            f"<code>{member_user_id}</code>\n\n"
            "✅ Status: <b>APPROVED</b>\n"
            "👑 Added manually by an admin.",
            parse_mode=ParseMode.HTML,
        )

    # ------------------------------------------------------
    # Notify the member if Telegram allows the bot to DM.
    # ------------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=int(member_user_id),
            text=(
                "🎟️ <b>YOU HAVE BEEN ADDED "
                "TO THE MELANATED AZ FRIENDS RAFFLE!</b>\n\n"
                f"🎁 Prize: "
                f"<b>{raffle['prize']}</b>\n"
                f"🆔 Entry: "
                f"<code>{entry_id}</code>\n\n"
                "Your entry has been approved. "
                "Good luck! 🍀"
            ),
            parse_mode=ParseMode.HTML,
        )

    except TelegramError:

        logger.info(
            "Could not DM manually added member %s.",
            member_user_id,
        )

    return True


# ==========================================================
# SINGLE RAFFLE CALLBACK ROUTER
# ==========================================================

async def raffle_callback(
    update,
    context,
):

    """
    Single callback router for ALL raffle callbacks.
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
    # RAFFLE APPROVAL
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
    # RAFFLE CANCEL
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
    # ENTRY APPROVAL
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
    # ENTRY DENIAL
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
    # ENTER
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

    if (
        not user
        or not is_raffle_admin(user.id)
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

        text = (
            "🎟️ <b>RAFFLE STATUS</b>\n\n"
            f"🆔 ID: <code>{raffle['id']}</code>\n"
            f"🎁 Prize: <b>{raffle['prize']}</b>\n"
            f"💵 Entry: <b>{raffle['price']}</b>\n"
            f"⏰ Ends: <b>"
            f"{format_expiration(raffle['expires_at'])}"
            f"</b>\n\n"
            f"✅ Approved Entries: "
            f"<b>{len(approved)}</b>\n"
            f"⏳ Pending Entries: "
            f"<b>{len(pending)}</b>"
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
# APPROVED ENTRIES
# ==========================================================

async def raffle_entries(
    update,
    context,
):

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if (
        not user
        or not is_raffle_admin(user.id)
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

        text = (
            "🎟️ <b>APPROVED ENTRIES</b>\n\n"
            + (
                "\n".join(
                    f"{i}. "
                    f"{display_user(e)} "
                    f"(Entry #{e['id']})"
                    for i, e in enumerate(
                        entries,
                        1,
                    )
                )
                if entries
                else "No approved entries yet."
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

    if (
        not user
        or not is_raffle_admin(user.id)
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

        text = (
            "⏳ <b>PENDING RAFFLE ENTRY</b>\n\n"
            f"🆔 Entry: "
            f"<code>{entry['id']}</code>\n"
            f"🎟️ Raffle: "
            f"<code>{entry['raffle_id']}</code>\n"
            f"🎁 Prize: "
            f"<b>{entry.get('prize') or 'Unknown'}</b>\n"
            f"💵 Price: "
            f"<b>{entry.get('price') or 'Unknown'}</b>\n"
            f"👤 Member: "
            f"<b>{display_user(entry)}</b>\n"
            f"💳 Payment: "
            f"<b>{entry.get('payment_method') or 'Not selected'}</b>\n\n"
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

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if (
        not user
        or not is_raffle_admin(user.id)
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
            "✅ <b>COMPLETED PAYMENTS</b>\n\n"
            "No active raffle."
        )

    else:

        entries = get_approved_entries(
            raffle["id"]
        )

        if not entries:

            text = (
                "✅ <b>COMPLETED PAYMENTS</b>\n\n"
                "No approved entries yet."
            )

        else:

            lines = [
                "✅ <b>COMPLETED PAYMENTS</b>",
                "",
                f"Total approved: "
                f"<b>{len(entries)}</b>",
                "",
            ]

            for i, entry in enumerate(
                entries,
                1,
            ):

                lines.append(
                    f"{i}. "
                    f"{display_user(entry)} "
                    f"— Entry #{entry['id']}"
                )

            text = "\n".join(
                lines
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
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle(
    update,
    context,
):

    query = update.callback_query
    message = update.effective_message
    user = update.effective_user

    if (
        not user
        or not is_raffle_admin(user.id)
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
            else "⚠️ Raffle could not be cancelled."
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

    if (
        not user
        or not is_raffle_admin(user.id)
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
        f"🏆 Winner: "
        f"<b>{display_user(winner)}</b>\n"
        f"🆔 Entry: "
        f"<code>{winner['id']}</code>\n\n"
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
