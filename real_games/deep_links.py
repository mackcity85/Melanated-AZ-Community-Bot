"""
Telegram deep-link handling for Real Games.

Supported formats:

/start rg_monopoly
/start rg_monopoly_<ROOM_ID>
/start rg_join_<ROOM_ID>
"""

import logging

from .game_manager import GAME_MANAGER


logger = logging.getLogger(__name__)


def make_game_link(bot_username, game_id):
    return (
        f"https://t.me/{bot_username}"
        f"?start=rg_join_{game_id}"
    )


async def handle_real_game_deep_link(update, context):

    if not update.effective_user:
        return False

    args = context.args or []

    if not args:
        return False

    payload = args[0]

    if not payload.startswith("rg_"):
        return False

    user = update.effective_user

    # ------------------------------------------------------
    # OPEN MONOPOLY
    # ------------------------------------------------------

    if payload == "rg_monopoly":

        await update.message.reply_text(
            "🎲 <b>Melanated AZ Real Games</b>\n\n"
            "Monopoly is ready.\n\n"
            "Create a game from the Real Games menu "
            "or use a room invite link.",
            parse_mode="HTML",
        )

        return True

    # ------------------------------------------------------
    # JOIN ROOM
    # ------------------------------------------------------

    if payload.startswith("rg_join_"):

        game_id = payload[len("rg_join_"):].upper()

        game = GAME_MANAGER.get(game_id)

        if not game:

            await update.message.reply_text(
                "❌ That game room no longer exists."
            )

            return True

        try:

            game.add_player(
                str(user.id),
                user.full_name or user.first_name,
            )

        except ValueError as exc:

            await update.message.reply_text(
                f"❌ {exc}"
            )

            return True

        game_url = (
            f"{context.bot_data.get('PUBLIC_BASE_URL', '').rstrip('/')}"
            f"/real-games/monopoly/{game_id}"
        )

        if not game_url.startswith("http"):
            game_url = (
                f"/real-games/monopoly/{game_id}"
            )

        await update.message.reply_text(
            "🎲 <b>MONOPOLY</b>\n\n"
            f"Room: <code>{game_id}</code>\n"
            f"Players: {len(game.players)}/6\n\n"
            f"🎮 <a href=\"{game_url}\">OPEN GAME</a>",
            parse_mode="HTML",
            disable_web_page_preview=False,
        )

        return True

    return False
