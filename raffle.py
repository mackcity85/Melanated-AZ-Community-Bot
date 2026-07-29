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

🎁 Prize:
{prize}

💰 Entry:
${RAFFLE_ENTRY_COST}

To enter:

1. Send payment:
💵 CashApp: {CASHAPP_TAG}
💳 Zelle: {ZELLE_EMAIL}

2. Then type:

/paid CashApp

or

/paid Zelle

Entry will be approved by admin.
"""
    )



# ==========================================================
# ENTER
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
🎟 Raffle Entry

Prize:
{raffle[1]}

Cost:
${RAFFLE_ENTRY_COST}

Send payment:

CashApp:
{CASHAPP_TAG}

Zelle:
{ZELLE_EMAIL}

After payment type:

/paid CashApp

or

/paid Zelle
"""
    )



# ==========================================================
# PAID
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


    username = (
        update.effective_user.username
        or update.effective_user.first_name
    )


    add_raffle_entry(
        raffle[0],
        update.effective_user.id,
        username,
        method
    )


    await update.message.reply_text(
        """
✅ Payment submitted!

Your entry is pending admin verification.

Good luck! 🍀
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



    message = "🎟 Pending Entries\n\n"


    for entry in entries:

        message += (
            f"ID: {entry[0]}\n"
            f"User: {entry[1]}\n"
            f"Payment: {entry[2]}\n\n"
        )


    message += (
        "Approve:\n"
        "/approveentry ID\n\n"
        "Deny:\n"
        "/denyentry ID"
    )


    await update.message.reply_text(
        message
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

        await update.message.reply_text(
            "Example:\n/approveentry 5"
        )

        return



    entry_id = int(
        context.args[0]
    )


    approve_entry(
        entry_id
    )


    await update.message.reply_text(
        f"✅ Entry {entry_id} approved."
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



    entry_id = int(
        context.args[0]
    )


    deny_entry(
        entry_id
    )


    await update.message.reply_text(
        f"❌ Entry {entry_id} denied."
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

Prize:
{raffle[1]}

Winner:
@{winner[1]}

Congratulations! 🔥
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


    if not raffle:

        await update.message.reply_text(
            "No active raffle."
        )

        return



    await update.message.reply_text(
        f"""
🎟 Active Raffle

Prize:
{raffle[1]}

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

    entries = get_approved_entries(
        get_active_raffle()[0]
    )


    await update.message.reply_text(
        f"🎟 Approved Entries: {len(entries)}"
    )



# ==========================================================
# STUB COMMANDS
# ==========================================================

async def reroll_raffle(update, context):

    await draw_raffle(update, context)



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
        "Bonus entries coming soon."
    )



async def remove_raffle_entry(update, context):

    if context.args:

        remove_entry(
            int(context.args[0])
        )

    await update.message.reply_text(
        "Entry removed."
    )
