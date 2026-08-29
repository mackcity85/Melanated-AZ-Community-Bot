# ==========================================================
# Melanated AZ Bot
# admin.py
#
# COMPLETE ADMIN PANEL
#
# Includes:
#   - Raffle management
#   - Birthday management
#   - Truth or Dare
#   - Games category
#   - Persistent birthday storage
#
# IMPORTANT:
#   Games are managed through games/games.py.
#   Individual games should NOT be imported here.
#
#   Truth or Dare is imported lazily to prevent circular
#   imports.
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
    save_birthday,
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
# ==========================================================

def admin_main_keyboard():

    return InlineKeyboardMarkup(
        [
            # ------------------------------------------------
            # RAFFLE
            # ------------------------------------------------
            [
                InlineKeyboardButton(
                    "🎟️ Start Raffle",
                    callback_data="admin_start_raffle",
                ),
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_status",
                ),
            ],

            [
                InlineKeyboardButton(
                    "👥 Raffle Entries",
                    callback_data="admin_entries",
                ),
                InlineKeyboardButton(
                    "⏳ Pending Payments",
                    callback_data="admin_pending",
                ),
            ],

            [
                InlineKeyboardButton(
                    "✅ Completed Payments",
                    callback_data="admin_completed",
                ),
                InlineKeyboardButton(
                    "🏆 Draw Winner",
                    callback_data="admin_draw",
                ),
            ],

            [
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
                    "🎂 Add Birthday",
                    callback_data="admin_birthday_add",
                ),
                InlineKeyboardButton(
                    "📅 View Birthdays",
                    callback_data="admin_birthdays",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🗑️ Remove Birthday",
                    callback_data="admin_birthday_remove",
                ),
            ],

            # ------------------------------------------------
            # TRUTH OR DARE
            # ------------------------------------------------
            [
                InlineKeyboardButton(
                    "🔥 Truth or Dare",
                    callback_data="admin_truthdare",
                ),
            ],

            # ------------------------------------------------
            # GAMES
            # ------------------------------------------------
            [
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="admin_games",
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
# ADMIN MENU TEXT
# ==========================================================

def admin_menu_text():

    return (
        "👑 **Melanated AZ Admin Panel**\n\n"
        "Select an option below.\n\n"

        "🎟️ **RAFFLE**\n"
        "Start, review, monitor, and draw raffles.\n\n"

        "🎂 **BIRTHDAYS**\n"
        "Add, view, and remove member birthdays.\n\n"

        "🔥 **TRUTH OR DARE**\n"
        "Manage the community Truth or Dare game.\n\n"

        "🎮 **GAMES**\n"
        "Open the community games category."
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

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

        await query.edit_message_text(
            text=admin_menu_text(),
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown",
        )

        return

    if update.effective_message:

        await update.effective_message.reply_text(
            text=admin_menu_text(),
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown",
        )


# ==========================================================
# RAFFLE WRAPPER
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
            "Error running admin action: %s",
            action_name,
        )

        query = update.callback_query

        if query and query.message:

            try:

                await query.message.reply_text(
                    "⚠️ An error occurred while "
                    f"processing **{action_name}**.\n\n"
                    "Please try again.",
                    parse_mode="Markdown",
                )

            except Exception:
                pass


# ==========================================================
# RAFFLE ACTIONS
# ==========================================================

async def admin_start_raffle(
    update,
    context,
):

    query = update.callback_query

    if query:

        await query.answer(
            "Starting raffle setup..."
        )

    await run_raffle_handler(
        start_raffle,
        update,
        context,
        "Start Raffle",
    )


async def admin_status(
    update,
    context,
):

    query = update.callback_query

    if query:

        await query.answer()

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Raffle Status",
    )


async def admin_entries(
    update,
    context,
):

    query = update.callback_query

    if query:

        await query.answer()

    await run_raffle_handler(
        raffle_entries,
        update,
        context,
        "Raffle Entries",
    )


async def admin_pending(
    update,
    context,
):

    query = update.callback_query

    if query:

        await query.answer()

    await run_raffle_handler(
        pending_entries,
        update,
        context,
        "Pending Payments",
    )


async def admin_completed(
    update,
    context,
):

    query = update.callback_query

    if query:

        await query.answer()

    await run_raffle_handler(
        paid_entry,
        update,
        context,
        "Completed Payments",
    )


async def admin_draw(
    update,
    context,
):

    query = update.callback_query

    if query:

        await query.answer()

    await run_raffle_handler(
        draw_raffle,
        update,
        context,
        "Draw Winner",
    )


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def admin_cancel(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⚠️ YES — CANCEL RAFFLE",
                    callback_data="admin_confirm_cancel",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ BACK",
                    callback_data="admin_back",
                )
            ],
        ]
    )

    await query.edit_message_text(
        "⚠️ **Cancel Active Raffle?**\n\n"
        "This will cancel the currently active raffle.\n\n"
        "Are you sure?",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def admin_confirm_cancel(
    update,
    context,
):

    query = update.callback_query

    if query:

        await query.answer(
            "Cancelling raffle..."
        )

    await run_raffle_handler(
        cancel_raffle,
        update,
        context,
        "Cancel Raffle",
    )


# ==========================================================
# BIRTHDAY NORMALIZER
# ==========================================================

def normalize_admin_birthday(value):

    if not value:
        return None

    value = value.strip().replace("-", "/")

    parts = value.split("/")

    if len(parts) != 2:
        return None

    try:

        month = int(parts[0])
        day = int(parts[1])

    except (TypeError, ValueError):

        return None

    if month < 1 or month > 12:
        return None

    if day < 1 or day > 31:
        return None

    return f"{month:02d}/{day:02d}"


# ==========================================================
# ADD BIRTHDAY
# ==========================================================

async def admin_birthday_add(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):

        await query.answer(
            "⛔ You are not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    context.user_data[
        "admin_birthday_chat_id"
    ] = query.message.chat_id

    context.user_data[
        "awaiting_admin_birthday"
    ] = True

    await query.message.reply_text(
        "🎂 **Add Member Birthday**\n\n"
        "Send the member's Telegram User ID "
        "followed by their birthday.\n\n"
        "**Format:**\n"
        "`USER_ID MM/DD`\n\n"
        "**Example:**\n"
        "`123456789 08/27`\n\n"
        "Send the information in your next message.\n\n"
        "Press Back in the admin panel if you "
        "want to cancel.",
        parse_mode="Markdown",
    )


# ==========================================================
# ADMIN BIRTHDAY TEXT HANDLER
# ==========================================================

async def admin_birthday_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return False

    if not context.user_data.get(
        "awaiting_admin_birthday"
    ):
        return False

    if not is_admin(user.id):

        context.user_data.pop(
            "awaiting_admin_birthday",
            None,
        )

        context.user_data.pop(
            "admin_birthday_chat_id",
            None,
        )

        await message.reply_text(
            "⛔ You are not authorized."
        )

        return True

    birthday_chat_id = context.user_data.get(
        "admin_birthday_chat_id"
    )

    if birthday_chat_id is None:

        context.user_data.pop(
            "awaiting_admin_birthday",
            None,
        )

        await message.reply_text(
            "⚠️ I lost track of the chat.\n\n"
            "Open `/admin` again and select "
            "🎂 Add Birthday."
        )

        return True

    text = (message.text or "").strip()

    parts = text.split()

    if len(parts) != 2:

        await message.reply_text(
            "⚠️ **Invalid format.**\n\n"
            "Use:\n"
            "`USER_ID MM/DD`\n\n"
            "Example:\n"
            "`123456789 08/27`",
            parse_mode="Markdown",
        )

        return True

    try:

        member_user_id = int(parts[0])

    except (TypeError, ValueError):

        await message.reply_text(
            "⚠️ Invalid Telegram User ID.\n\n"
            "The User ID must be a number."
        )

        return True

    if member_user_id <= 0:

        await message.reply_text(
            "⚠️ The Telegram User ID must be positive."
        )

        return True

    birthday_value = normalize_admin_birthday(
        parts[1]
    )

    if not birthday_value:

        await message.reply_text(
            "🎂 Invalid birthday.\n\n"
            "Use MM/DD.\n\n"
            "Example: `08/27`",
            parse_mode="Markdown",
        )

        return True

    try:

        success = save_birthday(
            user_id=member_user_id,
            chat_id=birthday_chat_id,
            birthday=birthday_value,
        )

    except Exception:

        logger.exception(
            "Failed to save birthday."
        )

        await message.reply_text(
            "❌ I couldn't save that birthday.\n\n"
            "Please check the Render logs."
        )

        return True

    if not success:

        await message.reply_text(
            "❌ The birthday could not be saved.\n\n"
            "Please try again."
        )

        return True

    context.user_data.pop(
        "awaiting_admin_birthday",
        None,
    )

    context.user_data.pop(
        "admin_birthday_chat_id",
        None,
    )

    await message.reply_text(
        "✅ **Birthday Saved!**\n\n"
        f"👤 Telegram User ID: `{member_user_id}`\n"
        f"🎂 Birthday: **{birthday_value}**",
        parse_mode="Markdown",
    )

    logger.info(
        "Admin added birthday | admin=%s | "
        "member=%s | birthday=%s | chat=%s",
        user.id,
        member_user_id,
        birthday_value,
        birthday_chat_id,
    )

    return True


# ==========================================================
# VIEW BIRTHDAYS
# ==========================================================

async def admin_birthdays(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    birthdays = get_all_birthdays()

    if not birthdays:

        await query.edit_message_text(
            "📅 **Saved Birthdays**\n\n"
            "No birthdays are currently saved.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin_back",
                        )
                    ]
                ]
            ),
            parse_mode="Markdown",
        )

        return

    lines = [
        "📅 **Saved Birthdays**",
        "",
        f"Total: **{len(birthdays)}**",
        "",
    ]

    for birthday in birthdays:

        display_name = (
            birthday.get("display_name")
            or birthday.get("username")
            or str(birthday.get("user_id"))
        )

        birthday_value = (
            birthday.get("birthday")
            or "Unknown"
        )

        lines.append(
            f"🎂 {display_name} — **{birthday_value}**"
        )

    await query.edit_message_text(
        text="\n".join(lines),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🗑️ Remove Birthday",
                        callback_data="admin_birthday_remove",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_back",
                    )
                ],
            ]
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# REMOVE BIRTHDAY LIST
# ==========================================================

def birthday_list_keyboard():

    birthdays = get_all_birthdays()

    buttons = []

    for birthday in birthdays:

        birthday_id = birthday.get("id")

        display_name = (
            birthday.get("display_name")
            or birthday.get("username")
            or str(birthday.get("user_id"))
        )

        birthday_value = (
            birthday.get("birthday")
            or "Unknown"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"🎂 {display_name} — {birthday_value}",
                    callback_data=(
                        f"admin_bday_remove_{birthday_id}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_back",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


# ==========================================================
# REMOVE BIRTHDAY
# ==========================================================

async def admin_birthday_remove(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    birthdays = get_all_birthdays()

    if not birthdays:

        await query.edit_message_text(
            "🗑️ **Remove Birthday**\n\n"
            "There are no saved birthdays to remove.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin_back",
                        )
                    ]
                ]
            ),
            parse_mode="Markdown",
        )

        return

    await query.edit_message_text(
        "🗑️ **Remove Birthday**\n\n"
        "Select the birthday to remove:",
        reply_markup=birthday_list_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# REMOVE ONE BIRTHDAY
# ==========================================================

async def admin_remove_birthday(
    update,
    context,
    birthday_id,
):

    query = update.callback_query

    try:

        birthday_id = int(birthday_id)

    except (TypeError, ValueError):

        await query.answer(
            "Invalid birthday.",
            show_alert=True,
        )

        return

    removed = remove_birthday_by_id(
        birthday_id
    )

    if removed:

        await query.answer(
            "Birthday removed."
        )

        await admin_birthday_remove(
            update,
            context,
        )

    else:

        await query.answer(
            "Birthday was not found.",
            show_alert=True,
        )


# ==========================================================
# GAMES CATEGORY
#
# IMPORTANT:
# We import games lazily here.
#
# This keeps admin.py independent from the individual
# games and prevents circular imports.
# ==========================================================

async def admin_games(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user or not is_admin(user.id):

        await query.answer(
            "⛔ You are not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    try:

        from games.games import (
            games_admin_menu,
        )

        await games_admin_menu(
            update,
            context,
        )

    except ImportError:

        logger.exception(
            "Could not import games.games"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_back",
                    )
                ]
            ]
        )

        await query.edit_message_text(
            "⚠️ **Games system not found.**\n\n"
            "Make sure the following file exists:\n\n"
            "`games/games.py`\n\n"
            "Then redeploy the bot.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Error opening Games admin menu."
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_back",
                    )
                ]
            ]
        )

        await query.edit_message_text(
            "⚠️ **Unable to open Games.**\n\n"
            "Check the Render logs for the exact error.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


# ==========================================================
# REFRESH
# ==========================================================

async def admin_refresh(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer(
        "Admin panel refreshed."
    )

    await query.edit_message_text(
        text=admin_menu_text(),
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

    query = update.callback_query

    if not query:
        return

    await query.answer()

    context.user_data.pop(
        "awaiting_admin_birthday",
        None,
    )

    context.user_data.pop(
        "admin_birthday_chat_id",
        None,
    )

    await query.edit_message_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
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
            "⛔ You are not authorized.",
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
    # NAVIGATION
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
    # GAMES
    # ======================================================

    if data == "admin_games":

        await admin_games(
            update,
            context,
        )

        return

    # ======================================================
    # TRUTH OR DARE
    #
    # Lazy imports prevent circular imports.
    # ======================================================

    if data == "admin_truthdare":

        from truth_dare import (
            truth_dare_admin_menu,
        )

        await truth_dare_admin_menu(
            update,
            context,
        )

        return

    if data == "admin_truthdare_toggle":

        from truth_dare import (
            toggle_truth_dare,
        )

        await toggle_truth_dare(
            update,
            context,
        )

        return

    if data == "admin_truthdare_help":

        from truth_dare import (
            truth_dare_help,
        )

        await truth_dare_help(
            update,
            context,
        )

        return

    # ======================================================
    # RAFFLE
    # ======================================================

    if data == "admin_start_raffle":

        await admin_start_raffle(
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
    # BIRTHDAYS
    # ======================================================

    if data == "admin_birthday_add":

        await admin_birthday_add(
            update,
            context,
        )

        return

    if data == "admin_birthdays":

        await admin_birthdays(
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

    if data.startswith("admin_bday_remove_"):

        birthday_id = data[
            len("admin_bday_remove_"):
        ]

        await admin_remove_birthday(
            update,
            context,
            birthday_id,
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
        "⚠️ This option is unavailable.",
        show_alert=True,
    )


# ==========================================================
# END admin.py
# ==========================================================
