# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# MELANATED AZ GAME CENTER
#
# Handles:
#   - /games
#   - Game Center menu
#   - Game categories
#   - Game menus
#   - Player profiles
#   - Leaderboards
#   - Game database
#   - XP / Coins
#   - Game routing
#   - Built-in mini games
#
# ==========================================================

import logging
import random
import time

from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from raffle_database import get_connection

from games.registry import (
    GAMES as GAME_REGISTRY,
    CATEGORY_NAME,
    CATEGORY_DESCRIPTION,
    get_enabled_games,
    get_game_menu_buttons,
)


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(
    "melanated_az_bot.games"
)


# ==========================================================
# GAME CATEGORIES
# ==========================================================

GAME_CATEGORIES = {

    "arcade": {
        "name": "🕹️ Arcade",
        "description": (
            "Classic fast-paced arcade games."
        ),
    },

    "outdoor": {
        "name": "🌲 Outdoor",
        "description": (
            "Fishing, hunting, camping and outdoor adventures."
        ),
    },

    "solo": {
        "name": "👤 Solo",
        "description": (
            "Games you can play by yourself."
        ),
    },

    "shooting": {
        "name": "🎯 Action & Shooting",
        "description": (
            "Target, shooting and action challenges."
        ),
    },

    "board": {
        "name": "🎲 Board Games",
        "description": (
            "Classic and strategic board games."
        ),
    },

    "party": {
        "name": "🎉 Party Games",
        "description": (
            "Games designed for the whole group."
        ),
    },

    "trivia": {
        "name": "🧠 Trivia & Brain",
        "description": (
            "Trivia, puzzles and brain challenges."
        ),
    },

    "sports": {
        "name": "🏆 Sports",
        "description": (
            "Sports challenges and competitions."
        ),
    },

    "racing": {
        "name": "🏎️ Racing",
        "description": (
            "Cars, motorcycles, boats and more."
        ),
    },

    "mystery": {
        "name": "🕵🏾 Mystery & Strategy",
        "description": (
            "Mysteries, investigations and strategy."
        ),
    },

    "fighting": {
        "name": "🥊 Fighting",
        "description": (
            "Arena battles and fighting games."
        ),
    },
}


# ==========================================================
# CATEGORY GAME MAP
#
# These are the games currently displayed in each category.
#
# The registry remains the master definition for games that
# are globally available.
#
# ==========================================================

CATEGORY_GAMES = {

    "arcade": [
        "reaction",
        "number_guess",
        "high_low",
        "coin_flip",
        "dice_roll",
    ],

    "outdoor": [
        "fishing",
        "camping",
        "hiking",
        "hunting",
        "survival",
    ],

    "solo": [
        "number_guess",
        "coin_flip",
        "dice_roll",
        "high_low",
        "reaction",
    ],

    "shooting": [
        "target",
        "quick_shot",
        "bullseye",
        "accuracy",
        "sniper",
    ],

    "board": [
        "dice_roll",
        "high_low",
        "number_guess",
        "strategy",
        "dice_duel",
    ],

    "party": [
        "coin_flip",
        "dice_roll",
        "truth_dare",
        "high_low",
        "reaction",
    ],

    "trivia": [
        "general_trivia",
        "music_trivia",
        "sports_trivia",
        "movie_trivia",
        "word_challenge",
    ],

    "sports": [
        "football",
        "basketball",
        "baseball",
        "boxing",
        "soccer",
    ],

    "racing": [
        "car_race",
        "bike_race",
        "boat_race",
        "drag_race",
        "street_race",
    ],

    "mystery": [
        "detective",
        "murder_mystery",
        "code_breaker",
        "escape",
        "investigation",
    ],

    "fighting": [
        "boxing",
        "mma",
        "karate",
        "street_fight",
        "arena",
    ],
}


# ==========================================================
# DISPLAY NAMES
# ==========================================================

GAME_NAMES = {

    "reaction": "⚡ Reaction Test",
    "number_guess": "🔢 Number Guess",
    "high_low": "📈 High or Low",
    "coin_flip": "🪙 Coin Flip",
    "dice_roll": "🎲 Dice Roll",

    "fishing": "🎣 Fishing",
    "camping": "🏕️ Camping",
    "hiking": "🥾 Hiking Challenge",
    "hunting": "🏹 Hunting Challenge",
    "survival": "🔥 Survival",

    "target": "🎯 Target Practice",
    "quick_shot": "🔫 Quick Shot",
    "bullseye": "🎯 Bullseye",
    "accuracy": "🏹 Accuracy",
    "sniper": "🔭 Sniper Challenge",

    "strategy": "♟️ Strategy",
    "dice_duel": "🎲 Dice Duel",

    "truth_dare": "🔥 Truth or Dare",

    "general_trivia": "🧠 General Trivia",
    "music_trivia": "🎵 Music Trivia",
    "sports_trivia": "🏆 Sports Trivia",
    "movie_trivia": "🎬 Movie Trivia",
    "word_challenge": "🔤 Word Challenge",

    "football": "🏈 Football Challenge",
    "basketball": "🏀 Basketball Challenge",
    "baseball": "⚾ Baseball Challenge",
    "boxing": "🥊 Boxing",
    "soccer": "⚽ Soccer Challenge",

    "car_race": "🏎️ Car Race",
    "bike_race": "🏍️ Bike Race",
    "boat_race": "🚤 Boat Race",
    "drag_race": "🏁 Drag Race",
    "street_race": "🏎️ Street Race",

    "detective": "🕵🏾 Detective",
    "murder_mystery": "🔎 Mystery Case",
    "code_breaker": "🔐 Code Breaker",
    "escape": "🚪 Escape Room",
    "investigation": "🔍 Investigation",

    "mma": "🥋 MMA",
    "karate": "🥋 Karate",
    "street_fight": "👊 Street Fight",
    "arena": "⚔️ Arena Battle",
}


# ==========================================================
# GAME COUNTS
#
# IMPORTANT:
# Only count games that are actually registered.
# ==========================================================

GAME_COUNTS = {
    category_id: len(
        CATEGORY_GAMES.get(category_id, [])
    )
    for category_id in GAME_CATEGORIES
}


TOTAL_REGISTERED_GAMES = sum(
    GAME_COUNTS.values()
)


# ==========================================================
# BUILT-IN PLAYABLE GAMES
#
# These games work immediately.
#
# Additional games can be added later without changing
# bot.py.
# ==========================================================

PLAYABLE_GAMES = {
    "reaction",
    "number_guess",
    "high_low",
    "coin_flip",
    "dice_roll",
    "dice_duel",
}


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_game_database():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ==================================================
        # GAME PLAYERS
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                coins INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                games_played INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # ==================================================
        # GAME SCORES
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES game_players(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ==================================================
        # GAME SESSIONS
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                game_data TEXT,
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # ==================================================
        # GAME STATS
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                games_played INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                high_score INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, game_id),
                FOREIGN KEY (user_id)
                    REFERENCES game_players(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ==================================================
        # ACHIEVEMENTS
        # ==================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TEXT NOT NULL,
                UNIQUE(user_id, achievement_id),
                FOREIGN KEY (user_id)
                    REFERENCES game_players(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ==================================================
        # INDEXES
        # ==================================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_game_scores_game_id
            ON game_scores(game_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_game_scores_user_id
            ON game_scores(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_game_sessions_user_id
            ON game_sessions(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_game_sessions_status
            ON game_sessions(status)
            """
        )

        conn.commit()

        logger.info(
            "Game Center database initialized."
        )

    except Exception:

        conn.rollback()

        logger.exception(
            "Game Center database initialization failed."
        )

        raise

    finally:

        conn.close()


# ==========================================================
# ENSURE PLAYER
# ==========================================================

def ensure_game_player(
    user_id,
    username=None,
    display_name=None,
):

    now = datetime.utcnow().isoformat()

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
# AWARD GAME RESULT
# ==========================================================

def record_game_result(
    user_id,
    game_id,
    score=0,
    won=False,
):

    now = datetime.utcnow().isoformat()

    xp_earned = max(
        5,
        int(score / 10),
    )

    coins_earned = (
        10 if won else 3
    )

    conn = get_connection()

    try:

        # --------------------------------------------------
        # Player totals
        # --------------------------------------------------

        conn.execute(
            """
            UPDATE game_players
            SET
                games_played = games_played + 1,
                wins = wins + ?,
                losses = losses + ?,
                xp = xp + ?,
                coins = coins + ?,
                level = 1 + ((xp + ?) / 100),
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                1 if won else 0,
                0 if won else 1,
                xp_earned,
                coins_earned,
                xp_earned,
                now,
                user_id,
            ),
        )

        # --------------------------------------------------
        # Score history
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
        # Individual game stats
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
                    MAX(
                        high_score,
                        excluded.high_score
                    )
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

    finally:

        conn.close()

    return (
        xp_earned,
        coins_earned,
    )


# ==========================================================
# GAME CENTER KEYBOARD
# ==========================================================

def game_center_keyboard():

    keyboard = []

    categories = list(
        GAME_CATEGORIES.items()
    )

    for index in range(
        0,
        len(categories),
        2,
    ):

        row = []

        first_key, first_category = categories[
            index
        ]

        row.append(
            InlineKeyboardButton(
                first_category["name"],
                callback_data=(
                    f"games_category_{first_key}"
                ),
            )
        )

        if index + 1 < len(categories):

            second_key, second_category = categories[
                index + 1
            ]

            row.append(
                InlineKeyboardButton(
                    second_category["name"],
                    callback_data=(
                        f"games_category_{second_key}"
                    ),
                )
            )

        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "👤 My Game Profile",
                callback_data="games_profile",
            ),
            InlineKeyboardButton(
                "🏆 Leaderboards",
                callback_data="games_leaderboards",
            ),
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# ==========================================================
# CATEGORY GAME KEYBOARD
# ==========================================================

def category_game_keyboard(
    category_id,
):

    game_ids = CATEGORY_GAMES.get(
        category_id,
        [],
    )

    keyboard = []

    for game_id in game_ids:

        game_name = GAME_NAMES.get(
            game_id,
            "🎮 Game",
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    game_name,
                    callback_data=(
                        f"games_play_{game_id}"
                    ),
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

    return InlineKeyboardMarkup(
        keyboard
    )


# ==========================================================
# /GAMES
# ==========================================================

async def games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    ensure_game_player(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    text = (
        f"{CATEGORY_NAME}\n\n"
        f"{CATEGORY_DESCRIPTION}\n\n"
        f"🎮 <b>{TOTAL_REGISTERED_GAMES} "
        "games currently listed</b>\n"
        "🪙 Earn AZ Coins\n"
        "⭐ Earn XP\n"
        "🏆 Build your stats\n"
        "🥇 Compete for high scores\n\n"
        "Choose a category below:"
    )

    await message.reply_text(
        text,
        reply_markup=game_center_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# CATEGORY CALLBACK
# ==========================================================

async def games_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    prefix = "games_category_"

    if not data.startswith(prefix):
        return

    category_id = data[
        len(prefix):
    ]

    category = GAME_CATEGORIES.get(
        category_id
    )

    if not category:

        await query.answer(
            "Category not found.",
            show_alert=True,
        )

        return

    count = GAME_COUNTS.get(
        category_id,
        0,
    )

    game_ids = CATEGORY_GAMES.get(
        category_id,
        [],
    )

    text = (
        f"<b>{category['name']}</b>\n\n"
        f"{category['description']}\n\n"
        f"🎮 <b>{count} games listed</b>\n\n"
        "Choose a game:"
    )

    if not game_ids:

        text = (
            f"<b>{category['name']}</b>\n\n"
            f"{category['description']}\n\n"
            "🚧 No games have been added "
            "to this category yet."
        )

    await query.edit_message_text(
        text,
        reply_markup=category_game_keyboard(
            category_id
        ),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME CENTER HOME
# ==========================================================

async def games_home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.edit_message_text(
        (
            f"{CATEGORY_NAME}\n\n"
            f"{CATEGORY_DESCRIPTION}\n\n"
            f"🎮 <b>{TOTAL_REGISTERED_GAMES} "
            "games currently listed</b>\n"
            "🪙 Earn AZ Coins\n"
            "⭐ Earn XP\n"
            "🏆 Build your stats\n"
            "🥇 Compete for high scores\n\n"
            "Choose a category below:"
        ),
        reply_markup=game_center_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# PROFILE
# ==========================================================

async def games_profile_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    ensure_game_player(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    conn = get_connection()

    try:

        player = conn.execute(
            """
            SELECT *
            FROM game_players
            WHERE user_id = ?
            """,
            (user.id,),
        ).fetchone()

    finally:

        conn.close()

    if not player:

        await query.answer(
            "Game profile not found.",
            show_alert=True,
        )

        return

    total_results = (
        player["wins"] +
        player["losses"]
    )

    win_rate = 0

    if total_results > 0:

        win_rate = round(
            (
                player["wins"]
                / total_results
            ) * 100
        )

    text = (
        "👤 <b>MY GAME PROFILE</b>\n\n"
        f"👑 <b>{player['display_name']}</b>\n\n"
        f"⭐ Level: <b>{player['level']}</b>\n"
        f"✨ XP: <b>{player['xp']:,}</b>\n"
        f"🪙 AZ Coins: <b>{player['coins']:,}</b>\n\n"
        f"🎮 Games Played: "
        f"<b>{player['games_played']:,}</b>\n"
        f"🏆 Wins: <b>{player['wins']:,}</b>\n"
        f"💀 Losses: <b>{player['losses']:,}</b>\n"
        f"📊 Win Rate: <b>{win_rate}%</b>"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ]
        ]
    )

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# LEADERBOARDS
# ==========================================================

async def games_leaderboards_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    conn = get_connection()

    try:

        players = conn.execute(
            """
            SELECT
                display_name,
                xp,
                coins,
                wins
            FROM game_players
            ORDER BY xp DESC
            LIMIT 10
            """
        ).fetchall()

    finally:

        conn.close()

    if not players:

        leaderboard_text = (
            "🏆 <b>GAME LEADERBOARD</b>\n\n"
            "No players yet.\n\n"
            "Be the first to play!"
        )

    else:

        lines = [
            "🏆 <b>GAME LEADERBOARD</b>\n"
        ]

        medals = [
            "🥇",
            "🥈",
            "🥉",
        ]

        for index, player in enumerate(
            players,
            start=1,
        ):

            medal = (
                medals[index - 1]
                if index <= 3
                else f"{index}."
            )

            display_name = (
                player["display_name"]
                or "Player"
            )

            lines.append(
                f"{medal} "
                f"<b>{display_name}</b> "
                f"— ⭐ {player['xp']:,} XP"
            )

        leaderboard_text = "\n".join(
            lines
        )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ]
        ]
    )

    await query.edit_message_text(
        leaderboard_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME RESULT SCREEN
# ==========================================================

def game_result_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 Play Again",
                    callback_data="games_play_again",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    )


# ==========================================================
# COIN FLIP
# ==========================================================

async def play_coin_flip(
    query,
    user,
):

    result = random.choice(
        [
            "HEADS",
            "TAILS",
        ]
    )

    score = 100

    xp, coins = record_game_result(
        user.id,
        "coin_flip",
        score=score,
        won=True,
    )

    text = (
        "🪙 <b>COIN FLIP</b>\n\n"
        f"🎲 The coin landed on:\n\n"
        f"<b>🪙 {result}</b>\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_result_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# DICE ROLL
# ==========================================================

async def play_dice_roll(
    query,
    user,
):

    roll = random.randint(
        1,
        6,
    )

    score = roll * 20

    xp, coins = record_game_result(
        user.id,
        "dice_roll",
        score=score,
        won=roll >= 4,
    )

    result = (
        "🏆 You rolled high!"
        if roll >= 4
        else "🎲 Better luck next roll!"
    )

    text = (
        "🎲 <b>DICE ROLL</b>\n\n"
        f"You rolled: <b>{roll}</b>\n\n"
        f"{result}\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_result_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# DICE DUEL
# ==========================================================

async def play_dice_duel(
    query,
    user,
):

    player_roll = random.randint(
        1,
        6,
    )

    bot_roll = random.randint(
        1,
        6,
    )

    if player_roll > bot_roll:
        won = True
        result = "🏆 YOU WIN!"
    elif player_roll < bot_roll:
        won = False
        result = "💀 YOU LOSE!"
    else:
        won = False
        result = "🤝 IT'S A TIE!"

    score = player_roll * 20

    xp, coins = record_game_result(
        user.id,
        "dice_duel",
        score=score,
        won=won,
    )

    text = (
        "🎲 <b>DICE DUEL</b>\n\n"
        f"👤 Your roll: <b>{player_roll}</b>\n"
        f"🤖 Bot roll: <b>{bot_roll}</b>\n\n"
        f"<b>{result}</b>\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_result_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# HIGH / LOW
# ==========================================================

async def play_high_low(
    query,
    user,
):

    first = random.randint(
        1,
        13,
    )

    second = random.randint(
        1,
        13,
    )

    if second > first:
        result = "HIGH"
    elif second < first:
        result = "LOW"
    else:
        result = "TIE"

    won = result != "TIE"

    score = (
        100
        if won
        else 25
    )

    xp, coins = record_game_result(
        user.id,
        "high_low",
        score=score,
        won=won,
    )

    text = (
        "📈 <b>HIGH OR LOW</b>\n\n"
        f"First card: <b>{first}</b>\n"
        f"Second card: <b>{second}</b>\n\n"
        f"Result: <b>{result}</b>\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_result_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# NUMBER GUESS
# ==========================================================

async def play_number_guess(
    query,
    user,
):

    secret = random.randint(
        1,
        10,
    )

    guess = random.randint(
        1,
        10,
    )

    won = (
        secret == guess
    )

    score = (
        100
        if won
        else 10
    )

    xp, coins = record_game_result(
        user.id,
        "number_guess",
        score=score,
        won=won,
    )

    result = (
        "🎯 <b>YOU GUESSED IT!</b>"
        if won
        else "😅 Not this time!"
    )

    text = (
        "🔢 <b>NUMBER GUESS</b>\n\n"
        f"Your guess: <b>{guess}</b>\n"
        f"Secret number: <b>{secret}</b>\n\n"
        f"{result}\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_result_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# REACTION TEST
# ==========================================================

async def play_reaction(
    query,
    user,
):

    reaction_time = random.randint(
        150,
        900,
    )

    score = max(
        10,
        1000 - reaction_time,
    )

    won = (
        reaction_time < 500
    )

    xp, coins = record_game_result(
        user.id,
        "reaction",
        score=score,
        won=won,
    )

    result = (
        "⚡ FAST!"
        if won
        else "🐢 TOO SLOW!"
    )

    text = (
        "⚡ <b>REACTION TEST</b>\n\n"
        f"Reaction time: "
        f"<b>{reaction_time} ms</b>\n\n"
        f"{result}\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_result_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME COMING SOON
# ==========================================================

async def game_coming_soon(
    query,
    game_id,
):

    game_name = GAME_NAMES.get(
        game_id,
        "🎮 Game",
    )

    text = (
        f"🎮 <b>{game_name}</b>\n\n"
        "🚧 <b>COMING SOON</b>\n\n"
        "This game is already registered "
        "in the Melanated AZ Game Center, "
        "but the gameplay is still being built.\n\n"
        "The button is working correctly. "
        "More games will be added as they are completed."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎮 Game Center",
                    callback_data="games_home",
                )
            ]
        ]
    )

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# PLAY GAME CALLBACK
# ==========================================================

async def games_play_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    data = query.data or ""

    # ------------------------------------------------------
    # PLAY AGAIN
    #
    # We cannot know the previous game from this simple
    # callback alone, so return to Game Center.
    # ------------------------------------------------------

    if data == "games_play_again":

        await query.answer()

        await query.edit_message_text(
            (
                "🎮 <b>GAME CENTER</b>\n\n"
                "Choose a game to play:"
            ),
            reply_markup=game_center_keyboard(),
            parse_mode=ParseMode.HTML,
        )

        return

    prefix = "games_play_"

    if not data.startswith(prefix):
        return

    game_id = data[
        len(prefix):
    ]

    ensure_game_player(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    logger.info(
        "Starting game | game=%s | user=%s",
        game_id,
        user.id,
    )

    await query.answer()

    # ------------------------------------------------------
    # TRUTH OR DARE
    #
    # Existing Truth or Dare system handles this game.
    # ------------------------------------------------------

    if game_id == "truth_dare":

        try:

            from truth_dare import (
                truth_dare_menu,
            )

            await truth_dare_menu(
                update,
                context,
            )

        except Exception:

            logger.exception(
                "Could not launch Truth or Dare "
                "from Game Center."
            )

            await query.edit_message_text(
                (
                    "🔥 <b>Truth or Dare</b>\n\n"
                    "⚠️ The Truth or Dare game "
                    "could not be opened."
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Game Center",
                                callback_data="games_home",
                            )
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )

        return

    # ------------------------------------------------------
    # PLAYABLE GAMES
    # ------------------------------------------------------

    if game_id == "coin_flip":

        await play_coin_flip(
            query,
            user,
        )

        return

    if game_id == "dice_roll":

        await play_dice_roll(
            query,
            user,
        )

        return

    if game_id == "dice_duel":

        await play_dice_duel(
            query,
            user,
        )

        return

    if game_id == "high_low":

        await play_high_low(
            query,
            user,
        )

        return

    if game_id == "number_guess":

        await play_number_guess(
            query,
            user,
        )

        return

    if game_id == "reaction":

        await play_reaction(
            query,
            user,
        )

        return

    # ------------------------------------------------------
    # REGISTERED BUT NOT IMPLEMENTED
    # ------------------------------------------------------

    await game_coming_soon(
        query,
        game_id,
    )


# ==========================================================
# INITIALIZE GAME DATABASE
# ==========================================================

initialize_game_database()


# ==========================================================
# END game_center.py
# ==========================================================
