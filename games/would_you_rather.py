# ==========================================================
# Melanated AZ Bot
# games/would_you_rather.py
#
# WOULD YOU RATHER
#
# Features:
#   - Button-based game
#   - Mild
#   - Spicy
#   - Extreme
#   - Random questions
#   - Vote buttons
#   - Next question
#   - Change level
#   - PASS always allowed
#   - Consent-focused
#
# This file does not import games.py.
# This prevents circular imports.
# ==========================================================

import logging
import random

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


# ==========================================================
# SETTINGS
# ==========================================================

WOULD_YOU_RATHER_ENABLED = True

VALID_LEVELS = (
    "mild",
    "spicy",
    "extreme",
)


# ==========================================================
# QUESTIONS
# ==========================================================

QUESTIONS = {

    "mild": [

        (
            "Would you rather have a perfect first date "
            "or an unforgettable first kiss?"
        ),

        (
            "Would you rather be the one who makes "
            "the first move or be approached?"
        ),

        (
            "Would you rather have amazing chemistry "
            "or amazing conversation?"
        ),

        (
            "Would you rather go on a spontaneous road trip "
            "or plan the perfect weekend getaway?"
        ),

        (
            "Would you rather receive a thoughtful message "
            "or an unexpected compliment?"
        ),

        (
            "Would you rather be mysterious or completely "
            "open about your intentions?"
        ),

        (
            "Would you rather meet someone at a party "
            "or through an online community?"
        ),

        (
            "Would you rather have a romantic dinner "
            "or a fun night out?"
        ),

        (
            "Would you rather be the flirt or the one being flirted with?"
        ),

        (
            "Would you rather have someone make you laugh "
            "or make you feel completely comfortable?"
        ),

        (
            "Would you rather have instant chemistry "
            "or chemistry that slowly builds?"
        ),

        (
            "Would you rather receive flowers "
            "or receive your favorite food?"
        ),

        (
            "Would you rather stay home for date night "
            "or go somewhere completely new?"
        ),

        (
            "Would you rather know exactly what someone thinks "
            "or keep a little mystery?"
        ),

        (
            "Would you rather have a partner who is adventurous "
            "or one who is spontaneous?"
        ),

        (
            "Would you rather flirt through messages "
            "or flirt face-to-face?"
        ),

        (
            "Would you rather have a beach date "
            "or a mountain getaway?"
        ),

        (
            "Would you rather be called beautiful/handsome "
            "or irresistible?"
        ),

        (
            "Would you rather make the first move "
            "or have someone surprise you?"
        ),

        (
            "Would you rather have one amazing date "
            "or several fun casual dates?"
        ),

    ],

    "spicy": [

        (
            "Would you rather spend the night flirting "
            "or spend the night building anticipation?"
        ),

        (
            "Would you rather be teased "
            "or do the teasing?"
        ),

        (
            "Would you rather receive a seductive message "
            "or hear something whispered in your ear?"
        ),

        (
            "Would you rather have a private date "
            "or a playful group adventure?"
        ),

        (
            "Would you rather make the first move "
            "or be pursued?"
        ),

        (
            "Would you rather have someone tell you "
            "exactly what they want or make you guess?"
        ),

        (
            "Would you rather have a slow-burn connection "
            "or instant chemistry?"
        ),

        (
            "Would you rather flirt all night "
            "or get straight to the point?"
        ),

        (
            "Would you rather receive a flirty photo "
            "or a flirty voice message?"
        ),

        (
            "Would you rather plan an adventurous date "
            "or let someone surprise you?"
        ),

        (
            "Would you rather be the center of attention "
            "or secretly watching the action?"
        ),

        (
            "Would you rather have a confident partner "
            "or a playful partner?"
        ),

        (
            "Would you rather explore something new "
            "or perfect something you already love?"
        ),

        (
            "Would you rather have someone whisper "
            "what they want or show you through actions?"
        ),

        (
            "Would you rather have an entire night of flirting "
            "or one unforgettable moment?"
        ),

        (
            "Would you rather go on a couples' adventure "
            "or a one-on-one date?"
        ),

        (
            "Would you rather be tempted "
            "or be the temptation?"
        ),

        (
            "Would you rather have someone confidently approach you "
            "or subtly show interest?"
        ),

        (
            "Would you rather receive attention from across the room "
            "or have someone pull you into a conversation?"
        ),

        (
            "Would you rather reveal a fantasy "
            "or hear someone else's fantasy?"
        ),

    ],

    "extreme": [

        (
            "Would you rather explore a new fantasy "
            "or revisit a favorite experience?"
        ),

        (
            "Would you rather be completely in control "
            "or willingly give up control?"
        ),

        (
            "Would you rather plan the entire adventure "
            "or have trusted consenting adults surprise you?"
        ),

        (
            "Would you rather explore with a couple "
            "or explore with a single?"
        ),

        (
            "Would you rather have a secret fantasy revealed "
            "or reveal one of your own?"
        ),

        (
            "Would you rather spend an entire evening teasing "
            "or skip straight to the adventure?"
        ),

        (
            "Would you rather be watched "
            "or be the one watching?"
        ),

        (
            "Would you rather explore something completely new "
            "or push the limits of something familiar?"
        ),

        (
            "Would you rather have a partner choose the adventure "
            "or choose it yourself?"
        ),

        (
            "Would you rather have intense chemistry "
            "or complete trust?"
        ),

        (
            "Would you rather share a fantasy privately "
            "or discuss it openly with trusted consenting adults?"
        ),

        (
            "Would you rather have one extremely adventurous night "
            "or several smaller adventures?"
        ),

        (
            "Would you rather be the one making the rules "
            "or agree to someone else's rules?"
        ),

        (
            "Would you rather explore a new kink "
            "or introduce someone to one of yours?"
        ),

        (
            "Would you rather have a spontaneous adventure "
            "or carefully planned experience?"
        ),

        (
            "Would you rather reveal your biggest YES "
            "or your biggest MAYBE?"
        ),

        (
            "Would you rather have someone challenge your comfort zone "
            "or let you decide exactly how far to go?"
        ),

        (
            "Would you rather explore with someone you just met "
            "or someone you already completely trust?"
        ),

        (
            "Would you rather have a night focused on teasing "
            "or a night focused on adventure?"
        ),

        (
            "Would you rather answer a very personal question "
            "or choose a bold challenge?"
        ),

    ],
}


# ==========================================================
# ENABLED STATUS
# ==========================================================

def is_enabled():

    return WOULD_YOU_RATHER_ENABLED


# ==========================================================
# GET LEVEL
# ==========================================================

def get_level(context):

    level = context.user_data.get(
        "wyr_level",
        "mild",
    )

    if level not in VALID_LEVELS:

        level = "mild"

    return level


# ==========================================================
# LEVEL MENU
# ==========================================================

def level_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 Mild",
                    callback_data="wyr_level_mild",
                ),
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data="wyr_level_spicy",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="wyr_level_extreme",
                ),
            ],
        ]
    )


# ==========================================================
# GAME KEYBOARD
# ==========================================================

def game_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "A️⃣ Option A",
                    callback_data="wyr_vote_a",
                ),
                InlineKeyboardButton(
                    "B️⃣ Option B",
                    callback_data="wyr_vote_b",
                ),
            ],
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="wyr_pass",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="wyr_next",
                ),
                InlineKeyboardButton(
                    "🔄 Level",
                    callback_data="wyr_menu",
                ),
            ],
        ]
    )


# ==========================================================
# FORMAT QUESTION
# ==========================================================

def format_question(question):

    return (
        "🤔 WOULD YOU RATHER?\n\n"
        f"{question}\n\n"
        "A️⃣ Option A\n"
        "B️⃣ Option B\n\n"
        "Choose A or B.\n"
        "😈 PASS is always allowed."
    )


# ==========================================================
# GET QUESTION
# ==========================================================

def get_question(context):

    level = get_level(context)

    question = random.choice(
        QUESTIONS[level]
    )

    context.user_data[
        "wyr_current_question"
    ] = question

    return question


# ==========================================================
# /WOULDYOURATHER
# ==========================================================

async def would_you_rather(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not WOULD_YOU_RATHER_ENABLED:

        await message.reply_text(
            "🤔 Would You Rather is currently disabled."
        )

        return

    await message.reply_text(
        "🤔 WOULD YOU RATHER\n\n"
        "Choose your level:",
        reply_markup=level_keyboard(),
    )


# ==========================================================
# START GAME
# ==========================================================

async def start_game(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    if not WOULD_YOU_RATHER_ENABLED:

        await query.answer(
            "Would You Rather is disabled.",
            show_alert=True,
        )

        return

    question = get_question(context)

    level = get_level(context)

    await query.edit_message_text(
        f"🤔 WOULD YOU RATHER — {level.upper()}\n\n"
        f"{question}\n\n"
        "A️⃣ Option A\n"
        "B️⃣ Option B\n\n"
        "Choose A or B.\n"
        "😈 PASS is always allowed.",
        reply_markup=game_keyboard(),
    )


# ==========================================================
# CALLBACK HANDLER
# ==========================================================

async def callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    # ------------------------------------------------------
    # LEVEL MENU
    # ------------------------------------------------------

    if data == "wyr_menu":

        await query.edit_message_text(
            "🤔 WOULD YOU RATHER\n\n"
            "Choose your level:",
            reply_markup=level_keyboard(),
        )

        return

    # ------------------------------------------------------
    # LEVEL SELECTION
    # ------------------------------------------------------

    if data.startswith("wyr_level_"):

        level = data.replace(
            "wyr_level_",
            "",
            1,
        )

        if level not in VALID_LEVELS:

            level = "mild"

        context.user_data[
            "wyr_level"
        ] = level

        question = get_question(context)

        await query.edit_message_text(
            f"🤔 WOULD YOU RATHER — {level.upper()}\n\n"
            f"{question}\n\n"
            "A️⃣ Option A\n"
            "B️⃣ Option B\n\n"
            "Choose A or B.\n"
            "😈 PASS is always allowed.",
            reply_markup=game_keyboard(),
        )

        return

    # ------------------------------------------------------
    # OPTION A
    # ------------------------------------------------------

    if data == "wyr_vote_a":

        await query.answer(
            "You chose Option A!",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # OPTION B
    # ------------------------------------------------------

    if data == "wyr_vote_b":

        await query.answer(
            "You chose Option B!",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # PASS
    # ------------------------------------------------------

    if data == "wyr_pass":

        await query.answer(
            "PASS accepted 😈",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # NEXT
    # ------------------------------------------------------

    if data == "wyr_next":

        if not WOULD_YOU_RATHER_ENABLED:

            await query.answer(
                "Would You Rather is disabled.",
                show_alert=True,
            )

            return

        level = get_level(context)

        question = get_question(context)

        await query.edit_message_text(
            f"🤔 WOULD YOU RATHER — {level.upper()}\n\n"
            f"{question}\n\n"
            "A️⃣ Option A\n"
            "B️⃣ Option B\n\n"
            "Choose A or B.\n"
            "😈 PASS is always allowed.",
            reply_markup=game_keyboard(),
        )

        return


# ==========================================================
# END would_you_rather.py
# ==========================================================
