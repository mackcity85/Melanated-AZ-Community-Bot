# ==========================================================
# Melanated AZ Bot
# games.py
#
# GAMES CATEGORY SYSTEM
#
# Main command:
#   /games
#
# Features:
#   - Central Games menu
#   - Button-based navigation
#   - Truth or Dare integration
#   - Easy to add additional games
#   - Admin Games settings
#   - No imports from admin.py
#
# IMPORTANT:
# Individual games should live in their own files.
#
# Example:
#   games.py
#   truth_dare.py
#   would_you_rather.py
#   never_have_i_ever.py
#   this_or_that.py
#   etc.
# ==========================================================

import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config import ADMIN_IDS


logger = logging.getLogger(__name__)


# ==========================================================
# SETTINGS
# ==========================================================

GAMES_ENABLED = True


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_games_admin(user_id):
    """
    Check whether a Telegram user is an administrator.
    """

    try:
        return int(user_id) in [
            int(admin_id)
            for admin_id in ADMIN_IDS
        ]

    except (TypeError, ValueError):
        return False


# ==========================================================
# ENABLED STATUS
# ==========================================================

def is_games_enabled():
    """
    Return whether the Games category is enabled.
    """

    return GAMES_ENABLED


# ==========================================================
# GAMES MENU KEYBOARD
# ==========================================================

def games_menu_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔥 Truth or Dare",
                    callback_data="games_truthdare",
                )
            ],

            [
                InlineKeyboardButton(
                    "🤔 Would You Rather",
                    callback_data="games_wouldyourather",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🙈 Never Have I Ever",
                    callback_data="games_neverhaveiever",
                ),
            ],

            [
                InlineKeyboardButton(
                    "⚡ This or That",
                    callback_data="games_thisorthat",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🎲 Random Game",
                    callback_data="games_random",
                )
            ],
        ]
    )


# ==========================================================
# GAMES MENU
# ==========================================================

async def games_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not GAMES_ENABLED:

        await message.reply_text(
            "🎮 Games are currently disabled."
        )

        return

    text = (
        "🎮 GAMES\n\n"
        "Welcome to the Melanated AZ Games section!\n\n"
        "Choose a game below.\n\n"
        "🔥 Truth or Dare\n"
        "🤔 Would You Rather\n"
        "🙈 Never Have I Ever\n"
        "⚡ This or That\n"
        "🎲 Random Game\n\n"
        "Have fun, respect boundaries, "
        "and remember that PASS is always allowed."
    )

    await message.reply_text(
        text,
        reply_markup=games_menu_keyboard(),
    )


# ==========================================================
# GAMES CALLBACK HANDLER
# ==========================================================

async def games_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # ------------------------------------------------------
    # ALWAYS ANSWER CALLBACK
    # ------------------------------------------------------

    try:

        await query.answer()

    except Exception:

        pass

    # ------------------------------------------------------
    # GAMES DISABLED
    # ------------------------------------------------------

    if not GAMES_ENABLED:

        try:

            await query.answer(
                "Games are currently disabled.",
                show_alert=True,
            )

        except Exception:

            pass

        return

    # ======================================================
    # BACK TO GAMES
    # ======================================================

    if data == "games_menu":

        await query.edit_message_text(
            "🎮 GAMES\n\n"
            "Choose a game below.\n\n"
            "🔥 Truth or Dare\n"
            "🤔 Would You Rather\n"
            "🙈 Never Have I Ever\n"
            "⚡ This or That\n"
            "🎲 Random Game\n\n"
            "Have fun, respect boundaries, "
            "and remember that PASS is always allowed.",
            reply_markup=games_menu_keyboard(),
        )

        return

    # ======================================================
    # TRUTH OR DARE
    # ======================================================

    if data == "games_truthdare":

        try:

            from truth_dare import (
                truth_dare_menu,
            )

            # We need to show the Truth or Dare menu
            await truth_dare_menu(
                update,
                context,
            )

        except ImportError:

            logger.exception(
                "Unable to load truth_dare.py"
            )

            await query.edit_message_text(
                "🔥 Truth or Dare\n\n"
                "The Truth or Dare game file "
                "is not available yet.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Games",
                                callback_data="games_menu",
                            )
                        ]
                    ]
                ),
            )

        return

    # ======================================================
    # WOULD YOU RATHER
    # ======================================================

    if data == "games_wouldyourather":

        await query.edit_message_text(
            "🤔 WOULD YOU RATHER\n\n"
            "This game is coming next!\n\n"
            "We're building the Games category "
            "so every game uses the same "
            "easy button system.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Games",
                            callback_data="games_menu",
                        )
                    ]
                ]
            ),
        )

        return

    # ======================================================
    # NEVER HAVE I EVER
    # ======================================================

    if data == "games_neverhaveiever":

        await query.edit_message_text(
            "🙈 NEVER HAVE I EVER\n\n"
            "This game is coming next!\n\n"
            "We're building it directly into "
            "the Games category.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Games",
                            callback_data="games_menu",
                        )
                    ]
                ]
            ),
        )

        return

    # ======================================================
    # THIS OR THAT
    # ======================================================

    if data == "games_thisorthat":

        await query.edit_message_text(
            "⚡ THIS OR THAT\n\n"
            "This game is coming next!\n\n"
            "It will use the same button-based "
            "game system.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Games",
                            callback_data="games_menu",
                        )
                    ]
                ]
            ),
        )

        return

    # ======================================================
    # RANDOM GAME
    # ======================================================

    if data == "games_random":

        await query.edit_message_text(
            "🎲 RANDOM GAME\n\n"
            "Random game selection will be "
            "available once the Games collection "
            "is installed.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Games",
                            callback_data="games_menu",
                        )
                    ]
                ]
            ),
        )

        return


# ==========================================================
# ADMIN GAMES MENU
# ==========================================================

async def games_admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    if not is_games_admin(user.id):
        return

    query = update.callback_query

    status = (
        "🟢 ENABLED"
        if GAMES_ENABLED
        else "🔴 DISABLED"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"🎮 Games: {status}",
                    callback_data="admin_games_toggle",
                )
            ],

            [
                InlineKeyboardButton(
                    "❓ Games Help",
                    callback_data="admin_games_help",
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="admin_back",
                )
            ],
        ]
    )

    text = (
        "🎮 GAMES SETTINGS\n\n"
        f"Status: {status}\n\n"
        "Games category:\n"
        "/games\n\n"
        "Currently available:\n"
        "🔥 Truth or Dare\n"
        "🤔 Would You Rather\n"
        "🙈 Never Have I Ever\n"
        "⚡ This or That\n"
        "🎲 Random Game\n\n"
        "Individual games can be enabled "
        "and expanded independently."
    )

    if query:

        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
        )

    elif update.effective_message:

        await update.effective_message.reply_text(
            text=text,
            reply_markup=keyboard,
        )


# ==========================================================
# TOGGLE GAMES
# ==========================================================

async def toggle_games(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    global GAMES_ENABLED

    user = update.effective_user

    if not user:
        return

    if not is_games_admin(user.id):
        return

    query = update.callback_query

    GAMES_ENABLED = not GAMES_ENABLED

    status = (
        "🟢 ENABLED"
        if GAMES_ENABLED
        else "🔴 DISABLED"
    )

    if query:

        try:

            await query.answer(
                f"Games {status}"
            )

        except Exception:

            pass

    await games_admin_menu(
        update,
        context,
    )


# ==========================================================
# ADMIN HELP
# ==========================================================

async def games_admin_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    if not is_games_admin(user.id):
        return

    query = update.callback_query

    text = (
        "🎮 GAMES HELP\n\n"
        "Members use:\n\n"
        "/games\n"
        "Opens the Games menu.\n\n"
        "Games are designed to use "
        "buttons instead of requiring "
        "members to remember commands.\n\n"
        "Current Games:\n"
        "🔥 Truth or Dare\n"
        "🤔 Would You Rather\n"
        "🙈 Never Have I Ever\n"
        "⚡ This or That\n\n"
        "More games can be added without "
        "changing the main Games menu.\n\n"
        "Game interactions are designed "
        "around consent and participation.\n\n"
        "Members can always PASS."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_games",
                )
            ]
        ]
    )

    if query:

        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
        )

    elif update.effective_message:

        await update.effective_message.reply_text(
            text=text,
            reply_markup=keyboard,
        )


# ==========================================================
# END games.py
# ==========================================================
