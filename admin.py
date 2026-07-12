# ==========================================================
# Melanated AZ Bot - Admin Controls
# ==========================================================

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes
)

from config import ADMIN_IDS


# ==========================================================
# ADMIN CHECK
# ==========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS



# ==========================================================
# ADMIN HELP
# ==========================================================

async def admin_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "❌ Admin only command."
        )
        return


    await update.message.reply_text(
        """
👑 Admin Commands

/promote
/demote
/announce
/kick
/ban

More controls coming soon.
"""
    )



# ==========================================================
# ANNOUNCE
# ==========================================================

async def announce(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        return


    if not context.args:

        await update.message.reply_text(
            "Usage:\n/announce message"
        )

        return


    message = " ".join(
        context.args
    )


    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )



# ==========================================================
# REGISTER ADMIN COMMANDS
# ==========================================================

def admin_commands(application):


    application.add_handler(
        CommandHandler(
            "admin",
            admin_help
        )
    )


    application.add_handler(
        CommandHandler(
            "announce",
            announce
        )
    )
