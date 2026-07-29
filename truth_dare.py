# ==========================================================
# Melanated AZ Bot
# truth_dare.py
# Advanced Truth or Dare System
# ==========================================================

import random

from telegram import Update
from telegram.ext import ContextTypes

from admin import is_admin

from database import get_db



# ==========================================================
# TRUTH QUESTIONS
# ==========================================================

TRUTHS = {

1: {
    "Icebreaker": [
        "What is something people would never guess about you?",
        "What is one thing on your bucket list?",
        "What is your biggest hidden talent?"
    ],

    "Fun": [
        "What is your funniest memory?",
        "What is your guilty pleasure?",
        "What is a weird habit you have?"
    ]
},


2: {
    "Fun": [
        "What is something you are proud of?",
        "What is your favorite way to relax?",
        "What is a hobby you want to try?"
    ],

    "Flirty": [
        "What catches your attention first about someone?",
        "What is your idea of a perfect date?",
        "What is your biggest turn on?"
    ]
},


3: {
    "Flirty": [
        "What is your biggest attraction trigger?",
        "What makes someone unforgettable?",
        "What is something romantic you enjoy?"
    ],

    "Spicy": [
        "What is something adventurous you want to try?",
        "What is a fantasy you have never shared?",
        "What is something that excites you?"
    ]
},


4: {
    "Spicy": [
        "What is something you have always wanted to explore?",
        "What is a boundary that matters to you?",
        "What makes a connection powerful?"
    ],

    "Lifestyle": [
        "What does trust mean to you?",
        "What does healthy communication look like?",
        "What is something you learned about relationships?"
    ]
},


5: {
    "Lifestyle": [
        "What experience changed your view on relationships?",
        "What does freedom mean to you?",
        "What is something you want more of in life?"
    ]
}

}



# ==========================================================
# DARES
# ==========================================================

DARES = {

1: {
    "Fun": [
        "Tell your funniest joke.",
        "Share your favorite song.",
        "Give someone in chat a compliment."
    ]
},


2: {
    "Flirty": [
        "Describe your perfect date.",
        "Give your best pickup line.",
        "Share your biggest green flag."
    ]
},


3: {
    "Spicy": [
        "Share something adventurous you want to experience.",
        "Describe your ideal vibe with someone.",
        "Say something confident about yourself."
    ]
},


4: {
    "Lifestyle": [
        "Share a lesson you learned about connections.",
        "Describe your ideal relationship dynamic.",
        "Share something you value deeply."
    ]
},


5: {
    "Lifestyle": [
        "Describe your dream experience.",
        "Share something you want to explore.",
        "Give advice about building trust."
    ]
}

}



# ==========================================================
# SETTINGS
# ==========================================================

def get_truth_status():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT enabled

    FROM truth_dare_settings

    WHERE id = 1
    """)


    result = cursor.fetchone()


    conn.close()


    if result:

        return result[0] == 1


    return True





def set_truth_status(enabled):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    UPDATE truth_dare_settings

    SET enabled = ?

    WHERE id = 1
    """,

    (
        1 if enabled else 0,
    ))


    conn.commit()

    conn.close()





# ==========================================================
# TRUTH
# ==========================================================

async def truth(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not get_truth_status():

        await update.message.reply_text(

            "🔥 Truth or Dare is currently disabled."

        )

        return



    level = random.randint(
        1,
        5
    )


    category = random.choice(

        list(
            TRUTHS[level].keys()
        )

    )


    question = random.choice(

        TRUTHS[level][category]

    )



    await update.message.reply_text(

f"""
🔥 TRUTH

⭐ Level: {level}

📂 Category: {category}

❓ {question}
"""

    )





# ==========================================================
# DARE
# ==========================================================

async def dare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not get_truth_status():

        await update.message.reply_text(

            "🔥 Truth or Dare is currently disabled."

        )

        return



    level = random.randint(
        1,
        5
    )


    category = random.choice(

        list(
            DARES[level].keys()
        )

    )


    challenge = random.choice(

        DARES[level][category]

    )



    await update.message.reply_text(

f"""
😈 DARE

⭐ Level: {level}

📂 Category: {category}

🔥 {challenge}
"""

    )





# ==========================================================
# ADMIN CONTROL
#
# /truthdare on
# /truthdare off
# /truthdare status
# ==========================================================

async def truthdare_control(
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

            "Usage:\n\n"
            "/truthdare on\n"
            "/truthdare off\n"
            "/truthdare status"

        )

        return



    option = context.args[0].lower()



    if option == "on":

        set_truth_status(
            True
        )

        await update.message.reply_text(

            "🔥 Truth or Dare enabled."

        )



    elif option == "off":

        set_truth_status(
            False
        )

        await update.message.reply_text(

            "🛑 Truth or Dare disabled."

        )



    elif option == "status":

        status = (

            "✅ Enabled"

            if get_truth_status()

            else

            "❌ Disabled"

        )


        await update.message.reply_text(

f"""
🔥 Truth or Dare Status

{status}
"""

        )



    else:

        await update.message.reply_text(

            "Invalid option."

        )
