# ==========================================================
# Melanated AZ Bot
# games/party_games.py
#
# PARTY GAMES
#
# Includes:
#   - Never Have I Ever
#   - Most Likely To
#   - This or That
#   - Hot Seat
#   - Finish the Sentence
#
# Features:
#   - Button-based menus
#   - Random prompts
#   - PASS allowed
#   - Next prompt
#   - Return to party menu
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

PARTY_GAMES_ENABLED = True


# ==========================================================
# NEVER HAVE I EVER
# ==========================================================

NEVER_HAVE_I_EVER = [

    "Never have I ever lied about why I was late.",
    "Never have I ever sent a message to the wrong person.",
    "Never have I ever pretended to know someone I didn't remember.",
    "Never have I ever danced when nobody was watching.",
    "Never have I ever stayed up all night talking to someone.",
    "Never have I ever had a crush on someone I shouldn't have.",
    "Never have I ever flirted just for fun.",
    "Never have I ever deleted a message because I got nervous.",
    "Never have I ever gone on a spontaneous adventure.",
    "Never have I ever regretted sending a late-night message.",
    "Never have I ever had chemistry with someone completely unexpected.",
    "Never have I ever flirted with someone I met online.",
    "Never have I ever had a secret crush.",
    "Never have I ever gone somewhere just because someone I liked was there.",
    "Never have I ever stayed in a conversation way longer than I planned.",
    "Never have I ever been caught checking someone out.",
    "Never have I ever had a crush on a friend's friend.",
    "Never have I ever made the first move.",
    "Never have I ever been the one who got pursued.",
    "Never have I ever changed my plans because of someone attractive.",
    "Never have I ever kissed someone on a first date.",
    "Never have I ever had a dating app story worth telling.",
    "Never have I ever flirted with someone I knew was trouble.",
    "Never have I ever had an unforgettable first date.",
    "Never have I ever been attracted to someone because of their voice.",
    "Never have I ever developed feelings unexpectedly.",
    "Never have I ever had chemistry with someone I initially wasn't interested in.",
    "Never have I ever gone on a date without telling anyone where I was going.",
    "Never have I ever had a crush that lasted way too long.",
    "Never have I ever been surprised by who I found attractive.",

]


# ==========================================================
# MOST LIKELY TO
# ==========================================================

MOST_LIKELY_TO = [

    "Who is most likely to make the first move?",
    "Who is most likely to flirt with someone they just met?",
    "Who is most likely to plan a spontaneous adventure?",
    "Who is most likely to stay up all night talking?",
    "Who is most likely to have a secret crush?",
    "Who is most likely to send the first message?",
    "Who is most likely to make everyone laugh?",
    "Who is most likely to disappear on a weekend adventure?",
    "Who is most likely to organize the group?",
    "Who is most likely to break the ice?",
    "Who is most likely to get caught flirting?",
    "Who is most likely to have the best pickup line?",
    "Who is most likely to turn a casual night into an adventure?",
    "Who is most likely to fall for someone's personality first?",
    "Who is most likely to make a bold decision?",
    "Who is most likely to be the biggest tease?",
    "Who is most likely to make the first move at a party?",
    "Who is most likely to have chemistry with someone unexpected?",
    "Who is most likely to convince everyone to go out?",
    "Who is most likely to start a group conversation?",
    "Who is most likely to plan the perfect date?",
    "Who is most likely to keep a secret?",
    "Who is most likely to make someone blush?",
    "Who is most likely to get everyone's attention without trying?",
    "Who is most likely to say yes to a spontaneous adventure?",
    "Who is most likely to have the wildest story?",
    "Who is most likely to become friends with a stranger?",
    "Who is most likely to be the last person awake?",
    "Who is most likely to make a dramatic entrance?",
    "Who is most likely to surprise everyone?",

]


# ==========================================================
# THIS OR THAT
# ==========================================================

THIS_OR_THAT = [

    (
        "Beach vacation 🌴",
        "Mountain getaway 🏔️",
    ),

    (
        "Morning date ☀️",
        "Late-night date 🌙",
    ),

    (
        "Texting 💬",
        "Phone calls 📞",
    ),

    (
        "Dinner date 🍽️",
        "Drinks date 🥂",
    ),

    (
        "Stay in 🏠",
        "Go out 🎉",
    ),

    (
        "Plan everything 📋",
        "Go with the flow 🌊",
    ),

    (
        "Make the first move 😈",
        "Be pursued 🔥",
    ),

    (
        "Slow burn ❤️",
        "Instant chemistry ⚡",
    ),

    (
        "Romantic date 🌹",
        "Adventurous date 🔥",
    ),

    (
        "Movie night 🎬",
        "Game night 🎮",
    ),

    (
        "Big party 🎉",
        "Small gathering 🥂",
    ),

    (
        "Sweet compliments 💜",
        "Flirty teasing 😈",
    ),

    (
        "Dance floor 💃",
        "Lounge area 🛋️",
    ),

    (
        "Road trip 🚗",
        "Flight somewhere new ✈️",
    ),

    (
        "Surprise date 🎁",
        "Planned date 📅",
    ),

    (
        "Private conversation 💬",
        "Group conversation 👥",
    ),

    (
        "Confidence 😎",
        "Mystery 🖤",
    ),

    (
        "Funny personality 😂",
        "Flirty personality 😏",
    ),

    (
        "First kiss 💋",
        "First deep conversation ❤️",
    ),

    (
        "Adventure 🗺️",
        "Relaxation 🛋️",
    ),

]


# ==========================================================
# HOT SEAT
# ==========================================================

HOT_SEAT = [

    "What is something people notice about you first?",
    "What is your biggest green flag?",
    "What is your biggest dating red flag?",
    "What makes you feel instantly comfortable around someone?",
    "What is your favorite way to flirt?",
    "What type of personality attracts you?",
    "What is your ideal date?",
    "What makes someone unforgettable to you?",
    "What is something adventurous you want to try?",
    "What is something you are surprisingly good at?",
    "What is one thing you could talk about for hours?",
    "What is your biggest pet peeve?",
    "What instantly makes you laugh?",
    "What is something you find unexpectedly attractive?",
    "What is your favorite way to spend a free night?",
    "What is something on your bucket list?",
    "What is one thing you will never compromise on?",
    "What is your favorite compliment to receive?",
    "What kind of energy attracts you?",
    "What makes you lose interest immediately?",
    "What is something people often misunderstand about you?",
    "What is your favorite type of adventure?",
    "What is something you have always wanted to learn?",
    "What is your perfect weekend?",
    "What is one thing you would change about your dating life?",
    "What is your favorite way to make someone feel special?",
    "What is something that always puts you in a good mood?",
    "What is one experience you will never forget?",
    "What is something you want to accomplish this year?",
    "What is your definition of great chemistry?",

]


# ==========================================================
# FINISH THE SENTENCE
# ==========================================================

FINISH_THE_SENTENCE = [

    "The fastest way to get my attention is...",
    "My biggest green flag is...",
    "My biggest turn-off is...",
    "A perfect date would be...",
    "I instantly smile when...",
    "I know there is chemistry when...",
    "My idea of a perfect weekend is...",
    "One thing I will always make time for is...",
    "The most adventurous thing I would try is...",
    "I am secretly really good at...",
    "One thing people should know about me is...",
    "The best compliment someone can give me is...",
    "I could never live without...",
    "My biggest weakness is...",
    "The quickest way to make me laugh is...",
    "A place I would love to visit is...",
    "My favorite way to relax is...",
    "If I could plan any date, it would be...",
    "Something I have always wanted to try is...",
    "My ideal night starts with...",
    "Someone instantly becomes more attractive when...",
    "I feel most confident when...",
    "One thing on my bucket list is...",
    "The best kind of chemistry is...",
    "If I could have one superpower, it would be...",
    "The most spontaneous thing I would do is...",
    "My perfect adventure would be...",
    "One thing that always makes me smile is...",
    "If I had an unexpected day off, I would...",
    "The one thing I would never compromise on is...",

]


# ==========================================================
# GAME NAMES
# ==========================================================

GAME_NAMES = {

    "never": "🙅🏾 Never Have I Ever",

    "likely": "👀 Most Likely To",

    "this_or_that": "🔀 This or That",

    "hot_seat": "🔥 Hot Seat",

    "finish": "✍🏾 Finish the Sentence",

}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():

    return PARTY_GAMES_ENABLED


# ==========================================================
# MAIN MENU
# ==========================================================

def party_menu_keyboard():

    return InlineKeyboardMarkup(

        [

            [
                InlineKeyboardButton(
                    GAME_NAMES["never"],
                    callback_data="party_never",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["likely"],
                    callback_data="party_likely",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["this_or_that"],
                    callback_data="party_this_or_that",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["hot_seat"],
                    callback_data="party_hot_seat",
                ),
            ],

            [
                InlineKeyboardButton(
                    GAME_NAMES["finish"],
                    callback_data="party_finish",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🔙 Games Menu",
                    callback_data="games_menu",
                ),
            ],

        ]

    )


# ==========================================================
# PROMPT KEYBOARD
# ==========================================================

def prompt_keyboard():

    return InlineKeyboardMarkup(

        [

            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="party_next",
                ),
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="party_pass",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🎉 Party Games",
                    callback_data="party_menu",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🎮 Games Menu",
                    callback_data="games_menu",
                ),
            ],

        ]

    )


# ==========================================================
# THIS OR THAT KEYBOARD
# ==========================================================

def this_or_that_keyboard():

    return InlineKeyboardMarkup(

        [

            [
                InlineKeyboardButton(
                    "1️⃣ OPTION 1",
                    callback_data="party_choice_0",
                ),
            ],

            [
                InlineKeyboardButton(
                    "2️⃣ OPTION 2",
                    callback_data="party_choice_1",
                ),
            ],

            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="party_pass",
                ),
            ],

            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="party_next",
                ),
            ],

        ]

    )


# ==========================================================
# GET GAME
# ==========================================================

def get_game(context):

    game = context.user_data.get(
        "party_game",
        "never",
    )

    if game not in GAME_NAMES:

        game = "never"

    return game


# ==========================================================
# GET RANDOM PROMPT
# ==========================================================

def get_prompt(context):

    game = get_game(context)

    if game == "never":

        prompt = random.choice(
            NEVER_HAVE_I_EVER
        )

    elif game == "likely":

        prompt = random.choice(
            MOST_LIKELY_TO
        )

    elif game == "hot_seat":

        prompt = random.choice(
            HOT_SEAT
        )

    elif game == "finish":

        prompt = random.choice(
            FINISH_THE_SENTENCE
        )

    else:

        prompt = random.choice(
            NEVER_HAVE_I_EVER
        )

    context.user_data[
        "party_current_prompt"
    ] = prompt

    context.user_data[
        "party_answered"
    ] = False

    return prompt


# ==========================================================
# SHOW MENU
# ==========================================================

async def show_menu(
    query,
    context,
):

    await query.edit_message_text(

        "🎉 PARTY GAMES\n\n"
        "Choose a game:\n\n"
        "🙅🏾 Never Have I Ever\n"
        "👀 Most Likely To\n"
        "🔀 This or That\n"
        "🔥 Hot Seat\n"
        "✍🏾 Finish the Sentence\n\n"
        "😈 PASS is always allowed.",

        reply_markup=party_menu_keyboard(),

    )


# ==========================================================
# SHOW PROMPT
# ==========================================================

async def show_prompt(
    query,
    context,
):

    game = get_game(context)

    # ------------------------------------------------------
    # THIS OR THAT
    # ------------------------------------------------------

    if game == "this_or_that":

        option1, option2 = random.choice(
            THIS_OR_THAT
        )

        context.user_data[
            "party_current_prompt"
        ] = (
            option1,
            option2,
        )

        context.user_data[
            "party_answered"
        ] = False

        await query.edit_message_text(

            "🔀 THIS OR THAT\n\n"
            "Choose one:\n\n"
            f"1️⃣ {option1}\n\n"
            f"2️⃣ {option2}\n\n"
            "😈 PASS is always allowed.",

            reply_markup=this_or_that_keyboard(),

        )

        return

    # ------------------------------------------------------
    # NORMAL PROMPTS
    # ------------------------------------------------------

    prompt = get_prompt(context)

    await query.edit_message_text(

        f"{GAME_NAMES.get(game, '🎉 Party Game')}\n\n"
        f"{prompt}\n\n"
        "😈 PASS is always allowed.",

        reply_markup=prompt_keyboard(),

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
            "🎉 Party Games are currently disabled."
        )

        return

    await message.reply_text(

        "🎉 PARTY GAMES\n\n"
        "Choose a game:\n\n"
        "🙅🏾 Never Have I Ever\n"
        "👀 Most Likely To\n"
        "🔀 This or That\n"
        "🔥 Hot Seat\n"
        "✍🏾 Finish the Sentence\n\n"
        "😈 PASS is always allowed.",

        reply_markup=party_menu_keyboard(),

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
    # PARTY MENU
    # ======================================================

    if data == "party_menu":

        await show_menu(
            query,
            context,
        )

        return

    # ======================================================
    # SELECT NEVER HAVE I EVER
    # ======================================================

    if data == "party_never":

        context.user_data[
            "party_game"
        ] = "never"

        await show_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # SELECT MOST LIKELY TO
    # ======================================================

    if data == "party_likely":

        context.user_data[
            "party_game"
        ] = "likely"

        await show_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # SELECT THIS OR THAT
    # ======================================================

    if data == "party_this_or_that":

        context.user_data[
            "party_game"
        ] = "this_or_that"

        await show_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # SELECT HOT SEAT
    # ======================================================

    if data == "party_hot_seat":

        context.user_data[
            "party_game"
        ] = "hot_seat"

        await show_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # SELECT FINISH THE SENTENCE
    # ======================================================

    if data == "party_finish":

        context.user_data[
            "party_game"
        ] = "finish"

        await show_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "party_next":

        await show_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "party_pass":

        context.user_data[
            "party_answered"
        ] = True

        await query.answer(
            "😈 PASS accepted!",
            show_alert=True,
        )

        await query.edit_message_text(

            "😈 PASS ACCEPTED\n\n"
            "No explanation needed.\n"
            "Respect the boundaries.\n\n"
            "Ready for another one?",

            reply_markup=InlineKeyboardMarkup(

                [

                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="party_next",
                        ),
                    ],

                    [
                        InlineKeyboardButton(
                            "🎉 Party Games",
                            callback_data="party_menu",
                        ),
                    ],

                    [
                        InlineKeyboardButton(
                            "🎮 Games Menu",
                            callback_data="games_menu",
                        ),
                    ],

                ]

            ),

        )

        return

    # ======================================================
    # THIS OR THAT CHOICE
    # ======================================================

    if data.startswith("party_choice_"):

        if context.user_data.get(
            "party_answered",
            False,
        ):

            await query.answer(
                "This round is already finished.",
                show_alert=True,
            )

            return

        try:

            choice = int(
                data.replace(
                    "party_choice_",
                    "",
                    1,
                )
            )

        except ValueError:

            return

        prompt = context.user_data.get(
            "party_current_prompt"
        )

        if not isinstance(
            prompt,
            tuple,
        ):

            await query.answer(
                "Please start a new round.",
                show_alert=True,
            )

            return

        if choice not in (0, 1):

            return

        context.user_data[
            "party_answered"
        ] = True

        selected = prompt[choice]

        await query.answer(
            "Choice recorded!",
            show_alert=True,
        )

        await query.edit_message_text(

            "🔀 THIS OR THAT\n\n"
            f"👉 You chose:\n"
            f"{selected}\n\n"
            "🔥 Good choice!\n\n"
            "Ready for another one?",

            reply_markup=InlineKeyboardMarkup(

                [

                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="party_next",
                        ),
                    ],

                    [
                        InlineKeyboardButton(
                            "🎉 Party Games",
                            callback_data="party_menu",
                        ),
                    ],

                    [
                        InlineKeyboardButton(
                            "🎮 Games Menu",
                            callback_data="games_menu",
                        ),
                    ],

                ]

            ),

        )

        return


# ==========================================================
# RESET
# ==========================================================

def reset_party_game(context):

    context.user_data[
        "party_game"
    ] = "never"

    context.user_data[
        "party_current_prompt"
    ] = None

    context.user_data[
        "party_answered"
    ] = False


# ==========================================================
# END party_games.py
# ==========================================================
