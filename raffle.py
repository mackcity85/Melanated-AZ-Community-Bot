# ==========================================================
# Melanated AZ Bot
# raffle.py
# Paid Raffle System
# ==========================================================

import random

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
${RAFFLE_ENTRY_COST}

Payment:
💵 CashApp: {CASHAPP_TAG}
💳 Zelle: {ZELLE_EMAIL}

After payment send:

/paid cashapp

or

/paid zelle
"""
    )



# ==========================================================
# PAYMENT ENTRY
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
            "Use:\n/paid cashapp\nor\n/paid zelle"
        )

        return



    method = context.args[0].lower()



    if method not in [
        "cashapp",
        "zelle"
    ]:

        await update.message.reply_text(
            "Payment must be cashapp or zelle."
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
"""
✅ Payment submitted

Your raffle entry is pending approval.

Thank you for supporting Melanated AZ 🔥
"""
    )



# ==========================================================
# PENDING
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        return



    entries = get_pending_entries()



    if not entries:

        await update.message.reply_text(
            "No pending payments."
        )

        return



    msg = "⏳ Pending Payments\n\n"


    for entry in entries:

        msg += (
            f"ID: {entry[0]}\n"
            f"User: {entry[1]}\n"
            f"Method: {entry[2]}\n\n"
        )



    msg += (
        "Approve:\n"
        "/approveentry ID\n\n"
        "Deny:\n"
        "/denyentry ID"
    )



    await update.message.reply_text(
        msg
    )



# ==========================================================
# APPROVE
# ==========================================================

async def approve_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        return



    if not context.args:

        return



    approve_entry(
        int(
            context.args[0]
        )
    )



    await update.message.reply_text(
        "✅ Entry approved."
    )



# ==========================================================
# DENY
# ==========================================================

async def deny_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        return



    deny_entry(
        int(
            context.args[0]
        )
    )



    await update.message.reply_text(
        "❌ Entry denied."
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
🎟 Active Raffle

🏆 {raffle[1]}

Entry:
${RAFFLE_ENTRY_COST}
"""
    )



# ==========================================================
# ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        return



    raffle = get_active_raffle()



    if not raffle:

        return



    entries = get_approved_entries(
        raffle[0]
    )



    msg = "🎟 Paid Entries\n\n"



    for e in entries:

        msg += (
            f"{e[1]}\n"
        )



    await update.message.reply_text(
        msg
    )



# ==========================================================
# DRAW
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        return



    raffle = get_active_raffle()



    if not raffle:

        return



    entries = get_approved_entries(
        raffle[0]
    )



    if not entries:

        await update.message.reply_text(
            "No paid entries."
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
        "Bonus entries coming soon."
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
        int(
            context.args[0]
        )
    )


    await update.message.reply_text(
        "Entry removed."
    )
