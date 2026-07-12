# ==========================================================
# raffle.py
# Melanated AZ Bot v3
# Raffle System
# ==========================================================

import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    create_raffle,
    close_raffle,
    get_active_raffle,
    add_raffle_entry,
    get_raffle_entries,
    clear_raffle
)

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

async def is_admin(update: Update, context):

    user = update.effective_user
    chat = update.effective_chat

    admins = await context.bot.get_chat_administrators(
        chat.id
    )

    return any(
        admin.user.id == user.id
        for admin in admins
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
            "Usage:\n"
            "/startraffle Prize Name"
        )

        return


    prize = " ".join(context.args)


    create_raffle(
        update.effective_chat.id,
        prize
    )


    await update.message.reply_text(
        "🎟️ RAFFLE STARTED!\n\n"
        f"🏆 Prize:\n{prize}\n\n"
        "To enter type:\n"
        "/joinraffle"
    )


# ==========================================================
# JOIN RAFFLE
# ==========================================================

async def join_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    raffle = get_active_raffle(
        update.effective_chat.id
    )


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return


    result = add_raffle_entry(
        raffle["id"],
        update.effective_user.id,
        update.effective_user.first_name
    )


    if result:

        await update.message.reply_text(
            "🎟️ You have been entered!"
        )

    else:

        await update.message.reply_text(
            "⚠️ You are already entered."
        )


# ==========================================================
# VIEW ENTRIES
# ==========================================================

async def raffle_entries(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    raffle = get_active_raffle(
        update.effective_chat.id
    )


    if not raffle:

        await update.message.reply_text(
            "No active raffle."
        )

        return


    entries = get_raffle_entries(
        raffle["id"]
    )


    if not entries:

        await update.message.reply_text(
            "No entries yet."
        )

        return


    message = (
        "🎟️ Raffle Entries\n\n"
    )


    for number, entry in enumerate(
        entries,
        start=1
    ):

        message += (
            f"{number}. {entry['name']}\n"
        )


    await update.message.reply_text(
        message
    )


# ==========================================================
# PICK WINNER
# ==========================================================

async def raffle_winner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return


    raffle = get_active_raffle(
        update.effective_chat.id
    )


    if not raffle:

        await update.message.reply_text(
            "No active raffle."
        )

        return


    entries = get_raffle_entries(
        raffle["id"]
    )


    if not entries:

        await update.message.reply_text(
            "No entries."
        )

        return


    winner = random.choice(
        entries
    )


    await update.message.reply_text(
        "🎉🎉 WINNER 🎉🎉\n\n"
        f"Congratulations {winner['name']}!\n\n"
        f"🏆 Prize:\n{raffle['prize']}"
    )


# ==========================================================
# END RAFFLE
# ==========================================================

async def end_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return


    close_raffle(
        update.effective_chat.id
    )


    clear_raffle()


    await update.message.reply_text(
        "🎟️ Raffle closed."
    )
