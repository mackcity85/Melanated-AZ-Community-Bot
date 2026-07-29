# ==========================================================
# Melanated AZ Bot
# raffle.py
# Automatic Raffle System
# ==========================================================

import random

from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from admin import is_admin

from raffle_database import (
    init_raffle_db,
    create_raffle,
    get_active_raffle,
    add_entry,
    get_entries,
    save_winner,
    cancel_raffle as db_cancel_raffle
)



# Initialize raffle tables

init_raffle_db()



# ==========================================================
# START RAFFLE
# /startraffle Prize Hours
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
            "/startraffle Prize Name Hours\n\n"
            "Example:\n"
            "/startraffle $25 Amazon Gift Card 24"

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
        timedelta(hours=hours)
    ).isoformat()



    raffle_id = create_raffle(

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

⏰ Duration:
{hours} hours

To enter:

/enter

Good luck everyone! 🍀
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



    success = add_entry(

        raffle["id"],

        user.id,

        user.username,

        user.first_name

    )



    if not success:

        await update.message.reply_text(

            "✅ You are already entered."

        )

        return



    await update.message.reply_text(

        f"🎟️ {user.first_name}, you are entered!"

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

👥 Entries:
{len(entries)}

⏰ Ends:
{raffle["end_time"]}

Use:

/enter
"""

    )





# ==========================================================
# SHOW ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

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



    entries = get_entries(
        raffle["id"]
    )


    text = "🎟️ ENTRIES\n\n"


    for number, entry in enumerate(
        entries,
        start=1
    ):

        text += (
            f"{number}. "
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

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    await pick_winner(
        update,
        context
    )





# ==========================================================
# WINNER PICKER
# ==========================================================

async def pick_winner(
    update,
    context
):

    raffle = get_active_raffle()


    if not raffle:

        return



    entries = get_entries(
        raffle["id"]
    )


    if not entries:

        await update.message.reply_text(
            "❌ No entries."
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

    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    raffle = get_active_raffle()


    if raffle:

        db_cancel_raffle(
            raffle["id"]
        )


    await update.message.reply_text(

        "🛑 Raffle cancelled."

    )





# ==========================================================
# BONUS ENTRY
# ==========================================================

async def bonus_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎟️ Bonus entries coming soon."

    )





# ==========================================================
# REMOVE ENTRY
# ==========================================================

async def remove_raffle_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎟️ Remove entry feature coming soon."

    )
