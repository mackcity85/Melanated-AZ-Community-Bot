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
#   - Game database foundation
#   - XP / Coins foundation
#
# ==========================================================

import logging
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
# GAME LISTS
#
# These are the games currently exposed in the Game Center.
#
# More games can be added without changing bot.py.
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
# GAME COUNTS
# ==========================================================

GAME_COUNTS = {
    "arcade": 10,
    "outdoor": 10,
    "solo": 10,
    "shooting": 10,
    "board": 10,
    "party": 10,
    "trivia": 10,
    "sports": 10,
    "racing": 10,
    "mystery": 10,
    "fighting": 20,
}


TOTAL_GAMES = sum(
    GAME_COUNTS.values()
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

    count = GAME_COUNTS.get(
        category_id,
        0,
    )

    games = GAMES.get(
        category_id,
        [],
    )

    text = (
        f"<b>{category['name']}</b>\n\n"
        f"{category['description']}\n\n"
        f"🎮 <b>{count} games available</b>\n\n"
        "Choose a game:"
    )

    # ------------------------------------------------------
    # If this category has no registered games yet.
    # ------------------------------------------------------

    if not games:

        text = (
            f"<b>{category['name']}</b>\n\n"
            f"{category['description']}\n\n"
            f"🎮 <b>{count} games planned</b>\n\n"
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
# GAME PROFILE
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

    win_rate = 0

    total_games = (
        player["wins"] +
        player["losses"]
    )

    if total_games > 0:

        win_rate = round(
            (
                player["wins"]
                / total_games
            ) * 100
        )

    text = (
        "👤 <b>MY GAME PROFILE</b>\n\n"
        f"👑 <b>{player['display_name']}</b>\n\n"
        f"⭐ Level: <b>{player['level']}</b>\n"
        f"✨ XP: <b>{player['xp']:,}</b>\n"
        f"🪙 AZ Coins: <b>{player['coins']:,}</b>\n\n"
        f"🎮 Games Played: <b>{player['games_played']:,}</b>\n"
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
                medal = medals[index - 1]
            else:
                medal = f"{index}."

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
# GAME PLAY CALLBACK
#
# This is the central entry point for actual games.
#
# For now it provides a clean placeholder for games that
# have not yet been implemented.
#
# ==========================================================

async def games_play_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    await query.answer()

    data = query.data or ""

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

    # ------------------------------------------------------
    # GAME ROUTING
    #
    # Actual games will be plugged into this section.
    # ------------------------------------------------------

    game_names = {

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
        "boxing": "🥊 Boxing Challenge",
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

    game_name = game_names.get(
        game_id,
        "🎮 Game",
    )

    # ------------------------------------------------------
    # TEMPORARY PLAY SCREEN
    #
    # This will be replaced as each actual game is built.
    # ------------------------------------------------------

    text = (
        f"🎮 <b>{game_name}</b>\n\n"
        "🚧 <b>Game coming next!</b>\n\n"
        "The Game Center is ready for this game, "
        "but the actual gameplay is being installed.\n\n"
        "🪙 AZ Coins\n"
        "⭐ XP\n"
        "🏆 Scores\n"
        "🎖️ Achievements\n\n"
        "More games are coming!"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    )

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# INITIALIZE GAME DATABASE
# ==========================================================

initialize_game_database()


# ==========================================================
# END game_center.py
# ==========================================================
