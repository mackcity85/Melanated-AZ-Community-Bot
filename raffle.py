# ==========================================================
# Melanated AZ Bot
# raffle.py
# Raffle System
# ==========================================================

import random

from telegram import Update
from telegram.ext import ContextTypes

from admin import is_admin

from database import (
    add_raffle_entry
)



# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

raffle_data = {

    "active": False,
    "prize": "",
    "entries": []

}



# ==========================================================
# START RAFFLE
# ADMIN ONLY
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(
        update,
        context
    ):

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



    prize = " ".join(
        context.args
    )


    raffle_data["active"] = True
    raffle_data["prize"] = prize
    raffle_data["entries"] = []



    await update.message.reply_text(

f"""
🎟️ RAFFLE STARTED 🎟️

🏆 Prize:
{prize}

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

    user = update.effective_user


    if not raffle_data["active"]:

        await update.message.reply_text(

            "❌ No active raffle."

        )

        return



    for entry in raffle_data["entries"]:

        if entry["id"] == user.id:

            await update.message.reply_text(

                "✅ You are already entered."

            )

            return



    entry = {

        "id": user.id,
        "name": user.first_name

    }


    raffle_data["entries"].append(
        entry
    )


    add_raffle_entry(

        user.id,
        user.username,
        raffle_data["prize"]

    )


    await update.message.reply_text(

        f"🎟️ {user.first_name}, you are entered!"

    )



# ==========================================================
# SHOW RAFFLE
# ==========================================================

async def raffle_status(
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
🎟️ CURRENT RAFFLE

🏆 Prize:
{raffle_data["prize"]}

👥 Entries:
{len(raffle_data["entries"])}

Enter:
 /enter
"""

    )



# ==========================================================
# DRAW WINNER
# ADMIN ONLY
# ==========================================================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(
        update,
        context
    ):

        await update.message.reply_text(

            "❌ Admins only."

        )

        return



    if not raffle_data["entries"]:

        await update.message.reply_text(

            "❌ No entries."

        )

        return



    winner = random.choice(

        raffle_data["entries"]

    )


    prize = raffle_data["prize"]



    raffle_data["active"] = False
    raffle_data["entries"] = []
    raffle_data["prize"] = ""



    await update.message.reply_text(

f"""
🎉 RAFFLE WINNER 🎉

🏆 Prize:
{prize}

👑 Winner:
{winner["name"]}

Congratulations! 🎊
"""

    )



# ==========================================================
# CANCEL RAFFLE
# ADMIN ONLY
# ==========================================================

async def cancel_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(
        update,
        context
    ):

        await update.message.reply_text(

            "❌ Admins only."

        )

        return



    raffle_data["active"] = False
    raffle_data["entries"] = []
    raffle_data["prize"] = ""



    await update.message.reply_text(

        "🛑 Raffle cancelled."

    )
