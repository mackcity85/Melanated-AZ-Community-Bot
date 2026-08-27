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
)

logger = logging.getLogger(**name**)

# ==========================================================

# ADMIN CHECK

# ==========================================================

def is_admin(user_id):

```
try:
    return int(user_id) in [int(x) for x in ADMIN_IDS]
except Exception:
    return False
```

# ==========================================================

# MAIN ADMIN KEYBOARD

# ==========================================================

def admin_main_keyboard():

```
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
    ]
)
```

# ==========================================================

# RAFFLE ADMIN KEYBOARD

# ==========================================================

def raffle_admin_keyboard():

```
return InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🎟️ Start Raffle",
                callback_data="admin_raffle_start",
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Raffle Status",
                callback_data="admin_raffle_status",
            ),
            InlineKeyboardButton(
                "📋 View Entries",
                callback_data="admin_raffle_entries",
            )
        ],
        [
            InlineKeyboardButton(
                "⏳ Pending Payments",
                callback_data="admin_raffle_pending",
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
                "🎲 Draw Raffle",
                callback_data="admin_raffle_draw",
            ),
            InlineKeyboardButton(
                "🔄 Reroll",
                callback_data="admin_raffle_reroll",
            )
        ],
        [
            InlineKeyboardButton(
                "🎁 Bonus Entry",
                callback_data="admin_raffle_bonus",
            ),
            InlineKeyboardButton(
                "🗑️ Remove Entry",
                callback_data="admin_raffle_remove",
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
```

# ==========================================================

# BIRTHDAY ADMIN KEYBOARD

# ==========================================================

def birthday_admin_keyboard():

```
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
```

# ==========================================================

# ADMIN MENU

# ==========================================================

async def admin_menu(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
user = update.effective_user

if not user or not is_admin(user.id):

    if update.effective_message:
        await update.effective_message.reply_text(
            "❌ Admins only."
        )

    return

await update.effective_message.reply_text(
    "👑 **MELANATED AZ ADMIN PANEL**\n\n"
    "Select an option below.",
    reply_markup=admin_main_keyboard(),
    parse_mode="Markdown",
)
```

# ==========================================================

# ADMIN BUTTON HANDLER

# ==========================================================

async def admin_button(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):

```
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
# MAIN ADMIN MENU
# ======================================================

if data == "admin_back":

    await query.edit_message_text(
        "👑 **MELANATED AZ ADMIN PANEL**\n\n"
        "Select an option below.",
        reply_markup=admin_main_keyboard(),
        parse_mode="Markdown",
    )

    return


# ======================================================
# RAFFLE MANAGEMENT
# ======================================================

if data == "admin_raffle":

    await query.edit_message_text(
        "🎟️ **RAFFLE MANAGEMENT**\n\n"
        "Manage the Melanated AZ raffle system.\n\n"
        "Choose an option below:",
        reply_markup=raffle_admin_keyboard(),
        parse_mode="Markdown",
    )

    return


# ======================================================
# RAFFLE START
#
# The actual /startraffle command remains handled by
# raffle.py. The button provides instructions and
# directs the admin to use the command.
# ======================================================

if data == "admin_raffle_start":

    await query.edit_message_text(
        "🎟️ **START A NEW RAFFLE**\n\n"
        "Use the command:\n\n"
        "`/startraffle`\n\n"
        "The bot will walk you through the raffle setup.\n\n"
        "Example:\n"
        "`$100 Cash Prize | $5`",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# RAFFLE STATUS
# ======================================================

if data == "admin_raffle_status":

    await query.edit_message_text(
        "📊 **RAFFLE STATUS**\n\n"
        "Use:\n\n"
        "`/rafflestatus`\n\n"
        "This will show the current raffle status.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# RAFFLE ENTRIES
# ======================================================

if data == "admin_raffle_entries":

    await query.edit_message_text(
        "📋 **RAFFLE ENTRIES**\n\n"
        "Use:\n\n"
        "`/entries`\n\n"
        "This will display the approved entries "
        "for the current raffle.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# PENDING PAYMENTS
# ======================================================

if data == "admin_raffle_pending":

    await query.edit_message_text(
        "⏳ **PENDING PAYMENTS**\n\n"
        "Use:\n\n"
        "`/pending`\n\n"
        "This will show raffle entries "
        "waiting for payment verification.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# CANCEL RAFFLE
# ======================================================

if data == "admin_raffle_cancel":

    await query.edit_message_text(
        "❌ **CANCEL RAFFLE**\n\n"
        "Use:\n\n"
        "`/cancelraffle`\n\n"
        "This will cancel the current active raffle.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# DRAW RAFFLE
# ======================================================

if data == "admin_raffle_draw":

    await query.edit_message_text(
        "🎲 **DRAW RAFFLE**\n\n"
        "Use:\n\n"
        "`/draw`\n\n"
        "The bot will select a winner "
        "from the approved entries.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# REROLL
# ======================================================

if data == "admin_raffle_reroll":

    await query.edit_message_text(
        "🔄 **REROLL WINNER**\n\n"
        "Use:\n\n"
        "`/reroll`\n\n"
        "This will reroll the raffle winner.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# BONUS ENTRY
# ======================================================

if data == "admin_raffle_bonus":

    await query.edit_message_text(
        "🎁 **BONUS ENTRY**\n\n"
        "Use:\n\n"
        "`/bonusentry`\n\n"
        "This allows an admin to add a bonus "
        "raffle entry.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )

    return


# ======================================================
# REMOVE ENTRY
# ======================================================

if data == "admin_raffle_remove":

    await query.edit_message_text(
        "🗑️ **REMOVE RAFFLE ENTRY**\n\n"
        "Use:\n\n"
        "`/removeentry`\n\n"
        "This allows an admin to remove "
        "a raffle entry.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Raffle Management",
                        callback_data="admin_raffle",
                    )
                ]
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
# LIST ALL BIRTHDAYS
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

        for birthday_record in birthdays:

            name = (
                birthday_record.get("display_name")
                or birthday_record.get("username")
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

            if birthday_record.get("chat_id"):

                lines.append(
                    f"   Chat ID: "
                    f"`{birthday_record['chat_id']}`"
                )

        text = "\n".join(lines)

    await query.edit_message_text(
        text,
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

        for birthday_record in birthdays:

            name = (
                birthday_record.get("display_name")
                or birthday_record.get("username")
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

    await query.edit_message_text(
        text,
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


# ======================================================
# RUN BIRTHDAY CHECK
# ======================================================

if data == "admin_birthday_check":

    try:

        from birthday_scheduler import (
            birthday_scheduler,
        )

        await birthday_scheduler(context)

        await query.message.reply_text(
            "✅ **Birthday check completed.**\n\n"
            "Any birthdays scheduled for today "
            "were processed.",
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Birthday check failed"
        )

        await query.message.reply_text(
            "❌ Birthday check failed.\n\n"
            "Check the Render logs for details."
        )

    return
```
