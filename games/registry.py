# ==========================================================
# Melanated AZ Bot
# games/registry.py
#
# CENTRAL GAME REGISTRY
#
# This file defines EVERY game that appears in the
# Melanated AZ Game Center.
#
# Game logic belongs in the individual game modules.
# This file only defines:
#
#   - Game ID
#   - Display name
#   - Description
#   - Category
#   - Callback
#   - Command
#   - Enabled status
#
# ==========================================================


# ==========================================================
# GAME DEFINITIONS
# ==========================================================

GAMES = {

    # ======================================================
    # PARTY / SOCIAL
    # ======================================================

    "truth_dare": {
        "name": "🔥 Truth or Dare",
        "description": "Fun, flirty, spicy, and extreme challenges.",
        "category": "party",
        "callback": "games_truthdare",
        "command": "/truthdare",
        "enabled": True,
    },

    "would_you_rather": {
        "name": "🤔 Would You Rather",
        "description": "Choose between two difficult or fun options.",
        "category": "party",
        "callback": "games_wyr",
        "command": "/wouldyourather",
        "enabled": True,
    },

    "never_have_i_ever": {
        "name": "🙈 Never Have I Ever",
        "description": "Find out what everyone has or has not done.",
        "category": "party",
        "callback": "games_nhie",
        "command": "/neverhaveiever",
        "enabled": True,
    },

    "most_likely": {
        "name": "👀 Most Likely To",
        "description": "Vote on who is most likely to do it.",
        "category": "party",
        "callback": "games_mostlikely",
        "command": "/mostlikely",
        "enabled": True,
    },

    "this_or_that": {
        "name": "⚖️ This or That",
        "description": "Pick your favorite between two choices.",
        "category": "party",
        "callback": "games_thisorthat",
        "command": "/thisorthat",
        "enabled": True,
    },

    "hot_seat": {
        "name": "🔥 Hot Seat",
        "description": "One player answers a series of questions.",
        "category": "party",
        "callback": "games_hotseat",
        "command": "/hotseat",
        "enabled": True,
    },

    "compliment": {
        "name": "💜 Compliment Game",
        "description": "Give someone a genuine compliment.",
        "category": "party",
        "callback": "games_compliment",
        "command": "/compliment",
        "enabled": True,
    },


    # ======================================================
    # ARCADE
    # ======================================================

    "reaction": {
        "name": "⚡ Reaction Test",
        "description": "Test how fast you can react.",
        "category": "arcade",
        "callback": "games_reaction",
        "command": "/reaction",
        "enabled": True,
    },

    "number_guess": {
        "name": "🔢 Number Guess",
        "description": "Guess the hidden number.",
        "category": "arcade",
        "callback": "games_number_guess",
        "command": "/numberguess",
        "enabled": True,
    },

    "high_low": {
        "name": "📈 High or Low",
        "description": "Predict whether the next number is higher or lower.",
        "category": "arcade",
        "callback": "games_high_low",
        "command": "/highlow",
        "enabled": True,
    },

    "coin_flip": {
        "name": "🪙 Coin Flip",
        "description": "Call heads or tails.",
        "category": "arcade",
        "callback": "games_coinflip",
        "command": "/coinflip",
        "enabled": True,
    },

    "dice_roll": {
        "name": "🎲 Dice Roll",
        "description": "Roll the dice and test your luck.",
        "category": "arcade",
        "callback": "games_dice",
        "command": "/gamedice",
        "enabled": True,
    },

    "dice_challenge": {
        "name": "🎲 Dice Challenge",
        "description": "Complete dice-based challenges.",
        "category": "arcade",
        "callback": "games_dice_challenge",
        "command": "/dicechallenge",
        "enabled": True,
    },

    "magic_8ball": {
        "name": "🎱 Magic 8-Ball",
        "description": "Ask a question and let the 8-Ball decide.",
        "category": "arcade",
        "callback": "games_8ball",
        "command": "/8ball",
        "enabled": True,
    },


    # ======================================================
    # OUTDOOR
    # ======================================================

    "fishing": {
        "name": "🎣 Fishing",
        "description": "Cast your line and see what you catch.",
        "category": "outdoor",
        "callback": "games_fishing",
        "command": "/fishing",
        "enabled": True,
    },

    "camping": {
        "name": "🏕️ Camping",
        "description": "Survive a night in the wilderness.",
        "category": "outdoor",
        "callback": "games_camping",
        "command": "/camping",
        "enabled": True,
    },

    "hiking": {
        "name": "🥾 Hiking Challenge",
        "description": "Choose your trail and survive the hike.",
        "category": "outdoor",
        "callback": "games_hiking",
        "command": "/hiking",
        "enabled": True,
    },

    "hunting": {
        "name": "🏹 Hunting Challenge",
        "description": "Track targets and complete hunting challenges.",
        "category": "outdoor",
        "callback": "games_hunting",
        "command": "/hunting",
        "enabled": True,
    },

    "survival": {
        "name": "🔥 Survival",
        "description": "Make the right choices to survive.",
        "category": "outdoor",
        "callback": "games_survival",
        "command": "/survival",
        "enabled": True,
    },


    # ======================================================
    # SHOOTING / ACTION
    # ======================================================

    "duck_hunt": {
        "name": "🦆 Duck Hunt",
        "description": "Take aim and see how many ducks you can hit.",
        "category": "shooting",
        "callback": "games_duck_hunt",
        "command": "/duckhunt",
        "enabled": True,
    },

    "target": {
        "name": "🎯 Target Practice",
        "description": "Hit targets and build your accuracy score.",
        "category": "shooting",
        "callback": "games_target",
        "command": "/target",
        "enabled": True,
    },

    "quick_shot": {
        "name": "⚡ Quick Shot",
        "description": "React quickly and hit the target.",
        "category": "shooting",
        "callback": "games_quick_shot",
        "command": "/quickshot",
        "enabled": True,
    },

    "bullseye": {
        "name": "🎯 Bullseye",
        "description": "Try to hit the center of the target.",
        "category": "shooting",
        "callback": "games_bullseye",
        "command": "/bullseye",
        "enabled": True,
    },

    "accuracy": {
        "name": "🏹 Accuracy Challenge",
        "description": "Test your precision.",
        "category": "shooting",
        "callback": "games_accuracy",
        "command": "/accuracy",
        "enabled": True,
    },

    "sniper": {
        "name": "🔭 Sniper Challenge",
        "description": "Test your long-range target accuracy.",
        "category": "shooting",
        "callback": "games_sniper",
        "command": "/sniper",
        "enabled": True,
    },


    # ======================================================
    # BOARD GAMES
    # ======================================================

    "monopoly": {
        "name": "💰 Monopoly",
        "description": "Buy properties, collect rent, and build your fortune.",
        "category": "board",
        "callback": "games_monopoly",
        "command": "/monopoly",
        "enabled": True,
    },

    "strategy": {
        "name": "♟️ Strategy Challenge",
        "description": "Make strategic decisions and outplay the competition.",
        "category": "board",
        "callback": "games_strategy",
        "command": "/strategy",
        "enabled": True,
    },

    "dice_duel": {
        "name": "🎲 Dice Duel",
        "description": "Challenge another player to a dice battle.",
        "category": "board",
        "callback": "games_dice_duel",
        "command": "/diceduel",
        "enabled": True,
    },


    # ======================================================
    # SPORTS
    # ======================================================

    "football": {
        "name": "🏈 Football Challenge",
        "description": "Make the play and score points.",
        "category": "sports",
        "callback": "games_football",
        "command": "/football",
        "enabled": True,
    },

    "basketball": {
        "name": "🏀 Basketball Challenge",
        "description": "Shoot for the highest score.",
        "category": "sports",
        "callback": "games_basketball",
        "command": "/basketball",
        "enabled": True,
    },

    "baseball": {
        "name": "⚾ Baseball Challenge",
        "description": "Step up to the plate and swing.",
        "category": "sports",
        "callback": "games_baseball",
        "command": "/baseball",
        "enabled": True,
    },

    "soccer": {
        "name": "⚽ Soccer Challenge",
        "description": "Take your shot and score.",
        "category": "sports",
        "callback": "games_soccer",
        "command": "/soccer",
        "enabled": True,
    },

    "boxing": {
        "name": "🥊 Boxing Challenge",
        "description": "Enter the ring and score points.",
        "category": "sports",
        "callback": "games_boxing",
        "command": "/boxing",
        "enabled": True,
    },


    # ======================================================
    # RACING
    # ======================================================

    "car_race": {
        "name": "🏎️ Car Race",
        "description": "Race to the finish line.",
        "category": "racing",
        "callback": "games_car_race",
        "command": "/carrace",
        "enabled": True,
    },

    "bike_race": {
        "name": "🏍️ Bike Race",
        "description": "Race through challenging terrain.",
        "category": "racing",
        "callback": "games_bike_race",
        "command": "/bikerace",
        "enabled": True,
    },

    "boat_race": {
        "name": "🚤 Boat Race",
        "description": "Race across the water.",
        "category": "racing",
        "callback": "games_boat_race",
        "command": "/boatrace",
        "enabled": True,
    },

    "drag_race": {
        "name": "🏁 Drag Race",
        "description": "Beat your opponent off the line.",
        "category": "racing",
        "callback": "games_drag_race",
        "command": "/dragrace",
        "enabled": True,
    },

    "street_race": {
        "name": "🏎️ Street Race",
        "description": "Race through the city.",
        "category": "racing",
        "callback": "games_street_race",
        "command": "/streetrace",
        "enabled": True,
    },


    # ======================================================
    # TRIVIA
    # ======================================================

    "general_trivia": {
        "name": "🧠 General Trivia",
        "description": "Test your general knowledge.",
        "category": "trivia",
        "callback": "games_general_trivia",
        "command": "/trivia",
        "enabled": True,
    },

    "music_trivia": {
        "name": "🎵 Music Trivia",
        "description": "Test your music knowledge.",
        "category": "trivia",
        "callback": "games_music_trivia",
        "command": "/musictrivia",
        "enabled": True,
    },

    "sports_trivia": {
        "name": "🏆 Sports Trivia",
        "description": "Test your sports knowledge.",
        "category": "trivia",
        "callback": "games_sports_trivia",
        "command": "/sportstrivia",
        "enabled": True,
    },

    "movie_trivia": {
        "name": "🎬 Movie Trivia",
        "description": "Test your movie knowledge.",
        "category": "trivia",
        "callback": "games_movie_trivia",
        "command": "/movietrivia",
        "enabled": True,
    },

    "word_challenge": {
        "name": "🔤 Word Challenge",
        "description": "Test your vocabulary and word skills.",
        "category": "trivia",
        "callback": "games_word_challenge",
        "command": "/wordchallenge",
        "enabled": True,
    },


    # ======================================================
    # MYSTERY / STRATEGY
    # ======================================================

    "detective": {
        "name": "🕵🏾 Detective",
        "description": "Solve clues and uncover the mystery.",
        "category": "mystery",
        "callback": "games_detective",
        "command": "/detective",
        "enabled": True,
    },

    "murder_mystery": {
        "name": "🔎 Mystery Case",
        "description": "Investigate a mysterious case.",
        "category": "mystery",
        "callback": "games_murder_mystery",
        "command": "/mystery",
        "enabled": True,
    },

    "code_breaker": {
        "name": "🔐 Code Breaker",
        "description": "Crack the hidden code.",
        "category": "mystery",
        "callback": "games_code_breaker",
        "command": "/codebreaker",
        "enabled": True,
    },

    "escape": {
        "name": "🚪 Escape Room",
        "description": "Solve puzzles and escape.",
        "category": "mystery",
        "callback": "games_escape",
        "command": "/escaperoom",
        "enabled": True,
    },

    "investigation": {
        "name": "🔍 Investigation",
        "description": "Follow the evidence and solve the case.",
        "category": "mystery",
        "callback": "games_investigation",
        "command": "/investigation",
        "enabled": True,
    },


    # ======================================================
    # FIGHTING
    # ======================================================

    "mma": {
        "name": "🥋 MMA",
        "description": "Choose your fighting style and battle.",
        "category": "fighting",
        "callback": "games_mma",
        "command": "/mma",
        "enabled": True,
    },

    "karate": {
        "name": "🥋 Karate",
        "description": "Test your martial arts skills.",
        "category": "fighting",
        "callback": "games_karate",
        "command": "/karate",
        "enabled": True,
    },

    "street_fight": {
        "name": "👊 Street Fight",
        "description": "Battle through an arcade-style fight.",
        "category": "fighting",
        "callback": "games_street_fight",
        "command": "/streetfight",
        "enabled": True,
    },

    "arena": {
        "name": "⚔️ Arena Battle",
        "description": "Enter the arena and battle for victory.",
        "category": "fighting",
        "callback": "games_arena",
        "command": "/arena",
        "enabled": True,
    },

}


# ==========================================================
# CATEGORY INFORMATION
# ==========================================================

CATEGORY_NAME = "🎮 GAMES"

CATEGORY_DESCRIPTION = (
    "Choose a category and pick a game!"
)


# ==========================================================
# GET ENABLED GAMES
# ==========================================================

def get_enabled_games():
    return {
        key: game
        for key, game in GAMES.items()
        if game.get("enabled", False)
    }


# ==========================================================
# GET GAMES BY CATEGORY
# ==========================================================

def get_games_by_category(category_id):

    return {
        key: game
        for key, game in GAMES.items()
        if (
            game.get("category") == category_id
            and game.get("enabled", False)
        )
    }


# ==========================================================
# GET GAME
# ==========================================================

def get_game(game_id):
    return GAMES.get(game_id)


# ==========================================================
# CHECK GAME
# ==========================================================

def game_exists(game_id):

    game = GAMES.get(game_id)

    if not game:
        return False

    return game.get("enabled", False)


# ==========================================================
# GAME COUNT
# ==========================================================

def game_count():
    return len(get_enabled_games())


# ==========================================================
# CATEGORY COUNT
# ==========================================================

def category_game_count(category_id):

    return len(
        get_games_by_category(category_id)
    )


# ==========================================================
# GAME MENU BUTTON DATA
# ==========================================================

def get_game_menu_buttons():

    return [
        game
        for game in GAMES.values()
        if game.get("enabled", False)
    ]


# ==========================================================
# CATEGORY MENU DATA
# ==========================================================

def get_category_menu_data():

    categories = {}

    for game_id, game in GAMES.items():

        if not game.get("enabled", False):
            continue

        category = game.get("category")

        if not category:
            continue

        categories.setdefault(
            category,
            []
        ).append(
            game
        )

    return categories


# ==========================================================
# END registry.py
# ==========================================================
