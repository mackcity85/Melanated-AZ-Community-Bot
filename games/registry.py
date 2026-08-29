# ==========================================================
# Melanated AZ Bot
# games/registry.py
#
# GAME REGISTRY
#
# Central list of all games available in the Games category.
#
# This file does NOT contain the actual game logic.
# It tells games.py which games exist and how they are
# displayed in the Games menu.
# ==========================================================


# ==========================================================
# GAME DEFINITIONS
# ==========================================================

GAMES = {

    "truth_dare": {
        "name": "🔥 Truth or Dare",
        "description": "Fun, flirty, spicy, and extreme challenges.",
        "callback": "games_truthdare",
        "command": "/truthdare",
        "enabled": True,
    },

    "would_you_rather": {
        "name": "🤔 Would You Rather",
        "description": "Choose between two difficult or fun options.",
        "callback": "games_wyr",
        "command": "/wouldyourather",
        "enabled": True,
    },

    "never_have_i_ever": {
        "name": "🙈 Never Have I Ever",
        "description": "Find out what everyone has or has not done.",
        "callback": "games_nhie",
        "command": "/neverhaveiever",
        "enabled": True,
    },

    "most_likely": {
        "name": "👀 Most Likely To",
        "description": "Vote on who is most likely to do it.",
        "callback": "games_mostlikely",
        "command": "/mostlikely",
        "enabled": True,
    },

    "this_or_that": {
        "name": "⚖️ This or That",
        "description": "Pick your favorite between two choices.",
        "callback": "games_thisorthat",
        "command": "/thisorthat",
        "enabled": True,
    },

    "hot_seat": {
        "name": "🔥 Hot Seat",
        "description": "One player answers a series of questions.",
        "callback": "games_hotseat",
        "command": "/hotseat",
        "enabled": True,
    },

    "dice": {
        "name": "🎲 Dice Challenge",
        "description": "Roll the dice and see what happens.",
        "callback": "games_dice",
        "command": "/gamedice",
        "enabled": True,
    },

    "coin_flip": {
        "name": "🪙 Coin Flip",
        "description": "Heads or tails. Let fate decide.",
        "callback": "games_coinflip",
        "command": "/coinflip",
        "enabled": True,
    },

    "8ball": {
        "name": "🎱 Magic 8-Ball",
        "description": "Ask a question and let the 8-Ball answer.",
        "callback": "games_8ball",
        "command": "/8ball",
        "enabled": True,
    },

    "compliment": {
        "name": "💜 Compliment Game",
        "description": "Give someone a genuine compliment.",
        "callback": "games_compliment",
        "command": "/compliment",
        "enabled": True,
    },

}


# ==========================================================
# CATEGORY INFORMATION
# ==========================================================

CATEGORY_NAME = "🎮 GAMES"

CATEGORY_DESCRIPTION = (
    "Choose a game below and have some fun with the group!"
)


# ==========================================================
# GET ENABLED GAMES
# ==========================================================

def get_enabled_games():
    """
    Return only games that are currently enabled.
    """

    return {
        key: game
        for key, game in GAMES.items()
        if game.get("enabled", False)
    }


# ==========================================================
# GET GAME
# ==========================================================

def get_game(game_id):
    """
    Return a game definition by ID.
    """

    return GAMES.get(game_id)


# ==========================================================
# CHECK GAME
# ==========================================================

def game_exists(game_id):
    """
    Check whether a game exists and is enabled.
    """

    game = GAMES.get(game_id)

    if not game:
        return False

    return game.get("enabled", False)


# ==========================================================
# GAME COUNT
# ==========================================================

def game_count():
    """
    Return the number of enabled games.
    """

    return len(get_enabled_games())


# ==========================================================
# MENU BUTTON DATA
# ==========================================================

def get_game_menu_buttons():
    """
    Return game definitions in menu order.

    games.py can use this to build the main Games menu.
    """

    return [
        game
        for game in GAMES.values()
        if game.get("enabled", False)
    ]


# ==========================================================
# END registry.py
# ==========================================================
