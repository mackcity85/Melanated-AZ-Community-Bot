# ==========================================================
# Melanated AZ Bot
# games/game_center.py
#
# GAME CENTER MENU / CALLBACK ROUTER
#
# Handles:
#   - Game Center home
#   - Game categories
#   - Game selection
#   - Game launching
#   - Game callbacks
#
# Compatible with:
#   games/games.py
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
# CATEGORY DEFINITIONS
# ==========================================================

GAME_CATEGORIES = {
    "arcade": {
        "title": "🕹️ Arcade Games",
        "games": [
            "reaction",
            "number_guess",
            "high_low",
            "coin_flip",
            "dice_roll",
        ],
    },

    "outdoor": {
        "title": "🌲 Outdoor Games",
        "games": [
            "fishing",
            "camping",
            "hiking",
            "hunting",
            "survival",
        ],
    },

    "shooting": {
        "title": "🎯 Shooting Games",
        "games": [
            "target",
            "quick_shot",
            "bullseye",
            "accuracy",
            "sniper",
        ],
    },

    "board": {
        "title": "♟️ Board Games",
        "games": [
            "strategy",
            "dice_duel",
        ],
    },

    "party": {
        "title": "🎉 Party Games",
        "games": [
            "truth_dare",
        ],
    },

    "trivia": {
        "title": "🧠 Trivia",
        "games": [
            "general_trivia",
            "music_trivia",
            "sports_trivia",
            "movie_trivia",
            "word_challenge",
        ],
    },

    "sports": {
        "title": "🏆 Sports Games",
        "games": [
            "football",
            "basketball",
            "baseball",
            "boxing",
            "soccer",
        ],
    },

    "racing": {
        "title": "🏁 Racing Games",
        "games": [
            "car_race",
            "bike_race",
            "boat_race",
            "drag_race",
            "street_race",
        ],
    },

    "mystery": {
        "title": "🕵🏾 Mystery Games",
        "games": [
            "detective",
            "murder_mystery",
            "code_breaker",
            "escape",
            "investigation",
        ],
    },

    "fighting": {
        "title": "🥊 Fighting Games",
        "games": [
            "mma",
            "karate",
            "street_fight",
            "arena",
        ],
    },
}


# ==========================================================
# GAME CENTER HOME
# ==========================================================

async def games_home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Display the main Game Center menu.
    """

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    keyboard = [
        [
            InlineKeyboardButton(
                "🕹️ Arcade",
                callback_data="games_category_arcade",
            ),
            InlineKeyboardButton(
                "🌲 Outdoor",
                callback_data="games_category_outdoor",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎯 Shooting",
                callback_data="games_category_shooting",
            ),
            InlineKeyboardButton(
                "♟️ Board",
                callback_data="games_category_board",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎉 Party",
                callback_data="games_category_party",
            ),
            InlineKeyboardButton(
                "🧠 Trivia",
                callback_data="games_category_trivia",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏆 Sports",
                callback_data="games_category_sports",
            ),
            InlineKeyboardButton(
                "🏁 Racing",
                callback_data="games_category_racing",
            ),
        ],
        [
            InlineKeyboardButton(
                "🕵🏾 Mystery",
                callback_data="games_category_mystery",
            ),
            InlineKeyboardButton(
                "🥊 Fighting",
                callback_data="games_category_fighting",
            ),
        ],
    ]

    text = (
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        "Choose a game category below.\n\n"
        "🏆 Play games\n"
        "⭐ Earn XP\n"
        "🪙 Earn AZ Coins\n"
        "📊 Build your game stats"
    )

    try:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception(
            "Could not display Game Center home."
        )


# ==========================================================
# CATEGORY MENU
# ==========================================================

async def games_category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category: str,
):
    """
    Display games belonging to a category.
    """

    query = update.callback_query

    if not query:
        return

    category_data = GAME_CATEGORIES.get(category)

    if not category_data:

        await query.answer(
            "Game category not found.",
            show_alert=True,
        )

        return

    try:
        await query.answer()
    except Exception:
        pass

    keyboard = []

    game_ids = category_data["games"]

    for index in range(0, len(game_ids), 2):

        row = []

        for game_id in game_ids[index:index + 2]:

            name = GAME_NAMES.get(
                game_id,
                game_id,
            )

            row.append(
                InlineKeyboardButton(
                    name,
                    callback_data=f"games_play_{game_id}",
                )
            )

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
        f"<b>{category_data['title']}</b>\n\n"
        "Choose a game:"
    )

    try:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception(
            "Could not display game category: %s",
            category,
        )


# ==========================================================
# PLAY GAME CALLBACK
# ==========================================================

async def games_play_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_id: str | None = None,
):
    """
    Launch a selected game.

    Supports both:
        games_play_<game>
    and direct game_id calls.
    """

    query = update.callback_query

    if not query:
        return

    if game_id is None:

        data = query.data or ""

        if data.startswith("games_play_"):

            game_id = data[
                len("games_play_"):
            ]

        else:

            await query.answer(
                "Game action not recognized.",
                show_alert=True,
            )

            return

    logger.info(
        "Starting Game Center game: %s | user=%s",
        game_id,
        update.effective_user.id
        if update.effective_user
        else "unknown",
    )

    if game_id not in GAME_NAMES:

        await query.answer(
            "That game is not available.",
            show_alert=True,
        )

        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        await play_game(
            update,
            context,
            game_id,
        )

    except Exception:

        logger.exception(
            "Game launch failed: %s",
            game_id,
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>Game Error</b>\n\n"
                "Something went wrong starting "
                "this game.\n\n"
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
# REACTION TEST COMPATIBILITY ROUTER
# ==========================================================

async def games_reaction_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handles the reaction button.

    Older Game Center versions use:
        games_react

    Newer games.py versions use:
        game_reaction_tap

    Accept both so the files remain compatible.
    """

    query = update.callback_query

    if not query:
        return

    logger.info(
        "Reaction callback received."
    )

    try:
        await query.answer()
    except Exception:
        pass

    try:

        await games_callback_router(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Reaction callback failed."
        )

        try:

            await query.edit_message_text(
                "⚠️ <b>Game Error</b>\n\n"
                "The reaction game could not "
                "process your move.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔄 Play Again",
                                callback_data="games_play_reaction",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⬅️ Game Center",
                                callback_data="games_home",
                            )
                        ],
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )

        except Exception:
            pass


# ==========================================================
# CENTRAL GAME CENTER CALLBACK
# ==========================================================

async def game_center_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Central Game Center callback router.

    Handles:
        games_home
        games_category_<category>
        games_play_<game>
        games_react
        game_reaction_tap
        game_guess_<number>
        game_high
        game_low
        game_td_truth
        game_td_dare
        game_trivia_<answer>
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

    # ------------------------------------------------------
    # PLAY GAME
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # OLD REACTION CALLBACK
    #
    # Existing button uses:
    # games_react
    # ------------------------------------------------------

    if data == "games_react":

        await games_reaction_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # NEW REACTION CALLBACK
    #
    # games.py uses:
    # game_reaction_tap
    # ------------------------------------------------------

    if data == "game_reaction_tap":

        await games_reaction_callback(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # OTHER GAME ACTIONS
    #
    # Pass these to games.py
    # ------------------------------------------------------

    game_action_prefixes = (
        "game_guess_",
        "game_high",
        "game_low",
        "game_td_",
        "game_trivia_",
    )

    if (
        data.startswith(game_action_prefixes)
    ):

        await games_callback_router(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # UNKNOWN CALLBACK
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
        pass


# ==========================================================
# ALIAS
# ==========================================================

games_callback = game_center_callback_router


# ==========================================================
# END games/game_center.py
# ==========================================================
