# ==========================================================

# Melanated AZ Bot

# games/game_center.py

#

# MELANATED AZ GAME CENTER

#

# Handles:

# - /games

# - Game Center menu

# - Game categories

# - Game menus

# - Player profiles

# - Leaderboards

# - Game database foundation

# - XP / Coins foundation

#

# The game list is controlled by:

#

# games/registry.py

#

# This file handles the Game Center UI and database.

# ==========================================================

import logging
from datetime import datetime

from telegram import (
Update,
InlineKeyboardButton,
InlineKeyboardMarkup,
)

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from raffle_database import get_connection

from games.registry import (
GAMES,
get_enabled_games,
get_game,
game_exists,
game_count,
)

# ==========================================================

# LOGGING

# ==========================================================

logger = logging.getLogger(
"melanated_az_bot.games"
)

# ==========================================================

# GAME CATEGORIES

# ==========================================================

GAME_CATEGORIES = {

```
"arcade": {
    "name": "🕹️ Arcade",
    "description": (
        "Classic fast-paced arcade games."
    ),
},

"outdoor": {
    "name": "🌲 Outdoor",
    "description": (
        "Fishing, hunting, camping and outdoor adventures."
    ),
},

"solo": {
    "name": "👤 Solo",
    "description": (
        "Games you can play by yourself."
    ),
},

"shooting": {
    "name": "🎯 Action & Shooting",
    "description": (
        "Target, shooting and action challenges."
    ),
},

"board": {
    "name": "🎲 Board Games",
    "description": (
        "Classic and strategic board games."
    ),
},

"party": {
    "name": "🎉 Party Games",
    "description": (
        "Games designed for the whole group."
    ),
},

"trivia": {
    "name": "🧠 Trivia & Brain",
    "description": (
        "Trivia, puzzles and brain challenges."
    ),
},

"sports": {
    "name": "🏆 Sports",
    "description": (
        "Sports challenges and competitions."
    ),
},

"racing": {
    "name": "🏎️ Racing",
    "description": (
        "Cars, motorcycles, boats and more."
    ),
},

"mystery": {
    "name": "🕵🏾 Mystery & Strategy",
    "description": (
        "Mysteries, investigations and strategy."
    ),
},

"fighting": {
    "name": "🥊 Fighting",
    "description": (
        "Arena battles and fighting games."
    ),
},
```

}

# ==========================================================

# CATEGORY GAME MAPPING

#

# Registry entries are the actual games.

#

# Each value is a list of game IDs from registry.py.

#

# This lets the same game appear in multiple categories

# without duplicating its definition.

# ==========================================================

CATEGORY_GAMES = {

```
"arcade": [
    "reaction",
    "number_guess",
    "high_low",
    "coin_flip",
    "dice_roll",
],

"outdoor": [
    "fishing",
    "camping",
    "hiking",
    "hunting",
    "survival",
],

"solo": [
    "number_guess",
    "coin_flip",
    "dice_roll",
    "high_low",
    "reaction",
],

"shooting": [
    "target",
    "quick_shot",
    "bullseye",
    "accuracy",
    "sniper",
],

"board": [
    "dice_roll",
    "high_low",
    "number_guess",
    "strategy",
    "dice_duel",
],

"party": [
    "coin_flip",
    "dice_roll",
    "truth_dare",
    "high_low",
    "reaction",
],

"trivia": [
    "general_trivia",
    "music_trivia",
    "sports_trivia",
    "movie_trivia",
    "word_challenge",
],

"sports": [
    "football",
    "basketball",
    "baseball",
    "boxing",
    "soccer",
],

"racing": [
    "car_race",
    "bike_race",
    "boat_race",
    "drag_race",
    "street_race",
],

"mystery": [
    "detective",
    "murder_mystery",
    "code_breaker",
    "escape",
    "investigation",
],

"fighting": [
    "boxing",
    "mma",
    "karate",
    "street_fight",
    "arena",
],
```

}

# ==========================================================

# TOTAL GAME COUNT

#

# Counts unique enabled games in registry.py.

#

# ==========================================================

def get_total_game_count():

```
enabled_games = get_enabled_games()

return len(enabled_games)
```

TOTAL_GAMES = get_total_game_count()

# ==========================================================

# CATEGORY GAMES

# ==========================================================

def get_category_games(
category_id,
):

```
game_ids = CATEGORY_GAMES.get(
    category_id,
    [],
)

games = []

for game_id in game_ids:

    game = get_game(
        game_id
    )

    if not game:
        continue

    if not game.get(
        "enabled",
        False,
    ):
        continue

    games.append(
        game
    )

return games
```

# ==========================================================

# CATEGORY GAME COUNT

# ==========================================================

def get_category_game_count(
category_id,
):

```
return len(
    get_category_games(
        category_id
    )
)
```

# ==========================================================

# DATABASE INITIALIZATION

# ==========================================================

def initialize_game_database():

```
conn = get_connection()

try:

    cursor = conn.cursor()

    # ==================================================
    # GAME PLAYERS
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            coins INTEGER NOT NULL DEFAULT 0,
            xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            games_played INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    # ==================================================
    # GAME SCORES
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_id TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES game_players(user_id)
                ON DELETE CASCADE
        )
        """
    )

    # ==================================================
    # GAME SESSIONS
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            game_data TEXT,
            started_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    # ==================================================
    # GAME STATS
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_stats (
            user_id INTEGER NOT NULL,
            game_id TEXT NOT NULL,
            games_played INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            high_score INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, game_id),
            FOREIGN KEY (user_id)
                REFERENCES game_players(user_id)
                ON DELETE CASCADE
        )
        """
    )

    # ==================================================
    # ACHIEVEMENTS
    # ==================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL,
            unlocked_at TEXT NOT NULL,
            UNIQUE(user_id, achievement_id),
            FOREIGN KEY (user_id)
                REFERENCES game_players(user_id)
                ON DELETE CASCADE
        )
        """
    )

    # ==================================================
    # INDEXES
    # ==================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_game_scores_game_id
        ON game_scores(game_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_game_scores_user_id
        ON game_scores(user_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_game_sessions_user_id
        ON game_sessions(user_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_game_sessions_status
        ON game_sessions(status)
        """
    )

    conn.commit()

    logger.info(
        "Game Center database initialized."
    )

except Exception:

    conn.rollback()

    logger.exception(
        "Game Center database initialization failed."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# CREATE / UPDATE PLAYER

# ==========================================================

def ensure_game_player(
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

except Exception:

    conn.rollback()

    logger.exception(
        "Could not create/update game player."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# GAME CENTER KEYBOARD

# ==========================================================

def game_center_keyboard():

```
keyboard = []

categories = list(
    GAME_CATEGORIES.items()
)

for index in range(
    0,
    len(categories),
    2,
):

    row = []

    first_key, first_category = categories[
        index
    ]

    row.append(
        InlineKeyboardButton(
            first_category["name"],
            callback_data=(
                f"games_category_{first_key}"
            ),
        )
    )

    if index + 1 < len(categories):

        second_key, second_category = categories[
            index + 1
        ]

        row.append(
            InlineKeyboardButton(
                second_category["name"],
                callback_data=(
                    f"games_category_{second_key}"
                ),
            )
        )

    keyboard.append(row)

keyboard.append(
    [
        InlineKeyboardButton(
            "👤 My Game Profile",
            callback_data="games_profile",
        ),
        InlineKeyboardButton(
            "🏆 Leaderboards",
            callback_data="games_leaderboards",
        ),
    ]
)

return InlineKeyboardMarkup(
    keyboard
)
```

# ==========================================================

# CATEGORY GAME KEYBOARD

# ==========================================================

def category_game_keyboard(
category_id,
):

```
games = get_category_games(
    category_id
)

keyboard = []

for game in games:

    game_id = game["callback"].replace(
        "games_",
        "",
        1,
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                game["name"],
                callback_data=(
                    f"games_play_{game_id}"
                ),
            )
        ]
    )

keyboard.append(
    [
        InlineKeyboardButton(
            "⬅️ Game Center",
            callback_data="games_home",
        )
    ]
)

return InlineKeyboardMarkup(
    keyboard
)
```

# ==========================================================

# /GAMES

# ==========================================================

async def games_command(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
message = update.effective_message
user = update.effective_user

if not message or not user:
    return

ensure_game_player(
    user_id=user.id,
    username=user.username,
    display_name=user.full_name,
)

total_games = get_total_game_count()

text = (
    "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
    "Welcome to the Game Center! 👑\n\n"
    f"🎮 <b>{total_games} Games</b>\n"
    "🪙 Earn AZ Coins\n"
    "⭐ Earn XP\n"
    "🏆 Build your stats\n"
    "🥇 Compete for high scores\n\n"
    "Choose a category below:"
)

await message.reply_text(
    text,
    reply_markup=game_center_keyboard(),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# CATEGORY CALLBACK

# ==========================================================

async def games_category_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

await query.answer()

data = query.data or ""

prefix = "games_category_"

if not data.startswith(prefix):
    return

category_id = data[
    len(prefix):
]

category = GAME_CATEGORIES.get(
    category_id
)

if not category:

    await query.answer(
        "Category not found.",
        show_alert=True,
    )

    return

games = get_category_games(
    category_id
)

count = len(games)

text = (
    f"<b>{category['name']}</b>\n\n"
    f"{category['description']}\n\n"
    f"🎮 <b>{count} games available</b>\n\n"
    "Choose a game:"
)

if not games:

    text = (
        f"<b>{category['name']}</b>\n\n"
        f"{category['description']}\n\n"
        "🚧 <b>Games are being added.</b>\n\n"
        "Check back soon!"
    )

await query.edit_message_text(
    text,
    reply_markup=category_game_keyboard(
        category_id
    ),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# GAME CENTER HOME

# ==========================================================

async def games_home_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

await query.answer()

total_games = get_total_game_count()

text = (
    "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
    f"🎮 <b>{total_games} Games</b>\n"
    "🪙 Earn AZ Coins\n"
    "⭐ Earn XP\n"
    "🏆 Build your stats\n"
    "🥇 Compete for high scores\n\n"
    "Choose a category below:"
)

await query.edit_message_text(
    text,
    reply_markup=game_center_keyboard(),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# GAME PROFILE

# ==========================================================

async def games_profile_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query
user = update.effective_user

if not query or not user:
    return

await query.answer()

ensure_game_player(
    user_id=user.id,
    username=user.username,
    display_name=user.full_name,
)

conn = get_connection()

try:

    player = conn.execute(
        """
        SELECT *
        FROM game_players
        WHERE user_id = ?
        """,
        (user.id,),
    ).fetchone()

finally:

    conn.close()

if not player:

    await query.answer(
        "Game profile not found.",
        show_alert=True,
    )

    return

win_rate = 0

total_games = (
    player["wins"] +
    player["losses"]
)

if total_games > 0:

    win_rate = round(
        (
            player["wins"]
            / total_games
        ) * 100
    )

text = (
    "👤 <b>MY GAME PROFILE</b>\n\n"
    f"👑 <b>{player['display_name']}</b>\n\n"
    f"⭐ Level: <b>{player['level']}</b>\n"
    f"✨ XP: <b>{player['xp']:,}</b>\n"
    f"🪙 AZ Coins: <b>{player['coins']:,}</b>\n\n"
    f"🎮 Games Played: <b>{player['games_played']:,}</b>\n"
    f"🏆 Wins: <b>{player['wins']:,}</b>\n"
    f"💀 Losses: <b>{player['losses']:,}</b>\n"
    f"📊 Win Rate: <b>{win_rate}%</b>"
)

keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    ]
)

await query.edit_message_text(
    text,
    reply_markup=keyboard,
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# LEADERBOARDS

# ==========================================================

async def games_leaderboards_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

await query.answer()

conn = get_connection()

try:

    players = conn.execute(
        """
        SELECT
            display_name,
            xp,
            coins,
            wins
        FROM game_players
        ORDER BY xp DESC
        LIMIT 10
        """
    ).fetchall()

finally:

    conn.close()

if not players:

    leaderboard_text = (
        "🏆 <b>GAME LEADERBOARD</b>\n\n"
        "No players yet.\n\n"
        "Be the first to play!"
    )

else:

    lines = [
        "🏆 <b>GAME LEADERBOARD</b>\n"
    ]

    medals = [
        "🥇",
        "🥈",
        "🥉",
    ]

    for index, player in enumerate(
        players,
        start=1,
    ):

        if index <= 3:
            medal = medals[index - 1]
        else:
            medal = f"{index}."

        display_name = (
            player["display_name"]
            or "Player"
        )

        lines.append(
            f"{medal} "
            f"<b>{display_name}</b> "
            f"— ⭐ {player['xp']:,} XP"
        )

    leaderboard_text = "\n".join(
        lines
    )

keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ]
    ]
)

await query.edit_message_text(
    leaderboard_text,
    reply_markup=keyboard,
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# GAME PLAY CALLBACK

# ==========================================================

async def games_play_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query
user = update.effective_user

if not query or not user:
    return

data = query.data or ""

prefix = "games_play_"

if not data.startswith(prefix):
    return

await query.answer()

game_id = data[
    len(prefix):
]

# ------------------------------------------------------
# Verify game exists.
# ------------------------------------------------------

game = get_game(
    game_id
)

if not game or not game.get(
    "enabled",
    False,
):

    await query.answer(
        "⚠️ That game is not available.",
        show_alert=True,
    )

    return

# ------------------------------------------------------
# Ensure player exists.
# ------------------------------------------------------

ensure_game_player(
    user_id=user.id,
    username=user.username,
    display_name=user.full_name,
)

game_name = game.get(
    "name",
    "🎮 Game",
)

description = game.get(
    "description",
    "",
)

command = game.get(
    "command",
    "",
)

text = (
    f"{game_name}\n\n"
    f"{description}\n\n"
    "🚧 <b>Gameplay module coming next!</b>\n\n"
    "The Game Center button is working and "
    "the game is registered correctly.\n\n"
    "🪙 AZ Coins\n"
    "⭐ XP\n"
    "🏆 Scores\n"
    "🎖️ Achievements"
)

if command:

    text += (
        "\n\n"
        f"⌨️ Command: <code>{command}</code>"
    )

keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "⬅️ Game Center",
                callback_data="games_home",
            )
        ],
    ]
)

await query.edit_message_text(
    text,
    reply_markup=keyboard,
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# INITIALIZE GAME DATABASE

# ==========================================================

initialize_game_database()

# ==========================================================

# END game_center.py

# ==========================================================
