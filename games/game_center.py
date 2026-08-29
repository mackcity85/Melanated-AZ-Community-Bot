# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# GAME CENTER
#
# Handles:
#   - Main Game Center menu
#   - Game category menus
#   - Game selection
#   - Game launch callbacks
#   - Compatibility aliases used by bot.py / games/__init__.py
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
)

# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger("melanated_az_bot.games")

# ==========================================================
# GAME CATEGORIES
# ==========================================================

GAME_CATEGORIES = {
    "arcade": {
        "name": "🕹️ Arcade",
        "games": [
            "reaction",
            "number_guess",
            "high_low",
            "coin_flip",
            "dice_roll",
        ],
    },

    "outdoor": {
        "name": "🌲 Outdoor",
        "games": [
            "fishing",
            "camping",
            "hiking",
            "hunting",
            "survival",
        ],
    },

    "shooting": {
        "name": "🎯 Shooting",
        "games": [
            "target",
            "quick_shot",
            "bullseye",
            "accuracy",
            "sniper",
        ],
    },

    "board": {
        "name": "♟️ Board",
        "games": [
            "strategy",
            "dice_duel",
        ],
    },

    "party": {
        "name": "🎉 Party",
        "games": [
            "truth_dare",
        ],
    },

    "trivia": {
        "name": "🧠 Trivia",
        "games": [
            "general_trivia",
            "music_trivia",
            "sports_trivia",
            "movie_trivia",
            "word_challenge",
        ],
    },

    "sports": {
        "name": "🏆 Sports",
        "games": [
            "football",
            "basketball",
            "baseball",
            "boxing",
            "soccer",
        ],
    },

    "racing": {
        "name": "🏎️ Racing",
        "games": [
            "car_race",
            "bike_race",
            "boat_race",
            "drag_race",
            "street_race",
        ],
    },

    "mystery": {
        "name": "🕵🏾 Mystery",
        "games": [
            "detective",
            "murder_mystery",
            "code_breaker",
            "escape",
            "investigation",
        ],
    },

    "fighting": {
        "name": "🥊 Fighting",
        "games": [
            "mma",
            "karate",
            "street_fight",
            "arena",
        ],
    },
}

# ==========================================================
# GAME CATEGORY LOOKUP
# ==========================================================

GAME_TO_CATEGORY = {}

for category_id, category_data in GAME_CATEGORIES.items():

    for game_id in category_data["games"]:

        GAME_TO_CATEGORY[game_id] = category_id


# ==========================================================
# MAIN GAME CENTER KEYBOARD
# ==========================================================

def games_main_keyboard():
    """
    Main Game Center keyboard.
    """

    keyboard = []

    row = []

    for category_id, category_data in GAME_CATEGORIES.items():

        row.append(
            InlineKeyboardButton(
                category_data["name"],
                callback_data=f"games_category_{category_id}",
            )
        )

        if len(row) == 2:

            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def games_category_keyboard(category_id):
    """
    Build keyboard for a game category.
    """

    category = GAME_CATEGORIES.get(category_id)

    if not category:
        return games_main_keyboard()

    keyboard = []

    row = []

    for game_id in category["games"]:

        game_name = GAME_NAMES.get(
            game_id,
            game_id.replace("_", " ").title(),
        )

        row.append(
            InlineKeyboardButton(
                game_name,
                callback_data=f"games_play_{game_id}",
            )
        )

        if len(row) == 2:

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

    return InlineKeyboardMarkup(keyboard)


# ==========================================================
# GAME CENTER MENU
# ==========================================================

async def games_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Open the main Game Center menu.

    Supports:
        /games
        /gamecenter
        callback_data = games_home
    """

    query = update.callback_query

    if query:

        await query.answer()

        await query.edit_message_text(
            "🎮 <b>Melanated AZ Game Center</b>\n\n"
            "Choose a category below and pick a game.\n\n"
            "🏆 Play games\n"
            "⭐ Earn XP\n"
            "🪙 Earn AZ Coins\n"
            "📊 Build your game stats",
            reply_markup=games_main_keyboard(),
            parse_mode=ParseMode.HTML,
        )

        return

    if update.message:

        await update.message.reply_text(
            "🎮 <b>Melanated AZ Game Center</b>\n\n"
            "Choose a category below and pick a game.\n\n"
            "🏆 Play games\n"
            "⭐ Earn XP\n"
            "🪙 Earn AZ Coins\n"
            "📊 Build your game stats",
            reply_markup=games_main_keyboard(),
            parse_mode=ParseMode.HTML,
        )


# ==========================================================
# GAME CENTER HOME CALLBACK
# ==========================================================

async def games_home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handles:

        games_home
    """

    query = update.callback_query

    if not query:
        return

    try:

        await query.answer()

        await query.edit_message_text(
            "🎮 <b>Melanated AZ Game Center</b>\n\n"
            "Choose a category below and pick a game.\n\n"
            "🏆 Play games\n"
            "⭐ Earn XP\n"
            "🪙 Earn AZ Coins\n"
            "📊 Build your game stats",
            reply_markup=games_main_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    except Exception:

        logger.exception(
            "Failed to display Game Center home."
        )


# ==========================================================
# CATEGORY CALLBACK
# ==========================================================

async def games_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handles:

        games_category_arcade
        games_category_outdoor
        games_category_shooting
        etc.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    prefix = "games_category_"

    if not data.startswith(prefix):
        return

    category_id = data[len(prefix):]

    category = GAME_CATEGORIES.get(category_id)

    if not category:

        await query.answer(
            "Game category not found.",
            show_alert=True,
        )

        return

    try:

        await query.answer()

        await query.edit_message_text(
            f"🎮 <b>{category['name']}</b>\n\n"
            "Choose a game:",
            reply_markup=games_category_keyboard(
                category_id
            ),
            parse_mode=ParseMode.HTML,
        )

    except Exception:

        logger.exception(
            "Failed to display game category: %s",
            category_id,
        )


# ==========================================================
# GAME PLAY CALLBACK
# ==========================================================

async def games_play_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handles:

        games_play_reaction
        games_play_number_guess
        games_play_high_low
        games_play_coin_flip
        games_play_dice_roll
        etc.

    This is the callback expected by bot.py.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    prefix = "games_play_"

    if not data.startswith(prefix):

        await query.answer(
            "Game action not recognized.",
            show_alert=True,
        )

        return

    game_id = data[len(prefix):]

    # ------------------------------------------------------
    # Validate game
    # ------------------------------------------------------

    if game_id not in GAME_NAMES:

        logger.warning(
            "Unknown game requested: %s",
            game_id,
        )

        await query.answer(
            "That game is not available.",
            show_alert=True,
        )

        return

    try:

        await query.answer()

        # --------------------------------------------------
        # IMPORTANT
        #
        # Pass the ORIGINAL update/context to games.py.
        #
        # games.py handles the actual gameplay.
        # --------------------------------------------------

        await play_game(
            update,
            context,
            game_id,
        )

    except Exception:

        logger.exception(
            "Failed to launch game: %s",
            game_id,
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>Game Error</b>\n\n"
                "Something went wrong starting "
                "that game.\n\n"
                "Please try again.",
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

        except Exception:

            logger.exception(
                "Could not display game error."
            )


# ==========================================================
# UNIVERSAL GAME CENTER CALLBACK ROUTER
# ==========================================================

async def games_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Central router for Game Center callbacks.

    Handles:

        games_home
        games_category_*
        games_play_*

    Gameplay-specific callbacks are passed to games.py.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # ------------------------------------------------------
    # GAME CENTER HOME
    # ------------------------------------------------------

    if data == "games_home":

        await games_home_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------

    if data.startswith(
        "games_category_"
    ):

        await games_category_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # GAME PLAY
    # ------------------------------------------------------

    if data.startswith(
        "games_play_"
    ):

        await games_play_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # OTHER GAME ACTIONS
    #
    # These belong to games.py.
    # ------------------------------------------------------

    if (
        data.startswith("game_")
        or data.startswith("games_")
    ):

        # Import here to avoid circular imports.
        from .games import games_callback_router

        await games_callback_router(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # UNKNOWN ACTION
    # ------------------------------------------------------

    logger.warning(
        "Unrecognized Game Center callback: %s",
        data,
    )

    await query.answer(
        "Game action not recognized.",
        show_alert=True,
    )


# ==========================================================
# COMPATIBILITY ALIASES
# ==========================================================

# Some versions of bot.py may use these names.

game_center_callback = games_callback_router

game_center_home_callback = games_home_callback

game_center_play_callback = games_play_callback

game_category_callback = games_category_callback


# ==========================================================
# COMMAND HANDLER
# ==========================================================

async def game_center_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Command handler for:

        /games
        /gamecenter
    """

    await games_menu(
        update,
        context,
    )


# ==========================================================
# END game_center.py
# ==========================================================
