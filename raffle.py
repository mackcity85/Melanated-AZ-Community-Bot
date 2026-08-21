# ==========================================================
# Melanated AZ Bot
# raffle.py
# ==========================================================

import logging
import random
from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS,
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
    set_message_id,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle,
)

import os

logger = logging.getLogger(__name__)

RAFFLE_CHAT_ID = os.getenv("RAFFLE_CHAT_ID")


def is_admin(user_id):
    return user_id in ADMIN_IDS


def admin_only(update):
    return (
        update.effective_user
        and is_admin(update.effective_user.id)
    )


def admin_approval_keyboard(raffle_id):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ APPROVE RAFFLE",
                callback_data=f"raffleapprove_{raffle_id}"
            ),
            InlineKeyboardButton(
                "❌ CANCEL",
                callback_data=f"rafflecancel_{raffle_id}"
            ),
        ]
    ])


def raffle_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎟️ ENTER RAFFLE",
                callback_data="raffle_enter"
            )
        ],
        [
            InlineKeyboardButton(
                "💵 CASH APP",
                callback_data="raffle_paid"
            ),
            InlineKeyboardButton(
                "💳 ZELLE",
                callback_data="raffle_zelle"
            )
        ]
    ])


def get_display_name(user):

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


def format_price(price):

    if float(price).is_integer():
        return f"${int(price)}"

    return f"${price:.2f}"


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update,
    context
):

    if not admin_only(update):
        await update.message.reply_text(
            "❌ Admins only."
        )
        return

    if not context.args or len(context.args) < 2:

        await update.message.reply_text(
            "Usage:\n\n"
            "/startraffle PRICE PRIZE\n\n"
            "Example:\n"
            "/startraffle 10 $100 Cash Prize"
        )
        return

    try:
        price = float(context.args[0].replace("$", ""))
    except ValueError:

        await update.message.reply_text(
            "❌ The first value must be the entry price.\n\n"
            "Example:\n"
            "/startraffle 10 $100 Cash Prize"
        )
        return

    prize = " ".join(context.args[1:])

    if price <= 0:
        await update.message.reply_text(
            "❌ Entry price must be greater than $0."
        )
        return

    if get_active_raffle():
        await update.message.reply_text(
            "⚠️ There is already an active raffle."
        )
        return

    if get_pending_raffle():
        await update.message.reply_text(
            "⚠️ There is already a raffle waiting for admin approval."
        )
        return

    raffle_id = create_raffle(
        prize,
        price
    )

    text = (
        "🎟️ **RAFFLE APPROVAL REQUIRED**\n\n"
        "🖤 **Melanated AZ Friends Raffle**\n\n"
        f"🎁 **Prize:** {prize}\n"
        f"💵 **Entry:** {format_price(price)}\n"
        f"🆔 **Raffle #:** {raffle_id}\n\n"
        "This is a private raffle for the Melanated AZ group.\n\n"
        "Approve this raffle to post it in the group."
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=admin_approval_keyboard(raffle_id),
                parse_mode="Markdown"
            )

        except Exception:
            logger.exception(
                "Unable to notify admin %s",
                admin_id
            )

    await update.message.reply_text(
        f"✅ Raffle #{raffle_id} created.\n\n"
        f"🎁 Prize: {prize}\n"
        f"💵 Entry: {format_price(price)}\n\n"
        "⏳ Waiting for admin approval before posting."
    )


# ==========================================================
# APPROVE RAFFLE
# ==========================================================

async def approve_raffle_button(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(query.from_user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )
        return

    await query.answer()

    try:
        raffle_id = int(
            query.data.split("_", 1)[1]
        )
    except ValueError:
        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await query.message.reply_text(
            "❌ Raffle not found."
        )
        return

    expires_at = (
        datetime.utcnow()
        + timedelta(days=7)
    ).isoformat()

    if not approve_raffle(
        raffle_id,
        expires_at
    ):

        await query.message.reply_text(
            "⚠️ Raffle could not be approved."
        )
        return

    if not RAFFLE_CHAT_ID:

        await query.message.reply_text(
            "⚠️ Raffle approved, but RAFFLE_CHAT_ID "
            "is not configured in Render."
        )
        return

    raffle = get_raffle(raffle_id)

    text = (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry Price:** {format_price(raffle['price'])}\n\n"
        "🔒 **Private raffle for Melanated AZ friends.**\n\n"
        "⏳ **Raffle closes in 7 days.**\n\n"
        "Tap **ENTER RAFFLE** below to participate.\n\n"
        "Payment must be completed and approved by an admin "
        "before your entry becomes active."
    )

    try:

        message = await context.bot.send_message(
            chat_id=RAFFLE_CHAT_ID,
            text=text,
            reply_markup=raffle_keyboard(),
            parse_mode="Markdown"
        )

        set_message_id(
            raffle_id,
            message.message_id
        )

        await query.message.reply_text(
            f"✅ Raffle #{raffle_id} approved and posted "
            "to the Melanated AZ group."
        )

    except Exception:

        logger.exception(
            "Unable to post raffle to group."
        )

        await query.message.reply_text(
            "❌ Raffle was approved, but I could not post "
            "it to the raffle group.\n\n"
            "Check RAFFLE_CHAT_ID and make sure the bot "
            "is in the group."
        )


# ==========================================================
# CANCEL RAFFLE APPROVAL
# ==========================================================

async def cancel_raffle_button(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(query.from_user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )
        return

    await query.answer()

    try:
        raffle_id = int(
            query.data.split("_", 1)[1]
        )
    except ValueError:
        return

    if cancel_pending_raffle(raffle_id):

        await query.message.reply_text(
            f"❌ Raffle #{raffle_id} cancelled."
        )

    else:

        await query.message.reply_text(
            "⚠️ Raffle could not be cancelled."
        )


# ==========================================================
# ENTER BUTTON
# ==========================================================

async def enter_button(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    await query.message.reply_text(
        "🎟️ **ENTER MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {format_price(raffle['price'])}\n\n"
        "Choose how you would like to pay:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💵 Cash App",
                    callback_data="raffle_paid"
                ),
                InlineKeyboardButton(
                    "💳 Zelle",
                    callback_data="raffle_zelle"
                )
            ]
        ]),
        parse_mode="Markdown"
    )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    user = query.from_user

    payment_method = (
        "Zelle"
        if query.data == "raffle_zelle"
        else "Cash App"
    )

    entry_id = add_raffle_entry(
        raffle["id"],
        user.id,
        user.username,
        get_display_name(user),
        payment_method
    )

    if entry_id is None:

        await query.message.reply_text(
            "⚠️ You already have a pending or approved "
            "entry for this raffle."
        )
        return

    if payment_method == "Cash App":

        payment = (
            "💵 **Cash App**\n"
            f"Send **{format_price(raffle['price'])}** to "
            f"`{CASHAPP_TAG}`"
        )

        if CASHAPP_URL:
            payment += f"\n\n🔗 {CASHAPP_URL}"

    else:

        payment = (
            "💳 **Zelle**\n"
            f"Send **{format_price(raffle['price'])}** to "
            f"`{ZELLE_PHONE}`"
        )

    await query.message.reply_text(
        "🎟️ **ENTRY CREATED**\n\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry Price: {format_price(raffle['price'])}\n"
        f"🆔 Entry #: {entry_id}\n\n"
        f"{payment}\n\n"
        "After payment is sent, an admin will verify it.\n\n"
        "⚠️ Your entry is NOT active until approved.",
        parse_mode="Markdown"
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **PENDING RAFFLE PAYMENT**\n\n"
                    f"🎁 Prize: {raffle['prize']}\n"
                    f"💵 Amount: {format_price(raffle['price'])}\n"
                    f"🆔 Entry #: {entry_id}\n"
                    f"👤 {get_display_name(user)}\n"
                    f"💳 Payment: {payment_method}\n\n"
                    "Verify payment before approving."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "✅ Approve",
                            callback_data=f"approve_{entry_id}"
                        ),
                        InlineKeyboardButton(
                            "❌ Deny",
                            callback_data=f"deny_{entry_id}"
                        )
                    ]
                ]),
                parse_mode="Markdown"
            )

        except Exception:
            logger.exception(
                "Unable to notify admin."
            )


# ==========================================================
# ADMIN ENTRY APPROVAL
# ==========================================================

async def admin_payment_button(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(query.from_user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True
        )
        return

    await query.answer()

    action, entry_text = query.data.split("_", 1)
    entry_id = int(entry_text)

    entry = get_entry(entry_id)

    if not entry:

        await query.message.reply_text(
            "❌ Entry not found."
        )
        return

    if action == "approve":

        success = approve_entry(
            entry_id,
            query.from_user.id
        )

        if success:

            await query.message.reply_text(
                f"✅ Entry #{entry_id} approved."
            )

            try:

                raffle = get_raffle(
                    entry["raffle_id"]
                )

                await context.bot.send_message(
                    chat_id=entry["user_id"],
                    text=(
                        "🎉 **RAFFLE ENTRY APPROVED!**\n\n"
                        f"🎁 Prize: {raffle['prize']}\n"
                        f"💵 Entry: {format_price(raffle['price'])}\n"
                        f"🆔 Entry #: {entry_id}\n\n"
                        "Good luck! 🍀"
                    ),
                    parse_mode="Markdown"
                )

            except Exception:
                logger.exception(
                    "Unable to notify participant."
                )

        else:

            await query.message.reply_text(
                "⚠️ Entry was already processed."
            )

    elif action == "deny":

        success = deny_entry(
            entry_id,
            query.from_user.id
        )

        await query.message.reply_text(
            f"❌ Entry #{entry_id} denied."
            if success
            else "⚠️ Entry was already processed."
        )


# ==========================================================
# COMMANDS
# ==========================================================

async def enter_raffle(update, context):

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ There is no active raffle."
        )
        return

    await update.message.reply_text(
        "🎟️ **ENTER RAFFLE**",
        reply_markup=raffle_keyboard(),
        parse_mode="Markdown"
    )


async def pending_entries(update, context):

    if not admin_only(update):
        return

    entries = get_pending_entries()

    if not entries:

        await update.message.reply_text(
            "✅ No pending payments."
        )
        return

    for entry in entries:

        await update.message.reply_text(
            f"💰 **Pending Entry #{entry['id']}**\n\n"
            f"👤 {entry['display_name']}\n"
            f"💳 {entry['payment_method']}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Approve",
                        callback_data=f"approve_{entry['id']}"
                    ),
                    InlineKeyboardButton(
                        "❌ Deny",
                        callback_data=f"deny_{entry['id']}"
                    )
                ]
            ]),
            parse_mode="Markdown"
        )


async def raffle_status(update, context):

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    entries = get_approved_entries(
        raffle["id"]
    )

    await update.message.reply_text(
        "🎟️ **RAFFLE STATUS**\n\n"
        f"🆔 Raffle #: {raffle['id']}\n"
        f"🎁 Prize: {raffle['prize']}\n"
        f"💵 Entry: {format_price(raffle['price'])}\n"
        f"👥 Approved Entries: {len(entries)}\n"
        f"⏳ Expires: {raffle['expires_at']}",
        parse_mode="Markdown"
    )


async def raffle_entries(update, context):

    if not admin_only(update):
        return

    raffle = get_active_raffle()

    if not raffle:
        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    entries = get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await update.message.reply_text(
            "No approved entries yet."
        )
        return

    lines = [
        "🎟️ **APPROVED ENTRIES**",
        ""
    ]

    for entry in entries:

        lines.append(
            f"#{entry['id']} — {entry['display_name']}"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


async def draw_raffle(update, context):

    if not admin_only(update):
        return

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    entries = get_approved_entries(
        raffle["id"]
    )

    if not entries:

        await update.message.reply_text(
            "❌ No approved entries."
        )
        return

    winner = random.choice(entries)

    close_raffle(
        raffle["id"]
    )

    await update.message.reply_text(
        "🎉 **RAFFLE WINNER!** 🎉\n\n"
        f"🎁 Prize: **{raffle['prize']}**\n"
        f"🏆 Winner: **{winner['display_name']}**\n"
        f"🆔 Entry #: {winner['id']}\n\n"
        "Congratulations! 🍀",
        parse_mode="Markdown"
    )


async def cancel_raffle(update, context):

    if not admin_only(update):
        return

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )
        return

    close_raffle(
        raffle["id"]
    )

    await update.message.reply_text(
        f"🛑 Raffle #{raffle['id']} cancelled."
    )


async def bonus_entry(update, context):

    if admin_only(update):

        await update.message.reply_text(
            "ℹ️ Bonus entries are not enabled."
        )


async def remove_raffle_entry(update, context):

    if not admin_only(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /removeentry ENTRY_ID"
        )
        return

    try:
        entry_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )
        return

    if remove_entry(entry_id):

        await update.message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )


async def approve_raffle_entry(update, context):

    if not admin_only(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /approveentry ENTRY_ID"
        )
        return

    entry_id = int(context.args[0])

    if approve_entry(
        entry_id,
        update.effective_user.id
    ):

        await update.message.reply_text(
            f"✅ Entry #{entry_id} approved."
        )

    else:

        await update.message.reply_text(
            "❌ Entry could not be approved."
        )


async def deny_raffle_entry(update, context):

    if not admin_only(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /denyentry ENTRY_ID"
        )
        return

    entry_id = int(context.args[0])

    if deny_entry(
        entry_id,
        update.effective_user.id
    ):

        await update.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )

    else:

        await update.message.reply_text(
            "❌ Entry could not be denied."
        )


async def reroll_raffle(update, context):

    if admin_only(update):

        await update.message.reply_text(
            "⚠️ Reroll is available after a completed raffle."
        )


# ==========================================================
# EXPIRATION JOB
# ==========================================================

async def raffle_expiration_job(context):

    raffle = get_active_raffle()

    if not raffle or not raffle["expires_at"]:
        return

    expires = datetime.fromisoformat(
        raffle["expires_at"]
    )

    if datetime.utcnow() >= expires:

        close_raffle(
            raffle["id"]
        )

        if RAFFLE_CHAT_ID:

            try:

                await context.bot.send_message(
                    chat_id=RAFFLE_CHAT_ID,
                    text=(
                        "⏰ **RAFFLE CLOSED**\n\n"
                        f"🎁 Prize: {raffle['prize']}\n\n"
                        "The 7-day entry period has ended.\n"
                        "An admin can now draw the winner."
                    ),
                    parse_mode="Markdown"
                )

            except Exception:
                logger.exception(
                    "Unable to announce raffle expiration."
                )
