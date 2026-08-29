# ==========================================================
# Melanated AZ Bot
# games/trivia.py
#
# TRIVIA
#
# Features:
#   - Button-based trivia
#   - Multiple categories
#   - Easy / Medium / Hard
#   - Random questions
#   - Answer buttons
#   - Score tracking
#   - Streak tracking
#   - PASS allowed
#   - Next question
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

TRIVIA_ENABLED = True

VALID_DIFFICULTIES = (
    "easy",
    "medium",
    "hard",
)


# ==========================================================
# QUESTIONS
#
# Each question:
#
# {
#     "question": "...",
#     "answers": ["A", "B", "C", "D"],
#     "correct": 0,
# }
#
# correct is the zero-based answer index.
# ==========================================================

TRIVIA_QUESTIONS = {

    "general": {

        "easy": [

            {
                "question": "What planet do we live on?",
                "answers": [
                    "Mars",
                    "Earth",
                    "Venus",
                    "Jupiter",
                ],
                "correct": 1,
            },

            {
                "question": "How many days are in a week?",
                "answers": [
                    "5",
                    "6",
                    "7",
                    "8",
                ],
                "correct": 2,
            },

            {
                "question": "What color do you get by mixing red and white?",
                "answers": [
                    "Purple",
                    "Pink",
                    "Green",
                    "Orange",
                ],
                "correct": 1,
            },

            {
                "question": "How many sides does a triangle have?",
                "answers": [
                    "2",
                    "3",
                    "4",
                    "5",
                ],
                "correct": 1,
            },

            {
                "question": "Which animal is known as man's best friend?",
                "answers": [
                    "Cat",
                    "Horse",
                    "Dog",
                    "Rabbit",
                ],
                "correct": 2,
            },

        ],

        "medium": [

            {
                "question": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Pacific",
                    "Arctic",
                ],
                "correct": 2,
            },

            {
                "question": "Which continent is the largest by area?",
                "answers": [
                    "Africa",
                    "Asia",
                    "Europe",
                    "North America",
                ],
                "correct": 1,
            },

            {
                "question": "How many bones are typically found in an adult human body?",
                "answers": [
                    "186",
                    "206",
                    "226",
                    "246",
                ],
                "correct": 1,
            },

            {
                "question": "Which gas makes up most of Earth's atmosphere?",
                "answers": [
                    "Oxygen",
                    "Carbon dioxide",
                    "Nitrogen",
                    "Hydrogen",
                ],
                "correct": 2,
            },

            {
                "question": "Which instrument has 88 keys?",
                "answers": [
                    "Guitar",
                    "Piano",
                    "Violin",
                    "Trumpet",
                ],
                "correct": 1,
            },

        ],

        "hard": [

            {
                "question": "What is the smallest prime number greater than 50?",
                "answers": [
                    "51",
                    "53",
                    "57",
                    "59",
                ],
                "correct": 1,
            },

            {
                "question": "Which element has the chemical symbol W?",
                "answers": [
                    "Tungsten",
                    "Titanium",
                    "Tin",
                    "Tantalum",
                ],
                "correct": 0,
            },

            {
                "question": "What is the capital of Mongolia?",
                "answers": [
                    "Astana",
                    "Ulaanbaatar",
                    "Tashkent",
                    "Bishkek",
                ],
                "correct": 1,
            },

            {
                "question": "Which scientist formulated the three laws of motion?",
                "answers": [
                    "Albert Einstein",
                    "Galileo Galilei",
                    "Isaac Newton",
                    "Nikola Tesla",
                ],
                "correct": 2,
            },

            {
                "question": "What is the hardest natural substance?",
                "answers": [
                    "Quartz",
                    "Diamond",
                    "Granite",
                    "Titanium",
                ],
                "correct": 1,
            },

        ],
    },

    # ======================================================
    # MUSIC
    # ======================================================

    "music": {

        "easy": [

            {
                "question": "Which instrument commonly has six strings?",
                "answers": [
                    "Guitar",
                    "Piano",
                    "Trumpet",
                    "Drums",
                ],
                "correct": 0,
            },

            {
                "question": "Which genre is strongly associated with DJs and turntables?",
                "answers": [
                    "Hip-hop",
                    "Classical",
                    "Opera",
                    "Bluegrass",
                ],
                "correct": 0,
            },

            {
                "question": "How many strings does a standard violin have?",
                "answers": [
                    "3",
                    "4",
                    "5",
                    "6",
                ],
                "correct": 1,
            },

            {
                "question": "Which instrument is typically played with drumsticks?",
                "answers": [
                    "Drums",
                    "Flute",
                    "Violin",
                    "Saxophone",
                ],
                "correct": 0,
            },

        ],

        "medium": [

            {
                "question": "Which city is widely associated with the birth of jazz?",
                "answers": [
                    "New Orleans",
                    "Seattle",
                    "Denver",
                    "Phoenix",
                ],
                "correct": 0,
            },

            {
                "question": "Which musical symbol indicates silence?",
                "answers": [
                    "Clef",
                    "Rest",
                    "Sharp",
                    "Flat",
                ],
                "correct": 1,
            },

            {
                "question": "Which singer was nicknamed the Queen of Soul?",
                "answers": [
                    "Aretha Franklin",
                    "Whitney Houston",
                    "Diana Ross",
                    "Tina Turner",
                ],
                "correct": 0,
            },

            {
                "question": "Which instrument belongs to the brass family?",
                "answers": [
                    "Clarinet",
                    "Trumpet",
                    "Violin",
                    "Harp",
                ],
                "correct": 1,
            },

        ],

        "hard": [

            {
                "question": "Which composer wrote The Four Seasons?",
                "answers": [
                    "Mozart",
                    "Vivaldi",
                    "Bach",
                    "Beethoven",
                ],
                "correct": 1,
            },

            {
                "question": "Which musical term means gradually becoming louder?",
                "answers": [
                    "Diminuendo",
                    "Crescendo",
                    "Staccato",
                    "Legato",
                ],
                "correct": 1,
            },

            {
                "question": "Which key contains no sharps or flats?",
                "answers": [
                    "C major",
                    "D major",
                    "G major",
                    "A major",
                ],
                "correct": 0,
            },

        ],
    },

    # ======================================================
    # MOVIES
    # ======================================================

    "movies": {

        "easy": [

            {
                "question": "Which fictional superhero is known as the Dark Knight?",
                "answers": [
                    "Superman",
                    "Batman",
                    "Flash",
                    "Aquaman",
                ],
                "correct": 1,
            },

            {
                "question": "Which movie features a character named Simba?",
                "answers": [
                    "Frozen",
                    "The Lion King",
                    "Toy Story",
                    "Shrek",
                ],
                "correct": 1,
            },

            {
                "question": "What type of creature is Shrek?",
                "answers": [
                    "Dragon",
                    "Ogre",
                    "Wizard",
                    "Troll",
                ],
                "correct": 1,
            },

            {
                "question": "Which superhero carries a shield with a star?",
                "answers": [
                    "Thor",
                    "Hulk",
                    "Captain America",
                    "Iron Man",
                ],
                "correct": 2,
            },

        ],

        "medium": [

            {
                "question": "Which movie features the character Jack Sparrow?",
                "answers": [
                    "Pirates of the Caribbean",
                    "The Mummy",
                    "Indiana Jones",
                    "Jumanji",
                ],
                "correct": 0,
            },

            {
                "question": "Who directed Jurassic Park?",
                "answers": [
                    "James Cameron",
                    "Steven Spielberg",
                    "Christopher Nolan",
                    "George Lucas",
                ],
                "correct": 1,
            },

            {
                "question": "Which movie series features the fictional world of Wakanda?",
                "answers": [
                    "Star Wars",
                    "Marvel",
                    "Fast & Furious",
                    "Transformers",
                ],
                "correct": 1,
            },

            {
                "question": "Which actor played Forrest Gump?",
                "answers": [
                    "Tom Hanks",
                    "Denzel Washington",
                    "Morgan Freeman",
                    "Robin Williams",
                ],
                "correct": 0,
            },

        ],

        "hard": [

            {
                "question": "Which film won the Academy Award for Best Picture in 1994?",
                "answers": [
                    "Pulp Fiction",
                    "Forrest Gump",
                    "The Shawshank Redemption",
                    "Speed",
                ],
                "correct": 1,
            },

            {
                "question": "Who directed Pulp Fiction?",
                "answers": [
                    "Quentin Tarantino",
                    "Martin Scorsese",
                    "Francis Ford Coppola",
                    "Spike Lee",
                ],
                "correct": 0,
            },

            {
                "question": "Which actor portrayed T'Challa in Black Panther?",
                "answers": [
                    "Idris Elba",
                    "Michael B. Jordan",
                    "Chadwick Boseman",
                    "Wesley Snipes",
                ],
                "correct": 2,
            },

        ],
    },

    # ======================================================
    # BLACK HISTORY & CULTURE
    # ======================================================

    "black_history": {

        "easy": [

            {
                "question": "Who delivered the famous 'I Have a Dream' speech?",
                "answers": [
                    "Malcolm X",
                    "Martin Luther King Jr.",
                    "Frederick Douglass",
                    "James Baldwin",
                ],
                "correct": 1,
            },

            {
                "question": "Who was the first Black president of the United States?",
                "answers": [
                    "Barack Obama",
                    "Colin Powell",
                    "Jesse Jackson",
                    "Thurgood Marshall",
                ],
                "correct": 0,
            },

            {
                "question": "Which holiday celebrates the end of slavery in the United States?",
                "answers": [
                    "Juneteenth",
                    "Memorial Day",
                    "Labor Day",
                    "Veterans Day",
                ],
                "correct": 0,
            },

            {
                "question": "Who is famous for refusing to give up her bus seat in Montgomery?",
                "answers": [
                    "Rosa Parks",
                    "Harriet Tubman",
                    "Ella Baker",
                    "Ida B. Wells",
                ],
                "correct": 0,
            },

        ],

        "medium": [

            {
                "question": "Who founded the NAACP with other activists?",
                "answers": [
                    "W. E. B. Du Bois",
                    "Booker T. Washington",
                    "Marcus Garvey",
                    "George Washington Carver",
                ],
                "correct": 0,
            },

            {
                "question": "Who founded the Universal Negro Improvement Association?",
                "answers": [
                    "Marcus Garvey",
                    "Martin Luther King Jr.",
                    "James Baldwin",
                    "Adam Clayton Powell Jr.",
                ],
                "correct": 0,
            },

            {
                "question": "Who was the first African American woman in space?",
                "answers": [
                    "Mae Jemison",
                    "Katherine Johnson",
                    "Dorothy Vaughan",
                    "Mary Jackson",
                ],
                "correct": 0,
            },

            {
                "question": "Which inventor became famous for improving the practical incandescent light bulb?",
                "answers": [
                    "Lewis Latimer",
                    "Alexander Graham Bell",
                    "Thomas Edison",
                    "Nikola Tesla",
                ],
                "correct": 0,
            },

        ],

        "hard": [

            {
                "question": "Who was the first African American Supreme Court justice?",
                "answers": [
                    "Thurgood Marshall",
                    "Clarence Thomas",
                    "Charles Hamilton Houston",
                    "Constance Baker Motley",
                ],
                "correct": 0,
            },

            {
                "question": "Which scholar wrote The Souls of Black Folk?",
                "answers": [
                    "W. E. B. Du Bois",
                    "Booker T. Washington",
                    "James Baldwin",
                    "Richard Wright",
                ],
                "correct": 0,
            },

            {
                "question": "Which organization was founded in 1909 to advance civil rights?",
                "answers": [
                    "NAACP",
                    "SCLC",
                    "SNCC",
                    "CORE",
                ],
                "correct": 0,
            },

        ],
    },

    # ======================================================
    # SPORTS
    # ======================================================

    "sports": {

        "easy": [

            {
                "question": "How many points is a touchdown worth in American football before the extra point?",
                "answers": [
                    "3",
                    "6",
                    "7",
                    "8",
                ],
                "correct": 1,
            },

            {
                "question": "How many players are on the court for one basketball team during normal play?",
                "answers": [
                    "4",
                    "5",
                    "6",
                    "7",
                ],
                "correct": 1,
            },

            {
                "question": "Which sport uses a bat and ball?",
                "answers": [
                    "Basketball",
                    "Baseball",
                    "Swimming",
                    "Boxing",
                ],
                "correct": 1,
            },

            {
                "question": "How many bases are on a standard baseball diamond?",
                "answers": [
                    "3",
                    "4",
                    "5",
                    "6",
                ],
                "correct": 1,
            },

        ],

        "medium": [

            {
                "question": "How many yards is a football field excluding the end zones?",
                "answers": [
                    "90",
                    "100",
                    "110",
                    "120",
                ],
                "correct": 1,
            },

            {
                "question": "How many periods are in a standard NHL hockey game?",
                "answers": [
                    "2",
                    "3",
                    "4",
                    "5",
                ],
                "correct": 1,
            },

            {
                "question": "In tennis, what score comes after 30?",
                "answers": [
                    "35",
                    "40",
                    "45",
                    "50",
                ],
                "correct": 1,
            },

            {
                "question": "How many players are on a baseball team in the field?",
                "answers": [
                    "7",
                    "8",
                    "9",
                    "10",
                ],
                "correct": 2,
            },

        ],

        "hard": [

            {
                "question": "How many minutes are in a regulation NBA game?",
                "answers": [
                    "40",
                    "48",
                    "50",
                    "60",
                ],
                "correct": 1,
            },

            {
                "question": "How many outs are recorded for each team during a complete half-inning?",
                "answers": [
                    "2",
                    "3",
                    "4",
                    "6",
                ],
                "correct": 1,
            },

            {
                "question": "How many points is a safety worth in American football?",
                "answers": [
                    "1",
                    "2",
                    "3",
                    "6",
                ],
                "correct": 1,
            },

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
}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():

    return TRIVIA_ENABLED


# ==========================================================
# GET CATEGORY
# ==========================================================

def get_category(context):

    category = context.user_data.get(
        "trivia_category",
        "general",
    )

    if category not in TRIVIA_QUESTIONS:

        category = "general"

    return category


# ==========================================================
# GET DIFFICULTY
# ==========================================================

def get_difficulty(context):

    difficulty = context.user_data.get(
        "trivia_difficulty",
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
                    callback_data="trivia_category_general",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["music"],
                    callback_data="trivia_category_music",
                ),
                InlineKeyboardButton(
                    CATEGORY_NAMES["movies"],
                    callback_data="trivia_category_movies",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["black_history"],
                    callback_data="trivia_category_black_history",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["sports"],
                    callback_data="trivia_category_sports",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎯 Change Difficulty",
                    callback_data="trivia_difficulty_menu",
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
                    callback_data="trivia_difficulty_easy",
                ),
                InlineKeyboardButton(
                    "🟡 Medium",
                    callback_data="trivia_difficulty_medium",
                ),
                InlineKeyboardButton(
                    "🔴 Hard",
                    callback_data="trivia_difficulty_hard",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 Categories",
                    callback_data="trivia_category_menu",
                ),
            ],
        ]
    )


# ==========================================================
# GAME KEYBOARD
# ==========================================================

def game_keyboard(question):

    buttons = []

    labels = [
        "A️⃣",
        "B️⃣",
        "C️⃣",
        "D️⃣",
    ]

    for index, label in enumerate(labels):

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{label} {question['answers'][index]}",
                    callback_data=f"trivia_answer_{index}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "😈 PASS",
                callback_data="trivia_pass",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                "➡️ Next",
                callback_data="trivia_next",
            ),
            InlineKeyboardButton(
                "🔄 Categories",
                callback_data="trivia_category_menu",
            ),
        ]
    )

    return InlineKeyboardMarkup(buttons)


# ==========================================================
# GET RANDOM QUESTION
# ==========================================================

def get_question(context):

    category = get_category(context)
    difficulty = get_difficulty(context)

    questions = TRIVIA_QUESTIONS.get(
        category,
        {},
    ).get(
        difficulty,
        [],
    )

    if not questions:

        category = "general"
        difficulty = "easy"

        context.user_data[
            "trivia_category"
        ] = category

        context.user_data[
            "trivia_difficulty"
        ] = difficulty

        questions = TRIVIA_QUESTIONS[
            category
        ][difficulty]

    question = random.choice(questions)

    context.user_data[
        "trivia_current_question"
    ] = question

    context.user_data[
        "trivia_answered"
    ] = False

    return question


# ==========================================================
# INITIALIZE SCORE
# ==========================================================

def initialize_score(context):

    if "trivia_score" not in context.user_data:

        context.user_data[
            "trivia_score"
        ] = 0

    if "trivia_streak" not in context.user_data:

        context.user_data[
            "trivia_streak"
        ] = 0

    if "trivia_questions" not in context.user_data:

        context.user_data[
            "trivia_questions"
        ] = 0


# ==========================================================
# SCORE TEXT
# ==========================================================

def score_text(context):

    initialize_score(context)

    score = context.user_data.get(
        "trivia_score",
        0,
    )

    streak = context.user_data.get(
        "trivia_streak",
        0,
    )

    questions = context.user_data.get(
        "trivia_questions",
        0,
    )

    return (
        f"🏆 Score: {score}\n"
        f"🔥 Streak: {streak}\n"
        f"❓ Questions: {questions}"
    )


# ==========================================================
# FORMAT QUESTION
# ==========================================================

def format_question(
    question,
    context,
):

    category = get_category(context)
    difficulty = get_difficulty(context)

    return (
        "🧠 TRIVIA\n\n"
        f"📚 Category: {CATEGORY_NAMES.get(category, category)}\n"
        f"🎯 Difficulty: {difficulty.upper()}\n\n"
        f"{question['question']}\n\n"
        f"{score_text(context)}\n\n"
        "Choose your answer."
    )


# ==========================================================
# /TRIVIA
# ==========================================================

async def trivia(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not TRIVIA_ENABLED:

        await message.reply_text(
            "🧠 Trivia is currently disabled."
        )

        return

    initialize_score(context)

    await message.reply_text(
        "🧠 TRIVIA\n\n"
        "Choose a category:",
        reply_markup=category_keyboard(),
    )


# ==========================================================
# START QUESTION
# ==========================================================

async def start_question(
    query,
    context,
):

    question = get_question(context)

    await query.edit_message_text(
        format_question(
            question,
            context,
        ),
        reply_markup=game_keyboard(
            question
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

    if not TRIVIA_ENABLED:

        await query.answer(
            "Trivia is disabled.",
            show_alert=True,
        )

        return

    initialize_score(context)

    # ======================================================
    # CATEGORY MENU
    # ======================================================

    if data == "trivia_category_menu":

        await query.edit_message_text(
            "🧠 TRIVIA\n\n"
            "Choose a category:",
            reply_markup=category_keyboard(),
        )

        return

    # ======================================================
    # DIFFICULTY MENU
    # ======================================================

    if data == "trivia_difficulty_menu":

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

    if data.startswith("trivia_category_"):

        category = data.replace(
            "trivia_category_",
            "",
            1,
        )

        if category not in TRIVIA_QUESTIONS:

            category = "general"

        context.user_data[
            "trivia_category"
        ] = category

        await start_question(
            query,
            context,
        )

        return

    # ======================================================
    # DIFFICULTY SELECTION
    # ======================================================

    if data.startswith("trivia_difficulty_"):

        difficulty = data.replace(
            "trivia_difficulty_",
            "",
            1,
        )

        if difficulty not in VALID_DIFFICULTIES:

            difficulty = "easy"

        context.user_data[
            "trivia_difficulty"
        ] = difficulty

        await start_question(
            query,
            context,
        )

        return

    # ======================================================
    # ANSWER
    # ======================================================

    if data.startswith("trivia_answer_"):

        if context.user_data.get(
            "trivia_answered",
            False,
        ):

            await query.answer(
                "You already answered this question.",
                show_alert=True,
            )

            return

        try:

            selected = int(
                data.replace(
                    "trivia_answer_",
                    "",
                    1,
                )
            )

        except ValueError:

            return

        question = context.user_data.get(
            "trivia_current_question"
        )

        if not question:

            await query.answer(
                "Please start a new question.",
                show_alert=True,
            )

            return

        context.user_data[
            "trivia_answered"
        ] = True

        context.user_data[
            "trivia_questions"
        ] += 1

        correct = question["correct"]

        if selected == correct:

            context.user_data[
                "trivia_score"
            ] += 1

            context.user_data[
                "trivia_streak"
            ] += 1

            await query.answer(
                "🎉 CORRECT!",
                show_alert=True,
            )

            result = (
                "🎉 CORRECT!\n\n"
                f"The answer was:\n"
                f"👉 {question['answers'][correct]}\n\n"
                f"{score_text(context)}"
            )

        else:

            context.user_data[
                "trivia_streak"
            ] = 0

            await query.answer(
                "❌ Not quite!",
                show_alert=True,
            )

            result = (
                "❌ NOT QUITE!\n\n"
                f"The correct answer was:\n"
                f"👉 {question['answers'][correct]}\n\n"
                f"{score_text(context)}"
            )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➡️ Next Question",
                        callback_data="trivia_next",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Categories",
                        callback_data="trivia_category_menu",
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

    if data == "trivia_pass":

        if context.user_data.get(
            "trivia_answered",
            False,
        ):

            await query.answer(
                "This question is already finished.",
                show_alert=True,
            )

            return

        context.user_data[
            "trivia_answered"
        ] = True

        context.user_data[
            "trivia_questions"
        ] += 1

        context.user_data[
            "trivia_streak"
        ] = 0

        question = context.user_data.get(
            "trivia_current_question"
        )

        if question:

            correct = question["correct"]

            text = (
                "😈 PASS ACCEPTED\n\n"
                f"The answer was:\n"
                f"👉 {question['answers'][correct]}\n\n"
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
                        "➡️ Next Question",
                        callback_data="trivia_next",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Categories",
                        callback_data="trivia_category_menu",
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

    if data == "trivia_next":

        await start_question(
            query,
            context,
        )

        return


# ==========================================================
# RESET PLAYER SCORE
# ==========================================================

def reset_score(context):

    context.user_data[
        "trivia_score"
    ] = 0

    context.user_data[
        "trivia_streak"
    ] = 0

    context.user_data[
        "trivia_questions"
    ] = 0

    context.user_data[
        "trivia_answered"
    ] = False


# ==========================================================
# END trivia.py
# ==========================================================
