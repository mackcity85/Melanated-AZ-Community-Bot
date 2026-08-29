# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# GAME CENTER MENU / CALLBACK ROUTER
#
# Handles:
#   games_home
#   games_category_<category>
#   games_play_<game>
#   games_react
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
# START GAME CALLBACK
# ==========================================================

async def games_play_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_id: str,
):
    """
    Start a Game Center game.

    This function is intentionally separate so bot.py
    can import it directly if needed.
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
            "Game start callback answer failed.",
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
    Handle the legacy Game Center Reaction callback.

    Legacy callback:
        games_react

    Actual game callback:
        game_reaction_tap
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

    # Translate the legacy callback into the actual
    # reaction-game callback understood by games.py.

    original_data = query.data

    try:

        query.data = "games_play_reaction"

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
    Central router for ALL Game Center callbacks.

    bot.py should send Game Center callbacks here.
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
    # LEGACY REACTION BUTTON
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
    # IMPORTANT:
    # Do NOT send games_react here.
    # It has already been handled above.
    # ------------------------------------------------------

    if data.startswith("game_"):

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

            try:
                await query.answer(
                    "⚠️ Game action failed.",
                    show_alert=True,
                )
            except Exception:
                pass

            return

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

games_callback = game_center_callback_router


# ==========================================================
# END game_center.py
# ==========================================================
