# ==========================================================
# Melanated AZ Bot
# admin.py
# ==========================================================

import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from config import ADMIN_IDS

from raffle import (
    start_raffle,
    enter_raffle,
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
)

from raffle_database import (
    get_all_birthdays,
    remove_birthday_by_id,
)

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    try:
        return int(user_id) in [
            int(admin_id)
            for admin_id in ADMIN_IDS
        ]

    except (TypeError, ValueError):

        return False


# ==========================================================
# MAIN ADMIN KEYBOARD
#
# EVERYTHING IS ON ONE SCREEN
# ==========================================================

def admin_main_keyboard():

    return InlineKeyboardMarkup(
        [

            # ------------------------------------------------
            # RAFFLES
            # ------------------------------------------------

            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle",
                ),
                InlineKeyboardButton(
                    "🎫 Active Raffle",
                    callback_data="admin_active_raffle",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📊 Status",
                    callback_data="admin_status",
                ),
                InlineKeyboardButton(
                    "👥 Entries",
                    callback_data="admin_entries",
                ),
            ],

            [
                InlineKeyboardButton(
                    "⏳ Pending Payments",
                    callback_data="admin_pending",
                ),
                InlineKeyboardButton(
                    "✅ Completed Payments",
                    callback_data="admin_completed",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🏆 Draw Winner",
                    callback_data="admin_draw",
                ),
                InlineKeyboardButton(
                    "❌ Cancel Raffle",
                    callback_data="admin_cancel",
                ),
            ],

            # ------------------------------------------------
            # BIRTHDAYS
            # ------------------------------------------------

            [
                InlineKeyboardButton(
                    "🎂 Enter / Update Birthday",
                    callback_data="admin_birthday_enter",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📅 View My Birthday",
                    callback_data="admin_birthday_view",
                ),
                InlineKeyboardButton(
                    "🗑️ Remove My Birthday",
                    callback_data="admin_birthday_remove",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📋 All Birthdays",
                    callback_data="admin_all_birthdays",
                ),
            ],

            # ------------------------------------------------
            # REFRESH
            # ------------------------------------------------

            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_refresh",
                ),
            ],
        ]
    )


# ==========================================================
# ADMIN MENU
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user or not is_admin(user.id):

        if update.effective_message:

            await update.effective_message.reply_text(
                "⛔ You are not authorized to use "
                "the admin panel."
            )

        return

    text = (
        "👑 **Melanated AZ Admin Panel**\n\n"
        "Welcome, Admin.\n\n"
        "Everything you need is available below."
    )

    keyboard = admin_main_keyboard()

    if update.callback_query:

        query = update.callback_query

        await query.answer()

        try:

            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception:

            await query.message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        return

    await update.effective_message.reply_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# ==========================================================
# RUN RAFFLE HANDLER
# ==========================================================

async def run_raffle_handler(
    handler,
    update,
    context,
    action_name,
):

    try:

        await handler(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Error running admin raffle action: %s",
            action_name,
        )

        query = update.callback_query

        if query:

            try:

                await query.message.reply_text(
                    "⚠️ An error occurred while processing "
                    f"the **{action_name}** request.\n\n"
                    "Please try again.",
                    parse_mode="Markdown",
                )

            except Exception:
                pass


# ==========================================================
# START RAFFLE
# ==========================================================

async def admin_start_raffle(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        start_raffle,
        update,
        context,
        "Start Raffle",
    )


# ==========================================================
# ACTIVE RAFFLE
# ==========================================================

async def admin_active_raffle(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        enter_raffle,
        update,
        context,
        "Active Raffle",
    )


# ==========================================================
# STATUS
# ==========================================================

async def admin_status(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Status",
    )


# ==========================================================
# ENTRIES
# ==========================================================

async def admin_entries(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        raffle_entries,
        update,
        context,
        "Entries",
    )


# ==========================================================
# PENDING
# ==========================================================

async def admin_pending(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        pending_entries,
        update,
        context,
        "Pending Payments",
    )


# ==========================================================
# COMPLETED
# ==========================================================

async def admin_completed(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        paid_entry,
        update,
        context,
        "Completed Payments",
    )


# ==========================================================
# DRAW
# ==========================================================

async def admin_draw(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        draw_raffle,
        update,
        context,
        "Draw Winner",
    )


# ==========================================================
# CANCEL CONFIRMATION
# ==========================================================

def cancel_confirmation_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⚠️ YES — CANCEL RAFFLE",
                    callback_data="admin_confirm_cancel",
                )
            ],

            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_back",
                )
            ],
        ]
    )


# ==========================================================
# CANCEL
# ==========================================================

async def admin_cancel(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "⚠️ **Cancel Active Raffle?**\n\n"
        "This will cancel the currently active raffle.\n\n"
        "Are you sure you want to continue?",
        reply_markup=cancel_confirmation_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# CONFIRM CANCEL
# ==========================================================

async def admin_confirm_cancel(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    await run_raffle_handler(
        cancel_raffle,
        update,
        context,
        "Cancel Raffle",
    )


# ==========================================================
# REFRESH
# ==========================================================

async def admin_refresh(
    update,
    context,
):

    query = update.callback_query

    await query.answer(
        "Admin panel refreshed."
    )

    await query.edit_message_text(
        "👑 **Melanated AZ Admin Panel**\n\n"
        "Welcome, Admin.\n\n"
        "Everything you need is available below.",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# BACK
# ==========================================================

async def admin_back(
    update,
    context,
):

    await admin_menu(
        update,
        context,
    )


# ==========================================================
# BIRTHDAY — ENTER
# ==========================================================

async def admin_birthday_enter(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    context.user_data[
        "awaiting_birthday"
    ] = True

    await query.message.reply_text(
        "🎂 **Enter Your Birthday**\n\n"
        "Please send your birthday using:\n\n"
        "`MM/DD`\n\n"
        "Example:\n"
        "`08/26`\n\n"
        "Your birthday will be saved permanently "
        "in the Melanated AZ database.",
        parse_mode="Markdown",
    )


# ==========================================================
# BIRTHDAY — VIEW
# ==========================================================

async def admin_birthday_view(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    chat_id = query.message.chat_id

    from raffle_database import get_birthday

    record = get_birthday(
        user_id=user.id,
        chat_id=chat_id,
    )

    if not record:

        await query.message.reply_text(
            "🎂 **No Birthday Saved**\n\n"
            "You do not currently have a birthday "
            "saved for this chat.",
            parse_mode="Markdown",
        )

        return

    await query.message.reply_text(
        "🎂 **Your Birthday**\n\n"
        f"📅 **{record['birthday']}**\n\n"
        "Your birthday is saved in the "
        "Melanated AZ database. 💜",
        parse_mode="Markdown",
    )


# ==========================================================
# BIRTHDAY — REMOVE
# ==========================================================

async def admin_birthday_remove(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    chat_id = query.message.chat_id

    from raffle_database import remove_birthday

    removed = remove_birthday(
        user_id=user.id,
        chat_id=chat_id,
    )

    if removed:

        await query.message.reply_text(
            "🗑️ **Birthday Removed**\n\n"
            "Your birthday has been removed from "
            "the Melanated AZ database.",
            parse_mode="Markdown",
        )

    else:

        await query.message.reply_text(
            "ℹ️ You do not currently have a birthday saved."
        )


# ==========================================================
# ALL BIRTHDAYS
# ==========================================================

async def admin_all_birthdays(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    birthdays = get_all_birthdays()

    if not birthdays:

        await query.message.reply_text(
            "📋 **Birthday Database**\n\n"
            "No birthdays have been saved yet.",
            parse_mode="Markdown",
        )

        return

    lines = [
        "📋 **Melanated AZ Birthday Database**\n"
    ]

    for birthday in birthdays:

        display_name = (
            birthday.get("display_name")
            or "Unknown Member"
        )

        birthday_value = birthday.get(
            "birthday",
            "Unknown",
        )

        username = birthday.get(
            "username"
        )

        if username:

            member = (
                f"{display_name} "
                f"(@{username})"
            )

        else:

            member = display_name

        lines.append(
            f"🎂 **{birthday_value}** — {member}"
        )

    text = "\n".join(lines)

    await query.message.reply_text(
        text,
        parse_mode="Markdown",
    )


# ==========================================================
# ADMIN BUTTON ROUTER
# ==========================================================

async def admin_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):

        await query.answer(
            "⛔ You are not authorized to use "
            "the admin panel.",
            show_alert=True,
        )

        return

    data = query.data or ""

    logger.info(
        "Admin button pressed: %s by %s",
        data,
        user.id,
    )

    # ======================================================
    # MAIN MENU
    # ======================================================

    if data == "admin_back":

        await admin_back(
            update,
            context,
        )

        return

    if data == "admin_refresh":

        await admin_refresh(
            update,
            context,
        )

        return

    # ======================================================
    # RAFFLE OPTIONS
    # ======================================================

    if data == "admin_start_raffle":

        await admin_start_raffle(
            update,
            context,
        )

        return

    if data == "admin_active_raffle":

        await admin_active_raffle(
            update,
            context,
        )

        return

    if data == "admin_status":

        await admin_status(
            update,
            context,
        )

        return

    if data == "admin_entries":

        await admin_entries(
            update,
            context,
        )

        return

    if data == "admin_pending":

        await admin_pending(
            update,
            context,
        )

        return

    if data == "admin_completed":

        await admin_completed(
            update,
            context,
        )

        return

    if data == "admin_draw":

        await admin_draw(
            update,
            context,
        )

        return

    if data == "admin_cancel":

        await admin_cancel(
            update,
            context,
        )

        return

    if data == "admin_confirm_cancel":

        await admin_confirm_cancel(
            update,
            context,
        )

        return

    # ======================================================
    # BIRTHDAY OPTIONS
    # ======================================================

    if data == "admin_birthday_enter":

        await admin_birthday_enter(
            update,
            context,
        )

        return

    if data == "admin_birthday_view":

        await admin_birthday_view(
            update,
            context,
        )

        return

    if data == "admin_birthday_remove":

        await admin_birthday_remove(
            update,
            context,
        )

        return

    if data == "admin_all_birthdays":

        await admin_all_birthdays(
            update,
            context,
        )

        return

    # ======================================================
    # UNKNOWN
    # ======================================================

    logger.warning(
        "Unknown admin callback: %s",
        data,
    )

    await query.answer(
        "⚠️ This admin option is unavailable.",
        show_alert=True,
    )
