# ==========================================================
# Melanated AZ Bot
# raffle.py
# Paid Raffle System
# ==========================================================

import random
import traceback

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS,
    RAFFLE_ENTRY_COST,
    CASHAPP_TAG,
    CASHAPP_URL,
    ZELLE_PHONE
)

from raffle_database import (
    create_raffle,
    get_active_raffle,
    add_raffle_entry,
    get_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle
)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ==========================================================
# PAYMENT BUTTONS
# ==========================================================

def payment_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "💵 Pay with Cash App",
                url=CASHAPP_URL
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Pay with Zelle",
                callback_data="raffle_zelle"
            )
        ],

        [
            InlineKeyboardButton(
                "✅ I've Paid",
                callback_data="raffle_paid"
            )
        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Admin only."
        )

        return


    if not context.args:

        await update.message.reply_text(
            "Usage:\n/startraffle Prize Name"
        )

        return


    prize = " ".join(
        context.args
    )


    raffle_id = create_raffle(
        prize
    )


    await update.message.reply_text(

        f"""
🎟 NEW RAFFLE STARTED

🏆 Prize:
{prize}

💰 Entry:
${RAFFLE_ENTRY_COST:.2f}

🎟 Raffle ID:
{raffle_id}

Members can use:

/enter
""",

        reply_markup=payment_keyboard()

    )


# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(
    update,
    context
):

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle right now."
        )

        return


    await update.message.reply_text(

        f"""
🎟 RAFFLE ENTRY

🏆 Prize:
{raffle[1]}

💰 Entry Cost:
${RAFFLE_ENTRY_COST:.2f}

Choose your payment method below.

💵 Cash App:
{CASHAPP_TAG}

💳 Zelle:
{ZELLE_PHONE}

After completing your payment, press:

✅ I've Paid
""",

        reply_markup=payment_keyboard()

    )


# ==========================================================
# PAYMENT BUTTON
# ==========================================================

async def payment_button(
    update,
    context
):

    query = update.callback_query

    await query.answer()


    if query.data == "raffle_zelle":

        await query.message.reply_text(

            f"""
💳 ZELLE PAYMENT

Send:

${RAFFLE_ENTRY_COST:.2f}

To Zelle:

📱 {ZELLE_PHONE}

After sending the payment, return here and press:

✅ I've Paid
""",

            reply_markup=InlineKeyboardMarkup(

                [
                    [
                        InlineKeyboardButton(
                            "✅ I've Paid",
                            callback_data="raffle_paid"
                        )
                    ]
                ]

            )

        )

        return


    if query.data == "raffle_paid":

        await create_paid_entry(
            query,
            context
        )


# ==========================================================
# CREATE PAID ENTRY
# ==========================================================

async def create_paid_entry(
    query,
    context
):

    raffle = get_active_raffle()


    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )

        return


    user = query.from_user


    username = (
        f"@{user.username}"
        if user.username
        else user.first_name
    )


    display_name = user.full_name


    # ======================================================
    # DEFAULT PAYMENT METHOD
    # ======================================================
    #
    # We don't actually receive payment confirmation from
    # Cash App or Zelle. The user is submitting an entry
    # for your manual approval.
    #
    # ======================================================

    payment_method = "PAYMENT SUBMITTED"


    entry_id = add_raffle_entry(

        raffle[0],

        user.id,

        username,

        display_name,

        payment_method

    )


    # ======================================================
    # DUPLICATE ENTRY
    # ======================================================

    if entry_id is None:

        await query.message.reply_text(

            """
⚠️ ENTRY ALREADY SUBMITTED

You already have a pending or approved entry for this raffle.

Please wait for admin approval.
""",

        )

        return


    # ======================================================
    # MEMBER CONFIRMATION
    # ======================================================

    await query.message.reply_text(

        f"""
✅ PAYMENT SUBMITTED

🎟 Entry ID:
#{entry_id}

🏆 Prize:
{raffle[1]}

👤 Name:
{display_name}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

⏳ Status:
PENDING ADMIN APPROVAL

You'll receive another message once your entry has been reviewed.

🔥 Good luck!
"""
    )


    # ======================================================
    # ADMIN NOTIFICATION
    # ======================================================

    admin_keyboard = InlineKeyboardMarkup(

        [

            [

                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"approve_{entry_id}"
                ),

                InlineKeyboardButton(
                    "❌ DENY",
                    callback_data=f"deny_{entry_id}"
                )

            ]

        ]

    )


    admin_message = f"""
🎟 NEW RAFFLE PAYMENT

⚠️ ACTION REQUIRED

🏆 Prize:
{raffle[1]}

🎟 Entry:
#{entry_id}

👤 Name:
{display_name}

🔹 Username:
{username}

🆔 User ID:
{user.id}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

💳 Payment:
{payment_method}

⏳ Status:
PENDING
"""


    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(

                chat_id=admin_id,

                text=admin_message,

                reply_markup=admin_keyboard

            )

        except Exception as e:

            print(
                f"Could not notify admin {admin_id}: {e}"
            )


# ==========================================================
# ADMIN PAYMENT BUTTON
# ==========================================================

async def admin_payment_button(
    update,
    context
):

    query = update.callback_query

    await query.answer()


    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "❌ Admin only.",
            show_alert=True
        )

        return


    data = query.data


    if data.startswith("approve_"):

        entry_id = int(
            data.split("_")[1]
        )


        entry = get_entry(
            entry_id
        )


        if not entry:

            await query.message.edit_text(
                "❌ Entry no longer exists."
            )

            return


        success = approve_entry(
            entry_id,
            query.from_user.id
        )


        if not success:

            await query.message.edit_text(
                "⚠️ This entry has already been processed."
            )

            return


        # ==================================================
        # ADMIN MESSAGE
        # ==================================================

        await query.message.edit_text(

            f"""
✅ RAFFLE PAYMENT APPROVED

🎟 Entry:
#{entry_id}

👤 {entry['display_name']}

💰 ${RAFFLE_ENTRY_COST:.2f}

Status: PAID
"""
        )


        # ==================================================
        # MEMBER NOTIFICATION
        # ==================================================

        try:

            await context.bot.send_message(

                chat_id=entry["user_id"],

                text=f"""
🎉 YOUR RAFFLE ENTRY IS APPROVED!

🏆 Prize:
{get_active_raffle()[1]}

🎟 Entry:
#{entry_id}

💰 Payment:
${RAFFLE_ENTRY_COST:.2f}

✅ Status:
APPROVED

Good luck! 🔥
"""
            )

        except Exception as e:

            print(
                f"Could not notify member: {e}"
            )


        return


    if data.startswith("deny_"):

        entry_id = int(
            data.split("_")[1]
        )


        entry = get_entry(
            entry_id
        )


        if not entry:

            await query.message.edit_text(
                "❌ Entry no longer exists."
            )

            return


        success = deny_entry(
            entry_id,
            query.from_user.id
        )


        if not success:

            await query.message.edit_text(
                "⚠️ This entry has already been processed."
            )

            return


        await query.message.edit_text(

            f"""
❌ RAFFLE PAYMENT DENIED

🎟 Entry:
#{entry_id}

👤 {entry['display_name']}

Status: DENIED
"""
        )


        try:

            await context.bot.send_message(

                chat_id=entry["user_id"],

                text=f"""
❌ RAFFLE ENTRY NOT APPROVED

🎟 Entry:
#{entry_id}

Your payment could not be approved at this time.

Please contact an administrator if you believe this was an error.
"""
            )

        except Exception as e:

            print(
                f"Could not notify member: {e}"
            )


# ==========================================================
# LEGACY /PAID COMMAND
# ==========================================================

async def paid_entry(
    update,
    context
):

    await enter_raffle(
        update,
        context
    )


# ==========================================================
# PENDING PAYMENTS
# ==========================================================

async def pending_entries(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Admin only."
        )

        return


    entries = get_pending_entries()


    if not entries:

        await update.message.reply_text(
            "✅ No pending payments."
        )

        return


    msg = "⏳ PENDING PAYMENTS\n\n"


    for entry in entries:

        msg += (

            f"🎟 ID: {entry[0]}\n"

            f"👤 User: {entry[1]}\n"

            f"💳 Method: {entry[2]}\n"

            f"🕐 {entry[3]}\n\n"

        )


    msg += (
        "Use the approval buttons from the "
        "payment notification."
    )


    await update.message.reply_text(
        msg
    )


# ==========================================================
# APPROVE COMMAND
# ==========================================================

async def approve_raffle_entry(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


    if not context.args:

        await update.message.reply_text(
            "Use /approveentry ID"
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


    entry = get_entry(
        entry_id
    )


    if not entry:

        await update.message.reply_text(
            "❌ Entry not found."
        )

        return


    success = approve_entry(
        entry_id,
        update.effective_user.id
    )


    if not success:

        await update.message.reply_text(
            "⚠️ Entry has already been processed."
        )

        return


    await update.message.reply_text(
        f"✅ Entry #{entry_id} approved."
    )


# ==========================================================
# DENY COMMAND
# ==========================================================

async def deny_raffle_entry(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


    if not context.args:

        await update.message.reply_text(
            "Use /denyentry ID"
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


    entry = get_entry(
        entry_id
    )


    if not entry:

        await update.message.reply_text(
            "❌ Entry not found."
        )

        return


    success = deny_entry(
        entry_id,
        update.effective_user.id
    )


    if not success:

        await update.message.reply_text(
            "⚠️ Entry has already been processed."
        )

        return


    await update.message.reply_text(
        f"❌ Entry #{entry_id} denied."
    )


# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(
    update,
    context
):

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return


    entries = get_approved_entries(
        raffle[0]
    )


    await update.message.reply_text(

        f"""
🎟 ACTIVE RAFFLE

🏆 Prize:
{raffle[1]}

💰 Entry:
${RAFFLE_ENTRY_COST:.2f}

👥 Approved Entries:
{len(entries)}
"""
    )


# ==========================================================
# ENTRIES
# ==========================================================

async def raffle_entries(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return


    entries = get_approved_entries(
        raffle[0]
    )


    if not entries:

        await update.message.reply_text(
            "No approved entries."
        )

        return


    msg = "🎟 APPROVED ENTRIES\n\n"


    for entry in entries:

        msg += (
            f"#{entry[0]} - "
            f"{entry[1]}\n"
        )


    await update.message.reply_text(
        msg
    )


# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return


    entries = get_approved_entries(
        raffle[0]
    )


    if not entries:

        await update.message.reply_text(
            "❌ No approved entries."
        )

        return


    winner = random.choice(
        entries
    )


    close_raffle(
        raffle[0]
    )


    await update.message.reply_text(

        f"""
🎉🎉 RAFFLE WINNER 🎉🎉

🏆 Prize:
{raffle[1]}

👑 Winner:
{winner[1]}

🎟 Entry:
#{winner[0]}

Congratulations! 🔥
"""
    )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update,
    context
):

    await draw_raffle(
        update,
        context
    )


# ==========================================================
# CANCEL
# ==========================================================

async def cancel_raffle(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


    raffle = get_active_raffle()


    if raffle:

        close_raffle(
            raffle[0]
        )


    await update.message.reply_text(
        "❌ Raffle cancelled."
    )


# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


    await update.message.reply_text(
        "🔥 Bonus entry coming soon."
    )


# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


    if not context.args:

        await update.message.reply_text(
            "Use /removeentry ID"
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
            f"✅ Entry #{entry_id} removed."
        )

    else:

        await update.message.reply_text(
            "❌ Entry not found."
        )
