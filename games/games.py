# ==========================================================
# Melanated AZ Bot
# games/games.py
#
# COMPLETE GAME ENGINE / GAME ROUTER
#
# Handles:
#   - Game database initialization
#   - Player profiles
#   - XP
#   - AZ Coins
#   - Wins / losses
#   - Scores
#   - Leaderboards
#   - Actual gameplay
#   - Game action callbacks
#
# Compatible with:
#   games/game_center.py
#
# ==========================================================

import logging
import random
import time
from datetime import datetime, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from raffle_database import get_connection


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(
    "melanated_az_bot.games.engine"
)


# ==========================================================
# REWARDS
# ==========================================================

BASE_XP = 10
WIN_XP = 25

BASE_COINS = 5
WIN_COINS = 15

XP_PER_LEVEL = 100


# ==========================================================
# GAME NAMES
# ==========================================================

GAME_NAMES = {

    # ------------------------------------------------------
    # ARCADE
    # ------------------------------------------------------

    "reaction": "⚡ Reaction Test",
    "number_guess": "🔢 Number Guess",
    "high_low": "📈 High or Low",
    "coin_flip": "🪙 Coin Flip",
    "dice_roll": "🎲 Dice Roll",

    # ------------------------------------------------------
    # OUTDOOR
    # ------------------------------------------------------

    "fishing": "🎣 Fishing",
    "camping": "🏕️ Camping",
    "hiking": "🥾 Hiking Challenge",
    "hunting": "🏹 Hunting Challenge",
    "survival": "🔥 Survival",

    # ------------------------------------------------------
    # SHOOTING
    # ------------------------------------------------------

    "target": "🎯 Target Practice",
    "quick_shot": "🔫 Quick Shot",
    "bullseye": "🎯 Bullseye",
    "accuracy": "🏹 Accuracy",
    "sniper": "🔭 Sniper Challenge",

    # ------------------------------------------------------
    # BOARD
    # ------------------------------------------------------

    "strategy": "♟️ Strategy",
    "dice_duel": "🎲 Dice Duel",

    # ------------------------------------------------------
    # PARTY
    # ------------------------------------------------------

    "truth_dare": "🔥 Truth or Dare",

    # ------------------------------------------------------
    # TRIVIA
    # ------------------------------------------------------

    "general_trivia": "🧠 General Trivia",
    "music_trivia": "🎵 Music Trivia",
    "sports_trivia": "🏆 Sports Trivia",
    "movie_trivia": "🎬 Movie Trivia",
    "word_challenge": "🔤 Word Challenge",

    # ------------------------------------------------------
    # SPORTS
    # ------------------------------------------------------

    "football": "🏈 Football Challenge",
    "basketball": "🏀 Basketball Challenge",
    "baseball": "⚾ Baseball Challenge",
    "boxing": "🥊 Boxing",
    "soccer": "⚽ Soccer",

    # ------------------------------------------------------
    # RACING
    # ------------------------------------------------------

    "car_race": "🏎️ Car Race",
    "bike_race": "🏍️ Bike Race",
    "boat_race": "🚤 Boat Race",
    "drag_race": "🏁 Drag Race",
    "street_race": "🏎️ Street Race",

    # ------------------------------------------------------
    # MYSTERY
    # ------------------------------------------------------

    "detective": "🕵🏾 Detective",
    "murder_mystery": "🔎 Mystery Case",
    "code_breaker": "🔐 Code Breaker",
    "escape": "🚪 Escape Room",
    "investigation": "🔍 Investigation",

    # ------------------------------------------------------
    # FIGHTING
    # ------------------------------------------------------

    "mma": "🥋 MMA",
    "karate": "🥋 Karate",
    "street_fight": "👊 Street Fight",
    "arena": "⚔️ Arena Battle",
}


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_game_database():
    """
    Create all Game Center tables if they do not exist.

    This is safe to call every time /games is opened.
    """

    conn = get_connection()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game_players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                games_played INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL DEFAULT 0,
                coins INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                games_played INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                high_score INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, game_id)
            )
            """
        )

        conn.commit()

        logger.info(
            "Game Center database initialized."
        )

    except Exception:

        conn.rollback()

        logger.exception(
            "Could not initialize Game Center database."
        )

        raise

    finally:

        conn.close()


# ==========================================================
# GENERIC KEYBOARDS
# ==========================================================

def game_back_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ]
        ]
    )


def replay_keyboard(game_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 Play Again",
                    callback_data=f"games_play_{game_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    )


# ==========================================================
# PLAYER
# ==========================================================

def ensure_player(
    user_id,
    username=None,
    display_name=None,
):

    initialize_game_database()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO game_players (
                user_id,
                username,
                display_name,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                username,
                display_name,
                now,
                now,
            ),
        )

        conn.commit()

    except Exception:

        conn.rollback()

        logger.exception(
            "Could not create/update game player."
        )

        raise

    finally:

        conn.close()


# ==========================================================
# RECORD GAME RESULT
# ==========================================================

def record_game_result(
    user_id,
    game_id,
    score=0,
    won=False,
):

    initialize_game_database()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    score = int(score or 0)

    xp_gain = (
        WIN_XP
        if won
        else BASE_XP
    )

    coin_gain = (
        WIN_COINS
        if won
        else BASE_COINS
    )

    conn = get_connection()

    try:

        # --------------------------------------------------
        # PLAYER TOTALS
        # --------------------------------------------------

        conn.execute(
            """
            UPDATE game_players
            SET
                games_played =
                    games_played + 1,

                wins =
                    wins + ?,

                losses =
                    losses + ?,

                xp =
                    xp + ?,

                coins =
                    coins + ?,

                level =
                    1 + ((xp + ?) / ?),

                updated_at = ?

            WHERE user_id = ?
            """,
            (
                1 if won else 0,
                0 if won else 1,
                xp_gain,
                coin_gain,
                xp_gain,
                XP_PER_LEVEL,
                now,
                user_id,
            ),
        )

        # --------------------------------------------------
        # SCORE HISTORY
        # --------------------------------------------------

        conn.execute(
            """
            INSERT INTO game_scores (
                user_id,
                game_id,
                score,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                game_id,
                score,
                now,
            ),
        )

        # --------------------------------------------------
        # PER-GAME STATISTICS
        # --------------------------------------------------

        conn.execute(
            """
            INSERT INTO game_stats (
                user_id,
                game_id,
                games_played,
                wins,
                losses,
                high_score
            )
            VALUES (?, ?, 1, ?, ?, ?)

            ON CONFLICT(user_id, game_id)
            DO UPDATE SET

                games_played =
                    games_played + 1,

                wins =
                    wins + excluded.wins,

                losses =
                    losses + excluded.losses,

                high_score =
                    CASE
                        WHEN excluded.high_score > high_score
                        THEN excluded.high_score
                        ELSE high_score
                    END
            """,
            (
                user_id,
                game_id,
                1 if won else 0,
                0 if won else 1,
                score,
            ),
        )

        conn.commit()

    except Exception:

        conn.rollback()

        logger.exception(
            "Could not record game result."
        )

        raise

    finally:

        conn.close()


# ==========================================================
# GET PLAYER STATS
# ==========================================================

def get_player_stats(user_id):

    initialize_game_database()

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT
                user_id,
                username,
                display_name,
                games_played,
                wins,
                losses,
                xp,
                coins,
                level
            FROM game_players
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        return row

    finally:

        conn.close()


# ==========================================================
# LEADERBOARDS
# ==========================================================

def get_leaderboard_by_xp(limit=10):

    initialize_game_database()

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT
                display_name,
                username,
                xp,
                level
            FROM game_players
            ORDER BY xp DESC, level DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    finally:

        conn.close()


def get_leaderboard_by_coins(limit=10):

    initialize_game_database()

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT
                display_name,
                username,
                coins
            FROM game_players
            ORDER BY coins DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    finally:

        conn.close()


def get_leaderboard_by_games(limit=10):

    initialize_game_database()

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT
                display_name,
                username,
                games_played
            FROM game_players
            ORDER BY games_played DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    finally:

        conn.close()


def get_leaderboard_by_wins(limit=10):

    initialize_game_database()

    conn = get_connection()

    try:

        return conn.execute(
            """
            SELECT
                display_name,
                username,
                wins
            FROM game_players
            ORDER BY wins DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    finally:

        conn.close()


# ==========================================================
# RESULT SCREEN
# ==========================================================

async def show_result(
    query,
    game_id,
    title,
    body,
    score,
    won,
):

    record_game_result(
        user_id=query.from_user.id,
        game_id=game_id,
        score=score,
        won=won,
    )

    xp = (
        WIN_XP
        if won
        else BASE_XP
    )

    coins = (
        WIN_COINS
        if won
        else BASE_COINS
    )

    result = (
        f"{title}\n\n"
        f"{body}\n\n"
        f"📊 <b>Score:</b> {score}\n\n"
        f"⭐ <b>+{xp} XP</b>\n"
        f"🪙 <b>+{coins} AZ Coins</b>"
    )

    await query.edit_message_text(
        result,
        reply_markup=replay_keyboard(game_id),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# REACTION TEST
# ==========================================================

async def reaction_game(
    query,
    context,
):

    context.user_data[
        "reaction_start"
    ] = time.monotonic()

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⚡ TAP NOW!",
                    callback_data="game_reaction_tap",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    )

    await query.edit_message_text(
        "⚡ <b>REACTION TEST</b>\n\n"
        "Hit the button as fast as you can!\n\n"
        "How fast are your reactions?",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


async def reaction_tap(
    query,
    context,
):

    start = context.user_data.pop(
        "reaction_start",
        None,
    )

    if start is None:

        await query.answer(
            "Start a new reaction test.",
            show_alert=True,
        )

        return

    elapsed = (
        time.monotonic() - start
    )

    milliseconds = max(
        1,
        int(elapsed * 1000),
    )

    score = max(
        1,
        1000 - milliseconds,
    )

    won = milliseconds < 600

    await show_result(
        query,
        "reaction",
        "⚡ <b>REACTION TEST</b>",
        (
            f"⏱️ Reaction time: "
            f"<b>{milliseconds} ms</b>\n\n"
            +
            (
                "🔥 Lightning fast!"
                if won
                else
                "😅 Try again and beat your time!"
            )
        ),
        score,
        won,
    )


# ==========================================================
# NUMBER GUESS
# ==========================================================

async def number_guess_game(
    query,
    context,
):

    target = random.randint(
        1,
        10,
    )

    context.user_data[
        "number_guess"
    ] = target

    buttons = []

    for value in range(
        1,
        11,
    ):

        buttons.append(
            InlineKeyboardButton(
                str(value),
                callback_data=f"game_guess_{value}",
            )
        )

    keyboard = [
        buttons[0:5],
        buttons[5:10],
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ],
    ]

    await query.edit_message_text(
        "🔢 <b>NUMBER GUESS</b>\n\n"
        "I'm thinking of a number from "
        "<b>1 to 10</b>.\n\n"
        "Can you guess it?",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode=ParseMode.HTML,
    )


async def number_guess_answer(
    query,
    context,
    guess,
):

    target = context.user_data.pop(
        "number_guess",
        None,
    )

    if target is None:

        await query.answer(
            "That game has already ended.",
            show_alert=True,
        )

        return

    try:

        guess = int(guess)

    except (
        ValueError,
        TypeError,
    ):

        await query.answer(
            "Invalid guess.",
            show_alert=True,
        )

        return

    correct = (
        guess == target
    )

    score = (
        100
        if correct
        else max(
            10,
            50 - abs(
                guess - target
            ) * 5,
        )
    )

    await show_result(
        query,
        "number_guess",
        "🔢 <b>NUMBER GUESS</b>",
        (
            f"🎯 My number was "
            f"<b>{target}</b>.\n\n"
            +
            (
                "🎉 You got it!"
                if correct
                else
                f"❌ You guessed <b>{guess}</b>."
            )
        ),
        score,
        correct,
    )


# ==========================================================
# HIGH / LOW
# ==========================================================

async def high_low_game(
    query,
    context,
):

    first = random.randint(
        1,
        13,
    )

    second = random.randint(
        1,
        13,
    )

    context.user_data[
        "high_low"
    ] = {
        "first": first,
        "second": second,
    }

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📈 HIGHER",
                    callback_data="game_high",
                ),
                InlineKeyboardButton(
                    "📉 LOWER",
                    callback_data="game_low",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    )

    await query.edit_message_text(
        "📈 <b>HIGH OR LOW</b>\n\n"
        f"Current card: <b>{first}</b>\n\n"
        "Will the next card be higher "
        "or lower?",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


async def high_low_answer(
    query,
    context,
    choice,
):

    data = context.user_data.pop(
        "high_low",
        None,
    )

    if not data:

        await query.answer(
            "That game has already ended.",
            show_alert=True,
        )

        return

    first = data["first"]
    second = data["second"]

    if second == first:

        won = False

    elif choice == "high":

        won = second > first

    else:

        won = second < first

    await show_result(
        query,
        "high_low",
        "📈 <b>HIGH OR LOW</b>",
        (
            f"First card: <b>{first}</b>\n"
            f"Next card: <b>{second}</b>\n\n"
            +
            (
                "🎉 Correct!"
                if won
                else
                "❌ Wrong guess!"
            )
        ),
        100 if won else 25,
        won,
    )


# ==========================================================
# COIN FLIP
# ==========================================================

async def coin_flip_game(
    query,
    context,
):

    result = random.choice(
        [
            "HEADS",
            "TAILS",
        ]
    )

    await show_result(
        query,
        "coin_flip",
        "🪙 <b>COIN FLIP</b>",
        f"The coin landed on <b>{result}</b>!",
        50,
        True,
    )


# ==========================================================
# DICE ROLL
# ==========================================================

async def dice_roll_game(
    query,
    context,
):

    roll = random.randint(
        1,
        6,
    )

    won = roll >= 4

    await show_result(
        query,
        "dice_roll",
        "🎲 <b>DICE ROLL</b>",
        (
            f"You rolled a "
            f"<b>{roll}</b>!\n\n"
            +
            (
                "🔥 Nice roll!"
                if won
                else
                "🎲 Better luck next time!"
            )
        ),
        roll * 10,
        won,
    )


# ==========================================================
# RANDOM CHALLENGES
# ==========================================================

CHALLENGES = {

    # ------------------------------------------------------
    # OUTDOOR
    # ------------------------------------------------------

    "fishing": [
        ("🐟 You caught a huge bass!", True),
        ("🐠 You caught a colorful fish!", True),
        ("🎣 The fish got away!", False),
        ("🐟 You landed a trophy fish!", True),
    ],

    "camping": [
        ("🔥 You built the perfect campfire!", True),
        ("🏕️ You found an amazing campsite!", True),
        ("🌧️ Rain ruined the campsite!", False),
        ("🦌 You spotted wildlife nearby!", True),
    ],

    "hiking": [
        ("🥾 You reached the summit!", True),
        ("🏔️ Amazing trail completed!", True),
        ("🌲 You discovered a hidden trail!", True),
        ("😅 You took the wrong trail!", False),
    ],

    "hunting": [
        ("🏹 Perfect shot!", True),
        ("🦌 You tracked your target!", True),
        ("🌲 The target escaped!", False),
        ("🎯 Bullseye!", True),
    ],

    "survival": [
        ("🔥 You survived the night!", True),
        ("💧 You found clean water!", True),
        ("🏕️ You built shelter!", True),
        ("🌧️ The storm almost got you!", False),
    ],

    # ------------------------------------------------------
    # SHOOTING
    # ------------------------------------------------------

    "target": [
        ("🎯 Bullseye!", True),
        ("🎯 Excellent shot!", True),
        ("💥 Direct hit!", True),
        ("😅 You missed!", False),
    ],

    "quick_shot": [
        ("⚡ Lightning-fast shot!", True),
        ("🎯 Fast and accurate!", True),
        ("💥 Perfect hit!", True),
        ("😅 Too slow!", False),
    ],

    "bullseye": [
        ("🎯 PERFECT BULLSEYE!", True),
        ("🔥 Dead center!", True),
        ("🎯 Almost perfect!", True),
        ("😅 Off target!", False),
    ],

    "accuracy": [
        ("🏹 Incredible accuracy!", True),
        ("🎯 Excellent aim!", True),
        ("💥 Great shot!", True),
        ("😅 Needs practice!", False),
    ],

    "sniper": [
        ("🔭 Perfect long-range shot!", True),
        ("🎯 Target hit!", True),
        ("🔥 Incredible accuracy!", True),
        ("😅 Target escaped!", False),
    ],

    # ------------------------------------------------------
    # BOARD
    # ------------------------------------------------------

    "strategy": [
        ("♟️ Brilliant strategy!", True),
        ("🧠 You outsmarted the opponent!", True),
        ("♟️ Excellent move!", True),
        ("😅 Your opponent saw it coming!", False),
    ],

    "dice_duel": [
        ("🎲 You won the dice duel!", True),
        ("🎲 Huge roll!", True),
        ("😈 Your opponent got crushed!", True),
        ("💀 Your opponent rolled higher!", False),
    ],

    # ------------------------------------------------------
    # SPORTS
    # ------------------------------------------------------

    "football": [
        ("🏈 TOUCHDOWN!", True),
        ("🏈 Huge gain!", True),
        ("🏈 Perfect pass!", True),
        ("🏈 Fumble!", False),
    ],

    "basketball": [
        ("🏀 THREE POINTER!", True),
        ("🏀 Nothing but net!", True),
        ("🔥 Clutch shot!", True),
        ("😅 Air ball!", False),
    ],

    "baseball": [
        ("⚾ HOME RUN!", True),
        ("⚾ Perfect hit!", True),
        ("🔥 Extra-base hit!", True),
        ("😅 Strikeout!", False),
    ],

    "boxing": [
        ("🥊 Knockout!", True),
        ("🥊 Perfect combination!", True),
        ("🔥 Huge punch!", True),
        ("😵 You got rocked!", False),
    ],

    "soccer": [
        ("⚽ GOAL!", True),
        ("⚽ Beautiful finish!", True),
        ("🔥 Top corner!", True),
        ("😅 Missed the shot!", False),
    ],

    # ------------------------------------------------------
    # RACING
    # ------------------------------------------------------

    "car_race": [
        ("🏎️ You crossed the finish line first!", True),
        ("🏁 Perfect launch!", True),
        ("🔥 Fastest lap!", True),
        ("💥 You spun out!", False),
    ],

    "bike_race": [
        ("🏍️ First across the line!", True),
        ("🏁 Amazing cornering!", True),
        ("🔥 Fastest lap!", True),
        ("😅 You wiped out!", False),
    ],

    "boat_race": [
        ("🚤 You dominated the race!", True),
        ("🌊 Perfect turn!", True),
        ("🏁 First place!", True),
        ("🌊 You hit a huge wave!", False),
    ],

    "drag_race": [
        ("🏁 LIGHTS OUT!", True),
        ("🏎️ Perfect launch!", True),
        ("🔥 You won by a nose!", True),
        ("😅 Bad reaction!", False),
    ],

    "street_race": [
        ("🏎️ You took the win!", True),
        ("🔥 Fastest car on the street!", True),
        ("🏁 Perfect corner!", True),
        ("💥 You lost control!", False),
    ],

    # ------------------------------------------------------
    # FIGHTING
    # ------------------------------------------------------

    "mma": [
        ("🥊 Submission victory!", True),
        ("🔥 Technical knockout!", True),
        ("💪 Dominant performance!", True),
        ("😵 You got submitted!", False),
    ],

    "karate": [
        ("🥋 Perfect strike!", True),
        ("🔥 Tournament victory!", True),
        ("🥋 Excellent technique!", True),
        ("😵 Countered!", False),
    ],

    "street_fight": [
        ("👊 You won the fight!", True),
        ("🔥 Knockout!", True),
        ("💪 Powerful combination!", True),
        ("😵 You got dropped!", False),
    ],

    "arena": [
        ("⚔️ ARENA VICTORY!", True),
        ("🔥 You defeated your opponent!", True),
        ("⚔️ Critical hit!", True),
        ("💀 You were defeated!", False),
    ],

    # ------------------------------------------------------
    # MYSTERY
    # ------------------------------------------------------

    "murder_mystery": [
        ("🔎 Mystery solved!", True),
        ("🕵🏾 You found the culprit!", True),
        ("🔍 Critical clue discovered!", True),
        ("😅 Wrong suspect!", False),
    ],

    "investigation": [
        ("🔍 Evidence discovered!", True),
        ("🕵🏾 Investigation successful!", True),
        ("🧠 Case breakthrough!", True),
        ("😅 Dead end!", False),
    ],
}


# ==========================================================
# RANDOM CHALLENGE ENGINE
# ==========================================================

async def random_challenge_game(
    query,
    game_id,
):

    outcomes = CHALLENGES.get(
        game_id,
        [
            ("🎮 Challenge completed!", True),
            ("🔥 Great job!", True),
            ("🏆 Excellent!", True),
            ("😅 Try again!", False),
        ],
    )

    outcome, won = random.choice(
        outcomes
    )

    score = random.randint(
        40,
        100,
    )

    await show_result(
        query,
        game_id,
        f"<b>{GAME_NAMES.get(game_id, '🎮 Game')}</b>",
        outcome,
        score,
        won,
    )


# ==========================================================
# TRUTH OR DARE
# ==========================================================

TRUTHS = [

    "What is something you've never told the group?",
    "Who in the group has the best personality?",
    "What's your biggest guilty pleasure?",
    "What's the wildest thing you've ever done?",
    "What is one thing you want to try someday?",
    "What's something that instantly makes you laugh?",
    "What's your biggest pet peeve?",
    "What's one thing people misunderstand about you?",
]


DARES = [

    "Send the funniest GIF you can find.",
    "Give someone in the group a genuine compliment.",
    "Change your profile picture for 10 minutes.",
    "Send your best pickup line.",
    "Tell the group your most embarrassing story.",
    "Send a funny emoji combination.",
    "Describe yourself using only three emojis.",
    "Give someone a compliment you normally wouldn't say.",
]


async def truth_dare_game(
    query,
):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔥 TRUTH",
                    callback_data="game_td_truth",
                ),
                InlineKeyboardButton(
                    "😈 DARE",
                    callback_data="game_td_dare",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    )

    await query.edit_message_text(
        "🔥 <b>TRUTH OR DARE</b>\n\n"
        "Choose your challenge!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


async def truth_dare_answer(
    query,
    choice,
):

    if choice == "truth":

        prompt = random.choice(
            TRUTHS
        )

        title = "🔥 TRUTH"

    else:

        prompt = random.choice(
            DARES
        )

        title = "😈 DARE"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 Another",
                    callback_data="games_play_truth_dare",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    )

    await query.edit_message_text(
        f"<b>{title}</b>\n\n"
        f"{prompt}\n\n"
        "🔥 Good luck!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# TRIVIA
# ==========================================================

TRIVIA = {

    "general_trivia": [

        (
            "What is the largest planet?",
            [
                "Earth",
                "Mars",
                "Jupiter",
                "Venus",
            ],
            "Jupiter",
        ),

        (
            "How many continents are there?",
            [
                "5",
                "6",
                "7",
                "8",
            ],
            "7",
        ),

        (
            "What is the fastest land animal?",
            [
                "Lion",
                "Cheetah",
                "Horse",
                "Tiger",
            ],
            "Cheetah",
        ),
    ],

    "music_trivia": [

        (
            "Which instrument has 88 keys?",
            [
                "Guitar",
                "Piano",
                "Drums",
                "Violin",
            ],
            "Piano",
        ),

        (
            "How many strings does a standard guitar have?",
            [
                "4",
                "5",
                "6",
                "7",
            ],
            "6",
        ),

        (
            "Which musical symbol indicates silence?",
            [
                "Rest",
                "Sharp",
                "Flat",
                "Clef",
            ],
            "Rest",
        ),
    ],

    "sports_trivia": [

        (
            "How many players are on a basketball team on the court?",
            [
                "4",
                "5",
                "6",
                "7",
            ],
            "5",
        ),

        (
            "How many bases are on a baseball field?",
            [
                "3",
                "4",
                "5",
                "6",
            ],
            "4",
        ),

        (
            "How many points is a touchdown worth before the extra point?",
            [
                "3",
                "6",
                "7",
                "8",
            ],
            "6",
        ),
    ],

    "movie_trivia": [

        (
            "Which superhero carries a shield?",
            [
                "Batman",
                "Spider-Man",
                "Captain America",
                "Thor",
            ],
            "Captain America",
        ),

        (
            "Which movie features Jack Sparrow?",
            [
                "Avatar",
                "Pirates of the Caribbean",
                "Titanic",
                "Rocky",
            ],
            "Pirates of the Caribbean",
        ),

        (
            "Who is Shrek's best friend?",
            [
                "Donkey",
                "Fiona",
                "Puss",
                "Dragon",
            ],
            "Donkey",
        ),
    ],

    "word_challenge": [

        (
            "Which word is spelled correctly?",
            [
                "Necessary",
                "Necesary",
                "Neccessary",
                "Necassary",
            ],
            "Necessary",
        ),

        (
            "What is the opposite of 'ancient'?",
            [
                "Old",
                "Modern",
                "Historic",
                "Past",
            ],
            "Modern",
        ),

        (
            "Which word means very happy?",
            [
                "Sad",
                "Angry",
                "Ecstatic",
                "Tired",
            ],
            "Ecstatic",
        ),
    ],
}


async def trivia_game(
    query,
    context,
    game_id,
):

    questions = TRIVIA.get(
        game_id,
        [],
    )

    if not questions:

        await query.answer(
            "Trivia is not available yet.",
            show_alert=True,
        )

        return

    question, answers, correct = random.choice(
        questions
    )

    shuffled = list(
        answers
    )

    random.shuffle(
        shuffled
    )

    context.user_data[
        "trivia"
    ] = {
        "game_id": game_id,
        "correct": correct,
    }

    context.user_data[
        "trivia_answers"
    ] = shuffled

    buttons = []

    for index, answer in enumerate(
        shuffled
    ):

        buttons.append(
            [
                InlineKeyboardButton(
                    answer,
                    callback_data=f"game_trivia_{index}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    )

    await query.edit_message_text(
        f"<b>{GAME_NAMES[game_id]}</b>\n\n"
        f"{question}",
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
        parse_mode=ParseMode.HTML,
    )


async def trivia_answer(
    query,
    context,
    answer_index,
):

    data = context.user_data.pop(
        "trivia",
        None,
    )

    answers = context.user_data.pop(
        "trivia_answers",
        None,
    )

    if not data or not answers:

        await query.answer(
            "That trivia game has already ended.",
            show_alert=True,
        )

        return

    try:

        index = int(
            answer_index
        )

        answer = answers[index]

    except (
        ValueError,
        IndexError,
        TypeError,
    ):

        await query.answer(
            "Invalid answer.",
            show_alert=True,
        )

        return

    correct = data["correct"]
    game_id = data["game_id"]

    won = (
        answer == correct
    )

    await show_result(
        query,
        game_id,
        f"<b>{GAME_NAMES[game_id]}</b>",
        (
            f"Your answer: "
            f"<b>{answer}</b>\n"
            f"Correct answer: "
            f"<b>{correct}</b>\n\n"
            +
            (
                "🎉 Correct!"
                if won
                else
                "❌ Incorrect!"
            )
        ),
        100 if won else 20,
        won,
    )


# ==========================================================
# CODE BREAKER
# ==========================================================

async def code_breaker_game(
    query,
    context,
):

    code = random.randint(
        100,
        999,
    )

    context.user_data[
        "code_breaker"
    ] = code

    # Instead of only offering 100, 200, 300...
    # give the player a range of practical guesses.

    hundreds = (code // 100) * 100

    guesses = {
        100,
        200,
        300,
        400,
        500,
        600,
        700,
        800,
        900,
        max(100, hundreds),
        min(999, hundreds + 99),
    }

    keyboard = []

    for number in sorted(
        guesses
    ):

        keyboard.append(
            [
                InlineKeyboardButton(
                    str(number),
                    callback_data=f"game_code_{number}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    )

    await query.edit_message_text(
        "🔐 <b>CODE BREAKER</b>\n\n"
        "Break the security code!\n\n"
        "The code is between "
        "<b>100 and 999</b>.\n\n"
        "Choose your guess:",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode=ParseMode.HTML,
    )


async def code_breaker_answer(
    query,
    context,
    guess,
):

    code = context.user_data.pop(
        "code_breaker",
        None,
    )

    if code is None:

        await query.answer(
            "That game has already ended.",
            show_alert=True,
        )

        return

    try:

        guess = int(
            guess
        )

    except (
        ValueError,
        TypeError,
    ):

        await query.answer(
            "Invalid code.",
            show_alert=True,
        )

        return

    won = (
        guess == code
    )

    difference = abs(
        guess - code
    )

    if won:

        score = 100

        message = (
            "🔓 <b>CODE BROKEN!</b>\n\n"
            f"The code was <b>{code}</b>!"
        )

    else:

        score = max(
            10,
            100 - difference // 5,
        )

        hint = (
            "📈 The code is HIGHER."
            if guess < code
            else
            "📉 The code is LOWER."
        )

        message = (
            f"❌ <b>Incorrect.</b>\n\n"
            f"{hint}\n"
            f"Your guess: <b>{guess}</b>"
        )

    await show_result(
        query,
        "code_breaker",
        "🔐 <b>CODE BREAKER</b>",
        message,
        score,
        won,
    )


# ==========================================================
# ESCAPE ROOM
# ==========================================================

ESCAPE_OPTIONS = [

    (
        "🚪 Open the red door",
        "red",
    ),

    (
        "🔐 Try the keypad",
        "keypad",
    ),

    (
        "🪟 Check the window",
        "window",
    ),
]


async def escape_game(
    query,
    context,
):

    correct = random.choice(
        [
            "red",
            "keypad",
            "window",
        ]
    )

    context.user_data[
        "escape"
    ] = correct

    keyboard = [
        [
            InlineKeyboardButton(
                label,
                callback_data=f"game_escape_{value}",
            )
        ]

        for label, value
        in ESCAPE_OPTIONS
    ]

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    )

    await query.edit_message_text(
        "🚪 <b>ESCAPE ROOM</b>\n\n"
        "You're locked inside a mysterious room.\n\n"
        "Find the correct way out!",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode=ParseMode.HTML,
    )


async def escape_answer(
    query,
    context,
    choice,
):

    correct = context.user_data.pop(
        "escape",
        None,
    )

    if correct is None:

        await query.answer(
            "That escape room has ended.",
            show_alert=True,
        )

        return

    won = (
        choice == correct
    )

    if won:

        message = (
            "🎉 <b>YOU ESCAPED!</b>\n\n"
            "You found the correct way out!"
        )

        score = 100

    else:

        message = (
            "⛓️ <b>STILL TRAPPED!</b>\n\n"
            "That wasn't the right way out."
        )

        score = 20

    await show_result(
        query,
        "escape",
        "🚪 <b>ESCAPE ROOM</b>",
        message,
        score,
        won,
    )


# ==========================================================
# DETECTIVE
# ==========================================================

async def detective_game(
    query,
    context,
):

    suspects = [

        "🕵🏾 Alex",
        "🕵🏾 Jordan",
        "🕵🏾 Taylor",
        "🕵🏾 Morgan",

    ]

    culprit = random.choice(
        suspects
    )

    context.user_data[
        "detective"
    ] = culprit

    context.user_data[
        "detective_suspects"
    ] = suspects

    keyboard = [

        [
            InlineKeyboardButton(
                suspect,
                callback_data=f"game_detective_{index}",
            )
        ]

        for index, suspect
        in enumerate(suspects)
    ]

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    )

    await query.edit_message_text(
        "🕵🏾 <b>DETECTIVE</b>\n\n"
        "A crime has been committed.\n\n"
        "Study the suspects and identify "
        "the culprit!",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode=ParseMode.HTML,
    )


async def detective_answer(
    query,
    context,
    index,
):

    culprit = context.user_data.pop(
        "detective",
        None,
    )

    suspects = context.user_data.pop(
        "detective_suspects",
        None,
    )

    if culprit is None or suspects is None:

        await query.answer(
            "That case has already been closed.",
            show_alert=True,
        )

        return

    try:

        selected = suspects[
            int(index)
        ]

    except (
        ValueError,
        IndexError,
        TypeError,
    ):

        await query.answer(
            "Invalid suspect.",
            show_alert=True,
        )

        return

    won = (
        selected == culprit
    )

    await show_result(
        query,
        "detective",
        "🕵🏾 <b>DETECTIVE</b>",
        (
            f"You selected: <b>{selected}</b>\n"
            f"The culprit was: <b>{culprit}</b>\n\n"
            +
            (
                "🧠 Brilliant deduction!"
                if won
                else
                "🔍 Better luck on the next case!"
            )
        ),
        100 if won else 20,
        won,
    )


# ==========================================================
# PLAY GAME
# ==========================================================

async def play_game(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_id,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    if game_id not in GAME_NAMES:

        await query.answer(
            "Game not found.",
            show_alert=True,
        )

        return

    ensure_player(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    try:

        if game_id == "reaction":

            await reaction_game(
                query,
                context,
            )

            return

        if game_id == "number_guess":

            await number_guess_game(
                query,
                context,
            )

            return

        if game_id == "high_low":

            await high_low_game(
                query,
                context,
            )

            return

        if game_id == "coin_flip":

            await coin_flip_game(
                query,
                context,
            )

            return

        if game_id == "dice_roll":

            await dice_roll_game(
                query,
                context,
            )

            return

        if game_id == "truth_dare":

            await truth_dare_game(
                query,
            )

            return

        if game_id in TRIVIA:

            await trivia_game(
                query,
                context,
                game_id,
            )

            return

        if game_id == "code_breaker":

            await code_breaker_game(
                query,
                context,
            )

            return

        if game_id == "escape":

            await escape_game(
                query,
                context,
            )

            return

        if game_id == "detective":

            await detective_game(
                query,
                context,
            )

            return

        await random_challenge_game(
            query,
            game_id,
        )

    except Exception:

        logger.exception(
            "Game failed: %s",
            game_id,
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>Game Error</b>\n\n"
                "Something went wrong starting "
                "this game.\n\n"
                "Please try again.",
                reply_markup=game_back_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        except Exception:

            logger.exception(
                "Could not display game error."
            )


# ==========================================================
# CENTRAL GAME ACTION ROUTER
# ==========================================================

async def games_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Game engine callback received: %s",
        data,
    )

    try:

        # --------------------------------------------------
        # REACTION
        # --------------------------------------------------

        if data == "game_reaction_tap":

            await query.answer()

            await reaction_tap(
                query,
                context,
            )

            return

        # --------------------------------------------------
        # NUMBER GUESS
        # --------------------------------------------------

        if data.startswith(
            "game_guess_"
        ):

            await query.answer()

            guess = data[
                len("game_guess_"):
            ]

            await number_guess_answer(
                query,
                context,
                guess,
            )

            return

        # --------------------------------------------------
        # HIGH / LOW
        # --------------------------------------------------

        if data == "game_high":

            await query.answer()

            await high_low_answer(
                query,
                context,
                "high",
            )

            return

        if data == "game_low":

            await query.answer()

            await high_low_answer(
                query,
                context,
                "low",
            )

            return

        # --------------------------------------------------
        # TRUTH / DARE
        # --------------------------------------------------

        if data == "game_td_truth":

            await query.answer()

            await truth_dare_answer(
                query,
                "truth",
            )

            return

        if data == "game_td_dare":

            await query.answer()

            await truth_dare_answer(
                query,
                "dare",
            )

            return

        # --------------------------------------------------
        # TRIVIA
        # --------------------------------------------------

        if data.startswith(
            "game_trivia_"
        ):

            await query.answer()

            answer_index = data[
                len("game_trivia_"):
            ]

            await trivia_answer(
                query,
                context,
                answer_index,
            )

            return

        # --------------------------------------------------
        # CODE BREAKER
        # --------------------------------------------------

        if data.startswith(
            "game_code_"
        ):

            await query.answer()

            guess = data[
                len("game_code_"):
            ]

            await code_breaker_answer(
                query,
                context,
                guess,
            )

            return

        # --------------------------------------------------
        # ESCAPE
        # --------------------------------------------------

        if data.startswith(
            "game_escape_"
        ):

            await query.answer()

            choice = data[
                len("game_escape_"):
            ]

            await escape_answer(
                query,
                context,
                choice,
            )

            return

        # --------------------------------------------------
        # DETECTIVE
        # --------------------------------------------------

        if data.startswith(
            "game_detective_"
        ):

            await query.answer()

            index = data[
                len("game_detective_"):
            ]

            await detective_answer(
                query,
                context,
                index,
            )

            return

        # --------------------------------------------------
        # UNKNOWN
        # --------------------------------------------------

        logger.warning(
            "Unknown game engine callback: %s",
            data,
        )

        await query.answer(
            "⚠️ Game action not recognized.",
            show_alert=True,
        )

    except Exception:

        logger.exception(
            "Game callback failed: %s",
            data,
        )

        try:

            await query.answer(
                "⚠️ Game action failed.",
                show_alert=True,
            )

        except Exception:

            pass


# ==========================================================
# END games.py
# ==========================================================
