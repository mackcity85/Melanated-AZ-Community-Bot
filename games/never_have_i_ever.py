# ==========================================================
# Melanated AZ Bot
# games/never_have_i_ever.py
#
# NEVER HAVE I EVER
#
# Features:
#   - Button-based game
#   - Mild / Spicy / Extreme
#   - Random statements
#   - "I Have" / "Never" buttons
#   - PASS allowed
#   - Next statement
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

NEVER_HAVE_I_EVER_ENABLED = True

VALID_LEVELS = (
    "mild",
    "spicy",
    "extreme",
)


# ==========================================================
# STATEMENTS
# ==========================================================

STATEMENTS = {

    # ======================================================
    # MILD
    # ======================================================

    "mild": [

        "Never have I ever stayed up all night talking to someone.",
        "Never have I ever had a crush on someone I just met.",
        "Never have I ever sent a message and immediately regretted it.",
        "Never have I ever flirted with someone just for fun.",
        "Never have I ever gone on a spontaneous date.",
        "Never have I ever had a crush on a friend.",
        "Never have I ever pretended not to notice someone flirting with me.",
        "Never have I ever fallen for someone's personality before their looks.",
        "Never have I ever given someone a fake excuse to avoid a date.",
        "Never have I ever had chemistry with someone completely unexpected.",
        "Never have I ever made the first move.",
        "Never have I ever received a pickup line that actually worked.",
        "Never have I ever sent a flirty emoji hoping someone would get the hint.",
        "Never have I ever had a secret crush.",
        "Never have I ever matched with someone online and actually met them.",
        "Never have I ever gone on a date without knowing what to expect.",
        "Never have I ever flirted with someone at a party.",
        "Never have I ever been attracted to someone's voice.",
        "Never have I ever been attracted to someone's confidence.",
        "Never have I ever changed my plans because someone interesting invited me out.",
        "Never have I ever had an instant connection with someone.",
        "Never have I ever gotten nervous around someone I liked.",
        "Never have I ever stayed up late because I didn't want a conversation to end.",
        "Never have I ever complimented someone hoping they would flirt back.",
        "Never have I ever had a date turn out much better than expected.",
    ],

    # ======================================================
    # SPICY
    # ======================================================

    "spicy": [

        "Never have I ever flirted with someone I knew was attracted to me.",
        "Never have I ever kissed someone on a first date.",
        "Never have I ever had a crush on someone I probably shouldn't have.",
        "Never have I ever sent a spicy message.",
        "Never have I ever had chemistry with someone I met online.",
        "Never have I ever flirted with someone while my partner knew about it.",
        "Never have I ever been attracted to someone simply because of their energy.",
        "Never have I ever had a date become much more exciting than planned.",
        "Never have I ever intentionally teased someone I was attracted to.",
        "Never have I ever had a fantasy about someone I knew.",
        "Never have I ever kissed someone unexpectedly.",
        "Never have I ever had a secret crush that lasted a long time.",
        "Never have I ever flirted with someone through messages for hours.",
        "Never have I ever exchanged flirty pictures with someone.",
        "Never have I ever had a conversation turn unexpectedly spicy.",
        "Never have I ever been attracted to someone else's partner after getting consent to explore.",
        "Never have I ever gone somewhere specifically because I knew an attractive person would be there.",
        "Never have I ever used flirting to get someone's attention.",
        "Never have I ever deliberately made someone blush.",
        "Never have I ever been caught flirting.",
        "Never have I ever had an attraction that surprised me.",
        "Never have I ever imagined what it would be like to kiss someone I was talking to.",
        "Never have I ever had a crush on someone from an adult community.",
        "Never have I ever considered exploring something outside my usual type.",
        "Never have I ever had chemistry with more than one person at the same time.",
        "Never have I ever planned a date specifically around creating chemistry.",
        "Never have I ever used a compliment as an excuse to start flirting.",
        "Never have I ever had someone completely change my type.",
        "Never have I ever been tempted to make a bold first move.",
        "Never have I ever had a conversation that became much more intimate than expected.",
    ],

    # ======================================================
    # EXTREME
    # ======================================================

    "extreme": [

        "Never have I ever explored a kink with a consenting partner.",
        "Never have I ever had a fantasy about someone I knew.",
        "Never have I ever had a consensual experience with more than one partner.",
        "Never have I ever discussed a fantasy with my partner that I wanted to explore.",
        "Never have I ever had a spontaneous adult adventure.",
        "Never have I ever gone somewhere specifically for an adults-only experience.",
        "Never have I ever flirted with someone while my partner was present and knew about it.",
        "Never have I ever explored outside my usual type with consenting adults.",
        "Never have I ever had a fantasy involving another couple.",
        "Never have I ever discussed boundaries before an intimate experience.",
        "Never have I ever changed my mind during an intimate experience and used my right to stop.",
        "Never have I ever had an experience that started as flirting and became much more.",
        "Never have I ever had a fantasy that I have never told anyone.",
        "Never have I ever tried something specifically because my partner was curious about it.",
        "Never have I ever attended an adults-only event.",
        "Never have I ever explored a new kink after researching it first.",
        "Never have I ever had an experience with someone I met through an adult community.",
        "Never have I ever considered a fantasy involving another consenting couple.",
        "Never have I ever had a partner ask me to try something completely new.",
        "Never have I ever created a safe word or other boundary system for an intimate experience.",
        "Never have I ever talked about limits before agreeing to an adventure.",
        "Never have I ever had an experience where communication made everything better.",
        "Never have I ever explored something I once thought I would never try.",
        "Never have I ever had a fantasy that became reality.",
        "Never have I ever had a consensual experience that surprised me in a good way.",
        "Never have I ever considered inviting another consenting adult into an experience.",
        "Never have I ever explored a fantasy with my partner without actually acting on it.",
        "Never have I ever had to establish a hard NO before an experience.",
        "Never have I ever discovered a new turn-on through consensual exploration.",
        "Never have I ever had an adventure that I would absolutely do again.",
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
    return NEVER_HAVE_I_EVER_ENABLED


# ==========================================================
# GET LEVEL
# ==========================================================

def get_level(context):

    level = context.user_data.get(
        "never_have_i_ever_level",
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
                    callback_data="nhie_level_mild",
                ),
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data="nhie_level_spicy",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="nhie_level_extreme",
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
                    "🙋 I HAVE",
                    callback_data="nhie_have",
                ),
                InlineKeyboardButton(
                    "😇 NEVER",
                    callback_data="nhie_never",
                ),
            ],
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="nhie_pass",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="nhie_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data="nhie_menu",
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

    if "nhie_have" not in context.user_data:
        context.user_data["nhie_have"] = 0

    if "nhie_never" not in context.user_data:
        context.user_data["nhie_never"] = 0

    if "nhie_passes" not in context.user_data:
        context.user_data["nhie_passes"] = 0

    if "nhie_rounds" not in context.user_data:
        context.user_data["nhie_rounds"] = 0


def stats_text(context):

    initialize_stats(context)

    return (
        f"🙋 I Have: {context.user_data['nhie_have']}\n"
        f"😇 Never: {context.user_data['nhie_never']}\n"
        f"😈 Passes: {context.user_data['nhie_passes']}\n"
        f"🎯 Rounds: {context.user_data['nhie_rounds']}"
    )


# ==========================================================
# GET STATEMENT
# ==========================================================

def get_statement(context):

    level = get_level(context)

    statements = STATEMENTS.get(
        level,
        STATEMENTS["mild"],
    )

    statement = random.choice(statements)

    context.user_data[
        "nhie_current_statement"
    ] = statement

    context.user_data[
        "nhie_answered"
    ] = False

    return statement


# ==========================================================
# FORMAT STATEMENT
# ==========================================================

def format_statement(
    statement,
    context,
):

    level = get_level(context)

    return (
        "🙈 NEVER HAVE I EVER\n\n"
        f"🎯 Level: {LEVEL_NAMES.get(level, level)}\n\n"
        f"👉 {statement}\n\n"
        f"{stats_text(context)}\n\n"
        "Be honest — or PASS. 😈"
    )


# ==========================================================
# START ROUND
# ==========================================================

async def start_round(
    query,
    context,
):

    statement = get_statement(context)

    await query.edit_message_text(
        format_statement(
            statement,
            context,
        ),
        reply_markup=game_keyboard(),
    )


# ==========================================================
# /NEVERHAVEIEVER
# ==========================================================

async def never_have_i_ever(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not NEVER_HAVE_I_EVER_ENABLED:

        await message.reply_text(
            "🙈 Never Have I Ever is currently disabled."
        )

        return

    initialize_stats(context)

    await message.reply_text(
        "🙈 NEVER HAVE I EVER\n\n"
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

    if not NEVER_HAVE_I_EVER_ENABLED:

        await query.answer(
            "Never Have I Ever is disabled.",
            show_alert=True,
        )

        return

    initialize_stats(context)

    # ======================================================
    # LEVEL MENU
    # ======================================================

    if data == "nhie_menu":

        await query.edit_message_text(
            "🙈 NEVER HAVE I EVER\n\n"
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

    if data.startswith("nhie_level_"):

        level = data.replace(
            "nhie_level_",
            "",
            1,
        )

        if level not in VALID_LEVELS:
            level = "mild"

        context.user_data[
            "never_have_i_ever_level"
        ] = level

        await start_round(
            query,
            context,
        )

        return

    # ======================================================
    # I HAVE
    # ======================================================

    if data == "nhie_have":

        if context.user_data.get(
            "nhie_answered",
            False,
        ):

            await query.answer(
                "You've already answered this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "nhie_answered"
        ] = True

        context.user_data[
            "nhie_have"
        ] += 1

        context.user_data[
            "nhie_rounds"
        ] += 1

        await query.answer(
            "🙋 I HAVE!",
            show_alert=True,
        )

        await query.edit_message_text(
            "🙈 NEVER HAVE I EVER\n\n"
            "🙋 You HAVE!\n\n"
            f"{stats_text(context)}\n\n"
            "Ready for another one?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="nhie_next",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Change Level",
                            callback_data="nhie_menu",
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
    # NEVER
    # ======================================================

    if data == "nhie_never":

        if context.user_data.get(
            "nhie_answered",
            False,
        ):

            await query.answer(
                "You've already answered this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "nhie_answered"
        ] = True

        context.user_data[
            "nhie_never"
        ] += 1

        context.user_data[
            "nhie_rounds"
        ] += 1

        await query.answer(
            "😇 NEVER!",
            show_alert=True,
        )

        await query.edit_message_text(
            "🙈 NEVER HAVE I EVER\n\n"
            "😇 You said NEVER!\n\n"
            f"{stats_text(context)}\n\n"
            "Ready for another one?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="nhie_next",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Change Level",
                            callback_data="nhie_menu",
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

    if data == "nhie_pass":

        if context.user_data.get(
            "nhie_answered",
            False,
        ):

            await query.answer(
                "You've already answered this round.",
                show_alert=True,
            )

            return

        context.user_data[
            "nhie_answered"
        ] = True

        context.user_data[
            "nhie_passes"
        ] += 1

        context.user_data[
            "nhie_rounds"
        ] += 1

        await query.answer(
            "😈 PASS accepted.",
            show_alert=True,
        )

        await query.edit_message_text(
            "🙈 NEVER HAVE I EVER\n\n"
            "😈 PASS ACCEPTED.\n\n"
            f"{stats_text(context)}\n\n"
            "No pressure. Ready for another?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➡️ Next",
                            callback_data="nhie_next",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Change Level",
                            callback_data="nhie_menu",
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

    if data == "nhie_next":

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
        "nhie_have"
    ] = 0

    context.user_data[
        "nhie_never"
    ] = 0

    context.user_data[
        "nhie_passes"
    ] = 0

    context.user_data[
        "nhie_rounds"
    ] = 0

    context.user_data[
        "nhie_answered"
    ] = False


# ==========================================================
# END never_have_i_ever.py
# ==========================================================
