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

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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


    raffle_id = create_raffle(
        prize
    )


    await update.message.reply_text(
f"""
🎟 NEW RAFFLE STARTED

🏆 Prize:
{prize}

💰 Entry Cost:
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

async def paid_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
Pending admin approval

Thank you for supporting Melanated AZ 🔥
"""
        )


    except Exception as e:

        print(
            "PAID ENTRY ERROR:"
        )

        traceback.print_exc()


        await update.message.reply_text(
            f"❌ Error processing payment:\n{e}"
        )



# ==========================================================
# PENDING PAYMENTS
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Admin only."
        )

        return



    entries = get_pending_entries()



    if not entries:

        await update.message.reply_text(
            "No pending payments."
        )

        return



    message = "⏳ Pending Payments\n\n"



    for entry in entries:

        message += (
            f"ID: {entry[0]}\n"
            f"User: {entry[1]}\n"
            f"Method: {entry[2]}\n\n"
        )



    message += (
        "/approveentry ID\n"
        "/denyentry ID"
    )



    await update.message.reply_text(
        message
    )



# ==========================================================
# APPROVE ENTRY
# ==========================================================

async def approve_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
        "✅ Payment approved."
    )



# ==========================================================
# DENY ENTRY
# ==========================================================

async def deny_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        return



    if not context.args:

        return



    deny_entry(
        int(context.args[0])
    )


    await update.message.reply_text(
        "❌ Payment denied."
    )



# ==========================================================
# STATUS
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
# VIEW ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        return



    raffle = get_active_raffle()


    if not raffle:

        return



    entries = get_approved_entries(
        raffle[0]
    )


    if not entries:

        await update.message.reply_text(
            "No approved entries."
        )

        return



    text = "🎟 Approved Entries\n\n"


    for entry in entries:

        text += f"{entry[1]}\n"



    await update.message.reply_text(
        text
    )



# ==========================================================
# DRAW RAFFLE
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        return



    raffle = get_active_raffle()


    if not raffle:

        return



    entries = get_approved_entries(
        raffle[0]
    )



    if not entries:

        await update.message.reply_text(
            "No approved entries."
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
"""
    )



# ==========================================================
# REROLL
# ==========================================================

async def reroll_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await draw_raffle(
        update,
        context
    )



# ==========================================================
# CANCEL
# ==========================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔥 Bonus entry feature coming soon."
    )



# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        return


    remove_entry(
        int(context.args[0])
    )


    await update.message.reply_text(
        "Entry removed."
    )
