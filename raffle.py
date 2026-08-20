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
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_approved_entries,
    remove_entry,
    close_raffle,
    get_entry
)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ==========================================================
# PAYMENT KEYBOARD
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


    chat_id = update.effective_chat.id


    raffle_id = create_raffle(
        prize,
        "",
        chat_id
    )


    await update.message.reply_text(

f"""
🎟️ NEW RAFFLE STARTED

🏆 Prize:
{prize}

💰 Entry:
${RAFFLE_ENTRY_COST:.2f}

👇 Tap below to enter.
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
🎟️ RAFFLE ENTRY

🏆 Prize:
{raffle[1]}

💰 Entry Cost:
${RAFFLE_ENTRY_COST:.2f}

Choose a payment method below.

After you send your payment, tap:

✅ I've Paid

Your entry will be sent to the admin for approval.
""",

        reply_markup=payment_keyboard()

    )


# ==========================================================
# PAID COMMAND
# ==========================================================

async def paid_entry(
    update,
    context
):

    try:

        raffle = get_active_raffle()


        if not raffle:

            await update.message.reply_text(
                "❌ No active raffle."
            )

            return


        if not context.args:

            await update.message.reply_text(

"""
Choose your payment method:

/paid cashapp

or

/paid zelle
"""
            )

            return


        method = context.args[0].lower()


        if method not in (
            "cashapp",
            "zelle"
        ):

            await update.message.reply_text(
                "❌ Payment method must be Cash App or Zelle."
            )

            return


        user = update.effective_user


        username = (
            f"@{user.username}"
            if user.username
            else user.first_name
        )


        display_name = user.full_name


        entry_id = add_raffle_entry(

            raffle[0],

            user.id,

            username,

            display_name,

            method

        )


        if entry_id is None:

            await update.message.reply_text(
"""
⚠️ You already have an entry pending
or approved for this raffle.

Please wait for admin approval.
"""
            )

            return


        await update.message.reply_text(

f"""
✅ PAYMENT SUBMITTED

👤 Name:
{display_name}

💳 Method:
{method.upper()}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

🎟️ Entry ID:
#{entry_id}

⏳ Status:
Waiting for admin approval.

You will be notified once your payment has been approved.
"""
        )


        # --------------------------------------------------
        # Notify Admins
        # --------------------------------------------------

        admin_message = f"""
🔔 NEW RAFFLE PAYMENT

🎟️ Raffle:
{raffle[1]}

🆔 Entry ID:
#{entry_id}

👤 Name:
{display_name}

📱 Username:
{username}

💳 Payment:
{method.upper()}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

⏳ Status:
PENDING APPROVAL
"""


        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=f"approve:{entry_id}"
                ),

                InlineKeyboardButton(
                    "❌ DENY",
                    callback_data=f"deny:{entry_id}"
                )

            ]

        ])


        for admin_id in ADMIN_IDS:

            try:

                await context.bot.send_message(

                    chat_id=admin_id,

                    text=admin_message,

                    reply_markup=keyboard

                )

            except Exception as e:

                print(
                    f"Could not notify admin {admin_id}: {e}"
                )


    except Exception as e:

        traceback.print_exc()


        await update.message.reply_text(
            f"❌ Error processing entry:\n{e}"
        )


# ==========================================================
# ZELLE INFORMATION
# ==========================================================

async def zelle_info(
    update,
    context
):

    query = update.callback_query


    await query.answer()


    await query.message.reply_text(

f"""
💳 ZELLE PAYMENT

Send:

${RAFFLE_ENTRY_COST:.2f}

To Zelle:

📱 {ZELLE_PHONE}

After sending the payment, tap:

/paid zelle

or use the payment buttons again and select:

✅ I've Paid
"""
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

        entry_id = entry["id"]

        name = (
            entry["display_name"]
            or entry["username"]
            or "Unknown"
        )

        method = (
            entry["payment_method"]
            or "Unknown"
        )


        msg += (

            f"🆔 Entry: #{entry_id}\n"

            f"👤 User: {name}\n"

            f"💳 Method: {method.upper()}\n"

            f"💰 Status: {entry['payment_status']}\n\n"

        )


    msg += (
        "Use the approval buttons in the "
        "admin notification."
    )


    await update.message.reply_text(
        msg
    )


# ==========================================================
# APPROVE
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
            "Use:\n/approveentry ID"
        )

        return


    try:

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid entry ID."
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
            "⚠️ Entry was already processed."
        )

        return


    await update.message.reply_text(

f"""
✅ ENTRY APPROVED

🎟️ Entry:
#{entry_id}

👤 User:
{entry['display_name'] or entry['username']}

💳 Payment:
{entry['payment_method'].upper()}
"""
    )


    # ------------------------------------------------------
    # Notify Member
    # ------------------------------------------------------

    try:

        await context.bot.send_message(

            chat_id=entry["user_id"],

            text=f"""
🎉 YOUR RAFFLE ENTRY IS APPROVED!

🏆 Raffle:
{get_active_raffle()[1]}

🎟️ Entry:
#{entry_id}

💳 Payment:
{entry['payment_method'].upper()}

✅ You are officially entered!

Good luck! 🔥👑
"""

        )

    except Exception as e:

        print(
            f"Could not notify member: {e}"
        )


# ==========================================================
# DENY
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
            "Use:\n/denyentry ID"
        )

        return


    try:

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid entry ID."
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
            "⚠️ Entry was already processed."
        )

        return


    await update.message.reply_text(

f"""
❌ ENTRY DENIED

🎟️ Entry:
#{entry_id}

👤 User:
{entry['display_name'] or entry['username']}
"""
    )


    # ------------------------------------------------------
    # Notify Member
    # ------------------------------------------------------

    try:

        await context.bot.send_message(

            chat_id=entry["user_id"],

            text="""
❌ YOUR RAFFLE PAYMENT WAS NOT APPROVED.

Please contact an administrator if you believe this was an error.
"""

        )

    except Exception as e:

        print(
            f"Could not notify member: {e}"
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
🎟️ ACTIVE RAFFLE

🏆 Prize:
{raffle[1]}

💰 Entry:
${RAFFLE_ENTRY_COST:.2f}

🎫 Approved Entries:
{len(entries)}

🔥 Good luck!
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


    msg = "🎟️ APPROVED ENTRIES\n\n"


    for entry in entries:

        name = (
            entry["display_name"]
            or entry["username"]
            or "Unknown"
        )


        msg += (

            f"🎫 #{entry['entry_number']} — "

            f"{name}\n"

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


    winner_name = (
        winner["display_name"]
        or winner["username"]
        or "Unknown"
    )


    await update.message.reply_text(

f"""
🎉🎉 RAFFLE WINNER 🎉🎉

🏆 Prize:
{raffle[1]}

👑 Winner:
{winner_name}

🎟️ Entry:
#{winner['entry_number']}

Congratulations! 🔥
"""
    )


    # ------------------------------------------------------
    # Notify Winner
    # ------------------------------------------------------

    try:

        await context.bot.send_message(

            chat_id=winner["user_id"],

            text=f"""
🎉 CONGRATULATIONS!

YOU WON THE MELANATED AZ RAFFLE! 👑🔥

🏆 Prize:
{raffle[1]}

🎟️ Winning Entry:
#{winner['entry_number']}

Congratulations! 🎊
"""
        )

    except Exception as e:

        print(
            f"Could not notify winner: {e}"
        )


# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update,
    context
):

    if not is_admin(
        update.effective_user.id
    ):

        return


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
            "Use:\n/removeentry ID"
        )

        return


    try:

        entry_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid entry ID."
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
