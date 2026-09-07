"""
Melanated AZ Real Games
Telegram Deep-Link Handler

Supported game payload:

    /start rg_snake
    /start rg_pong
    /start rg_breakout
    /start rg_dodge
    /start rg_2048
    /start rg_memory_match
    /start rg_reaction
    /start rg_whack_a_mole
    /start rg_basketball
    /start rg_target_shooter

Room payload:

    /start rg_join_<ROOM_ID>

This file intentionally contains NO Monopoly-specific routes.
"""

import logging

from .real_games import GAMES, get_game

logger = logging.getLogger(__name__)


# ==========================================================
# GAME IDS
# ==========================================================

VALID_GAME_IDS = {
    game["game_id"]
    for game in GAMES
}


# ==========================================================
# GAME LINK
# ==========================================================

def make_game_link(bot_username, game_id):
    """
    Create a Telegram deep link that opens a specific Real Game.
    """

    game_id = str(game_id).strip().lower()

    if game_id not in VALID_GAME_IDS:
        raise ValueError(f"Unknown Real Game: {game_id}")

    return (
        f"https://t.me/{bot_username}"
        f"?start=rg_{game_id}"
    )


# ==========================================================
# WEB GAME URL
# ==========================================================

def make_web_game_url(base_url, game_id):
    """
    Create the actual playable Real Games URL.
    """

    base_url = (base_url or "").rstrip("/")
    game_id = str(game_id).strip().lower()

    if game_id not in VALID_GAME_IDS:
        return None

    return f"{base_url}/real-games/play/{game_id}"


# ==========================================================
# TELEGRAM DEEP LINK HANDLER
# ==========================================================

async def handle_real_game_deep_link(update, context):

    if not update.effective_user:
        return False

    message = update.effective_message

    if not message:
        return False

    args = context.args or []

    if not args:
        return False

    payload = str(args[0]).strip().lower()

    # ------------------------------------------------------
    # ONLY HANDLE OUR REAL GAME PAYLOADS
    # ------------------------------------------------------

    if not payload.startswith("rg_"):
        return False

    user = update.effective_user

    logger.info(
        "Real Games deep link received: payload=%s user=%s",
        payload,
        user.id,
    )

    # ======================================================
    # OPEN A GAME
    # ======================================================

    if payload.startswith("rg_") and not payload.startswith("rg_join_"):

        game_id = payload[3:]

        game = get_game(game_id)

        if not game:

            await message.reply_text(
                "❌ <b>Game Not Found</b>\n\n"
                "That game is no longer available in the "
                "Melanated AZ Real Games Center.",
                parse_mode="HTML",
            )

            return True

        base_url = (
            context.bot_data.get("PUBLIC_BASE_URL")
            or "https://melanatedaz.onrender.com"
        )

        game_url = make_web_game_url(
            base_url,
            game_id,
        )

        if not game_url:
            await message.reply_text(
                "❌ Unable to create the game link."
            )

            return True

        await message.reply_text(
            f"{game['icon']} <b>{game['name']}</b>\n\n"
            f"{game['description']}\n\n"
            f"🎮 <a href=\"{game_url}\">PLAY {game['name'].upper()}</a>",
            parse_mode="HTML",
            disable_web_page_preview=False,
        )

        logger.info(
            "Opened Real Game: %s for user %s",
            game_id,
            user.id,
        )

        return True

    # ======================================================
    # JOIN ROOM
    # ======================================================

    if payload.startswith("rg_join_"):

        room_id = payload[len("rg_join_"):].strip()

        if not room_id:
            await message.reply_text(
                "❌ Invalid game room link."
            )

            return True

        # --------------------------------------------------
        # Import the game manager only when a room is used.
        # --------------------------------------------------

        try:
            from .game_manager import GAME_MANAGER
        except ImportError:

            logger.exception(
                "Game manager could not be imported."
            )

            await message.reply_text(
                "❌ Multiplayer rooms are temporarily unavailable."
            )

            return True

        game = GAME_MANAGER.get(room_id)

        if not game:

            await message.reply_text(
                "❌ <b>Game Room Not Found</b>\n\n"
                "That room may have expired or no longer exists.",
                parse_mode="HTML",
            )

            return True

        try:

            game.add_player(
                str(user.id),
                user.full_name or user.first_name,
            )

        except ValueError as exc:

            await message.reply_text(
                f"❌ {exc}"
            )

            return True

        # --------------------------------------------------
        # Determine which game the room belongs to.
        # --------------------------------------------------

        game_id = getattr(game, "game_id", None)

        if not game_id:
            game_id = getattr(game, "game_type", None)

        if not game_id:
            game_id = getattr(game, "name", None)

        if game_id:
            game_id = str(game_id).strip().lower()

        selected_game = get_game(game_id) if game_id else None

        if not selected_game:

            logger.warning(
                "Room %s has unknown game_id=%s",
                room_id,
                game_id,
            )

            await message.reply_text(
                "❌ This room is connected to a game that "
                "is no longer available."
            )

            return True

        # --------------------------------------------------
        # Create the correct web URL.
        # --------------------------------------------------

        base_url = (
            context.bot_data.get("PUBLIC_BASE_URL")
            or "https://melanatedaz.onrender.com"
        )

        game_url = make_web_game_url(
            base_url,
            selected_game["game_id"],
        )

        player_count = len(
            getattr(game, "players", {})
        )

        await message.reply_text(
            f"{selected_game['icon']} "
            f"<b>{selected_game['name'].upper()}</b>\n\n"
            f"Room: <code>{room_id}</code>\n"
            f"Players: {player_count}\n\n"
            f"🎮 <a href=\"{game_url}\">OPEN GAME</a>",
            parse_mode="HTML",
            disable_web_page_preview=False,
        )

        logger.info(
            "User %s joined Real Game room %s (%s)",
            user.id,
            room_id,
            selected_game["game_id"],
        )

        return True

    return False
