# ==========================================================
# Melanated AZ Bot
# admin.py
#
# COMPLETE ADMIN PANEL
#
# Includes:
#   - Raffle management
#   - Manual raffle entries
#   - Birthday management
#   - Scrollable member selector for birthdays
#   - Truth or Dare
#   - Games
#
# Games are routed to the existing games package.
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
    manual_raffle_entry,
)

from raffle_database import (
    get_all_birthdays,
    remove_birthday_by_id,
    save_birthday,
    get_members,
    get_member,
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
                    "➕ Manual Entry",
                    callback_data="admin_manual_entry",
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
            [
                InlineKeyboardButton(
                    "🔥 Truth or Dare",
                    callback_data="admin_truthdare",
                ),
                InlineKeyboardButton(
                    "🎮 Games",
                    callback_data="admin_games",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_refresh",
                ),
            ],
        ]
    )


# ==========================================================
# MENU TEXT
# ==========================================================

def admin_menu_text():

    return (
        "👑 **Melanated AZ Admin Panel**\n\n"
        "Select an option below.\n\n"

        "🎟️ **RAFFLE**\n"
        "Start, review, monitor, manually add, "
        "and draw raffles.\n\n"

        "🎂 **BIRTHDAYS**\n"
        "Add, view, and remove member birthdays.\n\n"

        "🔥 **TRUTH OR DARE**\n"
        "Manage the community Truth or Dare game.\n\n"

        "🎮 **GAMES**\n"
        "Access the Melanated AZ Games Center."
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
                    "Please check the Render logs.",
                    parse_mode="Markdown",
                )

            except Exception:
                pass


# ==========================================================
# RAFFLE ACTIONS
# ==========================================================

async def admin_start_raffle(update, context):

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


async def admin_status(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Raffle Status",
    )


async def admin_entries(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        raffle_entries,
        update,
        context,
        "Raffle Entries",
    )


async def admin_pending(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        pending_entries,
        update,
        context,
        "Pending Payments",
    )


async def admin_completed(update, context):

    query = update.callback_query

    if query:
        await query.answer()

    await run_raffle_handler(
        paid_entry,
        update,
        context,
        "Completed Payments",
    )


async def admin_draw(update, context):

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
# MANUAL RAFFLE ENTRY
# ==========================================================

async def admin_manual_entry(update, context):

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
        "awaiting_manual_raffle_user_id"
    ] = True

    context.user_data.pop(
        "manual_raffle_user_id",
        None,
    )

    await query.edit_message_text(
        "➕ **Manual Raffle Entry**\n\n"
        "Enter the member's **Telegram User ID**.\n\n"
        "Example:\n"
        "`123456789`\n\n"
        "The member will be added directly to the "
        "currently active raffle as an **APPROVED** entry.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Cancel",
                        callback_data="admin_back",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# MANUAL RAFFLE ENTRY TEXT HANDLER
# ==========================================================

async def admin_manual_entry_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return False

    if not context.user_data.get(
        "awaiting_manual_raffle_user_id"
    ):
        return False

    if not is_admin(user.id):

        context.user_data.pop(
            "awaiting_manual_raffle_user_id",
            None,
        )

        await message.reply_text(
            "⛔ You are not authorized."
        )

        return True

    text = (message.text or "").strip()

    try:

        member_user_id = int(text)

    except (TypeError, ValueError):

        await message.reply_text(
            "⚠️ Invalid Telegram User ID.\n\n"
            "Please enter numbers only.\n\n"
            "Example:\n"
            "`123456789`",
            parse_mode="Markdown",
        )

        return True

    if member_user_id <= 0:

        await message.reply_text(
            "⚠️ Invalid Telegram User ID."
        )

        return True

    context.user_data.pop(
        "awaiting_manual_raffle_user_id",
        None,
    )

    try:

        success = await manual_raffle_entry(
            update,
            context,
            member_user_id,
        )

    except Exception:

        logger.exception(
            "Manual raffle entry failed."
        )

        await message.reply_text(
            "❌ Manual raffle entry failed.\n\n"
            "Please check the Render logs."
        )

        return True

    return True


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def admin_cancel(update, context):

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


async def admin_confirm_cancel(update, context):

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
# BIRTHDAY MEMBER DISPLAY
# ==========================================================

def member_display_name(member):

    return (
        member.get("display_name")
        or (
            f"@{member.get('username')}"
            if member.get("username")
            else None
        )
        or str(member.get("user_id"))
    )


# ==========================================================
# BUILD SCROLLABLE MEMBER KEYBOARD
# ==========================================================

def birthday_member_keyboard(
    members,
    page,
    page_size=8,
):

    if not members:

        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_back",
                    )
                ]
            ]
        )

    total = len(members)

    max_page = max(
        0,
        (total - 1) // page_size,
    )

    page = max(
        0,
        min(page, max_page),
    )

    start = page * page_size
    end = start + page_size

    current_members = members[start:end]

    buttons = []

    for member in current_members:

        user_id = member.get("user_id")

        name = member_display_name(member)

        buttons.append(
            [
                InlineKeyboardButton(
                    f"👤 {name}",
                    callback_data=(
                        f"admin_bday_select_{user_id}"
                    ),
                )
            ]
        )

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                "⬅️ Previous",
                callback_data=(
                    f"admin_bday_page_{page - 1}"
                ),
            )
        )

    if page < max_page:

        navigation.append(
            InlineKeyboardButton(
                "Next ➡️",
                callback_data=(
                    f"admin_bday_page_{page + 1}"
                ),
            )
        )

    if navigation:
        buttons.append(navigation)

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
# SHOW MEMBER SELECTOR
# ==========================================================

async def show_birthday_member_selector(
    update,
    context,
    page=0,
):

    query = update.callback_query

    if not query:
        return

    chat_id = query.message.chat_id

    members = get_members(
        chat_id=chat_id,
        limit=1000,
    )

    context.user_data[
        "admin_birthday_members"
    ] = members

    context.user_data[
        "admin_birthday_page"
    ] = page

    if not members:

        await query.edit_message_text(
            "🎂 **Add Member Birthday**\n\n"
            "I don't have any known members for this "
            "chat yet.\n\n"
            "Once members interact with the bot, "
            "they will appear here.\n\n"
            "You can also use the manual method by "
            "sending the member's User ID and birthday.",
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

    total = len(members)

    page_size = 8

    max_page = max(
        1,
        (total + page_size - 1) // page_size,
    )

    current_page = page + 1

    await query.edit_message_text(
        "🎂 **Add Member Birthday**\n\n"
        "Select a member below.\n\n"
        f"Showing page **{current_page}** of "
        f"**{max_page}**\n\n"
        "Use **Previous** and **Next** to scroll.",
        reply_markup=birthday_member_keyboard(
            members,
            page,
            page_size,
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# ADD BIRTHDAY
# ==========================================================

async def admin_birthday_add(update, context):

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
    ] = False

    context.user_data.pop(
        "admin_birthday_selected_user_id",
        None,
    )

    await show_birthday_member_selector(
        update,
        context,
        page=0,
    )


# ==========================================================
# SELECT BIRTHDAY MEMBER
# ==========================================================

async def admin_birthday_select(
    update,
    context,
    member_user_id,
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

    try:
        member_user_id = int(member_user_id)

    except (TypeError, ValueError):

        await query.answer(
            "Invalid member.",
            show_alert=True,
        )

        return

    chat_id = context.user_data.get(
        "admin_birthday_chat_id"
    )

    if chat_id is None:
        chat_id = query.message.chat_id

    member = get_member(
        member_user_id,
        chat_id,
    )

    if not member:

        members = context.user_data.get(
            "admin_birthday_members",
            [],
        )

        for item in members:

            try:
                item_id = int(item.get("user_id", 0))
            except Exception:
                continue

            if item_id == member_user_id:

                member = item
                break

    if not member:

        await query.answer(
            "Member could not be found.",
            show_alert=True,
        )

        return

    name = member_display_name(member)

    context.user_data[
        "admin_birthday_selected_user_id"
    ] = member_user_id

    context.user_data[
        "admin_birthday_selected_name"
    ] = name

    context.user_data[
        "admin_birthday_chat_id"
    ] = chat_id

    context.user_data[
        "awaiting_admin_birthday"
    ] = True

    await query.answer(
        "Member selected."
    )

    await query.edit_message_text(
        "🎂 **Birthday for Selected Member**\n\n"
        f"👤 Member: **{name}**\n"
        f"🆔 User ID: `{member_user_id}`\n\n"
        "Now send the birthday in:\n\n"
        "`MM/DD`\n\n"
        "Example:\n"
        "`08/27`",
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

        context.user_data.pop(
            "admin_birthday_selected_user_id",
            None,
        )

        await message.reply_text(
            "⛔ You are not authorized."
        )

        return True

    birthday_chat_id = context.user_data.get(
        "admin_birthday_chat_id"
    )

    selected_user_id = context.user_data.get(
        "admin_birthday_selected_user_id"
    )

    selected_name = context.user_data.get(
        "admin_birthday_selected_name"
    )

    if birthday_chat_id is None or selected_user_id is None:

        context.user_data.pop(
            "awaiting_admin_birthday",
            None,
        )

        await message.reply_text(
            "⚠️ I lost track of the selected member.\n\n"
            "Open `/admin` again and select "
            "🎂 Add Birthday."
        )

        return True

    text = (message.text or "").strip()

    birthday_value = normalize_admin_birthday(
        text
    )

    if not birthday_value:

        await message.reply_text(
            "🎂 **Invalid birthday.**\n\n"
            "Enter only the birthday using MM/DD.\n\n"
            "Example:\n"
            "`08/27`",
            parse_mode="Markdown",
        )

        return True

    member = get_member(
        selected_user_id,
        birthday_chat_id,
    )

    username = None
    display_name = selected_name

    if member:

        username = member.get("username")

        display_name = (
            member.get("display_name")
            or display_name
        )

    try:

        success = save_birthday(
            user_id=selected_user_id,
            chat_id=birthday_chat_id,
            birthday=birthday_value,
            username=username,
            display_name=display_name,
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

    context.user_data.pop(
        "admin_birthday_selected_user_id",
        None,
    )

    context.user_data.pop(
        "admin_birthday_selected_name",
        None,
    )

    context.user_data.pop(
        "admin_birthday_members",
        None,
    )

    context.user_data.pop(
        "admin_birthday_page",
        None,
    )

    await message.reply_text(
        "✅ **Birthday Saved!**\n\n"
        f"👤 Member: **{display_name}**\n"
        f"🆔 Telegram User ID: `{selected_user_id}`\n"
        f"🎂 Birthday: **{birthday_value}**",
        parse_mode="Markdown",
    )

    logger.info(
        "Admin added birthday | admin=%s | "
        "member=%s | birthday=%s | chat=%s",
        user.id,
        selected_user_id,
        birthday_value,
        birthday_chat_id,
    )

    return True


# ==========================================================
# VIEW BIRTHDAYS
# ==========================================================

async def admin_birthdays(update, context):

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
            or (
                f"@{birthday.get('username')}"
                if birthday.get("username")
                else None
            )
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
            or (
                f"@{birthday.get('username')}"
                if birthday.get("username")
                else None
            )
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

async def admin_birthday_remove(update, context):

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
# GAMES
# ==========================================================

async def admin_games(update, context):

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

    try:
        await query.answer()
    except Exception:
        pass

    try:

        from games import (
            games_admin_menu,
        )

    except Exception:

        logger.exception(
            "Unable to import games package."
        )

        await query.edit_message_text(
            "❌ **Games could not be loaded.**\n\n"
            "The Games package could not be imported.\n\n"
            "Please check that the Games package has "
            "no import errors.",
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

    try:

        await games_admin_menu(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Error opening Games admin menu"
        )

        await query.edit_message_text(
            "⚠️ **Games Error**\n\n"
            "The Games menu exists, but an error occurred "
            "while opening it.\n\n"
            "Please check the Render logs.",
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


# ==========================================================
# TRUTH OR DARE
# ==========================================================

async def admin_truthdare(update, context):

    from truth_dare import truth_dare_admin_menu

    await truth_dare_admin_menu(
        update,
        context,
    )


async def admin_truthdare_toggle(update, context):

    from truth_dare import toggle_truth_dare

    await toggle_truth_dare(
        update,
        context,
    )


async def admin_truthdare_help(update, context):

    from truth_dare import truth_dare_help

    await truth_dare_help(
        update,
        context,
    )


# ==========================================================
# REFRESH
# ==========================================================

async def admin_refresh(update, context):

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

async def admin_back(update, context):

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

    context.user_data.pop(
        "admin_birthday_selected_user_id",
        None,
    )

    context.user_data.pop(
        "admin_birthday_selected_name",
        None,
    )

    context.user_data.pop(
        "admin_birthday_members",
        None,
    )

    context.user_data.pop(
        "admin_birthday_page",
        None,
    )

    context.user_data.pop(
        "awaiting_manual_raffle_user_id",
        None,
    )

    context.user_data.pop(
        "manual_raffle_user_id",
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

    # ------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # MANUAL RAFFLE ENTRY
    # ------------------------------------------------------

    if data == "admin_manual_entry":

        await admin_manual_entry(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # GAMES
    # ------------------------------------------------------

    if data == "admin_games":

        await admin_games(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # TRUTH OR DARE
    # ------------------------------------------------------

    if data == "admin_truthdare":

        await admin_truthdare(
            update,
            context,
        )

        return

    if data == "admin_truthdare_toggle":

        await admin_truthdare_toggle(
            update,
            context,
        )

        return

    if data == "admin_truthdare_help":

        await admin_truthdare_help(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # RAFFLE
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # BIRTHDAYS
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # BIRTHDAY MEMBER PAGES
    # ------------------------------------------------------

    if data.startswith("admin_bday_page_"):

        page_text = data[
            len("admin_bday_page_"):
        ]

        try:
            page = int(page_text)
        except (TypeError, ValueError):

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        await query.answer()

        members = context.user_data.get(
            "admin_birthday_members"
        )

        if not members:

            await show_birthday_member_selector(
                update,
                context,
                page=page,
            )

            return

        context.user_data[
            "admin_birthday_page"
        ] = page

        page_size = 8

        total = len(members)

        max_page = max(
            1,
            (total + page_size - 1) // page_size,
        )

        await query.edit_message_text(
            "🎂 **Add Member Birthday**\n\n"
            "Select a member below.\n\n"
            f"Showing page **{page + 1}** of "
            f"**{max_page}**\n\n"
            "Use **Previous** and **Next** to scroll.",
            reply_markup=birthday_member_keyboard(
                members,
                page,
                page_size,
            ),
            parse_mode="Markdown",
        )

        return

    # ------------------------------------------------------
    # SELECT MEMBER
    # ------------------------------------------------------

    if data.startswith("admin_bday_select_"):

        member_user_id = data[
            len("admin_bday_select_"):
        ]

        await admin_birthday_select(
            update,
            context,
            member_user_id,
        )

        return

    # ------------------------------------------------------
    # REMOVE ONE BIRTHDAY
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # UNKNOWN
    # ------------------------------------------------------

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
