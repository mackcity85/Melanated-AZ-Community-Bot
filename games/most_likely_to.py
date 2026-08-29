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
#   - Vote for yourself
#   - Vote for someone else by username
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
        "Who is most likely to flirt with someone first?",
        "Who is most likely to plan the perfect date?",
        "Who is most likely to stay up all night talking?",
        "Who is most likely to fall for someone's personality?",
        "Who is most likely to send the first message?",
        "Who is most likely to make everyone laugh?",
        "Who is most likely to have a secret crush?",
        "Who is most likely to organize a group adventure?",
        "Who is most likely to make someone blush?",
        "Who is most likely to break the ice at a party?",
        "Who is most likely to start dancing first?",
        "Who is most likely to remember everyone's birthday?",
        "Who is most likely to take a spontaneous trip?",
        "Who is most likely to give the best relationship advice?",
        "Who is most likely to have the best pickup line?",
        "Who is most likely to turn a friendship into something more?",
        "Who is most likely to make the first phone call?",
        "Who is most likely to make a bold entrance?",
        "Who is most likely to get everyone's attention without trying?",
        "Who is most likely to plan a surprise date?",
        "Who is most likely to make a new friend immediately?",
        "Who is most likely to be the biggest flirt?",
        "Who is most likely to have the best energy in the room?",
        "Who is most likely to convince everyone to go out?",
    ],

    # ======================================================
    # SPICY
    # ======================================================

    "spicy": [

        "Who is most likely to make the first flirty move?",
        "Who is most likely to send a spicy message first?",
        "Who is most likely to make someone blush?",
        "Who is most likely to flirt across the room?",
        "Who is most likely to turn a casual conversation into flirting?",
        "Who is most likely to have the boldest dating story?",
        "Who is most likely to plan a romantic getaway?",
        "Who is most likely to create instant chemistry?",
        "Who is most likely to tease someone they like?",
        "Who is most likely to make the first move on a date?",
        "Who is most likely to have a secret admirer?",
        "Who is most likely to flirt with someone they just met?",
        "Who is most likely to make the first kiss happen?",
        "Who is most likely to have the most adventurous dating life?",
        "Who is most likely to make someone nervous in a good way?",
        "Who is most likely to have the best flirting game?",
        "Who is most likely to start a private conversation after meeting someone?",
        "Who is most likely to make a date last all night?",
        "Who is most likely to surprise someone with a bold compliment?",
        "Who is most likely to have chemistry with someone unexpected?",
        "Who is most likely to suggest an adventurous date?",
        "Who is most likely to make the first romantic move?",
        "Who is most likely to be caught flirting?",
        "Who is most likely to turn up the heat during a date?",
        "Who is most likely to make someone think about them afterward?",
        "Who is most likely to have someone crushing on them without realizing it?",
        "Who is most likely to confidently approach someone attractive?",
        "Who is most likely to have the most interesting dating story?",
        "Who is most likely to get asked for their number?",
        "Who is most likely to leave someone wanting more?",
    ],

    # ======================================================
    # EXTREME
    # ======================================================

    "extreme": [

        "Who is most likely to suggest a wild adventure?",
        "Who is most likely to explore a new kink with a consenting partner?",
        "Who is most likely to have the boldest fantasy?",
        "Who is most likely to suggest trying something completely new?",
        "Who is most likely to attend an adults-only event?",
        "Who is most likely to plan an adventurous night?",
        "Who is most likely to flirt confidently with someone they find irresistible?",
        "Who is most likely to suggest exploring with another consenting adult?",
        "Who is most likely to have the wildest bucket list?",
        "Who is most likely to surprise their partner with an adventurous idea?",
        "Who is most likely to have a fantasy they have never told anyone?",
        "Who is most likely to say YES to a spontaneous adult adventure?",
        "Who is most likely to research a new kink before trying it?",
        "Who is most likely to establish boundaries before an adventurous experience?",
        "Who is most likely to create the perfect adults-only atmosphere?",
        "Who is most likely to turn a conversation extremely flirty?",
        "Who is most likely to suggest a fantasy to their partner?",
        "Who is most likely to try something outside their normal type?",
        "Who is most likely to have an unforgettable adults-only date?",
        "Who is most likely to make the boldest first move?",
        "Who is most likely to surprise everyone with their adventurous side?",
        "Who is most likely to suggest a consensual group adventure?",
        "Who is most likely to have the most adventurous bucket list?",
        "Who is most likely to be the biggest tease?",
        "Who is most likely to make someone blush with one sentence?",
        "Who is most likely to turn a date into an adventure?",
        "Who is most likely to have a fantasy become reality?",
        "Who is most likely to confidently discuss their boundaries?",
        "Who is most likely to suggest something nobody else expected?",
        "Who is most likely to say 'let's try it' after discussing boundaries?",
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
# LEVEL MENU
# ==========================================================

def level_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 Mild",
                    callback_data="mlt_level_mild",
                ),
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data="mlt_level_spicy",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="mlt_level_extreme",
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
                    "🙋 ME",
                    callback_data="mlt_me",
                ),
                InlineKeyboardButton(
                    "👥 SOMEONE ELSE",
                    callback_data="mlt_other",
                ),
            ],
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="mlt_pass",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="mlt_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data="mlt_menu",
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

    if "mlt_me" not in context.user_data:
        context.user_data["mlt_me"] = 0

    if "mlt_other" not in context.user_data:
        context.user_data["mlt_other"] = 0

    if "mlt_passes" not in context.user_data:
        context.user_data["mlt_passes"] = 0

    if "mlt_rounds" not in context.user_data:
        context.user_data["mlt_rounds"] = 0


def stats_text(context):

    initialize_stats(context)

    return (
        f"🙋 Votes for me: {context.user_data['mlt_me']}\n"
        f"👥 Votes for someone else: {context.user_data['mlt_other']}\n"
        f"😈 Passes: {context.user_data['mlt_passes']}\n"
        f"🎯 Rounds: {context.user_data['mlt_rounds']}"
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
        "mlt_current_prompt"
    ] = prompt

    context.user_data[
        "mlt_answered"
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
        "👀 MOST LIKELY TO\n\n"
        f"🎯 Level: {LEVEL_NAMES.get(level, level)}\n\n"
        f"👉 {prompt}\n\n"
        f"{stats_text(context)}\n\n"
        "Who are you voting for?"
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
            "👀 Most Likely To is currently disabled."
        )

        return

    initialize_stats(context)

    await message.reply_text(
        "👀 MOST LIKELY TO\n\n"
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

    if data == "mlt_menu":

        await query.edit_message_text(
            "👀 MOST LIKELY TO\n\n"
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

    if data.startswith("mlt_level_"):

        level = data.replace(
            "mlt_level_",
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
    # ME
    # ======================================================

    if data == "mlt_me":

        if context.user_data.get(
            "mlt_answered",
            False,
        ):

            await query.answer(
                "You've already voted this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "mlt_answered"
        ] = True

        context.user_data[
            "mlt_me"
        ] += 1

        context.user_data[
            "mlt_rounds"
        ] += 1

        await query.answer(
            "🙋 You picked yourself!",
            show_alert=True,
        )

        await query.edit_message_text(
            "👀 MOST LIKELY TO\n\n"
            "🙋 You picked YOURSELF!\n\n"
            f"{stats_text(context)}\n\n"
            "Ready for another?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="mlt_next",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Change Level",
                            callback_data="mlt_menu",
                        ),
                        InlineKeyboardButton(
                            "🎮 Games",
                            callback_data="games_menu",
                        ),
                    ],
                ]
            ),
        )

        return

    # ======================================================
    # SOMEONE ELSE
    # ======================================================

    if data == "mlt_other":

        if context.user_data.get(
            "mlt_answered",
            False,
        ):

            await query.answer(
                "You've already voted this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "mlt_answered"
        ] = True

        context.user_data[
            "mlt_other"
        ] += 1

        context.user_data[
            "mlt_rounds"
        ] += 1

        await query.answer(
            "👥 Someone else!",
            show_alert=True,
        )

        await query.edit_message_text(
            "👀 MOST LIKELY TO\n\n"
            "👥 You picked SOMEONE ELSE!\n\n"
            "Drop their name or tag in the chat if you want to reveal who you picked. 😉\n\n"
            f"{stats_text(context)}\n\n"
            "Ready for another?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="mlt_next",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Change Level",
                            callback_data="mlt_menu",
                        ),
                        InlineKeyboardButton(
                            "🎮 Games",
                            callback_data="games_menu",
                        ),
                    ],
                ]
            ),
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "mlt_pass":

        if context.user_data.get(
            "mlt_answered",
            False,
        ):

            await query.answer(
                "You've already answered this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "mlt_answered"
        ] = True

        context.user_data[
            "mlt_passes"
        ] += 1

        context.user_data[
            "mlt_rounds"
        ] += 1

        await query.answer(
            "😈 PASS accepted.",
            show_alert=True,
        )

        await query.edit_message_text(
            "👀 MOST LIKELY TO\n\n"
            "😈 PASS ACCEPTED.\n\n"
            "No pressure.\n\n"
            f"{stats_text(context)}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="mlt_next",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Change Level",
                            callback_data="mlt_menu",
                        ),
                        InlineKeyboardButton(
                            "🎮 Games",
                            callback_data="games_menu",
                        ),
                    ],
                ]
            ),
        )

        return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "mlt_next":

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
        "mlt_me"
    ] = 0

    context.user_data[
        "mlt_other"
    ] = 0

    context.user_data[
        "mlt_passes"
    ] = 0

    context.user_data[
        "mlt_rounds"
    ] = 0

    context.user_data[
        "mlt_answered"
    ] = False


# ==========================================================
# END most_likely_to.py
# ==========================================================
