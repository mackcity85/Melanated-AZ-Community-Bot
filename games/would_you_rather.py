# ==========================================================
# Melanated AZ Bot
# games/would_you_rather.py
# ==========================================================

import random

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


QUESTIONS = [

    (
        "Would you rather have unlimited money 💰 "
        "or unlimited free time ⏰?",
        "money",
        "time",
    ),

    (
        "Would you rather travel the world 🌎 "
        "or live in your dream home 🏡?",
        "travel",
        "home",
    ),

    (
        "Would you rather always be 10 minutes early "
        "or always be 10 minutes late?",
        "early",
        "late",
    ),

    (
        "Would you rather have the ability to fly 🦅 "
        "or become invisible 👻?",
        "fly",
        "invisible",
    ),

    (
        "Would you rather be famous 🎤 "
        "or completely anonymous 🥷?",
        "famous",
        "anonymous",
    ),

    (
        "Would you rather have unlimited food 🍔 "
        "or unlimited travel ✈️?",
        "food",
        "travel",
    ),

    (
        "Would you rather never use social media again "
        "or never watch TV again?",
        "social",
        "tv",
    ),

    (
        "Would you rather live at the beach 🏖️ "
        "or in the mountains 🏔️?",
        "beach",
        "mountains",
    ),

    (
        "Would you rather be incredibly intelligent 🧠 "
        "or incredibly athletic 🏆?",
        "intelligent",
        "athletic",
    ),

    (
        "Would you rather know your future 🔮 "
        "or change your past?",
        "future",
        "past",
    ),
]


def keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "A",
                    callback_data="wyr_a",
                ),
                InlineKeyboardButton(
                    "B",
                    callback_data="wyr_b",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="wyr_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="games_main",
                ),
            ],
        ]
    )


def get_question(context):

    question = random.choice(
        QUESTIONS
    )

    context.user_data[
        "wyr_question"
    ] = question

    return question


async def start_wyr(
    query,
    context,
):

    question = get_question(
        context
    )

    text = (
        "🤔 **WOULD YOU RATHER?**\n\n"
        f"{question[0]}\n\n"
        "Choose A or B."
    )

    await query.edit_message_text(
        text,
        reply_markup=keyboard(),
        parse_mode="Markdown",
    )


async def wyr_callback(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    data = query.data or ""

    if data == "wyr_next":

        await start_wyr(
            query,
            context,
        )

        return

    question = context.user_data.get(
        "wyr_question"
    )

    if not question:
        await start_wyr(
            query,
            context,
        )
        return

    if data == "wyr_a":

        answer = question[1]

    elif data == "wyr_b":

        answer = question[2]

    else:

        return

    await query.edit_message_text(
        "🤔 **WOULD YOU RATHER?**\n\n"
        f"{question[0]}\n\n"
        f"✅ You chose: **{answer}**",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➡️ Next",
                        callback_data="wyr_next",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🎮 Games",
                        callback_data="games_main",
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )
