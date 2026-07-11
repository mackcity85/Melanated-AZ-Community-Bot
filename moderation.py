from telegram import Update
from telegram.ext import ContextTypes


WARNING_MESSAGE = """
⚠️ Media Removed

Melanated AZ requires all photos and videos to be sent using Telegram's:

👁 Hide With Spoiler

Please resend your photo/video with the spoiler option enabled.

Thank you for helping keep the community comfortable. ❤️👑
"""


async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return


    # Only check photos and videos
    has_media = (
        message.photo
        or message.video
    )


    if has_media:

        # Allow spoiler media
        if not message.has_media_spoiler:

            try:

                await message.delete()

                await context.bot.send_message(
                    chat_id=message.chat.id,
                    text=WARNING_MESSAGE
                )


            except Exception as e:

                print(
                    f"Media moderation error: {e}"
                )
