# ==========================================================
# Melanated AZ Bot
# moderation.py
# Media Spoiler Protection
# ==========================================================

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


# ==========================================================
# MEDIA SPOILER CHECK
# ==========================================================

async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message


    if not message:
        return


    # --------------------------
    # Allow GIFS
    # --------------------------

    if message.animation:

        return


    # --------------------------
    # Check PHOTO
    # --------------------------

    media_found = False


    if message.photo:

        media_found = True


    # --------------------------
    # Check VIDEO
    # --------------------------

    if message.video:

        media_found = True



    if not media_found:

        return



    # --------------------------
    # Allow spoiler media
    # --------------------------

    if message.has_media_spoiler:

        return



    # --------------------------
    # Delete bad media
    # --------------------------

    try:

        await message.delete()


    except Exception as e:

        logger.error(
            f"Could not delete media: {e}"
        )



    # --------------------------
    # Warning message
    # --------------------------

    warning = await context.bot.send_message(

        chat_id=update.effective_chat.id,

        text=
        """
⚠️ MEDIA REMOVED

Photos and videos must be sent with the Telegram SPOILER option enabled.

Please resend using:
📷 Attach Media
➡️ Select Photo/Video
➡️ Tap ⋮
➡️ Enable "Hide with Spoiler"

Thank you for keeping Melanated AZ safe.
"""
    )


    # --------------------------
    # Remove warning after 30 sec
    # --------------------------

    await asyncio.sleep(30)


    try:

        await warning.delete()


    except Exception:

        pass
