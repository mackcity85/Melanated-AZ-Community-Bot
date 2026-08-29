# ==========================================================
# Melanated AZ Bot
# games/game_engine.py
#
# SHARED GAME ENGINE
#
# Used by:
#   - Truth or Dare
#   - Would You Rather
#   - Never Have I Ever
#   - This or That
#
# Features:
#   - Shared difficulty levels
#   - Random prompt selection
#   - PASS support
#   - Button navigation
#   - Safe callback handling
#   - Per-user game state
#   - No dependency on admin.py
#
# ==========================================================

import logging
import random

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


logger = logging.getLogger(__name__)


# ==========================================================
# LEVELS
# ==========================================================

VALID_LEVELS = (
    "mild",
    "spicy",
    "extreme",
)


DEFAULT_LEVEL = "mild"


# ==========================================================
# GAME IDENTIFIERS
# ==========================================================

GAME_TRUTH_DARE = "truthdare"
GAME_WOULD_YOU_RATHER = "wouldyourather"
GAME_NEVER_HAVE_I_EVER = "neverhaveiever"
GAME_THIS_OR_THAT = "thisorthat"


VALID_GAMES = (
    GAME_TRUTH_DARE,
    GAME_WOULD_YOU_RATHER,
    GAME_NEVER_HAVE_I_EVER,
    GAME_THIS_OR_THAT,
)


# ==========================================================
# LEVEL DISPLAY
# ==========================================================

LEVEL_DISPLAY = {
    "mild": "🟢 Mild",
    "spicy": "🌶️ Spicy",
    "extreme": "🔥 Extreme",
}


def normalize_level(level):
    """
    Normalize a level value.

    Invalid values automatically become mild.
    """

    if not isinstance(level, str):
        return DEFAULT_LEVEL

    level = level.lower().strip()

    if level not in VALID_LEVELS:
        return DEFAULT_LEVEL

    return level


def get_level(context):
    """
    Get the current level for the user.

    Each Telegram user gets their own level through
    context.user_data.
    """

    if not context:
        return DEFAULT_LEVEL

    level = context.user_data.get(
        "games_level",
        DEFAULT_LEVEL,
    )

    level = normalize_level(level)

    context.user_data["games_level"] = level

    return level


def set_level(context, level):
    """
    Save the user's selected level.
    """

    level = normalize_level(level)

    if context:
        context.user_data["games_level"] = level

    return level


# ==========================================================
# GAME STATE
# ==========================================================

def get_current_game(context):
    """
    Return the game currently being played by the user.
    """

    if not context:
        return None

    game = context.user_data.get(
        "games_current_game"
    )

    if game not in VALID_GAMES:
        return None

    return game


def set_current_game(context, game):
    """
    Save the game currently being played.
    """

    if game not in VALID_GAMES:
        return None

    if context:
        context.user_data[
            "games_current_game"
        ] = game

    return game


def clear_current_game(context):
    """
    Clear the user's current game.
    """

    if context:
        context.user_data.pop(
            "games_current_game",
            None,
        )


# ==========================================================
# PROMPT MEMORY
# ==========================================================

def get_used_prompts(context, game, level):
    """
    Return prompts already used during the current
    game session.

    This helps prevent the same question from appearing
    repeatedly until the available prompts have been used.
    """

    if not context:
        return set()

    used = context.user_data.setdefault(
        "games_used_prompts",
        {},
    )

    game_used = used.setdefault(
        game,
        {},
    )

    level_used = game_used.setdefault(
        level,
        [],
    )

    return set(level_used)


def remember_prompt(
    context,
    game,
    level,
    prompt,
):
    """
    Remember a prompt that was shown to the user.
    """

    if not context:
        return

    used = context.user_data.setdefault(
        "games_used_prompts",
        {},
    )

    game_used = used.setdefault(
        game,
        {},
    )

    level_used = game_used.setdefault(
        level,
        [],
    )

    if prompt not in level_used:
        level_used.append(prompt)


def reset_used_prompts(
    context,
    game=None,
    level=None,
):
    """
    Reset prompt history.

    Examples:

        reset_used_prompts(context)

        reset_used_prompts(
            context,
            "truthdare",
        )

        reset_used_prompts(
            context,
            "truthdare",
            "spicy",
        )
    """

    if not context:
        return

    if game is None:

        context.user_data.pop(
            "games_used_prompts",
            None,
        )

        return

    used = context.user_data.get(
        "games_used_prompts",
        {},
    )

    if game not in used:
        return

    if level is None:

        used.pop(game, None)

        return

    used[game].pop(level, None)


# ==========================================================
# RANDOM PROMPT
# ==========================================================

def get_random_prompt(
    context,
    game,
    level,
    prompts,
):
    """
    Select a random prompt while attempting to avoid
    repeats.

    When every prompt has been used, the history for that
    game/level is automatically reset and a new prompt
    is selected.
    """

    level = normalize_level(level)

    if not prompts:
        return None

    prompt_list = list(prompts)

    used = get_used_prompts(
        context,
        game,
        level,
    )

    available = [
        prompt
        for prompt in prompt_list
        if prompt not in used
    ]

    if not available:

        reset_used_prompts(
            context,
            game,
            level,
        )

        available = prompt_list

    prompt = random.choice(
        available
    )

    remember_prompt(
        context,
        game,
        level,
        prompt,
    )

    return prompt


# ==========================================================
# GAME MENU KEYBOARD
# ==========================================================

def games_back_keyboard():
    """
    Generic back-to-Games button.
    """

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="games_menu",
                )
            ]
        ]
    )


# ==========================================================
# LEVEL MENU
# ==========================================================

def level_keyboard(
    prefix,
):
    """
    Build a level-selection keyboard.

    prefix example:

        truthdare
        wouldyourather
        neverhaveiever
        thisorthat
    """

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 Mild",
                    callback_data=(
                        f"{prefix}_level_mild"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data=(
                        f"{prefix}_level_spicy"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data=(
                        f"{prefix}_level_extreme"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Games",
                    callback_data="games_menu",
                )
            ],
        ]
    )


# ==========================================================
# STANDARD GAME BUTTONS
# ==========================================================

def standard_game_keyboard(
    game,
    level=None,
    include_level=True,
):
    """
    Build a standard game navigation keyboard.

    Individual games can add their own specialized
    buttons on top of this structure.
    """

    buttons = []

    if game == GAME_TRUTH_DARE:

        buttons.append(
            [
                InlineKeyboardButton(
                    "🔥 Truth",
                    callback_data=(
                        "truthdare_truth"
                    ),
                ),
                InlineKeyboardButton(
                    "😈 Dare",
                    callback_data=(
                        "truthdare_dare"
                    ),
                ),
            ]
        )

    elif game == GAME_WOULD_YOU_RATHER:

        buttons.append(
            [
                InlineKeyboardButton(
                    "🤔 Another One",
                    callback_data=(
                        "wyr_question"
                    ),
                )
            ]
        )

    elif game == GAME_NEVER_HAVE_I_EVER:

        buttons.append(
            [
                InlineKeyboardButton(
                    "🙈 Next Statement",
                    callback_data=(
                        "nhie_statement"
                    ),
                )
            ]
        )

    elif game == GAME_THIS_OR_THAT:

        buttons.append(
            [
                InlineKeyboardButton(
                    "⚡ Next Choice",
                    callback_data=(
                        "tot_choice"
                    ),
                )
            ]
        )

    if include_level:

        buttons.append(
            [
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data=(
                        f"{game}_menu"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🎮 Games",
                callback_data="games_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================================
# PASS KEYBOARD
# ==========================================================

def pass_keyboard(
    game,
    next_callback=None,
):
    """
    Create a PASS button.

    PASS never requires an explanation.
    """

    buttons = []

    if next_callback:

        buttons.append(
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data=next_callback,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "😈 PASS",
                callback_data=(
                    f"{game}_pass"
                ),
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔄 Change Level",
                callback_data=(
                    f"{game}_menu"
                ),
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                "🎮 Games",
                callback_data="games_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================================
# FULL GAME KEYBOARD
# ==========================================================

def game_prompt_keyboard(
    game,
    next_callback,
    include_pass=True,
):
    """
    Keyboard displayed beneath a game prompt.
    """

    buttons = [
        [
            InlineKeyboardButton(
                "➡️ Next",
                callback_data=next_callback,
            )
        ],
    ]

    if include_pass:

        buttons.append(
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data=(
                        f"{game}_pass"
                    ),
                )
            ]
        )

    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data=(
                        f"{game}_menu"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="games_menu",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(
        buttons
    )


# ==========================================================
# DISPLAY HELPERS
# ==========================================================

def level_label(level):
    """
    Return the friendly display name for a level.
    """

    level = normalize_level(level)

    return LEVEL_DISPLAY.get(
        level,
        LEVEL_DISPLAY[DEFAULT_LEVEL],
    )


def game_header(
    title,
    level,
):
    """
    Create a consistent game header.
    """

    return (
        f"{title}\n\n"
        f"Level: {level_label(level)}"
    )


# ==========================================================
# PASS MESSAGE
# ==========================================================

def pass_message(game_title):
    """
    Standard PASS response.
    """

    return (
        f"{game_title}\n\n"
        "😈 PASS accepted.\n\n"
        "No explanation needed. "
        "Choose another prompt when you're ready."
    )


# ==========================================================
# ERROR-SAFE CALLBACK EDIT
# ==========================================================

async def safe_edit(
    query,
    text,
    reply_markup=None,
    parse_mode=None,
):
    """
    Safely edit an inline-button message.

    Telegram can throw an error when the message has
    already been changed or is otherwise unavailable.
    """

    if not query:
        return False

    try:

        kwargs = {
            "text": text,
        }

        if reply_markup is not None:
            kwargs["reply_markup"] = reply_markup

        if parse_mode is not None:
            kwargs["parse_mode"] = parse_mode

        await query.edit_message_text(
            **kwargs
        )

        return True

    except Exception as exc:

        logger.debug(
            "Unable to edit game message: %s",
            exc,
        )

        return False


# ==========================================================
# CALLBACK ANSWER
# ==========================================================

async def safe_answer(
    query,
    text=None,
    show_alert=False,
):
    """
    Safely answer an inline keyboard callback.
    """

    if not query:
        return

    try:

        if text:

            await query.answer(
                text=text,
                show_alert=show_alert,
            )

        else:

            await query.answer()

    except Exception as exc:

        logger.debug(
            "Unable to answer callback: %s",
            exc,
        )


# ==========================================================
# END game_engine.py
# ==========================================================
