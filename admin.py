import logging

from telegram import Update
from telegram.ext import ContextTypes



# ==========================
# ADMIN CHECK
# ==========================

async def is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        member = await context.bot.get_chat_member(

            chat_id=update.effective_chat.id,

            user_id=update.effective_user.id

        )


        return member.status in [

            "administrator",

            "creator"

        ]


    except Exception as e:

        logging.warning(

            "Admin check failed: %s",

            e

        )

        return False



# ==========================
# GET CHAT ID
# ==========================

async def get_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "GETID COMMAND RECEIVED"
    )

    await update.message.reply_text(
        f"🆔 Chat ID:\n\n{update.effective_chat.id}"
    )



# ==========================
# ANNOUNCEMENT COMMAND
# ==========================

async def announce(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):


    if not await is_admin(
        update,
        context
    ):

        await update.message.reply_text(

            "❌ Admins only."

        )

        return



    if not context.args:


        await update.message.reply_text(

            "Usage:\n"
            "/announce Your message here"

        )

        return



    message = " ".join(

        context.args

    )


    await context.bot.send_message(

        chat_id=update.effective_chat.id,

        text=(

            "📢 Community Announcement\n\n"

            f"{message}"

        )

    )


    logging.info(

        "Announcement sent by %s",

        update.effective_user.id

    )
