```python
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
    get_active_raffle,
    get_pending_raffle,
    get_pending_entries,
    get_approved_entries,
    get_all_birthdays,
    get_birthdays_for_date,
)

logger = logging.getLogger(__name__)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):
    try:
        return int(user_id) in [int(x) for x in ADMIN_IDS]
    except Exception:
        return False


# ==========================================================
# MAIN ADMIN KEYBOARD
# ==========================================================

def admin_main_keyboard():

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
# RAFFLE ADMIN KEYBOARD
# ==========================================================

def raffle_admin_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Start New Raffle",
                    callback_data="admin_raffle_start",
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Raffle Status",
                    callback_data="admin_raffle_status",
                ),
                InlineKeyboardButton(
                    "📋 Entries",
                    callback_data="admin_raffle_entries",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⏳ Pending Payments",
                    callback_data="admin_raffle_pending",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎲 Draw Raffle",
                    callback_data="admin_raffle_draw",
                ),
                InlineKeyboardButton(
                    "🔄 Reroll",
                    callback_data="admin_raffle_reroll",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎁 Bonus Entry",
                    callback_data="admin_raffle_bonus",
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Remove Entry",
                    callback_data="admin_raffle_remove",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel Raffle",
                    callback_data="admin_raffle_cancel",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Admin Panel",
                    callback_data="admin_back",
                )
            ],
        ]
    )


# ==========================================================
# BIRTHDAY ADMIN KEYBOARD
# ==========================================================

def birthday_admin_keyboard():

    return InlineKeyboardMarkup(
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
                "❌ Admins only."
            )

        return

    await update.effective_message.reply_text(
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        "Welcome to the administrator panel.\n\n"
        "Select an option below.",
        reply_markup=admin_main_keyboard(),
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

    if not is_admin(query.from_user.id):

        await query.answer(
            "Not authorized.",
            show_alert=True,
        )

        return

    await query.answer()

    data = query.data or ""

    # ======================================================
    # MAIN ADMIN PANEL
    # ======================================================

    if data == "admin_back":

        await query.edit_message_text(
            "👑 **MELANATED AZ ADMIN PANEL**\n\n"
            "Welcome to the administrator panel.\n\n"
            "Select an option below.",
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RAFFLE MANAGEMENT
    # ======================================================

    if data == "admin_raffle":

        active = get_active_raffle()
        pending = get_pending_raffle()

        lines = [
            "🎟️ **RAFFLE MANAGEMENT**",
            "",
        ]

        if active:

            lines.extend(
                [
                    "🟢 **Active Raffle**",
                    f"Prize: **{active.get('prize', 'Unknown')}**",
                    f"Entry: **{active.get('price', 'Unknown')}**",
                    f"Raffle ID: `{active.get('id')}`",
                    "",
                ]
            )

        else:

            lines.extend(
                [
                    "⚪ **No active raffle**",
                    "",
                ]
            )

        if pending:

            lines.extend(
                [
                    "🟡 **Pending Raffle**",
                    f"Prize: **{pending.get('prize', 'Unknown')}**",
                    f"Entry: **{pending.get('price', 'Unknown')}**",
                    f"Raffle ID: `{pending.get('id')}`",
                    "",
                ]
            )

        await query.edit_message_text(
            "\n".join(lines)
            + "Choose a raffle management option:",
            reply_markup=raffle_admin_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # START RAFFLE
    # ======================================================

    if data == "admin_raffle_start":

        await query.edit_message_text(
            "➕ **START A NEW RAFFLE**\n\n"
            "Use the `/startraffle` command to begin "
            "creating a new raffle.\n\n"
            "Example:\n"
            "`/startraffle`\n\n"
            "The bot will walk you through the setup "
            "process and send the raffle for approval.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back to Raffle Management",
                            callback_data="admin_raffle",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Admin Panel",
                            callback_data="admin_back",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RAFFLE STATUS
    # ======================================================

    if data == "admin_raffle_status":

        active = get_active_raffle()
        pending = get_pending_raffle()

        lines = [
            "📊 **RAFFLE STATUS**",
            "",
        ]

        if active:

            entries = get_approved_entries(
                active["id"]
            )

            lines.extend(
                [
                    "🟢 **ACTIVE RAFFLE**",
                    "",
                    f"🎁 Prize: **{active.get('prize')}**",
                    f"💵 Entry: **{active.get('price')}**",
                    f"🎟️ Approved Entries: **{len(entries)}**",
                    f"🆔 Raffle ID: `{active.get('id')}`",
                    f"⏰ Expires: `{active.get('expires_at')}`",
                ]
            )

        else:

            lines.append(
                "⚪ There is currently no active raffle."
            )

        if pending:

            lines.extend(
                [
                    "",
                    "🟡 **PENDING RAFFLE**",
                    "",
                    f"🎁 Prize: **{pending.get('prize')}**",
                    f"💵 Entry: **{pending.get('price')}**",
                    f"🆔 Raffle ID: `{pending.get('id')}`",
                ]
            )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh",
                            callback_data="admin_raffle_status",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Raffle Management",
                            callback_data="admin_raffle",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RAFFLE ENTRIES
    # ======================================================

    if data == "admin_raffle_entries":

        active = get_active_raffle()

        if not active:

            text = (
                "📋 **RAFFLE ENTRIES**\n\n"
                "There is no active raffle."
            )

        else:

            entries = get_approved_entries(
                active["id"]
            )

            if not entries:

                text = (
                    "📋 **RAFFLE ENTRIES**\n\n"
                    "No approved entries yet."
                )

            else:

                lines = [
                    "📋 **APPROVED RAFFLE ENTRIES**",
                    "",
                ]

                for number, entry in enumerate(
                    entries,
                    start=1,
                ):

                    name = (
                        entry.get("display_name")
                        or entry.get("username")
                        or str(entry.get("user_id"))
                    )

                    lines.append(
                        f"{number}. {name}"
                    )

                lines.extend(
                    [
                        "",
                        f"🎟️ Total: **{len(entries)}**",
                    ]
                )

                text = "\n".join(lines)

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh",
                            callback_data="admin_raffle_entries",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Raffle Management",
                            callback_data="admin_raffle",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # PENDING PAYMENTS
    # ======================================================

    if data == "admin_raffle_pending":

        pending_entries = get_pending_entries()

        if not pending_entries:

            text = (
                "⏳ **PENDING PAYMENTS**\n\n"
                "There are no pending payment entries."
            )

        else:

            lines = [
                "⏳ **PENDING PAYMENTS**",
                "",
            ]

            for entry in pending_entries:

                name = (
                    entry.get("display_name")
                    or entry.get("username")
                    or str(entry.get("user_id"))
                )

                payment = (
                    entry.get("payment_method")
                    or "Unknown"
                )

                lines.append(
                    f"🎟️ Entry #{entry.get('id')}"
                )
                lines.append(
                    f"👤 {name}"
                )
                lines.append(
                    f"💳 {payment}"
                )
                lines.append("")

            text = "\n".join(lines)

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh",
                            callback_data="admin_raffle_pending",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Raffle Management",
                            callback_data="admin_raffle",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # COMMAND HELP BUTTONS
    #
    # These display the existing raffle commands rather
    # than pretending a callback can execute a command.
    # ======================================================

    command_help = {

        "admin_raffle_draw": (
            "🎲 **DRAW RAFFLE**\n\n"
            "Use:\n"
            "`/draw`\n\n"
            "This will draw from the approved entries "
            "for the active raffle."
        ),

        "admin_raffle_reroll": (
            "🔄 **REROLL RAFFLE**\n\n"
            "Use:\n"
            "`/reroll`\n\n"
            "This will reroll the raffle winner "
            "according to your raffle system."
        ),

        "admin_raffle_bonus": (
            "🎁 **BONUS ENTRY**\n\n"
            "Use:\n"
            "`/bonusentry`\n\n"
            "Follow the bot's instructions to add "
            "a bonus entry."
        ),

        "admin_raffle_remove": (
            "🗑️ **REMOVE ENTRY**\n\n"
            "Use:\n"
            "`/removeentry`\n\n"
            "Follow the bot's instructions to remove "
            "a raffle entry."
        ),

        "admin_raffle_cancel": (
            "❌ **CANCEL RAFFLE**\n\n"
            "Use:\n"
            "`/cancelraffle`\n\n"
            "This will cancel the current active raffle "
            "according to the raffle system."
        ),
    }

    if data in command_help:

        await query.edit_message_text(
            command_help[data],
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Raffle Management",
                            callback_data="admin_raffle",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Admin Panel",
                            callback_data="admin_back",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # BIRTHDAY MANAGEMENT
    # ======================================================

    if data == "admin_birthdays":

        await query.edit_message_text(
            "🎂 **BIRTHDAY MANAGEMENT**\n\n"
            "Birthday records are stored permanently "
            "in the Melanated AZ SQLite database.\n\n"
            "Choose an option:",
            reply_markup=birthday_admin_keyboard(),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # LIST BIRTHDAYS
    # ======================================================

    if data == "admin_birthday_list":

        birthdays = get_all_birthdays()

        if not birthdays:

            text = (
                "📋 **BIRTHDAY LIST**\n\n"
                "No birthdays are currently saved."
            )

        else:

            lines = [
                "📋 **SAVED BIRTHDAYS**",
                "",
            ]

            for birthday in birthdays:

                name = (
                    birthday.get("display_name")
                    or birthday.get("username")
                    or str(birthday.get("user_id"))
                )

                lines.append(
                    f"🎂 **{birthday.get('birthday')}** — {name}"
                )

                if birthday.get("chat_id") is not None:

                    lines.append(
                        f"   Chat ID: `{birthday.get('chat_id')}`"
                    )

            text = "\n".join(lines)

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh",
                            callback_data="admin_birthday_list",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Birthday Management",
                            callback_data="admin_birthdays",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # TODAY'S BIRTHDAYS
    # ======================================================

    if data == "admin_birthday_today":

        today = datetime.now().strftime("%m/%d")

        birthdays = get_birthdays_for_date(today)

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

            for birthday in birthdays:

                name = (
                    birthday.get("display_name")
                    or birthday.get("username")
                    or str(birthday.get("user_id"))
                )

                lines.append(
                    f"🎂 {name}"
                )

            text = "\n".join(lines)

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh",
                            callback_data="admin_birthday_today",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Birthday Management",
                            callback_data="admin_birthdays",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",
        )

        return

    # ======================================================
    # RUN BIRTHDAY CHECK
    # ======================================================

    if data == "admin_birthday_check":

        try:

            from birthday_scheduler import (
                birthday_scheduler,
            )

            await birthday_scheduler(context)

            await query.edit_message_text(
                "✅ **BIRTHDAY CHECK COMPLETED**\n\n"
                "Any birthdays scheduled for today "
                "have been processed.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Birthday Management",
                                callback_data="admin_birthdays",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⬅️ Main Admin Panel",
                                callback_data="admin_back",
                            )
                        ],
                    ]
                ),
                parse_mode="Markdown",
            )

        except Exception:

            logger.exception(
                "Birthday check failed"
            )

            await query.edit_message_text(
                "❌ **Birthday check failed.**\n\n"
                "Check the Render logs for details.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Birthday Management",
                                callback_data="admin_birthdays",
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown",
            )

        return

    # ======================================================
    # UNKNOWN ADMIN CALLBACK
    # ======================================================

    logger.warning(
        "Unhandled admin callback: %s",
        data,
    )

    await query.answer(
        "That admin option is not available.",
        show_alert=True,
    )
```
