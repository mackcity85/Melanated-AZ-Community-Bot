# ==========================================================
# Melanated AZ Bot
# games/game_engine.py
#
# SHARED GAME ENGINE
#
# Used by:
#   - Trivia
#   - Would You Rather
#   - Truth or Dare
#   - Never Have I Ever
#   - Most Likely To
#   - This or That
#   - Hot Seat
#   - Guessing Games
#   - Word Games
#   - Party Games
#
# This file contains reusable game/session utilities.
#
# IMPORTANT:
# This file does NOT import from games.py.
# This prevents circular imports.
# ==========================================================

import logging
import random

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


logger = logging.getLogger(__name__)


# ==========================================================
# CONSTANTS
# ==========================================================

GAME_HOME_CALLBACK = "games_home"
GAME_MENU_CALLBACK = "games_menu"

PASS_CALLBACK = "game_pass"
NEXT_CALLBACK = "game_next"


# ==========================================================
# PLAYER SESSION HELPERS
# ==========================================================

def initialize_player(context):
    """
    Initialize common game statistics for a player.
    """

    defaults = {
        "games_played": 0,
        "games_won": 0,
        "games_score": 0,
        "games_streak": 0,
        "games_best_streak": 0,
        "games_passes": 0,
    }

    for key, value in defaults.items():

        if key not in context.user_data:

            context.user_data[key] = value


# ==========================================================
# GET PLAYER STAT
# ==========================================================

def get_player_stat(
    context,
    stat,
    default=0,
):
    """
    Safely retrieve a player statistic.
    """

    initialize_player(context)

    return context.user_data.get(
        stat,
        default,
    )


# ==========================================================
# ADD SCORE
# ==========================================================

def add_score(
    context,
    points=1,
):
    """
    Add points to the player's score.
    """

    initialize_player(context)

    try:

        points = int(points)

    except (TypeError, ValueError):

        points = 0

    context.user_data[
        "games_score"
    ] += points

    return context.user_data[
        "games_score"
    ]


# ==========================================================
# CORRECT ANSWER
# ==========================================================

def record_correct(
    context,
    points=1,
):
    """
    Record a correct answer.

    Updates:
        score
        games played
        wins
        current streak
        best streak
    """

    initialize_player(context)

    context.user_data[
        "games_played"
    ] += 1

    context.user_data[
        "games_won"
    ] += 1

    add_score(
        context,
        points,
    )

    context.user_data[
        "games_streak"
    ] += 1

    current_streak = context.user_data[
        "games_streak"
    ]

    best_streak = context.user_data.get(
        "games_best_streak",
        0,
    )

    if current_streak > best_streak:

        context.user_data[
            "games_best_streak"
        ] = current_streak

    return {
        "score": context.user_data["games_score"],
        "streak": context.user_data["games_streak"],
        "best_streak": context.user_data["games_best_streak"],
    }


# ==========================================================
# INCORRECT ANSWER
# ==========================================================

def record_incorrect(context):
    """
    Record an incorrect answer.

    Resets the current streak.
    """

    initialize_player(context)

    context.user_data[
        "games_played"
    ] += 1

    context.user_data[
        "games_streak"
    ] = 0

    return {
        "score": context.user_data["games_score"],
        "streak": 0,
        "best_streak": context.user_data["games_best_streak"],
    }


# ==========================================================
# PASS
# ==========================================================

def record_pass(context):
    """
    Record a PASS.

    PASS never counts as a loss.
    It does end the current streak.
    """

    initialize_player(context)

    context.user_data[
        "games_passes"
    ] += 1

    context.user_data[
        "games_streak"
    ] = 0

    return {
        "score": context.user_data["games_score"],
        "streak": 0,
        "passes": context.user_data["games_passes"],
    }


# ==========================================================
# START GAME
# ==========================================================

def start_game(
    context,
    game_name,
):
    """
    Start a new game session.
    """

    initialize_player(context)

    context.user_data[
        "current_game"
    ] = game_name

    context.user_data[
        "game_active"
    ] = True

    context.user_data[
        "game_answered"
    ] = False

    context.user_data[
        "game_current_item"
    ] = None

    return True


# ==========================================================
# END GAME
# ==========================================================

def end_game(context):
    """
    End the current game session.
    """

    context.user_data[
        "game_active"
    ] = False

    context.user_data[
        "game_answered"
    ] = False

    context.user_data[
        "game_current_item"
    ] = None


# ==========================================================
# CURRENT GAME
# ==========================================================

def get_current_game(context):

    return context.user_data.get(
        "current_game"
    )


# ==========================================================
# ACTIVE GAME
# ==========================================================

def is_game_active(context):

    return bool(
        context.user_data.get(
            "game_active",
            False,
        )
    )


# ==========================================================
# ANSWERED STATUS
# ==========================================================

def is_answered(context):

    return bool(
        context.user_data.get(
            "game_answered",
            False,
        )
    )


# ==========================================================
# MARK ANSWERED
# ==========================================================

def mark_answered(context):

    context.user_data[
        "game_answered"
    ] = True


# ==========================================================
# CURRENT ITEM
# ==========================================================

def set_current_item(
    context,
    item,
):
    context.user_data[
        "game_current_item"
    ] = item


def get_current_item(context):

    return context.user_data.get(
        "game_current_item"
    )


# ==========================================================
# RANDOM ITEM
# ==========================================================

def random_item(items):

    if not items:

        return None

    return random.choice(items)


# ==========================================================
# RANDOM ITEM WITHOUT IMMEDIATE DUPLICATE
# ==========================================================

def random_item_no_repeat(
    context,
    items,
    storage_key="game_previous_item",
):
    """
    Select a random item while avoiding
    the immediately previous item when possible.
    """

    if not items:

        return None

    if len(items) == 1:

        selected = items[0]

        context.user_data[
            storage_key
        ] = selected

        return selected

    previous = context.user_data.get(
        storage_key
    )

    available = [
        item
        for item in items
        if item != previous
    ]

    if not available:

        available = items

    selected = random.choice(
        available
    )

    context.user_data[
        storage_key
    ] = selected

    return selected


# ==========================================================
# SCORE DISPLAY
# ==========================================================

def score_text(context):

    initialize_player(context)

    score = context.user_data.get(
        "games_score",
        0,
    )

    streak = context.user_data.get(
        "games_streak",
        0,
    )

    best = context.user_data.get(
        "games_best_streak",
        0,
    )

    played = context.user_data.get(
        "games_played",
        0,
    )

    return (
        f"🏆 Score: {score}\n"
        f"🔥 Streak: {streak}\n"
        f"⭐ Best Streak: {best}\n"
        f"🎮 Played: {played}"
    )


# ==========================================================
# PLAYER STATS TEXT
# ==========================================================

def player_stats_text(context):

    initialize_player(context)

    played = context.user_data.get(
        "games_played",
        0,
    )

    wins = context.user_data.get(
        "games_won",
        0,
    )

    score = context.user_data.get(
        "games_score",
        0,
    )

    streak = context.user_data.get(
        "games_streak",
        0,
    )

    best = context.user_data.get(
        "games_best_streak",
        0,
    )

    passes = context.user_data.get(
        "games_passes",
        0,
    )

    if played > 0:

        win_rate = round(
            (wins / played) * 100
        )

    else:

        win_rate = 0

    return (
        "🏆 YOUR GAME STATS\n\n"
        f"🎮 Games Played: {played}\n"
        f"🏅 Wins: {wins}\n"
        f"📊 Win Rate: {win_rate}%\n"
        f"⭐ Score: {score}\n"
        f"🔥 Current Streak: {streak}\n"
        f"💥 Best Streak: {best}\n"
        f"😈 Passes: {passes}"
    )


# ==========================================================
# RESET STATS
# ==========================================================

def reset_player_stats(context):

    context.user_data[
        "games_played"
    ] = 0

    context.user_data[
        "games_won"
    ] = 0

    context.user_data[
        "games_score"
    ] = 0

    context.user_data[
        "games_streak"
    ] = 0

    context.user_data[
        "games_best_streak"
    ] = 0

    context.user_data[
        "games_passes"
    ] = 0


# ==========================================================
# STANDARD GAME BUTTONS
# ==========================================================

def standard_game_buttons(
    include_pass=True,
    include_next=True,
    include_home=True,
):
    """
    Build a reusable game button layout.
    """

    buttons = []

    if include_pass:

        buttons.append(
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data=PASS_CALLBACK,
                )
            ]
        )

    navigation = []

    if include_next:

        navigation.append(
            InlineKeyboardButton(
                "➡️ Next",
                callback_data=NEXT_CALLBACK,
            )
        )

    if include_home:

        navigation.append(
            InlineKeyboardButton(
                "🎮 Games",
                callback_data=GAME_HOME_CALLBACK,
            )
        )

    if navigation:

        buttons.append(
            navigation
        )

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================================
# ANSWER BUTTONS
# ==========================================================

def answer_keyboard(
    answers,
    prefix="game_answer",
    include_pass=True,
):
    """
    Create answer buttons.

    Example:

        A️⃣ Answer One
        B️⃣ Answer Two
        C️⃣ Answer Three
        D️⃣ Answer Four
    """

    labels = [
        "A️⃣",
        "B️⃣",
        "C️⃣",
        "D️⃣",
    ]

    buttons = []

    for index, answer in enumerate(
        answers
    ):

        if index >= len(labels):

            break

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{labels[index]} {answer}",
                    callback_data=(
                        f"{prefix}_{index}"
                    ),
                )
            ]
        )

    if include_pass:

        buttons.append(
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data=PASS_CALLBACK,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🎮 Games",
                callback_data=GAME_HOME_CALLBACK,
            )
        ]
    )

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================================
# YES / NO BUTTONS
# ==========================================================

def yes_no_keyboard(
    yes_callback,
    no_callback,
    include_pass=True,
):

    buttons = [
        [
            InlineKeyboardButton(
                "✅ YES",
                callback_data=yes_callback,
            ),
            InlineKeyboardButton(
                "❌ NO",
                callback_data=no_callback,
            ),
        ],
    ]

    if include_pass:

        buttons.append(
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data=PASS_CALLBACK,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🎮 Games",
                callback_data=GAME_HOME_CALLBACK,
            )
        ]
    )

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================================
# CHOICE KEYBOARD
# ==========================================================

def choice_keyboard(
    choices,
    prefix="game_choice",
    include_pass=True,
):
    """
    Generic button generator for games
    with multiple choices.
    """

    buttons = []

    for index, choice in enumerate(
        choices
    ):

        buttons.append(
            [
                InlineKeyboardButton(
                    str(choice),
                    callback_data=(
                        f"{prefix}_{index}"
                    ),
                )
            ]
        )

    if include_pass:

        buttons.append(
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data=PASS_CALLBACK,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🎮 Games",
                callback_data=GAME_HOME_CALLBACK,
            )
        ]
    )

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================================
# GAME MENU BUTTON
# ==========================================================

def games_button():

    return InlineKeyboardButton(
        "🎮 Games",
        callback_data=GAME_HOME_CALLBACK,
    )


# ==========================================================
# NEXT BUTTON
# ==========================================================

def next_button():

    return InlineKeyboardButton(
        "➡️ Next",
        callback_data=NEXT_CALLBACK,
    )


# ==========================================================
# PASS BUTTON
# ==========================================================

def pass_button():

    return InlineKeyboardButton(
        "😈 PASS",
        callback_data=PASS_CALLBACK,
    )


# ==========================================================
# SAFE CALLBACK PREFIX CHECK
# ==========================================================

def callback_starts_with(
    callback_data,
    prefix,
):

    if not callback_data:

        return False

    return callback_data.startswith(
        prefix
    )


# ==========================================================
# CALLBACK INDEX
# ==========================================================

def callback_index(
    callback_data,
    prefix,
):
    """
    Extract numeric callback index.

    Example:

        callback_index(
            "game_answer_2",
            "game_answer"
        )

        returns 2
    """

    if not callback_data:

        return None

    expected = (
        f"{prefix}_"
    )

    if not callback_data.startswith(
        expected
    ):

        return None

    value = callback_data[
        len(expected):
    ]

    try:

        return int(value)

    except (TypeError, ValueError):

        return None


# ==========================================================
# END
# ==========================================================
