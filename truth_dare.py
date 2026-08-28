# ==========================================================
# Melanated AZ Bot
# truth_dare.py
#
# Truth or Dare System
#
# Commands:
#   /truth
#   /truth mild
#   /truth spicy
#   /truth extreme
#
#   /dare
#   /dare mild
#   /dare spicy
#   /dare extreme
#
#   /truthdare
#   /truthdarehelp
#
# Admin:
#   /toggletruthdare
#
# Buttons:
#   Truth
#   Dare
#   Mild
#   Spicy
#   Extreme
#   Back
# ==========================================================

import logging
import random

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from admin import is_admin


logger = logging.getLogger(__name__)


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
        "What is something you want to accomplish this year?",
        "What is your favorite way to spend a free day?",
        "What is something that always makes you smile?",
        "What is one thing you are really proud of?",
        "What is your favorite type of music?",
        "What is something you could talk about for hours?",
        "What is one place you would love to visit?"

    ],

    "spicy": [

        "What is something that instantly attracts you to someone?",
        "What is a fantasy you have never shared?",
        "What is your biggest turn on?",
        "What is something you secretly enjoy?",
        "What is your biggest dating green flag?",
        "What is the most attractive quality in a partner?",
        "What is something that can instantly make someone more attractive to you?",
        "What is your idea of a perfect date?",
        "Have you ever had a crush on someone unexpected?",
        "What is something adventurous you would like to try?"

    ],

    "extreme": [

        "What is a boundary you will never cross?",
        "What is something adventurous you want to try?",
        "What is the wildest experience you have had?",
        "What is something people would never guess about you?",
        "What is something bold you have always wanted to do?",
        "What is one experience that pushed you completely outside your comfort zone?",
        "What is something on your bucket list that you have not told many people about?",
        "What is the most spontaneous thing you have ever done?",
        "What is something you would try if you knew nobody would judge you?",
        "What is one adventure you absolutely want to experience someday?"

    ]

}


# ==========================================================
# DARES
# ==========================================================

DARES = {

    "mild": [

        "Give someone in the chat a genuine compliment.",
        "Share your favorite song.",
        "Tell the group something positive about yourself.",
        "Post a GIF that describes your mood.",
        "Tell the group your favorite movie.",
        "Give someone a shout-out.",
        "Share one thing that always makes you laugh.",
        "Post your favorite emoji combination.",
        "Tell the group one fun fact about yourself.",
        "Share your favorite food."

    ],

    "spicy": [

        "Send a flirty compliment to someone.",
        "Describe your perfect date.",
        "Share your favorite way to relax.",
        "Give someone in the chat a playful compliment.",
        "Describe your ideal romantic getaway.",
        "Tell the group what your biggest dating green flag is.",
        "Share the most attractive quality you look for in someone.",
        "Give someone a compliment without using the word beautiful.",
        "Describe your perfect evening with someone you like.",
        "Tell the group your idea of a great first date."

    ],

    "extreme": [

        "Share a secret bucket-list item.",
        "Describe your dream adventure.",
        "Tell the group something bold you want to experience.",
        "Describe the most spontaneous adventure you would take.",
        "Share one experience you would love to have someday.",
        "Tell the group something adventurous that is on your bucket list.",
        "Describe your ultimate fantasy vacation.",
        "Share something exciting you would try with the right person.",
        "Tell the group about an adventure you would never forget.",
        "Describe your dream weekend getaway."

    ]

}


# ==========================================================
# MAIN MENU
# ==========================================================

def truth_dare_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔥 TRUTH",
                    callback_data="truth_dare:truth",
                ),
                InlineKeyboardButton(
                    "😈 DARE",
                    callback_data="truth_dare:dare",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📖 Help",
                    callback_data="truth_dare:help",
                ),
            ],
        ]
    )


# ==========================================================
# LEVEL MENU
# ==========================================================

def level_keyboard(action):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🙂 Mild",
                    callback_data=f"truth_dare:{action}:mild",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data=f"truth_dare:{action}:spicy",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data=f"truth_dare:{action}:extreme",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="truth_dare:menu",
                ),
            ],
        ]
    )


# ==========================================================
# RESULT KEYBOARD
# ==========================================================

def result_keyboard(action, level):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 Another",
                    callback_data=(
                        f"truth_dare:{action}:{level}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Truth",
                    callback_data="truth_dare:truth",
                ),
                InlineKeyboardButton(
                    "😈 Dare",
                    callback_data="truth_dare:dare",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Menu",
                    callback_data="truth_dare:menu",
                ),
            ],
        ]
    )


# ==========================================================
# HELP
# ==========================================================

def truth_dare_help_text():

    return (
        "🔥 **TRUTH OR DARE** 🔥\n\n"
        "Choose your challenge and pick a level.\n\n"
        "🙂 **Mild**\n"
        "Fun and easy.\n\n"
        "🌶️ **Spicy**\n"
        "A little more personal.\n\n"
        "🔥 **Extreme**\n"
        "For the brave ones. 😈\n\n"
        "Commands also work:\n\n"
        "/truth\n"
        "/truth mild\n"
        "/truth spicy\n"
        "/truth extreme\n\n"
        "/dare\n"
        "/dare mild\n"
        "/dare spicy\n"
        "/dare extreme\n"
    )


# ==========================================================
# /TRUTHDARE
# ==========================================================

async def truth_dare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not TRUTH_DARE_ENABLED:

        await message.reply_text(
            "🔥 Truth or Dare is currently disabled."
        )

        return

    await message.reply_text(
        "🔥 **MELANATED AZ TRUTH OR DARE** 🔥\n\n"
        "Ready to play?\n\n"
        "Choose **Truth** or **Dare** below! 😈",
        reply_markup=truth_dare_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# /TRUTH
# ==========================================================

async def truth(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not TRUTH_DARE_ENABLED:

        await message.reply_text(
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

    await message.reply_text(
        f"🔥 **TRUTH — {level.upper()}**\n\n"
        f"{question}",
        reply_markup=result_keyboard(
            "truth",
            level,
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# /DARE
# ==========================================================

async def dare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not TRUTH_DARE_ENABLED:

        await message.reply_text(
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

    await message.reply_text(
        f"😈 **DARE — {level.upper()}**\n\n"
        f"{challenge}",
        reply_markup=result_keyboard(
            "dare",
            level,
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# CALLBACK HANDLER
# ==========================================================

async def truth_dare_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if not data.startswith(
        "truth_dare:"
    ):

        return

    if not TRUTH_DARE_ENABLED:

        await query.answer(
            "Truth or Dare is currently disabled.",
            show_alert=True,
        )

        return

    await query.answer()

    parts = data.split(":")

    action = (
        parts[1]
        if len(parts) > 1
        else ""
    )

    level = (
        parts[2]
        if len(parts) > 2
        else ""
    )

    # ------------------------------------------------------
    # MAIN MENU
    # ------------------------------------------------------

    if action == "menu":

        try:

            await query.edit_message_text(
                "🔥 **MELANATED AZ TRUTH OR DARE** 🔥\n\n"
                "Ready to play?\n\n"
                "Choose **Truth** or **Dare** below! 😈",
                reply_markup=truth_dare_keyboard(),
                parse_mode="Markdown",
            )

        except Exception:

            await query.message.reply_text(
                "🔥 **MELANATED AZ TRUTH OR DARE** 🔥\n\n"
                "Choose **Truth** or **Dare** below! 😈",
                reply_markup=truth_dare_keyboard(),
                parse_mode="Markdown",
            )

        return

    # ------------------------------------------------------
    # HELP
    # ------------------------------------------------------

    if action == "help":

        try:

            await query.edit_message_text(
                truth_dare_help_text(),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back",
                                callback_data=(
                                    "truth_dare:menu"
                                ),
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown",
            )

        except Exception:

            await query.message.reply_text(
                truth_dare_help_text(),
                reply_markup=truth_dare_keyboard(),
                parse_mode="Markdown",
            )

        return

    # ------------------------------------------------------
    # CHOOSE TRUTH OR DARE
    # ------------------------------------------------------

    if action in {
        "truth",
        "dare",
    } and not level:

        await query.edit_message_text(
            (
                "🔥 **TRUTH**\n\n"
                "Choose your level:"
                if action == "truth"
                else
                "😈 **DARE**\n\n"
                "Choose your level:"
            ),
            reply_markup=level_keyboard(
                action
            ),
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # GENERATE TRUTH
    # ------------------------------------------------------

    if action == "truth":

        if level not in TRUTHS:

            level = "mild"

        question = random.choice(
            TRUTHS[level]
        )

        await query.edit_message_text(
            f"🔥 **TRUTH — {level.upper()}**\n\n"
            f"{question}",
            reply_markup=result_keyboard(
                "truth",
                level,
            ),
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # GENERATE DARE
    # ------------------------------------------------------

    if action == "dare":

        if level not in DARES:

            level = "mild"

        challenge = random.choice(
            DARES[level]
        )

        await query.edit_message_text(
            f"😈 **DARE — {level.upper()}**\n\n"
            f"{challenge}",
            reply_markup=result_keyboard(
                "dare",
                level,
            ),
            parse_mode="Markdown",
        )

        return


# ==========================================================
# ADMIN ENABLE / DISABLE
# ==========================================================

async def toggle_truth_dare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    global TRUTH_DARE_ENABLED

    if not await is_admin(
        update,
        context,
    ):

        return

    TRUTH_DARE_ENABLED = (
        not TRUTH_DARE_ENABLED
    )

    status = (
        "ENABLED"
        if TRUTH_DARE_ENABLED
        else "DISABLED"
    )

    message = update.effective_message

    if message:

        await message.reply_text(
            f"🔥 Truth or Dare is now **{status}**.",
            parse_mode="Markdown",
        )

    logger.info(
        "Truth or Dare changed to %s by admin %s",
        status,
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )


# ==========================================================
# HELP COMMAND
# ==========================================================

async def truth_dare_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    await message.reply_text(
        truth_dare_help_text(),
        parse_mode="Markdown",
        reply_markup=truth_dare_keyboard(),
    )
