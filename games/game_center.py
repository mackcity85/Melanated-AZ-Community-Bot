# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# GAME CENTER MENU / CALLBACK ROUTER
#
# IMPORTANT:
# This file controls the Game Center menus and routes
# game buttons into games.games.
#
# Compatible callback IDs:
#   games_home
#   games_category_<category>
#   games_play_<game>
#   games_react
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
# CATEGORY ICONS
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
    """Return the main Game Center keyboard."""

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

    return InlineKeyboardMarkup(rows)


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def category_keyboard(category):
    """Return keyboard containing games in a category."""

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

    await query.answer()

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
    category: str,
):
    """Display games in a selected category."""

    query = update.callback_query

    if not query:
        return

    if category not in GAME_CATEGORIES:

        await query.answer(
            "Category not found.",
            show_alert=True,
        )

        return

    await query.answer()

    category_data = GAME_CATEGORIES[category]

    await query.edit_message_text(
        f"{category_data['title']}\n\n"
        "Choose a game:",
        reply_markup=category_keyboard(category),
        parse_mode=ParseMode.HTML,
    )


# ==========================================================
# START GAME CALLBACK
# ==========================================================

async def games_play_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_id: str,
):
    """
    Start a game.

    This is intentionally separate from the main callback
    router so bot.py can import games_play_callback directly.
    """

    query = update.callback_query

    if not query:
        return

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
            "Callback answer failed while starting game.",
            exc_info=True,
        )

    await play_game(
        update,
        context,
        game_id,
    )


# ==========================================================
# REACTION BUTTON
# ==========================================================

async def games_reaction_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handle the Reaction Test button.

    Older Game Center messages use:

        games_react

    The actual game engine uses:

        game_reaction_tap

    We translate the old Game Center callback here.
    """

    query = update.callback_query

    if not query:
        return

    logger.info(
        "Reaction button pressed | user=%s",
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

    # games_callback_router handles the actual reaction test.
    #
    # Temporarily replace the callback data so the existing
    # game engine can process it.

    original_data = query.data

    try:

        query.data = "game_reaction_tap"

        await games_callback_router(
            update,
            context,
        )

    finally:

        query.data = original_data


# ==========================================================
# CENTRAL GAME CENTER ROUTER
# ==========================================================

async def game_center_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Central router for all Game Center callbacks.

    This function can be used directly by bot.py.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    logger.info(
        "Game Center callback received: %s",
        data,
    )

    # ------------------------------------------------------
    # HOME
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

    if data.startswith("games_category_"):

        category = data[
            len("games_category_"):
        ]

        await games_category_callback(
            update,
            context,
            category,
        )

        return

    # ------------------------------------------------------
    # REACTION TEST
    #
    # IMPORTANT:
    # Existing Game Center buttons send:
    #
    #     games_react
    #
    # ------------------------------------------------------

    if data == "games_react":

        await games_reaction_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # GAME PLAY
    # ------------------------------------------------------

    if data.startswith("games_play_"):

        game_id = data[
            len("games_play_"):
        ]

        await games_play_callback(
            update,
            context,
            game_id,
        )

        return

    # ------------------------------------------------------
    # ACTUAL GAME ACTIONS
    #
    # Pass game-specific callbacks to games.py.
    # ------------------------------------------------------

    if (
        data.startswith("game_")
        or data.startswith("games_")
    ):

        try:

            await games_callback_router(
                update,
                context,
            )

            return

        except Exception:

            logger.exception(
                "Game engine callback failed: %s",
                data,
            )

    # ------------------------------------------------------
    # UNKNOWN
    # ------------------------------------------------------

    logger.warning(
        "Unknown Game Center callback: %s",
        data,
    )

    try:

        await query.answer(
            "Game action not recognized.",
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

# Some versions of bot.py may import this name.

games_callback = game_center_callback_router


# ==========================================================
# END game_center.py
# ==========================================================
