# ==========================================================

# Melanated AZ Bot

# games/games.py

#

# GAME ENGINE / GAME ROUTER

#

# Handles actual gameplay for the Game Center.

#

# Games currently implemented:

#

# Arcade

# - Reaction Test

# - Number Guess

# - High or Low

# - Coin Flip

# - Dice Roll

#

# Outdoor

# - Fishing

# - Camping

# - Hiking Challenge

# - Hunting Challenge

# - Survival

#

# Shooting

# - Target Practice

# - Quick Shot

# - Bullseye

# - Accuracy

# - Sniper Challenge

#

# Board

# - Strategy

# - Dice Duel

#

# Party

# - Truth or Dare

#

# Trivia

# - General Trivia

# - Music Trivia

# - Sports Trivia

# - Movie Trivia

# - Word Challenge

#

# Sports

# - Football Challenge

# - Basketball Challenge

# - Baseball Challenge

# - Boxing

# - Soccer

#

# Racing

# - Car Race

# - Bike Race

# - Boat Race

# - Drag Race

# - Street Race

#

# Mystery

# - Detective

# - Mystery Case

# - Code Breaker

# - Escape Room

# - Investigation

#

# Fighting

# - MMA

# - Karate

# - Street Fight

# - Arena Battle

#

# ==========================================================

import logging
import random
import time
from datetime import datetime

from telegram import (
Update,
InlineKeyboardButton,
InlineKeyboardMarkup,
)

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from raffle_database import get_connection

# ==========================================================

# LOGGING

# ==========================================================

logger = logging.getLogger(
"melanated_az_bot.games.engine"
)

# ==========================================================

# REWARDS

# ==========================================================

BASE_XP = 10
WIN_XP = 25
BASE_COINS = 5
WIN_COINS = 15

# ==========================================================

# GAME NAMES

# ==========================================================

GAME_NAMES = {

```
"reaction": "⚡ Reaction Test",
"number_guess": "🔢 Number Guess",
"high_low": "📈 High or Low",
"coin_flip": "🪙 Coin Flip",
"dice_roll": "🎲 Dice Roll",

"fishing": "🎣 Fishing",
"camping": "🏕️ Camping",
"hiking": "🥾 Hiking Challenge",
"hunting": "🏹 Hunting Challenge",
"survival": "🔥 Survival",

"target": "🎯 Target Practice",
"quick_shot": "🔫 Quick Shot",
"bullseye": "🎯 Bullseye",
"accuracy": "🏹 Accuracy",
"sniper": "🔭 Sniper Challenge",

"strategy": "♟️ Strategy",
"dice_duel": "🎲 Dice Duel",

"truth_dare": "🔥 Truth or Dare",

"general_trivia": "🧠 General Trivia",
"music_trivia": "🎵 Music Trivia",
"sports_trivia": "🏆 Sports Trivia",
"movie_trivia": "🎬 Movie Trivia",
"word_challenge": "🔤 Word Challenge",

"football": "🏈 Football Challenge",
"basketball": "🏀 Basketball Challenge",
"baseball": "⚾ Baseball Challenge",
"boxing": "🥊 Boxing",
"soccer": "⚽ Soccer",

"car_race": "🏎️ Car Race",
"bike_race": "🏍️ Bike Race",
"boat_race": "🚤 Boat Race",
"drag_race": "🏁 Drag Race",
"street_race": "🏎️ Street Race",

"detective": "🕵🏾 Detective",
"murder_mystery": "🔎 Mystery Case",
"code_breaker": "🔐 Code Breaker",
"escape": "🚪 Escape Room",
"investigation": "🔍 Investigation",

"mma": "🥋 MMA",
"karate": "🥋 Karate",
"street_fight": "👊 Street Fight",
"arena": "⚔️ Arena Battle",
```

}

# ==========================================================

# GENERIC BUTTONS

# ==========================================================

def game_back_keyboard():

```
return InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    ]
)
```

def replay_keyboard(game_id):

```
return InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🔄 Play Again",
                callback_data=f"games_play_{game_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ],
    ]
)
```

# ==========================================================

# PLAYER

# ==========================================================

def ensure_player(
user_id,
username=None,
display_name=None,
):

```
now = datetime.utcnow().isoformat()

conn = get_connection()

try:

    conn.execute(
        """
        INSERT INTO game_players (
            user_id,
            username,
            display_name,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            display_name = excluded.display_name,
            updated_at = excluded.updated_at
        """,
        (
            user_id,
            username,
            display_name,
            now,
            now,
        ),
    )

    conn.commit()

finally:

    conn.close()
```

# ==========================================================

# RECORD GAME RESULT

# ==========================================================

def record_game_result(
user_id,
game_id,
score=0,
won=False,
):

```
now = datetime.utcnow().isoformat()

xp_gain = (
    WIN_XP
    if won
    else BASE_XP
)

coin_gain = (
    WIN_COINS
    if won
    else BASE_COINS
)

conn = get_connection()

try:

    conn.execute(
        """
        UPDATE game_players
        SET
            games_played = games_played + 1,
            wins = wins + ?,
            losses = losses + ?,
            xp = xp + ?,
            coins = coins + ?,
            level = 1 + ((xp + ?) / 100),
            updated_at = ?
        WHERE user_id = ?
        """,
        (
            1 if won else 0,
            0 if won else 1,
            xp_gain,
            coin_gain,
            xp_gain,
            now,
            user_id,
        ),
    )

    conn.execute(
        """
        INSERT INTO game_scores (
            user_id,
            game_id,
            score,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            game_id,
            score,
            now,
        ),
    )

    conn.execute(
        """
        INSERT INTO game_stats (
            user_id,
            game_id,
            games_played,
            wins,
            losses,
            high_score
        )
        VALUES (?, ?, 1, ?, ?, ?)

        ON CONFLICT(user_id, game_id)
        DO UPDATE SET
            games_played =
                games_played + 1,

            wins =
                wins + excluded.wins,

            losses =
                losses + excluded.losses,

            high_score =
                CASE
                    WHEN excluded.high_score >
                         high_score
                    THEN excluded.high_score
                    ELSE high_score
                END
        """,
        (
            user_id,
            game_id,
            1 if won else 0,
            0 if won else 1,
            score,
        ),
    )

    conn.commit()

except Exception:

    conn.rollback()

    logger.exception(
        "Could not record game result."
    )

finally:

    conn.close()
```

# ==========================================================

# RESULT SCREEN

# ==========================================================

async def show_result(
query,
game_id,
title,
body,
score,
won,
):

```
user = query.from_user

record_game_result(
    user_id=user.id,
    game_id=game_id,
    score=score,
    won=won,
)

reward_text = (
    f"⭐ +{WIN_XP if won else BASE_XP} XP\n"
    f"🪙 +{WIN_COINS if won else BASE_COINS} AZ Coins"
)

result = (
    f"{title}\n\n"
    f"{body}\n\n"
    f"📊 Score: <b>{score}</b>\n\n"
    f"{reward_text}"
)

await query.edit_message_text(
    result,
    reply_markup=replay_keyboard(game_id),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# REACTION TEST

# ==========================================================

async def reaction_game(
query,
context,
):

```
game_id = "reaction"

context.user_data[
    "reaction_start"
] = time.time()

keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "⚡ TAP NOW!",
                callback_data="game_reaction_tap",
            )
        ]
    ]
)

await query.edit_message_text(
    "⚡ <b>REACTION TEST</b>\n\n"
    "When you're ready, hit the button!\n\n"
    "How fast can you react?",
    reply_markup=keyboard,
    parse_mode=ParseMode.HTML,
)
```

async def reaction_tap(
query,
context,
):

```
start = context.user_data.pop(
    "reaction_start",
    None,
)

if not start:

    await query.answer(
        "Start the game first.",
        show_alert=True,
    )

    return

elapsed = time.time() - start

milliseconds = int(
    elapsed * 1000
)

score = max(
    1,
    1000 - milliseconds,
)

won = milliseconds < 600

await show_result(
    query,
    "reaction",
    "⚡ <b>REACTION TEST</b>",
    (
        f"⏱️ Reaction time: "
        f"<b>{milliseconds} ms</b>\n\n"
        + (
            "🔥 Lightning fast!"
            if won
            else "😅 Try to beat your time!"
        )
    ),
    score,
    won,
)
```

# ==========================================================

# NUMBER GUESS

# ==========================================================

async def number_guess_game(
query,
context,
):

```
number = random.randint(
    1,
    10,
)

context.user_data[
    "number_guess"
] = number

buttons = []

for number_value in range(
    1,
    11,
):

    buttons.append(
        InlineKeyboardButton(
            str(number_value),
            callback_data=(
                f"game_guess_{number_value}"
            ),
        )
    )

keyboard = [
    buttons[0:5],
    buttons[5:10],
]

await query.edit_message_text(
    "🔢 <b>NUMBER GUESS</b>\n\n"
    "I'm thinking of a number from "
    "<b>1 to 10</b>.\n\n"
    "Can you guess it?",
    reply_markup=InlineKeyboardMarkup(
        keyboard
    ),
    parse_mode=ParseMode.HTML,
)
```

async def number_guess_answer(
query,
context,
guess,
):

```
target = context.user_data.pop(
    "number_guess",
    None,
)

if target is None:

    await query.answer(
        "Start a new game.",
        show_alert=True,
    )

    return

correct = (
    int(guess) == target
)

score = (
    100
    if correct
    else max(
        10,
        50 - abs(
            int(guess) - target
        ) * 5,
    )
)

await show_result(
    query,
    "number_guess",
    "🔢 <b>NUMBER GUESS</b>",
    (
        f"🎯 My number was "
        f"<b>{target}</b>.\n\n"
        + (
            "🎉 You got it!"
            if correct
            else "❌ Not this time!"
        )
    ),
    score,
    correct,
)
```

# ==========================================================

# HIGH / LOW

# ==========================================================

async def high_low_game(
query,
context,
):

```
first = random.randint(
    1,
    13,
)

second = random.randint(
    1,
    13,
)

context.user_data[
    "high_low"
] = {
    "first": first,
    "second": second,
}

keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "📈 HIGHER",
                callback_data="game_high",
            ),
            InlineKeyboardButton(
                "📉 LOWER",
                callback_data="game_low",
            ),
        ]
    ]
)

await query.edit_message_text(
    "📈 <b>HIGH OR LOW</b>\n\n"
    f"First card: <b>{first}</b>\n\n"
    "Will the next card be higher "
    "or lower?",
    reply_markup=keyboard,
    parse_mode=ParseMode.HTML,
)
```

async def high_low_answer(
query,
context,
choice,
):

```
data = context.user_data.pop(
    "high_low",
    None,
)

if not data:

    await query.answer(
        "Start a new game.",
        show_alert=True,
    )

    return

first = data["first"]
second = data["second"]

if second == first:

    won = False

elif choice == "high":

    won = second > first

else:

    won = second < first

await show_result(
    query,
    "high_low",
    "📈 <b>HIGH OR LOW</b>",
    (
        f"First card: <b>{first}</b>\n"
        f"Next card: <b>{second}</b>\n\n"
        + (
            "🎉 Correct!"
            if won
            else "❌ Wrong guess!"
        )
    ),
    100 if won else 25,
    won,
)
```

# ==========================================================

# COIN FLIP

# ==========================================================

async def coin_flip_game(
query,
context,
):

```
result = random.choice(
    [
        "HEADS",
        "TAILS",
    ]
)

await show_result(
    query,
    "coin_flip",
    "🪙 <b>COIN FLIP</b>",
    f"The coin landed on <b>{result}</b>!",
    50,
    True,
)
```

# ==========================================================

# DICE ROLL

# ==========================================================

async def dice_roll_game(
query,
context,
):

```
roll = random.randint(
    1,
    6,
)

won = roll >= 4

await show_result(
    query,
    "dice_roll",
    "🎲 <b>DICE ROLL</b>",
    (
        f"You rolled a <b>{roll}</b>!\n\n"
        + (
            "🔥 Nice roll!"
            if won
            else "🎲 Better luck next roll!"
        )
    ),
    roll * 10,
    won,
)
```

# ==========================================================

# RANDOM CHALLENGE GAMES

# ==========================================================

CHALLENGES = {

```
"fishing": [
    "🐟 You caught a huge bass!",
    "🐠 You caught a colorful fish!",
    "🎣 The fish got away!",
    "🐟 You landed a trophy fish!",
],

"camping": [
    "🔥 You built the perfect campfire!",
    "🏕️ You found an amazing campsite!",
    "🌧️ Rain ruined the campsite!",
    "🦌 You spotted wildlife nearby!",
],

"hiking": [
    "🥾 You reached the summit!",
    "🏔️ Amazing trail completed!",
    "🌲 You discovered a hidden trail!",
    "😅 You took the wrong trail!",
],

"hunting": [
    "🏹 Perfect shot!",
    "🦌 You tracked your target!",
    "🌲 The target escaped!",
    "🎯 Bullseye!",
],

"survival": [
    "🔥 You survived the night!",
    "💧 You found clean water!",
    "🏕️ You built shelter!",
    "🌧️ The storm almost got you!",
],

"target": [
    "🎯 Bullseye!",
    "🎯 Excellent shot!",
    "💥 Direct hit!",
    "😅 You missed!",
],

"quick_shot": [
    "⚡ Lightning-fast shot!",
    "🎯 Fast and accurate!",
    "💥 Perfect hit!",
    "😅 Too slow!",
],

"bullseye": [
    "🎯 PERFECT BULLSEYE!",
    "🔥 Dead center!",
    "🎯 Almost perfect!",
    "😅 Off target!",
],

"accuracy": [
    "🏹 Incredible accuracy!",
    "🎯 Excellent aim!",
    "💥 Great shot!",
    "😅 Needs practice!",
],

"sniper": [
    "🔭 Perfect long-range shot!",
    "🎯 Target eliminated!",
    "🔥 Incredible accuracy!",
    "😅 Target escaped!",
],

"strategy": [
    "♟️ Brilliant strategy!",
    "🧠 You outsmarted the opponent!",
    "♟️ Excellent move!",
    "😅 Your opponent saw it coming!",
],

"dice_duel": [
    "🎲 You won the dice duel!",
    "🎲 Huge roll!",
    "😈 Your opponent got crushed!",
    "💀 Your opponent rolled higher!",
],

"football": [
    "🏈 TOUCHDOWN!",
    "🏈 Huge gain!",
    "🏈 Perfect pass!",
    "🏈 Fumble!",
],

"basketball": [
    "🏀 THREE POINTER!",
    "🏀 Nothing but net!",
    "🔥 Clutch shot!",
    "😅 Air ball!",
],

"baseball": [
    "⚾ HOME RUN!",
    "⚾ Perfect hit!",
    "🔥 Extra-base hit!",
    "😅 Strikeout!",
],

"boxing": [
    "🥊 Knockout!",
    "🥊 Perfect combination!",
    "🔥 Huge punch!",
    "😵 You got rocked!",
],

"soccer": [
    "⚽ GOAL!",
    "⚽ Beautiful finish!",
    "🔥 Top corner!",
    "😅 Missed the shot!",
],

"car_race": [
    "🏎️ You crossed the finish line first!",
    "🏁 Perfect launch!",
    "🔥 Fastest lap!",
    "💥 You spun out!",
],

"bike_race": [
    "🏍️ First across the line!",
    "🏁 Amazing cornering!",
    "🔥 Fastest lap!",
    "😅 You wiped out!",
],

"boat_race": [
    "🚤 You dominated the race!",
    "🌊 Perfect turn!",
    "🏁 First place!",
    "🌊 You hit a huge wave!",
],

"drag_race": [
    "🏁 LIGHTS OUT!",
    "🏎️ Perfect launch!",
    "🔥 You won by a nose!",
    "😅 Bad reaction!",
],

"street_race": [
    "🏎️ You took the win!",
    "🔥 Fastest car on the street!",
    "🏁 Perfect corner!",
    "💥 You lost control!",
],

"mma": [
    "🥊 Submission victory!",
    "🔥 Technical knockout!",
    "💪 Dominant performance!",
    "😵 You got submitted!",
],

"karate": [
    "🥋 Perfect strike!",
    "🔥 Tournament victory!",
    "🥋 Excellent technique!",
    "😵 Countered!",
],

"street_fight": [
    "👊 You won the fight!",
    "🔥 Knockout!",
    "💪 Powerful combination!",
    "😵 You got dropped!",
],

"arena": [
    "⚔️ ARENA VICTORY!",
    "🔥 You defeated your opponent!",
    "⚔️ Critical hit!",
    "💀 You were defeated!",
],

"detective": [
    "🕵🏾 Case solved!",
    "🔍 You found the clue!",
    "🧠 Brilliant deduction!",
    "😅 Wrong suspect!",
],

"murder_mystery": [
    "🔎 Mystery solved!",
    "🕵🏾 You found the killer!",
    "🔍 Critical clue discovered!",
    "😅 Wrong suspect!",
],

"escape": [
    "🚪 You escaped!",
    "🔐 Door unlocked!",
    "🧠 Puzzle solved!",
    "⛓️ You're still trapped!",
],

"investigation": [
    "🔍 Evidence discovered!",
    "🕵🏾 Investigation successful!",
    "🧠 Case breakthrough!",
    "😅 Dead end!",
],
```

}

# ==========================================================

# RANDOM CHALLENGE ENGINE

# ==========================================================

async def random_challenge_game(
query,
game_id,
):

```
outcomes = CHALLENGES.get(
    game_id,
    [
        "🎮 Challenge completed!",
        "🔥 Great job!",
        "🏆 Excellent!",
        "😅 Try again!",
    ],
)

outcome = random.choice(
    outcomes
)

positive = not (
    "missed" in outcome.lower()
    or "escaped" in outcome.lower()
    or "wiped" in outcome.lower()
    or "fumble" in outcome.lower()
    or "air ball" in outcome.lower()
    or "strikeout" in outcome.lower()
    or "rocked" in outcome.lower()
    or "submitted" in outcome.lower()
    or "dropped" in outcome.lower()
    or "defeated" in outcome.lower()
    or "trapped" in outcome.lower()
    or "wrong" in outcome.lower()
    or "dead end" in outcome.lower()
    or "control" in outcome.lower()
    or "countered" in outcome.lower()
    or "bad reaction" in outcome.lower()
    or "hit a huge wave" in outcome.lower()
    or "spun out" in outcome.lower()
)

score = random.randint(
    40,
    100,
)

await show_result(
    query,
    game_id,
    f"<b>{GAME_NAMES.get(game_id, '🎮 Game')}</b>",
    outcome,
    score,
    positive,
)
```

# ==========================================================

# TRUTH OR DARE

# ==========================================================

TRUTHS = [
"What is something you've never told the group?",
"Who in the group has the best personality?",
"What's your biggest guilty pleasure?",
"What's the wildest thing you've ever done?",
"What is one thing you want to try someday?",
]

DARES = [
"Send the funniest GIF you can find.",
"Give someone in the group a genuine compliment.",
"Change your profile picture for 10 minutes.",
"Send your best pickup line.",
"Tell the group your most embarrassing story.",
]

async def truth_dare_game(
query,
):

```
keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🔥 TRUTH",
                callback_data="game_td_truth",
            ),
            InlineKeyboardButton(
                "😈 DARE",
                callback_data="game_td_dare",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ],
    ]
)

await query.edit_message_text(
    "🔥 <b>TRUTH OR DARE</b>\n\n"
    "Choose your challenge!",
    reply_markup=keyboard,
    parse_mode=ParseMode.HTML,
)
```

async def truth_dare_answer(
query,
choice,
):

```
if choice == "truth":

    prompt = random.choice(
        TRUTHS
    )

    title = "🔥 TRUTH"

else:

    prompt = random.choice(
        DARES
    )

    title = "😈 DARE"

await query.edit_message_text(
    f"<b>{title}</b>\n\n"
    f"{prompt}\n\n"
    "🔥 Good luck!",
    reply_markup=InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 Another",
                    callback_data="games_play_truth_dare",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Game Center",
                    callback_data="games_home",
                )
            ],
        ]
    ),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# TRIVIA QUESTIONS

# ==========================================================

TRIVIA = {

```
"general_trivia": [
    (
        "What is the largest planet?",
        ["Earth", "Mars", "Jupiter", "Venus"],
        "Jupiter",
    ),
    (
        "How many continents are there?",
        ["5", "6", "7", "8"],
        "7",
    ),
    (
        "What is the fastest land animal?",
        ["Lion", "Cheetah", "Horse", "Tiger"],
        "Cheetah",
    ),
],

"music_trivia": [
    (
        "Which instrument has 88 keys?",
        ["Guitar", "Piano", "Drums", "Violin"],
        "Piano",
    ),
    (
        "How many strings does a standard guitar have?",
        ["4", "5", "6", "7"],
        "6",
    ),
    (
        "Which musical symbol indicates silence?",
        ["Rest", "Sharp", "Flat", "Clef"],
        "Rest",
    ),
],

"sports_trivia": [
    (
        "How many players are on a basketball team on the court?",
        ["4", "5", "6", "7"],
        "5",
    ),
    (
        "How many bases are on a baseball field?",
        ["3", "4", "5", "6"],
        "4",
    ),
    (
        "How many points is a touchdown worth before the extra point?",
        ["3", "6", "7", "8"],
        "6",
    ),
],

"movie_trivia": [
    (
        "Which superhero carries a shield?",
        ["Batman", "Spider-Man", "Captain America", "Thor"],
        "Captain America",
    ),
    (
        "Which movie features the character Jack Sparrow?",
        ["Avatar", "Pirates of the Caribbean", "Titanic", "Rocky"],
        "Pirates of the Caribbean",
    ),
    (
        "Who is Shrek's best friend?",
        ["Donkey", "Fiona", "Puss", "Dragon"],
        "Donkey",
    ),
],

"word_challenge": [
    (
        "Which word is spelled correctly?",
        ["Necessary", "Necesary", "Neccessary", "Necassary"],
        "Necessary",
    ),
    (
        "What is the opposite of 'ancient'?",
        ["Old", "Modern", "Historic", "Past"],
        "Modern",
    ),
    (
        "Which word means very happy?",
        ["Sad", "Angry", "Ecstatic", "Tired"],
        "Ecstatic",
    ),
],
```

}

async def trivia_game(
query,
context,
game_id,
):

```
questions = TRIVIA.get(
    game_id,
    [],
)

if not questions:

    await query.answer(
        "Trivia is not available yet.",
        show_alert=True,
    )

    return

question, answers, correct = random.choice(
    questions
)

context.user_data[
    "trivia"
] = {
    "game_id": game_id,
    "correct": correct,
}

buttons = []

for answer in answers:

    buttons.append(
        [
            InlineKeyboardButton(
                answer,
                callback_data=(
                    "game_trivia_"
                    + answer
                ),
            )
        ]
    )

await query.edit_message_text(
    f"<b>{GAME_NAMES[game_id]}</b>\n\n"
    f"{question}",
    reply_markup=InlineKeyboardMarkup(
        buttons
    ),
    parse_mode=ParseMode.HTML,
)
```

async def trivia_answer(
query,
context,
answer,
):

```
data = context.user_data.pop(
    "trivia",
    None,
)

if not data:

    await query.answer(
        "Start a new trivia game.",
        show_alert=True,
    )

    return

correct = data["correct"]
game_id = data["game_id"]

won = (
    answer == correct
)

await show_result(
    query,
    game_id,
    f"<b>{GAME_NAMES[game_id]}</b>",
    (
        f"Your answer: <b>{answer}</b>\n"
        f"Correct answer: <b>{correct}</b>\n\n"
        + (
            "🎉 Correct!"
            if won
            else "❌ Incorrect!"
        )
    ),
    100 if won else 20,
    won,
)
```

# ==========================================================

# GAME ROUTER

# ==========================================================

async def play_game(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
game_id,
):

```
query = update.callback_query

if not query:
    return

user = update.effective_user

if not user:
    return

ensure_player(
    user_id=user.id,
    username=user.username,
    display_name=user.full_name,
)

try:

    if game_id == "reaction":

        await reaction_game(
            query,
            context,
        )

        return

    if game_id == "number_guess":

        await number_guess_game(
            query,
            context,
        )

        return

    if game_id == "high_low":

        await high_low_game(
            query,
            context,
        )

        return

    if game_id == "coin_flip":

        await coin_flip_game(
            query,
            context,
        )

        return

    if game_id == "dice_roll":

        await dice_roll_game(
            query,
            context,
        )

        return

    if game_id == "truth_dare":

        await truth_dare_game(
            query,
        )

        return

    if game_id in TRIVIA:

        await trivia_game(
            query,
            context,
            game_id,
        )

        return

    await random_challenge_game(
        query,
        game_id,
    )

except Exception:

    logger.exception(
        "Game failed: %s",
        game_id,
    )

    await query.edit_message_text(
        "⚠️ <b>Game Error</b>\n\n"
        "Something went wrong starting "
        "this game.\n\n"
        "Please try again.",
        reply_markup=game_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )
```

# ==========================================================

# CENTRAL CALLBACK ROUTER

# ==========================================================

async def games_callback_router(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

data = query.data or ""

# ------------------------------------------------------
# REACTION TAP
# ------------------------------------------------------

if data == "game_reaction_tap":

    await query.answer()

    await reaction_tap(
        query,
        context,
    )

    return

# ------------------------------------------------------
# NUMBER GUESS
# ------------------------------------------------------

if data.startswith(
    "game_guess_"
):

    await query.answer()

    guess = data[
        len("game_guess_"):
    ]

    await number_guess_answer(
        query,
        context,
        guess,
    )

    return

# ------------------------------------------------------
# HIGH / LOW
# ------------------------------------------------------

if data == "game_high":

    await query.answer()

    await high_low_answer(
        query,
        context,
        "high",
    )

    return

if data == "game_low":

    await query.answer()

    await high_low_answer(
        query,
        context,
        "low",
    )

    return

# ------------------------------------------------------
# TRUTH / DARE
# ------------------------------------------------------

if data == "game_td_truth":

    await query.answer()

    await truth_dare_answer(
        query,
        "truth",
    )

    return

if data == "game_td_dare":

    await query.answer()

    await truth_dare_answer(
        query,
        "dare",
    )

    return

# ------------------------------------------------------
# TRIVIA
# ------------------------------------------------------

if data.startswith(
    "game_trivia_"
):

    await query.answer()

    answer = data[
        len("game_trivia_"):
    ]

    await trivia_answer(
        query,
        context,
        answer,
    )

    return

# ------------------------------------------------------
# GAME PLAY
# ------------------------------------------------------

if data.startswith(
    "games_play_"
):

    await query.answer()

    game_id = data[
        len("games_play_"):
    ]

    await play_game(
        update,
        context,
        game_id,
    )

    return
```

# ==========================================================

# END games.py

# ==========================================================
