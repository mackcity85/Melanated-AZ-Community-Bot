"""Admin override controls for approved Dirty Minds rooms.

Admins can approve a Dirty Minds room and start it themselves if the host
never presses START.  This runs before the legacy approval callback so the
admin message retains a START button after approval.
"""

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationHandlerStop, CallbackQueryHandler, ContextTypes

from real_games.game_manager import GAME_MANAGER
from real_games.dirty_minds import start_game
from real_games.real_games import _notify_dirty_minds_started

logger = logging.getLogger("melanatedaz.dirty_minds_admin_override")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "0") or "0")


def _room_id(data: str) -> str:
    return data.rsplit("_", 1)[-1]


async def _authorized(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    from admin import is_admin
    return await is_admin(user_id, context)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    data = query.data if query else ""
    if not query or not user:
        return

    if not await _authorized(user.id, context):
        await query.answer("⛔ Admin access required.", show_alert=True)
        raise ApplicationHandlerStop

    room_id = _room_id(data)
    room = GAME_MANAGER.get(room_id)
    if not room or room.game_id != "dirty_minds":
        await query.answer("Room no longer exists.", show_alert=True)
        raise ApplicationHandlerStop

    if data.startswith("games_dirty_minds_approve_"):
        if room.state.get("approval_status") not in ("pending", None):
            await query.answer("This request was already processed.", show_alert=True)
            raise ApplicationHandlerStop

        room.state["approval_status"] = "approved"
        room.state["approved_by"] = str(user.id)
        text = (
            "🎭 <b>DIRTY MINDS APPROVAL REQUEST</b>\n\n"
            f"<b>Room:</b> {room.room_id}\n"
            f"<b>Players:</b> {room.player_count()}/20\n\n"
            "✅ <b>Approved</b>\n"
            "The host can start the game. An admin can also start it if the host does not."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ START DIRTY MINDS", callback_data=f"games_dirty_minds_admin_start_{room.room_id}")],
            [InlineKeyboardButton("❌ DENY", callback_data=f"games_dirty_minds_deny_{room.room_id}")],
        ])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
        await query.answer("Dirty Minds approved. Admin START is available.")
        raise ApplicationHandlerStop

    if data.startswith("games_dirty_minds_deny_"):
        if room.state.get("approval_status") not in ("pending", None):
            await query.answer("This request was already processed.", show_alert=True)
            raise ApplicationHandlerStop
        room.state["approval_status"] = "denied"
        room.state["approved_by"] = None
        await query.edit_message_text(
            query.message.text_html + "\n\n❌ <b>Denied by an admin</b>",
            parse_mode="HTML",
        )
        await query.answer("Dirty Minds denied.")
        raise ApplicationHandlerStop

    if data.startswith("games_dirty_minds_admin_start_"):
        if room.state.get("approval_status") != "approved":
            await query.answer("This Dirty Minds game has not been approved.", show_alert=True)
            raise ApplicationHandlerStop
        if room.started:
            await query.answer("Dirty Minds is already running.", show_alert=True)
            raise ApplicationHandlerStop
        if room.finished:
            await query.answer("This game has already finished.", show_alert=True)
            raise ApplicationHandlerStop

        start_game(room)
        room.state["started_by_admin"] = str(user.id)
        _notify_dirty_minds_started(room)

        await query.edit_message_text(
            query.message.text_html + "\n\n▶️ <b>Started by an admin</b>",
            parse_mode="HTML",
        )
        await query.answer("Dirty Minds started.")
        raise ApplicationHandlerStop


def install_application(application):
    if getattr(application, "_dirty_minds_admin_override_installed", False):
        return
    application.add_handler(
        CallbackQueryHandler(
            handle,
            pattern=r"^games_dirty_minds_(?:approve|deny|admin_start)_",
        ),
        group=-1,
    )
    application._dirty_minds_admin_override_installed = True
    logger.info("Dirty Minds admin approval/start override enabled.")
