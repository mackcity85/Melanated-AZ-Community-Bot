from telegram import Update
from telegram.ext import ContextTypes


WARNING_MESSAGE = """
⚠️ Media Removed

Melanated AZ requires all photos and videos to be sent using:

👁 Hide With Spoiler

Please resend your media with the spoiler option enabled.
"""


async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return


    print("MEDIA RECEIVED")
    print("Photo:", bool(message.photo))
    print("Video:", bool(message.video))
    print("Spoiler:", message.has_media_spoiler)


    if message.photo or message.video:

        if not message.has_media_spoiler:

            try:
                await message.delete()

                await context.bot.send_message(
                    chat_id=message.chat.id,
                    text=WARNING_MESSAGE
                )

                print("MEDIA DELETED")

            except Exception as e:
                print(f"DELETE ERROR: {e}")
