# ==========================================================
# Melanated AZ Bot
# raffle.py
#
# Private paid raffle between friends
# Admin approval required before raffle is posted
# ==========================================================

import logging
import random

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
    get_active_raffle,
    get_pending_raffle,
    get_raffle,
    set_raffle_posted_message,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle,
)


logger = logging.getLogger(__name__)


# ==========================================================
# HELPERS
# ==========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_only(update: Update) -> bool:

    user = update.effective_user

    if not user:
        return False

    return is_admin(user.id)


def get_display_name(user) -> str:

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return str(user.id)


# ==========================================================
# MEMBER RAFFLE KEYBOARD
# ==========================================================

def raffle_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Enter Raffle",
                    callback_data="raffle_enter",
                )
            ]
        ]
    )


# ==========================================================
# PAYMENT KEYBOARD
# ==========================================================

def payment_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 Pay with Cash App",
                    callback_data="raffle_paid",
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 Pay with Zelle",
                    callback_data="raffle_zelle",
                )
            ],
        ]
    )


# ==========================================================
# ADMIN RAFFLE APPROVAL KEYBOARD
# ==========================================================

def admin_raffle_keyboard(raffle_id: int):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve & Post",
                    callback_data=f"raffleapprove_{raffle_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel Raffle",
                    callback_data=f"rafflecancel_{raffle_id}",
                )
            ],
        ]
    )


# ==========================================================
# ADMIN ENTRY APPROVAL KEYBOARD
# ==========================================================

def admin_entry_keyboard(entry_id: int):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"approve_{entry_id}",
                ),
                InlineKeyboardButton(
                    "❌ Deny",
                    callback_data=f"deny_{entry_id}",
                ),
            ]
        ]
    )


# ==========================================================
# FORMAT RAFFLE POST
# ==========================================================

def raffle_post_text(raffle):

    return (
        "🎟️ **MELANATED AZ FRIENDS RAFFLE** 🎟️\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {raffle['entry_price']}\n"
        f"🆔 **Raffle #:** {raffle['id']}\n\n"
        "This is a **private raffle between friends**.\n\n"
        "To participate, click **Enter Raffle** below.\n"
        "Payment is required for your entry to be approved.\n\n"
        "🍀 Good luck!"
    )


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ This command is for raffle admins only."
        )

        return

    if not update.message:
        return

    if not context.args:

        await update.message.reply_text(
            "🎟️ **Start a Raffle**\n\n"
            "Use:\n"
            "/startraffle PRIZE | ENTRY PRICE\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | $10 Entry",
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # Parse prize and price
    # ------------------------------------------------------

    full_text = " ".join(context.args).strip()

    if "|" not in full_text:

        await update.message.reply_text(
            "❌ Please include both the prize and entry price.\n\n"
            "Example:\n"
            "/startraffle $100 Cash Prize | $10 Entry"
        )

        return

    prize, entry_price = full_text.split("|", 1)

    prize = prize.strip()
    entry_price = entry_price.strip()

    if not prize:

        await update.message.reply_text(
            "❌ Prize cannot be empty."
        )

        return

    if not entry_price:

        await update.message.reply_text(
            "❌ Entry price cannot be empty."
        )

        return

    # ------------------------------------------------------
    # Check for existing active raffle
    # ------------------------------------------------------

    active = get_active_raffle()

    if active:

        await update.message.reply_text(
            "⚠️ There is already an active raffle.\n\n"
            f"🎁 Prize: {active['prize']}\n"
            f"💵 Entry: {active['entry_price']}\n"
            f"🆔 Raffle #: {active['id']}"
        )

        return

    # ------------------------------------------------------
    # Check for pending raffle
    # ------------------------------------------------------

    pending = get_pending_raffle()

    if pending:

        await update.message.reply_text(
            "⚠️ There is already a raffle waiting for admin approval.\n\n"
            f"🎁 Prize: {pending['prize']}\n"
            f"💵 Entry: {pending['entry_price']}\n"
            f"🆔 Raffle #: {pending['id']}"
        )

        return

    # ------------------------------------------------------
    # Create pending raffle
    # ------------------------------------------------------

    raffle_id = create_raffle(
        prize=prize,
        entry_price=entry_price,
        chat_id=update.effective_chat.id,
    )

    raffle = get_raffle(raffle_id)

    if not raffle:

        await update.message.reply_text(
            "❌ Unable to create raffle."
        )

        return

    # ------------------------------------------------------
    # Confirm to admin
    # ------------------------------------------------------

    await update.message.reply_text(
        "🎟️ **RAFFLE CREATED — AWAITING APPROVAL**\n\n"
        f"🎁 **Prize:** {prize}\n"
        f"💵 **Entry:** {entry_price}\n"
        f"🆔 **Raffle #:** {raffle_id}\n\n"
        "The raffle has NOT been posted yet.\n"
        "An admin must approve it before it is posted "
        "to the group.",
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # Send approval request to admins
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "🎟️ **RAFFLE APPROVAL REQUIRED**\n\n"
                    f"🎁 **Prize:** {prize}\n"
                    f"💵 **Entry:** {entry_price}\n"
                    f"🆔 **Raffle #:** {raffle_id}\n\n"
                    "Approve this raffle to post it "
                    "to the group."
                ),
                reply_markup=admin_raffle_keyboard(
                    raffle_id
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin %s about raffle %s",
                admin_id,
                raffle_id,
            )


# ==========================================================
# ADMIN RAFFLE APPROVAL BUTTON
# ==========================================================

async def admin_raffle_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    admin = query.from_user

    if not is_admin(admin.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    data = query.data

    try:

        if data.startswith("raffleapprove_"):

            raffle_id = int(
                data.split("_", 1)[1]
            )

            action = "approve"

        elif data.startswith("rafflecancel_"):

            raffle_id = int(
                data.split("_", 1)[1]
            )

            action = "cancel"

        else:

            await query.message.reply_text(
                "❌ Invalid raffle action."
            )

            return

    except (ValueError, AttributeError):

        await query.message.reply_text(
            "❌ Invalid raffle."
        )

        return

    raffle = get_raffle(raffle_id)

    if not raffle:

        await query.message.reply_text(
            "❌ Raffle not found."
        )

        return

    # ------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------

    if action == "cancel":

        if raffle["status"] != "pending":

            await query.message.reply_text(
                "⚠️ This raffle has already been processed."
            )

            return

        close_raffle(raffle_id)

        await query.message.reply_text(
            f"🛑 Raffle #{raffle_id} cancelled."
        )

        return

    # ------------------------------------------------------
    # APPROVE
    # ------------------------------------------------------

    if raffle["status"] != "pending":

        await query.message.reply_text(
            "⚠️ This raffle has already been processed."
        )

        return

    from raffle_database import approve_raffle

    approved = approve_raffle(
        raffle_id,
        admin.id,
    )

    if not approved:

        await query.message.reply_text(
            "⚠️ Raffle could not be approved."
        )

        return

    # ------------------------------------------------------
    # Post raffle to original group
    # ------------------------------------------------------

    try:

        posted_message = await context.bot.send_message(
            chat_id=raffle["chat_id"],
            text=raffle_post_text(raffle),
            reply_markup=raffle_keyboard(),
            parse_mode="Markdown",
        )

        set_raffle_posted_message(
            raffle_id,
            posted_message.message_id,
        )

    except Exception:

        logger.exception(
            "Unable to post raffle %s",
            raffle_id,
        )

        await query.message.reply_text(
            "⚠️ Raffle was approved, but I could not post "
            "it to the group. Check that the bot can send "
            "messages in the group."
        )

        return

    await query.message.reply_text(
        f"✅ Raffle #{raffle_id} approved and posted!"
    )


# ==========================================================
# ENTER RAFFLE BUTTON
# ==========================================================

async def enter_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle right now."
        )

        return

    await query.message.reply_text(
        "🎟️ **ENTER MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {raffle['entry_price']}\n\n"
        "Choose your payment method below.\n\n"
        "⚠️ Your entry is not active until an admin "
        "verifies your payment.",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# ENTER COMMAND
# ==========================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    raffle = get_active_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ There is no active raffle right now."
        )

        return

    await update.message.reply_text(
        "🎟️ **ENTER MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {raffle['entry_price']}\n\n"
        "Choose your payment method below.",
        reply_markup=payment_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# PAID ENTRY COMMAND
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await enter_raffle(
        update,
        context,
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

    await query.answer()

    user = query.from_user

    raffle = get_active_raffle()

    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )

        return

    if query.data == "raffle_zelle":

        payment_method = "Zelle"

    else:

        payment_method = "Cash App"

    # ------------------------------------------------------
    # Create entry
    # ------------------------------------------------------

    entry_id = add_raffle_entry(
        raffle_id=raffle["id"],
        user_id=user.id,
        username=user.username,
        display_name=get_display_name(user),
        payment_method=payment_method,
    )

    if entry_id is None:

        await query.message.reply_text(
            "⚠️ You already have a pending or approved "
            "entry for this raffle."
        )

        return

    # ------------------------------------------------------
    # Payment instructions
    # ------------------------------------------------------

    if payment_method == "Cash App":

        payment_text = (
            "💵 **Cash App**\n\n"
            f"Send **{raffle['entry_price']}** to:\n"
            f"`{CASHAPP_TAG}`\n"
        )

        if CASHAPP_URL:

            payment_text += (
                f"\n🔗 {CASHAPP_URL}\n"
            )

    else:

        payment_text = (
            "💳 **Zelle**\n\n"
            f"Send **{raffle['entry_price']}** to:\n"
            f"`{ZELLE_PHONE}`\n"
        )

    # ------------------------------------------------------
    # Tell member
    # ------------------------------------------------------

    await query.message.reply_text(
        "🎟️ **RAFFLE ENTRY CREATED**\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {raffle['entry_price']}\n"
        f"🆔 **Entry #:** {entry_id}\n"
        f"💳 **Method:** {payment_method}\n\n"
        f"{payment_text}\n"
        "Once payment is sent, an admin will verify it "
        "and approve your entry.\n\n"
        "⚠️ Your entry is **NOT ACTIVE** until approved.",
        parse_mode="Markdown",
    )

    # ------------------------------------------------------
    # Notify admins
    # ------------------------------------------------------

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "💰 **RAFFLE PAYMENT PENDING**\n\n"
                    f"🎁 **Prize:** {raffle['prize']}\n"
                    f"💵 **Entry:** {raffle['entry_price']}\n"
                    f"🆔 **Entry #:** {entry_id}\n"
                    f"👤 **Name:** {get_display_name(user)}\n"
                    f"🔹 **User ID:** `{user.id}`\n"
                    f"💳 **Payment:** {payment_method}\n\n"
                    "Verify the payment before approving."
                ),
                reply_markup=admin_entry_keyboard(
                    entry_id
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify admin %s",
                admin_id,
            )


# ==========================================================
# ADMIN ENTRY APPROVAL BUTTON
# ==========================================================

async def admin_payment_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    admin = query.from_user

    if not is_admin(admin.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    data = query.data

    try:

        action, entry_text = data.split(
            "_",
            1
        )

        entry_id = int(entry_text)

    except (ValueError, AttributeError):

        await query.message.reply_text(
            "❌ Invalid raffle entry."
        )

        return

    entry = get_entry(entry_id)

    if not entry:

        await query.message.reply_text(
            "❌ Entry not found."
        )

        return

    raffle = get_raffle(
        entry["raffle_id"]
    )

    if not raffle:

        await query.message.reply_text(
            "❌ Raffle not found."
        )

        return

    # ------------------------------------------------------
    # APPROVE ENTRY
    # ------------------------------------------------------

    if action == "approve":

        success = approve_entry(
            entry_id,
            admin.id,
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry could not be approved. "
                "It may already have been processed."
            )

            return

        await query.message.reply_text(
            f"✅ Entry #{entry_id} approved."
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "🎉 **RAFFLE ENTRY APPROVED!**\n\n"
                    f"🎁 **Prize:** {raffle['prize']}\n"
                    f"💵 **Entry:** {raffle['entry_price']}\n"
                    f"🆔 **Entry #:** {entry_id}\n\n"
                    "Your payment has been verified "
                    "and your entry is active.\n\n"
                    "Good luck! 🍀"
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify raffle participant."
            )

    # ------------------------------------------------------
    # DENY ENTRY
    # ------------------------------------------------------

    elif action == "deny":

        success = deny_entry(
            entry_id,
            admin.id,
        )

        if not success:

            await query.message.reply_text(
                "⚠️ Entry could not be denied. "
                "It may already have been processed."
            )

            return

        await query.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )

        try:

            await context.bot.send_message(
                chat_id=entry["user_id"],
                text=(
                    "❌ **RAFFLE ENTRY NOT APPROVED**\n\n"
                    f"🆔 **Entry #:** {entry_id}\n\n"
                    "Please contact an admin if you believe "
                    "this was an error."
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to notify participant."
            )


# ==========================================================
# PENDING ENTRIES
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    entries = get_pending_entries()

    if not entries:

        await update.message.reply_text(
            "✅ No pending raffle entries."
        )

        return

    for entry in entries:

        raffle = get_raffle(
            entry["raffle_id"]
        )

        raffle_text = ""

        if raffle:

            raffle_text = (
                f"🎁 Prize: {raffle['prize']}\n"
                f"💵 Entry: {raffle['entry_price']}\n"
            )

        text = (
            "💰 **PENDING RAFFLE ENTRY**\n\n"
            f"{raffle_text}"
            f"🆔 Entry #: {entry['id']}\n"
            f"👤 User ID: {entry['user_id']}\n"
            f"💳 Payment: {entry['payment_method']}\n"
            f"🕐 Created: {entry['created_at']}"
        )

        await update.message.reply_text(
            text,
            reply_markup=admin_entry_keyboard(
                entry["id"]
            ),
            parse_mode="Markdown",
        )


# ==========================================================
# APPROVE ENTRY COMMAND
# ==========================================================

async def approve_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "Usage: /approveentry ENTRY_ID"
        )

        return

    try:

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )

        return

    entry = get_entry(entry_id)

    if not entry:

        await update.message.reply_text(
            "❌ Entry not found."
        )

        return

    success = approve_entry(
        entry_id,
        update.effective_user.id,
    )

    if success:

        await update.message.reply_text(
            f"✅ Entry #{entry_id} approved."
        )

    else:

        await update.message.reply_text(
            "❌ Entry could not be approved."
        )


# ==========================================================
# DENY ENTRY COMMAND
# ==========================================================

async def deny_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "Usage: /denyentry ENTRY_ID"
        )

        return

    try:

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )

        return

    success = deny_entry(
        entry_id,
        update.effective_user.id,
    )

    if success:

        await update.message.reply_text(
            f"❌ Entry #{entry_id} denied."
        )

    else:

        await update.message.reply_text(
            "❌ Entry could not be denied."
        )


# ==========================================================
# RAFFLE STATUS
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    raffle = get_active_raffle()

    if not raffle:

        pending = get_pending_raffle()

        if pending:

            await update.message.reply_text(
                "🎟️ **RAFFLE STATUS**\n\n"
                f"🆔 Raffle #: {pending['id']}\n"
                f"🎁 Prize: {pending['prize']}\n"
                f"💵 Entry: {pending['entry_price']}\n"
                "📌 Status: Awaiting admin approval",
                parse_mode="Markdown",
            )

            return

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
        f"💵 Entry: {raffle['entry_price']}\n"
        f"📌 Status: {raffle['status']}\n"
        f"👥 Approved Entries: {len(entries)}",
        parse_mode="Markdown",
    )


# ==========================================================
# RAFFLE ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

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
        "",
        f"🎁 Prize: {raffle['prize']}",
        f"💵 Entry: {raffle['entry_price']}",
        "",
    ]

    for entry in entries:

        name = (
            entry["display_name"]
            or entry["username"]
            or str(entry["user_id"])
        )

        lines.append(
            f"#{entry['id']} — {name}"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ==========================================================
# DRAW RAFFLE
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

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
            "❌ There are no approved paid entries."
        )

        return

    winner = random.choice(entries)

    close_raffle(
        raffle["id"]
    )

    name = (
        winner["display_name"]
        or winner["username"]
        or str(winner["user_id"])
    )

    await update.message.reply_text(
        "🎉🎉 **RAFFLE WINNER!** 🎉🎉\n\n"
        "🎟️ **MELANATED AZ FRIENDS RAFFLE**\n\n"
        f"🎁 **Prize:** {raffle['prize']}\n"
        f"💵 **Entry:** {raffle['entry_price']}\n\n"
        f"🏆 **Winner:** {name}\n"
        f"🆔 **Entry #:** {winner['id']}\n\n"
        "Congratulations! 🍀",
        parse_mode="Markdown",
    )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    await update.message.reply_text(
        "⚠️ The previous raffle has already been closed.\n"
        "Use /startraffle to create a new raffle."
    )


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    raffle = get_active_raffle()

    if not raffle:

        raffle = get_pending_raffle()

    if not raffle:

        await update.message.reply_text(
            "❌ No active or pending raffle."
        )

        return

    close_raffle(
        raffle["id"]
    )

    await update.message.reply_text(
        f"🛑 Raffle #{raffle['id']} cancelled."
    )


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    await update.message.reply_text(
        "ℹ️ Bonus entries are not enabled in this database version."
    )


# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not admin_only(update):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "Usage: /removeentry ENTRY_ID"
        )

        return

    try:

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Entry ID must be a number."
        )

        return

    success = remove_entry(
        entry_id
    )

    if success:

        await update.message.reply_text(
            f"🗑️ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )
