# ==========================================================
# Melanated AZ Bot
# Media Restriction System
# Photos/Videos Require Spoiler
# GIFs Allowed
# ==========================================================

import asyncio

from telegram import Update
from telegram.ext import ContextTypes


WARNING_MESSAGE = """
🚫 Media Removed

Photos and videos must be posted using Telegram Spoiler.

How to send:

1️⃣ Select your photo/video
2️⃣ Tap the ⋮ menu
3️⃣ Select "Hide with Spoiler"
4️⃣ Send again

GIFs are allowed ✅

Thank you for helping keep Melanated AZ organized.
"""


async def remove_warning(
    message
):

    await asyncio.sleep(
        30
    )

    try:

        await message.delete()

    except Exception:

        pass



async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message


    if not message:
        return



    # Allow spoiler media

    if message.has_media_spoiler:

        return



    blocked = False



    # Photos

    if message.photo:

        blocked = True



    # Videos

    elif message.video:

        blocked = True



    # Video files sent as documents

    elif message.document:

        mime = (
            message.document.mime_type
            or ""
        )


        if mime.startswith(
            "video/"
        ):

            blocked = True



    # GIFs are allowed
    # Animations are ignored



    if blocked:


        try:

            # Delete media

            await message.delete()



            # Send warning

            warning = await context.bot.send_message(

                chat_id=update.effective_chat.id,

                text=WARNING_MESSAGE

            )



            # Delete warning after 30 seconds

            asyncio.create_task(

                remove_warning(
                    warning
                )

            )


        except Exception as e:


            print(
                f"Media restriction error: {e}"
            )
