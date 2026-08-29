# ==========================================================
# Melanated AZ Bot
# games/game_engine.py
#
# Shared game engine
#
# Handles:
#   - Game state
#   - Player tracking
#   - Levels
#   - Scores
#   - Pass
#   - Reset
#   - Random game content
#
# IMPORTANT:
#   This file does NOT import bot.py or admin.py.
# ==========================================================

import logging
import random
from typing import Any, Dict, Optional

from .game_data import (
    GAME_DEFINITIONS,
    WOULD_YOU_RATHER,
    NEVER_HAVE_I_EVER,
    MOST_LIKELY,
    THIS_OR_THAT,
    HOT_SEAT,
    CONFESSIONS,
    COMPLIMENT_BATTLE,
    DICE_RESULTS,
    COIN_RESULTS,
)


logger = logging.getLogger(__name__)


# ==========================================================
# CONSTANTS
# ==========================================================

VALID_LEVELS = (
    "mild",
    "spicy",
    "extreme",
)


DEFAULT_LEVEL = "mild"


# ==========================================================
# GAME STATE
# ==========================================================

def get_game_state(context) -> Dict[str, Any]:
    """
    Get the current user's game state.

    State is stored in Telegram user_data so every player
    can have their own current game level and score.
    """

    state = context.user_data.get(
        "games_state"
    )

    if not isinstance(state, dict):
        state = {
            "level": DEFAULT_LEVEL,
            "score": 0,
            "rounds": 0,
            "passes": 0,
            "current_game": None,
            "current_prompt": None,
        }

        context.user_data[
            "games_state"
        ] = state

    return state


# ==========================================================
# LEVEL
# ==========================================================

def get_level(context) -> str:
    """
    Return the current game level.
    """

    state = get_game_state(context)

    level = state.get(
        "level",
        DEFAULT_LEVEL,
    )

    if level not in VALID_LEVELS:
        level = DEFAULT_LEVEL
        state["level"] = level

    return level


def set_level(
    context,
    level: str,
) -> str:
    """
    Set the current game level.

    Invalid levels automatically become mild.
    """

    level = str(level or "").lower().strip()

    if level not in VALID_LEVELS:
        level = DEFAULT_LEVEL

    state = get_game_state(context)

    state["level"] = level

    return level


# ==========================================================
# SCORE
# ==========================================================

def get_score(context) -> int:
    """
    Return the current score.
    """

    state = get_game_state(context)

    try:
        return int(
            state.get(
                "score",
                0,
            )
        )

    except (TypeError, ValueError):
        state["score"] = 0
        return 0


def add_score(
    context,
    amount: int = 1,
) -> int:
    """
    Add points to the current player's score.
    """

    state = get_game_state(context)

    try:
        amount = int(amount)

    except (TypeError, ValueError):
        amount = 1

    state["score"] = (
        get_score(context) + amount
    )

    return state["score"]


def reset_score(context) -> None:
    """
    Reset the current player's score.
    """

    state = get_game_state(context)

    state["score"] = 0


# ==========================================================
# ROUNDS
# ==========================================================

def get_rounds(context) -> int:
    """
    Return number of completed rounds.
    """

    state = get_game_state(context)

    try:
        return int(
            state.get(
                "rounds",
                0,
            )
        )

    except (TypeError, ValueError):
        state["rounds"] = 0
        return 0


def add_round(context) -> int:
    """
    Add one completed round.
    """

    state = get_game_state(context)

    state["rounds"] = (
        get_rounds(context) + 1
    )

    return state["rounds"]


# ==========================================================
# PASSES
# ==========================================================

def get_passes(context) -> int:
    """
    Return number of passes.
    """

    state = get_game_state(context)

    try:
        return int(
            state.get(
                "passes",
                0,
            )
        )

    except (TypeError, ValueError):
        state["passes"] = 0
        return 0


def add_pass(context) -> int:
    """
    Record a PASS.

    PASS never costs points.
    """

    state = get_game_state(context)

    state["passes"] = (
        get_passes(context) + 1
    )

    return state["passes"]


# ==========================================================
# CURRENT GAME
# ==========================================================

def set_current_game(
    context,
    game_key: Optional[str],
) -> None:
    """
    Store the current game.
    """

    state = get_game_state(context)

    state["current_game"] = game_key


def get_current_game(context):
    """
    Return current game key.
    """

    state = get_game_state(context)

    return state.get(
        "current_game"
    )


def set_current_prompt(
    context,
    prompt: Any,
) -> None:
    """
    Store the current prompt.
    """

    state = get_game_state(context)

    state["current_prompt"] = prompt


def get_current_prompt(context):
    """
    Return the current prompt.
    """

    state = get_game_state(context)

    return state.get(
        "current_prompt"
    )


# ==========================================================
# RESET GAME
# ==========================================================

def reset_game(
    context,
    keep_level: bool = True,
) -> None:
    """
    Reset game state.

    By default the player's selected level remains.
    """

    old_level = get_level(context)

    context.user_data[
        "games_state"
    ] = {
        "level": (
            old_level
            if keep_level
            else DEFAULT_LEVEL
        ),
        "score": 0,
        "rounds": 0,
        "passes": 0,
        "current_game": None,
        "current_prompt": None,
    }


# ==========================================================
# GAME LOOKUP
# ==========================================================

def get_game_definition(
    game_key: str,
) -> Optional[Dict[str, Any]]:
    """
    Return a game definition.
    """

    return GAME_DEFINITIONS.get(
        game_key
    )


def game_exists(
    game_key: str,
) -> bool:
    """
    Check whether a game exists.
    """

    return game_key in GAME_DEFINITIONS


# ==========================================================
# RANDOM CONTENT
# ==========================================================

def random_would_you_rather(
    level: str = DEFAULT_LEVEL,
):
    """
    Return a random Would You Rather question.
    """

    questions = WOULD_YOU_RATHER.get(
        level,
        WOULD_YOU_RATHER[DEFAULT_LEVEL],
    )

    return random.choice(
        questions
    )


def random_never_have_i_ever(
    level: str = DEFAULT_LEVEL,
):
    """
    Return a random Never Have I Ever statement.
    """

    questions = NEVER_HAVE_I_EVER.get(
        level,
        NEVER_HAVE_I_EVER[DEFAULT_LEVEL],
    )

    return random.choice(
        questions
    )


def random_most_likely(
    level: str = DEFAULT_LEVEL,
):
    """
    Return a random Most Likely To question.
    """

    questions = MOST_LIKELY.get(
        level,
        MOST_LIKELY[DEFAULT_LEVEL],
    )

    return random.choice(
        questions
    )


def random_this_or_that(
    level: str = DEFAULT_LEVEL,
):
    """
    Return a random This or That question.
    """

    choices = THIS_OR_THAT.get(
        level,
        THIS_OR_THAT[DEFAULT_LEVEL],
    )

    return random.choice(
        choices
    )


def random_hot_seat(
    level: str = DEFAULT_LEVEL,
):
    """
    Return a random Hot Seat question.
    """

    questions = HOT_SEAT.get(
        level,
        HOT_SEAT[DEFAULT_LEVEL],
    )

    return random.choice(
        questions
    )


def random_confession(
    level: str = DEFAULT_LEVEL,
):
    """
    Return a random confession prompt.
    """

    questions = CONFESSIONS.get(
        level,
        CONFESSIONS[DEFAULT_LEVEL],
    )

    return random.choice(
        questions
    )


def random_compliment():
    """
    Return a random compliment challenge.
    """

    return random.choice(
        COMPLIMENT_BATTLE
    )


def random_dice():
    """
    Return a random dice result.
    """

    return random.choice(
        DICE_RESULTS
    )


def random_coin():
    """
    Return a random coin result.
    """

    return random.choice(
        COIN_RESULTS
    )


# ==========================================================
# DICE ROLL
# ==========================================================

def roll_dice() -> int:
    """
    Roll a standard six-sided die.
    """

    return random.randint(
        1,
        6,
    )


# ==========================================================
# COIN FLIP
# ==========================================================

def flip_coin() -> str:
    """
    Return HEADS or TAILS.
    """

    return random.choice(
        (
            "HEADS",
            "TAILS",
        )
    )


# ==========================================================
# PLAYER NAME
# ==========================================================

def get_player_name(update) -> str:
    """
    Safely determine the player's display name.
    """

    user = update.effective_user

    if not user:
        return "Player"

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return "Player"


# ==========================================================
# GAME ROUND
# ==========================================================

def start_round(
    context,
    game_key: str,
    prompt: Any,
) -> None:
    """
    Start and store a new game round.
    """

    set_current_game(
        context,
        game_key,
    )

    set_current_prompt(
        context,
        prompt,
    )

    add_round(context)


# ==========================================================
# COMPLETE ROUND
# ==========================================================

def complete_round(
    context,
    points: int = 1,
) -> int:
    """
    Complete the current round and award points.
    """

    return add_score(
        context,
        points,
    )


# ==========================================================
# PASS
# ==========================================================

def pass_current_round(
    context,
) -> int:
    """
    Pass the current challenge.

    Passing does not remove points.
    """

    add_pass(context)

    state = get_game_state(context)

    state["current_prompt"] = None

    return get_passes(context)


# ==========================================================
# GAME STATISTICS
# ==========================================================

def get_statistics(
    context,
) -> Dict[str, int]:
    """
    Return current player statistics.
    """

    return {
        "score": get_score(context),
        "rounds": get_rounds(context),
        "passes": get_passes(context),
    }


# ==========================================================
# FORMAT STATISTICS
# ==========================================================

def format_statistics(
    context,
) -> str:
    """
    Format player statistics for Telegram.
    """

    stats = get_statistics(
        context
    )

    level = get_level(
        context
    )

    return (
        "🎮 YOUR GAME STATS\n\n"
        f"🏆 Score: {stats['score']}\n"
        f"🎯 Rounds: {stats['rounds']}\n"
        f"😈 Passes: {stats['passes']}\n"
        f"🔥 Level: {level.upper()}"
    )


# ==========================================================
# SAFE CALLBACK PARSER
# ==========================================================

def parse_callback(
    callback_data: str,
):
    """
    Split callback data safely.

    Example:

        game_wyr:mild

    becomes:

        ("game_wyr", "mild")
    """

    if not callback_data:
        return (
            "",
            "",
        )

    parts = callback_data.split(
        ":",
        1,
    )

    if len(parts) == 1:
        return (
            parts[0],
            "",
        )

    return (
        parts[0],
        parts[1],
    )


# ==========================================================
# CALLBACK LEVEL
# ==========================================================

def level_from_callback(
    callback_data: str,
) -> Optional[str]:
    """
    Extract a valid level from callback data.
    """

    _, value = parse_callback(
        callback_data
    )

    if value in VALID_LEVELS:
        return value

    return None


# ==========================================================
# LOGGING HELPER
# ==========================================================

def log_game_event(
    game_key: str,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
) -> None:
    """
    Log game activity.

    This intentionally does not log game answers or
    potentially sensitive player content.
    """

    logger.info(
        "Game event | game=%s | user_id=%s | action=%s",
        game_key,
        user_id,
        action,
    )


# ==========================================================
# END game_engine.py
# ==========================================================
