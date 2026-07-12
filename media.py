# ==========================================================
# Melanated AZ Bot
# Media Restriction System
# Blocks Photos and Videos
# Allows GIFs
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes


WARNING_MESSAGE = """
🚫 Media Removed

Photos and videos must be posted using Telegram's Spoiler feature.

To share media:
1️⃣ Select your photo/video
2️⃣ Tap the ⋮ menu
3️⃣ Choose "Hide with Spoiler"
4️⃣ Send it again

GIFs are allowed ✅

Thank you for helping keep Melanated AZ organized.
"""


async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return


    # Allow spoiler protected media

    if message.has_media_spoiler:
        return



    blocked = False



    # Block photos

    if message.photo:

        blocked = True



    # Block videos

    elif message.video:

        blocked = True



    # Block video files sent as documents

    elif message.document:

        mime = message.document.mime_type or ""

        if mime.startswith(
            "video/"
        ):

            blocked = True



    # GIFs are allowed
    # message.animation is ignored



    if blocked:

        try:

            await message.delete()


            await context.bot.send_message(

                chat_id=update.effective_chat.id,

                text=WARNING_MESSAGE,

                reply_to_message_id=message.id

            )


        except Exception as e:

            print(
                f"Media delete error: {e}"
            )
