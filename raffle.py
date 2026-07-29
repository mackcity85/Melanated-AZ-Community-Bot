# ==========================================================
# Melanated AZ Bot
# raffle.py
# Payment Verified Raffle System
# ==========================================================

import random

from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    CASHAPP_TAG,
    ZELLE_INFO,
    RAFFLE_ENTRY_COST,
    RAFFLE_DURATION_HOURS
)

from admin import is_admin

from raffle_database import (
    create_raffle,
    get_active_raffle,
    add_payment_entry,
    get_pending_entries,
    approve_entry,
    get_entries,
    close_raffle
)



# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
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


    end_time = (
        datetime.now()
        +
        timedelta(
            hours=RAFFLE_DURATION_HOURS
        )
    ).isoformat()



    raffle_id = create_raffle(

        prize,

        end_time,

        update.effective_chat.id

    )



    await update.message.reply_text(

f"""
🎟️ RAFFLE STARTED 🎟️

🏆 Prize:
{prize}

💵 Entry:
{RAFFLE_ENTRY_COST}

How to enter:

/enter

Good luck 🍀
"""

    )



# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    await update.message.reply_text(

f"""
🎟️ Raffle Entry

🏆 Prize:
{raffle[1]}

💵 Cost:
{RAFFLE_ENTRY_COST}


Payment Options:

💵 Cash App:
{CASHAPP_TAG}


🏦 Zelle:
{ZELLE_INFO}


After sending payment:

/paid CashApp

or

/paid Zelle


Your payment will be verified by an admin.
"""

    )



# ==========================================================
# PAYMENT SUBMISSION
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    if not context.args:

        await update.message.reply_text(
            "Example:\n/paid CashApp"
        )

        return



    method = context.args[0]


    user = update.effective_user



    add_payment_entry(

        raffle[0],

        user.id,

        user.username or user.first_name,

        method

    )



    await update.message.reply_text(

"""
✅ Payment Submitted

Your entry is pending approval.

Good luck! 🍀
"""

    )



# ==========================================================
# ADMIN VIEW PAYMENTS
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    entries = get_pending_entries()


    if not entries:

        await update.message.reply_text(
            "No pending payments."
        )

        return



    text = "💰 Pending Payments\n\n"


    for entry in entries:

        text += (
            f"ID: {entry[0]}\n"
            f"User: {entry[1]}\n"
            f"Method: {entry[2]}\n\n"
        )



    await update.message.reply_text(
        text
    )



# ==========================================================
# APPROVE PAYMENT
# ==========================================================

async def approve_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    if not context.args:

        await update.message.reply_text(
            "/approveentry ID"
        )

        return



    approve_entry(

        int(context.args[0])

    )



    await update.message.reply_text(
        "✅ Payment approved."
    )



# ==========================================================
# DENY PAYMENT
# ==========================================================

async def deny_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🛑 Payment denied."
    )



# ==========================================================
# VIEW ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "No active raffle."
        )

        return



    entries = get_entries(
        raffle[0]
    )


    if not entries:

        await update.message.reply_text(
            "No approved entries."
        )

        return



    text = "🎟️ Approved Entries\n\n"


    for entry in entries:

        text += (
            f"👤 {entry[1]}\n"
        )



    await update.message.reply_text(
        text
    )



# ==========================================================
# DRAW WINNER
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    entries = get_entries(
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
🎉 RAFFLE WINNER 🎉

🏆 Prize:
{raffle[1]}

👑 Winner:
{winner[1]}

Congratulations! 🎊
"""

    )



# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    raffle = get_active_raffle()


    if raffle:

        await update.message.reply_text(

f"""
🎟️ Active Raffle

🏆 Prize:
{raffle[1]}

💵 Entry:
{RAFFLE_ENTRY_COST}
"""

        )

    else:

        await update.message.reply_text(
            "No active raffle."
        )



# ==========================================================
# EXTRA COMMANDS
# ==========================================================

async def reroll_raffle(
    update,
    context
):

    await draw_raffle(
        update,
        context
    )



async def cancel_raffle(
    update,
    context
):

    raffle = get_active_raffle()


    if raffle:

        close_raffle(
            raffle[0]
        )


    await update.message.reply_text(
        "🛑 Raffle cancelled."
    )



async def bonus_entry(
    update,
    context
):

    await update.message.reply_text(
        "⭐ Bonus entry feature ready."
    )



async def remove_raffle_entry(
    update,
    context
):

    await update.message.reply_text(
        "🗑 Remove entry feature ready."
    )
