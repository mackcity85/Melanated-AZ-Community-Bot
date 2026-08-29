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
#   - PASS always allowed
#   - Next statement
#   - Change level
#   - Personal player score
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
        "Never have I ever had a crush on someone I couldn't have.",
        "Never have I ever flirted with someone just for fun.",
        "Never have I ever sent a message and immediately regretted it.",
        "Never have I ever pretended not to notice someone checking me out.",
        "Never have I ever had a crush on a friend.",
        "Never have I ever gone on a spontaneous date.",
        "Never have I ever used a pickup line.",
        "Never have I ever flirted with someone I just met.",
        "Never have I ever had chemistry with someone completely unexpected.",
        "Never have I ever gotten butterflies from a text message.",
        "Never have I ever gone somewhere just because someone I liked was there.",
        "Never have I ever had a secret crush.",
        "Never have I ever caught someone flirting with me.",
        "Never have I ever made the first move.",
        "Never have I ever changed my outfit because I knew someone attractive would be there.",
        "Never have I ever complimented someone hoping they would flirt back.",
        "Never have I ever stayed up way too late talking to someone new.",
        "Never have I ever exchanged numbers with someone I met that night.",
        "Never have I ever been attracted to someone's personality before their appearance.",
    ],

    # ======================================================
    # SPICY
    # ======================================================

    "spicy": [

        "Never have I ever kissed someone on a first date.",
        "Never have I ever had chemistry with someone I wasn't expecting.",
        "Never have I ever sent a flirty picture.",
        "Never have I ever had a crush on someone in this type of community.",
        "Never have I ever flirted with someone while my partner knew about it.",
        "Never have I ever gone on a date that turned much more interesting than expected.",
        "Never have I ever kissed someone I had just met.",
        "Never have I ever had a fantasy about someone I knew.",
        "Never have I ever intentionally teased someone because I knew they liked it.",
        "Never have I ever had a conversation that became unexpectedly seductive.",
        "Never have I ever exchanged spicy messages with someone.",
        "Never have I ever had a secret fantasy I hadn't told anyone.",
        "Never have I ever been attracted to someone because of their confidence.",
        "Never have I ever had an attraction that I tried to ignore.",
        "Never have I ever gone somewhere knowing there was a chance I would meet someone attractive.",
        "Never have I ever intentionally built anticipation with someone.",
        "Never have I ever flirted with more than one person at the same time.",
        "Never have I ever been tempted to make the first move but waited for them.",
        "Never have I ever had a fantasy involving a couple.",
        "Never have I ever considered exploring something outside my normal comfort zone.",
        "Never have I ever had a conversation that made me blush.",
        "Never have I ever told someone exactly what I wanted.",
        "Never have I ever been attracted to someone's voice.",
        "Never have I ever been attracted to someone's energy before seeing them in person.",
        "Never have I ever intentionally dressed to get someone's attention.",
    ],

    # ======================================================
    # EXTREME
    # ======================================================

    "extreme": [

        "Never have I ever explored a fantasy with another consenting adult.",
        "Never have I ever had a fantasy involving more than two people.",
        "Never have I ever discussed a kink with a potential partner.",
        "Never have I ever tried something specifically because a partner wanted to explore it.",
        "Never have I ever attended an adults-only event.",
        "Never have I ever had an adventurous experience I couldn't believe I actually tried.",
        "Never have I ever explored something completely outside my usual type.",
        "Never have I ever had a fantasy that I was nervous to admit.",
        "Never have I ever discussed boundaries before an intimate experience.",
        "Never have I ever negotiated limits before trying something new.",
        "Never have I ever explored a fantasy with a couple.",
        "Never have I ever considered inviting another consenting adult into an experience.",
        "Never have I ever had a fantasy involving someone I met unexpectedly.",
        "Never have I ever tried something adventurous and wanted to do it again.",
        "Never have I ever had a fantasy that stayed on my bucket list.",
        "Never have I ever told a partner about a fantasy I had been keeping secret.",
        "Never have I ever explored a new dynamic with someone I trusted.",
        "Never have I ever changed my mind about something after discussing boundaries.",
        "Never have I ever said YES to an experience that initially made me nervous.",
        "Never have I ever said HARD NO to something someone suggested.",
        "Never have I ever had an adults-only adventure that became a great story.",
        "Never have I ever had chemistry with someone I absolutely did not expect.",
        "Never have I ever discussed a fantasy with someone I had just met.",
        "Never have I ever intentionally pushed myself outside my normal dating comfort zone.",
        "Never have I ever had an experience that changed what I thought I was interested in.",
    ],
}


# ==========================================================
# ENABLED STATUS
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
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="nhie_level_extreme",
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
                InlineKeyboardButton(
                    "🔄 Change Level",
                    callback_data="nhie_menu",
                ),
            ],
        ]
    )


# ==========================================================
# SCORE
# ==========================================================

def initialize_score(context):

    if "nhie_have" not in context.user_data:
        context.user_data["nhie_have"] = 0

    if "nhie_never" not in context.user_data:
        context.user_data["nhie_never"] = 0

    if "nhie_pass" not in context.user_data:
        context.user_data["nhie_pass"] = 0

    if "nhie_total" not in context.user_data:
        context.user_data["nhie_total"] = 0


def score_text(context):

    initialize_score(context)

    return (
        f"🙋 I Have: {context.user_data['nhie_have']}\n"
        f"😇 Never: {context.user_data['nhie_never']}\n"
        f"😈 Passes: {context.user_data['nhie_pass']}\n"
        f"🎮 Played: {context.user_data['nhie_total']}"
    )


# ==========================================================
# GET STATEMENT
# ==========================================================

def get_statement(context):

    level = get_level(context)

    statement = random.choice(
        STATEMENTS[level]
    )

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
        "🙋 NEVER HAVE I EVER\n\n"
        f"🎯 Level: {level.upper()}\n\n"
        f"{statement}\n\n"
        f"{score_text(context)}\n\n"
        "Choose your answer."
    )


# ==========================================================
# START GAME
# ==========================================================

async def start_game(
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
            "🙋 Never Have I Ever is currently disabled."
        )

        return

    initialize_score(context)

    await message.reply_text(
        "🙋 NEVER HAVE I EVER\n\n"
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

        try:
            await query.answer(
                "Never Have I Ever is disabled.",
                show_alert=True,
            )
        except Exception:
            pass

        return

    initialize_score(context)

    # ======================================================
    # MENU
    # ======================================================

    if data == "nhie_menu":

        await query.edit_message_text(
            "🙋 NEVER HAVE I EVER\n\n"
            "Choose your level:\n\n"
            "🟢 Mild — fun & flirty\n"
            "🌶️ Spicy — adult-community vibes\n"
            "🔥 Extreme — bold & adventurous\n\n"
            "😈 PASS is always allowed.",
            reply_markup=level_keyboard(),
        )

        return

    # ======================================================
    # LEVEL
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

        await start_game(
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
                "You already answered this one.",
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
            "nhie_total"
        ] += 1

        await query.answer(
            "🙋 I HAVE!",
            show_alert=True,
        )

        text = (
            "🙋 I HAVE!\n\n"
            "No judgment. 😈\n\n"
            f"{score_text(context)}"
        )

        keyboard = InlineKeyboardMarkup(
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
                ],
            ]
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
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
                "You already answered this one.",
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
            "nhie_total"
        ] += 1

        await query.answer(
            "😇 NEVER!",
            show_alert=True,
        )

        text = (
            "😇 NEVER!\n\n"
            "Respect the boundaries. 💜\n\n"
            f"{score_text(context)}"
        )

        keyboard = InlineKeyboardMarkup(
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
                ],
            ]
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
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
                "This one is already finished.",
                show_alert=True,
            )

            return

        context.user_data[
            "nhie_answered"
        ] = True

        context.user_data[
            "nhie_pass"
        ] += 1

        context.user_data[
            "nhie_total"
        ] += 1

        await query.answer(
            "😈 PASS accepted!",
            show_alert=True,
        )

        text = (
            "😈 PASS ACCEPTED\n\n"
            "No explanation needed. 💜\n\n"
            f"{score_text(context)}"
        )

        keyboard = InlineKeyboardMarkup(
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
                ],
            ]
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
        )

        return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "nhie_next":

        await start_game(
            query,
            context,
        )

        return


# ==========================================================
# RESET SCORE
# ==========================================================

def reset_score(context):

    context.user_data[
        "nhie_have"
    ] = 0

    context.user_data[
        "nhie_never"
    ] = 0

    context.user_data[
        "nhie_pass"
    ] = 0

    context.user_data[
        "nhie_total"
    ] = 0

    context.user_data[
        "nhie_answered"
    ] = False


# ==========================================================
# END never_have_i_ever.py
# ==========================================================
