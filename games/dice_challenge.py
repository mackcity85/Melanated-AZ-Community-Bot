# ==========================================================
# Melanated AZ Bot
# games/dice_challenge.py
#
# DICE CHALLENGE
#
# Features:
#   - Button-based gameplay
#   - Solo dice challenge
#   - Multiple challenge types
#   - Easy / Medium / Extreme
#   - Roll buttons
#   - Random targets
#   - Score tracking
#   - Win / loss tracking
#   - Streak tracking
#   - PASS always allowed
#   - Next challenge
#   - Change difficulty
#   - No import from admin.py
#
# This file is standalone.
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

DICE_ENABLED = True

VALID_DIFFICULTIES = (
    "easy",
    "medium",
    "extreme",
)


# ==========================================================
# CHALLENGES
# ==========================================================

CHALLENGES = {

    "easy": [

        {
            "name": "Lucky Seven",
            "description": "Roll two dice. Get exactly 7 to win!",
            "dice": 2,
            "target": 7,
            "type": "exact",
        },

        {
            "name": "High Roller",
            "description": "Roll one die. Roll 5 or higher to win!",
            "dice": 1,
            "target": 5,
            "type": "minimum",
        },

        {
            "name": "Double Trouble",
            "description": "Roll two dice. Get matching numbers to win!",
            "dice": 2,
            "target": 0,
            "type": "double",
        },

        {
            "name": "Lucky Six",
            "description": "Roll one die. Roll exactly 6 to win!",
            "dice": 1,
            "target": 6,
            "type": "exact",
        },

        {
            "name": "High Five",
            "description": "Roll one die. Roll 5 or 6 to win!",
            "dice": 1,
            "target": 5,
            "type": "minimum",
        },

    ],

    "medium": [

        {
            "name": "Double Down",
            "description": "Roll two dice. Get doubles to win!",
            "dice": 2,
            "target": 0,
            "type": "double",
        },

        {
            "name": "Lucky Eight",
            "description": "Roll two dice. Get exactly 8 to win!",
            "dice": 2,
            "target": 8,
            "type": "exact",
        },

        {
            "name": "Nine Lives",
            "description": "Roll two dice. Get 9 or higher to win!",
            "dice": 2,
            "target": 9,
            "type": "minimum",
        },

        {
            "name": "Snake Eyes",
            "description": "Roll two dice. Get double 1s to win!",
            "dice": 2,
            "target": 1,
            "type": "snake",
        },

        {
            "name": "Perfect Ten",
            "description": "Roll two dice. Get exactly 10 to win!",
            "dice": 2,
            "target": 10,
            "type": "exact",
        },

        {
            "name": "Lucky Eleven",
            "description": "Roll two dice. Get exactly 11 to win!",
            "dice": 2,
            "target": 11,
            "type": "exact",
        },

    ],

    "extreme": [

        {
            "name": "Triple Six",
            "description": "Roll three dice. All three must be 6!",
            "dice": 3,
            "target": 6,
            "type": "triple",
        },

        {
            "name": "Perfect Twelve",
            "description": "Roll two dice. Get exactly 12!",
            "dice": 2,
            "target": 12,
            "type": "exact",
        },

        {
            "name": "Triple Match",
            "description": "Roll three dice. All three must match!",
            "dice": 3,
            "target": 0,
            "type": "triple_double",
        },

        {
            "name": "Low Roll",
            "description": "Roll three dice. Total 5 or less to win!",
            "dice": 3,
            "target": 5,
            "type": "maximum",
        },

        {
            "name": "Lucky Fifteen",
            "description": "Roll three dice. Get exactly 15!",
            "dice": 3,
            "target": 15,
            "type": "exact",
        },

        {
            "name": "Jackpot",
            "description": "Roll three dice. Get 18!",
            "dice": 3,
            "target": 18,
            "type": "exact",
        },

    ],
}


# ==========================================================
# DIFFICULTY NAMES
# ==========================================================

DIFFICULTY_NAMES = {
    "easy": "🟢 Easy",
    "medium": "🟡 Medium",
    "extreme": "🔥 Extreme",
}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():

    return DICE_ENABLED


# ==========================================================
# GET DIFFICULTY
# ==========================================================

def get_difficulty(context):

    difficulty = context.user_data.get(
        "dice_difficulty",
        "easy",
    )

    if difficulty not in VALID_DIFFICULTIES:

        difficulty = "easy"

    return difficulty


# ==========================================================
# INITIALIZE STATS
# ==========================================================

def initialize_stats(context):

    if "dice_wins" not in context.user_data:

        context.user_data[
            "dice_wins"
        ] = 0

    if "dice_losses" not in context.user_data:

        context.user_data[
            "dice_losses"
        ] = 0

    if "dice_passes" not in context.user_data:

        context.user_data[
            "dice_passes"
        ] = 0

    if "dice_streak" not in context.user_data:

        context.user_data[
            "dice_streak"
        ] = 0

    if "dice_rolls" not in context.user_data:

        context.user_data[
            "dice_rolls"
        ] = 0


# ==========================================================
# STATS TEXT
# ==========================================================

def stats_text(context):

    initialize_stats(context)

    return (
        f"🏆 Wins: "
        f"{context.user_data.get('dice_wins', 0)}\n"
        f"❌ Losses: "
        f"{context.user_data.get('dice_losses', 0)}\n"
        f"🔥 Streak: "
        f"{context.user_data.get('dice_streak', 0)}\n"
        f"🎲 Rolls: "
        f"{context.user_data.get('dice_rolls', 0)}"
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
                    callback_data="dice_difficulty_easy",
                ),
                InlineKeyboardButton(
                    "🟡 Medium",
                    callback_data="dice_difficulty_medium",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="dice_difficulty_extreme",
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
                    "🎲 ROLL DICE",
                    callback_data="dice_roll",
                ),
            ],
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="dice_pass",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next Challenge",
                    callback_data="dice_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎯 Change Difficulty",
                    callback_data="dice_difficulty_menu",
                ),
            ],
        ]
    )


# ==========================================================
# GET CHALLENGE
# ==========================================================

def get_challenge(context):

    difficulty = get_difficulty(context)

    challenges = CHALLENGES.get(
        difficulty,
        CHALLENGES["easy"],
    )

    challenge = random.choice(
        challenges
    )

    context.user_data[
        "dice_current_challenge"
    ] = challenge

    context.user_data[
        "dice_answered"
    ] = False

    return challenge


# ==========================================================
# FORMAT CHALLENGE
# ==========================================================

def format_challenge(
    challenge,
    context,
):

    difficulty = get_difficulty(context)

    return (
        "🎲 DICE CHALLENGE\n\n"
        f"🎯 Level: "
        f"{DIFFICULTY_NAMES.get(difficulty, difficulty)}\n\n"
        f"🔥 {challenge['name']}\n\n"
        f"{challenge['description']}\n\n"
        f"{stats_text(context)}\n\n"
        "Ready to roll?\n"
        "😈 PASS is always allowed."
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
        reply_markup=game_keyboard(),
    )


# ==========================================================
# CHECK RESULT
# ==========================================================

def check_result(
    challenge,
    rolls,
):

    challenge_type = challenge["type"]

    total = sum(rolls)

    if challenge_type == "exact":

        return total == challenge["target"]

    if challenge_type == "minimum":

        return total >= challenge["target"]

    if challenge_type == "maximum":

        return total <= challenge["target"]

    if challenge_type == "double":

        return (
            len(rolls) == 2
            and rolls[0] == rolls[1]
        )

    if challenge_type == "snake":

        return (
            len(rolls) == 2
            and rolls[0] == 1
            and rolls[1] == 1
        )

    if challenge_type == "triple":

        return (
            len(rolls) == 3
            and rolls[0] == 6
            and rolls[1] == 6
            and rolls[2] == 6
        )

    if challenge_type == "triple_double":

        return (
            len(rolls) == 3
            and rolls[0] == rolls[1]
            and rolls[1] == rolls[2]
        )

    return False


# ==========================================================
# ROLL
# ==========================================================

async def roll_dice(
    query,
    context,
):

    challenge = context.user_data.get(
        "dice_current_challenge"
    )

    if not challenge:

        await start_challenge(
            query,
            context,
        )

        return

    if context.user_data.get(
        "dice_answered",
        False,
    ):

        await query.answer(
            "This challenge is already finished.",
            show_alert=True,
        )

        return

    rolls = [
        random.randint(1, 6)
        for _ in range(challenge["dice"])
    ]

    context.user_data[
        "dice_answered"
    ] = True

    context.user_data[
        "dice_rolls"
    ] += 1

    won = check_result(
        challenge,
        rolls,
    )

    roll_display = " + ".join(
        str(number)
        for number in rolls
    )

    total = sum(rolls)

    if won:

        context.user_data[
            "dice_wins"
        ] += 1

        context.user_data[
            "dice_streak"
        ] += 1

        await query.answer(
            "🎉 YOU WON!",
            show_alert=True,
        )

        result = (
            "🎉 JACKPOT!\n\n"
            f"🎯 Challenge: {challenge['name']}\n\n"
            f"🎲 Roll: {roll_display}\n"
            f"📊 Total: {total}\n\n"
            "🔥 YOU BEAT THE CHALLENGE!\n\n"
            f"{stats_text(context)}"
        )

    else:

        context.user_data[
            "dice_losses"
        ] += 1

        context.user_data[
            "dice_streak"
        ] = 0

        await query.answer(
            "❌ Better luck next time!",
            show_alert=True,
        )

        result = (
            "❌ NO LUCK!\n\n"
            f"🎯 Challenge: {challenge['name']}\n\n"
            f"🎲 Roll: {roll_display}\n"
            f"📊 Total: {total}\n\n"
            "😈 The dice weren't feeling generous.\n\n"
            f"{stats_text(context)}"
        )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➡️ Next Challenge",
                    callback_data="dice_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎯 Change Difficulty",
                    callback_data="dice_difficulty_menu",
                ),
            ],
        ]
    )

    await query.edit_message_text(
        result,
        reply_markup=keyboard,
    )


# ==========================================================
# /DICE
# ==========================================================

async def dice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not DICE_ENABLED:

        await message.reply_text(
            "🎲 Dice Challenge is currently disabled."
        )

        return

    initialize_stats(context)

    await message.reply_text(
        "🎲 DICE CHALLENGE\n\n"
        "Test your luck!\n\n"
        "Choose a difficulty:",
        reply_markup=difficulty_keyboard(),
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

    if not DICE_ENABLED:

        await query.answer(
            "Dice Challenge is disabled.",
            show_alert=True,
        )

        return

    initialize_stats(context)

    # ======================================================
    # DIFFICULTY MENU
    # ======================================================

    if data == "dice_difficulty_menu":

        await query.edit_message_text(
            "🎲 DICE CHALLENGE\n\n"
            "Choose your difficulty:",
            reply_markup=difficulty_keyboard(),
        )

        return

    # ======================================================
    # DIFFICULTY
    # ======================================================

    if data.startswith("dice_difficulty_"):

        difficulty = data.replace(
            "dice_difficulty_",
            "",
            1,
        )

        if difficulty not in VALID_DIFFICULTIES:

            difficulty = "easy"

        context.user_data[
            "dice_difficulty"
        ] = difficulty

        await start_challenge(
            query,
            context,
        )

        return

    # ======================================================
    # ROLL
    # ======================================================

    if data == "dice_roll":

        await roll_dice(
            query,
            context,
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "dice_pass":

        if context.user_data.get(
            "dice_answered",
            False,
        ):

            await query.answer(
                "This challenge is already finished.",
                show_alert=True,
            )

            return

        context.user_data[
            "dice_answered"
        ] = True

        context.user_data[
            "dice_passes"
        ] += 1

        context.user_data[
            "dice_streak"
        ] = 0

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➡️ Next Challenge",
                        callback_data="dice_next",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🎯 Change Difficulty",
                        callback_data="dice_difficulty_menu",
                    ),
                ],
            ]
        )

        await query.edit_message_text(
            "😈 PASS ACCEPTED\n\n"
            "No explanation required.\n"
            "Your choice, your rules. ❤️\n\n"
            f"{stats_text(context)}",
            reply_markup=keyboard,
        )

        return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "dice_next":

        await start_challenge(
            query,
            context,
        )

        return


# ==========================================================
# RESET STATS
# ==========================================================

def reset_stats(context):

    context.user_data[
        "dice_wins"
    ] = 0

    context.user_data[
        "dice_losses"
    ] = 0

    context.user_data[
        "dice_passes"
    ] = 0

    context.user_data[
        "dice_streak"
    ] = 0

    context.user_data[
        "dice_rolls"
    ] = 0

    context.user_data[
        "dice_answered"
    ] = False


# ==========================================================
# END dice_challenge.py
# ==========================================================
