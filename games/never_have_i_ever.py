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
#   - "I HAVE" / "NEVER" buttons
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

        "Never have I ever sent the first message to someone I liked.",
        "Never have I ever had a crush on someone I just met.",
        "Never have I ever flirted with someone at a party.",
        "Never have I ever stayed up all night talking to someone.",
        "Never have I ever gone on a spontaneous date.",
        "Never have I ever had a secret crush.",
        "Never have I ever pretended not to notice someone flirting with me.",
        "Never have I ever given someone my number without being asked.",
        "Never have I ever gotten nervous around someone I liked.",
        "Never have I ever had chemistry with someone completely unexpected.",
        "Never have I ever sent a flirty emoji and waited for a response.",
        "Never have I ever planned a surprise date.",
        "Never have I ever made the first move.",
        "Never have I ever had a crush on a friend.",
        "Never have I ever flirted with someone I met online.",
        "Never have I ever gone on a date without telling anyone where I was going.",
        "Never have I ever danced with someone I just met.",
        "Never have I ever complimented someone because I wanted their attention.",
        "Never have I ever stayed in a conversation because I liked the person's voice.",
        "Never have I ever caught someone checking me out.",
        "Never have I ever had someone develop a crush on me unexpectedly.",
        "Never have I ever changed my outfit because I wanted to impress someone.",
        "Never have I ever rehearsed what I was going to say before messaging someone.",
        "Never have I ever flirted just for fun.",
        "Never have I ever had an instant connection with someone.",
    ],

    # ======================================================
    # SPICY
    # ======================================================

    "spicy": [

        "Never have I ever sent a spicy message to someone.",
        "Never have I ever flirted with someone across a crowded room.",
        "Never have I ever kissed someone on a first date.",
        "Never have I ever had chemistry with someone I did not expect.",
        "Never have I ever intentionally made someone blush.",
        "Never have I ever had a secret admirer.",
        "Never have I ever flirted with someone I met through an adult community.",
        "Never have I ever gone on an adults-only date.",
        "Never have I ever exchanged flirty pictures with someone.",
        "Never have I ever teased someone because I knew they liked it.",
        "Never have I ever stayed up late having a very flirty conversation.",
        "Never have I ever had a crush on someone I probably should not have.",
        "Never have I ever made the first romantic move.",
        "Never have I ever intentionally left someone wanting more.",
        "Never have I ever had a date turn much more exciting than expected.",
        "Never have I ever flirted with someone while my partner knew about it.",
        "Never have I ever discussed a fantasy with a partner.",
        "Never have I ever considered trying something adventurous with a consenting partner.",
        "Never have I ever been attracted to someone because of their confidence.",
        "Never have I ever had an unexpected romantic connection.",
        "Never have I ever asked someone if they wanted to move the conversation to private chat.",
        "Never have I ever received a message that instantly made me blush.",
        "Never have I ever intentionally dressed to get someone's attention.",
        "Never have I ever had a flirtation that lasted longer than expected.",
        "Never have I ever been attracted to someone based entirely on their energy.",
        "Never have I ever made a bold move because the chemistry was undeniable.",
        "Never have I ever had someone confess that they were attracted to me.",
        "Never have I ever flirted with someone without knowing where it would lead.",
        "Never have I ever planned an adventurous date.",
        "Never have I ever been surprised by how attracted I was to someone.",
    ],

    # ======================================================
    # EXTREME
    # ======================================================

    "extreme": [

        "Never have I ever discussed a kink I wanted to explore.",
        "Never have I ever tried a new kink with a consenting partner.",
        "Never have I ever attended an adults-only event.",
        "Never have I ever had a fantasy become a real experience.",
        "Never have I ever explored something outside my normal comfort zone with consent.",
        "Never have I ever discussed boundaries before an adventurous experience.",
        "Never have I ever had an adults-only adventure I never expected.",
        "Never have I ever suggested trying something completely new with a partner.",
        "Never have I ever explored a fantasy with someone I trusted.",
        "Never have I ever had an adventurous date that lasted all night.",
        "Never have I ever talked openly about my biggest fantasy.",
        "Never have I ever considered exploring with another consenting adult.",
        "Never have I ever been tempted to say yes to an unexpected adventure.",
        "Never have I ever planned an adventurous night with a partner.",
        "Never have I ever tried something because my partner was curious about it.",
        "Never have I ever had a conversation about hard boundaries before playing.",
        "Never have I ever explored an adult-community event.",
        "Never have I ever been attracted to someone because of their confidence discussing kink.",
        "Never have I ever had a fantasy I was nervous to admit.",
        "Never have I ever surprised a partner with an adventurous idea.",
        "Never have I ever discussed what would make an experience a hard NO.",
        "Never have I ever discussed what would make an experience an enthusiastic YES.",
        "Never have I ever explored something I once thought I would never try.",
        "Never have I ever had chemistry convince me to consider something new.",
        "Never have I ever talked about an adult fantasy with trusted friends.",
        "Never have I ever been curious about exploring with another couple.",
        "Never have I ever considered attending a private adults-only gathering.",
        "Never have I ever had an experience that completely changed what I thought I liked.",
        "Never have I ever tried something adventurous after establishing clear consent.",
        "Never have I ever discovered a new interest because of a partner.",
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
# LEVEL MENU
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
        "Have you done it?"
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
            "🙋 You HAVE done it!\n\n"
            f"{stats_text(context)}\n\n"
            "Ready for another?",
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
            "😇 You've NEVER done it!\n\n"
            f"{stats_text(context)}\n\n"
            "Ready for another?",
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
            "No pressure.\n\n"
            f"{stats_text(context)}",
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
