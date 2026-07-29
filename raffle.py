# ==========================================================
# Melanated AZ Bot
# raffle.py
# Payment Verified Raffle System
# ==========================================================

import random

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    CASHAPP_TAG,
    ZELLE_INFO,
    RAFFLE_ENTRY_COST
)

from admin import is_admin

from raffle_database import (
    initialize_raffle_database,
    add_pending_payment,
    get_pending_payments,
    approve_payment,
    deny_payment,
    get_approved_entries,
    save_winner
)



# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

raffle_data = {

    "active": False,
    "prize": ""

}



# Initialize database

initialize_raffle_database()



# ==========================================================
# START RAFFLE
# ADMIN ONLY
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


    raffle_data["active"] = True

    raffle_data["prize"] = prize



    await update.message.reply_text(

f"""
🎟️ RAFFLE STARTED 🎟️

🏆 Prize:
{prize}

💵 Entry:
{RAFFLE_ENTRY_COST}

To enter:

/enter

Good luck! 🍀
"""

    )



# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not raffle_data["active"]:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    await update.message.reply_text(

f"""
🎟️ Raffle Entry

🏆 Prize:
{raffle_data["prize"]}

Entry Fee:
{RAFFLE_ENTRY_COST}


Send payment through:

💵 Cash App:
{CASHAPP_TAG}

🏦 Zelle:
{ZELLE_INFO}


After payment send:

/paid CashApp

or

/paid Zelle

An admin will verify your entry.
"""

    )



# ==========================================================
# SUBMIT PAYMENT
# ==========================================================

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user



    if not raffle_data["active"]:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    if not context.args:

        await update.message.reply_text(

            "Usage:\n"
            "/paid CashApp\n"
            "/paid Zelle"

        )

        return



    method = context.args[0]



    add_pending_payment(

        user.id,

        user.username or user.first_name,

        method,

        raffle_data["prize"]

    )



    await update.message.reply_text(

f"""
✅ Payment Submitted

Payment Method:
{method}

Your entry is pending admin approval.

Good luck! 🍀
"""

    )



# ==========================================================
# SHOW PENDING PAYMENTS
# ADMIN ONLY
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    entries = get_pending_payments()



    if not entries:

        await update.message.reply_text(
            "No pending entries."
        )

        return



    text = "🎟️ Pending Entries\n\n"



    for entry in entries:

        text += (

f"ID: {entry[0]}\n"
f"User: {entry[2]}\n"
f"Payment: {entry[3]}\n\n"

        )



    await update.message.reply_text(
        text
    )



# ==========================================================
# APPROVE ENTRY
# ==========================================================

async def approve_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    if not context.args:

        await update.message.reply_text(

            "Usage:\n"
            "/approveentry ID"

        )

        return



    result = approve_payment(

        int(context.args[0])

    )



    if result:

        await update.message.reply_text(

            "✅ Entry approved."

        )

    else:

        await update.message.reply_text(

            "❌ Entry not found."

        )



# ==========================================================
# DENY ENTRY
# ==========================================================

async def deny_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    if not context.args:

        return



    deny_payment(

        int(context.args[0])

    )


    await update.message.reply_text(

        "🛑 Entry denied."

    )



# ==========================================================
# SHOW ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    entries = get_approved_entries(

        raffle_data["prize"]

    )


    if not entries:

        await update.message.reply_text(

            "No approved entries."

        )

        return



    text = "🎟️ Approved Entries\n\n"



    for entry in entries:

        text += f"👤 {entry[1]}\n"



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



    entries = get_approved_entries(

        raffle_data["prize"]

    )


    if not entries:

        await update.message.reply_text(

            "❌ No approved entries."

        )

        return



    winner = random.choice(entries)



    save_winner(

        winner[0],

        winner[1],

        raffle_data["prize"]

    )


    raffle_data["active"] = False



    await update.message.reply_text(

f"""
🎉 RAFFLE WINNER 🎉

🏆 Prize:
{raffle_data["prize"]}

👑 Winner:
{winner[1]}

Congratulations! 🎊
"""

    )



# ==========================================================
# PLACEHOLDER COMMANDS
# ==========================================================

async def raffle_status(update, context):

    await update.message.reply_text(

        f"🎟️ Active: {raffle_data['active']}\n"
        f"🏆 Prize: {raffle_data['prize']}"

    )



async def reroll_raffle(update, context):

    await draw_raffle(update, context)



async def cancel_raffle(update, context):

    raffle_data["active"] = False

    await update.message.reply_text(
        "🛑 Raffle cancelled."
    )



async def bonus_entry(update, context):

    await update.message.reply_text(
        "⭐ Bonus entries coming soon."
    )



async def remove_raffle_entry(update, context):

    await update.message.reply_text(
        "🗑️ Remove entry coming soon."
    )
