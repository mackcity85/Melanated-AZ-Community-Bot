# ==========================================================
# Melanated AZ Bot
# games/games.py
#
# COMPLETE GAMES SYSTEM
# ==========================================================

import logging
import random

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from .game_data import (
    GAME_CATEGORIES,
    GAMES,
    get_games_by_category,
    get_game,
)

logger = logging.getLogger(__name__)


# ==========================================================
# MAIN GAMES MENU
# ==========================================================

def games_menu_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎲 Board & Classic",
                    callback_data="games_category_board",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏆 Sports",
                    callback_data="games_category_sports",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🦆 Arcade & Shooting",
                    callback_data="games_category_arcade",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎣 Adventure & Outdoors",
                    callback_data="games_category_outdoors",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🧠 Trivia & Knowledge",
                    callback_data="games_category_trivia",
                ),
            ],
            [
                InlineKeyboardButton(
                    "😂 Party & Social",
                    callback_data="games_category_party",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Spicy / Adult",
                    callback_data="games_category_spicy",
                ),
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

    await message.reply_text(
        "🎮 **MELANATED AZ GAMES**\n\n"
        "Choose a category below.\n\n"
        "There are games for solo play, group play, "
        "competition, trivia, arcade challenges, "
        "sports, fishing, and more.",
        reply_markup=games_menu_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# COMMAND
# ==========================================================

async def games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await games_menu(
        update,
        context,
    )


# ==========================================================
# CATEGORY KEYBOARD
# ==========================================================

def category_keyboard(category):

    games = get_games_by_category(category)

    buttons = []

    for game_id, game in games.items():

        buttons.append(
            [
                InlineKeyboardButton(
                    game["name"],
                    callback_data=f"game_start_{game_id}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Games",
                callback_data="games_main",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


# ==========================================================
# CATEGORY MENU
# ==========================================================

async def show_category(
    query,
    category,
):

    category_data = GAME_CATEGORIES.get(category)

    if not category_data:

        await query.edit_message_text(
            "⚠️ Unknown game category."
        )

        return

    games = get_games_by_category(category)

    text = (
        f"{category_data['name']}\n\n"
        f"{category_data['description']}\n\n"
        f"🎮 Games available: {len(games)}\n\n"
        "Choose a game:"
    )

    await query.edit_message_text(
        text,
        reply_markup=category_keyboard(category),
    )


# ==========================================================
# GAME DESCRIPTION
# ==========================================================

def game_description(game):

    return (
        f"{game['name']}\n\n"
        f"{game['description']}\n\n"
        "Press START to play."
    )


# ==========================================================
# GAME START KEYBOARD
# ==========================================================

def start_game_keyboard(game_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "▶️ START GAME",
                    callback_data=f"game_play_{game_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Category",
                    callback_data="game_back_category",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="games_main",
                )
            ],
        ]
    )


# ==========================================================
# GAME START SCREEN
# ==========================================================

async def show_game_start(
    query,
    context,
    game_id,
):

    game = get_game(game_id)

    if not game:

        await query.edit_message_text(
            "⚠️ Game not found."
        )

        return

    context.user_data[
        "selected_game"
    ] = game_id

    context.user_data[
        "selected_game_category"
    ] = game["category"]

    await query.edit_message_text(
        game_description(game),
        reply_markup=start_game_keyboard(game_id),
    )


# ==========================================================
# GAME BUTTONS
# ==========================================================

def generic_game_keyboard(game_id):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎮 Play Again",
                    callback_data=f"game_play_{game_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Category",
                    callback_data="game_back_category",
                ),
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="games_main",
                ),
            ],
        ]
    )


# ==========================================================
# GENERIC GAME
# ==========================================================

async def play_generic_game(
    query,
    context,
    game_id,
):

    game = get_game(game_id)

    if not game:
        return

    outcomes = [
        "🔥 Great choice!",
        "🎯 Nice move!",
        "⭐ You scored a point!",
        "💥 Excellent!",
        "🏆 That's a strong play!",
        "😎 Smooth move!",
        "🎉 You got it!",
    ]

    outcome = random.choice(outcomes)

    score = context.user_data.get(
        "games_score",
        0,
    )

    score += 1

    context.user_data[
        "games_score"
    ] = score

    await query.edit_message_text(
        f"{game['name']}\n\n"
        f"{outcome}\n\n"
        f"🏆 Your Games Score: {score}\n\n"
        "Ready for another round?",
        reply_markup=generic_game_keyboard(
            game_id
        ),
    )


# ==========================================================
# DUCK HUNT
# ==========================================================

async def play_duck_hunt(
    query,
    context,
):

    ducks = random.randint(
        1,
        5,
    )

    hits = random.randint(
        0,
        ducks,
    )

    points = hits * 10

    score = context.user_data.get(
        "duck_hunt_score",
        0,
    )

    score += points

    context.user_data[
        "duck_hunt_score"
    ] = score

    duck_text = "🦆 " * ducks

    await query.edit_message_text(
        "🦆 **DUCK HUNT**\n\n"
        f"{duck_text}\n\n"
        f"🎯 Ducks: {ducks}\n"
        f"💥 Hits: {hits}\n"
        f"⭐ Points: +{points}\n\n"
        f"🏆 High Score: {score}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🦆 HUNT!",
                        callback_data="game_play_duck_hunt",
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


# ==========================================================
# FISHING
# ==========================================================

FISH = [
    (
        "🐟 Bluegill",
        5,
        "Common",
    ),
    (
        "🐠 Bass",
        15,
        "Common",
    ),
    (
        "🐟 Trout",
        25,
        "Uncommon",
    ),
    (
        "🐡 Catfish",
        35,
        "Uncommon",
    ),
    (
        "🐟 Salmon",
        50,
        "Rare",
    ),
    (
        "🦈 Shark",
        100,
        "Very Rare",
    ),
    (
        "🐉 Legendary Fish",
        250,
        "LEGENDARY",
    ),
]


async def play_fishing(
    query,
    context,
):

    fish, value, rarity = random.choice(
        FISH
    )

    total = context.user_data.get(
        "fishing_value",
        0,
    )

    total += value

    context.user_data[
        "fishing_value"
    ] = total

    catches = context.user_data.get(
        "fishing_catches",
        0,
    )

    catches += 1

    context.user_data[
        "fishing_catches"
    ] = catches

    await query.edit_message_text(
        "🎣 **FISHING**\n\n"
        "🌊 You cast your line...\n\n"
        "⏳ Waiting...\n\n"
        f"🎣 **YOU CAUGHT A FISH!**\n\n"
        f"{fish}\n"
        f"⭐ Rarity: {rarity}\n"
        f"💰 Value: ${value}\n\n"
        f"🐟 Total Catches: {catches}\n"
        f"💰 Total Value: ${total}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎣 Fish Again",
                        callback_data="game_play_fishing",
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


# ==========================================================
# MONOPOLY
# ==========================================================

MONOPOLY_PROPERTIES = [
    "Mediterranean Avenue",
    "Baltic Avenue",
    "Oriental Avenue",
    "Vermont Avenue",
    "Connecticut Avenue",
    "St. Charles Place",
    "States Avenue",
    "Virginia Avenue",
    "St. James Place",
    "Tennessee Avenue",
    "New York Avenue",
    "Kentucky Avenue",
    "Indiana Avenue",
    "Illinois Avenue",
    "Atlantic Avenue",
    "Ventnor Avenue",
    "Marvin Gardens",
    "Pacific Avenue",
    "North Carolina Avenue",
    "Pennsylvania Avenue",
    "Park Place",
    "Boardwalk",
]


async def play_monopoly(
    query,
    context,
):

    position = random.randint(
        1,
        12,
    )

    roll = random.randint(
        1,
        6,
    ) + random.randint(
        1,
        6,
    )

    property_name = random.choice(
        MONOPOLY_PROPERTIES
    )

    cash = context.user_data.get(
        "monopoly_cash",
        1500,
    )

    event = random.choice(
        [
            f"🎲 You rolled **{roll}**.",
            f"🏠 You landed near **{property_name}**.",
            "💰 You collected $200.",
            "💸 You paid $100.",
            "🎁 You received a Community Chest bonus.",
            "🚔 Uh oh... Jail!",
        ]
    )

    if "collected" in event or "received" in event:

        cash += 200

    if "paid" in event:

        cash = max(
            0,
            cash - 100,
        )

    context.user_data[
        "monopoly_cash"
    ] = cash

    await query.edit_message_text(
        "🎲 **MONOPOLY**\n\n"
        f"{event}\n\n"
        f"💵 Cash: ${cash}\n\n"
        "Keep playing to build your fortune.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎲 Roll Dice",
                        callback_data="game_play_monopoly",
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


# ==========================================================
# GAME PLAY ROUTER
# ==========================================================

async def play_game(
    query,
    context,
    game_id,
):

    game = get_game(game_id)

    if not game:

        await query.edit_message_text(
            "⚠️ Game not found."
        )

        return

    game_type = game.get(
        "type"
    )

    if game_type == "duck_hunt":

        await play_duck_hunt(
            query,
            context,
        )

        return

    if game_type == "fishing":

        await play_fishing(
            query,
            context,
        )

        return

    if game_type == "monopoly":

        await play_monopoly(
            query,
            context,
        )

        return

    await play_generic_game(
        query,
        context,
        game_id,
    )


# ==========================================================
# CALLBACK ROUTER
# ==========================================================

async def games_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    data = query.data or ""

    # ------------------------------------------------------
    # MAIN MENU
    # ------------------------------------------------------

    if data == "games_main":

        await query.edit_message_text(
            "🎮 **MELANATED AZ GAMES**\n\n"
            "Choose a category:",
            reply_markup=games_menu_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------

    if data.startswith(
        "games_category_"
    ):

        category = data.replace(
            "games_category_",
            "",
            1,
        )

        await show_category(
            query,
            category,
        )

        return

    # ------------------------------------------------------
    # GAME DESCRIPTION
    # ------------------------------------------------------

    if data.startswith(
        "game_start_"
    ):

        game_id = data.replace(
            "game_start_",
            "",
            1,
        )

        await show_game_start(
            query,
            context,
            game_id,
        )

        return

    # ------------------------------------------------------
    # PLAY
    # ------------------------------------------------------

    if data.startswith(
        "game_play_"
    ):

        game_id = data.replace(
            "game_play_",
            "",
            1,
        )

        await play_game(
            query,
            context,
            game_id,
        )

        return

    # ------------------------------------------------------
    # BACK
    # ------------------------------------------------------

    if data == "game_back_category":

        category = context.user_data.get(
            "selected_game_category",
            "board",
        )

        await show_category(
            query,
            category,
        )

        return

    logger.warning(
        "Unknown games callback: %s",
        data,
    )
