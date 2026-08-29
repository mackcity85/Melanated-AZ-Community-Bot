# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# MELANATED AZ GAME CENTER
#
# Handles:
#   - /games
#   - Categories
#   - Games
#   - Player profiles
#   - Leaderboards
#   - Game database
#   - XP
#   - Coins
#   - Game statistics
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

from games.registry import (
    GAMES,
    get_game,
    get_games_by_category,
    game_count,
    category_game_count,
)


logger = logging.getLogger(
    "melanated_az_bot.games"
)


# ==========================================================
# CATEGORIES
# ==========================================================

GAME_CATEGORIES = {

    "arcade": {
        "name": "🕹️ Arcade",
        "description": "Classic fast-paced arcade games.",
    },

    "outdoor": {
        "name": "🌲 Outdoor",
        "description": "Fishing, hunting, camping and outdoor adventures.",
    },

    "solo": {
        "name": "👤 Solo",
        "description": "Games you can play by yourself.",
    },

    "shooting": {
        "name": "🎯 Action & Shooting",
        "description": "Target, shooting and action challenges.",
    },

    "board": {
        "name": "🎲 Board Games",
        "description": "Classic and strategic board games.",
    },

    "party": {
        "name": "🎉 Party Games",
        "description": "Games designed for the whole group.",
    },

    "trivia": {
        "name": "🧠 Trivia & Brain",
        "description": "Trivia, puzzles and brain challenges.",
    },

    "sports": {
        "name": "🏆 Sports",
        "description": "Sports challenges and competitions.",
    },

    "racing": {
        "name": "🏎️ Racing",
        "description": "Cars, motorcycles, boats and more.",
    },

    "mystery": {
        "name": "🕵🏾 Mystery & Strategy",
        "description": "Mysteries, investigations and strategy.",
    },

    "fighting": {
        "name": "🥊 Fighting",
        "description": "Arena battles and fighting games.",
    },
}


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_game_database():

    conn = get_connection()

    try:

        cursor = conn.cursor()

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
# PLAYER
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
# MAIN GAME CENTER KEYBOARD
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

        first_key, first_category = categories[index]

        first_count = category_game_count(
            first_key
        )

        row.append(
            InlineKeyboardButton(
                f"{first_category['name']} ({first_count})",
                callback_data=(
                    f"games_category_{first_key}"
                ),
            )
        )

        if index + 1 < len(categories):

            second_key, second_category = categories[
                index + 1
            ]

            second_count = category_game_count(
                second_key
            )

            row.append(
                InlineKeyboardButton(
                    f"{second_category['name']} ({second_count})",
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
# CATEGORY KEYBOARD
# ==========================================================

def category_game_keyboard(category_id):

    games = get_games_by_category(
        category_id
    )

    keyboard = []

    for game_id, game in games.items():

        keyboard.append(
            [
                InlineKeyboardButton(
                    game["name"],
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

    total = game_count()

    text = (
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        "Welcome to the Game Center! 👑\n\n"
        f"🎮 <b>{total} Games Available</b>\n"
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

    await query.answer()

    category_id = data[len(prefix):]

    category = GAME_CATEGORIES.get(
        category_id
    )

    if not category:

        await query.answer(
            "Category not found.",
            show_alert=True,
        )

        return

    games = get_games_by_category(
        category_id
    )

    count = len(games)

    text = (
        f"<b>{category['name']}</b>\n\n"
        f"{category['description']}\n\n"
        f"🎮 <b>{count} games available</b>\n\n"
        "Choose a game:"
    )

    if not games:

        text = (
            f"<b>{category['name']}</b>\n\n"
            f"{category['description']}\n\n"
            "🚧 No games are currently enabled "
            "in this category."
        )

    await query.edit_message_text(
        text,
        reply_markup=category_game_keyboard(
            category_id
        ),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# HOME
# ==========================================================

async def games_home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    total = game_count()

    text = (
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        f"🎮 <b>{total} Games Available</b>\n"
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
        return

    total_games = (
        player["wins"] +
        player["losses"]
    )

    win_rate = 0

    if total_games:

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
# LEADERBOARD
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
            "🏆 <b>GAME LEADERBOARD</b>",
            "",
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
# GAME PLAY CALLBACK
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

    await query.answer()

    game_id = data[len(prefix):]

    game = get_game(game_id)

    if not game or not game.get("enabled", False):

        await query.answer(
            "That game is unavailable.",
            show_alert=True,
        )

        return

    ensure_game_player(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    logger.info(
        "Game selected | game=%s | user=%s",
        game_id,
        user.id,
    )

    # ======================================================
    # SPECIAL GAME ROUTING
    #
    # Existing completed game modules can be connected here.
    # ======================================================

    if game_id == "truth_dare":

        try:

            from games.truth_dare import (
                truth_dare_menu,
            )

            await truth_dare_menu(
                update,
                context,
            )

            return

        except Exception:

            logger.exception(
                "Truth or Dare game failed."
            )

    if game_id == "would_you_rather":

        try:

            from games.would_you_rather import (
                would_you_rather,
            )

            await would_you_rather(
                update,
                context,
            )

            return

        except Exception:

            logger.exception(
                "Would You Rather failed."
            )

    # ======================================================
    # GAME SCREEN
    # ======================================================

    text = (
        f"🎮 <b>{game['name']}</b>\n\n"
        f"{game['description']}\n\n"
        "🚧 <b>Game module ready to connect.</b>\n\n"
        "This game is registered in the Game Center "
        "and can now be connected to its gameplay module.\n\n"
        "⭐ XP\n"
        "🪙 AZ Coins\n"
        "🏆 Scores\n"
        "🎖️ Achievements"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "▶️ PLAY",
                    callback_data=(
                        f"games_start_{game_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Category",
                    callback_data=(
                        f"games_category_{game['category']}"
                    ),
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

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# GAME START CALLBACK
# ==========================================================

async def games_start_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    data = query.data or ""

    prefix = "games_start_"

    if not data.startswith(prefix):
        return

    await query.answer()

    game_id = data[len(prefix):]

    game = get_game(game_id)

    if not game:

        await query.answer(
            "Game not found.",
            show_alert=True,
        )

        return

    # ------------------------------------------------------
    # Temporary gameplay launcher.
    #
    # Individual game modules will be connected here in
    # batches.
    # ------------------------------------------------------

    text = (
        f"🎮 <b>{game['name']}</b>\n\n"
        "🚧 <b>Gameplay module is next.</b>\n\n"
        "The game is installed in the Game Center.\n"
        "The next batch connects the actual gameplay."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=(
                        f"games_category_{game['category']}"
                    ),
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

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

# Intentionally initialize here because bot.py also calls
# initialize_game_database() during startup.
#
# The function uses CREATE IF NOT EXISTS, so this is safe.

initialize_game_database()


# ==========================================================
# END game_center.py
# ==========================================================
