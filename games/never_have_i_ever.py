# ==========================================================
# Melanated AZ Bot
# games/never_have_i_ever.py
#
# NEVER HAVE I EVER
#
# Features:
#   - Button-based gameplay
#   - Multiple categories
#   - Mild / Spicy / Extreme
#   - Random prompts
#   - "I HAVE" / "NEVER" buttons
#   - PASS always allowed
#   - Next prompt
#   - Change category
#   - Change difficulty
#   - Personal statistics
#   - No import from admin.py
#
# This file is standalone.
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

VALID_DIFFICULTIES = (
    "mild",
    "spicy",
    "extreme",
)


# ==========================================================
# PROMPTS
# ==========================================================

PROMPTS = {

    # ======================================================
    # GENERAL
    # ======================================================

    "general": {

        "mild": [

            "Never have I ever stayed up all night talking to someone.",
            "Never have I ever had a crush on someone I just met.",
            "Never have I ever sent a message and immediately regretted it.",
            "Never have I ever pretended to be busy to avoid someone.",
            "Never have I ever forgotten someone's name after meeting them.",
            "Never have I ever gone on a spontaneous adventure.",
            "Never have I ever had a crush on a friend.",
            "Never have I ever lied about liking someone's outfit.",
            "Never have I ever flirted just for fun.",
            "Never have I ever gotten nervous before a first date.",
            "Never have I ever practiced what I was going to say before calling someone.",
            "Never have I ever re-read an old conversation.",
            "Never have I ever checked someone's social media before meeting them.",
            "Never have I ever accidentally sent a message to the wrong person.",
            "Never have I ever stayed somewhere longer because I liked someone there.",
            "Never have I ever made an excuse to talk to someone.",
            "Never have I ever had a secret crush.",
            "Never have I ever changed my plans because someone I liked invited me somewhere.",
            "Never have I ever gotten butterflies from a text message.",
            "Never have I ever smiled at my phone because of someone.",
        ],

        "spicy": [

            "Never have I ever kissed someone I just met.",
            "Never have I ever flirted with someone I knew was attracted to me.",
            "Never have I ever had chemistry with someone completely unexpected.",
            "Never have I ever sent a flirty photo.",
            "Never have I ever had a crush on someone who was off limits.",
            "Never have I ever gone on a date that became much more adventurous than expected.",
            "Never have I ever flirted with someone at a party.",
            "Never have I ever used a dating app just to see who was nearby.",
            "Never have I ever intentionally made someone jealous.",
            "Never have I ever had a secret admirer.",
            "Never have I ever kissed someone on a first date.",
            "Never have I ever had a fantasy about someone I knew.",
            "Never have I ever flirted with someone through messages for hours.",
            "Never have I ever been attracted to someone because of their voice.",
            "Never have I ever had a crush on someone else's partner before knowing their relationship status.",
            "Never have I ever intentionally dressed to get someone's attention.",
            "Never have I ever had a date turn into an unexpected adventure.",
            "Never have I ever exchanged flirty pictures with someone.",
            "Never have I ever been caught flirting.",
            "Never have I ever had chemistry with someone I originally considered just a friend.",
        ],

        "extreme": [

            "Never have I ever explored a fantasy with another consenting adult.",
            "Never have I ever tried something completely outside my usual comfort zone.",
            "Never have I ever had a secret fantasy about someone I knew.",
            "Never have I ever had an adults-only adventure I never expected to have.",
            "Never have I ever explored a new kink with a trusted consenting partner.",
            "Never have I ever had chemistry with someone I absolutely did not expect.",
            "Never have I ever discussed a fantasy with a partner that I wanted to explore.",
            "Never have I ever attended an adults-only event.",
            "Never have I ever explored something new because a trusted partner was curious about it.",
            "Never have I ever had a fantasy that surprised even me.",
            "Never have I ever tried something adventurous on a date.",
            "Never have I ever had an experience that completely changed what I thought I liked.",
            "Never have I ever had a conversation about boundaries before an intimate adventure.",
            "Never have I ever explored something only because I trusted the people involved.",
            "Never have I ever had a spontaneous adults-only adventure.",
            "Never have I ever surprised a partner with something adventurous.",
            "Never have I ever had a fantasy I was nervous to admit.",
            "Never have I ever explored a new experience with multiple consenting adults.",
            "Never have I ever said yes to something adventurous after initially saying maybe.",
            "Never have I ever discovered a new interest because of someone I trusted.",
        ],
    },

    # ======================================================
    # DATING
    # ======================================================

    "dating": {

        "mild": [

            "Never have I ever had a crush on someone at work.",
            "Never have I ever gone on a blind date.",
            "Never have I ever canceled a date because I got nervous.",
            "Never have I ever arrived early to a date just to make sure everything was perfect.",
            "Never have I ever searched someone's name before a date.",
            "Never have I ever dressed differently because I knew someone I liked would be there.",
            "Never have I ever had a crush on someone I met online.",
            "Never have I ever asked a friend for dating advice.",
            "Never have I ever gone on a date with someone I met through a friend.",
            "Never have I ever stayed up late talking to a romantic interest.",
            "Never have I ever planned an entire date in my head before asking someone out.",
            "Never have I ever been nervous about making the first move.",
            "Never have I ever had a first date that lasted much longer than expected.",
            "Never have I ever fallen for someone's personality before their looks.",
            "Never have I ever had a crush on someone because of their smile.",
        ],

        "spicy": [

            "Never have I ever kissed someone on the first date.",
            "Never have I ever had a date end with a very unexpected invitation.",
            "Never have I ever flirted with someone while knowing they were flirting back.",
            "Never have I ever gone on a date primarily because I found someone extremely attractive.",
            "Never have I ever had a crush on someone I knew I probably shouldn't pursue.",
            "Never have I ever sent a suggestive text before a date.",
            "Never have I ever deliberately planned a date around creating chemistry.",
            "Never have I ever had a date become physical sooner than expected.",
            "Never have I ever gone on a date with someone I met in an adult community.",
            "Never have I ever flirted with someone at a bar or club.",
            "Never have I ever been asked to go somewhere private after a date.",
            "Never have I ever had a date that ended with us planning the next one immediately.",
            "Never have I ever had a crush on someone based almost entirely on their confidence.",
            "Never have I ever intentionally teased someone during a date.",
            "Never have I ever had chemistry with someone before learning much about them.",
        ],

        "extreme": [

            "Never have I ever had an adults-only date with someone I met online.",
            "Never have I ever gone on a date specifically to explore mutual fantasies.",
            "Never have I ever had a date involve discussing boundaries and limits.",
            "Never have I ever had a date become an adults-only adventure.",
            "Never have I ever planned a date around a fantasy.",
            "Never have I ever gone on a date with more than one consenting adult.",
            "Never have I ever met someone specifically because we shared a kink.",
            "Never have I ever had a date where the chemistry was immediate.",
            "Never have I ever discussed what I wanted to explore before meeting someone.",
            "Never have I ever had a spontaneous intimate adventure after a date.",
            "Never have I ever gone on a date where we both knew exactly what we were hoping for.",
            "Never have I ever changed my mind about a date after learning someone's boundaries.",
            "Never have I ever had an adventurous date with another couple.",
            "Never have I ever gone on a date that completely exceeded my expectations.",
            "Never have I ever trusted someone enough to try something completely new on a date.",
        ],
    },

    # ======================================================
    # ADULT COMMUNITY
    # ======================================================

    "adult": {

        "mild": [

            "Never have I ever joined an adult community out of curiosity.",
            "Never have I ever attended an adults-only social event.",
            "Never have I ever made a new friend through an adult community.",
            "Never have I ever flirted with someone I met in an adult community.",
            "Never have I ever been nervous attending an adult event for the first time.",
            "Never have I ever met someone online before meeting them in person.",
            "Never have I ever connected with someone because of a shared interest.",
            "Never have I ever had a great conversation with someone I originally expected nothing from.",
            "Never have I ever discovered a new interest through an adult community.",
            "Never have I ever made a connection that surprised me.",
        ],

        "spicy": [

            "Never have I ever exchanged flirty messages with someone from an adult community.",
            "Never have I ever attended a private adults-only gathering.",
            "Never have I ever flirted with another couple.",
            "Never have I ever been approached by another couple.",
            "Never have I ever discussed fantasies with someone I met online.",
            "Never have I ever exchanged pictures with someone I met in an adult community.",
            "Never have I ever explored a new interest because of someone I met online.",
            "Never have I ever had chemistry with someone at an adult event.",
            "Never have I ever connected with someone based on shared kinks.",
            "Never have I ever had an unexpected attraction at an adult gathering.",
        ],

        "extreme": [

            "Never have I ever explored a fantasy with another consenting adult.",
            "Never have I ever attended a lifestyle or kink event.",
            "Never have I ever explored with another couple.",
            "Never have I ever discussed a fantasy with multiple consenting adults.",
            "Never have I ever tried a new kink because a trusted partner suggested it.",
            "Never have I ever participated in a consensual group adventure.",
            "Never have I ever had an experience with someone I met through an adult community.",
            "Never have I ever explored something that was completely outside my normal routine.",
            "Never have I ever attended an adults-only party where everyone knew the boundaries.",
            "Never have I ever had a fantasy become a real experience.",
            "Never have I ever had an adults-only adventure with people I met online.",
            "Never have I ever explored a new experience after establishing clear consent.",
        ],
    },

    # ======================================================
    # FUN
    # ======================================================

    "fun": {

        "mild": [

            "Never have I ever laughed so hard that I cried.",
            "Never have I ever fallen asleep during a movie.",
            "Never have I ever forgotten where I parked.",
            "Never have I ever danced when nobody was watching.",
            "Never have I ever talked to myself out loud.",
            "Never have I ever eaten dessert before dinner.",
            "Never have I ever sung loudly while driving.",
            "Never have I ever pretended to understand something I didn't.",
            "Never have I ever laughed at the wrong moment.",
            "Never have I ever accidentally called someone by the wrong name.",
            "Never have I ever spent too much money on something unnecessary.",
            "Never have I ever stayed up way too late watching videos.",
            "Never have I ever sent a meme instead of answering a serious message.",
            "Never have I ever forgotten why I walked into a room.",
            "Never have I ever had a completely ridiculous nickname.",
        ],

        "spicy": [

            "Never have I ever flirted with someone just because I could.",
            "Never have I ever used a cheesy pickup line.",
            "Never have I ever had a crush on someone because of their laugh.",
            "Never have I ever intentionally tried to make someone blush.",
            "Never have I ever sent a message just to get someone's attention.",
            "Never have I ever dressed up specifically to impress someone.",
            "Never have I ever stayed awake because I was having too much fun talking to someone.",
            "Never have I ever flirted with someone without telling them I was interested.",
            "Never have I ever had a secret crush at a party.",
            "Never have I ever made eye contact with someone and immediately felt chemistry.",
        ],

        "extreme": [

            "Never have I ever said yes to an adventure without knowing exactly how it would end.",
            "Never have I ever tried something adventurous on a dare.",
            "Never have I ever had an experience that became a story I still tell.",
            "Never have I ever done something completely unexpected because of chemistry.",
            "Never have I ever accepted a spontaneous adults-only invitation.",
            "Never have I ever tried something outside my normal comfort zone because someone I trusted encouraged me.",
            "Never have I ever had an adventure that started as a joke.",
            "Never have I ever agreed to something adventurous at the last minute.",
            "Never have I ever done something that surprised everyone who knows me.",
            "Never have I ever had a night that went completely differently than planned.",
        ],
    },

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    "relationships": {

        "mild": [

            "Never have I ever planned a surprise for a partner.",
            "Never have I ever stayed up all night talking with my partner.",
            "Never have I ever written a romantic message to someone.",
            "Never have I ever cooked for someone I cared about.",
            "Never have I ever introduced someone I was dating to my closest friends.",
            "Never have I ever gone on a romantic getaway.",
            "Never have I ever had a relationship that started as friendship.",
            "Never have I ever fallen for someone's personality before their appearance.",
            "Never have I ever kept a sentimental gift from an ex.",
            "Never have I ever had a relationship teach me something important about myself.",
        ],

        "spicy": [

            "Never have I ever discussed a fantasy with my partner.",
            "Never have I ever surprised my partner with something romantic and unexpected.",
            "Never have I ever intentionally teased my partner.",
            "Never have I ever planned a romantic night specifically around building anticipation.",
            "Never have I ever tried something new because my partner wanted to explore it.",
            "Never have I ever had a private joke with a partner that nobody else understood.",
            "Never have I ever sent my partner a message designed to make them blush.",
            "Never have I ever planned an adults-only date night.",
            "Never have I ever talked about boundaries before trying something new.",
            "Never have I ever surprised my partner with a spontaneous adventure.",
        ],

        "extreme": [

            "Never have I ever explored a kink with a long-term partner.",
            "Never have I ever discussed opening a relationship or exploring non-monogamy.",
            "Never have I ever explored a fantasy with my partner and another consenting adult.",
            "Never have I ever attended an adults-only event with a partner.",
            "Never have I ever discussed relationship boundaries in detail before exploring.",
            "Never have I ever tried something completely new because my partner trusted me.",
            "Never have I ever explored with another couple.",
            "Never have I ever planned a fantasy experience with my partner.",
            "Never have I ever discovered a new kink through a relationship.",
            "Never have I ever had a partner encourage me to explore something I had been curious about.",
        ],
    },
}


# ==========================================================
# CATEGORY NAMES
# ==========================================================

CATEGORY_NAMES = {
    "general": "🌎 General",
    "dating": "💘 Dating",
    "adult": "🔥 Adult Community",
    "fun": "😂 Just For Fun",
    "relationships": "❤️ Relationships",
}


# ==========================================================
# ENABLED STATUS
# ==========================================================

def is_enabled():

    return NEVER_HAVE_I_EVER_ENABLED


# ==========================================================
# GET CATEGORY
# ==========================================================

def get_category(context):

    category = context.user_data.get(
        "never_category",
        "general",
    )

    if category not in PROMPTS:

        category = "general"

    return category


# ==========================================================
# GET DIFFICULTY
# ==========================================================

def get_difficulty(context):

    difficulty = context.user_data.get(
        "never_difficulty",
        "mild",
    )

    if difficulty not in VALID_DIFFICULTIES:

        difficulty = "mild"

    return difficulty


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def category_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["general"],
                    callback_data="never_category_general",
                ),
                InlineKeyboardButton(
                    CATEGORY_NAMES["dating"],
                    callback_data="never_category_dating",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["adult"],
                    callback_data="never_category_adult",
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_NAMES["fun"],
                    callback_data="never_category_fun",
                ),
                InlineKeyboardButton(
                    CATEGORY_NAMES["relationships"],
                    callback_data="never_category_relationships",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎯 Change Difficulty",
                    callback_data="never_difficulty_menu",
                ),
            ],
        ]
    )


# ==========================================================
# DIFFICULTY KEYBOARD
# ==========================================================

def difficulty_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 Mild",
                    callback_data="never_difficulty_mild",
                ),
                InlineKeyboardButton(
                    "🌶️ Spicy",
                    callback_data="never_difficulty_spicy",
                ),
                InlineKeyboardButton(
                    "🔥 Extreme",
                    callback_data="never_difficulty_extreme",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 Categories",
                    callback_data="never_category_menu",
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
                    callback_data="never_answer_have",
                ),
                InlineKeyboardButton(
                    "😇 NEVER",
                    callback_data="never_answer_never",
                ),
            ],
            [
                InlineKeyboardButton(
                    "😈 PASS",
                    callback_data="never_pass",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="never_next",
                ),
                InlineKeyboardButton(
                    "🔄 Categories",
                    callback_data="never_category_menu",
                ),
            ],
        ]
    )


# ==========================================================
# INITIALIZE STATS
# ==========================================================

def initialize_stats(context):

    if "never_have_count" not in context.user_data:

        context.user_data[
            "never_have_count"
        ] = 0

    if "never_never_count" not in context.user_data:

        context.user_data[
            "never_never_count"
        ] = 0

    if "never_pass_count" not in context.user_data:

        context.user_data[
            "never_pass_count"
        ] = 0

    if "never_total" not in context.user_data:

        context.user_data[
            "never_total"
        ] = 0


# ==========================================================
# STATS TEXT
# ==========================================================

def stats_text(context):

    initialize_stats(context)

    return (
        f"🙋 I HAVE: "
        f"{context.user_data.get('never_have_count', 0)}\n"
        f"😇 NEVER: "
        f"{context.user_data.get('never_never_count', 0)}\n"
        f"😈 PASS: "
        f"{context.user_data.get('never_pass_count', 0)}\n"
        f"🎮 Played: "
        f"{context.user_data.get('never_total', 0)}"
    )


# ==========================================================
# GET PROMPT
# ==========================================================

def get_prompt(context):

    category = get_category(context)
    difficulty = get_difficulty(context)

    prompts = PROMPTS.get(
        category,
        {},
    ).get(
        difficulty,
        [],
    )

    if not prompts:

        category = "general"
        difficulty = "mild"

        context.user_data[
            "never_category"
        ] = category

        context.user_data[
            "never_difficulty"
        ] = difficulty

        prompts = PROMPTS[
            category
        ][difficulty]

    prompt = random.choice(prompts)

    context.user_data[
        "never_current_prompt"
    ] = prompt

    context.user_data[
        "never_answered"
    ] = False

    return prompt


# ==========================================================
# FORMAT PROMPT
# ==========================================================

def format_prompt(
    prompt,
    context,
):

    category = get_category(context)
    difficulty = get_difficulty(context)

    return (
        "🎭 NEVER HAVE I EVER\n\n"
        f"📚 Category: "
        f"{CATEGORY_NAMES.get(category, category)}\n"
        f"🎯 Level: {difficulty.upper()}\n\n"
        f"👉 {prompt}\n\n"
        f"{stats_text(context)}\n\n"
        "Choose honestly. No judgment.\n"
        "😈 PASS is always allowed."
    )


# ==========================================================
# START PROMPT
# ==========================================================

async def start_prompt(
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
# /NEVER
# ==========================================================

async def never(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not NEVER_HAVE_I_EVER_ENABLED:

        await message.reply_text(
            "🎭 Never Have I Ever is currently disabled."
        )

        return

    initialize_stats(context)

    await message.reply_text(
        "🎭 NEVER HAVE I EVER\n\n"
        "Choose a category:",
        reply_markup=category_keyboard(),
    )


# ==========================================================
# ALIAS: /NEVERHAVEIEVER
# ==========================================================

async def never_have_i_ever(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await never(
        update,
        context,
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
    # CATEGORY MENU
    # ======================================================

    if data == "never_category_menu":

        await query.edit_message_text(
            "🎭 NEVER HAVE I EVER\n\n"
            "Choose a category:",
            reply_markup=category_keyboard(),
        )

        return

    # ======================================================
    # DIFFICULTY MENU
    # ======================================================

    if data == "never_difficulty_menu":

        await query.edit_message_text(
            "🎯 CHOOSE LEVEL\n\n"
            "🟢 Mild — fun and flirty\n"
            "🌶️ Spicy — adult-community vibes\n"
            "🔥 Extreme — bold and adventurous",
            reply_markup=difficulty_keyboard(),
        )

        return

    # ======================================================
    # CATEGORY SELECTION
    # ======================================================

    if data.startswith("never_category_"):

        category = data.replace(
            "never_category_",
            "",
            1,
        )

        if category not in PROMPTS:

            category = "general"

        context.user_data[
            "never_category"
        ] = category

        await start_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # DIFFICULTY SELECTION
    # ======================================================

    if data.startswith("never_difficulty_"):

        difficulty = data.replace(
            "never_difficulty_",
            "",
            1,
        )

        if difficulty not in VALID_DIFFICULTIES:

            difficulty = "mild"

        context.user_data[
            "never_difficulty"
        ] = difficulty

        await start_prompt(
            query,
            context,
        )

        return

    # ======================================================
    # ANSWER
    # ======================================================

    if data in (
        "never_answer_have",
        "never_answer_never",
    ):

        if context.user_data.get(
            "never_answered",
            False,
        ):

            await query.answer(
                "You already answered this one.",
                show_alert=True,
            )

            return

        context.user_data[
            "never_answered"
        ] = True

        context.user_data[
            "never_total"
        ] += 1

        if data == "never_answer_have":

            context.user_data[
                "never_have_count"
            ] += 1

            result = (
                "🙋 I HAVE!\n\n"
                "No judgment. 😈\n\n"
                f"{stats_text(context)}"
            )

        else:

            context.user_data[
                "never_never_count"
            ] += 1

            result = (
                "😇 NEVER!\n\n"
                "Keeping it mysterious. 👀\n\n"
                f"{stats_text(context)}"
            )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➡️ Next",
                        callback_data="never_next",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Categories",
                        callback_data="never_category_menu",
                    ),
                ],
            ]
        )

        await query.edit_message_text(
            result,
            reply_markup=keyboard,
        )

        return

    # ======================================================
    # PASS
    # ======================================================

    if data == "never_pass":

        if context.user_data.get(
            "never_answered",
            False,
        ):

            await query.answer(
                "This one is already finished.",
                show_alert=True,
            )

            return

        context.user_data[
            "never_answered"
        ] = True

        context.user_data[
            "never_pass_count"
        ] += 1

        context.user_data[
            "never_total"
        ] += 1

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➡️ Next",
                        callback_data="never_next",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Categories",
                        callback_data="never_category_menu",
                    ),
                ],
            ]
        )

        await query.edit_message_text(
            "😈 PASS ACCEPTED\n\n"
            "No explanation required.\n"
            "Your boundaries come first. ❤️\n\n"
            f"{stats_text(context)}",
            reply_markup=keyboard,
        )

        return

    # ======================================================
    # NEXT
    # ======================================================

    if data == "never_next":

        await start_prompt(
            query,
            context,
        )

        return


# ==========================================================
# RESET STATS
# ==========================================================

def reset_stats(context):

    context.user_data[
        "never_have_count"
    ] = 0

    context.user_data[
        "never_never_count"
    ] = 0

    context.user_data[
        "never_pass_count"
    ] = 0

    context.user_data[
        "never_total"
    ] = 0

    context.user_data[
        "never_answered"
    ] = False


# ==========================================================
# END never_have_i_ever.py
# ==========================================================
