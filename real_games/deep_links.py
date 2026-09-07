# ==========================================================
# Melanated AZ Real Games
# deep_links.py
#
# Telegram deep-link handling for Real Games.
#
# Supported:
#
#   /start rg_snake
#   /start rg_pong
#   /start rg_breakout
#   /start rg_dodge
#   /start rg_2048
#   /start rg_memory_match
#   /start rg_reaction
#   /start rg_whack_a_mole
#   /start rg_basketball
#   /start rg_target_shooter
#
# Dirty Minds:
#
#   /start rg_join_<ROOM_ID>
#
# The Dirty Minds JOIN link:
#
#   1. Finds the game room
#   2. Adds the Telegram user to the room
#   3. Creates a private player key
#   4. Sends the user their personalized game link
#
# IMPORTANT:
# Telegram user IDs are NEVER placed in the browser URL.
# ==========================================================

from __future__ import annotations

import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
)

from .game_manager import GAME_MANAGER
from .real_games import (
    get_game,
)


logger = logging.getLogger(
    __name__
)


# ==========================================================
# CONFIGURATION
# ==========================================================

PUBLIC_BASE_URL = (
    "https://melanatedaz.onrender.com"
)


# ==========================================================
# WEB URL HELPERS
# ==========================================================

def make_web_game_url(
    game_id: str,
) -> str:
    """
    Create the normal URL for a single-player game.
    """

    base_url = (
        __import__(
            "os"
        ).getenv(
            "PUBLIC_BASE_URL",
            PUBLIC_BASE_URL,
        )
        .strip()
        .rstrip("/")
    )

    return (
        f"{base_url}"
        f"/real-games/play/"
        f"{game_id}"
    )


def make_dirty_minds_url(
    room_id: str,
    player_key: str,
) -> str:
    """
    Create a personalized Dirty Minds URL.

    The player key is random and is NOT the Telegram ID.
    """

    base_url = (
        __import__(
            "os"
        ).getenv(
            "PUBLIC_BASE_URL",
            PUBLIC_BASE_URL,
        )
        .strip()
        .rstrip("/")
    )

    return (
        f"{base_url}"
        f"/real-games/play/dirty_minds"
        f"?room={room_id}"
        f"&player_key={player_key}"
    )


# ==========================================================
# TELEGRAM DEEP LINK HANDLER
# ==========================================================

async def real_games_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle:

        /start rg_<GAME_ID>

    and:

        /start rg_join_<ROOM_ID>
    """

    if not update.effective_user:
        return

    user = update.effective_user

    args = context.args or []

    # ------------------------------------------------------
    # Normal /start
    # ------------------------------------------------------

    if not args:
        await _send_games_home(
            update
        )
        return

    payload = str(
        args[0]
    ).strip()

    # ------------------------------------------------------
    # Dirty Minds room join
    # ------------------------------------------------------

    if payload.lower().startswith(
        "rg_join_"
    ):
        room_id = payload[
            len("rg_join_"):
        ].strip().upper()

        await handle_dirty_minds_join(
            update,
            context,
            room_id,
        )

        return

    # ------------------------------------------------------
    # Normal game launch
    # ------------------------------------------------------

    if payload.lower().startswith(
        "rg_"
    ):
        game_id = payload[
            len("rg_"):
        ].strip().lower()

        await handle_game_launch(
            update,
            context,
            game_id,
        )

        return

    # ------------------------------------------------------
    # Unknown payload
    # ------------------------------------------------------

    await _send_games_home(
        update
    )


# ==========================================================
# NORMAL GAME LAUNCH
# ==========================================================

async def handle_game_launch(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game_id: str,
) -> None:
    """
    Open a normal Real Games game.
    """

    game = get_game(
        game_id
    )

    if not game:
        await _send_games_home(
            update
        )
        return

    # Dirty Minds must always be entered
    # through a room.
    if game_id == "dirty_minds":
        await update.effective_message.reply_text(
            "🎭 Dirty Minds is a multiplayer game.\n\n"
            "You need to join a Dirty Minds room "
            "from the JOIN button."
        )
        return

    game_url = make_web_game_url(
        game_id
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{game['icon']} PLAY {game['name'].upper()}",
                    url=game_url,
                )
            ],
            [
                InlineKeyboardButton(
                    "🎮 ALL GAMES",
                    url=(
                        game_url.split(
                            "/play/"
                        )[0]
                        + "/"
                    ),
                )
            ],
        ]
    )

    await update.effective_message.reply_text(
        f"{game['icon']} <b>{game['name']}</b>\n\n"
        f"{game.get('description', '')}\n\n"
        "Tap the button below to play.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ==========================================================
# DIRTY MINDS JOIN
# ==========================================================

async def handle_dirty_minds_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    room_id: str,
) -> None:
    """
    Add the Telegram user to a Dirty Minds room.
    """

    if not room_id:
        await update.effective_message.reply_text(
            "❌ Invalid Dirty Minds room."
        )
        return

    room = GAME_MANAGER.get(
        room_id
    )

    if not room:
        await update.effective_message.reply_text(
            "❌ This Dirty Minds game room "
            "no longer exists.\n\n"
            "Ask the host to create a new game."
        )
        return

    if room.game_id != "dirty_minds":
        await update.effective_message.reply_text(
            "❌ This is not a Dirty Minds room."
        )
        return

    user = update.effective_user

    user_id = str(
        user.id
    )

    display_name = (
        user.full_name
        or user.first_name
        or "Player"
    )

    # ------------------------------------------------------
    # Already in room
    # ------------------------------------------------------

    existing_player = room.get_player(
        user_id
    )

    if existing_player:
        player = existing_player

    else:
        # --------------------------------------------------
        # Room full
        # --------------------------------------------------

        if room.player_count() >= room.max_players:
            await update.effective_message.reply_text(
                "❌ This Dirty Minds room is full."
            )
            return

        try:
            player = room.add_player(
                user_id=user_id,
                display_name=display_name,
            )

        except ValueError as exc:
            await update.effective_message.reply_text(
                f"❌ {exc}"
            )
            return

    player_key = player.get(
        "player_key"
    )

    if not player_key:
        await update.effective_message.reply_text(
            "❌ Your game session could not be created.\n\n"
            "Please ask the host to create a new game."
        )
        return

    game_url = make_dirty_minds_url(
        room.room_id,
        player_key,
    )

    # ------------------------------------------------------
    # Build player list
    # ------------------------------------------------------

    player_lines = []

    for index, room_player in enumerate(
        room.players.values(),
        start=1,
    ):
        name = room_player.get(
            "name",
            "Player",
        )

        host_marker = (
            " 👑"
            if room_player.get(
                "host",
                False,
            )
            else ""
        )

        player_lines.append(
            f"{index}. {name}{host_marker}"
        )

    player_text = "\n".join(
        player_lines
    )

    # ------------------------------------------------------
    # Game button
    # ------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎭 ENTER DIRTY MINDS",
                    url=game_url,
                )
            ]
        ]
    )

    await update.effective_message.reply_text(
        "🎭 <b>DIRTY MINDS</b>\n\n"
        f"Room: <code>{room.room_id}</code>\n\n"
        "You're in! 👇\n\n"
        "🎤 Microphone: optional\n"
        "📷 Camera: optional\n"
        "🔇 You can use neither, either one, or both.\n\n"
        "<b>Players:</b>\n"
        f"{player_text}\n\n"
        "Tap ENTER DIRTY MINDS to open the game.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    # ------------------------------------------------------
    # Tell the group that someone joined.
    #
    # Only send this if the update came from a private
    # chat. If the JOIN link was clicked from the group,
    # Telegram normally opens the bot privately.
    # ------------------------------------------------------

    await _notify_host(
        context,
        room,
        display_name,
    )


# ==========================================================
# HOST NOTIFICATION
# ==========================================================

async def _notify_host(
    context: ContextTypes.DEFAULT_TYPE,
    room,
    player_name: str,
) -> None:
    """
    Notify the Telegram host that a new player joined.

    This uses the host's Telegram user ID internally.
    """

    host_id = room.host_id

    if not host_id:
        return

    try:
        host_id_int = int(
            host_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return

    # Do not message the host about themselves.
    # Telegram may still allow this, but it creates
    # unnecessary notifications.
    try:
        await context.bot.send_message(
            chat_id=host_id_int,
            text=(
                "🎭 <b>Dirty Minds Update</b>\n\n"
                f"👤 <b>{player_name}</b> joined your game.\n\n"
                f"👥 Players: "
                f"{room.player_count()}/"
                f"{room.max_players}\n\n"
                "Open the game to start when "
                "everyone is ready."
            ),
            parse_mode="HTML",
        )

    except Exception:
        logger.exception(
            "Unable to notify Dirty Minds host."
        )


# ==========================================================
# GAMES HOME
# ==========================================================

async def _send_games_home(
    update: Update,
) -> None:
    """
    Send a simple Real Games launcher link.
    """

    base_url = (
        __import__(
            "os"
        ).getenv(
            "PUBLIC_BASE_URL",
            PUBLIC_BASE_URL,
        )
        .strip()
        .rstrip("/")
    )

    games_url = (
        f"{base_url}/real-games/"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎮 OPEN REAL GAMES",
                    url=games_url,
                )
            ]
        ]
    )

    await update.effective_message.reply_text(
        "🎮 <b>Melanated AZ Real Games</b>\n\n"
        "Choose a game from the Real Games center.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ==========================================================
# HANDLER FACTORY
# ==========================================================

def get_real_games_handler():
    """
    Return the Telegram handler used by bot.py.

    Register this handler before any generic /start
    handler that might consume the same command.
    """

    return CommandHandler(
        "start",
        real_games_start,
    )
