"""Admin override controls for approved Dirty Minds rooms.

Admins can approve a Dirty Minds room and start it themselves if the host
never presses START. This runs before the legacy approval callback so the
admin message retains a START button after approval.
"""

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

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


async def _start_approved_room(room, admin_user_id: int, context: ContextTypes.DEFAULT_TYPE):
    if room.state.get("approval_status") != "approved":
        return False, "This Dirty Minds game has not been approved."
    if room.started:
        return False, "Dirty Minds is already running."
    if room.finished:
        return False, "This game has already finished."

    start_game(room)
    room.state["started_by_admin"] = str(admin_user_id)
    _notify_dirty_minds_started(room)
    return True, "Dirty Minds started."


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
        ok, message = await _start_approved_room(room, user.id, context)
        if not ok:
            await query.answer(message, show_alert=True)
            raise ApplicationHandlerStop

        await query.edit_message_text(
            query.message.text_html + "\n\n▶️ <b>Started by an admin</b>",
            parse_mode="HTML",
        )
        await query.answer(message)
        raise ApplicationHandlerStop


async def start_dirty_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow an admin to start an already-approved room by room ID.

    This is also a recovery path for approval requests that were approved
    before the admin START button was added.
    """
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return

    if not await _authorized(user.id, context):
        await message.reply_text("⛔ Admin access required.")
        return

    if not context.args:
        await message.reply_text("Usage: /startdirty ROOM_ID")
        return

    room_id = str(context.args[0]).strip().upper()
    room = GAME_MANAGER.get(room_id)
    if not room or room.game_id != "dirty_minds":
        await message.reply_text("❌ Dirty Minds room not found.")
        return

    ok, result = await _start_approved_room(room, user.id, context)
    if not ok:
        await message.reply_text(f"❌ {result}")
        return

    await message.reply_text(
        f"▶️ Dirty Minds <b>{room.room_id}</b> has been started by an admin.",
        parse_mode="HTML",
    )


def install_application(application):
    if getattr(application, "_dirty_minds_admin_override_installed", False):
        return

    application.add_handler(
        CommandHandler("startdirty", start_dirty_command),
        group=-1,
    )
    application.add_handler(
        CallbackQueryHandler(
            handle,
            pattern=r"^games_dirty_minds_(?:approve|deny|admin_start)_",
        ),
        group=-1,
    )
    application._dirty_minds_admin_override_installed = True
    logger.info("Dirty Minds admin approval/start override enabled.")
