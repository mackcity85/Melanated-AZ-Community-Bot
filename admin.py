# ==========================================================
# Melanated AZ Bot
# admin.py
#
# COMPLETE ADMIN PANEL
#
# ADMIN AUTHORIZATION:
#   - ADMIN_GROUP_ID membership grants admin-panel access
#   - Accepted statuses:
#       member
#       administrator
#       creator
#   - ADMIN_IDS remains an emergency/configured fallback
#   - MAIN_GROUP_ID is NOT required for admin-panel access
#
# Includes:
#   - Raffle management
#   - Repost active raffle
#   - Manual raffle entry
#   - Birthday management
#   - Scrollable member selector for birthdays
#   - Scrollable member selector for manual raffle entries
#   - Truth or Dare
#   - Games
#   - Dirty Minds multiplayer
#   - Holiday Exchange
# ==========================================================

import html
import logging
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.error import BadRequest, TelegramError
from telegram.ext import ApplicationHandlerStop, ContextTypes

from config import ADMIN_IDS, MAIN_GROUP_ID, RAFFLE_CHAT_ID

from member_bank import (
    admin_members, admin_member_view, _community_rows,
    _member_message_prompt, _member_message_cancel,
    _member_remove_prompt, _member_remove_cancel, _member_remove_confirm,
)

from raffle import (
    start_raffle,
    raffle_status,
    raffle_entries,
    pending_entries,
    paid_entry,
    cancel_raffle,
    draw_raffle,
    manual_raffle_entry,
    repost_raffle,
    admin_edit_raffle_end_date,
)

from holiday_exchange import holiday_exchange_admin_callback

from raffle_database import (
    get_all_birthdays,
    remove_birthday_by_id,
    save_birthday,
    get_members,
    get_member,
    get_active_raffle,
    get_pending_entries,
    get_entry,
    create_queued_raffle,
    get_queued_raffles,
    cancel_queued_raffle,
)


logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN AUTHORIZATION
# ==========================================================

async def is_admin(user_id, context=None):
    """
    Check whether a Telegram user is authorized to use the
    Melanated AZ admin panel.

    PRIMARY AUTHORIZATION:
        Current membership in ADMIN_GROUP_ID.

    Accepted ADMIN_GROUP_ID statuses:
        - member
        - administrator
        - creator

    FALLBACK:
        ADMIN_IDS remains an emergency/configured fallback.

    IMPORTANT:
        MAIN_GROUP_ID is intentionally NOT checked here.

    This performs a LIVE Telegram membership check.
    """

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return False

    # ------------------------------------------------------
    # ADMIN_IDS FALLBACK
    # ------------------------------------------------------

    try:
        configured_admin_ids = {
            int(admin_id)
            for admin_id in (ADMIN_IDS or [])
        }

        if user_id in configured_admin_ids:
            logger.info(
                "Admin authorization granted via ADMIN_IDS | "
                "user_id=%s",
                user_id,
            )
            return True

    except Exception:
        logger.exception(
            "Unable to process ADMIN_IDS."
        )

    # ------------------------------------------------------
    # BOT CONTEXT REQUIRED FOR LIVE GROUP CHECK
    # ------------------------------------------------------

    if context is None:
        logger.warning(
            "Admin authorization failed: no bot context | "
            "user_id=%s",
            user_id,
        )
        return False

    # ------------------------------------------------------
    # ADMIN GROUP ID
    # ------------------------------------------------------

    try:
        admin_group_id = int(
            os.environ.get(
                "ADMIN_GROUP_ID",
                "0",
            ) or "0"
        )
    except (TypeError, ValueError):

        logger.error(
            "ADMIN_GROUP_ID is not a valid integer."
        )

        return False

    if not admin_group_id:

        logger.error(
            "ADMIN_GROUP_ID is not configured."
        )

        return False

    # ------------------------------------------------------
    # LIVE ADMIN GROUP MEMBERSHIP CHECK
    # ------------------------------------------------------

    try:

        member = await context.bot.get_chat_member(
            chat_id=admin_group_id,
            user_id=user_id,
        )

        status = getattr(
            member,
            "status",
            None,
        )

        if status in {
            "member",
            "administrator",
            "creator",
        }:

            logger.info(
                "Admin authorization granted via "
                "ADMIN_GROUP_ID | user_id=%s | "
                "status=%s | admin_group=%s",
                user_id,
                status,
                admin_group_id,
            )

            return True

        logger.info(
            "Admin authorization denied | "
            "user_id=%s | status=%s | "
            "admin_group=%s",
            user_id,
            status,
            admin_group_id,
        )

        return False

    except TelegramError as exc:

        logger.warning(
            "Could not verify ADMIN_GROUP_ID membership | "
            "user_id=%s | admin_group=%s | error=%s",
            user_id,
            admin_group_id,
            exc,
        )

        return False

    except Exception:

        logger.exception(
            "Unexpected ADMIN_GROUP_ID membership check "
            "error | user_id=%s | admin_group=%s",
            user_id,
            admin_group_id,
        )

        return False


# ==========================================================
# CONSISTENT ADMIN AUTHORIZATION GATE
# ==========================================================

async def require_admin(
    update,
    context,
    *,
    alert=True,
):
    """
    Central authorization helper.

    Every privileged admin handler should call this before
    performing its protected operation.
    """

    user = update.effective_user

    if not user:

        return False

    authorized = await is_admin(
        user.id,
        context,
    )

    if authorized:
        return True

    query = update.callback_query

    if query:

        try:

            await query.answer(
                "⛔ You are not authorized.",
                show_alert=alert,
            )

        except Exception:
            pass

    elif update.effective_message:

        try:

            await update.effective_message.reply_text(
                "⛔ You are not authorized to use "
                "the admin panel."
            )

        except Exception:
            pass

    logger.warning(
        "Unauthorized admin action blocked | "
        "user_id=%s | callback=%s",
        user.id,
        query.data if query else None,
    )

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
                    "📊 Post Raffle Status",
                    callback_data="admin_status",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎟️ Raffle Queue",
                    callback_data="admin_raffle_queue",
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
                    "💸 Payment Reminders",
                    callback_data="admin_payment_reminders",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➕ Manual Raffle Entry",
                    callback_data="admin_manual_entry",
                ),
                InlineKeyboardButton(
                    "📢 Repost Raffle Stats",
                    callback_data="admin_repost_raffle",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📅 Edit Raffle End Date",
                    callback_data="admin_edit_raffle_end_date",
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
                    "📢 Repost Birthdays",
                    callback_data="admin_repost_birthdays",
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
                    "🎭 Dirty Minds",
                    callback_data="admin_dirty_minds",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎁 Holiday Exchange",
                    callback_data="admin_holiday_exchange",
                ),
            ],
            [
                InlineKeyboardButton(
                    "💭 Questions / QOTD",
                    callback_data="admin_questions",
                ),
                InlineKeyboardButton(
                    "🌙 After Dark",
                    callback_data="admin_after_dark",
                ),
            ],
            [
                InlineKeyboardButton(
                    "👥 Members",
                    callback_data="admin_members",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📥 Pending Event Approvals",
                    callback_data="admin_pending_event_approvals",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📅 Approved Events",
                    callback_data="admin_approved_events",
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
        "Start, review, monitor, manually enter members, "
        "repost, and draw raffles.\n\n"

        "🎂 **BIRTHDAYS**\n"
        "Add, view, and remove member birthdays.\n\n"

        "🔥 **TRUTH OR DARE**\n"
        "Manage the community Truth or Dare game.\n\n"

        "🎮 **GAMES**\n"
        "Access the Melanated AZ Games Center.\n\n"

        "🎭 **DIRTY MINDS**\n"
        "Create and manage multiplayer Dirty Minds rooms.\n\n"

        "🎁 **HOLIDAY EXCHANGE**\n"
        "Manage the Holiday Exchange.\n\n"
        "💭 **QUESTIONS / QOTD**\n"
        "Manage the Question/Poll bank. Daily release: **11:00 AM Arizona time**.\n\n"
        "🌙 **AFTER DARK**\n"
        "Separate content bank. Daily release: **11:00 PM Arizona time**."
    )


# ==========================================================
# ADMIN MENU
# ==========================================================

async def admin_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await require_admin(
        update,
        context,
        alert=True,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

        try:

            await query.edit_message_text(
                text=admin_menu_text(),
                reply_markup=admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to display admin menu."
            )

        return

    if update.effective_message:

        try:

            await update.effective_message.reply_text(
                text=admin_menu_text(),
                reply_markup=admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Unable to send admin menu."
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
    """
    Protected wrapper for raffle actions.

    Authorization is checked AGAIN here so raffle handlers
    cannot accidentally become exposed if called elsewhere.
    """

    if not await require_admin(
        update,
        context,
        alert=True,
    ):
        return

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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer(
                "Starting raffle setup..."
            )
        except Exception:
            pass

    await run_raffle_handler(
        start_raffle,
        update,
        context,
        "Start Raffle",
    )


async def admin_status(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

    await run_raffle_handler(
        raffle_status,
        update,
        context,
        "Raffle Status",
    )


async def admin_entries(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

    await run_raffle_handler(
        raffle_entries,
        update,
        context,
        "Raffle Entries",
    )


async def admin_pending(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

    await run_raffle_handler(
        pending_entries,
        update,
        context,
        "Pending Payments",
    )


async def admin_completed(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

    await run_raffle_handler(
        paid_entry,
        update,
        context,
        "Completed Payments",
    )


async def admin_draw(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

    await run_raffle_handler(
        draw_raffle,
        update,
        context,
        "Draw Winner",
    )


# ==========================================================
# REPOST ACTIVE RAFFLE
# ==========================================================

async def admin_repost_raffle(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer(
                "🔄 Reposting active raffle..."
            )
        except Exception:
            pass

    try:

        await repost_raffle(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Failed to repost active raffle."
        )

        if query and query.message:

            try:

                await query.message.reply_text(
                    "❌ **Repost Failed**\n\n"
                    "The active raffle could not be reposted.\n\n"
                    "Please check the Render logs.",
                    parse_mode="Markdown",
                )

            except Exception:
                pass


# ==========================================================
# MANUAL RAFFLE ENTRY
# ==========================================================

async def admin_manual_entry(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    context.user_data.pop(
        "admin_manual_raffle_members",
        None,
    )

    context.user_data.pop(
        "admin_manual_raffle_page",
        None,
    )

    context.user_data.pop(
        "admin_manual_raffle_selected_user_id",
        None,
    )

    context.user_data.pop(
        "admin_manual_raffle_chat_id",
        None,
    )

    await show_manual_raffle_member_selector(
        update,
        context,
        page=0,
    )


# ==========================================================
# MANUAL RAFFLE MEMBER DISPLAY
# ==========================================================

def manual_member_display_name(member):

    return (
        member.get("display_name")
        or member.get("first_name")
        or (
            f"@{member.get('username')}"
            if member.get("username")
            else None
        )
        or str(member.get("user_id"))
    )


# ==========================================================
# MANUAL RAFFLE MEMBER KEYBOARD
# ==========================================================

def manual_raffle_member_keyboard(
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
        name = manual_member_display_name(member)

        buttons.append(
            [
                InlineKeyboardButton(
                    f"👤 {name}",
                    callback_data=(
                        f"admin_manual_select_{user_id}"
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
                    f"admin_manual_page_{page - 1}"
                ),
            )
        )

    if page < max_page:

        navigation.append(
            InlineKeyboardButton(
                "Next ➡️",
                callback_data=(
                    f"admin_manual_page_{page + 1}"
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
# SHOW MANUAL RAFFLE MEMBER SELECTOR
# ==========================================================

async def show_manual_raffle_member_selector(
    update,
    context,
    page=0,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query or not query.message:
        return

    # The admin panel is opened in the admin's private chat, but
    # member records are keyed by the community group chat ID.
    try:
        chat_id = int(MAIN_GROUP_ID)
    except (TypeError, ValueError):
        logger.error("MAIN_GROUP_ID is missing or invalid; cannot load birthday members.")
        await query.edit_message_text(
            "⚠️ The community group is not configured correctly. Please check MAIN_GROUP_ID.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
            ]),
        )
        return

    # Use the same community Member Bank source as the admin's Members
    # screen. The raffle DB's members table may be empty even when the
    # community database already knows these people.
    members_by_id = {}

    try:
        for row in _community_rows():
            item = dict(row)
            try:
                uid = int(item.get("user_id"))
            except (TypeError, ValueError):
                continue
            item["user_id"] = uid
            item["display_name"] = (
                item.get("display_name")
                or item.get("first_name")
                or (f"@{item['username']}" if item.get("username") else str(uid))
            )
            members_by_id[uid] = item
    except Exception:
        logger.exception("Unable to load community Member Bank for birthday selector.")

    # Also include people known only to the raffle database, without
    # duplicating members already present in the community Member Bank.
    try:
        for row in get_members(chat_id=chat_id, limit=1000):
            item = dict(row)
            try:
                uid = int(item.get("user_id"))
            except (TypeError, ValueError):
                continue
            item["user_id"] = uid
            item["display_name"] = (
                item.get("display_name")
                or (f"@{item['username']}" if item.get("username") else str(uid))
            )
            members_by_id.setdefault(uid, item)
    except Exception:
        logger.exception("Unable to load raffle DB members for birthday selector.")

    members = sorted(
        members_by_id.values(),
        key=lambda item: str(item.get("display_name") or item.get("user_id")).casefold(),
    )

    if not members:

        try:
            from config import RAFFLE_CHAT_ID

            members = get_members(
                chat_id=int(RAFFLE_CHAT_ID),
                limit=1000,
            )

            chat_id = int(RAFFLE_CHAT_ID)

        except Exception:

            members = []

    context.user_data[
        "admin_manual_raffle_members"
    ] = members

    context.user_data[
        "admin_manual_raffle_page"
    ] = page

    context.user_data[
        "admin_manual_raffle_chat_id"
    ] = chat_id

    if not members:

        await query.edit_message_text(
            "🎟️ **Manual Raffle Entry**\n\n"
            "I don't have any known members for the raffle "
            "group yet.\n\n"
            "Once members interact with the bot, they will "
            "appear here.",
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
        "🎟️ **Manual Raffle Entry**\n\n"
        "Select the group member you want to add.\n\n"
        f"Showing page **{current_page}** of "
        f"**{max_page}**\n\n"
        "Use **Previous** and **Next** to scroll.",
        reply_markup=manual_raffle_member_keyboard(
            members,
            page,
            page_size,
        ),
        parse_mode="Markdown",
    )


# ==========================================================
# SELECT MANUAL RAFFLE MEMBER
# ==========================================================

async def admin_manual_select(
    update,
    context,
    member_user_id,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        member_user_id = int(member_user_id)
    except (TypeError, ValueError):

        await query.answer(
            "Invalid member.",
            show_alert=True,
        )

        return

    members = context.user_data.get(
        "admin_manual_raffle_members",
        [],
    )

    member = None

    for item in members:

        try:

            if int(item.get("user_id", 0)) == member_user_id:

                member = item
                break

        except (TypeError, ValueError):
            continue

    if not member:

        chat_id = context.user_data.get(
            "admin_manual_raffle_chat_id"
        )

        if chat_id:

            member = get_member(
                member_user_id,
                chat_id,
            )

    if not member:

        await query.answer(
            "Member could not be found.",
            show_alert=True,
        )

        return

    name = manual_member_display_name(member)

    context.user_data[
        "admin_manual_raffle_selected_user_id"
    ] = member_user_id

    context.user_data[
        "admin_manual_raffle_selected_name"
    ] = name

    try:
        await query.answer(
            "Member selected."
        )
    except Exception:
        pass

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ ADD ENTRY",
                    callback_data=(
                        f"admin_manual_confirm_{member_user_id}"
                    ),
                ),
                InlineKeyboardButton(
                    "❌ CANCEL",
                    callback_data="admin_manual_cancel",
                ),
            ],
        ]
    )

    await query.edit_message_text(
        "🎟️ **Manual Raffle Entry**\n\n"
        f"👤 Member: **{name}**\n"
        f"🆔 User ID: `{member_user_id}`\n\n"
        "This will add the member directly to the active "
        "raffle as an **APPROVED** entry.\n\n"
        "Continue?",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# ==========================================================
# CONFIRM MANUAL RAFFLE ENTRY
# ==========================================================

async def admin_manual_confirm(
    update,
    context,
    member_user_id,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        member_user_id = int(member_user_id)
    except (TypeError, ValueError):

        await query.answer(
            "Invalid member.",
            show_alert=True,
        )

        return

    selected_id = context.user_data.get(
        "admin_manual_raffle_selected_user_id"
    )

    if selected_id is not None:

        try:

            if int(selected_id) != member_user_id:

                await query.answer(
                    "Member selection changed.",
                    show_alert=True,
                )

                return

        except (TypeError, ValueError):
            pass

    try:

        await query.answer(
            "Adding raffle entry..."
        )

    except Exception:
        pass

    try:

        result = await manual_raffle_entry(
            update,
            context,
            member_user_id,
        )

    except Exception:

        logger.exception(
            "Manual raffle entry failed."
        )

        try:

            await query.edit_message_text(
                "❌ **Manual Entry Failed**\n\n"
                "The entry could not be added.\n\n"
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

        except Exception:
            pass

        return

    if result:

        for key in [
            "admin_manual_raffle_members",
            "admin_manual_raffle_page",
            "admin_manual_raffle_selected_user_id",
            "admin_manual_raffle_selected_name",
            "admin_manual_raffle_chat_id",
        ]:

            context.user_data.pop(
                key,
                None,
            )


# ==========================================================
# CANCEL MANUAL ENTRY
# ==========================================================

async def admin_manual_cancel(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer(
            "Manual entry cancelled."
        )
    except Exception:
        pass

    for key in [
        "admin_manual_raffle_members",
        "admin_manual_raffle_page",
        "admin_manual_raffle_selected_user_id",
        "admin_manual_raffle_selected_name",
        "admin_manual_raffle_chat_id",
    ]:

        context.user_data.pop(
            key,
            None,
        )

    await query.edit_message_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# CANCEL RAFFLE
# ==========================================================

async def admin_cancel(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if query:

        try:
            await query.answer(
                "Cancelling raffle..."
            )
        except Exception:
            pass

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
        or member.get("first_name")
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
# SHOW BIRTHDAY MEMBER SELECTOR
# ==========================================================

async def show_birthday_member_selector(
    update,
    context,
    page=0,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query or not query.message:
        return

    # The selector is displayed in the admin's private chat, but
    # member records are keyed to the community group ID.
    try:
        chat_id = int(
            context.user_data.get("admin_birthday_chat_id")
            or MAIN_GROUP_ID
        )
    except (TypeError, ValueError):
        await query.edit_message_text(
            "⚠️ The community group is not configured correctly. "
            "Please check MAIN_GROUP_ID.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
            ]),
        )
        return

    # Prefer the community Member Bank as the source of known group
    # members. The raffle database may be empty even when the community
    # database already contains members. Merge raffle records as a fallback.
    members_by_id = {}

    try:
        for member in _community_rows():
            try:
                uid = int(member.get("user_id"))
            except (TypeError, ValueError):
                continue
            if uid:
                normalized = dict(member)
                normalized["user_id"] = uid
                members_by_id[uid] = normalized
    except Exception:
        logger.exception("Unable to load community Member Bank for birthday selector.")

    try:
        for member in get_members(chat_id=chat_id, limit=1000):
            try:
                uid = int(member.get("user_id"))
            except (TypeError, ValueError):
                continue
            if not uid:
                continue
            if uid not in members_by_id:
                members_by_id[uid] = dict(member)
            else:
                # Fill missing display details from raffle history without
                # replacing the authoritative community member record.
                for key in ("username", "first_name", "display_name"):
                    if not members_by_id[uid].get(key) and member.get(key):
                        members_by_id[uid][key] = member[key]
    except Exception:
        logger.exception("Unable to load raffle members for birthday selector.")

    members = sorted(
        members_by_id.values(),
        key=lambda item: (
            str(item.get("first_name") or item.get("display_name") or "").casefold(),
            int(item.get("user_id") or 0),
        ),
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
            "they will appear here.",
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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    # Store the community chat ID, not the private admin DM ID.
    try:
        context.user_data["admin_birthday_chat_id"] = int(MAIN_GROUP_ID)
    except (TypeError, ValueError):
        await query.edit_message_text(
            "⚠️ The community group is not configured correctly. Please check MAIN_GROUP_ID.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
            ]),
        )
        return

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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
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

                if int(item.get("user_id", 0)) == member_user_id:

                    member = item
                    break

            except (TypeError, ValueError):
                continue

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

    try:
        await query.answer(
            "Member selected."
        )
    except Exception:
        pass

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

    if not await require_admin(
        update,
        context,
        alert=False,
    ):

        context.user_data.pop(
            "awaiting_admin_birthday",
            None,
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

    if (
        birthday_chat_id is None
        or selected_user_id is None
    ):

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

    for key in [
        "awaiting_admin_birthday",
        "admin_birthday_chat_id",
        "admin_birthday_selected_user_id",
        "admin_birthday_selected_name",
        "admin_birthday_members",
        "admin_birthday_page",
    ]:

        context.user_data.pop(
            key,
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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

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
# REPOST BIRTHDAYS TO THE MAIN COMMUNITY GROUP
# ==========================================================

async def admin_repost_birthdays(update, context):

    if not await require_admin(update, context):
        return

    query = update.callback_query

    if query:
        try:
            await query.answer("🎂 Reposting birthdays...")
        except Exception:
            pass

    # Use the configured community group. RAFFLE_CHAT_ID is the
    # existing fallback used by this project when MAIN_GROUP_ID
    # is not separately configured.
    target_chat_id = MAIN_GROUP_ID or RAFFLE_CHAT_ID

    if not target_chat_id:
        if query and query.message:
            await query.message.reply_text(
                "❌ Birthday repost failed: MAIN_GROUP_ID is not configured."
            )
        logger.error("Birthday repost skipped: no community group ID configured.")
        return

    try:
        birthdays = get_all_birthdays() or []
        lines = []

        for record in birthdays:
            name = (
                record.get("display_name")
                or (
                    "@" + record.get("username")
                    if record.get("username")
                    else None
                )
                or "Melanated AZ Member"
            )
            birthday_value = record.get("birthday") or "Date not set"
            lines.append(
                f"🎂 {html.escape(str(birthday_value))} — {html.escape(str(name))}"
            )

        if lines:
            body = (
                "🎉 <b>MELANATED AZ BIRTHDAYS</b> 🎂\n\n"
                "Let's show our Queens and Kings some birthday love! 💜🥳\n\n"
                + "\n".join(lines)
                + "\n\nNot on the list yet, or need to update your date? "
                "Tap the button below!"
            )
        else:
            body = (
                "🎉 <b>MELANATED AZ BIRTHDAYS</b> 🎂\n\n"
                "We don't have any birthdays saved yet. Be the first to add yours! 💜🥳"
            )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎂 Submit My Birthday",
                callback_data="birthday_enter",
            )]
        ])

        # Telegram limits a message to 4096 characters. Split long lists
        # into safe-sized posts and include the submit button on every post.
        max_chars = 3400
        chunks = []
        current = (
            "🎉 <b>MELANATED AZ BIRTHDAYS</b> 🎂\n\n"
            "Let's show our Queens and Kings some birthday love! 💜🥳\n\n"
        )
        if not lines:
            chunks = [body]
        else:
            for line in lines:
                if len(current) + len(line) + 1 > max_chars:
                    chunks.append(current.rstrip())
                    current = "🎂 <b>MORE MELANATED AZ BIRTHDAYS</b> 🎂\n\n"
                current += line + "\n"
            current += (
                "\nNot on the list yet, or need to update your date? "
                "Tap the button below!"
            )
            chunks.append(current.rstrip())

        sent = 0
        for chunk in chunks:
            await context.bot.send_message(
                chat_id=target_chat_id,
                text=chunk,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            sent += 1

        logger.info(
            "Admin reposted birthdays | admin=%s | count=%s | messages=%s | chat=%s",
            update.effective_user.id if update.effective_user else None,
            len(birthdays),
            sent,
            target_chat_id,
        )

        if query and query.message:
            await query.message.reply_text(
                f"✅ Birthday list reposted to the community group ({len(birthdays)} saved birthdays)."
            )

    except Exception:
        logger.exception("Failed to repost birthdays.")
        if query and query.message:
            try:
                await query.message.reply_text(
                    "❌ <b>Birthday Repost Failed</b>\n\n"
                    "The birthday list could not be reposted. Check the Render logs.",
                    parse_mode="HTML",
                )
            except Exception:
                pass


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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

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

        try:
            await query.answer(
                "Birthday removed."
            )
        except Exception:
            pass

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

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        from games.game_center import games_admin_menu

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
# DIRTY MINDS
# ==========================================================

async def admin_dirty_minds(
    update,
    context,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎭 CREATE DIRTY MINDS GAME",
                    callback_data="admin_dirty_create",
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 ACTIVE DIRTY MINDS ROOMS",
                    callback_data="admin_dirty_rooms",
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

    await query.edit_message_text(
        "🎭 **DIRTY MINDS**\n\n"
        "Create a multiplayer Dirty Minds game for the "
        "community.\n\n"
        "Players join through Telegram and then play "
        "together in the web game.\n\n"
        "🎤 Microphone: optional\n"
        "📷 Camera: optional\n"
        "👥 Up to 20 players\n\n"
        "Each player can independently choose:\n"
        "• Mic only\n"
        "• Camera only\n"
        "• Mic + Camera\n"
        "• Neither",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# ==========================================================
# CREATE DIRTY MINDS GAME
# ==========================================================

async def admin_create_dirty_minds(
    update,
    context,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    try:
        await query.answer(
            "Creating Dirty Minds game..."
        )
    except Exception:
        pass

    try:

        from game_manager import GAME_MANAGER

    except ImportError:

        try:
            from real_games.game_manager import GAME_MANAGER

        except ImportError:

            logger.exception(
                "Could not import GAME_MANAGER."
            )

            await query.edit_message_text(
                "❌ **Dirty Minds Error**\n\n"
                "The game manager could not be loaded.\n\n"
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

            return

    try:

        from dirty_minds import create_dirty_minds_state

    except ImportError:

        try:

            from real_games.dirty_minds import (
                create_dirty_minds_state
            )

        except ImportError:

            logger.exception(
                "Could not import Dirty Minds engine."
            )

            await query.edit_message_text(
                "❌ **Dirty Minds Error**\n\n"
                "The Dirty Minds game engine could not "
                "be loaded.\n\n"
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

            return

    try:

        room = GAME_MANAGER.create(
            game_id="dirty_minds",
            game_name="Dirty Minds",
            max_players=20,
            min_players=2,
            state=create_dirty_minds_state(),
        )

        display_name = (
            user.full_name
            or user.first_name
            or f"Player {user.id}"
        )

        room.add_player(
            str(user.id),
            display_name,
        )

        room.host_id = str(user.id)

        if str(user.id) in room.players:

            room.players[
                str(user.id)
            ]["host"] = True

    except Exception:

        logger.exception(
            "Failed to create Dirty Minds room."
        )

        await query.edit_message_text(
            "❌ **Dirty Minds Game Creation Failed**\n\n"
            "The room could not be created.\n\n"
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

        return

    try:

        me = await context.bot.get_me()
        bot_username = me.username

    except Exception:

        logger.exception(
            "Unable to get bot username."
        )

        bot_username = None

    if not bot_username:

        await query.edit_message_text(
            "❌ **Dirty Minds Created — But No Join Link**\n\n"
            f"Room: `{room.room_id}`\n\n"
            "I could not determine the Telegram bot username.\n"
            "Check the Render logs.",
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

    join_link = (
        f"https://t.me/{bot_username}"
        f"?start=rg_join_{room.room_id}"
    )

    # ------------------------------------------------------
    # POST GAME TO COMMUNITY CHAT
    # ------------------------------------------------------

    try:

        from config import RAFFLE_CHAT_ID

        community_chat_id = int(
            RAFFLE_CHAT_ID
        )

    except Exception:

        community_chat_id = None

    announcement_text = (
        "🎭 **DIRTY MINDS IS LIVE!** 🎭\n\n"
        "Think dirty. Answer clean. 😈\n\n"
        "A new multiplayer Dirty Minds game has been "
        "created.\n\n"
        f"👥 Players: **{room.player_count()}/20**\n"
        f"🎮 Room: `{room.room_id}`\n\n"
        "🎤 **Microphone:** Optional\n"
        "📷 **Camera:** Optional\n\n"
        "Everyone controls their own mic and camera.\n"
        "You can use either one, both, or neither.\n\n"
        "Tap the button below to join."
    )

    join_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎭 JOIN DIRTY MINDS",
                    url=join_link,
                )
            ]
        ]
    )

    community_message = None

    if community_chat_id:

        try:

            community_message = await context.bot.send_message(
                chat_id=community_chat_id,
                text=announcement_text,
                reply_markup=join_keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )

        except Exception:

            logger.exception(
                "Could not post Dirty Minds announcement "
                "to community chat."
            )

    # ------------------------------------------------------
    # ADMIN CONFIRMATION
    # ------------------------------------------------------

    admin_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎭 OPEN GAME",
                    url=join_link,
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 ACTIVE ROOMS",
                    callback_data="admin_dirty_rooms",
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

    community_status = (
        "✅ Posted to the community chat."
        if community_message
        else
        "⚠️ I could not post to the configured community chat."
    )

    await query.edit_message_text(
        "✅ **DIRTY MINDS GAME CREATED!** 🎭\n\n"
        f"🎮 Room: `{room.room_id}`\n"
        f"👑 Host: **{display_name}**\n"
        f"👥 Players: **1/20**\n\n"
        "🎤 Mic: Optional\n"
        "📷 Camera: Optional\n\n"
        f"{community_status}\n\n"
        "The Telegram JOIN button is ready.",
        reply_markup=admin_keyboard,
        parse_mode="Markdown",
    )

    logger.info(
        "Dirty Minds room created | room=%s | host=%s | "
        "community_posted=%s",
        room.room_id,
        user.id,
        bool(community_message),
    )


# ==========================================================
# ACTIVE DIRTY MINDS ROOMS
# ==========================================================

async def admin_dirty_rooms(
    update,
    context,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        from game_manager import GAME_MANAGER

    except ImportError:

        try:
            from real_games.game_manager import GAME_MANAGER

        except ImportError:

            await query.edit_message_text(
                "❌ Game manager unavailable.",
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
            )

            return

    rooms = GAME_MANAGER.list_rooms(
        game_id="dirty_minds"
    )

    active_rooms = [
        room
        for room in rooms
        if not room.finished
    ]

    if not active_rooms:

        await query.edit_message_text(
            "📋 **ACTIVE DIRTY MINDS ROOMS**\n\n"
            "There are currently no active Dirty Minds rooms.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➕ Create Game",
                            callback_data="admin_dirty_create",
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

        return

    buttons = []

    for room in active_rooms:

        buttons.append(
            [
                InlineKeyboardButton(
                    (
                        f"🎭 {room.room_id} "
                        f"({room.player_count()}/20)"
                    ),
                    callback_data=(
                        f"admin_dirty_view_{room.room_id}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "➕ Create Game",
                callback_data="admin_dirty_create",
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

    await query.edit_message_text(
        "📋 **ACTIVE DIRTY MINDS ROOMS**\n\n"
        f"Active rooms: **{len(active_rooms)}**\n\n"
        "Select a room to view or close it.",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


# ==========================================================
# VIEW DIRTY MINDS ROOM
# ==========================================================

async def admin_dirty_view_room(
    update,
    context,
    room_id,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        from game_manager import GAME_MANAGER

    except ImportError:

        try:
            from real_games.game_manager import GAME_MANAGER

        except ImportError:

            await query.edit_message_text(
                "❌ Game manager unavailable."
            )

            return

    room = GAME_MANAGER.get(
        room_id
    )

    if not room:

        await query.edit_message_text(
            "❌ **Room Not Found**\n\n"
            "This Dirty Minds room no longer exists.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Active Rooms",
                            callback_data="admin_dirty_rooms",
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

        return

    players = room.players

    player_lines = []

    for player in players.values():

        host_marker = (
            " 👑"
            if player.get("host")
            else ""
        )

        player_lines.append(
            f"• {player.get('name', 'Player')}{host_marker}"
        )

    if not player_lines:
        player_lines.append("• No players")

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🛑 CLOSE ROOM",
                    callback_data=(
                        f"admin_dirty_close_{room.room_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Active Rooms",
                    callback_data="admin_dirty_rooms",
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

    await query.edit_message_text(
        "🎭 **DIRTY MINDS ROOM**\n\n"
        f"🎮 Room: `{room.room_id}`\n"
        f"👥 Players: **{room.player_count()}/20**\n"
        f"▶️ Started: **{'Yes' if room.started else 'No'}**\n\n"
        "**Players:**\n"
        + "\n".join(player_lines),
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# ==========================================================
# CLOSE DIRTY MINDS ROOM
# ==========================================================

async def admin_dirty_close_room(
    update,
    context,
    room_id,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    try:
        await query.answer(
            "Closing room..."
        )
    except Exception:
        pass

    try:

        from game_manager import GAME_MANAGER

    except ImportError:

        try:
            from real_games.game_manager import GAME_MANAGER

        except ImportError:

            await query.edit_message_text(
                "❌ Game manager unavailable."
            )

            return

    room = GAME_MANAGER.get(
        room_id
    )

    if not room:

        await query.edit_message_text(
            "⚠️ That room is already gone.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Active Rooms",
                            callback_data="admin_dirty_rooms",
                        )
                    ]
                ]
            ),
        )

        return

    GAME_MANAGER.remove(
        room.room_id
    )

    await query.edit_message_text(
        "🛑 **DIRTY MINDS ROOM CLOSED**\n\n"
        f"Room `{room.room_id}` has been closed.\n\n"
        "Players will no longer be able to use that "
        "game room.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📋 Active Rooms",
                        callback_data="admin_dirty_rooms",
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

    logger.info(
        "Dirty Minds room closed | room=%s | admin=%s",
        room.room_id,
        user.id,
    )


# ==========================================================
# TRUTH OR DARE
# ==========================================================

async def admin_truthdare(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    try:

        from truth_dare import truth_dare_admin_menu

        await truth_dare_admin_menu(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Truth or Dare admin menu failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.edit_message_text(
                    "❌ **Truth or Dare Error**\n\n"
                    "The Truth or Dare admin menu could "
                    "not be loaded.\n\n"
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

            except Exception:
                pass


async def admin_truthdare_toggle(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    try:

        from truth_dare import toggle_truth_dare

        await toggle_truth_dare(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Truth or Dare toggle failed."
        )


async def admin_truthdare_help(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    try:

        from truth_dare import truth_dare_help

        await truth_dare_help(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Truth or Dare help failed."
        )


# ==========================================================
# HOLIDAY EXCHANGE
# ==========================================================

async def admin_holiday_exchange(
    update,
    context,
):

    if not await require_admin(
        update,
        context,
    ):
        return

    try:

        await holiday_exchange_admin_callback(
            update,
            context,
        )

    except Exception:

        logger.exception(
            "Holiday Exchange admin callback failed."
        )

        query = update.callback_query

        if query:

            try:

                await query.edit_message_text(
                    "❌ **Holiday Exchange Error**\n\n"
                    "The Holiday Exchange admin panel "
                    "could not be loaded.\n\n"
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

            except Exception:
                pass


# ==========================================================
# REFRESH
# ==========================================================

async def admin_refresh(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer(
            "Admin panel refreshed."
        )
    except Exception:
        pass

    await query.edit_message_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# BACK
# ==========================================================

async def admin_back(update, context):

    if not await require_admin(
        update,
        context,
    ):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    for key in [
        "awaiting_admin_birthday",
        "admin_birthday_chat_id",
        "admin_birthday_selected_user_id",
        "admin_birthday_selected_name",
        "admin_birthday_members",
        "admin_birthday_page",
        "admin_manual_raffle_members",
        "admin_manual_raffle_page",
        "admin_manual_raffle_selected_user_id",
        "admin_manual_raffle_selected_name",
        "admin_manual_raffle_chat_id",
    ]:

        context.user_data.pop(
            key,
            None,
        )

    await query.edit_message_text(
        text=admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# QUESTION OF THE DAY / AFTER DARK ADMIN CONTROLS
# ==========================================================

async def admin_questions(update, context):
    if not await require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer()
    try:
        from question_of_day import queued_count, daily_post_already_done, qotd_enabled
        count = queued_count()
        posted = daily_post_already_done()
        enabled = qotd_enabled()
    except Exception:
        count, posted, enabled = 0, False, False
    await query.edit_message_text(
        "💭 **QUESTION OF THE DAY**\n\n"
        "🕚 **Daily:** 11:00 AM Arizona time\n"
        f"📚 Queued: **{count} day{'s' if count != 1 else ''}**\n"
        f"📅 Today's post: **{'Posted' if posted else 'Not posted'}**\n"
        f"⚙️ System: **{'Enabled' if enabled else 'Not configured'}**\n\n"
        "📍 Destination: topic `11999`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 QOTD Bank Status", callback_data="admin_qotd_status")],
            [InlineKeyboardButton("▶️ Post Next QOTD Now", callback_data="admin_qotd_post_next")],
            [InlineKeyboardButton("📌 Recreate QOTD Panel", callback_data="admin_qotd_panel")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")],
        ]),
        parse_mode="Markdown",
    )

async def admin_qotd_status(update, context):
    if not await require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer()
    try:
        import json
        from question_of_day import db_connect, daily_post_already_done
        with db_connect() as conn:
            rows = conn.execute(
                "SELECT id, item_type, prompt, options_json, voice_file_id "
                "FROM qotd_items WHERE status='queued' ORDER BY id ASC LIMIT 8"
            ).fetchall()
            count = conn.execute(
                "SELECT COUNT(*) FROM qotd_items WHERE status='queued'"
            ).fetchone()[0]
        posted = daily_post_already_done()
        lines = [
            "📚 <b>QOTD BANK — QUEUED ITEMS</b>",
            f"Queued: <b>{count}</b> | Today's post: <b>{'Posted' if posted else 'Not posted'}</b>",
            "",
            "Select an item below to view it and edit or delete it:",
        ]
        buttons = []
        for row in rows:
            item_id, item_type, prompt, options_json, voice_file_id = row
            label = (prompt or ("Voice question" if voice_file_id else "Untitled question")).replace("\\n", " ").strip()
            if len(label) > 48:
                label = label[:45] + "..."
            prefix = "📊" if item_type == "poll" else ("🎙️" if item_type == "voice" or voice_file_id else "💭")
            buttons.append([InlineKeyboardButton(
                f"{prefix} #{item_id} {label}",
                callback_data=f"qotd_bank_item_{item_id}"
            )])
        if count > 8:
            buttons.append([InlineKeyboardButton("➡️ Next items", callback_data="qotd_bank_page_1")])
        buttons.extend([
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_qotd_status")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_questions")],
            [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
        ])
        if not rows:
            lines.append("\nNo queued questions or polls were found in the QOTD database.")
        await query.edit_message_text(
            "\\n".join(lines),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Unable to display queued QOTD items in admin panel")
        await query.edit_message_text(
            "📚 QOTD bank could not be loaded. Check the bot logs for the database error.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try again", callback_data="admin_qotd_status")],
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_questions")],
            ]),
        )

async def admin_qotd_post_next(update, context):
    if not await require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer("Posting next QOTD...")
    try:
        from question_of_day import publish_item, get_next_item
        item = get_next_item()
        if not item:
            text = "📚 **QOTD BANK EMPTY**\n\nThere is nothing queued to post."
        else:
            posted = await publish_item(context, int(item["id"]))
            text = "✅ **QOTD POSTED**\n\nThe next queued Question/Poll was posted to topic `11999`." if posted else "❌ **QOTD POST FAILED**\n\nCheck the Render logs."
    except Exception:
        text = "❌ **QOTD POST FAILED**\n\nCheck the Render logs."
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("💭 QOTD Controls", callback_data="admin_questions")],
        [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
    ]), parse_mode="Markdown")

async def admin_qotd_panel(update, context):
    if not await require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer("Recreating QOTD panel...")
    try:
        from question_of_day import ensure_qotd_submission_panel
        await ensure_qotd_submission_panel(context.application)
        text = "📌 **QOTD PANEL READY**\n\nThe submission panel was created/re-pinned in topic `11999`."
    except Exception:
        text = "❌ **QOTD PANEL FAILED**\n\nCheck the Render logs."
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("💭 QOTD Controls", callback_data="admin_questions")],
        [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
    ]), parse_mode="Markdown")

async def admin_after_dark(update, context):
    if not await require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer()
    await query.edit_message_text(
        "🌙 **AFTER DARK**\n\n"
        "After Dark uses its separate content bank and posts into the shared topic.\n\n"
        "🌙 **Daily:** 11:00 PM Arizona time\n"
        "📍 **Destination:** topic `11999`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌙 Confirm 11:00 PM Schedule", callback_data="admin_after_dark_schedule")],
            [InlineKeyboardButton("🌙 Post After Dark Now", callback_data="admin_after_dark_now")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")],
        ]),
        parse_mode="Markdown",
    )

async def admin_after_dark_schedule(update, context):
    if not await require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer("Schedule confirmed")
    await query.edit_message_text(
        "🌙 **AFTER DARK SCHEDULE**\n\n"
        "Daily at **11:00 PM Arizona time**.\n\n"
        "Posts to the shared topic `11999`.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌙 After Dark Controls", callback_data="admin_after_dark")],
            [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
        ]),
        parse_mode="Markdown",
    )

async def admin_after_dark_now(update, context):
    if not await require_admin(update, context):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer("Posting After Dark...")
    try:
        import daily_messages
        handler = getattr(daily_messages, "_after_dark_message_handler", None)
        if handler is None:
            raise RuntimeError("After Dark routing handler is not configured.")
        await handler(context)
        text = "🌙 **AFTER DARK POSTED**\n\nThe current After Dark prompt was posted to topic `11999`."
    except Exception:
        text = "❌ **AFTER DARK POST FAILED**\n\nCheck the Render logs."
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🌙 After Dark Controls", callback_data="admin_after_dark")],
        [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
    ]), parse_mode="Markdown")


# ==========================================================
# APPROVED EVENTS
# ==========================================================

async def admin_approved_events(update, context, page=0):
    """Show Event OCR submissions in pages so older IDs never disappear from the admin UI."""
    if not await require_admin(update, context):
        return

    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    from event_ocr import _db, _fields

    PAGE_SIZE = 5

    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM event_submissions "
            "WHERE status != 'denied' "
            "ORDER BY id DESC"
        ).fetchall()

    total = len(rows)
    max_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    try:
        page = max(0, min(int(page), max_page - 1))
    except (TypeError, ValueError):
        page = 0

    if not rows:
        await query.edit_message_text(
            "📅 **EVENT SUBMISSIONS**\n\nThere are currently no Event submissions.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
            ]),
            parse_mode="Markdown",
        )
        return

    page_rows = rows[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    blocks = []
    buttons = []

    for row in page_rows:
        sid = int(row["id"])
        status = str(row["status"] or "")
        fields = _fields(row)
        name = fields.get("event") or f"Event #{sid}"
        date = fields.get("date") or "Date missing"

        status_label = {
            "approved": "✅ APPROVED",
            "pending_admin": "⏳ PENDING APPROVAL",
            "member_input": "✏️ MEMBER INPUT",
            "awaiting_confirmation": "🔎 AWAITING CONFIRMATION",
            "admin_send_failed": "⚠️ ADMIN SEND FAILED",
            "expired": "⌛ EXPIRED — FLYER REMOVED",
        }.get(status, status.upper() or "UNKNOWN")

        blocks.append(
            f"**{name}**\n"
            f"📅 {date}\n"
            f"📌 {status_label}\n"
            f"🆔 Submission #{sid}"
        )

        if status in {
            "approved",
            "pending_admin",
            "member_input",
            "awaiting_confirmation",
            "admin_send_failed",
            "expired",
        }:
            buttons += [
                [InlineKeyboardButton("✏️ Event", callback_data=f"event_ocr_admin_edit_event_{sid}")],
                [
                    InlineKeyboardButton("✏️ Date", callback_data=f"event_ocr_admin_edit_date_{sid}"),
                    InlineKeyboardButton("✏️ Time", callback_data=f"event_ocr_admin_edit_time_{sid}"),
                ],
                [
                    InlineKeyboardButton("✏️ Location", callback_data=f"event_ocr_admin_edit_location_{sid}"),
                    InlineKeyboardButton("✏️ Price", callback_data=f"event_ocr_admin_edit_price_{sid}"),
                ],
                [InlineKeyboardButton("✏️ Website", callback_data=f"event_ocr_admin_edit_website_{sid}")],
                [InlineKeyboardButton(
                    f"🗑️ Remove #{sid}",
                    callback_data=f"event_ocr_admin_remove_{sid}",
                )],
            ]
            if status == "pending_admin":
                buttons.append([
                    InlineKeyboardButton(
                        f"🔎 Review / Approve #{sid}",
                        callback_data="admin_pending_event_approvals",
                    )
                ])

        buttons.append([
            InlineKeyboardButton("────────", callback_data=f"admin_approved_events_{page}")
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Newer", callback_data=f"admin_approved_events_{page - 1}"))
    if page < max_page - 1:
        nav.append(InlineKeyboardButton("Older ➡️", callback_data=f"admin_approved_events_{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons += [
        [InlineKeyboardButton(f"📄 Page {page + 1} of {max_page} ({total} total)", callback_data=f"admin_approved_events_{page}")],
        [InlineKeyboardButton("🔄 Refresh Events", callback_data=f"admin_approved_events_{page}")],
        [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")],
    ]

    await query.edit_message_text(
        f"📅 **EVENT SUBMISSIONS — Page {page + 1} of {max_page}**\n\n"
        + "\n\n".join(blocks)
        + "\n\nUse **Older ➡️** to reach older submission IDs. "
          "Expired flyers remain recoverable here; only the public Events flyer is removed after the event date.",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )

async def admin_pending_event_approvals(update, context):
    """Show pending Event OCR flyers so an admin can review them manually."""
    if not await require_admin(update, context):
        return

    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    from event_ocr import _db, _fields, _admin_keyboard

    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM event_submissions "
            "WHERE status='pending_admin' ORDER BY id ASC"
        ).fetchall()

    if not rows:
        await query.edit_message_text(
            "📥 **PENDING EVENT APPROVALS**\n\n"
            "There are currently no Event flyers waiting for approval.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_pending_event_approvals")],
                [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return

    try:
        await query.edit_message_text(
            f"📥 **PENDING EVENT APPROVALS — {len(rows)}**\n\n"
            "Sending the pending flyer(s) below for manual review...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_pending_event_approvals")],
                [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
    except Exception:
        pass

    for row in rows:
        sid = int(row["id"])
        fields = _fields(row)
        submitter = (
            f"@{row['username']}"
            if row["username"]
            else (row["first_name"] or str(row["user_id"]))
        )
        caption = (
            "📥 <b>PENDING EVENT APPROVAL</b>\n\n"
            + _format_fields(fields)
            + f"\n\nSubmitted by: {html.escape(submitter)}\n"
            + f"Submission #{sid}"
        )

        try:
            if row["media_type"] == "photo":
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=row["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                )
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=row["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                )

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=(
                    f"🔎 <b>Review Submission #{sid}</b>\n\n"
                    "Use the buttons to edit a field, approve, or deny this Event."
                ),
                parse_mode="HTML",
                reply_markup=_admin_keyboard(sid, approved=False),
            )
        except TelegramError:
            logger.exception(
                "Could not display pending Event flyer | submission=%s",
                sid,
            )


# ==========================================================
# ADMIN BUTTON ROUTER
# ==========================================================

# ==========================================================
# RAFFLE QUEUE ADMIN PANEL
# ==========================================================

def admin_raffle_queue_keyboard(queued):
    rows = []
    for position, raffle in enumerate(queued, 1):
        rows.append([
            InlineKeyboardButton(
                f"❌ Remove #{raffle['id']}",
                callback_data=f"admin_queue_remove_{raffle['id']}",
            )
        ])
    rows.extend([
        [InlineKeyboardButton("➕ Add Raffle", callback_data="admin_queue_add")],
        [InlineKeyboardButton("🔄 Refresh Queue", callback_data="admin_queue_refresh")],
        [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")],
    ])
    return InlineKeyboardMarkup(rows)


async def show_admin_raffle_queue(update, context, notice=None):
    if not await require_admin(update, context, alert=True):
        return
    query = update.callback_query
    if query:
        try:
            await query.answer()
        except Exception:
            pass
    try:
        queued = get_queued_raffles()
    except Exception:
        logger.exception("Unable to load raffle queue in admin panel.")
        text = "⚠️ <b>Raffle Queue</b>\n\nI couldn't load the queue. Please check the Render logs."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")]])
    else:
        lines = ["🎟️ <b>Raffle Queue</b>", ""]
        if notice:
            lines.extend([notice, ""])
        if not queued:
            lines.append("The queue is currently empty.")
        else:
            lines.append("Upcoming raffles launch in this order:")
            for position, raffle in enumerate(queued, 1):
                prize = html.escape(str(raffle.get("prize") or "Raffle"))
                price = html.escape(str(raffle.get("price") or ""))
                lines.append(f"<b>{position}.</b> Raffle <b>#{raffle['id']}</b> — {prize} ({price})")
        text = "\n".join(lines)
        keyboard = admin_raffle_queue_keyboard(queued)
    target = query.message if query else update.effective_message
    if not target:
        return
    try:
        if query:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await target.reply_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    except BadRequest as exc:
        # Telegram returns this when a refresh produces identical text and buttons.
        # That is a harmless no-op, not a queue failure.
        if "Message is not modified" in str(exc):
            logger.debug("Raffle queue refresh unchanged; no edit needed.")
            return
        logger.exception("Unable to display raffle queue admin panel.")
    except Exception:
        logger.exception("Unable to display raffle queue admin panel.")


async def admin_queue_add_prompt(update, context):
    if not await require_admin(update, context, alert=True):
        return
    query = update.callback_query
    if not query:
        return
    context.user_data["admin_queue_raffle_waiting"] = True
    logger.info("Admin started queued-raffle entry | user=%s", update.effective_user.id if update.effective_user else None)
    try:
        await query.answer()
        await query.edit_message_text(
            "➕ **Add a Raffle to the Queue**\n\n"
            "Send the prize and entry price on one line, separated by `|`.\n\n"
            "Example: `$50 Gift Card | $5`\n\n"
            "This only adds an upcoming raffle; it will not change the active raffle.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✖️ Cancel", callback_data="admin_queue_cancel_add")],
                [InlineKeyboardButton("⬅️ Back to Queue", callback_data="admin_queue_refresh")],
            ]),
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Unable to open Add Raffle queue prompt.")


async def admin_queue_text_handler(update, context):
    """Consume the next non-command text message when an admin started queue-add from the panel."""
    if not context.user_data.get("admin_queue_raffle_waiting"):
        return False
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return False
    if not await is_admin(user.id, context):
        context.user_data.pop("admin_queue_raffle_waiting", None)
        await message.reply_text("⛔ You are not authorized to add a queued raffle.")
        raise ApplicationHandlerStop
    payload = (message.text or "").strip()
    logger.info("Received queued-raffle submission | user=%s | payload_length=%s", user.id, len(payload))
    if "|" not in payload:
        await message.reply_text(
            "⚠️ Please use this format: `Prize | Entry Price`\nExample: `$50 Gift Card | $5`",
            parse_mode="Markdown",
        )
        raise ApplicationHandlerStop
    prize, price = (part.strip() for part in payload.split("|", 1))
    if not prize or not price:
        await message.reply_text(
            "⚠️ Both prize and entry price are required. Use: `Prize | Entry Price`",
            parse_mode="Markdown",
        )
        raise ApplicationHandlerStop
    try:
        raffle_id = create_queued_raffle(prize, price)
        queued = get_queued_raffles()
        position = next((i for i, item in enumerate(queued, 1) if int(item["id"]) == int(raffle_id)), len(queued))
    except Exception:
        logger.exception("Admin panel could not add raffle to queue | user=%s", user.id)
        context.user_data.pop("admin_queue_raffle_waiting", None)
        await message.reply_text("❌ I couldn't add that raffle. No existing raffle was changed.")
        raise ApplicationHandlerStop
    context.user_data.pop("admin_queue_raffle_waiting", None)
    await message.reply_text(
        "✅ <b>Raffle Added to Queue</b>\n\n"
        f"<b>Raffle ID:</b> {raffle_id}\n"
        f"<b>Prize:</b> {html.escape(prize)}\n"
        f"<b>Entry price:</b> {html.escape(price)}\n"
        f"<b>Queue position:</b> {position}\n\n"
        "It will launch automatically after the current raffle closes and its winner is drawn.",
        parse_mode="HTML",
    )
    raise ApplicationHandlerStop


async def admin_queue_remove_button(update, context, raffle_id):
    if not await require_admin(update, context, alert=True):
        return
    try:
        removed = cancel_queued_raffle(int(raffle_id))
    except Exception:
        logger.exception("Could not remove queued raffle %s from admin panel.", raffle_id)
        removed = False
    await show_admin_raffle_queue(
        update, context,
        notice=("❌ Raffle #%s removed from the queue." % raffle_id) if removed
        else ("⚠️ Raffle #%s was not in the queue; nothing was changed." % raffle_id),
    )


# ==========================================================
# ACTIVE RAFFLE PAYMENT REMINDERS
# ==========================================================

def _payment_reminder_keyboard(raffle_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 Private DMs", callback_data=f"admin_payment_mode_private_{raffle_id}"),
            InlineKeyboardButton("📢 Group Post", callback_data=f"admin_payment_mode_group_{raffle_id}"),
        ],
        [InlineKeyboardButton("📩 + 📢 Send Both", callback_data=f"admin_payment_mode_both_{raffle_id}")],
        [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")],
    ])

def _payment_reminder_confirm_keyboard(mode, raffle_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Send", callback_data=f"admin_payment_execute_{mode}_{raffle_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_payment_reminders")],
    ])

def _active_pending_payment_entries():
    raffle = get_active_raffle()
    if not raffle:
        return None, []
    return raffle, get_pending_entries(int(raffle["id"]))

async def admin_payment_reminders(update, context):
    if not await require_admin(update, context, alert=True):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer()
    raffle, entries = _active_pending_payment_entries()
    if not raffle:
        await query.edit_message_text(
            "💸 <b>PAYMENT REMINDERS</b>\n\nThere is no active raffle right now.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_payment_reminders")],
                [InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="HTML",
        )
        return
    prize = html.escape(str(raffle.get("prize") or "Raffle"))
    price = html.escape(str(raffle.get("price") or ""))
    await query.edit_message_text(
        "💸 <b>ACTIVE RAFFLE PAYMENT REMINDERS</b>\n\n"
        f"🎟️ Raffle: <b>{prize}</b>\n"
        f"💵 Entry price: <b>{price or 'See raffle details'}</b>\n"
        f"⏳ Entries awaiting payment/approval: <b>{len(entries)}</b>\n\n"
        "Choose where to send the reminder. You will get a confirmation screen before anything is sent. "
        "Only pending entries for this active raffle are eligible; approved entries are excluded.",
        reply_markup=_payment_reminder_keyboard(int(raffle["id"])),
        parse_mode="HTML",
    )

async def admin_payment_reminder_choose_mode(update, context, mode, raffle_id):
    if not await require_admin(update, context, alert=True):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer()
    raffle = get_active_raffle()
    if not raffle or int(raffle.get("id", 0)) != int(raffle_id):
        await query.edit_message_text(
            "⚠️ The active raffle changed or ended. No reminders were sent. Please reopen Payment Reminders.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Recheck", callback_data="admin_payment_reminders")]]),
        )
        return
    entries = get_pending_entries(int(raffle_id))
    mode_names = {
        "private": "private messages to pending entrants",
        "group": "one generic group announcement",
        "both": "private messages plus one generic group announcement",
    }
    if mode not in mode_names:
        await query.answer("Invalid reminder option.", show_alert=True)
        return
    pending_note = (
        "There are no pending entries to message privately."
        if mode in {"private", "both"} and not entries
        else f"{len(entries)} pending entries will be checked again before sending."
    )
    await query.edit_message_text(
        "⚠️ <b>CONFIRM PAYMENT REMINDER</b>\n\n"
        f"🎟️ Raffle: <b>{html.escape(str(raffle.get('prize') or 'Raffle'))}</b>\n"
        f"📨 Action: <b>{html.escape(mode_names[mode])}</b>\n"
        f"⏳ {html.escape(pending_note)}\n\n"
        "Approved entries will not be messaged. Group announcements will not name members. Continue?",
        reply_markup=_payment_reminder_confirm_keyboard(mode, int(raffle_id)),
        parse_mode="HTML",
    )

async def admin_payment_reminder_execute(update, context, mode, raffle_id):
    if not await require_admin(update, context, alert=True):
        return
    query = update.callback_query
    if not query:
        return
    await query.answer("Processing payment reminders...")
    raffle = get_active_raffle()
    if not raffle or int(raffle.get("id", 0)) != int(raffle_id):
        await query.edit_message_text(
            "⚠️ The active raffle changed or ended. No reminders were sent.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_back")]]),
        )
        return
    prize = str(raffle.get("prize") or "the active raffle")
    price = str(raffle.get("price") or "")
    private_sent = 0
    private_failed = 0
    private_skipped = 0
    group_status = "Not requested"
    group_error = None
    if mode in {"private", "both"}:
        candidates = get_pending_entries(int(raffle_id))
        for candidate in candidates:
            entry_id = candidate.get("id")
            try:
                current = get_entry(int(entry_id)) if entry_id is not None else None
                if (
                    not current
                    or str(current.get("status", "")).lower() != "pending"
                    or int(current.get("raffle_id", 0)) != int(raffle_id)
                    or str(current.get("raffle_status", "")).lower() != "active"
                ):
                    private_skipped += 1
                    continue
                member_id = current.get("user_id")
                if not member_id:
                    private_skipped += 1
                    continue
                name = html.escape(str(current.get("display_name") or current.get("username") or "there"))
                safe_prize = html.escape(prize)
                safe_price = html.escape(price)
                message = (
                    "🎟️ <b>MELANATED AZ — PAYMENT REMINDER</b>\n\n"
                    f"Hey {name}! ❤️🖤\n\n"
                    f"You entered our <b>{safe_prize}</b>, but your entry is still awaiting payment confirmation.\n\n"
                    + (f"💵 Entry price: <b>{safe_price}</b>\n\n" if safe_price else "")
                    + "Please complete your payment so your entry can be approved. Your entry remains pending until payment is received and verified.\n\n"
                    "Thanks for supporting Melanated AZ! Good luck! 🔥"
                )
                await context.bot.send_message(chat_id=int(member_id), text=message, parse_mode="HTML")
                private_sent += 1
            except TelegramError as exc:
                private_failed += 1
                logger.info("Payment reminder DM failed | raffle_id=%s | entry_id=%s | error=%s", raffle_id, entry_id, exc)
            except Exception:
                private_failed += 1
                logger.exception("Unexpected payment reminder DM failure | raffle_id=%s | entry_id=%s", raffle_id, entry_id)
    if mode in {"group", "both"}:
        try:
            group_id = int(MAIN_GROUP_ID)
            safe_prize = html.escape(prize)
            safe_price = html.escape(price)
            group_text = (
                "🎟️🔥 <b>MELANATED AZ — RAFFLE PAYMENT REMINDER!</b> 🔥🎟️\n\n"
                "Hey, Melanated AZ family! ❤️🖤\n\n"
                f"If you entered our <b>{safe_prize}</b> but have not completed payment, this is your reminder.\n"
                + (f"💵 Entry price: <b>{safe_price}</b>\n" if safe_price else "")
                + "✅ Payment must be received and verified before your entry is approved.\n"
                "⏳ Entries remain pending until payment is confirmed.\n\n"
                "If you cannot receive the bot's private messages, please open the Melanated AZ bot or contact an admin to check your entry status.\n\n"
                "Good luck, family! ❤️🖤🔥"
            )
            await context.bot.send_message(chat_id=group_id, text=group_text, parse_mode="HTML")
            group_status = "Posted successfully"
        except Exception as exc:
            group_status = "Failed"
            group_error = str(exc)
            logger.exception("Payment reminder group post failed | raffle_id=%s", raffle_id)
    report = [
        "✅ <b>PAYMENT REMINDER RESULTS</b>",
        "",
        f"🎟️ Raffle: <b>{html.escape(prize)}</b>",
    ]
    if mode in {"private", "both"}:
        report.extend([
            f"📩 Private messages sent: <b>{private_sent}</b>",
            f"⚠️ Private messages failed: <b>{private_failed}</b>",
            f"⏭️ Entries skipped after recheck: <b>{private_skipped}</b>",
        ])
    if mode in {"group", "both"}:
        report.append(f"📢 Group announcement: <b>{html.escape(group_status)}</b>")
        if group_error:
            report.append(f"Error: <code>{html.escape(group_error[:250])}</code>")
    report.extend(["", "Approved entries were not messaged."])
    await query.edit_message_text(
        "\n".join(report),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Counts", callback_data="admin_payment_reminders")],
            [InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_back")],
        ]),
        parse_mode="HTML",
    )

async def admin_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    # ------------------------------------------------------
    # FIRST SECURITY GATE
    # ------------------------------------------------------

    if not await require_admin(
        update,
        context,
        alert=True,
    ):
        return

    user = update.effective_user
    data = query.data or ""

    logger.info(
        "Admin button pressed: %s by %s",
        data,
        user.id,
    )

    if data == "admin_payment_reminders":
        await admin_payment_reminders(update, context)
        return

    for mode in ("private", "group", "both"):
        prefix = f"admin_payment_mode_{mode}_"
        if data.startswith(prefix):
            raffle_id = data[len(prefix):]
            if not raffle_id.isdigit():
                await query.answer("Invalid raffle ID.", show_alert=True)
                return
            await admin_payment_reminder_choose_mode(update, context, mode, int(raffle_id))
            return

        prefix = f"admin_payment_execute_{mode}_"
        if data.startswith(prefix):
            raffle_id = data[len(prefix):]
            if not raffle_id.isdigit():
                await query.answer("Invalid raffle ID.", show_alert=True)
                return
            await admin_payment_reminder_execute(update, context, mode, int(raffle_id))
            return

    # ------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------

    if data == "admin_back":

        await admin_back(
            update,
            context,
        )

        return

    if data.startswith("admin_member_message_cancel_"):
        await _member_message_cancel(update, context, data[len("admin_member_message_cancel_"):])
        return
    if data.startswith("admin_member_message_"):
        await _member_message_prompt(update, context, data[len("admin_member_message_"):])
        return
    if data.startswith("admin_member_remove_confirm_"):
        await _member_remove_confirm(update, context, data[len("admin_member_remove_confirm_"):])
        return
    if data.startswith("admin_member_remove_cancel_"):
        await _member_remove_cancel(update, context, data[len("admin_member_remove_cancel_"):])
        return
    if data.startswith("admin_member_remove_"):
        await _member_remove_prompt(update, context, data[len("admin_member_remove_"):])
        return

    if data == "admin_raffle_queue":
        await show_admin_raffle_queue(update, context)
        return

    if data == "admin_queue_add":
        await admin_queue_add_prompt(update, context)
        return

    if data == "admin_queue_refresh":
        context.user_data.pop("admin_queue_raffle_waiting", None)
        await show_admin_raffle_queue(update, context)
        return

    if data == "admin_queue_cancel_add":
        context.user_data.pop("admin_queue_raffle_waiting", None)
        await show_admin_raffle_queue(update, context, notice="Queue-add cancelled.")
        return

    if data.startswith("admin_queue_remove_"):
        raffle_id = data[len("admin_queue_remove_"):]
        if not raffle_id.isdigit():
            await query.answer("Invalid raffle ID.", show_alert=True)
            return
        await admin_queue_remove_button(update, context, int(raffle_id))
        return

    if data == "admin_refresh":

        await admin_refresh(
            update,
            context,
        )

        return

    if data == "admin_pending_event_approvals":
        await admin_pending_event_approvals(update, context)
        return

    if data == "admin_approved_events":
        await admin_approved_events(update, context, page=0)
        return

    if data.startswith("admin_approved_events_"):
        page_text = data[len("admin_approved_events_"):]
        try:
            page = int(page_text)
        except (TypeError, ValueError):
            await query.answer("Invalid page.", show_alert=True)
            return
        await admin_approved_events(update, context, page=page)
        return

    # ------------------------------------------------------
    # QUESTION OF THE DAY / AFTER DARK
    # ------------------------------------------------------

    if data == "admin_questions":
        await admin_questions(update, context)
        return

    if data == "admin_qotd_status":
        await admin_qotd_status(update, context)
        return

    if data == "admin_qotd_post_next":
        await admin_qotd_post_next(update, context)
        return

    if data == "admin_qotd_panel":
        await admin_qotd_panel(update, context)
        return

    if data == "admin_after_dark":
        await admin_after_dark(update, context)
        return

    if data == "admin_after_dark_schedule":
        await admin_after_dark_schedule(update, context)
        return

    if data == "admin_after_dark_now":
        await admin_after_dark_now(update, context)
        return

    # ------------------------------------------------------
    # HOLIDAY EXCHANGE
    # ------------------------------------------------------

    if (
        data == "admin_holiday_exchange"
        or data.startswith("admin_hx_")
    ):

        await admin_holiday_exchange(
            update,
            context,
        )

        return

    # ------------------------------------------------------
    # MANUAL RAFFLE
    # ------------------------------------------------------

    if data == "admin_manual_entry":

        await admin_manual_entry(
            update,
            context,
        )

        return

    if data == "admin_manual_cancel":

        await admin_manual_cancel(
            update,
            context,
        )

        return

    if data.startswith("admin_manual_page_"):

        page_text = data[
            len("admin_manual_page_"):
        ]

        try:
            page = int(page_text)
        except (TypeError, ValueError):

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        members = context.user_data.get(
            "admin_manual_raffle_members"
        )

        if not members:

            await show_manual_raffle_member_selector(
                update,
                context,
                page=page,
            )

            return

        context.user_data[
            "admin_manual_raffle_page"
        ] = page

        page_size = 8
        total = len(members)

        max_page = max(
            1,
            (total + page_size - 1) // page_size,
        )

        try:
            await query.answer()
        except Exception:
            pass

        await query.edit_message_text(
            "🎟️ **Manual Raffle Entry**\n\n"
            "Select the group member you want to add.\n\n"
            f"Showing page **{page + 1}** of "
            f"**{max_page}**\n\n"
            "Use **Previous** and **Next** to scroll.",
            reply_markup=manual_raffle_member_keyboard(
                members,
                page,
                page_size,
            ),
            parse_mode="Markdown",
        )

        return

    if data.startswith("admin_manual_select_"):

        member_user_id = data[
            len("admin_manual_select_"):
        ]

        await admin_manual_select(
            update,
            context,
            member_user_id,
        )

        return

    if data.startswith("admin_manual_confirm_"):

        member_user_id = data[
            len("admin_manual_confirm_"):
        ]

        await admin_manual_confirm(
            update,
            context,
            member_user_id,
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
    # DIRTY MINDS
    # ------------------------------------------------------

    if data == "admin_dirty_minds":

        await admin_dirty_minds(
            update,
            context,
        )

        return

    if data == "admin_dirty_create":

        await admin_create_dirty_minds(
            update,
            context,
        )

        return

    if data == "admin_dirty_rooms":

        await admin_dirty_rooms(
            update,
            context,
        )

        return

    if data.startswith("admin_dirty_view_"):

        room_id = data[
            len("admin_dirty_view_"):
        ]

        await admin_dirty_view_room(
            update,
            context,
            room_id,
        )

        return

    if data.startswith("admin_dirty_close_"):

        room_id = data[
            len("admin_dirty_close_"):
        ]

        await admin_dirty_close_room(
            update,
            context,
            room_id,
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

    if data == "admin_repost_raffle":

        await admin_repost_raffle(
            update,
            context,
        )

        return

    if data == "admin_edit_raffle_end_date":
        await admin_edit_raffle_end_date(update, context)
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

    if data == "admin_repost_birthdays":

        await admin_repost_birthdays(
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
    # BIRTHDAY MEMBER SELECTION + PAGINATION
    # ------------------------------------------------------

    if data.startswith("admin_bday_select_"):
        member_user_id = data[len("admin_bday_select_"):]
        await admin_birthday_select(update, context, member_user_id)
        return

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

        try:
            await query.answer()
        except Exception:
            pass

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