# ==========================================================
# Melanated AZ Bot
# games/party_games.py
#
# PARTY GAMES CATEGORY
#
# Games included:
#   - Never Have I Ever
#   - Most Likely To
#   - This or That
#   - Hot Seat
#   - Finish the Sentence
#
# Features:
#   - Button-based menus
#   - Random prompts
#   - PASS support
#   - Next prompt
#   - Return to Games category
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

PARTY_GAMES_ENABLED = True


# ==========================================================
# NEVER HAVE I EVER
# ==========================================================

NEVER_HAVE_I_EVER = [

    "Never have I ever flirted with someone I just met.",
    "Never have I ever sent a message to the wrong person.",
    "Never have I ever had a crush on someone in this group.",
    "Never have I ever gone on a date and immediately wanted to leave.",
    "Never have I ever stayed up all night talking to someone.",
    "Never have I ever kissed someone on the first date.",
    "Never have I ever had chemistry with someone completely unexpected.",
    "Never have I ever pretended not to be interested when I actually was.",
    "Never have I ever slid into someone's DMs first.",
    "Never have I ever been caught flirting.",
    "Never have I ever had a secret crush.",
    "Never have I ever gone on a spontaneous date.",
    "Never have I ever regretted sending a flirty message.",
    "Never have I ever flirted with someone older than me.",
    "Never have I ever flirted with someone younger than me.",
    "Never have I ever matched with someone I already knew.",
    "Never have I ever gone on a date without telling anyone where I was.",
    "Never have I ever fallen for someone's personality before their looks.",
    "Never have I ever been attracted to someone I knew I shouldn't be.",
    "Never have I ever had a friends-with-benefits situation.",
    "Never have I ever kissed more than one person in the same night.",
    "Never have I ever had a crush on a friend's partner.",
    "Never have I ever changed my plans because someone attractive invited me out.",
    "Never have I ever used a cheesy pickup line.",
    "Never have I ever been the one to make the first move.",
]


# ==========================================================
# MOST LIKELY TO
# ==========================================================

MOST_LIKELY_TO = [

    "Who is most likely to make the first move?",
    "Who is most likely to flirt with someone they just met?",
    "Who is most likely to plan the perfect date?",
    "Who is most likely to disappear from the chat and come back with a story?",
    "Who is most likely to fall for someone's personality?",
    "Who is most likely to have a secret crush?",
    "Who is most likely to start a conversation with a stranger?",
    "Who is most likely to send the first DM?",
    "Who is most likely to organize a group adventure?",
    "Who is most likely to stay up all night talking?",
    "Who is most likely to make everyone laugh?",
    "Who is most likely to break the ice?",
    "Who is most likely to try something completely new?",
    "Who is most likely to have the best pickup line?",
    "Who is most likely to turn a casual date into an adventure?",
    "Who is most likely to be the biggest flirt?",
    "Who is most likely to make someone blush?",
    "Who is most likely to suggest a spontaneous road trip?",
    "Who is most likely to have the wildest bucket list?",
    "Who is most likely to make the first move at a party?",
    "Who is most likely to remember everyone's birthday?",
    "Who is most likely to make a new friend anywhere?",
    "Who is most likely to talk their way out of trouble?",
    "Who is most likely to say YES to an adventure?",
    "Who is most likely to turn a boring night into a good time?",
]


# ==========================================================
# THIS OR THAT
# ==========================================================

THIS_OR_THAT = [

    ("Beach", "Mountains"),
    ("Texting", "Calling"),
    ("Morning date", "Late-night date"),
    ("Dinner date", "Adventure date"),
    ("Stay in", "Go out"),
    ("Make the first move", "Be pursued"),
    ("Romantic", "Adventurous"),
    ("Sweet", "Spicy"),
    ("Slow burn", "Instant chemistry"),
    ("Planned date", "Spontaneous date"),
    ("Movies", "Concert"),
    ("Road trip", "Flight"),
    ("Coffee date", "Dinner date"),
    ("Flirty texts", "Flirty calls"),
    ("Private conversation", "Group conversation"),
    ("One-on-one", "Group date"),
    ("Casual", "Formal"),
    ("Sunrise", "Sunset"),
    ("City", "Beach"),
    ("Dance floor", "Lounge"),
    ("Music", "Movies"),
    ("Funny", "Confident"),
    ("Brains", "Looks"),
    ("Personality", "Chemistry"),
    ("Kiss", "Cuddle"),
]


# ==========================================================
# HOT SEAT
# ==========================================================

HOT_SEAT = [

    "What is something people would never guess about you?",
    "What is your biggest green flag?",
    "What is your biggest red flag?",
    "What instantly gets your attention?",
    "What makes you feel comfortable around someone?",
    "What is your favorite type of date?",
    "What is something adventurous you want to try?",
    "What is one thing you absolutely will not compromise on?",
    "What is something you find unexpectedly attractive?",
    "What is your biggest dating pet peeve?",
    "What is the best compliment you have ever received?",
    "What is the boldest thing you have done on a date?",
    "What makes someone unforgettable to you?",
    "What is one thing you wish people knew about you?",
    "What kind of energy attracts you?",
    "What is your favorite way to flirt?",
    "What makes you lose interest immediately?",
    "What is something on your bucket list?",
    "What is your ideal night out?",
    "What is one thing you are always willing to try?",
    "What is one thing you will always say NO to?",
    "What is something that instantly makes you smile?",
    "What is your favorite way to meet new people?",
    "What is something you have learned from past relationships?",
    "What is one adventure you want to experience someday?",
]


# ==========================================================
# FINISH THE SENTENCE
# ==========================================================

FINISH_THE_SENTENCE = [

    "The fastest way to get my attention is ______.",
    "My perfect date would be ______.",
    "I instantly smile when ______.",
    "The biggest green flag is ______.",
    "The biggest red flag is ______.",
    "I feel most confident when ______.",
    "My idea of a perfect night is ______.",
    "I would never say no to ______.",
    "One thing on my bucket list is ______.",
    "The best way to flirt with me is ______.",
    "I know there is chemistry when ______.",
    "I immediately notice someone's ______.",
    "The most adventurous thing I would try is ______.",
    "My favorite way to spend a weekend is ______.",
    "A great conversation starts with ______.",
    "I cannot resist someone who ______.",
    "My biggest weakness is ______.",
    "I am always down for ______.",
    "The perfect first date includes ______.",
    "I feel most comfortable when ______.",
    "Something that always makes me laugh is ______.",
    "The best compliment someone can give me is ______.",
    "If I could travel anywhere tomorrow, I would go to ______.",
    "A spontaneous adventure sounds like ______.",
    "One thing I want to experience someday is ______.",
]


# ==========================================================
# GAME NAMES
# ==========================================================

GAME_NAMES = {
    "never": "🙅 Never Have I Ever",
    "most_likely": "👀 Most Likely To",
    "this_that": "⚖️ This or That",
    "hot_seat": "🔥 Hot Seat",
    "finish": "✍️ Finish the Sentence",
}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():
    return PARTY_GAMES_ENABLED


# ==========================================================
# MAIN MENU
# ==========================================================

def party_games_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    GAME_NAMES["never"],
                    callback_data="party_game_never",
                ),
            ],
            [
                InlineKeyboardButton(
                    GAME_NAMES["most_likely"],
                    callback_data="party_game_most_likely",
                ),
            ],
            [
                InlineKeyboardButton(
                    GAME_NAMES["this_that"],
                    callback_data="party_game_this_that",
                ),
            ],
            [
                InlineKeyboardButton(
                    GAME_NAMES["hot_seat"],
                    callback_data="party_game_hot_seat",
                ),
            ],
            [
                InlineKeyboardButton(
                    GAME_NAMES["finish"],
                    callback_data="party_game_finish",
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
                    callback_data="party_game_next",
                ),
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="party_game_pass",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎮 Other Party Games",
                    callback_data="party_games_menu",
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
# GET CURRENT GAME
# ==========================================================

def get_current_game(context):

    return context.user_data.get(
        "party_current_game",
        "never",
    )


# ==========================================================
# GET PROMPT
# ==========================================================

def get_prompt(context):

    game = get_current_game(context)

    if game == "never":

        return random.choice(
            NEVER_HAVE_I_EVER
        )

    if game == "most_likely":

        return random.choice(
            MOST_LIKELY_TO
        )

    if game == "this_that":

        first, second = random.choice(
            THIS_OR_THAT
        )

        return (
            f"Would you rather choose:\n\n"
            f"🅰️ {first}\n\n"
            f"OR\n\n"
            f"🅱️ {second}"
        )

    if game == "hot_seat":

        return random.choice(
            HOT_SEAT
        )

    if game == "finish":

        return random.choice(
            FINISH_THE_SENTENCE
        )

    return random.choice(
        NEVER_HAVE_I_EVER
    )


# ==========================================================
# FORMAT GAME
# ==========================================================

def format_game(context):

    game = get_current_game(context)

    title = GAME_NAMES.get(
        game,
        "🎮 Party Game",
    )

    prompt = get_prompt(context)

    context.user_data[
        "party_current_prompt"
    ] = prompt

    return (
        f"{title}\n\n"
        f"{prompt}\n\n"
        "😈 You can PASS at any time."
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

        game = "never"

    context.user_data[
        "party_current_game"
    ] = game

    context.user_data[
        "party_current_prompt"
    ] = None

    await query.edit_message_text(
        format_game(context),
        reply_markup=game_controls(),
    )


# ==========================================================
# /PARTYGAMES
# ==========================================================

async def party_games(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:

        return

    if not PARTY_GAMES_ENABLED:

        await message.reply_text(
            "🎮 Party Games are currently disabled."
        )

        return

    await message.reply_text(
        "🎮 PARTY GAMES\n\n"
        "Choose a game:\n\n"
        "Have fun, respect boundaries, "
        "and remember that PASS is always allowed.",
        reply_markup=party_games_keyboard(),
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

    if not PARTY_GAMES_ENABLED:

        await query.answer(
            "Party Games are disabled.",
            show_alert=True,
        )

        return

    # ======================================================
    # MENU
    # ======================================================

    if data == "party_games_menu":

        await query.edit_message_text(
            "🎮 PARTY GAMES\n\n"
            "Choose a game:",
            reply_markup=party_games_keyboard(),
        )

        return

    # ======================================================
    # GAME SELECTION
    # ======================================================

    if data.startswith("party_game_"):

        game = data.replace(
            "party_game_",
            "",
            1,
        )

        # Don't treat controls as games.

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

    if data == "party_game_next":

        game = get_current_game(context)

        await start_game(
            query,
            context,
            game,
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "party_game_pass":

        game = get_current_game(context)

        title = GAME_NAMES.get(
            game,
            "🎮 Party Game",
        )

        await query.edit_message_text(
            f"{title}\n\n"
            "😈 PASS ACCEPTED!\n\n"
            "No explanation needed. "
            "Choose another prompt when you're ready.",
            reply_markup=game_controls(),
        )

        return


# ==========================================================
# END party_games.py
# ==========================================================
