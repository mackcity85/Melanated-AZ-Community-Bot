# ==========================================================
# Melanated AZ Bot
# games/social_games.py
#
# SOCIAL GAMES CATEGORY
#
# Games included:
#   - Two Truths & A Lie
#   - Would You Rather
#   - Question Roulette
#   - Compliment Battle
#   - Pick a Player
#
# Features:
#   - Button-based menus
#   - Random prompts
#   - PASS support
#   - Next prompt
#   - Return to category
#   - Return to main Games menu
#
# IMPORTANT:
# This file does NOT import from games.py.
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

SOCIAL_GAMES_ENABLED = True


# ==========================================================
# TWO TRUTHS & A LIE
# ==========================================================

TWO_TRUTHS_LIE = [

    {
        "statements": [
            "I have traveled to another country.",
            "I have stayed awake for more than 24 hours.",
            "I have never been on a blind date.",
        ],
        "lie": 2,
    },

    {
        "statements": [
            "I love spontaneous adventures.",
            "I have met someone through social media.",
            "I have never sent a flirty message.",
        ],
        "lie": 2,
    },

    {
        "statements": [
            "I have gone on a road trip with friends.",
            "I have danced until sunrise.",
            "I have never had a crush on someone unexpected.",
        ],
        "lie": 2,
    },

    {
        "statements": [
            "I have tried something completely outside my comfort zone.",
            "I have been the first person to make a move.",
            "I have never stayed up all night talking to someone.",
        ],
        "lie": 2,
    },

    {
        "statements": [
            "I prefer the beach over the mountains.",
            "I have gone on a spontaneous date.",
            "I have never changed my plans for someone attractive.",
        ],
        "lie": 2,
    },

]


# ==========================================================
# WOULD YOU RATHER
# ==========================================================

WOULD_YOU_RATHER = [

    (
        "Have an amazing first date",
        "Have an amazing second date",
    ),

    (
        "Be pursued",
        "Do the pursuing",
    ),

    (
        "Have instant chemistry",
        "Build chemistry slowly",
    ),

    (
        "Take a spontaneous road trip",
        "Plan the perfect vacation",
    ),

    (
        "Spend a night dancing",
        "Spend a night talking",
    ),

    (
        "Get a surprise date",
        "Plan every detail yourself",
    ),

    (
        "Have great conversation",
        "Have undeniable chemistry",
    ),

    (
        "Go to the beach",
        "Go to the mountains",
    ),

    (
        "Stay in for the night",
        "Go out until sunrise",
    ),

    (
        "Get a flirty text",
        "Get a flirty phone call",
    ),

    (
        "Meet someone at a party",
        "Meet someone online",
    ),

    (
        "Have a romantic date",
        "Have an adventurous date",
    ),

    (
        "Be the best dancer",
        "Be the best storyteller",
    ),

    (
        "Have unlimited travel",
        "Have unlimited free food",
    ),

    (
        "Know exactly what someone thinks",
        "Know exactly what someone wants",
    ),

    (
        "Have a perfect first kiss",
        "Have a perfect first date",
    ),

    (
        "Go camping",
        "Stay at a luxury hotel",
    ),

    (
        "Watch a movie together",
        "Listen to music together",
    ),

    (
        "Have one amazing adventure",
        "Have many small adventures",
    ),

    (
        "Have confidence",
        "Have charisma",
    ),

]


# ==========================================================
# QUESTION ROULETTE
# ==========================================================

QUESTION_ROULETTE = [

    "What is one thing people usually misunderstand about you?",

    "What is something you are secretly proud of?",

    "What is your biggest green flag?",

    "What is your biggest red flag?",

    "What is something that always makes you smile?",

    "What is your favorite way to spend a free day?",

    "What is something you would love to learn?",

    "What is your dream vacation?",

    "What is one thing you could talk about for hours?",

    "What is the best compliment you have ever received?",

    "What is something you find instantly attractive?",

    "What is one adventure on your bucket list?",

    "What is something you wish more people knew about you?",

    "What is your favorite way to meet new people?",

    "What makes you feel comfortable around someone?",

    "What is your favorite type of date?",

    "What is something that instantly kills the vibe for you?",

    "What is one thing you always notice about someone?",

    "What is something you have always wanted to try?",

    "What is your favorite way to relax?",

    "What is something that makes you laugh every time?",

    "What is your favorite conversation topic?",

    "What is one place you would visit again in a heartbeat?",

    "What is something you value most in a friendship?",

    "What makes someone unforgettable to you?",

]


# ==========================================================
# COMPLIMENT BATTLE
# ==========================================================

COMPLIMENT_BATTLE = [

    "Give another player a genuine compliment.",

    "Compliment someone's personality.",

    "Compliment someone's sense of humor.",

    "Compliment someone's energy.",

    "Compliment someone's confidence.",

    "Compliment someone's style.",

    "Compliment someone's kindness.",

    "Compliment someone's creativity.",

    "Compliment someone's conversation skills.",

    "Compliment someone's positive attitude.",

    "Tell someone what makes them stand out.",

    "Tell someone what you appreciate about their vibe.",

    "Give someone a compliment they probably do not hear often.",

    "Give someone a playful but respectful compliment.",

    "Compliment someone without mentioning their appearance.",

    "Tell someone why they seem fun to be around.",

    "Tell someone what makes their energy memorable.",

    "Give someone your most creative compliment.",

    "Compliment someone who has made you laugh.",

    "Give a compliment to someone you have not talked to before.",

]


# ==========================================================
# PICK A PLAYER
# ==========================================================

PICK_A_PLAYER = [

    "Pick someone who seems like they would make a great travel partner.",

    "Pick someone who seems like they would plan the perfect date.",

    "Pick someone who seems like they would be fun at a party.",

    "Pick someone who seems like they would make you laugh.",

    "Pick someone who seems adventurous.",

    "Pick someone who seems easy to talk to.",

    "Pick someone who has great energy.",

    "Pick someone who seems like they would give good advice.",

    "Pick someone who seems like they would be the best dance partner.",

    "Pick someone who seems like they would be fun on a road trip.",

    "Pick someone who seems confident.",

    "Pick someone who seems mysterious.",

    "Pick someone who seems like they would surprise you.",

    "Pick someone who seems like they would be the life of the party.",

    "Pick someone you would want on your team during game night.",

    "Pick someone who seems like they would have the best stories.",

    "Pick someone who seems like they would make a great wingman or wingwoman.",

    "Pick someone whose personality caught your attention.",

    "Pick someone you would want to have a long conversation with.",

    "Pick someone who seems like they would say YES to an adventure.",

]


# ==========================================================
# GAME NAMES
# ==========================================================

GAME_NAMES = {

    "two_truths":
        "🤥 Two Truths & A Lie",

    "would_rather":
        "🤔 Would You Rather",

    "roulette":
        "🎯 Question Roulette",

    "compliment":
        "💜 Compliment Battle",

    "pick_player":
        "👀 Pick a Player",

}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():

    return SOCIAL_GAMES_ENABLED


# ==========================================================
# MENU KEYBOARD
# ==========================================================

def social_games_keyboard():

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    GAME_NAMES["two_truths"],
                    callback_data="social_game_two_truths",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["would_rather"],
                    callback_data="social_game_would_rather",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["roulette"],
                    callback_data="social_game_roulette",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["compliment"],
                    callback_data="social_game_compliment",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["pick_player"],
                    callback_data="social_game_pick_player",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🔙 Games",
                    callback_data="games_main",
                ),
            ],

        ]
    )


# ==========================================================
# GAME CONTROLS
# ==========================================================

def game_controls():

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="social_game_next",
                ),

                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="social_game_pass",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🎮 Other Social Games",
                    callback_data="social_games_menu",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🔙 Games",
                    callback_data="games_main",
                ),
            ],

        ]
    )


# ==========================================================
# CURRENT GAME
# ==========================================================

def get_current_game(context):

    return context.user_data.get(
        "social_current_game",
        "roulette",
    )


# ==========================================================
# BUILD PROMPT
# ==========================================================

def get_prompt(context):

    game = get_current_game(context)

    # ------------------------------------------------------
    # TWO TRUTHS
    # ------------------------------------------------------

    if game == "two_truths":

        round_data = random.choice(
            TWO_TRUTHS_LIE
        )

        statements = round_data[
            "statements"
        ]

        return (
            "🤥 TWO TRUTHS & A LIE\n\n"

            f"1️⃣ {statements[0]}\n\n"

            f"2️⃣ {statements[1]}\n\n"

            f"3️⃣ {statements[2]}\n\n"

            "Which statement is the lie?"
        )

    # ------------------------------------------------------
    # WOULD YOU RATHER
    # ------------------------------------------------------

    if game == "would_rather":

        first, second = random.choice(
            WOULD_YOU_RATHER
        )

        return (
            "🤔 WOULD YOU RATHER?\n\n"

            f"🅰️ {first}\n\n"

            "OR\n\n"

            f"🅱️ {second}"
        )

    # ------------------------------------------------------
    # QUESTION ROULETTE
    # ------------------------------------------------------

    if game == "roulette":

        return random.choice(
            QUESTION_ROULETTE
        )

    # ------------------------------------------------------
    # COMPLIMENT
    # ------------------------------------------------------

    if game == "compliment":

        return random.choice(
            COMPLIMENT_BATTLE
        )

    # ------------------------------------------------------
    # PICK PLAYER
    # ------------------------------------------------------

    if game == "pick_player":

        return random.choice(
            PICK_A_PLAYER
        )

    return random.choice(
        QUESTION_ROULETTE
    )


# ==========================================================
# START GAME
# ==========================================================

async def start_game(
    query,
    context,
    game,
):

    if game not in GAME_NAMES:

        game = "roulette"

    context.user_data[
        "social_current_game"
    ] = game

    prompt = get_prompt(
        context
    )

    context.user_data[
        "social_current_prompt"
    ] = prompt

    title = GAME_NAMES.get(
        game,
        "🎮 Social Game",
    )

    await query.edit_message_text(

        f"{title}\n\n"

        f"{prompt}\n\n"

        "😈 PASS is always allowed.",

        reply_markup=game_controls(),

    )


# ==========================================================
# /SOCIALGAMES
# ==========================================================

async def social_games(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:

        return

    if not SOCIAL_GAMES_ENABLED:

        await message.reply_text(
            "🎮 Social Games are currently disabled."
        )

        return

    await message.reply_text(

        "🎮 SOCIAL GAMES\n\n"

        "Choose a game below.\n\n"

        "Have fun, respect boundaries, "
        "and remember that PASS is always allowed.",

        reply_markup=social_games_keyboard(),

    )


# ==========================================================
# CALLBACK
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

    if not SOCIAL_GAMES_ENABLED:

        await query.answer(
            "Social Games are disabled.",
            show_alert=True,
        )

        return

    # ======================================================
    # MENU
    # ======================================================

    if data == "social_games_menu":

        await query.edit_message_text(

            "🎮 SOCIAL GAMES\n\n"
            "Choose a game:",

            reply_markup=social_games_keyboard(),

        )

        return

    # ======================================================
    # GAME SELECTION
    # ======================================================

    if data.startswith(
        "social_game_"
    ):

        game = data.replace(
            "social_game_",
            "",
            1,
        )

        if game in GAME_NAMES:

            await start_game(
                query,
                context,
                game,
            )

            return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "social_game_next":

        game = get_current_game(
            context
        )

        await start_game(
            query,
            context,
            game,
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "social_game_pass":

        title = GAME_NAMES.get(

            get_current_game(
                context
            ),

            "🎮 Social Game",

        )

        await query.edit_message_text(

            f"{title}\n\n"

            "😈 PASS ACCEPTED!\n\n"

            "No explanation needed. "
            "Hit Next whenever you're ready.",

            reply_markup=game_controls(),

        )

        return


# ==========================================================
# END social_games.py
# ==========================================================
