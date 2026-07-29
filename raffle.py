# ==========================================================
# Melanated AZ Bot
# raffle.py
# Persistent Raffle System
# ==========================================================

import random

from telegram import Update
from telegram.ext import ContextTypes

from admin import is_admin

from raffle_database import (
    init_raffle_db,
    create_raffle,
    get_active_raffle,
    add_entry,
    get_entries,
    count_entries,
    add_bonus,
    remove_entry,
    save_winner,
    cancel_raffle as db_cancel_raffle
)


# Initialize raffle database
init_raffle_db()



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
            "Usage:\n/startraffle Prize Name"
        )

        return



    existing = get_active_raffle()

    if existing:

        await update.message.reply_text(
            "❌ A raffle is already active."
        )

        return



    prize = " ".join(context.args)


    create_raffle(
        prize,
        update.effective_user.id
    )


    await update.message.reply_text(

f"""
🎟️ RAFFLE STARTED 🎟️

🏆 Prize:
{prize}

How to enter:

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


    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    success = add_entry(

        raffle["id"],

        user.id,

        user.username,

        user.full_name

    )


    if not success:

        await update.message.reply_text(
            "✅ You are already entered."
        )

        return



    await update.message.reply_text(

        f"🎟️ {user.full_name}, you are entered!"

    )



# ==========================================================
# RAFFLE STATUS
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



    await update.message.reply_text(

f"""
🎟️ CURRENT RAFFLE

🏆 Prize:
{raffle["prize"]}

👥 Entries:
{count_entries(raffle["id"])}

Enter:
 /enter
"""

    )



# ==========================================================
# SHOW ENTRIES
# ADMIN ONLY
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


    if not entries:

        await update.message.reply_text(
            "🎟️ No entries yet."
        )

        return



    message = "🎟️ CURRENT ENTRIES\n\n"


    for number, entry in enumerate(
        entries,
        start=1
    ):

        message += (

            f"{number}. "
            f"{entry['display_name']} "
            f"({entry['entries']} entries)\n"

        )


    await update.message.reply_text(
        message
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



    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    entries = get_entries(
        raffle["id"]
    )


    if not entries:

        await update.message.reply_text(
            "❌ No entries."
        )

        return



    pool = []


    for entry in entries:

        for _ in range(entry["entries"]):

            pool.append(entry)



    winner = random.choice(pool)



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
# REROLL WINNER
# ADMIN ONLY
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



    raffle = get_active_raffle()


    if raffle:

        db_cancel_raffle(
            raffle["id"]
        )


    await update.message.reply_text(

        "🛑 Raffle cancelled."

    )



# ==========================================================
# BONUS ENTRIES
# ADMIN ONLY
# ==========================================================

async def bonus_entry(
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
            "/bonus user_id amount"

        )

        return



    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    user_id = int(
        context.args[0]
    )


    amount = int(
        context.args[1]
    )


    add_bonus(

        raffle["id"],

        user_id,

        amount

    )


    await update.message.reply_text(

        "✅ Bonus entries added."

    )



# ==========================================================
# REMOVE ENTRY
# ADMIN ONLY
# ==========================================================

async def remove_raffle_entry(
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
            "/removeentry user_id"

        )

        return



    raffle = get_active_raffle()


    if not raffle:

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    remove_entry(

        raffle["id"],

        int(context.args[0])

    )


    await update.message.reply_text(

        "✅ Entry removed."

    )
