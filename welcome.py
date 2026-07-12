from telegram import Update
from telegram.ext import ContextTypes

from database import update_member



# ==========================================================
# NEW MEMBER WELCOME
# ==========================================================

async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    for member in update.message.new_chat_members:


        # Ignore the bot joining itself

        if member.is_bot:
            continue


        update_member(
            member.id,
            update.effective_chat.id,
            member.username,
            member.first_name
        )


        await update.message.reply_text(
            f"🔥 Welcome {member.first_name} "
            "to Melanated AZ!\n\n"

            "👋 Please introduce yourself.\n\n"

            "Required:\n"
            "✅ Profile picture\n"
            "✅ Short introduction\n"
            "✅ Respect our community rules\n\n"

            "Type /rules to view guidelines."
        )



# ==========================================================
# PROFILE CHECK
# ==========================================================

async def profile_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    user = update.effective_user


    try:

        photos = await context.bot.get_user_profile_photos(
            user.id,
            limit=1
        )


        if photos.total_count == 0:


            await update.message.reply_text(
                f"👋 {user.first_name}, "
                "please add a profile picture "
                "to complete your community profile."
            )


    except Exception:

        pass



# ==========================================================
# INTRO COMMAND
# ==========================================================

async def intro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:


        await update.message.reply_text(
            "Usage:\n"
            "/intro Your introduction"
        )

        return



    text = " ".join(
        context.args
    )


    await update.message.reply_text(
        "✅ Introduction saved!\n\n"
        f"{text}"
    )
