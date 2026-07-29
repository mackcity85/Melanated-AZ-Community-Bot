# ==========================================================
# Melanated AZ Bot
# truth_dare.py
# Truth or Dare System
# ==========================================================

import random

from telegram import Update
from telegram.ext import ContextTypes

from admin import is_admin


# ==========================================================
# SETTINGS
# ==========================================================

TRUTH_DARE_ENABLED = True


# ==========================================================
# QUESTIONS
# ==========================================================

TRUTHS = {

    "mild": [

        "What is something people assume about you that is wrong?",
        "What is a hidden talent you have?",
        "What is your biggest green flag?",
        "What is something you want to accomplish this year?"

    ],


    "spicy": [

        "What is something that instantly attracts you to someone?",
        "What is a fantasy you have never shared?",
        "What is your biggest turn on?",
        "What is something you secretly enjoy?"

    ],


    "extreme": [

        "What is a boundary you will never cross?",
        "What is something adventurous you want to try?",
        "What is the wildest experience you have had?",
        "What is something people would never guess about you?"

    ]

}



DARES = {


    "mild": [

        "Give someone in the chat a compliment.",
        "Share your favorite song.",
        "Tell the group something positive about yourself."

    ],


    "spicy": [

        "Send a flirty compliment to someone.",
        "Describe your perfect date.",
        "Share your favorite way to relax."

    ],


    "extreme": [

        "Share a secret bucket list item.",
        "Describe your dream adventure.",
        "Tell the group something bold you want to experience."

    ]

}



# ==========================================================
# ENABLE / DISABLE
# ==========================================================

async def toggle_truth_dare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global TRUTH_DARE_ENABLED


    if not await is_admin(update, context):

        return



    TRUTH_DARE_ENABLED = not TRUTH_DARE_ENABLED



    status = (
        "ENABLED"
        if TRUTH_DARE_ENABLED
        else "DISABLED"
    )


    await update.message.reply_text(

        f"🔥 Truth or Dare is now {status}"

    )



# ==========================================================
# TRUTH COMMAND
# ==========================================================

async def truth(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not TRUTH_DARE_ENABLED:

        await update.message.reply_text(
            "🔥 Truth or Dare is currently disabled."
        )

        return



    level = "mild"


    if context.args:

        level = context.args[0].lower()



    if level not in TRUTHS:

        level = "mild"



    question = random.choice(
        TRUTHS[level]
    )



    await update.message.reply_text(

f"""
🔥 TRUTH ({level.upper()})

{question}
"""

    )



# ==========================================================
# DARE COMMAND
# ==========================================================

async def dare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not TRUTH_DARE_ENABLED:

        await update.message.reply_text(
            "🔥 Truth or Dare is currently disabled."
        )

        return



    level = "mild"


    if context.args:

        level = context.args[0].lower()



    if level not in DARES:

        level = "mild"



    challenge = random.choice(
        DARES[level]
    )



    await update.message.reply_text(

f"""
🔥 DARE ({level.upper()})

{challenge}
"""

    )



# ==========================================================
# HELP COMMAND
# ==========================================================

async def truth_dare_help(
    update,
    context
):

    await update.message.reply_text(

"""
🔥 Truth or Dare

Commands:

/truth
/truth mild
/truth spicy
/truth extreme

/dare
/dare mild
/dare spicy
/dare extreme


Admin:

/toggletruthdare
"""

    )
