# ==========================================================

# Melanated AZ Bot

# games/game_center.py

#

# GAME CENTER MENU / ROUTER

#

# Connects the Game Center menus to games/games.py

# ==========================================================

import logging
from datetime import datetime
from html import escape

from telegram import (
Update,
InlineKeyboardButton,
InlineKeyboardMarkup,
)

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from raffle_database import get_connection

from games.games import (
GAME_NAMES,
games_callback_router as gameplay_callback_router,
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
    "games": [
        "reaction",
        "number_guess",
        "high_low",
        "coin_flip",
        "dice_roll",
    ],
},

"outdoor": {
    "name": "🏕️ Outdoor",
    "games": [
        "fishing",
        "camping",
        "hiking",
        "hunting",
        "survival",
    ],
},

"shooting": {
    "name": "🎯 Shooting",
    "games": [
        "target",
        "quick_shot",
        "bullseye",
        "accuracy",
        "sniper",
    ],
},

"board": {
    "name": "♟️ Board",
    "games": [
        "strategy",
        "dice_duel",
    ],
},

"party": {
    "name": "🎉 Party",
    "games": [
        "truth_dare",
    ],
},

"trivia": {
    "name": "🧠 Trivia",
    "games": [
        "general_trivia",
        "music_trivia",
        "sports_trivia",
        "movie_trivia",
        "word_challenge",
    ],
},

"sports": {
    "name": "🏆 Sports",
    "games": [
        "football",
        "basketball",
        "baseball",
        "boxing",
        "soccer",
    ],
},

"racing": {
    "name": "🏎️ Racing",
    "games": [
        "car_race",
        "bike_race",
        "boat_race",
        "drag_race",
        "street_race",
    ],
},

"mystery": {
    "name": "🕵🏾 Mystery",
    "games": [
        "detective",
        "murder_mystery",
        "code_breaker",
        "escape",
        "investigation",
    ],
},

"fighting": {
    "name": "🥊 Fighting",
    "games": [
        "mma",
        "karate",
        "street_fight",
        "arena",
    ],
},
```

}

# ==========================================================

# MAIN GAME CENTER KEYBOARD

# ==========================================================

def game_center_keyboard():

```
buttons = []

for category_id, category in GAME_CATEGORIES.items():

    buttons.append(
        [
            InlineKeyboardButton(
                category["name"],
                callback_data=(
                    f"games_category_{category_id}"
                ),
            )
        ]
    )

buttons.append(
    [
        InlineKeyboardButton(
            "👤 My Profile",
            callback_data="games_profile",
        ),
        InlineKeyboardButton(
            "🏆 Leaderboards",
            callback_data="games_leaderboards",
        ),
    ]
)

return InlineKeyboardMarkup(buttons)
```

# ==========================================================

# CATEGORY KEYBOARD

# ==========================================================

def category_keyboard(category_id):

```
category = GAME_CATEGORIES.get(
    category_id
)

if not category:
    return game_center_keyboard()

buttons = []

for game_id in category["games"]:

    game_name = GAME_NAMES.get(
        game_id,
        game_id.replace("_", " ").title(),
    )

    buttons.append(
        [
            InlineKeyboardButton(
                game_name,
                callback_data=(
                    f"games_play_{game_id}"
                ),
            )
        ]
    )

buttons.append(
    [
        InlineKeyboardButton(
            "⬅️ Game Center",
            callback_data="games_home",
        )
    ]
)

return InlineKeyboardMarkup(buttons)
```

# ==========================================================

# GAMES COMMAND

# ==========================================================

async def games_command(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
message = update.effective_message
user = update.effective_user

if not message:
    return

if user:

    ensure_game_player(
        user.id,
        user.username,
        user.full_name,
    )

await message.reply_text(
    "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
    "Welcome to the Game Center!\n\n"
    "Choose a category below and start playing.\n\n"
    "🎯 Earn XP\n"
    "🪙 Earn AZ Coins\n"
    "🏆 Track your wins\n"
    "📊 Build your game profile",
    reply_markup=game_center_keyboard(),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# HOME

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

user = query.from_user

ensure_game_player(
    user.id,
    user.username,
    user.full_name,
)

await query.edit_message_text(
    "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
    "Choose a category below.\n\n"
    "🎯 Play games\n"
    "⭐ Earn XP\n"
    "🪙 Earn AZ Coins\n"
    "🏆 Climb the leaderboards",
    reply_markup=game_center_keyboard(),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# CATEGORY

# ==========================================================

async def games_category_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

data = query.data or ""

if not data.startswith(
    "games_category_"
):

    await query.answer(
        "Invalid game category.",
        show_alert=True,
    )

    return

category_id = data[
    len("games_category_"):
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

await query.answer()

await query.edit_message_text(
    f"<b>{category['name']}</b>\n\n"
    "Choose a game:",
    reply_markup=category_keyboard(
        category_id
    ),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# PROFILE

# ==========================================================

async def games_profile_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

await query.answer()

user = query.from_user

ensure_game_player(
    user.id,
    user.username,
    user.full_name,
)

player = get_player(
    user.id
)

if not player:

    await query.edit_message_text(
        "⚠️ Could not load your game profile.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Game Center",
                        callback_data="games_home",
                    )
                ]
            ]
        ),
    )

    return

level = player.get("level", 1)
xp = player.get("xp", 0)
coins = player.get("coins", 0)
games_played = player.get(
    "games_played",
    0,
)
wins = player.get("wins", 0)
losses = player.get("losses", 0)

text = (
    "👤 <b>MY GAME PROFILE</b>\n\n"
    f"👤 <b>{escape(user.full_name)}</b>\n\n"
    f"🏆 Level: <b>{level}</b>\n"
    f"⭐ XP: <b>{xp}</b>\n"
    f"🪙 AZ Coins: <b>{coins}</b>\n\n"
    f"🎮 Games Played: <b>{games_played}</b>\n"
    f"🥇 Wins: <b>{wins}</b>\n"
    f"💀 Losses: <b>{losses}</b>"
)

keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🏆 Leaderboards",
                callback_data="games_leaderboards",
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

players = get_leaderboard()

if not players:

    text = (
        "🏆 <b>LEADERBOARDS</b>\n\n"
        "No games have been played yet."
    )

else:

    lines = [
        "🏆 <b>MELANATED AZ LEADERBOARD</b>",
        "",
    ]

    medals = [
        "🥇",
        "🥈",
        "🥉",
    ]

    for index, player in enumerate(
        players
    ):

        if index < 3:
            position = medals[index]
        else:
            position = f"{index + 1}."

        name = (
            player.get("display_name")
            or player.get("username")
            or f"Player {player.get('user_id')}"
        )

        wins = player.get(
            "wins",
            0,
        )

        xp = player.get(
            "xp",
            0,
        )

        lines.append(
            f"{position} "
            f"<b>{escape(str(name))}</b> "
            f"— 🥇 {wins} wins | ⭐ {xp} XP"
        )

    text = "\n".join(lines)

keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="games_leaderboards",
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

await query.edit_message_text(
    text,
    reply_markup=keyboard,
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# GAME CALLBACK BRIDGE

#

# IMPORTANT:

#

# Menu callbacks:

#

# games_play_reaction

# games_play_number_guess

# games_play_high_low

# etc.

#

# Gameplay callbacks:

#

# game_reaction_tap

# game_guess_5

# game_high

# game_low

# game_td_truth

# game_td_dare

# game_trivia_...

#

# ALL OF THESE ARE SENT TO games/games.py

# ==========================================================

async def games_gameplay_callback(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

data = query.data or ""

logger.info(
    "Forwarding gameplay callback: %s",
    data,
)

try:

    await gameplay_callback_router(
        update,
        context,
    )

except Exception:

    logger.exception(
        "Gameplay callback failed: %s",
        data,
    )

    try:

        await query.answer(
            "⚠️ Game action failed.",
            show_alert=True,
        )

    except Exception:
        pass
```

# ==========================================================

# PLAYER DATABASE

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

finally:

    conn.close()
```

# ==========================================================

# GET PLAYER

# ==========================================================

def get_player(
user_id,
):

```
conn = get_connection()

try:

    cursor = conn.execute(
        """
        SELECT
            user_id,
            username,
            display_name,
            games_played,
            wins,
            losses,
            xp,
            coins,
            level
        FROM game_players
        WHERE user_id = ?
        """,
        (user_id,),
    )

    row = cursor.fetchone()

    if not row:
        return None

    columns = [
        description[0]
        for description in cursor.description
    ]

    return dict(
        zip(
            columns,
            row,
        )
    )

finally:

    conn.close()
```

# ==========================================================

# LEADERBOARD DATABASE QUERY

# ==========================================================

def get_leaderboard(
limit=10,
):

```
conn = get_connection()

try:

    cursor = conn.execute(
        """
        SELECT
            user_id,
            username,
            display_name,
            games_played,
            wins,
            losses,
            xp,
            coins,
            level
        FROM game_players
        ORDER BY
            wins DESC,
            xp DESC,
            coins DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()

    columns = [
        description[0]
        for description in cursor.description
    ]

    return [
        dict(
            zip(
                columns,
                row,
            )
        )
        for row in rows
    ]

finally:

    conn.close()
```

# ==========================================================

# DATABASE INITIALIZATION

# ==========================================================

def initialize_game_database():

```
conn = get_connection()

try:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS game_players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_id TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS game_stats (
            user_id INTEGER NOT NULL,
            game_id TEXT NOT NULL,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            high_score INTEGER DEFAULT 0,
            PRIMARY KEY (
                user_id,
                game_id
            )
        )
        """
    )

    conn.commit()

    logger.info(
        "Game Center database initialized."
    )

finally:

    conn.close()
```

# ==========================================================

# END games/game_center.py

# ==========================================================
