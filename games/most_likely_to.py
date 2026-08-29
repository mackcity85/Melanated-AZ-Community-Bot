# ==========================================================
# Melanated AZ Bot
# games/most_likely_to.py
#
# MOST LIKELY TO
#
# Features:
#   - Button-based game
#   - Mild / Spicy / Extreme
#   - Random prompts
#   - Player selection
#   - PASS allowed
#   - Next prompt
#   - Change level
#   - Player statistics
#
# This file does NOT import from games.py.
# This prevents circular imports.
# ==========================================================

import logging
import random

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


# ==========================================================
# SETTINGS
# ==========================================================

MOST_LIKELY_ENABLED = True

VALID_LEVELS = (
    "mild",
    "spicy",
    "extreme",
)


# ==========================================================
# PROMPTS
# ==========================================================

PROMPTS = {

    # ======================================================
    # MILD
    # ======================================================

    "mild": [

        "Who is most likely to make the first move?",
        "Who is most likely to start a conversation with a stranger?",
        "Who is most likely to plan an amazing date?",
        "Who is most likely to flirt without realizing it?",
        "Who is most likely to stay up all night talking?",
        "Who is most likely to make everyone laugh?",
        "Who is most likely to send the first message?",
        "Who is most likely to have a secret crush?",
        "Who is most likely to organize a group outing?",
        "Who is most likely to try something new?",
        "Who is most likely to make someone blush?",
        "Who is most likely to give the best compliment?",
        "Who is most likely to fall for someone's personality first?",
        "Who is most likely to have the best pickup line?",
        "Who is most likely to turn a casual conversation into flirting?",
        "Who is most likely to plan a spontaneous adventure?",
        "Who is most likely to remember everyone's birthday?",
        "Who is most likely to make a new friend tonight?",
        "Who is most likely to get caught checking someone out?",
        "Who is most likely to have the best date story?",
        "Who is most likely to break the ice in an awkward situation?",
        "Who is most likely to make the first romantic gesture?",
        "Who is most likely to dance with someone they just met?",
        "Who is most likely to compliment someone's outfit?",
        "Who is most likely to turn a boring night into a fun one?",
    ],

    # ======================================================
    # SPICY
    # ======================================================

    "spicy": [

        "Who is most likely to send a flirty message first?",
        "Who is most likely to make someone blush?",
        "Who is most likely to have the boldest pickup line?",
        "Who is most likely to flirt across the room?",
        "Who is most likely to make the first move?",
        "Who is most likely to turn a conversation spicy?",
        "Who is most likely to plan an adults-only date?",
        "Who is most likely to tease someone just because they enjoy the reaction?",
        "Who is most likely to have unexpected chemistry with someone?",
        "Who is most likely to send a message that makes someone blush?",
        "Who is most likely to suggest moving a conversation to private chat?",
        "Who is most likely to have the most adventurous date?",
        "Who is most likely to flirt with someone they just met?",
        "Who is most likely to be the biggest tease?",
        "Who is most likely to receive the most DMs?",
        "Who is most likely to make someone nervous in a good way?",
        "Who is most likely to plan a spontaneous romantic adventure?",
        "Who is most likely to admit they are attracted to someone first?",
        "Who is most likely to create instant chemistry?",
        "Who is most likely to make a bold romantic move?",
        "Who is most likely to have a secret admirer?",
        "Who is most likely to suggest trying something new?",
        "Who is most likely to turn flirting into an actual date?",
        "Who is most likely to make someone forget what they were saying?",
        "Who is most likely to have the most interesting dating story?",
        "Who is most likely to make the room's energy change when they walk in?",
        "Who is most likely to be the one doing the pursuing?",
        "Who is most likely to enjoy being pursued?",
        "Who is most likely to create the most tension without saying much?",
        "Who is most likely to leave someone wanting more?",
    ],

    # ======================================================
    # EXTREME
    # ======================================================

    "extreme": [

        "Who is most likely to suggest an adventurous experience?",
        "Who is most likely to have the boldest fantasy?",
        "Who is most likely to try something completely new with a consenting partner?",
        "Who is most likely to attend an adults-only event?",
        "Who is most likely to suggest exploring a new kink?",
        "Who is most likely to have the wildest date story?",
        "Who is most likely to make a bold move when the chemistry is strong?",
        "Who is most likely to plan an adventurous night?",
        "Who is most likely to talk openly about their fantasies?",
        "Who is most likely to suggest a spontaneous adults-only adventure?",
        "Who is most likely to have a secret adventurous side?",
        "Who is most likely to surprise their partner with a new idea?",
        "Who is most likely to say YES to a new experience after discussing boundaries?",
        "Who is most likely to have the most interesting bucket list?",
        "Who is most likely to suggest something outside their normal comfort zone?",
        "Who is most likely to have the boldest answer in this game?",
        "Who is most likely to turn chemistry into an adventure?",
        "Who is most likely to be curious about exploring with another consenting adult?",
        "Who is most likely to have an unexpected fantasy?",
        "Who is most likely to suggest a private adults-only gathering?",
        "Who is most likely to make the first bold move?",
        "Who is most likely to enjoy being the center of attention?",
        "Who is most likely to surprise everyone with their answer?",
        "Who is most likely to have a hidden adventurous side?",
        "Who is most likely to say 'let's try it' after establishing consent?",
        "Who is most likely to have the most adventurous weekend?",
        "Who is most likely to discover a new kink through a partner?",
        "Who is most likely to plan an unforgettable adults-only date?",
        "Who is most likely to be the biggest flirt in the room?",
        "Who is most likely to create undeniable chemistry?",
    ],
}


# ==========================================================
# LEVEL NAMES
# ==========================================================

LEVEL_NAMES = {
    "mild": "🟢 Mild",
    "spicy": "🌶️ Spicy",
    "extreme": "🔥 Extreme",
}


# ==========================================================
# ENABLED
# ==========================================================

def is_enabled():
    return MOST_LIKELY_ENABLED


# ==========================================================
# GET LEVEL
# ==========================================================

def get_level(context):

    level = context.user_data.get(
        "most_likely_level",
        "mild",
    )

    if level not in VALID_LEVELS:
        level = "mild"

    return level


# ==========================================================
# LEVEL KEYBOARD
# ==========================================================

def level_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 Mild",
                    callback_data="mostlikely_level_mild",
                ),
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data="mostlikely_level_spicy",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="mostlikely_level_extreme",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 Games",
                    callback_data="games_menu",
                ),
            ],
        ]
    )


# ==========================================================
# GAME KEYBOARD
# ==========================================================

def game_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👑 PICK SOMEONE",
                    callback_data="mostlikely_pick",
                ),
            ],
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="mostlikely_pass",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="mostlikely_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data="mostlikely_menu",
                ),
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="games_menu",
                ),
            ],
        ]
    )


# ==========================================================
# RESULT KEYBOARD
# ==========================================================

def result_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="mostlikely_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data="mostlikely_menu",
                ),
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="games_menu",
                ),
            ],
        ]
    )


# ==========================================================
# STATS
# ==========================================================

def initialize_stats(context):

    if "mostlikely_picks" not in context.user_data:
        context.user_data["mostlikely_picks"] = 0

    if "mostlikely_passes" not in context.user_data:
        context.user_data["mostlikely_passes"] = 0

    if "mostlikely_rounds" not in context.user_data:
        context.user_data["mostlikely_rounds"] = 0


def stats_text(context):

    initialize_stats(context)

    return (
        f"👑 Picks: {context.user_data['mostlikely_picks']}\n"
        f"😈 Passes: {context.user_data['mostlikely_passes']}\n"
        f"🎯 Rounds: {context.user_data['mostlikely_rounds']}"
    )


# ==========================================================
# GET PROMPT
# ==========================================================

def get_prompt(context):

    level = get_level(context)

    prompts = PROMPTS.get(
        level,
        PROMPTS["mild"],
    )

    prompt = random.choice(prompts)

    context.user_data[
        "mostlikely_current_prompt"
    ] = prompt

    context.user_data[
        "mostlikely_answered"
    ] = False

    return prompt


# ==========================================================
# FORMAT PROMPT
# ==========================================================

def format_prompt(
    prompt,
    context,
):

    level = get_level(context)

    return (
        "👑 MOST LIKELY TO\n\n"
        f"🎯 Level: {LEVEL_NAMES.get(level, level)}\n\n"
        f"👉 {prompt}\n\n"
        f"{stats_text(context)}\n\n"
        "Choose someone in the chat!"
    )


# ==========================================================
# START ROUND
# ==========================================================

async def start_round(
    query,
    context,
):

    prompt = get_prompt(context)

    await query.edit_message_text(
        format_prompt(
            prompt,
            context,
        ),
        reply_markup=game_keyboard(),
    )


# ==========================================================
# /MOSTLIKELYTO
# ==========================================================

async def most_likely_to(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not MOST_LIKELY_ENABLED:

        await message.reply_text(
            "👑 Most Likely To is currently disabled."
        )

        return

    initialize_stats(context)

    await message.reply_text(
        "👑 MOST LIKELY TO\n\n"
        "Choose your level:\n\n"
        "🟢 Mild — fun & flirty\n"
        "🌶️ Spicy — adult-community vibes\n"
        "🔥 Extreme — bold & adventurous\n\n"
        "😈 PASS is always allowed.",
        reply_markup=level_keyboard(),
    )


# ==========================================================
# CALLBACK
# ==========================================================

async def callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    if not MOST_LIKELY_ENABLED:

        await query.answer(
            "Most Likely To is disabled.",
            show_alert=True,
        )

        return

    initialize_stats(context)

    # ======================================================
    # LEVEL MENU
    # ======================================================

    if data == "mostlikely_menu":

        await query.edit_message_text(
            "👑 MOST LIKELY TO\n\n"
            "Choose your level:\n\n"
            "🟢 Mild — fun & flirty\n"
            "🌶️ Spicy — adult-community vibes\n"
            "🔥 Extreme — bold & adventurous",
            reply_markup=level_keyboard(),
        )

        return

    # ======================================================
    # LEVEL SELECTION
    # ======================================================

    if data.startswith("mostlikely_level_"):

        level = data.replace(
            "mostlikely_level_",
            "",
            1,
        )

        if level not in VALID_LEVELS:
            level = "mild"

        context.user_data[
            "most_likely_level"
        ] = level

        await start_round(
            query,
            context,
        )

        return

    # ======================================================
    # PICK SOMEONE
    #
    # Telegram bots cannot automatically determine which
    # member a user is pointing at from a normal button.
    #
    # We therefore instruct the player to reply to/tag
    # someone in the chat.
    # ======================================================

    if data == "mostlikely_pick":

        if context.user_data.get(
            "mostlikely_answered",
            False,
        ):

            await query.answer(
                "You've already picked someone this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "mostlikely_answered"
        ] = True

        context.user_data[
            "mostlikely_picks"
        ] += 1

        context.user_data[
            "mostlikely_rounds"
        ] += 1

        await query.edit_message_text(
            "👑 MOST LIKELY TO\n\n"
            f"{context.user_data.get('mostlikely_current_prompt', '')}\n\n"
            "👑 PICK SOMEONE IN THE CHAT!\n\n"
            "Reply to or tag the person you think fits best.\n\n"
            f"{stats_text(context)}",
            reply_markup=result_keyboard(),
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "mostlikely_pass":

        if context.user_data.get(
            "mostlikely_answered",
            False,
        ):

            await query.answer(
                "You've already answered this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "mostlikely_answered"
        ] = True

        context.user_data[
            "mostlikely_passes"
        ] += 1

        context.user_data[
            "mostlikely_rounds"
        ] += 1

        await query.answer(
            "😈 PASS accepted.",
            show_alert=True,
        )

        await query.edit_message_text(
            "👑 MOST LIKELY TO\n\n"
            "😈 PASS ACCEPTED.\n\n"
            "No pressure.\n\n"
            f"{stats_text(context)}",
            reply_markup=result_keyboard(),
        )

        return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "mostlikely_next":

        await start_round(
            query,
            context,
        )

        return


# ==========================================================
# RESET STATS
# ==========================================================

def reset_stats(context):

    context.user_data[
        "mostlikely_picks"
    ] = 0

    context.user_data[
        "mostlikely_passes"
    ] = 0

    context.user_data[
        "mostlikely_rounds"
    ] = 0

    context.user_data[
        "mostlikely_answered"
    ] = False


# ==========================================================
# END most_likely_to.py
# ==========================================================
