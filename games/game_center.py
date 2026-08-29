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
#   - Persistent game database
#   - XP
#   - AZ Coins
#   - Game statistics
#   - Achievements foundation
#
# PLAYABLE GAMES:
#   - Reaction Test
#   - Number Guess
#   - High or Low
#   - Coin Flip
#   - Dice Roll
#
# Other registered games display a "coming next" screen
# until their individual game engine is installed.
# ==========================================================

import logging
import random
from datetime import datetime

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
            "Fishing, camping, hiking and outdoor adventures."
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
# REGISTERED GAMES
#
# These are the games currently displayed by the Game Center.
#
# A game can appear in more than one category.
# ==========================================================

GAMES = {

    "arcade": [
        ("reaction", "⚡ Reaction Test"),
        ("number_guess", "🔢 Number Guess"),
        ("high_low", "📈 High or Low"),
        ("coin_flip", "🪙 Coin Flip"),
        ("dice_roll", "🎲 Dice Roll"),
    ],

    "outdoor": [
        ("fishing", "🎣 Fishing"),
        ("camping", "🏕️ Camping"),
        ("hiking", "🥾 Hiking Challenge"),
        ("hunting", "🏹 Hunting Challenge"),
        ("survival", "🔥 Survival"),
    ],

    "solo": [
        ("number_guess", "🔢 Number Guess"),
        ("coin_flip", "🪙 Coin Flip"),
        ("dice_roll", "🎲 Dice Roll"),
        ("high_low", "📈 High or Low"),
        ("reaction", "⚡ Reaction Test"),
    ],

    "shooting": [
        ("target", "🎯 Target Practice"),
        ("quick_shot", "🔫 Quick Shot"),
        ("bullseye", "🎯 Bullseye"),
        ("accuracy", "🏹 Accuracy"),
        ("sniper", "🔭 Sniper Challenge"),
    ],

    "board": [
        ("dice_roll", "🎲 Dice Roll"),
        ("high_low", "📈 High or Low"),
        ("number_guess", "🔢 Number Guess"),
        ("strategy", "♟️ Strategy"),
        ("dice_duel", "🎲 Dice Duel"),
    ],

    "party": [
        ("coin_flip", "🪙 Coin Flip"),
        ("dice_roll", "🎲 Dice Roll"),
        ("truth_dare", "🔥 Truth or Dare"),
        ("high_low", "📈 High or Low"),
        ("reaction", "⚡ Reaction Test"),
    ],

    "trivia": [
        ("general_trivia", "🧠 General Trivia"),
        ("music_trivia", "🎵 Music Trivia"),
        ("sports_trivia", "🏆 Sports Trivia"),
        ("movie_trivia", "🎬 Movie Trivia"),
        ("word_challenge", "🔤 Word Challenge"),
    ],

    "sports": [
        ("football", "🏈 Football Challenge"),
        ("basketball", "🏀 Basketball Challenge"),
        ("baseball", "⚾ Baseball Challenge"),
        ("boxing", "🥊 Boxing Challenge"),
        ("soccer", "⚽ Soccer Challenge"),
    ],

    "racing": [
        ("car_race", "🏎️ Car Race"),
        ("bike_race", "🏍️ Bike Race"),
        ("boat_race", "🚤 Boat Race"),
        ("drag_race", "🏁 Drag Race"),
        ("street_race", "🏎️ Street Race"),
    ],

    "mystery": [
        ("detective", "🕵🏾 Detective"),
        ("murder_mystery", "🔎 Mystery Case"),
        ("code_breaker", "🔐 Code Breaker"),
        ("escape", "🚪 Escape Room"),
        ("investigation", "🔍 Investigation"),
    ],

    "fighting": [
        ("boxing", "🥊 Boxing"),
        ("mma", "🥋 MMA"),
        ("karate", "🥋 Karate"),
        ("street_fight", "👊 Street Fight"),
        ("arena", "⚔️ Arena Battle"),
    ],
}


# ==========================================================
# PLAYABLE GAMES
# ==========================================================

PLAYABLE_GAMES = {
    "reaction",
    "number_guess",
    "high_low",
    "coin_flip",
    "dice_roll",
}


# ==========================================================
# GAME NAME LOOKUP
# ==========================================================

GAME_NAMES = {}


for category_games in GAMES.values():

    for game_id, game_name in category_games:

        GAME_NAMES[game_id] = game_name


# ==========================================================
# GAME COUNTS
#
# Counts the games actually registered in each category.
# ==========================================================

GAME_COUNTS = {
    category_id: len(category_games)
    for category_id, category_games in GAMES.items()
}


# ==========================================================
# TOTAL UNIQUE GAMES
#
# Some games appear in multiple categories.
# Count them only once.
# ==========================================================

TOTAL_GAMES = len(
    GAME_NAMES
)


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
# PLAYER LEVEL
# ==========================================================

def calculate_level(xp):
    """
    Calculate player level from XP.

    Every 500 XP = one additional level.
    """

    try:

        xp = int(xp)

    except (TypeError, ValueError):

        xp = 0

    return max(
        1,
        (xp // 500) + 1,
    )


# ==========================================================
# CREATE / UPDATE PLAYER
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
# REWARD PLAYER
# ==========================================================

def reward_player(
    user_id,
    xp_reward,
    coin_reward,
    won=False,
    lost=False,
):

    now = datetime.utcnow().isoformat()

    conn = get_connection()

    try:

        player = conn.execute(
            """
            SELECT
                xp,
                coins
            FROM game_players
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not player:

            raise RuntimeError(
                "Game player does not exist."
            )

        new_xp = (
            player["xp"]
            + xp_reward
        )

        new_coins = (
            player["coins"]
            + coin_reward
        )

        new_level = calculate_level(
            new_xp
        )

        wins_increment = 1 if won else 0
        losses_increment = 1 if lost else 0

        conn.execute(
            """
            UPDATE game_players
            SET
                xp = ?,
                coins = ?,
                level = ?,
                wins = wins + ?,
                losses = losses + ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                new_xp,
                new_coins,
                new_level,
                wins_increment,
                losses_increment,
                now,
                user_id,
            ),
        )

        conn.commit()

        return {
            "xp": new_xp,
            "coins": new_coins,
            "level": new_level,
        }

    except Exception:

        conn.rollback()

        logger.exception(
            "Could not reward game player."
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
    lost=False,
):

    now = datetime.utcnow().isoformat()

    conn = get_connection()

    try:

        # --------------------------------------------------
        # PLAYER TOTALS
        # --------------------------------------------------

        conn.execute(
            """
            UPDATE game_players
            SET
                games_played = games_played + 1,
                wins = wins + ?,
                losses = losses + ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                1 if won else 0,
                1 if lost else 0,
                now,
                user_id,
            ),
        )

        # --------------------------------------------------
        # SCORE
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
        # GAME STATS
        # --------------------------------------------------

        existing = conn.execute(
            """
            SELECT high_score
            FROM game_stats
            WHERE user_id = ?
              AND game_id = ?
            """,
            (
                user_id,
                game_id,
            ),
        ).fetchone()

        if existing:

            high_score = max(
                existing["high_score"],
                score,
            )

            conn.execute(
                """
                UPDATE game_stats
                SET
                    games_played =
                        games_played + 1,
                    wins =
                        wins + ?,
                    losses =
                        losses + ?,
                    high_score = ?
                WHERE user_id = ?
                  AND game_id = ?
                """,
                (
                    1 if won else 0,
                    1 if lost else 0,
                    high_score,
                    user_id,
                    game_id,
                ),
            )

        else:

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
                """,
                (
                    user_id,
                    game_id,
                    1 if won else 0,
                    1 if lost else 0,
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

    games = GAMES.get(
        category_id,
        [],
    )

    keyboard = []

    for game_id, game_name in games:

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
# GAME BACK BUTTON
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
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        "Welcome to the Game Center! 👑\n\n"
        f"🎮 <b>{TOTAL_GAMES} Games</b>\n"
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

    await query.answer()

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

    games = GAMES.get(
        category_id,
        [],
    )

    count = len(games)

    text = (
        f"<b>{category['name']}</b>\n\n"
        f"{category['description']}\n\n"
        f"🎮 <b>{count} games</b>\n\n"
        "Choose a game:"
    )

    if not games:

        text = (
            f"<b>{category['name']}</b>\n\n"
            f"{category['description']}\n\n"
            "🚧 Games are being added."
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

    await query.answer()

    text = (
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        f"🎮 <b>{TOTAL_GAMES} Games</b>\n"
        "🪙 Earn AZ Coins\n"
        "⭐ Earn XP\n"
        "🏆 Build your stats\n"
        "🥇 Compete for high scores\n\n"
        "Choose a category below:"
    )

    await query.edit_message_text(
        text,
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

    await query.answer()

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

    total_games = (
        player["wins"]
        + player["losses"]
    )

    if total_games > 0:

        win_rate = round(
            (
                player["wins"]
                / total_games
            ) * 100
        )

    else:

        win_rate = 0

    text = (
        "👤 <b>MY GAME PROFILE</b>\n\n"
        f"👑 <b>{player['display_name'] or 'Player'}</b>\n\n"
        f"⭐ Level: <b>{player['level']}</b>\n"
        f"✨ XP: <b>{player['xp']:,}</b>\n"
        f"🪙 AZ Coins: <b>{player['coins']:,}</b>\n\n"
        f"🎮 Games Played: <b>{player['games_played']:,}</b>\n"
        f"🏆 Wins: <b>{player['wins']:,}</b>\n"
        f"💀 Losses: <b>{player['losses']:,}</b>\n"
        f"📊 Win Rate: <b>{win_rate}%</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_back_keyboard(),
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

    await query.answer()

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

            if index <= 3:

                medal = medals[
                    index - 1
                ]

            else:

                medal = f"{index}."

            display_name = (
                player["display_name"]
                or "Player"
            )

            lines.append(
                f"{medal} "
                f"<b>{display_name}</b> "
                f"— ⭐ {player['xp']:,} XP "
                f"🪙 {player['coins']:,}"
            )

        leaderboard_text = "\n".join(
            lines
        )

    await query.edit_message_text(
        leaderboard_text,
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME: COIN FLIP
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

    xp = 25
    coins = 10

    record_game_result(
        user.id,
        "coin_flip",
        score=100,
        won=True,
        lost=False,
    )

    reward = reward_player(
        user.id,
        xp_reward=xp,
        coin_reward=coins,
        won=False,
        lost=False,
    )

    text = (
        "🪙 <b>COIN FLIP</b>\n\n"
        f"The coin landed on:\n\n"
        f"🪙 <b>{result}</b>\n\n"
        "🎉 You played!\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins\n\n"
        f"⭐ Total XP: <b>{reward['xp']:,}</b>\n"
        f"🪙 Total Coins: <b>{reward['coins']:,}</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME: DICE ROLL
# ==========================================================

async def play_dice_roll(
    query,
    user,
):

    roll = random.randint(
        1,
        6,
    )

    score = roll * 10

    xp = 20 + roll * 5
    coins = roll * 2

    record_game_result(
        user.id,
        "dice_roll",
        score=score,
        won=roll >= 4,
        lost=roll <= 2,
    )

    reward = reward_player(
        user.id,
        xp_reward=xp,
        coin_reward=coins,
        won=False,
        lost=False,
    )

    if roll == 6:

        result_text = (
            "🔥 <b>CRITICAL ROLL!</b>"
        )

    elif roll >= 4:

        result_text = (
            "🎉 Great roll!"
        )

    elif roll <= 2:

        result_text = (
            "😅 Better luck next roll!"
        )

    else:

        result_text = (
            "👍 Solid roll!"
        )

    text = (
        "🎲 <b>DICE ROLL</b>\n\n"
        f"🎲 You rolled: <b>{roll}</b>\n\n"
        f"{result_text}\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins\n\n"
        f"⭐ Total XP: <b>{reward['xp']:,}</b>\n"
        f"🪙 Total Coins: <b>{reward['coins']:,}</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME: NUMBER GUESS
# ==========================================================

async def start_number_guess(
    query,
    context,
):

    number = random.randint(
        1,
        10,
    )

    context.user_data[
        "game_number_guess"
    ] = number

    keyboard = []

    row = []

    for number_option in range(
        1,
        11,
    ):

        row.append(
            InlineKeyboardButton(
                str(number_option),
                callback_data=(
                    f"games_guess_{number_option}"
                ),
            )
        )

        if len(row) == 5:

            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    )

    text = (
        "🔢 <b>NUMBER GUESS</b>\n\n"
        "I'm thinking of a number from "
        "<b>1 to 10</b>.\n\n"
        "Can you guess it?"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# NUMBER GUESS CALLBACK
# ==========================================================

async def number_guess_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    await query.answer()

    data = query.data or ""

    try:

        guess = int(
            data.replace(
                "games_guess_",
                "",
            )
        )

    except ValueError:

        await query.answer(
            "Invalid guess.",
            show_alert=True,
        )

        return

    target = context.user_data.get(
        "game_number_guess"
    )

    if target is None:

        await query.answer(
            "That game has expired. Start a new one.",
            show_alert=True,
        )

        return

    context.user_data.pop(
        "game_number_guess",
        None,
    )

    won = guess == target

    if won:

        score = 100
        xp = 100
        coins = 50

        result = (
            "🎉 <b>YOU GOT IT!</b>"
        )

        record_game_result(
            user.id,
            "number_guess",
            score=score,
            won=True,
            lost=False,
        )

    else:

        score = 0
        xp = 15
        coins = 5

        result = (
            "❌ Not this time!"
        )

        record_game_result(
            user.id,
            "number_guess",
            score=score,
            won=False,
            lost=True,
        )

    reward = reward_player(
        user.id,
        xp_reward=xp,
        coin_reward=coins,
        won=False,
        lost=False,
    )

    text = (
        "🔢 <b>NUMBER GUESS</b>\n\n"
        f"You guessed: <b>{guess}</b>\n"
        f"The number was: <b>{target}</b>\n\n"
        f"{result}\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins\n\n"
        f"⭐ Total XP: <b>{reward['xp']:,}</b>\n"
        f"🪙 Total Coins: <b>{reward['coins']:,}</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME: HIGH OR LOW
# ==========================================================

async def start_high_low(
    query,
    context,
):

    current = random.randint(
        2,
        11,
    )

    next_card = random.randint(
        1,
        13,
    )

    context.user_data[
        "game_high_low"
    ] = {
        "current": current,
        "next": next_card,
    }

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬆️ HIGHER",
                    callback_data="games_high",
                ),
                InlineKeyboardButton(
                    "⬇️ LOWER",
                    callback_data="games_low",
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

    text = (
        "📈 <b>HIGH OR LOW</b>\n\n"
        f"The current card is: "
        f"<b>{current}</b>\n\n"
        "Will the next card be higher "
        "or lower?"
    )

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# HIGH / LOW CALLBACK
# ==========================================================

async def high_low_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    await query.answer()

    choice = query.data

    game_data = context.user_data.get(
        "game_high_low"
    )

    if not game_data:

        await query.answer(
            "That game has expired. Start a new one.",
            show_alert=True,
        )

        return

    context.user_data.pop(
        "game_high_low",
        None,
    )

    current = game_data[
        "current"
    ]

    next_card = game_data[
        "next"
    ]

    if next_card > current:

        actual = "games_high"

    elif next_card < current:

        actual = "games_low"

    else:

        actual = "tie"

    won = (
        choice == actual
    )

    if actual == "tie":

        xp = 30
        coins = 10

        result = (
            "🤝 <b>TIE!</b>"
        )

        won = False
        lost = False

    elif won:

        xp = 75
        coins = 35

        result = (
            "🎉 <b>YOU WIN!</b>"
        )

        lost = False

    else:

        xp = 10
        coins = 3

        result = (
            "❌ <b>YOU LOSE!</b>"
        )

        lost = True

    record_game_result(
        user.id,
        "high_low",
        score=100 if won else 0,
        won=won,
        lost=lost,
    )

    reward = reward_player(
        user.id,
        xp_reward=xp,
        coin_reward=coins,
        won=False,
        lost=False,
    )

    text = (
        "📈 <b>HIGH OR LOW</b>\n\n"
        f"Current card: <b>{current}</b>\n"
        f"Next card: <b>{next_card}</b>\n\n"
        f"{result}\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins\n\n"
        f"⭐ Total XP: <b>{reward['xp']:,}</b>\n"
        f"🪙 Total Coins: <b>{reward['coins']:,}</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME: REACTION TEST
# ==========================================================

async def start_reaction_test(
    query,
    context,
):

    context.user_data[
        "reaction_started"
    ] = True

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⚡ TAP NOW!",
                    callback_data="games_react",
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

    text = (
        "⚡ <b>REACTION TEST</b>\n\n"
        "Get ready...\n\n"
        "When you're ready, hit the button!\n\n"
        "🏆 Faster reactions = higher scores."
    )

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# REACTION CALLBACK
# ==========================================================

async def reaction_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    await query.answer()

    started = context.user_data.get(
        "reaction_started"
    )

    if not started:

        await query.answer(
            "Start a new reaction test.",
            show_alert=True,
        )

        return

    context.user_data.pop(
        "reaction_started",
        None,
    )

    # ------------------------------------------------------
    # Simulated reaction score.
    #
    # A future version can use timestamps between messages
    # for a more precise reaction-time game.
    # ------------------------------------------------------

    reaction_time = random.randint(
        180,
        900,
    )

    score = max(
        10,
        1000 - reaction_time,
    )

    xp = max(
        10,
        score // 5,
    )

    coins = max(
        2,
        score // 20,
    )

    record_game_result(
        user.id,
        "reaction",
        score=score,
        won=score >= 500,
        lost=score < 300,
    )

    reward = reward_player(
        user.id,
        xp_reward=xp,
        coin_reward=coins,
        won=False,
        lost=False,
    )

    text = (
        "⚡ <b>REACTION TEST</b>\n\n"
        f"⏱️ Reaction: <b>{reaction_time} ms</b>\n"
        f"🏆 Score: <b>{score}</b>\n\n"
        f"⭐ +{xp} XP\n"
        f"🪙 +{coins} AZ Coins\n\n"
        f"⭐ Total XP: <b>{reward['xp']:,}</b>\n"
        f"🪙 Total Coins: <b>{reward['coins']:,}</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME PLAY CALLBACK
#
# Central entry point for all Game Center games.
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

    prefix = "games_play_"

    if not data.startswith(prefix):
        return

    game_id = data[
        len(prefix):
    ]

    logger.info(
        "Starting Game Center game: %s | user=%s",
        game_id,
        user.id,
    )

    ensure_game_player(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    try:

        await query.answer()

    except Exception:

        pass

    # ======================================================
    # PLAYABLE GAME ROUTING
    # ======================================================

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

    if game_id == "number_guess":

        await start_number_guess(
            query,
            context,
        )

        return

    if game_id == "high_low":

        await start_high_low(
            query,
            context,
        )

        return

    if game_id == "reaction":

        await start_reaction_test(
            query,
            context,
        )

        return

    # ======================================================
    # NOT YET IMPLEMENTED
    # ======================================================

    game_name = GAME_NAMES.get(
        game_id,
        "🎮 Game",
    )

    text = (
        f"🎮 <b>{game_name}</b>\n\n"
        "🚧 <b>Game coming next!</b>\n\n"
        "This game is registered in the Game Center "
        "and will be playable when its game engine "
        "is installed.\n\n"
        "🪙 AZ Coins\n"
        "⭐ XP\n"
        "🏆 Scores\n"
        "🎖️ Achievements\n\n"
        "More games are being added!"
    )

    await query.edit_message_text(
        text,
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME CALLBACK ROUTER
#
# Handles callbacks created by the individual games.
# ==========================================================

async def games_gameplay_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    try:

        if data.startswith(
            "games_guess_"
        ):

            await number_guess_callback(
                update,
                context,
            )

            return

        if data in (
            "games_high",
            "games_low",
        ):

            await high_low_callback(
                update,
                context,
            )

            return

        if data == "games_react":

            await reaction_callback(
                update,
                context,
            )

            return

    except Exception:

        logger.exception(
            "Game gameplay callback failed."
        )

        try:

            await query.answer(
                "⚠️ Game action failed.",
                show_alert=True,
            )

        except Exception:

            pass


# ==========================================================
# STARTUP
# ==========================================================

initialize_game_database()


# ==========================================================
# END game_center.py
# ==========================================================
