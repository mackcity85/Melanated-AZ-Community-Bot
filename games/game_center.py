# ==========================================================

# Melanated AZ Bot

# games/game_center.py

#

# COMPLETE GAME CENTER

#

# Handles:

# - Main Game Center

# - Categories

# - Game selection

# - Game launching

# - Profile

# - Leaderboards

# - Callback routing

# - Game database initialization

# ==========================================================

import logging

from telegram import (
Update,
InlineKeyboardButton,
InlineKeyboardMarkup,
)

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from raffle_database import get_connection

from .games import (
GAME_NAMES,
play_game,
)

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
    "name": "🌲 Outdoor",
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
    "name": "🔥 Party",
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
    "name": "🏁 Racing",
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
    "name": "⚔️ Fighting",
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
            created_at TEXT
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

# PLAYER

# ==========================================================

def ensure_game_player(user):

```
if not user:
    return

from datetime import datetime

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
            user.id,
            user.username,
            user.full_name,
            now,
            now,
        ),
    )

    conn.commit()

finally:

    conn.close()
```

# ==========================================================

# MAIN GAME CENTER

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

ensure_game_player(user)

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

await message.reply_text(
    "🎮 <b>GAME CENTER</b>\n\n"
    "Welcome to the Melanated AZ Game Center!\n\n"
    "Choose a category below.\n\n"
    "⭐ Earn XP\n"
    "🪙 Earn AZ Coins\n"
    "🏆 Build your stats",
    reply_markup=InlineKeyboardMarkup(
        buttons
    ),
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# COMPATIBILITY ALIAS

# ==========================================================

async def games_menu(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
await games_command(
    update,
    context,
)
```

# ==========================================================

# HOME CALLBACK

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

await query.edit_message_text(
    "🎮 <b>GAME CENTER</b>\n\n"
    "Choose a category below:",
    reply_markup=InlineKeyboardMarkup(
        buttons
    ),
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

data = query.data or ""

prefix = "games_category_"

if not data.startswith(prefix):

    await query.answer(
        "Invalid category.",
        show_alert=True,
    )

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

await query.answer()

buttons = []

for game_id in category["games"]:

    game_name = GAME_NAMES.get(
        game_id,
        "🎮 Game",
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

await query.edit_message_text(
    f"<b>{category['name']}</b>\n\n"
    "Choose a game:",
    reply_markup=InlineKeyboardMarkup(
        buttons
    ),
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

if not query:
    return

data = query.data or ""

prefix = "games_play_"

if not data.startswith(prefix):

    await query.answer(
        "Invalid game.",
        show_alert=True,
    )

    return

game_id = data[
    len(prefix):
]

if not game_id:

    await query.answer(
        "Game not found.",
        show_alert=True,
    )

    return

if game_id not in GAME_NAMES:

    await query.answer(
        "That game is not available yet.",
        show_alert=True,
    )

    return

logger.info(
    "Starting game: %s | user=%s",
    game_id,
    query.from_user.id,
)

await query.answer()

await play_game(
    update,
    context,
    game_id,
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

user = query.from_user

ensure_game_player(user)

conn = get_connection()

try:

    row = conn.execute(
        """
        SELECT
            games_played,
            wins,
            losses,
            xp,
            coins,
            level
        FROM game_players
        WHERE user_id = ?
        """,
        (user.id,),
    ).fetchone()

finally:

    conn.close()

if not row:

    await query.answer(
        "Profile not found.",
        show_alert=True,
    )

    return

await query.answer()

await query.edit_message_text(
    "👤 <b>MY GAME PROFILE</b>\n\n"
    f"👤 Player: <b>{user.full_name}</b>\n\n"
    f"🎮 Games Played: <b>{row[0]}</b>\n"
    f"🏆 Wins: <b>{row[1]}</b>\n"
    f"💀 Losses: <b>{row[2]}</b>\n"
    f"⭐ XP: <b>{row[3]}</b>\n"
    f"🪙 AZ Coins: <b>{row[4]}</b>\n"
    f"📈 Level: <b>{row[5]}</b>",
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

conn = get_connection()

try:

    rows = conn.execute(
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

await query.answer()

text = (
    "🏆 <b>GAME CENTER LEADERBOARD</b>\n\n"
)

if not rows:

    text += (
        "No players yet.\n\n"
        "Be the first to play!"
    )

else:

    medals = [
        "🥇",
        "🥈",
        "🥉",
    ]

    for index, row in enumerate(rows):

        name = (
            row[0]
            or "Player"
        )

        medal = (
            medals[index]
            if index < 3
            else f"{index + 1}."
        )

        text += (
            f"{medal} <b>{name}</b>\n"
            f"⭐ {row[1] or 0} XP | "
            f"🪙 {row[2] or 0} | "
            f"🏆 {row[3] or 0} wins\n\n"
        )

await query.edit_message_text(
    text,
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
    parse_mode=ParseMode.HTML,
)
```

# ==========================================================

# PROFILE ALIAS

# ==========================================================

async def games_profile(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
await games_profile_callback(
    update,
    context,
)
```

# ==========================================================

# LEADERBOARD ALIAS

# ==========================================================

async def games_leaderboards(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
await games_leaderboards_callback(
    update,
    context,
)
```

# ==========================================================

# CENTRAL CALLBACK ROUTER

# ==========================================================

async def game_center_callback_router(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
query = update.callback_query

if not query:
    return

data = query.data or ""

logger.info(
    "Game Center callback received: %s",
    data,
)

try:

    # --------------------------------------------------
    # HOME
    # --------------------------------------------------

    if data == "games_home":

        await games_home_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------
    # CATEGORY
    # --------------------------------------------------

    if data.startswith(
        "games_category_"
    ):

        await games_category_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------
    # PROFILE
    # --------------------------------------------------

    if data == "games_profile":

        await games_profile_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------
    # LEADERBOARDS
    # --------------------------------------------------

    if data == "games_leaderboards":

        await games_leaderboards_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------
    # PLAY GAME
    # --------------------------------------------------

    if data.startswith(
        "games_play_"
    ):

        await games_play_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------
    # GAME ENGINE CALLBACKS
    # --------------------------------------------------

    if data.startswith(
        "game_"
    ):

        from .games import (
            games_callback_router,
        )

        await games_callback_router(
            update,
            context,
        )

        return

    # --------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------

    logger.warning(
        "Game action not recognized: %s",
        data,
    )

    await query.answer(
        "⚠️ Game action not recognized.",
        show_alert=True,
    )

except Exception:

    logger.exception(
        "Game Center callback failed: %s",
        data,
    )

    try:

        await query.answer(
            "⚠️ Game Center action failed.",
            show_alert=True,
        )

    except Exception:
        pass
```

# ==========================================================

# END GAME CENTER

# ==========================================================
