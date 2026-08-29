# ==========================================================
# Melanated AZ Bot
# games/word_games.py
#
# WORD GAMES CATEGORY
#
# Games included:
#   - Word Scramble
#   - Guess the Word
#   - Word Association
#   - Rhyme Time
#   - 5-Second Word Challenge
#
# Features:
#   - Button-based menus
#   - Random prompts
#   - Answer checking where applicable
#   - PASS support
#   - Next challenge
#   - Category navigation
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

WORD_GAMES_ENABLED = True


# ==========================================================
# WORD SCRAMBLE
# ==========================================================

WORD_SCRAMBLE = [

    {
        "word": "MUSIC",
        "scramble": "CUMSI",
    },

    {
        "word": "FRIEND",
        "scramble": "DREFNI",
    },

    {
        "word": "PARTY",
        "scramble": "TYAPR",
    },

    {
        "word": "ADVENTURE",
        "scramble": "VADNETRUE",
    },

    {
        "word": "COMMUNITY",
        "scramble": "MUNITCYO",
    },

    {
        "word": "WEEKEND",
        "scramble": "KWEENED",
    },

    {
        "word": "DANCING",
        "scramble": "GICNDAN",
    },

    {
        "word": "VACATION",
        "scramble": "CAVOTIAN",
    },

    {
        "word": "SUNSHINE",
        "scramble": "HINESUNS",
    },

    {
        "word": "CONFIDENCE",
        "scramble": "FIDECONCNE",
    },

    {
        "word": "CHEMISTRY",
        "scramble": "TRYCHMEIS",
    },

    {
        "word": "EXCITEMENT",
        "scramble": "CITEMEXENT",
    },

    {
        "word": "LAUGHTER",
        "scramble": "GHTLRAUE",
    },

    {
        "word": "FRIENDSHIP",
        "scramble": "SHIPFRIEND",
    },

    {
        "word": "CELEBRATE",
        "scramble": "BRATECELE",
    },

]


# ==========================================================
# GUESS THE WORD
# ==========================================================

GUESS_THE_WORD = [

    {
        "word": "BEACH",
        "hint": "A sandy place where many people go to relax.",
    },

    {
        "word": "MUSIC",
        "hint": "You can listen to it, dance to it, or sing it.",
    },

    {
        "word": "PARTY",
        "hint": "A social gathering with people having fun.",
    },

    {
        "word": "PIZZA",
        "hint": "A popular food usually covered with cheese and toppings.",
    },

    {
        "word": "DANCE",
        "hint": "Something people do when music moves them.",
    },

    {
        "word": "FRIEND",
        "hint": "Someone you enjoy spending time with and trust.",
    },

    {
        "word": "VACATION",
        "hint": "Time away from your normal routine.",
    },

    {
        "word": "SUNSET",
        "hint": "It happens when the sun goes below the horizon.",
    },

    {
        "word": "COFFEE",
        "hint": "A popular caffeinated morning drink.",
    },

    {
        "word": "MOVIE",
        "hint": "Something you watch on a screen for entertainment.",
    },

    {
        "word": "TRAVEL",
        "hint": "Going from one place to another.",
    },

    {
        "word": "ADVENTURE",
        "hint": "An exciting or unusual experience.",
    },

    {
        "word": "LAUGHTER",
        "hint": "The sound people make when something is funny.",
    },

    {
        "word": "CHEMISTRY",
        "hint": "A strong connection or attraction between people.",
    },

    {
        "word": "CONFIDENCE",
        "hint": "Belief in yourself and your abilities.",
    },

]


# ==========================================================
# WORD ASSOCIATION
# ==========================================================

WORD_ASSOCIATION = [

    "Beach",

    "Music",

    "Party",

    "Love",

    "Adventure",

    "Summer",

    "Coffee",

    "Travel",

    "Friendship",

    "Dance",

    "Movies",

    "Food",

    "Weekend",

    "Vacation",

    "Sunset",

    "Laugh",

    "Confidence",

    "Chemistry",

    "Dream",

    "Freedom",

    "Family",

    "Success",

    "Happiness",

    "Energy",

    "Community",

]


# ==========================================================
# RHYME TIME
# ==========================================================

RHYME_TIME = [

    {
        "word": "NIGHT",
        "examples": [
            "light",
            "flight",
            "right",
            "bright",
        ],
    },

    {
        "word": "DAY",
        "examples": [
            "play",
            "way",
            "say",
            "stay",
        ],
    },

    {
        "word": "LOVE",
        "examples": [
            "above",
            "dove",
            "glove",
            "shove",
        ],
    },

    {
        "word": "FIRE",
        "examples": [
            "higher",
            "wire",
            "tire",
            "desire",
        ],
    },

    {
        "word": "HEART",
        "examples": [
            "start",
            "part",
            "smart",
            "art",
        ],
    },

    {
        "word": "DREAM",
        "examples": [
            "team",
            "stream",
            "cream",
            "beam",
        ],
    },

    {
        "word": "FUN",
        "examples": [
            "run",
            "sun",
            "done",
            "one",
        ],
    },

    {
        "word": "SMILE",
        "examples": [
            "style",
            "while",
            "mile",
            "file",
        ],
    },

    {
        "word": "PLAY",
        "examples": [
            "stay",
            "way",
            "day",
            "say",
        ],
    },

    {
        "word": "COOL",
        "examples": [
            "rule",
            "school",
            "pool",
            "tool",
        ],
    },

]


# ==========================================================
# 5-SECOND WORD CHALLENGE
# ==========================================================

FIVE_SECOND_CHALLENGE = [

    "Name 3 things you would take on a road trip.",

    "Name 3 foods you could eat anytime.",

    "Name 3 cities you would like to visit.",

    "Name 3 songs that always get you moving.",

    "Name 3 things that make you smile.",

    "Name 3 things you would bring to a beach day.",

    "Name 3 movies you could watch again.",

    "Name 3 things you look for in a friend.",

    "Name 3 things that make a great date.",

    "Name 3 things you would do on a perfect weekend.",

    "Name 3 hobbies you would like to try.",

    "Name 3 things you cannot live without.",

    "Name 3 places you would travel to tomorrow.",

    "Name 3 things that instantly improve your mood.",

    "Name 3 things you would do with an unexpected day off.",

    "Name 3 things you associate with summer.",

    "Name 3 things you would bring to game night.",

    "Name 3 things that make someone attractive.",

    "Name 3 things you would do on a spontaneous adventure.",

    "Name 3 things that make a conversation interesting.",

    "Name 3 things you would order at your favorite restaurant.",

    "Name 3 things you are grateful for.",

    "Name 3 things you would do if money were no object.",

    "Name 3 things that make a party fun.",

    "Name 3 things you want to accomplish this year.",

]


# ==========================================================
# GAME NAMES
# ==========================================================

GAME_NAMES = {

    "scramble":
        "🔤 Word Scramble",

    "guess":
        "🕵️ Guess the Word",

    "association":
        "🔗 Word Association",

    "rhyme":
        "🎤 Rhyme Time",

    "five_second":
        "⏱️ 5-Second Challenge",

}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():

    return WORD_GAMES_ENABLED


# ==========================================================
# MENU
# ==========================================================

def word_games_keyboard():

    return InlineKeyboardMarkup(
        [

            [
                InlineKeyboardButton(
                    GAME_NAMES["scramble"],
                    callback_data="word_game_scramble",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["guess"],
                    callback_data="word_game_guess",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["association"],
                    callback_data="word_game_association",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["rhyme"],
                    callback_data="word_game_rhyme",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["five_second"],
                    callback_data="word_game_five_second",
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
                    callback_data="word_game_next",
                ),

                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="word_game_pass",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🎮 Other Word Games",
                    callback_data="word_games_menu",
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
        "word_current_game",
        "scramble",
    )


# ==========================================================
# PROMPT GENERATOR
# ==========================================================

def get_prompt(context):

    game = get_current_game(
        context
    )

    # ------------------------------------------------------
    # WORD SCRAMBLE
    # ------------------------------------------------------

    if game == "scramble":

        item = random.choice(
            WORD_SCRAMBLE
        )

        context.user_data[
            "word_current_answer"
        ] = item["word"]

        return (
            "🔤 WORD SCRAMBLE\n\n"

            f"Unscramble this word:\n\n"

            f"👉 {item['scramble']}\n\n"

            "Type your answer in the chat!"
        )

    # ------------------------------------------------------
    # GUESS THE WORD
    # ------------------------------------------------------

    if game == "guess":

        item = random.choice(
            GUESS_THE_WORD
        )

        context.user_data[
            "word_current_answer"
        ] = item["word"]

        return (
            "🕵️ GUESS THE WORD\n\n"

            f"Hint:\n"
            f"👉 {item['hint']}\n\n"

            "Type your answer in the chat!"
        )

    # ------------------------------------------------------
    # WORD ASSOCIATION
    # ------------------------------------------------------

    if game == "association":

        word = random.choice(
            WORD_ASSOCIATION
        )

        context.user_data[
            "word_current_answer"
        ] = None

        return (
            "🔗 WORD ASSOCIATION\n\n"

            f"Your word is:\n\n"

            f"👉 {word}\n\n"

            "Reply with the FIRST word "
            "that comes to your mind."
        )

    # ------------------------------------------------------
    # RHYME TIME
    # ------------------------------------------------------

    if game == "rhyme":

        item = random.choice(
            RHYME_TIME
        )

        context.user_data[
            "word_current_answer"
        ] = item["examples"]

        return (
            "🎤 RHYME TIME\n\n"

            f"Give us a word that rhymes with:\n\n"

            f"👉 {item['word']}\n\n"

            "Type your answer in the chat!"
        )

    # ------------------------------------------------------
    # FIVE SECOND
    # ------------------------------------------------------

    if game == "five_second":

        context.user_data[
            "word_current_answer"
        ] = None

        return (
            "⏱️ 5-SECOND CHALLENGE\n\n"

            f"{random.choice(FIVE_SECOND_CHALLENGE)}\n\n"

            "GO! GO! GO!"
        )

    return (
        "🔤 WORD SCRAMBLE\n\n"
        "Unscramble the word!"
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

        game = "scramble"

    context.user_data[
        "word_current_game"
    ] = game

    prompt = get_prompt(
        context
    )

    context.user_data[
        "word_current_prompt"
    ] = prompt

    title = GAME_NAMES.get(
        game,
        "🎮 Word Game",
    )

    await query.edit_message_text(

        f"{title}\n\n"
        f"{prompt}\n\n"
        "😈 PASS is always allowed.",

        reply_markup=game_controls(),

    )


# ==========================================================
# /WORDGAMES
# ==========================================================

async def word_games(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:

        return

    if not WORD_GAMES_ENABLED:

        await message.reply_text(
            "🔤 Word Games are currently disabled."
        )

        return

    await message.reply_text(

        "🔤 WORD GAMES\n\n"

        "Choose a game below.\n\n"

        "Some games require you to type "
        "your answer directly in the chat.\n\n"

        "😈 PASS is always allowed.",

        reply_markup=word_games_keyboard(),

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

    if not WORD_GAMES_ENABLED:

        await query.answer(
            "Word Games are disabled.",
            show_alert=True,
        )

        return

    # ======================================================
    # MENU
    # ======================================================

    if data == "word_games_menu":

        await query.edit_message_text(

            "🔤 WORD GAMES\n\n"
            "Choose a game:",

            reply_markup=word_games_keyboard(),

        )

        return

    # ======================================================
    # GAME SELECTION
    # ======================================================

    if data.startswith(
        "word_game_"
    ):

        game = data.replace(
            "word_game_",
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

    if data == "word_game_next":

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

    if data == "word_game_pass":

        title = GAME_NAMES.get(

            get_current_game(
                context
            ),

            "🎮 Word Game",

        )

        await query.edit_message_text(

            f"{title}\n\n"

            "😈 PASS ACCEPTED!\n\n"

            "No explanation needed. "
            "Hit Next when you're ready.",

            reply_markup=game_controls(),

        )

        return


# ==========================================================
# TEXT ANSWER CHECKER
#
# This can be registered by games.py for text messages.
# ==========================================================

async def check_text_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:

        return False

    game = get_current_game(
        context
    )

    if game not in (
        "scramble",
        "guess",
        "rhyme",
    ):

        return False

    answer = (
        message.text or ""
    ).strip().lower()

    if not answer:

        return False

    correct = context.user_data.get(
        "word_current_answer"
    )

    if not correct:

        return False

    # ------------------------------------------------------
    # SCRAMBLE / GUESS
    # ------------------------------------------------------

    if isinstance(
        correct,
        str,
    ):

        if answer == correct.lower():

            await message.reply_text(
                "🎉 CORRECT!\n\n"
                f"The answer was **{correct}**!\n\n"
                "🔥 Great job!",
                parse_mode="Markdown",
                reply_markup=game_controls(),
            )

            context.user_data[
                "word_current_answer"
            ] = None

            return True

        return False

    # ------------------------------------------------------
    # RHYME
    # ------------------------------------------------------

    if isinstance(
        correct,
        list,
    ):

        if answer in [
            item.lower()
            for item in correct
        ]:

            await message.reply_text(
                "🎤 NICE RHYME!\n\n"
                "🔥 That works!",
                reply_markup=game_controls(),
            )

            context.user_data[
                "word_current_answer"
            ] = None

            return True

    return False


# ==========================================================
# END word_games.py
# ==========================================================
