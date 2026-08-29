# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# GAME CENTER MENU / CALLBACK ROUTER
#
# Handles:
#   /games
#   games_home
#   games_category_<category>
#   games_profile
#   games_leaderboards
#   games_play_<game>
#   games_react
#   game_*
#
# Routes actual gameplay callbacks to games.py
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
)

logger = logging.getLogger("melanated_az_bot.games")


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
    """Build the main Game Center keyboard."""

    rows = []

    for index in range(0, len(CATEGORY_ORDER), 2):

        row = []

        first = CATEGORY_ORDER[index]

        row.append(
            InlineKeyboardButton(
                CATEGORY_BUTTONS[first],
                callback_data=f"games_category_{first}",
            )
        )

        if index + 1 < len(CATEGORY_ORDER):

            second = CATEGORY_ORDER[index + 1]

            row.append(
                InlineKeyboardButton(
                    CATEGORY_BUTTONS[second],
                    callback_data=f"games_category_{second}",
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

    return InlineKeyboardMarkup(rows)


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def category_keyboard(category):
    """Build keyboard for a selected category."""

    category_data = GAME_CATEGORIES.get(category)

    if not category_data:
        return games_home_keyboard()

    game_ids = category_data["games"]

    rows = []

    for index in range(0, len(game_ids), 2):

        row = []

        first_game = game_ids[index]

        row.append(
            InlineKeyboardButton(
                GAME_NAMES.get(
                    first_game,
                    first_game,
                ),
                callback_data=f"games_play_{first_game}",
            )
        )

        if index + 1 < len(game_ids):

            second_game = game_ids[index + 1]

            row.append(
                InlineKeyboardButton(
                    GAME_NAMES.get(
                        second_game,
                        second_game,
                    ),
                callback_data=f"games_play_{second_game}",
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

    return InlineKeyboardMarkup(rows)


# ==========================================================
# /GAMES COMMAND
# ==========================================================

async def games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    /games

    Opens the Game Center.
    """

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
    """Display the main Game Center."""

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
    """
    Display games in a selected category.

    Supports both:

        games_category_callback(update, context, "arcade")

    and the bot.py style:

        games_category_callback(update, context)

    where the category is extracted from query.data.
    """

    query = update.callback_query

    if not query:
        return

    if category is None:

        data = query.data or ""

        prefix = "games_category_"

        if not data.startswith(prefix):

            await query.answer(
                "Category not found.",
                show_alert=True,
            )

            return

        category = data[len(prefix):]

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

    category_data = GAME_CATEGORIES[category]

    await query.edit_message_text(
        f"{category_data['title']}\n\n"
        "Choose a game:",
        reply_markup=category_keyboard(category),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# PROFILE
# ==========================================================

async def games_profile_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Display the player's Game Center profile.

    The detailed player statistics remain handled by games.py
    when available.
    """

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

    name = user.first_name or "Player"

    username = (
        f"@{user.username}"
        if user.username
        else "No username"
    )

    text = (
        "👤 <b>GAME CENTER PROFILE</b>\n\n"
        f"Player: <b>{name}</b>\n"
        f"Username: {username}\n\n"
        "⭐ XP: Coming from Game Center stats\n"
        "🪙 AZ Coins: Coming from Game Center stats\n"
        "🎮 Games Played: Coming from Game Center stats\n"
        "🏆 Wins: Coming from Game Center stats\n\n"
        "Keep playing to build your stats!"
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
    """
    Display Game Center leaderboards.

    If games.py later provides detailed leaderboard data,
    this screen can be expanded without changing bot.py.
    """

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

    text = (
        "🏆 <b>GAME CENTER LEADERBOARDS</b>\n\n"
        "⭐ Top XP Players\n"
        "🪙 Top AZ Coin Players\n"
        "🎮 Most Games Played\n"
        "🥇 Most Wins\n\n"
        "Leaderboard statistics will appear here "
        "as players compete."
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
    """
    Start a Game Center game.

    Supports both:

        games_play_callback(update, context, "reaction")

    and the bot.py style:

        games_play_callback(update, context)

    where the game ID is extracted from query.data.
    """

    query = update.callback_query

    if not query:
        return

    if game_id is None:

        data = query.data or ""

        prefix = "games_play_"

        if not data.startswith(prefix):

            await query.answer(
                "Game not found.",
                show_alert=True,
            )

            return

        game_id = data[len(prefix):]

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
# REACTION LEGACY CALLBACK
# ==========================================================

async def games_reaction_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handle legacy Game Center Reaction callback.

    Legacy:
        games_react

    Converts it to:
        games_play_reaction
    """

    query = update.callback_query

    if not query:
        return

    logger.info(
        "Reaction Game Center callback received | user=%s",
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Reaction callback answer failed.",
            exc_info=True,
        )

    original_data = query.data

    try:

        query.data = "games_play_reaction"

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
    """
    Forward actual in-game callbacks to games.py.

    Examples:

        game_reaction_tap
        game_coin_heads
        game_coin_tails
        game_dice_roll
        game_guess_*
        etc.

    These MUST NOT be treated as Game Center menu callbacks.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Game action received: %s",
        data,
    )

    if not data.startswith("game_"):

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
    """
    Central router for ALL Game Center callbacks.

    Handles:

        games_home
        games_category_*
        games_profile
        games_leaderboards
        games_play_*
        games_react
        game_*
    """

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

    if data.startswith("games_category_"):

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

    if data.startswith("games_play_"):

        await games_play_callback(
            update,
            context,
        )

        return

    # ======================================================
    # ACTUAL GAME ACTION
    #
    # IMPORTANT:
    #
    # These callbacks begin with game_, NOT games_.
    #
    # They must be sent to games.py.
    # ======================================================

    if data.startswith("game_"):

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

games_callback = game_center_callback_router


# ==========================================================
# END game_center.py
# ==========================================================
