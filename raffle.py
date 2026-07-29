# ==========================================================
# Melanated AZ Bot
# raffle.py
# Paid Raffle System
# ==========================================================

import random
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS,
    RAFFLE_ENTRY_COST,
    CASHAPP_TAG,
    ZELLE_EMAIL
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
    close_raffle
)



# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS



# ==========================================================
# START RAFFLE
# ==========================================================

async def start_raffle(update, context):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Admin only."
        )
        return


    if not context.args:

        await update.message.reply_text(
            "Usage:\n/startraffle Prize Name"
        )

        return


    prize = " ".join(context.args)


    create_raffle(
        prize
    )


    await update.message.reply_text(
f"""
🎟 NEW RAFFLE STARTED

🏆 Prize:
{prize}

💰 Entry:
${RAFFLE_ENTRY_COST}

How to enter:

1️⃣ Send payment

CashApp:
{CASHAPP_TAG}

Zelle:
{ZELLE_EMAIL}


2️⃣ Submit:

/paid cashapp

or

/paid zelle
"""
    )



# ==========================================================
# ENTER RAFFLE
# ==========================================================

async def enter_raffle(update, context):

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

💰 Cost:
${RAFFLE_ENTRY_COST}


Payment Options:

💵 CashApp:
{CASHAPP_TAG}

💳 Zelle:
{ZELLE_EMAIL}


After payment send:

/paid cashapp

or

/paid zelle
"""
    )



# ==========================================================
# PAID ENTRY
# ==========================================================

async def paid_entry(update, context):

    try:

        print(
            "PAID COMMAND RECEIVED"
        )


        raffle = get_active_raffle()


        if not raffle:

            await update.message.reply_text(
                "❌ No active raffle."
            )

            return



        if not context.args:

            await update.message.reply_text(
                "Use:\n/paid cashapp\nor\n/paid zelle"
            )

            return



        method = context.args[0].lower()


        if method not in [
            "cashapp",
            "zelle"
        ]:

            await update.message.reply_text(
                "❌ Payment must be cashapp or zelle."
            )

            return



        user = update.effective_user


        add_raffle_entry(

            raffle[0],

            user.id,

            user.username or user.first_name,

            method

        )


        await update.message.reply_text(
f"""
✅ PAYMENT SUBMITTED

👤 User:
{user.first_name}

💳 Method:
{method.upper()}

💰 Amount:
${RAFFLE_ENTRY_COST}

⏳ Status:
Waiting for admin approval

Thank you 🔥
"""
        )


    except Exception as e:

        traceback.print_exc()

        await update.message.reply_text(
            f"❌ Error:\n{e}"
        )



# ==========================================================
# PENDING
# ==========================================================

async def pending_entries(update, context):

    if not is_admin(update.effective_user.id):

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


    for e in entries:

        msg += (
            f"ID: {e[0]}\n"
            f"User: {e[1]}\n"
            f"Method: {e[2]}\n\n"
        )


    msg += (
        "/approveentry ID\n"
        "/denyentry ID"
    )


    await update.message.reply_text(
        msg
    )



# ==========================================================
# APPROVE
# ==========================================================

async def approve_raffle_entry(update, context):

    if not is_admin(update.effective_user.id):

        return


    if not context.args:

        await update.message.reply_text(
            "Use /approveentry ID"
        )

        return


    approve_entry(
        int(context.args[0])
    )


    await update.message.reply_text(
        "✅ Entry approved."
    )



# ==========================================================
# DENY
# ==========================================================

async def deny_raffle_entry(update, context):

    if not is_admin(update.effective_user.id):

        return


    deny_entry(
        int(context.args[0])
    )


    await update.message.reply_text(
        "❌ Entry denied."
    )



# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(update, context):

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "No active raffle."
        )

        return


    await update.message.reply_text(
f"""
🎟 ACTIVE RAFFLE

🏆 Prize:
{raffle[1]}

💰 Entry:
${RAFFLE_ENTRY_COST}
"""
    )



# ==========================================================
# ENTRIES
# ==========================================================

async def raffle_entries(update, context):

    if not is_admin(update.effective_user.id):

        return


    raffle = get_active_raffle()


    if not raffle:

        return


    entries = get_approved_entries(
        raffle[0]
    )


    msg = "🎟 APPROVED ENTRIES\n\n"


    for e in entries:

        msg += f"{e[1]}\n"


    await update.message.reply_text(
        msg
    )



# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(update, context):

    if not is_admin(update.effective_user.id):

        return


    raffle = get_active_raffle()


    entries = get_approved_entries(
        raffle[0]
    )


    if not entries:

        await update.message.reply_text(
            "No approved entries."
        )

        return


    winner = random.choice(entries)


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
"""
    )



async def reroll_raffle(update, context):

    await draw_raffle(
        update,
        context
    )



async def cancel_raffle(update, context):

    raffle = get_active_raffle()

    if raffle:

        close_raffle(
            raffle[0]
        )


    await update.message.reply_text(
        "❌ Raffle cancelled."
    )



async def bonus_entry(update, context):

    await update.message.reply_text(
        "🔥 Bonus entry coming soon."
    )



async def remove_raffle_entry(update, context):

    remove_entry(
        int(context.args[0])
    )


    await update.message.reply_text(
        "Entry removed."
    )
