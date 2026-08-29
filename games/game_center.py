# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# COMPLETE GAME CENTER MENU / CALLBACK ROUTER
#
# Handles:
#   /games
#   games_home
#   games_category_<category>
#   games_play_<game>
#   games_react
#   game_<action>
#
# Routes actual gameplay callbacks to games.py
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

    # ------------------------------------------------------
    # ARCADE
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # OUTDOOR
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # SHOOTING
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # BOARD
    # ------------------------------------------------------

    "board": {
        "title": "♟️ BOARD",
        "games": [
            "strategy",
            "dice_duel",
        ],
    },

    # ------------------------------------------------------
    # PARTY
    # ------------------------------------------------------

    "party": {
        "title": "🔥 PARTY",
        "games": [
            "truth_dare",
        ],
    },

    # ------------------------------------------------------
    # TRIVIA
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # SPORTS
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # RACING
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # MYSTERY
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # FIGHTING
    # ------------------------------------------------------

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
# CATEGORY BUTTON LABELS
# ==========================================================

CATEGORY_BUTTONS = {

    "arcade":
        "🕹️ Arcade",

    "outdoor":
        "🌲 Outdoor",

    "shooting":
        "🎯 Shooting",

    "board":
        "♟️ Board",

    "party":
        "🔥 Party",

    "trivia":
        "🧠 Trivia",

    "sports":
        "🏆 Sports",

    "racing":
        "🏎️ Racing",

    "mystery":
        "🕵🏾 Mystery",

    "fighting":
        "🥊 Fighting",
}


# ==========================================================
# MAIN GAME CENTER KEYBOARD
# ==========================================================

def games_home_keyboard():
    """
    Return the main Game Center keyboard.

    Categories are displayed two per row.
    """

    rows = []

    for index in range(
        0,
        len(CATEGORY_ORDER),
        2,
    ):

        row = []

        first = CATEGORY_ORDER[index]

        row.append(
            InlineKeyboardButton(
                CATEGORY_BUTTONS.get(
                    first,
                    first,
                ),
                callback_data=(
                    f"games_category_{first}"
                ),
            )
        )

        if index + 1 < len(CATEGORY_ORDER):

            second = CATEGORY_ORDER[
                index + 1
            ]

            row.append(
                InlineKeyboardButton(
                    CATEGORY_BUTTONS.get(
                        second,
                        second,
                    ),
                    callback_data=(
                        f"games_category_{second}"
                    ),
                )
            )

        rows.append(row)

    return InlineKeyboardMarkup(rows)


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def category_keyboard(category):
    """
    Return keyboard containing games
    belonging to a category.
    """

    category_data = GAME_CATEGORIES.get(
        category
    )

    if not category_data:

        return games_home_keyboard()

    game_ids = category_data["games"]

    rows = []

    for index in range(
        0,
        len(game_ids),
        2,
    ):

        row = []

        first_game = game_ids[index]

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

        if index + 1 < len(game_ids):

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

    return InlineKeyboardMarkup(rows)


# ==========================================================
# /games COMMAND
# ==========================================================

async def games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Open the Game Center using /games.

    This function is intentionally separate from
    games_home_callback() because /games is a
    Telegram command, not a callback query.
    """

    message = update.effective_message

    if not message:

        logger.warning(
            "games_command called without a message."
        )

        return

    try:

        await message.reply_text(
            "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
            "Choose a category below and pick a game.\n\n"
            "🏆 Play games\n"
            "⭐ Earn XP\n"
            "🪙 Earn AZ Coins\n"
            "📊 Build your game stats!",
            reply_markup=games_home_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    except Exception:

        logger.exception(
            "Could not open Game Center "
            "from /games command."
        )


# ==========================================================
# GAME CENTER HOME CALLBACK
# ==========================================================

async def games_home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Display the main Game Center from
    the games_home callback.
    """

    query = update.callback_query

    if not query:

        return

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Could not answer Game Center "
            "home callback.",
            exc_info=True,
        )

    try:

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

    except Exception:

        logger.exception(
            "Could not display Game Center home."
        )


# ==========================================================
# CATEGORY CALLBACK
# ==========================================================

async def games_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category: str,
):
    """
    Display games in a selected category.
    """

    query = update.callback_query

    if not query:

        return

    if category not in GAME_CATEGORIES:

        try:

            await query.answer(
                "Category not found.",
                show_alert=True,
            )

        except Exception:

            pass

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

    try:

        await query.edit_message_text(
            f"{category_data['title']}\n\n"
            "Choose a game:",
            reply_markup=category_keyboard(
                category
            ),
            parse_mode=ParseMode.HTML,
        )

    except Exception:

        logger.exception(
            "Could not display category: %s",
            category,
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

    This function is intentionally separate so
    bot.py can import it directly if needed.
    """

    query = update.callback_query

    if not query:

        return

    if game_id not in GAME_NAMES:

        try:

            await query.answer(
                "Game not found.",
                show_alert=True,
            )

        except Exception:

            pass

        logger.warning(
            "Unknown Game Center game: %s",
            game_id,
        )

        return

    logger.info(
        "Starting Game Center game: %s | user=%s",
        game_id,
        (
            update.effective_user.id
            if update.effective_user
            else "unknown"
        ),
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

            await query.edit_message_text(
                "⚠️ <b>Game Error</b>\n\n"
                "Something went wrong starting "
                "this game.\n\n"
                "Please return to the Game Center "
                "and try again.",
                reply_markup=games_home_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        except Exception:

            logger.exception(
                "Could not display game-start error."
            )


# ==========================================================
# LEGACY REACTION CALLBACK
# ==========================================================

async def games_reaction_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handle the legacy Game Center Reaction callback.

    Legacy callback:
        games_react

    Normal game callback:
        games_play_reaction
    """

    query = update.callback_query

    if not query:

        return

    logger.info(
        "Legacy Reaction callback received | user=%s",
        (
            update.effective_user.id
            if update.effective_user
            else "unknown"
        ),
    )

    try:

        await query.answer()

    except Exception:

        logger.debug(
            "Reaction callback answer failed.",
            exc_info=True,
        )

    # ------------------------------------------------------
    # IMPORTANT
    #
    # Do NOT manually call reaction_game() here.
    #
    # Translate the old callback to the normal
    # games_play_reaction route.
    # ------------------------------------------------------

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
# CENTRAL GAME CENTER CALLBACK ROUTER
# ==========================================================

async def game_center_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Central router for ALL Game Center callbacks.

    bot.py should route Game Center callbacks here.

    Supported callbacks:

        games_home

        games_category_<category>

        games_play_<game>

        games_react

        game_<action>
    """

    query = update.callback_query

    if not query:

        return

    data = query.data or ""

    logger.info(
        "Game Center callback received: %s",
        data,
    )

    try:

        # ==================================================
        # HOME
        # ==================================================

        if data == "games_home":

            await games_home_callback(
                update,
                context,
            )

            return

        # ==================================================
        # CATEGORY
        # ==================================================

        if data.startswith(
            "games_category_"
        ):

            category = data[
                len("games_category_"):
            ]

            await games_category_callback(
                update,
                context,
                category,
            )

            return

        # ==================================================
        # LEGACY REACTION
        # ==================================================

        if data == "games_react":

            await games_reaction_callback(
                update,
                context,
            )

            return

        # ==================================================
        # GAME PLAY
        # ==================================================

        if data.startswith(
            "games_play_"
        ):

            game_id = data[
                len("games_play_"):
            ]

            await games_play_callback(
                update,
                context,
                game_id,
            )

            return

        # ==================================================
        # ACTUAL GAME ACTIONS
        #
        # Examples:
        #
        # game_reaction_tap
        # game_guess_5
        # game_high
        # game_low
        # game_td_truth
        # game_trivia_0
        # game_code_500
        # game_escape_red
        # game_detective_2
        # ==================================================

        if data.startswith("game_"):

            await games_callback_router(
                update,
                context,
            )

            return

        # ==================================================
        # UNKNOWN
        # ==================================================

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
                "Could not answer unknown "
                "Game Center callback.",
                exc_info=True,
            )

    except Exception:

        logger.exception(
            "Game Center callback failed: %s",
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
# COMPATIBILITY ALIASES
# ==========================================================

# Existing code may import games_callback.
games_callback = game_center_callback_router


# Existing code may import games_home.
games_home = games_home_callback


# Existing code may import games_category.
games_category = games_category_callback


# Existing code may import games_play.
games_play = games_play_callback


# ==========================================================
# END game_center.py
# ==========================================================
