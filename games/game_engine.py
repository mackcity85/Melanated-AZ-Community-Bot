# ==========================================================

# Melanated AZ Bot

# games/game_engine.py

#

# MELANATED AZ GAME ENGINE

#

# Shared engine for all Game Center games.

#

# Handles:

# - Player creation

# - XP

# - AZ Coins

# - Levels

# - Games played

# - Wins

# - Losses

# - High scores

# - Game statistics

# - Game sessions

# - Achievements

# ==========================================================

import json
import logging
from datetime import datetime

from raffle_database import get_connection

logger = logging.getLogger(
"melanated_az_bot.games.engine"
)

# ==========================================================

# REWARDS

# ==========================================================

BASE_XP_WIN = 25
BASE_XP_LOSS = 5

BASE_COINS_WIN = 10
BASE_COINS_LOSS = 2

# ==========================================================

# LEVEL SYSTEM

# ==========================================================

def calculate_level(xp):
"""
Calculate player level from XP.

```
Every 100 XP = one additional level.
"""

try:
    xp = max(0, int(xp))
except (TypeError, ValueError):
    xp = 0

return max(
    1,
    (xp // 100) + 1,
)
```

def xp_for_next_level(xp):
"""
Return XP required for the next level.
"""

```
level = calculate_level(xp)

return level * 100
```

# ==========================================================

# ENSURE PLAYER

# ==========================================================

def ensure_player(
user_id,
username=None,
display_name=None,
):
"""
Create the player if they don't exist.

```
Existing player information is updated.
"""

now = datetime.utcnow().isoformat()

conn = get_connection()

try:

    conn.execute(
        """
        INSERT INTO game_players (
            user_id,
            username,
            display_name,
            coins,
            xp,
            level,
            games_played,
            wins,
            losses,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, 0, 0, 1, 0, 0, 0, ?, ?
        )

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
        "Could not ensure game player."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# GET PLAYER

# ==========================================================

def get_player(user_id):
"""
Return a player's complete profile.
"""

```
conn = get_connection()

try:

    player = conn.execute(
        """
        SELECT *
        FROM game_players
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    return player

finally:

    conn.close()
```

# ==========================================================

# START GAME SESSION

# ==========================================================

def start_game_session(
game_id,
chat_id,
user_id,
game_data=None,
):
"""
Create a new active game session.
"""

```
now = datetime.utcnow().isoformat()

if game_data is not None:

    game_data = json.dumps(
        game_data
    )

conn = get_connection()

try:

    # Close any previous active session
    # for this player and chat.

    conn.execute(
        """
        UPDATE game_sessions
        SET status = 'closed',
            updated_at = ?
        WHERE user_id = ?
          AND chat_id = ?
          AND status = 'active'
        """,
        (
            now,
            user_id,
            chat_id,
        ),
    )

    cursor = conn.execute(
        """
        INSERT INTO game_sessions (
            game_id,
            chat_id,
            user_id,
            status,
            game_data,
            started_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, 'active', ?, ?, ?
        )
        """,
        (
            game_id,
            chat_id,
            user_id,
            game_data,
            now,
            now,
        ),
    )

    session_id = cursor.lastrowid

    conn.commit()

    return session_id

except Exception:

    conn.rollback()

    logger.exception(
        "Could not start game session."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# GET ACTIVE SESSION

# ==========================================================

def get_active_session(
user_id,
chat_id,
):
"""
Return the player's active session.
"""

```
conn = get_connection()

try:

    session = conn.execute(
        """
        SELECT *
        FROM game_sessions
        WHERE user_id = ?
          AND chat_id = ?
          AND status = 'active'
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            user_id,
            chat_id,
        ),
    ).fetchone()

    return session

finally:

    conn.close()
```

# ==========================================================

# UPDATE GAME SESSION

# ==========================================================

def update_game_session(
session_id,
game_data=None,
status=None,
):
"""
Update an existing game session.
"""

```
now = datetime.utcnow().isoformat()

conn = get_connection()

try:

    if game_data is not None:

        game_data = json.dumps(
            game_data
        )

    if status is not None:

        conn.execute(
            """
            UPDATE game_sessions
            SET game_data = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                game_data,
                status,
                now,
                session_id,
            ),
        )

    else:

        conn.execute(
            """
            UPDATE game_sessions
            SET game_data = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                game_data,
                now,
                session_id,
            ),
        )

    conn.commit()

except Exception:

    conn.rollback()

    logger.exception(
        "Could not update game session."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# END GAME SESSION

# ==========================================================

def end_game_session(
session_id,
):
"""
Close a game session.
"""

```
now = datetime.utcnow().isoformat()

conn = get_connection()

try:

    conn.execute(
        """
        UPDATE game_sessions
        SET status = 'completed',
            updated_at = ?
        WHERE id = ?
        """,
        (
            now,
            session_id,
        ),
    )

    conn.commit()

except Exception:

    conn.rollback()

    logger.exception(
        "Could not end game session."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# RECORD GAME RESULT

# ==========================================================

def record_game_result(
user_id,
game_id,
won=False,
score=0,
xp=None,
coins=None,
):
"""
Record the result of a completed game.

```
Updates:
    - Player totals
    - Game-specific statistics
    - High score
    - XP
    - Coins
    - Level
    - Wins/losses
    - Games played
"""

try:
    score = max(
        0,
        int(score),
    )
except (TypeError, ValueError):
    score = 0

if xp is None:

    xp = (
        BASE_XP_WIN
        if won
        else BASE_XP_LOSS
    )

if coins is None:

    coins = (
        BASE_COINS_WIN
        if won
        else BASE_COINS_LOSS
    )

try:
    xp = max(0, int(xp))
    coins = max(0, int(coins))
except (TypeError, ValueError):

    xp = BASE_XP_LOSS
    coins = BASE_COINS_LOSS

now = datetime.utcnow().isoformat()

conn = get_connection()

try:

    # --------------------------------------------------
    # MAKE SURE PLAYER EXISTS
    # --------------------------------------------------

    conn.execute(
        """
        INSERT OR IGNORE INTO game_players (
            user_id,
            coins,
            xp,
            level,
            games_played,
            wins,
            losses,
            created_at,
            updated_at
        )
        VALUES (
            ?, 0, 0, 1, 0, 0, 0, ?, ?
        )
        """,
        (
            user_id,
            now,
            now,
        ),
    )

    # --------------------------------------------------
    # CURRENT PLAYER
    # --------------------------------------------------

    player = conn.execute(
        """
        SELECT *
        FROM game_players
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    if not player:
        raise RuntimeError(
            "Game player could not be created."
        )

    new_xp = (
        player["xp"] + xp
    )

    new_coins = (
        player["coins"] + coins
    )

    new_games_played = (
        player["games_played"] + 1
    )

    new_wins = (
        player["wins"] + (1 if won else 0)
    )

    new_losses = (
        player["losses"] + (0 if won else 1)
    )

    new_level = calculate_level(
        new_xp
    )

    # --------------------------------------------------
    # UPDATE PLAYER
    # --------------------------------------------------

    conn.execute(
        """
        UPDATE game_players
        SET
            coins = ?,
            xp = ?,
            level = ?,
            games_played = ?,
            wins = ?,
            losses = ?,
            updated_at = ?
        WHERE user_id = ?
        """,
        (
            new_coins,
            new_xp,
            new_level,
            new_games_played,
            new_wins,
            new_losses,
            now,
            user_id,
        ),
    )

    # --------------------------------------------------
    # GAME STATISTICS
    # --------------------------------------------------

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
        VALUES (
            ?, ?, 1, ?, ?, ?
        )

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
                    WHEN excluded.high_score > high_score
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

    # --------------------------------------------------
    # SCORE HISTORY
    # --------------------------------------------------

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

    conn.commit()

    return {
        "xp_earned": xp,
        "coins_earned": coins,
        "total_xp": new_xp,
        "total_coins": new_coins,
        "level": new_level,
        "games_played": new_games_played,
        "wins": new_wins,
        "losses": new_losses,
        "score": score,
        "won": won,
    }

except Exception:

    conn.rollback()

    logger.exception(
        "Could not record game result."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# GET GAME STATS

# ==========================================================

def get_game_stats(
user_id,
game_id,
):
"""
Return statistics for one player and one game.
"""

```
conn = get_connection()

try:

    stats = conn.execute(
        """
        SELECT *
        FROM game_stats
        WHERE user_id = ?
          AND game_id = ?
        """,
        (
            user_id,
            game_id,
        ),
    ).fetchone()

    return stats

finally:

    conn.close()
```

# ==========================================================

# SAVE ACHIEVEMENT

# ==========================================================

def unlock_achievement(
user_id,
achievement_id,
):
"""
Unlock an achievement.

```
Returns True if newly unlocked.
Returns False if already unlocked.
"""

now = datetime.utcnow().isoformat()

conn = get_connection()

try:

    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO game_achievements (
            user_id,
            achievement_id,
            unlocked_at
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            achievement_id,
            now,
        ),
    )

    conn.commit()

    return cursor.rowcount > 0

except Exception:

    conn.rollback()

    logger.exception(
        "Could not unlock achievement."
    )

    raise

finally:

    conn.close()
```

# ==========================================================

# GET ACHIEVEMENTS

# ==========================================================

def get_player_achievements(
user_id,
):
"""
Return all achievements unlocked by a player.
"""

```
conn = get_connection()

try:

    return conn.execute(
        """
        SELECT *
        FROM game_achievements
        WHERE user_id = ?
        ORDER BY unlocked_at ASC
        """,
        (user_id,),
    ).fetchall()

finally:

    conn.close()
```

# ==========================================================

# GAME RESULT MESSAGE

# ==========================================================

def format_game_result(
result,
title="GAME OVER",
):
"""
Create a standard Telegram-friendly result message.
"""

```
status = (
    "🏆 YOU WIN!"
    if result.get("won")
    else "💀 GAME OVER"
)

return (
    f"🎮 <b>{title}</b>\n\n"
    f"{status}\n\n"
    f"🎯 Score: <b>{result.get('score', 0):,}</b>\n"
    f"⭐ XP: <b>+{result.get('xp_earned', 0)}</b>\n"
    f"🪙 Coins: <b>+{result.get('coins_earned', 0)}</b>\n\n"
    f"⭐ Total XP: <b>{result.get('total_xp', 0):,}</b>\n"
    f"🪙 Total Coins: <b>{result.get('total_coins', 0):,}</b>\n"
    f"📈 Level: <b>{result.get('level', 1)}</b>"
)

```

# ==========================================================

# END game_engine.py

# ==========================================================
