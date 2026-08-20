# ==========================================================
# Melanated AZ Bot
# raffle_buttons.py
# Raffle Payment & Approval Buttons
# ==========================================================

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from config import (
    ADMIN_IDS,
    RAFFLE_ENTRY_COST,
    CASHAPP_TAG,
    CASHAPP_URL,
    ZELLE_PHONE
)

from raffle_database import (
    get_active_raffle,
    add_raffle_entry,
    get_entry,
    approve_entry,
    deny_entry
)


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ==========================================================
# PAYMENT MENU
# ==========================================================

def payment_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "💵 Pay with Cash App",
                callback_data="raffle_cashapp"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Pay with Zelle",
                callback_data="raffle_zelle"
            )
        ],

        [
            InlineKeyboardButton(
                "✅ I've Paid",
                callback_data="raffle_paid"
            )
        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ==========================================================
# ADMIN APPROVAL BUTTONS
# ==========================================================

def approval_keyboard(entry_id):

    keyboard = [

        [

            InlineKeyboardButton(
                "✅ APPROVE",
                callback_data=f"approve:{entry_id}"
            ),

            InlineKeyboardButton(
                "❌ DENY",
                callback_data=f"deny:{entry_id}"
            )

        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ==========================================================
# BUTTON HANDLER
# ==========================================================

async def raffle_button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data


    # ======================================================
    # CASH APP
    # ======================================================

    if data == "raffle_cashapp":

        await query.message.reply_text(

f"""
💵 CASH APP PAYMENT

🎟️ Raffle Entry:
${RAFFLE_ENTRY_COST:.2f}

Send payment to:

{CASHAPP_TAG}

Tap the button below after you send the payment.
""",

            reply_markup=InlineKeyboardMarkup(

                [

                    [

                        InlineKeyboardButton(
                            "💵 Open Cash App",
                            url=CASHAPP_URL
                        )

                    ],

                    [

                        InlineKeyboardButton(
                            "✅ I've Paid",
                            callback_data="raffle_paid_cashapp"
                        )

                    ]

                ]

            )

        )

        return


    # ======================================================
    # ZELLE
    # ======================================================

    if data == "raffle_zelle":

        await query.message.reply_text(

f"""
💳 ZELLE PAYMENT

🎟️ Raffle Entry:
${RAFFLE_ENTRY_COST:.2f}

Send payment to:

📱 {ZELLE_PHONE}

After sending the payment, tap:

✅ I've Paid
""",

            reply_markup=InlineKeyboardMarkup(

                [

                    [

                        InlineKeyboardButton(
                            "✅ I've Paid",
                            callback_data="raffle_paid_zelle"
                        )

                    ]

                ]

            )

        )

        return


    # ======================================================
    # CASH APP PAID
    # ======================================================

    if data == "raffle_paid_cashapp":

        await create_pending_entry(

            query,

            context,

            "cashapp"

        )

        return


    # ======================================================
    # ZELLE PAID
    # ======================================================

    if data == "raffle_paid_zelle":

        await create_pending_entry(

            query,

            context,

            "zelle"

        )

        return


    # ======================================================
    # APPROVE
    # ======================================================

    if data.startswith("approve:"):

        if not is_admin(
            query.from_user.id
        ):

            await query.answer(
                "❌ Admin only.",
                show_alert=True
            )

            return


        try:

            entry_id = int(
                data.split(":")[1]
            )

        except (ValueError, IndexError):

            await query.message.reply_text(
                "❌ Invalid entry ID."
            )

            return


        entry = get_entry(
            entry_id
        )


        if not entry:

            await query.message.reply_text(
                "❌ Entry not found."
            )

            return


        success = approve_entry(
            entry_id,
            query.from_user.id
        )


        if not success:

            await query.message.reply_text(
                "⚠️ This entry has already been processed."
            )

            return


        await query.edit_message_reply_markup(
            reply_markup=None
        )


        await query.message.reply_text(

f"""
✅ RAFFLE ENTRY APPROVED

🎟️ Entry:
#{entry_id}

👤 User:
{entry["display_name"]}

💳 Payment:
{entry["payment_method"].upper()}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}
"""
        )


        # --------------------------------------------------
        # Notify Member
        # --------------------------------------------------

        try:

            raffle = get_active_raffle()

            prize = (
                raffle[1]
                if raffle
                else "Current Raffle"
            )


            await context.bot.send_message(

                chat_id=entry["user_id"],

                text=f"""
🎉 YOUR RAFFLE ENTRY IS APPROVED!

🏆 Prize:
{prize}

🎟️ Entry:
#{entry_id}

💳 Payment:
{entry["payment_method"].upper()}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

✅ You are officially entered!

Good luck! 🔥👑
"""
            )

        except Exception as e:

            print(
                f"Member approval notification failed: {e}"
            )

        return


    # ======================================================
    # DENY
    # ======================================================

    if data.startswith("deny:"):

        if not is_admin(
            query.from_user.id
        ):

            await query.answer(
                "❌ Admin only.",
                show_alert=True
            )

            return


        try:

            entry_id = int(
                data.split(":")[1]
            )

        except (ValueError, IndexError):

            await query.message.reply_text(
                "❌ Invalid entry ID."
            )

            return


        entry = get_entry(
            entry_id
        )


        if not entry:

            await query.message.reply_text(
                "❌ Entry not found."
            )

            return


        success = deny_entry(
            entry_id,
            query.from_user.id
        )


        if not success:

            await query.message.reply_text(
                "⚠️ This entry has already been processed."
            )

            return


        await query.edit_message_reply_markup(
            reply_markup=None
        )


        await query.message.reply_text(

f"""
❌ RAFFLE ENTRY DENIED

🎟️ Entry:
#{entry_id}

👤 User:
{entry["display_name"]}
"""
        )


        # --------------------------------------------------
        # Notify Member
        # --------------------------------------------------

        try:

            await context.bot.send_message(

                chat_id=entry["user_id"],

                text="""
❌ YOUR RAFFLE ENTRY WAS NOT APPROVED.

Please contact an administrator if you believe this was an error.
"""
            )

        except Exception as e:

            print(
                f"Member denial notification failed: {e}"
            )

        return


# ==========================================================
# CREATE PENDING ENTRY
# ==========================================================

async def create_pending_entry(
    query,
    context,
    payment_method
):

    raffle = get_active_raffle()


    if not raffle:

        await query.message.reply_text(
            "❌ There is no active raffle."
        )

        return


    user = query.from_user


    username = (

        f"@{user.username}"

        if user.username

        else user.first_name

    )


    display_name = user.full_name


    # ------------------------------------------------------
    # Create entry
    # ------------------------------------------------------

    entry_id = add_raffle_entry(

        raffle[0],

        user.id,

        username,

        display_name,

        payment_method

    )


    if entry_id is None:

        await query.message.reply_text(

"""
⚠️ You already have an active entry
for this raffle.

Your previous payment is either pending
approval or has already been approved.
"""
        )

        return


    # ------------------------------------------------------
    # Tell member
    # ------------------------------------------------------

    await query.message.reply_text(

f"""
✅ PAYMENT SUBMITTED

👤 Name:
{display_name}

🎟️ Entry:
#{entry_id}

💳 Payment:
{payment_method.upper()}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

⏳ Status:
WAITING FOR ADMIN APPROVAL

You will receive a message when your
entry has been approved.
"""
    )


    # ------------------------------------------------------
    # Admin notification
    # ------------------------------------------------------

    admin_message = f"""
🔔 NEW RAFFLE PAYMENT

🏆 Prize:
{raffle[1]}

🎟️ Entry:
#{entry_id}

👤 Name:
{display_name}

📱 Username:
{username}

🆔 Telegram ID:
{user.id}

💳 Payment Method:
{payment_method.upper()}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

⏳ Status:
PENDING APPROVAL
"""


    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(

                chat_id=admin_id,

                text=admin_message,

                reply_markup=approval_keyboard(
                    entry_id
                )

            )

        except Exception as e:

            print(
                f"Admin notification failed: {e}"
            )
