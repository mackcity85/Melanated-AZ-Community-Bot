# ==========================================================
# Melanated AZ Bot
# raffle.py
# ==========================================================

import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    create_raffle_entry,
    get_raffle_entries,
    clear_raffle_entries
)



# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id, context):

    admin_ids = context.bot_data.get(
        "ADMIN_IDS",
        []
    )

    return user_id in admin_ids



# ==========================================================
# VIEW CURRENT RAFFLE
# ==========================================================

async def raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    entries = get_raffle_entries(
        update.effective_chat.id
    )


    if not entries:

        await update.message.reply_text(
            """
🎟️ Current Raffle

No entries yet.

Use:
/joinraffle

to enter!
"""
        )

        return



    await update.message.reply_text(
        f"""
🎟️ Melanated AZ Raffle

Current Entries:
{len(entries)}

Good luck everyone! 🍀

Use:
/joinraffle
to enter.
"""
    )



# ==========================================================
# JOIN RAFFLE
# ==========================================================

async def join_raffle_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    create_raffle_entry(
        update.effective_chat.id,
        user.id,
        user.first_name,
        user.username
    )


    await update.message.reply_text(
        f"""
🎟️ Entry Added!

Good luck {user.first_name}! 🍀

You are now entered into the Melanated AZ raffle.
"""
    )



# ==========================================================
# CREATE RAFFLE (ADMIN ONLY)
# ==========================================================

async def create_raffle_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id,
        context
    ):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    clear_raffle_entries(
        update.effective_chat.id
    )



    await update.message.reply_text(
        """
🎟️ New Raffle Started!

Everyone can enter using:

/joinraffle

Good luck! 🍀
"""
    )



# ==========================================================
# DRAW RAFFLE (ADMIN ONLY)
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):


    if not is_admin(
        update.effective_user.id,
        context
    ):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    entries = get_raffle_entries(
        update.effective_chat.id
    )



    if not entries:


        await update.message.reply_text(
            "❌ No raffle entries."
        )

        return



    winner = random.choice(
        entries
    )



    await update.message.reply_text(
        f"""
🎉 RAFFLE WINNER 🎉

👑 {winner['first_name']}

Congratulations!

Thank you everyone who participated.
"""
    )



    clear_raffle_entries(
        update.effective_chat.id
    )
