# ==========================================================
# Melanated AZ Bot
# raffle.py
# Payment Verified Raffle System
# ==========================================================

import random

from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from admin import is_admin

from config import (
    CASHAPP_TAG,
    ZELLE_INFO,
    DEFAULT_RAFFLE_ENTRY
)


from raffle_database import (
    init_raffle_db,
    create_raffle,
    get_active_raffle,
    add_pending_entry,
    get_pending_entries,
    approve_entry,
    deny_entry,
    get_entries,
    save_winner,
    cancel_raffle as db_cancel_raffle
)



# Create tables

init_raffle_db()



# ==========================================================
# START RAFFLE
#
# /startraffle Prize Hours
#
# Example:
# /startraffle $50 Gift Card 24
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



    if len(context.args) < 2:

        await update.message.reply_text(

            "Usage:\n"
            "/startraffle Prize Hours\n\n"
            "Example:\n"
            "/startraffle $50 Gift Card 24"

        )

        return



    try:

        hours = int(
            context.args[-1]
        )

    except:

        await update.message.reply_text(
            "❌ Last value must be hours."
        )

        return



    prize = " ".join(
        context.args[:-1]
    )


    end_time = (

        datetime.now()

        +

        timedelta(
            hours=hours
        )

    ).isoformat()



    create_raffle(

        prize,

        update.effective_chat.id,

        update.effective_user.id,

        end_time

    )



    await update.message.reply_text(

f"""
🎟️ RAFFLE STARTED 🎟️

🏆 Prize:
{prize}

💵 Entry:
{DEFAULT_RAFFLE_ENTRY}

Payment Options:

💚 Cash App:
{CASHAPP_TAG}

💙 Zelle:
{ZELLE_INFO}


After payment:

Use:
/enter

An admin will verify your entry.

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

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    user = update.effective_user



    add_pending_entry(

        raffle["id"],

        user.id,

        user.username,

        user.first_name

    )



    await update.message.reply_text(

f"""
💳 Payment Verification Submitted

User:
{user.first_name}

Your entry is waiting for admin approval.

Thank you! 🎟️
"""

    )





# ==========================================================
# SHOW RAFFLE STATUS
# ==========================================================

async def raffle_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    entries = get_entries(
        raffle["id"]
    )



    await update.message.reply_text(

f"""
🎟️ CURRENT RAFFLE

🏆 Prize:
{raffle["prize"]}

✅ Approved Entries:
{len(entries)}

⏰ Ends:
{raffle["end_time"]}
"""

    )





# ==========================================================
# ADMIN VIEW PENDING
# ==========================================================

async def pending_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    pending = get_pending_entries()



    if not pending:

        await update.message.reply_text(
            "No pending entries."
        )

        return



    text = "💳 PENDING PAYMENTS\n\n"


    for item in pending:

        text += (

            f"ID: {item['id']}\n"

            f"Name: {item['display_name']}\n"

            f"User ID: {item['user_id']}\n\n"

        )


    await update.message.reply_text(
        text
    )





# ==========================================================
# APPROVE PAYMENT
#
# /approveentry ID
# ==========================================================

async def approve_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    if not context.args:

        await update.message.reply_text(
            "Usage: /approveentry ID"
        )

        return



    result = approve_entry(
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
# DENY PAYMENT
#
# /denyentry ID
# ==========================================================

async def deny_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    if not context.args:

        await update.message.reply_text(
            "Usage: /denyentry ID"
        )

        return



    deny_entry(
        int(context.args[0])
    )


    await update.message.reply_text(
        "🛑 Entry denied."
    )





# ==========================================================
# SHOW APPROVED ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        return



    raffle = get_active_raffle()


    if not raffle:

        return



    entries = get_entries(
        raffle["id"]
    )


    text = "🎟️ APPROVED ENTRIES\n\n"


    for entry in entries:

        text += (

            f"{entry['display_name']}\n"

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

        return



    entries = get_entries(
        raffle["id"]
    )


    if not entries:

        await update.message.reply_text(
            "❌ No approved entries."
        )

        return



    winner = random.choice(
        entries
    )



    save_winner(

        raffle["id"],

        winner["user_id"],

        winner["display_name"]

    )



    await update.message.reply_text(

f"""
🎉 RAFFLE WINNER 🎉

🏆 Prize:
{raffle["prize"]}

👑 Winner:
{winner["display_name"]}

Congratulations! 🎊
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

        db_cancel_raffle(
            raffle["id"]
        )


    await update.message.reply_text(
        "🛑 Raffle cancelled."
    )





# ==========================================================
# PLACEHOLDER COMMANDS
# ==========================================================

async def bonus_entry(
    update,
    context
):

    await update.message.reply_text(
        "🎟 Bonus entries disabled."
    )



async def remove_raffle_entry(
    update,
    context
):

    await update.message.reply_text(
        "🎟 Remove entry disabled."
    )
