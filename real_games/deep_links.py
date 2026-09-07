"""
Melanated AZ Real Games
Telegram Deep-Link Handler
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

from .real_games import (
    GAMES,
    get_game,
)
from .game_manager import GAME_MANAGER

logger = logging.getLogger(__name__)

VALID_GAME_IDS = {
    game["game_id"]
    for game in GAMES
}


def make_game_link(
    bot_username,
    game_id,
):

    game_id = (
        str(game_id)
        .strip()
        .lower()
    )

    if game_id not in VALID_GAME_IDS:
        raise ValueError(
            f"Unknown Real Game: {game_id}"
        )

    return (
        f"https://t.me/"
        f"{bot_username}"
        f"?start=rg_{game_id}"
    )


def make_room_join_link(
    bot_username,
    room_id,
):

    return (
        f"https://t.me/"
        f"{bot_username}"
        f"?start=rg_join_"
        f"{room_id}"
    )


def make_web_game_url(
    base_url,
    game_id,
    room_id=None,
    player_key=None,
):

    base_url = (
        base_url or ""
    ).rstrip("/")

    game_id = (
        str(game_id)
        .strip()
        .lower()
    )

    if game_id not in VALID_GAME_IDS:
        return None

    url = (
        f"{base_url}/real-games/"
        f"play/{game_id}"
    )

    params = {}

    if room_id:
        params["room"] = room_id

    if player_key:
        params["player_key"] = player_key

    if params:
        url += "?" + urlencode(params)

    return url


async def handle_real_game_deep_link(
    update,
    context,
):

    if not update.effective_user:
        return False

    message = update.effective_message

    if not message:
        return False

    args = context.args or []

    if not args:
        return False

    payload = (
        str(args[0])
        .strip()
        .lower()
    )

    if not payload.startswith("rg_"):
        return False

    user = update.effective_user

    logger.info(
        "Real Games deep link received: "
        "payload=%s user=%s",
        payload,
        user.id,
    )

    # ======================================================
    # NORMAL GAME
    # ======================================================

    if (
        payload.startswith("rg_")
        and not payload.startswith("rg_join_")
    ):

        game_id = payload[3:]

        game = get_game(game_id)

        if not game:

            await message.reply_text(
                "❌ <b>Game Not Found</b>",
                parse_mode="HTML",
            )

            return True

        base_url = (
            context.bot_data.get(
                "PUBLIC_BASE_URL"
            )
            or "https://melanatedaz.onrender.com"
        )

        game_url = make_web_game_url(
            base_url,
            game_id,
        )

        await message.reply_text(
            f"{game['icon']} "
            f"<b>{game['name']}</b>\n\n"
            f"{game['description']}\n\n"
            f"🎮 <a href=\"{game_url}\">"
            f"PLAY {game['name'].upper()}"
            f"</a>",
            parse_mode="HTML",
            disable_web_page_preview=False,
        )

        return True

    # ======================================================
    # JOIN MULTIPLAYER ROOM
    # ======================================================

    if payload.startswith("rg_join_"):

        room_id = payload[
            len("rg_join_"):
        ].strip().upper()

        if not room_id:

            await message.reply_text(
                "❌ Invalid game room link."
            )

            return True

        room = GAME_MANAGER.get(
            room_id
        )

        if not room:

            await message.reply_text(
                "❌ <b>Game Room Not Found</b>\n\n"
                "The room may have expired.",
                parse_mode="HTML",
            )

            return True

        try:

            player_key = room.add_player(
                str(user.id),
                user.full_name
                or user.first_name
                or "Player",
            )

        except ValueError as exc:

            await message.reply_text(
                f"❌ {exc}"
            )

            return True

        selected_game = get_game(
            room.game_id
        )

        if not selected_game:

            await message.reply_text(
                "❌ Game configuration is missing."
            )

            return True

        base_url = (
            context.bot_data.get(
                "PUBLIC_BASE_URL"
            )
            or "https://melanatedaz.onrender.com"
        )

        game_url = make_web_game_url(
            base_url,
            selected_game["game_id"],
            room.room_id,
            player_key,
        )

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎭 OPEN DIRTY MINDS",
                        url=game_url,
                    )
                ]
            ]
        )

        await message.reply_text(
            f"{selected_game['icon']} "
            f"<b>{selected_game['name'].upper()}</b>\n\n"
            f"You're in!\n\n"
            f"Room: <code>{room.room_id}</code>\n"
            f"Players: {room.player_count()}/"
            f"{room.max_players}\n\n"
            f"Tap below to enter the game room.",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        return True

    return False
