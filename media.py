# ==========================================================
# Melanated AZ Bot
# media.py
# Photo / Video Spoiler Protection
# ==========================================================

import asyncio

from telegram import Update
from telegram.ext import ContextTypes


WARNING_MESSAGE = """
🚫 Media Removed

Photos and videos must use Telegram Spoiler.

How to send with Spoiler:

1️⃣ Select your photo/video
2️⃣ Tap ⋮ menu
3️⃣ Choose "Hide with Spoiler"
4️⃣ Send again

Thank you for helping keep Melanated AZ organized.
"""


async def remove_warning(message):

    await asyncio.sleep(30)

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



    # Photo

    if message.photo:

        blocked = True



    # Video

    if message.video:

        blocked = True



    if not blocked:
        return



    try:

        # Send warning first

        warning = await context.bot.send_message(
            chat_id=message.chat.id,
            text=WARNING_MESSAGE
        )


        # Delete media

        await message.delete()



        # Delete warning after 30 seconds

        asyncio.create_task(
            remove_warning(warning)
        )


    except Exception as e:

        print(
            f"Media restriction error: {e}"
        )
