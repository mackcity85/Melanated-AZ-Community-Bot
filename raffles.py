import sqlite3
import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import DB_FILE, RAFFLE_PAYMENT_INFO


# ==========================
# CHECK ADMIN
# ==========================

async def is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat


    member = await context.bot.get_chat_member(
        chat.id,
        user.id
    )


    return member.status in [
        "administrator",
        "creator"
    ]



# ==========================
# START RAFFLE
# ==========================

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
            "/raffle_start amount prize\n\n"
            "Example:\n"
            "/raffle_start 5 $100 Gift Card"

        )

        return



    amount = context.args[0]

    prize = " ".join(
        context.args[1:]
    )

    chat_id = update.effective_chat.id


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffles
        SET active=0
        WHERE chat_id=?
        """,
        (chat_id,)
    )


    cursor.execute(
        """
        INSERT INTO raffles
        (
            chat_id,
            prize,
            amount,
            active
        )
        VALUES (?, ?, ?, 1)
        """,
        (
            chat_id,
            prize,
            amount
        )
    )


    conn.commit()
    conn.close()



    await update.message.reply_text(

        "💜 MELANATED AZ RAFFLE 💜\n\n"

        f"🏆 Prize:\n{prize}\n\n"

        f"🎟 Entry Cost:\n${amount}\n\n"

        f"{RAFFLE_PAYMENT_INFO}\n"

        "After payment:\n"
        "/enter\n\n"

        "Good luck everyone! 🍀"

    )



# ==========================
# ENTER RAFFLE
# ==========================

async def enter_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT id, prize, amount
        FROM raffles
        WHERE chat_id=?
        AND active=1
        """,
        (chat.id,)
    )


    raffle = cursor.fetchone()



    if not raffle:

        conn.close()

        await update.message.reply_text(
            "❌ No active raffle."
        )

        return



    raffle_id, prize, amount = raffle



    try:

        cursor.execute(
            """
            INSERT INTO raffle_entries
            (
                raffle_id,
                user_id,
                username
            )
            VALUES (?, ?, ?)
            """,
            (
                raffle_id,
                user.id,
                user.first_name
            )
        )


        conn.commit()



        await update.message.reply_text(

            "✅ You are entered!\n\n"

            f"🏆 Prize:\n{prize}\n\n"

            f"🎟 Entry: ${amount}\n\n"

            "Good luck! 🍀"

        )


    except sqlite3.IntegrityError:

        await update.message.reply_text(

            "⚠️ You are already entered."

        )


    finally:

        conn.close()



# ==========================
# LIST ENTRIES
# ==========================

async def raffle_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT id, prize
        FROM raffles
        WHERE chat_id=?
        AND active=1
        """,
        (chat.id,)
    )


    raffle = cursor.fetchone()



    if not raffle:

        conn.close()

        await update.message.reply_text(
            "No active raffle."
        )

        return



    cursor.execute(
        """
        SELECT username
        FROM raffle_entries
        WHERE raffle_id=?
        """,
        (raffle[0],)
    )


    entries = cursor.fetchall()

    conn.close()



    message = (

        "🎟️ Raffle Entries\n\n"

    )


    for number, entry in enumerate(entries, 1):

        message += f"{number}. {entry[0]}\n"



    message += (
        f"\nTotal Entries: {len(entries)}"
    )



    await update.message.reply_text(
        message
    )



# ==========================
# DRAW WINNER
# ==========================

async def draw_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return



    chat = update.effective_chat


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT id, prize
        FROM raffles
        WHERE chat_id=?
        AND active=1
        """,
        (chat.id,)
    )


    raffle = cursor.fetchone()



    if not raffle:

        conn.close()

        await update.message.reply_text(
            "No active raffle."
        )

        return



    raffle_id, prize = raffle



    cursor.execute(
        """
        SELECT username
        FROM raffle_entries
        WHERE raffle_id=?
        """,
        (raffle_id,)
    )


    entries = cursor.fetchall()



    if not entries:

        conn.close()

        await update.message.reply_text(
            "No entries."
        )

        return



    winner = random.choice(entries)[0]



    cursor.execute(
        """
        UPDATE raffles
        SET active=0
        WHERE id=?
        """,
        (raffle_id,)
    )


    conn.commit()
    conn.close()



    await update.message.reply_text(

        "🎉 WINNER 🎉\n\n"

        f"🏆 Prize:\n{prize}\n\n"

        f"👑 Winner:\n{winner}\n\n"

        "Congratulations! 💜"

    )



# ==========================
# CLOSE RAFFLE
# ==========================

async def close_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await is_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return


    chat_id = update.effective_chat.id


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE raffles
        SET active=0
        WHERE chat_id=?
        """,
        (chat_id,)
    )


    conn.commit()
    conn.close()



    await update.message.reply_text(

        "🛑 Raffle closed."

    )
