# ==========================================================
# Melanated AZ Bot
# raffle.py
# Raffle System
# ==========================================================

import random

from telegram import Update
from telegram.ext import ContextTypes

from admin import is_admin


# ==========================================================
# TEMP RAFFLE STORAGE
# Will move to database.py
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

    if not update.effective_user:
        return


    user = update.effective_user


    if not raffle_data["active"]:

        await update.message.reply_text(
            "❌ There is no active raffle."
        )

        return



    for entry in raffle_data["entries"]:

        if entry["id"] == user.id:

            await update.message.reply_text(
                "✅ You are already entered."
            )

            return



    raffle_data["entries"].append(

        {
            "id": user.id,
            "name": user.first_name
        }

    )


    await update.message.reply_text(

        f"🎟️ {user.first_name}, you are entered!"

    )



# ==========================================================
# RAFFLE STATUS
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

Type:
 /enter

to join!
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


    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    if not raffle_data["active"]:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    if not raffle_data["entries"]:

        await update.message.reply_text(
            "❌ No entries yet."
        )

        return



    winner = random.choice(
        raffle_data["entries"]
    )


    prize = raffle_data["prize"]


    raffle_data["active"] = False
    raffle_data["entries"] = []


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


    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    raffle_data["active"] = False
    raffle_data["prize"] = ""
    raffle_data["entries"] = []


    await update.message.reply_text(

        "🛑 Raffle cancelled."

    )
