# ==========================================================
# Melanated AZ Bot
# truth_dare.py
#
# Adult Community Truth or Dare
#
# Features:
#   - Truth
#   - Dare
#   - Mild
#   - Spicy
#   - Extreme
#   - Button-based menu
#   - Admin enable/disable
#   - PASS is always allowed
#   - Consent-focused
#
# IMPORTANT:
# This file does NOT import from admin.py.
# This prevents a circular import.
# ==========================================================

import logging
import random

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import ADMIN_IDS


logger = logging.getLogger(__name__)


# ==========================================================
# SETTINGS
# ==========================================================

TRUTH_DARE_ENABLED = True

VALID_LEVELS = (
    "mild",
    "spicy",
    "extreme",
)


# ==========================================================
# ADMIN CHECK
#
# IMPORTANT:
# Do NOT import is_admin from admin.py.
# That would create a circular import.
# ==========================================================

def is_truth_dare_admin(user_id):

    try:
        return int(user_id) in [
            int(admin_id)
            for admin_id in ADMIN_IDS
        ]

    except (TypeError, ValueError):

        return False


# ==========================================================
# TRUTHS
# ==========================================================

TRUTHS = {

    "mild": [

        "What is something people assume about you that is completely wrong?",
        "What is your biggest green flag when meeting someone new?",
        "What is your favorite way to flirt?",
        "What instantly makes someone more attractive to you?",
        "What is something adventurous you would like to try someday?",
        "What is one boundary you always communicate upfront?",
        "What kind of personality catches your attention first?",
        "Would you rather meet another couple or a single for a first experience?",
        "What makes you feel comfortable enough to explore with someone new?",
        "What is your favorite type of date?",
        "What is one thing that makes you feel desired?",
        "Are you more of a tease or the one being teased?",
        "What is your biggest dating green flag?",
        "What is something you find unexpectedly attractive?",
        "What is one thing you wish more people understood about you?",
        "What type of flirting gets your attention immediately?",
        "What is your favorite way to break the ice with someone?",
        "What makes you feel comfortable around a new couple?",
        "What is one thing you would never compromise on?",
        "What kind of chemistry do you look for?",
    ],

    "spicy": [

        "What is something that instantly turns up the chemistry for you?",
        "What is your biggest turn-on when meeting someone new?",
        "What is something adventurous on your kink bucket list?",
        "Have you ever developed unexpected chemistry with someone?",
        "What is your favorite kind of teasing?",
        "What is your favorite way someone can flirt with you?",
        "Would you rather plan an experience or let the night unfold naturally?",
        "What is one thing that instantly makes someone irresistible to you?",
        "What kind of couple catches your attention?",
        "What is something you have always been curious about exploring?",
        "What is your favorite type of adult date night?",
        "What is your favorite way to build anticipation?",
        "What is something that makes you immediately curious about someone?",
        "What kind of confidence do you find attractive?",
        "What is the boldest thing you have ever done on a date?",
        "What is something you secretly find extremely attractive?",
        "What kind of flirting makes you blush?",
        "What is one fantasy you would consider exploring with the right consenting people?",
        "What is your favorite part of getting to know someone new?",
        "What makes a person unforgettable to you?",
        "Would you rather be pursued or do the pursuing?",
        "What is your favorite way to tease someone?",
        "What kind of energy attracts you the most?",
        "What is one thing you would love a potential partner to ask you?",
        "What makes you feel confident in an adult-community setting?",
    ],

    "extreme": [

        "What is the boldest experience you would consider trying?",
        "What is one kink you are curious about but have not explored?",
        "What is one fantasy you have discussed with your partner but have not explored yet?",
        "What would make you immediately say YES to an adventure?",
        "What would make you immediately say HARD NO?",
        "Would you rather explore with another couple, a single, or both?",
        "What is something adventurous you would try with the right consenting people?",
        "What is your biggest boundary when exploring?",
        "What is one thing you would love to experience with a partner?",
        "What kind of situation creates the strongest chemistry for you?",
        "What is something you have always wanted to be asked?",
        "What is the most adventurous date you would actually agree to?",
        "What is something that would make you instantly curious about someone?",
        "What is one fantasy that stays on your bucket list?",
        "What is something you would consider exploring but only with someone you trust?",
        "What is one thing that makes you feel completely confident and comfortable?",
        "What is your biggest YES when it comes to exploring?",
        "What is your biggest MAYBE?",
        "What is one thing that is absolutely off limits?",
        "What is the wildest experience you would consider trying?",
        "What kind of chemistry would convince you to take things further?",
        "What is one thing you would want a new play partner to know about you?",
        "What is something that would make you immediately lose interest?",
        "What is your idea of the perfect adventurous night?",
        "What is one experience you hope to have someday?",
    ],
}


# ==========================================================
# DARES
# ==========================================================

DARES = {

    "mild": [

        "Give someone in the chat a genuine compliment.",
        "Tell the group your favorite way to flirt.",
        "Give someone your best pickup line.",
        "Tell the group whether you are more tease or temptation.",
        "Share your favorite song for setting the mood.",
        "Describe your ideal date in three words.",
        "Tell someone what caught your attention about them.",
        "Give your partner a playful compliment.",
        "Tell the group one of your biggest green flags.",
        "Send someone a 😉 and see if they respond.",
        "Tell the group what kind of flirting gets your attention.",
        "Share one item from your adult bucket list.",
        "Give someone a compliment based only on their personality.",
        "Tell the group what makes someone immediately attractive to you.",
        "Pick someone and tell them they have good energy.",
        "Tell the group whether you prefer making the first move.",
        "Describe your perfect first date.",
        "Tell the group your favorite way to receive attention.",
        "Give someone your most creative compliment.",
        "Tell the group one thing that always makes you smile.",
    ],

    "spicy": [

        "Send someone a flirty message that makes your intentions clear.",
        "Give someone your best seductive pickup line.",
        "Tell someone in the group what caught your attention about them.",
        "Invite someone you're interested in to chat privately — if they're interested too.",
        "Send your partner a message designed to make them blush.",
        "Tell the group your ideal couple's night out.",
        "Tell someone what kind of chemistry you are looking for.",
        "Send someone a 😉 and wait for their response.",
        "Tell someone one thing about their vibe that you find attractive.",
        "Share one item from your adult bucket list.",
        "Describe your perfect adults-only date.",
        "Tell the group your favorite way to build anticipation.",
        "Give someone your best flirty compliment.",
        "Tell the group what kind of teasing you enjoy.",
        "Ask someone you're interested in if they would like to exchange pictures.",
        "Tell someone what made you notice them.",
        "Send your partner a message telling them something you find irresistible about them.",
        "Tell the group whether you prefer being pursued or doing the pursuing.",
        "Tell someone what kind of energy attracts you.",
    ],

    "extreme": [

        "Give someone your most creative seductive pickup line.",
        "Tell someone exactly what made you notice them.",
        "Tell the group about one adventure that is on your bucket list.",
        "Tell the group your biggest YES, biggest MAYBE, and biggest NO.",
        "Tell someone what kind of flirting gets your attention fastest.",
        "Send your partner a message telling them what you find irresistible about them.",
        "Tell the group what makes a couple especially attractive to you.",
        "Ask someone you're interested in whether they would like to exchange pictures.",
        "Tell the group one adventurous experience you would consider with the right consenting people.",
        "Give someone permission to ask you one spicy question. You may still PASS.",
        "Describe your perfect adults-only night out.",
        "Tell someone what would make you instantly curious about them.",
        "Share something adventurous you would like to explore.",
        "Tell the group your boldest fantasy without naming another member.",
        "Describe your ideal kinky-date atmosphere in three words.",
        "Tell someone what type of chemistry you find irresistible.",
        "Ask someone you're interested in if they would like to move the conversation to private chat.",
        "Let another player choose Truth or Dare for your next turn.",
        "Tell the group your biggest adventure goal.",
        "Give someone a bold but respectful compliment.",
        "Tell someone what makes their energy attractive to you.",
        "Share one experience you would consider with trusted consenting adults.",
        "Tell the group something adventurous you would like to experience someday.",
    ],
}


# ==========================================================
# ENABLED STATUS
# ==========================================================

def is_truth_dare_enabled():

    return TRUTH_DARE_ENABLED


# ==========================================================
# GET CURRENT LEVEL
# ==========================================================

def get_level(context):

    level = context.user_data.get(
        "truth_dare_level",
        "mild",
    )

    if level not in VALID_LEVELS:

        level = "mild"

    return level


# ==========================================================
# MAIN MENU KEYBOARD
# ==========================================================

def truth_dare_menu_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 Mild",
                    callback_data="truthdare_level_mild",
                ),
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data="truthdare_level_spicy",
                ),
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="truthdare_level_extreme",
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
                    "🔥 Truth",
                    callback_data="truthdare_truth",
                ),
                InlineKeyboardButton(
                    "😈 Dare",
                    callback_data="truthdare_dare",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data="truthdare_menu",
                ),
            ],
        ]
    )


# ==========================================================
# /TRUTHDARE
# ==========================================================

async def truth_dare_menu(
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
        "🔥 TRUTH OR DARE\n\n"
        "Choose your level:\n\n"
        "🟢 Mild — fun & flirty\n"
        "🌶️ Spicy — adult-community vibes\n"
        "🔥 Extreme — bold & adventurous\n\n"
        "😈 PASS is always allowed.",
        reply_markup=truth_dare_menu_keyboard(),
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

    level = get_level(context)

    if context.args:

        requested_level = context.args[0].lower()

        if requested_level in TRUTHS:

            level = requested_level

            context.user_data[
                "truth_dare_level"
            ] = level

    question = random.choice(
        TRUTHS[level]
    )

    await message.reply_text(
        f"🔥 TRUTH — {level.upper()}\n\n"
        f"{question}\n\n"
        "😈 You may PASS.",
        reply_markup=game_keyboard(),
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

    level = get_level(context)

    if context.args:

        requested_level = context.args[0].lower()

        if requested_level in DARES:

            level = requested_level

            context.user_data[
                "truth_dare_level"
            ] = level

    challenge = random.choice(
        DARES[level]
    )

    await message.reply_text(
        f"😈 DARE — {level.upper()}\n\n"
        f"{challenge}\n\n"
        "😈 PASS is always allowed.",
        reply_markup=game_keyboard(),
    )


# ==========================================================
# ADMIN TRUTH/DARE MENU
# ==========================================================

async def truth_dare_admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_truth_dare_admin(user.id):

        return

    query = update.callback_query

    status = (
        "🟢 ENABLED"
        if TRUTH_DARE_ENABLED
        else "🔴 DISABLED"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"🔥 Truth or Dare: {status}",
                    callback_data="admin_truthdare_toggle",
                )
            ],
            [
                InlineKeyboardButton(
                    "❓ View Help",
                    callback_data="admin_truthdare_help",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="admin_back",
                )
            ],
        ]
    )

    text = (
        "🔥 **TRUTH OR DARE SETTINGS**\n\n"
        f"Status: {status}\n\n"
        "Members can use:\n"
        "/truthdare\n"
        "/truth\n"
        "/dare\n\n"
        "Levels:\n"
        "🟢 Mild\n"
        "🌶️ Spicy\n"
        "🔥 Extreme\n\n"
        "😈 PASS is always allowed."
    )

    if query:

        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif update.effective_message:

        await update.effective_message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


# ==========================================================
# TOGGLE
# ==========================================================

async def toggle_truth_dare(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    global TRUTH_DARE_ENABLED

    user = update.effective_user

    if not user or not is_truth_dare_admin(user.id):

        return

    query = update.callback_query

    TRUTH_DARE_ENABLED = not TRUTH_DARE_ENABLED

    status = (
        "🟢 ENABLED"
        if TRUTH_DARE_ENABLED
        else "🔴 DISABLED"
    )

    if query:

        await query.answer(
            f"Truth or Dare {status}"
        )

    await truth_dare_admin_menu(
        update,
        context,
    )


# ==========================================================
# HELP
# ==========================================================

async def truth_dare_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_truth_dare_admin(user.id):

        return

    query = update.callback_query

    text = (
        "🔥 **TRUTH OR DARE HELP**\n\n"
        "Members can use:\n\n"
        "/truthdare\n"
        "Opens the button menu.\n\n"
        "/truth\n"
        "Random truth using the selected level.\n\n"
        "/truth mild\n"
        "/truth spicy\n"
        "/truth extreme\n\n"
        "/dare\n"
        "Random dare using the selected level.\n\n"
        "/dare mild\n"
        "/dare spicy\n"
        "/dare extreme\n\n"
        "Everyone may PASS.\n"
        "Respect boundaries and consent."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_truthdare",
                )
            ],
        ]
    )

    if query:

        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif update.effective_message:

        await update.effective_message.reply_text(
            text=text,
            reply_markup=keyboard,
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

    try:

        await query.answer()

    except Exception:

        pass

    # ======================================================
    # CHANGE LEVEL
    # ======================================================

    if data == "truthdare_menu":

        await query.edit_message_text(
            "🔥 CHOOSE YOUR LEVEL\n\n"
            "🟢 Mild — fun & flirty\n"
            "🌶️ Spicy — adult-community vibes\n"
            "🔥 Extreme — bold & adventurous",
            reply_markup=truth_dare_menu_keyboard(),
        )

        return

    # ======================================================
    # SELECT LEVEL
    # ======================================================

    if data.startswith("truthdare_level_"):

        level = data.replace(
            "truthdare_level_",
            "",
            1,
        )

        if level not in VALID_LEVELS:

            level = "mild"

        context.user_data[
            "truth_dare_level"
        ] = level

        await query.edit_message_text(
            f"🔥 {level.upper()} SELECTED\n\n"
            "Choose Truth or Dare:",
            reply_markup=game_keyboard(),
        )

        return

    # ======================================================
    # TRUTH
    # ======================================================

    if data == "truthdare_truth":

        if not TRUTH_DARE_ENABLED:

            await query.answer(
                "Truth or Dare is disabled.",
                show_alert=True,
            )

            return

        level = get_level(context)

        question = random.choice(
            TRUTHS[level]
        )

        await query.edit_message_text(
            f"🔥 TRUTH — {level.upper()}\n\n"
            f"{question}\n\n"
            "😈 You may PASS.",
            reply_markup=game_keyboard(),
        )

        return

    # ======================================================
    # DARE
    # ======================================================

    if data == "truthdare_dare":

        if not TRUTH_DARE_ENABLED:

            await query.answer(
                "Truth or Dare is disabled.",
                show_alert=True,
            )

            return

        level = get_level(context)

        challenge = random.choice(
            DARES[level]
        )

        await query.edit_message_text(
            f"😈 DARE — {level.upper()}\n\n"
            f"{challenge}\n\n"
            "😈 PASS is always allowed.",
            reply_markup=game_keyboard(),
        )

        return


# ==========================================================
# END truth_dare.py
# ==========================================================
