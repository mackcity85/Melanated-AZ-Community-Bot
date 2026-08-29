# ==========================================================
# Melanated AZ Bot
# games/game_data.py
#
# CENTRAL GAME CATALOG
#
# Add games here without changing the Games menu system.
# ==========================================================


# ==========================================================
# CATEGORY DEFINITIONS
# ==========================================================

GAME_CATEGORIES = {

    "board": {
        "name": "🎲 Board & Classic",
        "description": "Classic games and board-style games.",
    },

    "sports": {
        "name": "🏆 Sports",
        "description": "Sports challenges and competitions.",
    },

    "arcade": {
        "name": "🦆 Arcade & Shooting",
        "description": "Fast arcade-style games and target challenges.",
    },

    "outdoors": {
        "name": "🎣 Adventure & Outdoors",
        "description": "Fishing, treasure, adventure, and outdoor games.",
    },

    "trivia": {
        "name": "🧠 Trivia & Knowledge",
        "description": "Trivia and knowledge challenges.",
    },

    "party": {
        "name": "😂 Party & Social",
        "description": "Group conversation and party games.",
    },

    "spicy": {
        "name": "🔥 Spicy / Adult",
        "description": "Flirty, spicy, and adult community games.",
    },
}


# ==========================================================
# GAME DEFINITIONS
# ==========================================================

GAMES = {

    # ======================================================
    # BOARD & CLASSIC
    # ======================================================

    "monopoly": {
        "name": "🎲 Monopoly",
        "category": "board",
        "description": "Buy property, collect rent, and build your fortune.",
        "type": "monopoly",
    },

    "checkers": {
        "name": "🔴 Checkers",
        "category": "board",
        "description": "Classic checkers.",
        "type": "board",
    },

    "chess": {
        "name": "♟️ Chess",
        "category": "board",
        "description": "Classic chess challenge.",
        "type": "board",
    },

    "tic_tac_toe": {
        "name": "❌ Tic-Tac-Toe",
        "category": "board",
        "description": "Get three in a row.",
        "type": "tic_tac_toe",
    },

    "connect_four": {
        "name": "🔵 Connect 4",
        "category": "board",
        "description": "Connect four pieces before your opponent.",
        "type": "board",
    },

    "battleship": {
        "name": "🚢 Battleship",
        "category": "board",
        "description": "Find and sink the hidden fleet.",
        "type": "board",
    },

    "hangman": {
        "name": "🔤 Hangman",
        "category": "board",
        "description": "Guess the hidden word.",
        "type": "word",
    },

    "bingo": {
        "name": "🎱 Bingo",
        "category": "board",
        "description": "Play bingo against the community.",
        "type": "bingo",
    },

    "yahtzee": {
        "name": "🎲 Yahtzee",
        "category": "board",
        "description": "Roll the dice and chase the best score.",
        "type": "dice",
    },

    "rock_paper_scissors": {
        "name": "✊ Rock Paper Scissors",
        "category": "board",
        "description": "Classic three-way battle.",
        "type": "rps",
    },

    "higher_lower": {
        "name": "⬆️ Higher or Lower",
        "category": "board",
        "description": "Predict whether the next number is higher or lower.",
        "type": "higher_lower",
    },

    "number_guess": {
        "name": "🔢 Number Guess",
        "category": "board",
        "description": "Guess the hidden number.",
        "type": "number_guess",
    },

    "dice_duel": {
        "name": "🎲 Dice Duel",
        "category": "board",
        "description": "Roll against the house.",
        "type": "dice",
    },

    "coin_flip": {
        "name": "🪙 Coin Flip",
        "category": "board",
        "description": "Heads or tails.",
        "type": "coin",
    },

    "lucky_number": {
        "name": "🍀 Lucky Number",
        "category": "board",
        "description": "Pick a number and test your luck.",
        "type": "number_guess",
    },

    "memory_match": {
        "name": "🧠 Memory Match",
        "category": "board",
        "description": "Test your memory.",
        "type": "memory",
    },

    "word_scramble": {
        "name": "🔀 Word Scramble",
        "category": "board",
        "description": "Unscramble the word.",
        "type": "word",
    },


    # ======================================================
    # SPORTS
    # ======================================================

    "football": {
        "name": "🏈 Football Challenge",
        "category": "sports",
        "description": "Choose the play and score.",
        "type": "sports",
    },

    "basketball": {
        "name": "🏀 Basketball Challenge",
        "category": "sports",
        "description": "Take the shot.",
        "type": "sports",
    },

    "baseball": {
        "name": "⚾ Baseball Challenge",
        "category": "sports",
        "description": "Step up to the plate.",
        "type": "sports",
    },

    "soccer": {
        "name": "⚽ Soccer Challenge",
        "category": "sports",
        "description": "Take the shot.",
        "type": "sports",
    },

    "boxing": {
        "name": "🥊 Boxing Challenge",
        "category": "sports",
        "description": "Choose your punch.",
        "type": "sports",
    },

    "tennis": {
        "name": "🎾 Tennis Challenge",
        "category": "sports",
        "description": "Return the serve.",
        "type": "sports",
    },

    "golf": {
        "name": "⛳ Golf Challenge",
        "category": "sports",
        "description": "Choose your club and take your shot.",
        "type": "sports",
    },

    "bowling": {
        "name": "🎳 Bowling",
        "category": "sports",
        "description": "Roll for a strike.",
        "type": "sports",
    },

    "home_run_derby": {
        "name": "⚾ Home Run Derby",
        "category": "sports",
        "description": "Swing for the fences.",
        "type": "sports",
    },

    "free_throw": {
        "name": "🏀 Free Throw Challenge",
        "category": "sports",
        "description": "Make your free throws.",
        "type": "sports",
    },

    "field_goal": {
        "name": "🏈 Field Goal Challenge",
        "category": "sports",
        "description": "Kick the winning field goal.",
        "type": "sports",
    },

    "touchdown": {
        "name": "🏈 Touchdown Run",
        "category": "sports",
        "description": "Find the end zone.",
        "type": "sports",
    },

    "slam_dunk": {
        "name": "🏀 Slam Dunk",
        "category": "sports",
        "description": "Go up for the dunk.",
        "type": "sports",
    },

    "penalty_kick": {
        "name": "⚽ Penalty Kick",
        "category": "sports",
        "description": "Beat the goalkeeper.",
        "type": "sports",
    },

    "sports_trivia": {
        "name": "🏆 Sports Trivia",
        "category": "sports",
        "description": "Test your sports knowledge.",
        "type": "trivia",
    },


    # ======================================================
    # ARCADE
    # ======================================================

    "duck_hunt": {
        "name": "🦆 Duck Hunt",
        "category": "arcade",
        "description": "Hit the ducks and build your high score.",
        "type": "duck_hunt",
    },

    "target_practice": {
        "name": "🎯 Target Practice",
        "category": "arcade",
        "description": "Hit the target.",
        "type": "target",
    },

    "balloon_pop": {
        "name": "🎈 Balloon Pop",
        "category": "arcade",
        "description": "Pop as many balloons as possible.",
        "type": "target",
    },

    "bottle_knockdown": {
        "name": "🍾 Bottle Knockdown",
        "category": "arcade",
        "description": "Knock down the targets.",
        "type": "target",
    },

    "bullseye": {
        "name": "🎯 Bullseye",
        "category": "arcade",
        "description": "Aim for the center.",
        "type": "target",
    },

    "moving_targets": {
        "name": "🎯 Moving Targets",
        "category": "arcade",
        "description": "Hit the moving target.",
        "type": "target",
    },

    "reaction_challenge": {
        "name": "⚡ Reaction Challenge",
        "category": "arcade",
        "description": "React as quickly as possible.",
        "type": "reaction",
    },

    "high_score": {
        "name": "🏆 High Score Challenge",
        "category": "arcade",
        "description": "Try to beat the community high score.",
        "type": "arcade",
    },

    "space_blaster": {
        "name": "🚀 Space Blaster",
        "category": "arcade",
        "description": "Arcade space battle.",
        "type": "arcade",
    },

    "alien_attack": {
        "name": "👾 Alien Attack",
        "category": "arcade",
        "description": "Defend against the invasion.",
        "type": "arcade",
    },

    "asteroid_field": {
        "name": "☄️ Asteroid Field",
        "category": "arcade",
        "description": "Navigate the asteroid field.",
        "type": "arcade",
    },

    "treasure_crusher": {
        "name": "💎 Treasure Crusher",
        "category": "arcade",
        "description": "Find the treasure.",
        "type": "arcade",
    },


    # ======================================================
    # ADVENTURE / OUTDOORS
    # ======================================================

    "fishing": {
        "name": "🎣 Fishing",
        "category": "outdoors",
        "description": "Cast your line and catch fish.",
        "type": "fishing",
    },

    "ocean_fishing": {
        "name": "🌊 Ocean Fishing",
        "category": "outdoors",
        "description": "Fish the open ocean.",
        "type": "fishing",
    },

    "lake_fishing": {
        "name": "🏞️ Lake Fishing",
        "category": "outdoors",
        "description": "Fish the lake.",
        "type": "fishing",
    },

    "river_fishing": {
        "name": "🏞️ River Fishing",
        "category": "outdoors",
        "description": "Fish the river.",
        "type": "fishing",
    },

    "swamp_fishing": {
        "name": "🐊 Swamp Fishing",
        "category": "outdoors",
        "description": "Fish the swamp.",
        "type": "fishing",
    },

    "treasure_hunt": {
        "name": "💎 Treasure Hunt",
        "category": "outdoors",
        "description": "Search for hidden treasure.",
        "type": "treasure",
    },

    "treasure_dig": {
        "name": "⛏️ Treasure Dig",
        "category": "outdoors",
        "description": "Dig for buried treasure.",
        "type": "treasure",
    },

    "gold_miner": {
        "name": "⛏️ Gold Miner",
        "category": "outdoors",
        "description": "Mine for gold.",
        "type": "mining",
    },

    "camping": {
        "name": "🏕️ Camping Challenge",
        "category": "outdoors",
        "description": "Survive the wilderness.",
        "type": "adventure",
    },

    "survival": {
        "name": "🏝️ Survival Challenge",
        "category": "outdoors",
        "description": "Make the right survival decisions.",
        "type": "adventure",
    },

    "adventure_quest": {
        "name": "🗺️ Adventure Quest",
        "category": "outdoors",
        "description": "Choose your path.",
        "type": "adventure",
    },

    "pirate_treasure": {
        "name": "🏴‍☠️ Pirate Treasure",
        "category": "outdoors",
        "description": "Search for the pirate treasure.",
        "type": "treasure",
    },


    # ======================================================
    # TRIVIA
    # ======================================================

    "general_trivia": {
        "name": "🌎 General Trivia",
        "category": "trivia",
        "description": "General knowledge.",
        "type": "trivia",
    },

    "music_trivia": {
        "name": "🎵 Music Trivia",
        "category": "trivia",
        "description": "Test your music knowledge.",
        "type": "trivia",
    },

    "movie_trivia": {
        "name": "🎬 Movie Trivia",
        "category": "trivia",
        "description": "Test your movie knowledge.",
        "type": "trivia",
    },

    "black_history": {
        "name": "✊🏾 Black History & Culture",
        "category": "trivia",
        "description": "Black history and culture trivia.",
        "type": "trivia",
    },

    "geography": {
        "name": "🌎 Geography",
        "category": "trivia",
        "description": "Countries, cities, and landmarks.",
        "type": "trivia",
    },

    "science": {
        "name": "🔬 Science",
        "category": "trivia",
        "description": "Science trivia.",
        "type": "trivia",
    },

    "food_trivia": {
        "name": "🍔 Food Trivia",
        "category": "trivia",
        "description": "Food and cooking trivia.",
        "type": "trivia",
    },

    "90s_trivia": {
        "name": "📼 90s Trivia",
        "category": "trivia",
        "description": "Test your 90s knowledge.",
        "type": "trivia",
    },

    "2000s_trivia": {
        "name": "📀 2000s Trivia",
        "category": "trivia",
        "description": "Test your 2000s knowledge.",
        "type": "trivia",
    },


    # ======================================================
    # PARTY
    # ======================================================

    "would_you_rather": {
        "name": "🤔 Would You Rather",
        "category": "party",
        "description": "Pick between two choices.",
        "type": "would_you_rather",
    },

    "truth_or_dare": {
        "name": "🔥 Truth or Dare",
        "category": "party",
        "description": "Choose truth or dare.",
        "type": "truth_dare",
    },

    "never_have_i_ever": {
        "name": "🙈 Never Have I Ever",
        "category": "party",
        "description": "Have you ever?",
        "type": "questions",
    },

    "most_likely": {
        "name": "👀 Most Likely To",
        "category": "party",
        "description": "Who is most likely?",
        "type": "questions",
    },

    "this_or_that": {
        "name": "⚖️ This or That",
        "category": "party",
        "description": "Pick one.",
        "type": "questions",
    },

    "hot_seat": {
        "name": "🔥 Hot Seat",
        "category": "party",
        "description": "One person answers the questions.",
        "type": "questions",
    },

    "twenty_questions": {
        "name": "❓ 20 Questions",
        "category": "party",
        "description": "Ask questions and solve the mystery.",
        "type": "questions",
    },

    "charades": {
        "name": "🎭 Charades",
        "category": "party",
        "description": "Act it out.",
        "type": "questions",
    },

    "rapid_fire": {
        "name": "⚡ Rapid Fire",
        "category": "party",
        "description": "Answer quickly.",
        "type": "questions",
    },

    "guess_the_word": {
        "name": "🔤 Guess the Word",
        "category": "party",
        "description": "Guess the mystery word.",
        "type": "word",
    },

    "red_flag_green_flag": {
        "name": "🚩 Red Flag / Green Flag",
        "category": "party",
        "description": "Judge the situation.",
        "type": "questions",
    },

    "kiss_marry": {
        "name": "💋 Kiss / Marry",
        "category": "party",
        "description": "Make the choice.",
        "type": "questions",
    },


    # ======================================================
    # SPICY
    # ======================================================

    "spicy_wyr": {
        "name": "🔥 Spicy Would You Rather",
        "category": "spicy",
        "description": "A spicier version of Would You Rather.",
        "type": "questions",
    },

    "spicy_truth_dare": {
        "name": "🌶️ Spicy Truth or Dare",
        "category": "spicy",
        "description": "A more daring Truth or Dare.",
        "type": "truth_dare",
    },

    "flirty_questions": {
        "name": "💋 Flirty Questions",
        "category": "spicy",
        "description": "Flirty conversation starters.",
        "type": "questions",
    },

    "couple_questions": {
        "name": "❤️ Couple Questions",
        "category": "spicy",
        "description": "Questions for couples.",
        "type": "questions",
    },

    "fantasy_questions": {
        "name": "✨ Fantasy Questions",
        "category": "spicy",
        "description": "Fantasy conversation prompts.",
        "type": "questions",
    },

    "confession_game": {
        "name": "🤫 Confession Game",
        "category": "spicy",
        "description": "Share a confession.",
        "type": "questions",
    },

    "spicy_this_or_that": {
        "name": "🌶️ Spicy This or That",
        "category": "spicy",
        "description": "Spicy choices.",
        "type": "questions",
    },

    "date_night": {
        "name": "❤️ Date Night",
        "category": "spicy",
        "description": "Date-night questions and challenges.",
        "type": "questions",
    },

    "chemistry_test": {
        "name": "💘 Chemistry Test",
        "category": "spicy",
        "description": "Test the chemistry.",
        "type": "questions",
    },

    "relationship_quiz": {
        "name": "❤️ Relationship Quiz",
        "category": "spicy",
        "description": "Relationship questions.",
        "type": "questions",
    },
}


# ==========================================================
# HELPERS
# ==========================================================

def get_games_by_category(category):

    return {
        key: game
        for key, game in GAMES.items()
        if game.get("category") == category
    }


def get_game(game_id):

    return GAMES.get(game_id)


def get_category(category):

    return GAME_CATEGORIES.get(category)
