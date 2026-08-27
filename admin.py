# ==========================================================
# Melanated AZ Bot
# admin.py
# ==========================================================

import logging
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from config import ADMIN_IDS

from raffle_database import (
    get_all_birthdays,
    get_birthdays_for_date,
    remove_birthday_by_id,
)

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    try:

        return int(user_id) in [
            int(x)
            for x in ADMIN_IDS
        ]

    except Exception:

        return False


# ==========================================================
# ADMIN MENU KEYBOARD
# ==========================================================

def admin_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎟️ Raffle Management",
                    callback_data="admin_raffle",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎂 Birthday Management",
                    callback_data="admin_birthdays",
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Today's Birthdays",
                    callback_data="admin_birthday_today",
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 View All Birthdays",
                    callback_data="admin_birthday_list",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Run Birthday Check Now",
                    callback_data="admin_birthday_check",
                )
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
    message = update.effective_message

    if not user or not message:
        return

    if not is_admin(user.id):

        await message.reply_text(
            "❌ Admins only."
        )

        return

    await message.reply_text(
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        "Select an option below.",
        reply_markup=admin_keyboard(),
        parse_mode="Markdown",
    )


# ==========================================================
# ADMIN BUTTON HANDLER
# ==========================================================

async def admin_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    data = query.data or ""

    # ======================================================
    # BACK
    # ======================================================

    if data == "admin_back":

        await query.edit_message_text(
            "👑 **MELANATED AZ ADMIN PANEL**\n\n"
            "Select an option below.",
            reply_markup=admin_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # BIRTHDAY MANAGEMENT
    # ======================================================

    if data == "admin_birthdays":

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📋 View All Birthdays",
                        callback_data="admin_birthday_list",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📅 Today's Birthdays",
                        callback_data="admin_birthday_today",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Run Birthday Check Now",
                        callback_data="admin_birthday_check",
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
            "🎂 **BIRTHDAY MANAGEMENT**\n\n"
            "Birthday records are stored permanently "
            "in the Melanated AZ SQLite database.\n\n"
            "They are separate from raffle records "
            "and are not removed when a raffle is closed.\n\n"
            "Choose an option:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # ALL BIRTHDAYS
    # ======================================================

    if data == "admin_birthday_list":

        birthdays = get_all_birthdays()

        if not birthdays:

            await query.edit_message_text(
                "📋 **SAVED BIRTHDAYS**\n\n"
                "No birthdays are currently saved.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back",
                                callback_data="admin_birthdays",
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown",
            )

            return

        lines = [
            "📋 **SAVED BIRTHDAYS**",
            "",
        ]

        for birthday_record in birthdays:

            name = (
                birthday_record.get(
                    "display_name"
                )
                or birthday_record.get(
                    "username"
                )
                or str(
                    birthday_record.get(
                        "user_id"
                    )
                )
            )

            lines.append(
                f"🎂 **{birthday_record['birthday']}** — "
                f"{name}"
            )

            if birthday_record.get(
                "chat_id"
            ):

                lines.append(
                    f"   Chat ID: "
                    f"`{birthday_record['chat_id']}`"
                )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_birthdays",
                    )
                ]
            ]
        )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # TODAY'S BIRTHDAYS
    # ======================================================

    if data == "admin_birthday_today":

        today = datetime.now().strftime(
            "%m/%d"
        )

        birthdays = get_birthdays_for_date(
            today
        )

        if not birthdays:

            text = (
                "📅 **TODAY'S BIRTHDAYS**\n\n"
                f"Date: **{today}**\n\n"
                "No birthdays today."
            )

        else:

            lines = [
                "📅 **TODAY'S BIRTHDAYS**",
                f"Date: **{today}**",
                "",
            ]

            for birthday_record in birthdays:

                name = (
                    birthday_record.get(
                        "display_name"
                    )
                    or birthday_record.get(
                        "username"
                    )
                    or str(
                        birthday_record.get(
                            "user_id"
                        )
                    )
                )

                lines.append(
                    f"🎂 {name}"
                )

            text = "\n".join(lines)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_birthdays",
                    )
                ]
            ]
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RUN BIRTHDAY CHECK
    # ======================================================

    if data == "admin_birthday_check":

        from birthday_scheduler import (
            birthday_scheduler,
        )

        await birthday_scheduler(
            context
        )

        await query.message.reply_text(
            "✅ **Birthday check completed.**\n\n"
            "Any birthdays scheduled for today "
            "were processed.",
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RAFFLE ADMIN
    #
    # Keep this callback available for your existing
    # raffle admin system.
    # ======================================================

    if data == "admin_raffle":

        await query.message.reply_text(
            "🎟️ **RAFFLE MANAGEMENT**\n\n"
            "Use the raffle commands from the admin "
            "panel to manage the current raffle.",
            parse_mode="Markdown",
        )

        return
