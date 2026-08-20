# ==========================================================
# Melanated AZ Bot
# raffle_buttons.py
# Raffle Inline Button Handlers
# ==========================================================

from telegram import Update

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
    # ZELLE BUTTON
    # ======================================================

    if data == "raffle_zelle":

        await query.message.reply_text(

f"""
💳 ZELLE PAYMENT

Send:

💰 ${RAFFLE_ENTRY_COST:.2f}

To:

📱 {ZELLE_PHONE}

Once you've sent the payment, return here and tap:

✅ I've Paid
"""
        )

        return


    # ======================================================
    # I'VE PAID BUTTON
    # ======================================================

    if data == "raffle_paid":

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


        # --------------------------------------------------
        # Create pending entry
        # --------------------------------------------------

        entry_id = add_raffle_entry(

            raffle[0],

            user.id,

            username,

            display_name,

            "UNKNOWN"

        )


        if entry_id is None:

            await query.message.reply_text(

"""
⚠️ You already have a pending or approved
entry for this raffle.

Please wait for approval.
"""
            )

            return


        await query.message.reply_text(

f"""
✅ PAYMENT SUBMITTED

👤 Name:
{display_name}

🎟️ Entry:
#{entry_id}

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

⏳ Status:
PENDING APPROVAL

An administrator has been notified.
"""
        )


        # --------------------------------------------------
        # Notify Admins
        # --------------------------------------------------

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

💳 Payment:
MEMBER CONFIRMED PAYMENT

💰 Amount:
${RAFFLE_ENTRY_COST:.2f}

⏳ Status:
PENDING APPROVAL
"""


        for admin_id in ADMIN_IDS:

            try:

                await context.bot.send_message(

                    chat_id=admin_id,

                    text=admin_message

                )

            except Exception as e:

                print(
                    f"Admin notification failed: {e}"
                )

        return


    # ======================================================
    # APPROVE BUTTON
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

        except ValueError:

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


        await query.message.reply_text(

f"""
✅ RAFFLE ENTRY APPROVED

🎟️ Entry:
#{entry_id}

👤 User:
{entry["display_name"] or entry["username"]}

💳 Payment:
{entry["payment_method"].upper()}
"""
        )


        # --------------------------------------------------
        # Notify Member
        # --------------------------------------------------

        try:

            await context.bot.send_message(

                chat_id=entry["user_id"],

                text=f"""
🎉 YOUR RAFFLE ENTRY HAS BEEN APPROVED!

🏆 Prize:
{entry["raffle_id"]}

🎟️ Entry:
#{entry["entry_number"]}

💳 Payment:
{entry["payment_method"].upper()}

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
    # DENY BUTTON
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

        except ValueError:

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


        await query.message.reply_text(

f"""
❌ RAFFLE ENTRY DENIED

🎟️ Entry:
#{entry_id}

👤 User:
{entry["display_name"] or entry["username"]}
"""
        )


        # --------------------------------------------------
        # Notify Member
        # --------------------------------------------------

        try:

            await context.bot.send_message(

                chat_id=entry["user_id"],

                text="""
❌ YOUR RAFFLE PAYMENT WAS NOT APPROVED.

Please contact an administrator if you believe this was an error.
"""
            )

        except Exception as e:

            print(
                f"Member denial notification failed: {e}"
            )

        return
