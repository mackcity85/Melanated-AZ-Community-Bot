# ==========================================================
# Melanated AZ Bot
# games/word_scramble.py
#
# WORD SCRAMBLE
#
# Features:
#   - Button-based word scramble
#   - Multiple categories
#   - Easy / Medium / Hard
#   - Random words
#   - Multiple-choice answers
#   - Score tracking
#   - Streak tracking
#   - PASS allowed
#   - Next challenge
#   - Change category
#   - Change difficulty
#
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

WORD_SCRAMBLE_ENABLED = True

VALID_DIFFICULTIES = (
    "easy",
    "medium",
    "hard",
)


# ==========================================================
# WORDS
#
# Each word:
#
# {
#     "word": "BLACK",
#     "category": "Culture",
# }
#
# The game automatically creates three incorrect choices.
# ==========================================================

WORDS = {

    # ======================================================
    # GENERAL
    # ======================================================

    "general": {

        "easy": [
            {"word": "APPLE", "category": "Food"},
            {"word": "HOUSE", "category": "Places"},
            {"word": "MUSIC", "category": "Entertainment"},
            {"word": "WATER", "category": "Nature"},
            {"word": "PHONE", "category": "Technology"},
            {"word": "CLOUD", "category": "Nature"},
            {"word": "CHAIR", "category": "Everyday"},
            {"word": "TIGER", "category": "Animals"},
            {"word": "PIZZA", "category": "Food"},
            {"word": "BEACH", "category": "Places"},
        ],

        "medium": [
            {"word": "JOURNEY", "category": "Travel"},
            {"word": "SUNSET", "category": "Nature"},
            {"word": "FREEDOM", "category": "Ideas"},
            {"word": "DIAMOND", "category": "Nature"},
            {"word": "THUNDER", "category": "Nature"},
            {"word": "FAMILY", "category": "People"},
            {"word": "ADVENTURE", "category": "Experiences"},
            {"word": "PASSION", "category": "Ideas"},
            {"word": "HOLIDAY", "category": "Events"},
            {"word": "TREASURE", "category": "Objects"},
        ],

        "hard": [
            {"word": "CHALLENGE", "category": "Ideas"},
            {"word": "DISCOVERY", "category": "Ideas"},
            {"word": "IMAGINATION", "category": "Ideas"},
            {"word": "KNOWLEDGE", "category": "Ideas"},
            {"word": "CELEBRATION", "category": "Events"},
            {"word": "OPPORTUNITY", "category": "Ideas"},
            {"word": "EXPERIENCE", "category": "Ideas"},
            {"word": "ADVENTUROUS", "category": "Personality"},
            {"word": "CONNECTION", "category": "Relationships"},
            {"word": "CREATIVITY", "category": "Ideas"},
        ],
    },

    # ======================================================
    # MUSIC
    # ======================================================

    "music": {

        "easy": [
            {"word": "GUITAR", "category": "Instrument"},
            {"word": "PIANO", "category": "Instrument"},
            {"word": "DRUMS", "category": "Instrument"},
            {"word": "SINGER", "category": "Music"},
            {"word": "RHYTHM", "category": "Music"},
            {"word": "MELODY", "category": "Music"},
            {"word": "BEAT", "category": "Music"},
            {"word": "SONG", "category": "Music"},
        ],

        "medium": [
            {"word": "JAZZ", "category": "Genre"},
            {"word": "HIPHOP", "category": "Genre"},
            {"word": "SOUL", "category": "Genre"},
            {"word": "REGGAE", "category": "Genre"},
            {"word": "RHYTHM", "category": "Music"},
            {"word": "VOCALS", "category": "Music"},
            {"word": "CONCERT", "category": "Event"},
            {"word": "PLAYLIST", "category": "Music"},
        ],

        "hard": [
            {"word": "ORCHESTRA", "category": "Music"},
            {"word": "COMPOSITION", "category": "Music"},
            {"word": "IMPROVISATION", "category": "Music"},
            {"word": "PERCUSSION", "category": "Instrument Family"},
            {"word": "SAXOPHONE", "category": "Instrument"},
            {"word": "HARMONICA", "category": "Instrument"},
            {"word": "SYMPHONY", "category": "Music"},
            {"word": "ARRANGEMENT", "category": "Music"},
        ],
    },

    # ======================================================
    # MOVIES
    # ======================================================

    "movies": {

        "easy": [
            {"word": "ACTOR", "category": "Movies"},
            {"word": "MOVIE", "category": "Movies"},
            {"word": "HERO", "category": "Movies"},
            {"word": "VILLAIN", "category": "Movies"},
            {"word": "SCENE", "category": "Movies"},
            {"word": "COMEDY", "category": "Genre"},
            {"word": "DRAMA", "category": "Genre"},
            {"word": "HORROR", "category": "Genre"},
        ],

        "medium": [
            {"word": "DIRECTOR", "category": "Movies"},
            {"word": "HOLLYWOOD", "category": "Movies"},
            {"word": "SCREENPLAY", "category": "Movies"},
            {"word": "CINEMA", "category": "Movies"},
            {"word": "SUPERHERO", "category": "Movies"},
            {"word": "BLOCKBUSTER", "category": "Movies"},
            {"word": "TRAILER", "category": "Movies"},
            {"word": "PREMIERE", "category": "Movies"},
        ],

        "hard": [
            {"word": "CINEMATOGRAPHY", "category": "Film"},
            {"word": "PROTAGONIST", "category": "Film"},
            {"word": "SCREENWRITER", "category": "Film"},
            {"word": "PRODUCTION", "category": "Film"},
            {"word": "SOUNDTRACK", "category": "Film"},
            {"word": "CHARACTERIZATION", "category": "Film"},
            {"word": "DOCUMENTARY", "category": "Film"},
        ],
    },

    # ======================================================
    # BLACK HISTORY & CULTURE
    # ======================================================

    "black_history": {

        "easy": [
            {"word": "FREEDOM", "category": "History"},
            {"word": "CULTURE", "category": "Culture"},
            {"word": "PRIDE", "category": "Community"},
            {"word": "JUSTICE", "category": "Civil Rights"},
            {"word": "LEGACY", "category": "History"},
            {"word": "UNITY", "category": "Community"},
            {"word": "HISTORY", "category": "History"},
            {"word": "LEADER", "category": "Leadership"},
        ],

        "medium": [
            {"word": "JUNETEENTH", "category": "History"},
            {"word": "HARLEM", "category": "Culture"},
            {"word": "FREEDOM", "category": "Civil Rights"},
            {"word": "ACTIVIST", "category": "Civil Rights"},
            {"word": "COMMUNITY", "category": "Community"},
            {"word": "RESISTANCE", "category": "History"},
            {"word": "HERITAGE", "category": "Culture"},
            {"word": "MOVEMENT", "category": "History"},
        ],

        "hard": [
            {"word": "RECONSTRUCTION", "category": "History"},
            {"word": "ABOLITIONIST", "category": "History"},
            {"word": "SEGREGATION", "category": "History"},
            {"word": "EMANCIPATION", "category": "History"},
            {"word": "ENTREPRENEURSHIP", "category": "Culture"},
            {"word": "INTEGRATION", "category": "Civil Rights"},
            {"word": "PANAFRICANISM", "category": "History"},
        ],
    },

    # ======================================================
    # SPORTS
    # ======================================================

    "sports": {

        "easy": [
            {"word": "FOOTBALL", "category": "Sport"},
            {"word": "BASKETBALL", "category": "Sport"},
            {"word": "BASEBALL", "category": "Sport"},
            {"word": "SOCCER", "category": "Sport"},
            {"word": "TENNIS", "category": "Sport"},
            {"word": "BOXING", "category": "Sport"},
            {"word": "RUNNER", "category": "Sport"},
            {"word": "COACH", "category": "Sports"},
        ],

        "medium": [
            {"word": "TOUCHDOWN", "category": "Football"},
            {"word": "QUARTERBACK", "category": "Football"},
            {"word": "DRIBBLE", "category": "Basketball"},
            {"word": "HOME RUN", "category": "Baseball"},
            {"word": "GOALKEEPER", "category": "Soccer"},
            {"word": "CHAMPIONSHIP", "category": "Sports"},
            {"word": "ATHLETE", "category": "Sports"},
            {"word": "PLAYOFFS", "category": "Sports"},
        ],

        "hard": [
            {"word": "OFFSIDES", "category": "Soccer"},
            {"word": "INTERCEPTION", "category": "Football"},
            {"word": "CONTRIBUTION", "category": "Sports"},
            {"word": "DEFENSIVE", "category": "Sports"},
            {"word": "CHOREOGRAPHY", "category": "Sports"},
            {"word": "COMPETITION", "category": "Sports"},
            {"word": "CHAMPIONSHIP", "category": "Sports"},
        ],
    },

    # ======================================================
    # ADULT COMMUNITY
    #
    # Kept playful rather than explicit.
    # ======================================================

    "adult": {

        "easy": [
            {"word": "FLIRT", "category": "Vibes"},
            {"word": "DATE", "category": "Dating"},
            {"word": "KISS", "category": "Romance"},
            {"word": "TEASE", "category": "Flirting"},
            {"word": "CHEMISTRY", "category": "Connection"},
            {"word": "DESIRE", "category": "Attraction"},
            {"word": "ROMANCE", "category": "Dating"},
            {"word": "VIBES", "category": "Energy"},
        ],

        "medium": [
            {"word": "ATTRACTION", "category": "Dating"},
            {"word": "ADVENTURE", "category": "Experiences"},
            {"word": "BOUNDARIES", "category": "Consent"},
            {"word": "CONSENT", "category": "Safety"},
            {"word": "CONFIDENCE", "category": "Dating"},
            {"word": "PASSION", "category": "Attraction"},
            {"word": "CONNECTION", "category": "Relationships"},
            {"word": "EXPLORATION", "category": "Experiences"},
        ],

        "hard": [
            {"word": "COMMUNICATION", "category": "Relationships"},
            {"word": "COMPATIBILITY", "category": "Relationships"},
            {"word": "VULNERABILITY", "category": "Relationships"},
            {"word": "NEGOTIATION", "category": "Communication"},
            {"word": "EXPECTATIONS", "category": "Relationships"},
            {"word": "ADVENTUROUS", "category": "Personality"},
            {"word": "CONSENSUAL", "category": "Consent"},
        ],
    },
}


# ==========================================================
# CATEGORY NAMES
# ==========================================================

CATEGORY_NAMES = {
    "general": "🌎 General",
    "music": "🎵 Music",
    "movies": "🎬 Movies",
    "black_history": "✊🏾 Black History & Culture",
    "sports": "🏆 Sports",
    "adult": "🔥 Adult Community",
}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():
    return WORD_SCRAMBLE_ENABLED


# ==========================================================
# GET CATEGORY
# ==========================================================

def get_category(context):

    category = context.user_data.get(
        "scramble_category",
        "general",
    )

    if category not in WORDS:
        category = "general"

    return category


# ==========================================================
# GET DIFFICULTY
# ==========================================================

def get_difficulty(context):

    difficulty = context.user_data.get(
        "scramble_difficulty",
        "easy",
    )

    if difficulty not in VALID_DIFFICULTIES:
        difficulty = "easy"

    return difficulty


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def category_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["general"],
                    callback_data="scramble_category_general",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["music"],
                    callback_data="scramble_category_music",
                ),
                InlineKeyboardButton(
                    CATEGORY_NAMES["movies"],
                    callback_data="scramble_category_movies",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["black_history"],
                    callback_data="scramble_category_black_history",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["sports"],
                    callback_data="scramble_category_sports",
                ),
                InlineKeyboardButton(
                    CATEGORY_NAMES["adult"],
                    callback_data="scramble_category_adult",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎯 Change Difficulty",
                    callback_data="scramble_difficulty_menu",
                ),
            ],
        ]
    )


# ==========================================================
# DIFFICULTY KEYBOARD
# ==========================================================

def difficulty_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 Easy",
                    callback_data="scramble_difficulty_easy",
                ),
                InlineKeyboardButton(
                    "🟡 Medium",
                    callback_data="scramble_difficulty_medium",
                ),
                InlineKeyboardButton(
                    "🔴 Hard",
                    callback_data="scramble_difficulty_hard",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 Categories",
                    callback_data="scramble_category_menu",
                ),
            ],
        ]
    )


# ==========================================================
# SCRAMBLE WORD
# ==========================================================

def scramble_word(word):

    clean_word = word.replace(
        " ",
        "",
    )

    if len(clean_word) <= 3:
        return clean_word

    letters = list(clean_word)

    original = "".join(letters)

    for _ in range(20):

        random.shuffle(letters)

        scrambled = "".join(letters)

        if scrambled != original:
            return scrambled

    return original


# ==========================================================
# BUILD ANSWERS
# ==========================================================

def build_answers(context, correct_word):

    category = get_category(context)
    difficulty = get_difficulty(context)

    pool = [
        item["word"]
        for item in WORDS.get(
            category,
            {},
        ).get(
            difficulty,
            [],
        )
    ]

    incorrect_pool = [
        word
        for word in pool
        if word != correct_word
    ]

    random.shuffle(incorrect_pool)

    answers = [
        correct_word,
    ]

    for word in incorrect_pool:

        if word not in answers:

            answers.append(word)

        if len(answers) >= 4:
            break

    # If a category does not have enough choices,
    # pull from all categories at the same difficulty.

    if len(answers) < 4:

        for other_category in WORDS.values():

            for item in other_category.get(
                difficulty,
                [],
            ):

                word = item["word"]

                if word not in answers:

                    answers.append(word)

                if len(answers) >= 4:
                    break

            if len(answers) >= 4:
                break

    random.shuffle(answers)

    return answers


# ==========================================================
# GET CHALLENGE
# ==========================================================

def get_challenge(context):

    category = get_category(context)
    difficulty = get_difficulty(context)

    pool = WORDS.get(
        category,
        {},
    ).get(
        difficulty,
        [],
    )

    if not pool:

        category = "general"
        difficulty = "easy"

        context.user_data[
            "scramble_category"
        ] = category

        context.user_data[
            "scramble_difficulty"
        ] = difficulty

        pool = WORDS[
            category
        ][difficulty]

    item = random.choice(pool)

    word = item["word"]

    scrambled = scramble_word(word)

    answers = build_answers(
        context,
        word,
    )

    correct_index = answers.index(
        word
    )

    challenge = {
        "word": word,
        "scrambled": scrambled,
        "category": item["category"],
        "answers": answers,
        "correct": correct_index,
    }

    context.user_data[
        "scramble_current"
    ] = challenge

    context.user_data[
        "scramble_answered"
    ] = False

    return challenge


# ==========================================================
# INITIALIZE SCORE
# ==========================================================

def initialize_score(context):

    if "scramble_score" not in context.user_data:
        context.user_data["scramble_score"] = 0

    if "scramble_streak" not in context.user_data:
        context.user_data["scramble_streak"] = 0

    if "scramble_questions" not in context.user_data:
        context.user_data["scramble_questions"] = 0


# ==========================================================
# SCORE TEXT
# ==========================================================

def score_text(context):

    initialize_score(context)

    return (
        f"🏆 Score: {context.user_data.get('scramble_score', 0)}\n"
        f"🔥 Streak: {context.user_data.get('scramble_streak', 0)}\n"
        f"🔤 Words: {context.user_data.get('scramble_questions', 0)}"
    )


# ==========================================================
# FORMAT CHALLENGE
# ==========================================================

def format_challenge(
    challenge,
    context,
):

    category = get_category(context)
    difficulty = get_difficulty(context)

    return (
        "🔤 WORD SCRAMBLE\n\n"
        f"📚 Category: {CATEGORY_NAMES.get(category, category)}\n"
        f"🎯 Difficulty: {difficulty.upper()}\n\n"
        f"🔀 Unscramble this word:\n\n"
        f"👉 {challenge['scrambled']}\n\n"
        f"💡 Hint: {challenge['category']}\n\n"
        f"{score_text(context)}\n\n"
        "Choose the correct answer."
    )


# ==========================================================
# GAME KEYBOARD
# ==========================================================

def game_keyboard(challenge):

    buttons = []

    labels = [
        "A️⃣",
        "B️⃣",
        "C️⃣",
        "D️⃣",
    ]

    for index, label in enumerate(labels):

        if index >= len(
            challenge["answers"]
        ):
            break

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{label} {challenge['answers'][index]}",
                    callback_data=f"scramble_answer_{index}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "😈 PASS",
                callback_data="scramble_pass",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                "➡️ Next",
                callback_data="scramble_next",
            ),
            InlineKeyboardButton(
                "🔄 Categories",
                callback_data="scramble_category_menu",
            ),
        ]
    )

    return InlineKeyboardMarkup(buttons)


# ==========================================================
# /SCRAMBLE
# ==========================================================

async def word_scramble(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not WORD_SCRAMBLE_ENABLED:

        await message.reply_text(
            "🔤 Word Scramble is currently disabled."
        )

        return

    initialize_score(context)

    await message.reply_text(
        "🔤 WORD SCRAMBLE\n\n"
        "Unscramble words and test your knowledge!\n\n"
        "Choose a category:",
        reply_markup=category_keyboard(),
    )


# ==========================================================
# START CHALLENGE
# ==========================================================

async def start_challenge(
    query,
    context,
):

    challenge = get_challenge(context)

    await query.edit_message_text(
        format_challenge(
            challenge,
            context,
        ),
        reply_markup=game_keyboard(
            challenge
        ),
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

    if not WORD_SCRAMBLE_ENABLED:

        await query.answer(
            "Word Scramble is disabled.",
            show_alert=True,
        )

        return

    initialize_score(context)

    # ======================================================
    # CATEGORY MENU
    # ======================================================

    if data == "scramble_category_menu":

        await query.edit_message_text(
            "🔤 WORD SCRAMBLE\n\n"
            "Choose a category:",
            reply_markup=category_keyboard(),
        )

        return

    # ======================================================
    # DIFFICULTY MENU
    # ======================================================

    if data == "scramble_difficulty_menu":

        await query.edit_message_text(
            "🎯 CHOOSE DIFFICULTY\n\n"
            "🟢 Easy\n"
            "🟡 Medium\n"
            "🔴 Hard",
            reply_markup=difficulty_keyboard(),
        )

        return

    # ======================================================
    # CATEGORY SELECTION
    # ======================================================

    if data.startswith(
        "scramble_category_"
    ):

        category = data.replace(
            "scramble_category_",
            "",
            1,
        )

        if category not in WORDS:
            category = "general"

        context.user_data[
            "scramble_category"
        ] = category

        await start_challenge(
            query,
            context,
        )

        return

    # ======================================================
    # DIFFICULTY SELECTION
    # ======================================================

    if data.startswith(
        "scramble_difficulty_"
    ):

        difficulty = data.replace(
            "scramble_difficulty_",
            "",
            1,
        )

        if difficulty not in VALID_DIFFICULTIES:
            difficulty = "easy"

        context.user_data[
            "scramble_difficulty"
        ] = difficulty

        await start_challenge(
            query,
            context,
        )

        return

    # ======================================================
    # ANSWER
    # ======================================================

    if data.startswith(
        "scramble_answer_"
    ):

        if context.user_data.get(
            "scramble_answered",
            False,
        ):

            await query.answer(
                "You already answered this word.",
                show_alert=True,
            )

            return

        try:

            selected = int(
                data.replace(
                    "scramble_answer_",
                    "",
                    1,
                )
            )

        except ValueError:

            return

        challenge = context.user_data.get(
            "scramble_current"
        )

        if not challenge:

            await query.answer(
                "Please start a new challenge.",
                show_alert=True,
            )

            return

        answers = challenge["answers"]

        if selected < 0 or selected >= len(
            answers
        ):

            await query.answer(
                "Invalid answer.",
                show_alert=True,
            )

            return

        context.user_data[
            "scramble_answered"
        ] = True

        context.user_data[
            "scramble_questions"
        ] += 1

        correct = challenge["correct"]

        if selected == correct:

            context.user_data[
                "scramble_score"
            ] += 1

            context.user_data[
                "scramble_streak"
            ] += 1

            await query.answer(
                "🎉 CORRECT!",
                show_alert=True,
            )

            result = (
                "🎉 CORRECT!\n\n"
                f"👉 {challenge['word']}\n\n"
                f"{score_text(context)}"
            )

        else:

            context.user_data[
                "scramble_streak"
            ] = 0

            await query.answer(
                "❌ Not quite!",
                show_alert=True,
            )

            result = (
                "❌ NOT QUITE!\n\n"
                f"The word was:\n"
                f"👉 {challenge['word']}\n\n"
                f"{score_text(context)}"
            )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➡️ Next Challenge",
                        callback_data="scramble_next",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Categories",
                        callback_data="scramble_category_menu",
                    ),
                ],
            ]
        )

        await query.edit_message_text(
            result,
            reply_markup=keyboard,
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "scramble_pass":

        if context.user_data.get(
            "scramble_answered",
            False,
        ):

            await query.answer(
                "This challenge is already finished.",
                show_alert=True,
            )

            return

        context.user_data[
            "scramble_answered"
        ] = True

        context.user_data[
            "scramble_questions"
        ] += 1

        context.user_data[
            "scramble_streak"
        ] = 0

        challenge = context.user_data.get(
            "scramble_current"
        )

        if challenge:

            text = (
                "😈 PASS ACCEPTED\n\n"
                f"The word was:\n"
                f"👉 {challenge['word']}\n\n"
                f"{score_text(context)}"
            )

        else:

            text = (
                "😈 PASS ACCEPTED\n\n"
                f"{score_text(context)}"
            )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➡️ Next Challenge",
                        callback_data="scramble_next",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Categories",
                        callback_data="scramble_category_menu",
                    ),
                ],
            ]
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
        )

        return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "scramble_next":

        await start_challenge(
            query,
            context,
        )

        return


# ==========================================================
# RESET SCORE
# ==========================================================

def reset_score(context):

    context.user_data[
        "scramble_score"
    ] = 0

    context.user_data[
        "scramble_streak"
    ] = 0

    context.user_data[
        "scramble_questions"
    ] = 0

    context.user_data[
        "scramble_answered"
    ] = False


# ==========================================================
# END word_scramble.py
# ==========================================================
