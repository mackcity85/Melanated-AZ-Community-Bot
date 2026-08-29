# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# GAME CENTER MENU / CALLBACK ROUTER
#
# Handles:
#   /games
#   games_home
#   games_category_*
#   games_profile
#   games_leaderboards
#   games_play_*
#   games_react
#   game_*
#
# Actual gameplay is handled by games.py.
#
# ==========================================================

import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .games import (
    GAME_NAMES,
    play_game,
    games_callback_router,
    initialize_game_database,
    get_player_stats,
    get_leaderboard_by_xp,
    get_leaderboard_by_coins,
    get_leaderboard_by_games,
    get_leaderboard_by_wins,
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
        "title": "🕹️ ARCADE",
        "games": [
            "reaction",
            "number_guess",
            "high_low",
            "coin_flip",
            "dice_roll",
        ],
    },

    "outdoor": {
        "title": "🌲 OUTDOOR",
        "games": [
            "fishing",
            "camping",
            "hiking",
            "hunting",
            "survival",
        ],
    },

    "shooting": {
        "title": "🎯 SHOOTING",
        "games": [
            "target",
            "quick_shot",
            "bullseye",
            "accuracy",
            "sniper",
        ],
    },

    "board": {
        "title": "♟️ BOARD",
        "games": [
            "strategy",
            "dice_duel",
        ],
    },

    "party": {
        "title": "🔥 PARTY",
        "games": [
            "truth_dare",
        ],
    },

    "trivia": {
        "title": "🧠 TRIVIA",
        "games": [
            "general_trivia",
            "music_trivia",
            "sports_trivia",
            "movie_trivia",
            "word_challenge",
        ],
    },

    "sports": {
        "title": "🏆 SPORTS",
        "games": [
            "football",
            "basketball",
            "baseball",
            "boxing",
            "soccer",
        ],
    },

    "racing": {
        "title": "🏎️ RACING",
        "games": [
            "car_race",
            "bike_race",
            "boat_race",
            "drag_race",
            "street_race",
        ],
    },

    "mystery": {
        "title": "🕵🏾 MYSTERY",
        "games": [
            "detective",
            "murder_mystery",
            "code_breaker",
            "escape",
            "investigation",
        ],
    },

    "fighting": {
        "title": "🥊 FIGHTING",
        "games": [
            "mma",
            "karate",
            "street_fight",
            "arena",
        ],
    },
}


# ==========================================================
# CATEGORY DISPLAY ORDER
# ==========================================================

CATEGORY_ORDER = [

    "arcade",
    "outdoor",
    "shooting",
    "board",
    "party",
    "trivia",
    "sports",
    "racing",
    "mystery",
    "fighting",

]


# ==========================================================
# CATEGORY BUTTONS
# ==========================================================

CATEGORY_BUTTONS = {

    "arcade": "🕹️ Arcade",
    "outdoor": "🌲 Outdoor",
    "shooting": "🎯 Shooting",
    "board": "♟️ Board",
    "party": "🔥 Party",
    "trivia": "🧠 Trivia",
    "sports": "🏆 Sports",
    "racing": "🏎️ Racing",
    "mystery": "🕵🏾 Mystery",
    "fighting": "🥊 Fighting",

}


# ==========================================================
# MAIN GAME CENTER KEYBOARD
# ==========================================================

def games_home_keyboard():
    """
    Build the main Game Center keyboard.
    """

    rows = []

    for index in range(
        0,
        len(CATEGORY_ORDER),
        2,
    ):

        row = []

        first = CATEGORY_ORDER[
            index
        ]

        row.append(
            InlineKeyboardButton(
                CATEGORY_BUTTONS[first],
                callback_data=(
                    f"games_category_{first}"
                ),
            )
        )

        if index + 1 < len(
            CATEGORY_ORDER
        ):

            second = CATEGORY_ORDER[
                index + 1
            ]

            row.append(
                InlineKeyboardButton(
                    CATEGORY_BUTTONS[second],
                    callback_data=(
                        f"games_category_{second}"
                    ),
                )
            )

        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "👤 My Profile",
                callback_data="games_profile",
            ),
            InlineKeyboardButton(
                "🏆 Leaderboards",
                callback_data="games_leaderboards",
            ),
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def category_keyboard(category):
    """
    Build keyboard for a selected category.
    """

    category_data = GAME_CATEGORIES.get(
        category
    )

    if not category_data:

        return games_home_keyboard()

    game_ids = category_data[
        "games"
    ]

    rows = []

    for index in range(
        0,
        len(game_ids),
        2,
    ):

        row = []

        first_game = game_ids[
            index
        ]

        row.append(
            InlineKeyboardButton(
                GAME_NAMES.get(
                    first_game,
                    first_game,
                ),
                callback_data=(
                    f"games_play_{first_game}"
                ),
            )
        )

        if index + 1 < len(
            game_ids
        ):

            second_game = game_ids[
                index + 1
            ]

            row.append(
                InlineKeyboardButton(
                    GAME_NAMES.get(
                        second_game,
                        second_game,
                    ),
                    callback_data=(
                        f"games_play_{second_game}"
                    ),
                )
            )

        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ==========================================================
# /GAMES COMMAND
# ==========================================================

async def games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    try:

        initialize_game_database()

    except Exception:

        logger.exception(
            "Could not initialize Game Center database."
        )

    text = (
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        "Welcome to the Game Center!\n\n"
        "Choose a category below and pick a game.\n\n"
        "🏆 Play games\n"
        "⭐ Earn XP\n"
        "🪙 Earn AZ Coins\n"
        "📊 Build your game stats!"
    )

    await message.reply_text(
        text,
        reply_markup=games_home_keyboard(),
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

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Could not answer Game Center home callback.",
            exc_info=True,
        )

    await query.edit_message_text(
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        "Choose a category below and pick a game.\n\n"
        "🏆 Play games\n"
        "⭐ Earn XP\n"
        "🪙 Earn AZ Coins\n"
        "📊 Build your game stats!",
        reply_markup=games_home_keyboard(),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# CATEGORY CALLBACK
# ==========================================================

async def games_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category: str | None = None,
):

    query = update.callback_query

    if not query:
        return

    if category is None:

        data = query.data or ""

        prefix = (
            "games_category_"
        )

        if not data.startswith(
            prefix
        ):

            await query.answer(
                "Category not found.",
                show_alert=True,
            )

            return

        category = data[
            len(prefix):
        ]

    if category not in GAME_CATEGORIES:

        await query.answer(
            "Category not found.",
            show_alert=True,
        )

        logger.warning(
            "Unknown Game Center category: %s",
            category,
        )

        return

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Could not answer category callback.",
            exc_info=True,
        )

    category_data = GAME_CATEGORIES[
        category
    ]

    await query.edit_message_text(
        f"{category_data['title']}\n\n"
        "Choose a game:",
        reply_markup=category_keyboard(
            category
        ),
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

    if not query:
        return

    user = update.effective_user

    if not user:

        await query.answer(
            "User information unavailable.",
            show_alert=True,
        )

        return

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Could not answer profile callback.",
            exc_info=True,
        )

    initialize_game_database()

    # Make sure the player exists.

    from .games import ensure_player

    ensure_player(
        user_id=user.id,
        username=user.username,
        display_name=user.full_name,
    )

    stats = get_player_stats(
        user.id
    )

    if not stats:

        await query.answer(
            "Unable to load your profile.",
            show_alert=True,
        )

        return

    display_name = (
        stats["display_name"]
        or user.first_name
        or "Player"
    )

    username = (
        f"@{stats['username']}"
        if stats["username"]
        else "No username"
    )

    games_played = stats[
        "games_played"
    ]

    wins = stats[
        "wins"
    ]

    losses = stats[
        "losses"
    ]

    xp = stats[
        "xp"
    ]

    coins = stats[
        "coins"
    ]

    level = stats[
        "level"
    ]

    text = (
        "👤 <b>GAME CENTER PROFILE</b>\n\n"
        f"Player: <b>{display_name}</b>\n"
        f"Username: {username}\n\n"
        f"🏅 Level: <b>{level}</b>\n"
        f"⭐ XP: <b>{xp}</b>\n"
        f"🪙 AZ Coins: <b>{coins}</b>\n\n"
        f"🎮 Games Played: <b>{games_played}</b>\n"
        f"🥇 Wins: <b>{wins}</b>\n"
        f"💔 Losses: <b>{losses}</b>"
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
# FORMAT LEADERBOARD
# ==========================================================

def format_leaderboard(
    title,
    rows,
    value_column,
    suffix="",
):

    lines = [
        title,
        "",
    ]

    if not rows:

        lines.append(
            "No players yet."
        )

        return "\n".join(
            lines
        )

    medals = [
        "🥇",
        "🥈",
        "🥉",
    ]

    for index, row in enumerate(
        rows,
        start=1,
    ):

        name = (
            row["display_name"]
            or row["username"]
            or "Player"
        )

        value = row[
            value_column
        ]

        if index <= 3:

            prefix = medals[
                index - 1
            ]

        else:

            prefix = (
                f"{index}."
            )

        lines.append(
            f"{prefix} <b>{name}</b> — "
            f"{value}{suffix}"
        )

    return "\n".join(
        lines
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

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Could not answer leaderboard callback.",
            exc_info=True,
        )

    xp_rows = (
        get_leaderboard_by_xp()
    )

    coin_rows = (
        get_leaderboard_by_coins()
    )

    game_rows = (
        get_leaderboard_by_games()
    )

    win_rows = (
        get_leaderboard_by_wins()
    )

    text = (
        "🏆 <b>GAME CENTER LEADERBOARDS</b>\n\n"

        + format_leaderboard(
            "⭐ <b>TOP XP</b>",
            xp_rows,
            "xp",
        )

        + "\n\n"

        + format_leaderboard(
            "🪙 <b>TOP AZ COINS</b>",
            coin_rows,
            "coins",
        )

        + "\n\n"

        + format_leaderboard(
            "🎮 <b>MOST GAMES</b>",
            game_rows,
            "games_played",
        )

        + "\n\n"

        + format_leaderboard(
            "🥇 <b>MOST WINS</b>",
            win_rows,
            "wins",
        )
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
# START GAME CALLBACK
# ==========================================================

async def games_play_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_id: str | None = None,
):

    query = update.callback_query

    if not query:
        return

    if game_id is None:

        data = query.data or ""

        prefix = (
            "games_play_"
        )

        if not data.startswith(
            prefix
        ):

            await query.answer(
                "Game not found.",
                show_alert=True,
            )

            return

        game_id = data[
            len(prefix):
        ]

    if game_id not in GAME_NAMES:

        await query.answer(
            "Game not found.",
            show_alert=True,
        )

        logger.warning(
            "Unknown Game Center game: %s",
            game_id,
        )

        return

    logger.info(
        "Starting Game Center game: %s | user=%s",
        game_id,
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Game start callback answer failed.",
            exc_info=True,
        )

    try:

        await play_game(
            update,
            context,
            game_id,
        )

    except Exception:

        logger.exception(
            "Game failed to start: %s",
            game_id,
        )

        try:

            await query.answer(
                "⚠️ Unable to start that game.",
                show_alert=True,
            )

        except Exception:

            pass


# ==========================================================
# LEGACY REACTION CALLBACK
# ==========================================================

async def games_reaction_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    logger.info(
        "Reaction Game Center callback received | user=%s",
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )

    original_data = query.data

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Reaction callback answer failed.",
            exc_info=True,
        )

    try:

        query.data = (
            "games_play_reaction"
        )

        await games_play_callback(
            update,
            context,
            "reaction",
        )

    finally:

        query.data = original_data


# ==========================================================
# ACTUAL GAME ACTION ROUTER
# ==========================================================

async def games_action_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Game action received: %s",
        data,
    )

    # ------------------------------------------------------
    # ONLY actual game actions belong here.
    #
    # Menu callbacks start with games_
    # Gameplay callbacks start with game_
    # ------------------------------------------------------

    if not data.startswith(
        "game_"
    ):

        try:

            await query.answer(
                "⚠️ Game action not recognized.",
                show_alert=True,
            )

        except Exception:

            pass

        return

    try:

        await games_callback_router(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Game engine callback failed: %s",
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
# CENTRAL GAME CENTER ROUTER
# ==========================================================

async def game_center_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Game Center callback received: %s",
        data,
    )

    # ======================================================
    # HOME
    # ======================================================

    if data == "games_home":

        await games_home_callback(
            update,
            context,
        )

        return

    # ======================================================
    # CATEGORY
    # ======================================================

    if data.startswith(
        "games_category_"
    ):

        await games_category_callback(
            update,
            context,
        )

        return

    # ======================================================
    # PROFILE
    # ======================================================

    if data == "games_profile":

        await games_profile_callback(
            update,
            context,
        )

        return

    # ======================================================
    # LEADERBOARDS
    # ======================================================

    if data == "games_leaderboards":

        await games_leaderboards_callback(
            update,
            context,
        )

        return

    # ======================================================
    # LEGACY REACTION
    # ======================================================

    if data == "games_react":

        await games_reaction_callback(
            update,
            context,
        )

        return

    # ======================================================
    # PLAY GAME
    # ======================================================

    if data.startswith(
        "games_play_"
    ):

        await games_play_callback(
            update,
            context,
        )

        return

    # ======================================================
    # ACTUAL GAME ACTION
    # ======================================================

    if data.startswith(
        "game_"
    ):

        await games_action_callback(
            update,
            context,
        )

        return

    # ======================================================
    # UNKNOWN
    # ======================================================

    logger.warning(
        "Unknown Game Center callback: %s",
        data,
    )

    try:

        await query.answer(
            "⚠️ Game action not recognized.",
            show_alert=True,
        )

    except Exception:

        logger.debug(
            "Could not answer unknown callback.",
            exc_info=True,
        )


# ==========================================================
# ALIAS
# ==========================================================

games_callback = (
    game_center_callback_router
)


# ==========================================================
# END game_center.py
# ==========================================================
