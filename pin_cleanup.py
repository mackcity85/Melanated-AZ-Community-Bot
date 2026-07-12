import asyncio
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    save_pin,
    get_old_pins,
    remove_pin
)



# ==========================================================
# ADMIN CHECK
# ==========================================================

async def check_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    admins = await context.bot.get_chat_administrators(
        update.effective_chat.id
    )


    for admin in admins:

        if admin.user.id == update.effective_user.id:

            return True


    return False



# ==========================================================
# PIN MESSAGE
# ==========================================================

async def pinmessage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await check_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return


    if not context.args:

        await update.message.reply_text(
            "Usage:\n/pinmessage Your announcement"
        )

        return


    text = " ".join(
        context.args
    )


    message = await update.message.reply_text(
        text
    )


    await message.pin()


    save_pin(
        update.effective_chat.id,
        message.message_id,
        text
    )


    await update.message.reply_text(
        "📌 Message pinned and tracked."
    )



# ==========================================================
# REMOVE OLD PINS
# ==========================================================

async def unpinold(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await check_admin(update, context):

        await update.message.reply_text(
            "❌ Admins only."
        )

        return


    old_pins = get_old_pins(
        datetime.now() - timedelta(days=90)
    )


    removed = 0


    for pin in old_pins:

        chat_id = pin[0]
        message_id = pin[1]


        try:

            await context.bot.unpin_chat_message(
                chat_id=chat_id,
                message_id=message_id
            )


            remove_pin(
                message_id
            )


            removed += 1


        except Exception:

            pass



    await update.message.reply_text(
        f"📌 Removed {removed} old pins."
    )



# ==========================================================
# AUTOMATIC CLEANUP TASK
# ==========================================================

async def pin_cleanup_task(
    application
):

    while True:

        await asyncio.sleep(
            86400
        )


        old_pins = get_old_pins(
            datetime.now() - timedelta(days=90)
        )


        for pin in old_pins:

            try:

                await application.bot.unpin_chat_message(
                    chat_id=pin[0],
                    message_id=pin[1]
                )


                remove_pin(
                    pin[1]
                )


            except Exception:

                pass
