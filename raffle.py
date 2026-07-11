# ==========================================================
# Melanated AZ Bot
# Raffle System v1.0
# ==========================================================

import random
from datetime import datetime
import sqlite3

from telegram import Update
from telegram.ext import ContextTypes


DB_FILE = "database/bot.db"


# ==========================================================
# DATABASE
# ==========================================================

def get_db():

    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )



def initialize_raffle():

    conn = get_db()
    cursor = conn.cursor()


    # Active raffle entries

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_entries (

        user_id INTEGER PRIMARY KEY,

        username TEXT,

        joined_date TEXT

    )
    """)



    # Current raffle

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_settings (

        id INTEGER PRIMARY KEY,

        active INTEGER DEFAULT 0,

        prize TEXT

    )
    """)



    # Raffle history

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raffle_history (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        prize TEXT,

        winner TEXT,

        total_entries INTEGER,

        date TEXT

    )
    """)



    cursor.execute("""
    INSERT OR IGNORE INTO raffle_settings
    (
        id,
        active,
        prize
    )

    VALUES
    (
        1,
        0,
        ''
    )
    """)


    conn.commit()
    conn.close()


# ==========================================================
# SHOW CURRENT RAFFLE
# ==========================================================

async def raffle_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    conn=get_db()
    cursor=conn.cursor()


    cursor.execute("""
    SELECT active, prize
    FROM raffle_settings
    WHERE id=1
    """)

    raffle=cursor.fetchone()



    cursor.execute("""
    SELECT COUNT(*)
    FROM raffle_entries
    """)

    count=cursor.fetchone()[0]


    conn.close()



    if raffle[0] == 0:

        await update.message.reply_text(
            "🎟 There is currently no active raffle."
        )

        return



    await update.message.reply_text(
f"""
🎉 MELANATED AZ RAFFLE 🎉


🎁 Prize:

{raffle[1]}


👥 Current Entries:

{count}


Enter now:

/joinraffle
"""
)



# ==========================================================
# JOIN RAFFLE
# ==========================================================

async def join_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user=update.effective_user


    conn=get_db()
    cursor=conn.cursor()



    cursor.execute("""
    SELECT active
    FROM raffle_settings
    WHERE id=1
    """)


    active=cursor.fetchone()[0]


    if active == 0:

        conn.close()

        await update.message.reply_text(
            "❌ No raffle is active right now."
        )

        return



    cursor.execute("""
    SELECT user_id
    FROM raffle_entries
    WHERE user_id=?
    """,
    (user.id,))


    exists=cursor.fetchone()



    if exists:

        conn.close()

        await update.message.reply_text(
            "🎟 You are already entered!"
        )

        return



    cursor.execute("""
    INSERT INTO raffle_entries

    (
        user_id,
        username,
        joined_date
    )

    VALUES (?,?,?)

    """,
    (
        user.id,
        user.username or user.first_name,
        datetime.now().strftime("%Y-%m-%d")
    ))



    conn.commit()
    conn.close()



    await update.message.reply_text(
        "🎟 You have been entered into the raffle! Good luck 👑"
    )



# ==========================================================
# START RAFFLE (ADMIN)
# ==========================================================

async def start_raffle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    prize=" ".join(context.args)



    if not prize:

        await update.message.reply_text(
            "Example:\n/startraffle $50 Gift Card"
        )

        return



    conn=get_db()
    cursor=conn.cursor()



    cursor.execute(
        "DELETE FROM raffle_entries"
    )



    cursor.execute("""
    UPDATE raffle_settings

    SET active=1,
        prize=?

    WHERE id=1

    """,
    (prize,))


    conn.commit()
    conn.close()



    await update.message.reply_text(
f"""
🎉 RAFFLE STARTED 🎉


🎁 Prize:

{prize}


Enter:

/joinraffle


Good luck everyone! 👑
"""
)



# ==========================================================
# PICK RANDOM WINNER
# ==========================================================

async def raffle_winner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    conn=get_db()
    cursor=conn.cursor()



    cursor.execute("""
    SELECT username
    FROM raffle_entries
    """)


    entries=cursor.fetchall()



    if not entries:

        conn.close()

        await update.message.reply_text(
            "❌ No entries yet."
        )

        return



    winner=random.choice(entries)[0]



    cursor.execute("""
    SELECT prize
    FROM raffle_settings
    WHERE id=1
    """)


    prize=cursor.fetchone()[0]



    cursor.execute("""
    INSERT INTO raffle_history

    (
        prize,
        winner,
        total_entries,
        date
    )

    VALUES (?,?,?,?)

    """,
    (
        prize,
        winner,
        len(entries),
        datetime.now().strftime("%Y-%m-%d")
    ))



    cursor.execute("""
    UPDATE raffle_settings

    SET active=0

    WHERE id=1
    """)



    conn.commit()
    conn.close()



    await update.message.reply_text(
f"""
🏆 RAFFLE WINNER 🏆


🎁 Prize:

{prize}


👑 Winner:

{winner}


🎟 Total Entries:

{len(entries)}


Congratulations! 🎉
"""
)
