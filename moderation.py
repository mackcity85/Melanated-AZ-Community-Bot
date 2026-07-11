from telegram import Update
from telegram.ext import ContextTypes

from database import log_action


WARNING = """
⚠️ Media Removed

To help keep Melanated AZ a safe space, all pictures, videos, GIFs, and media must be sent using Telegram's **Hide With Spoiler** feature.

How to add a spoiler:

📱 Mobile:
1. Select your photo or video
2. Before sending, tap the three dots (⋮) or media options
3. Choose **Hide With Spoiler**
4. Send the media

💻 Desktop:
1. Select your photo or video
2. Right-click the media preview
3. Select **Hide With Spoiler**
4. Send the media

Your media will remain hidden until someone chooses to reveal it.

Thank you for helping protect our community ❤️
"""


async def check_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return


    user = update.effective_user


    # Ignore admins
    admins = await context.bot.get_chat_administrators(
        update.effective_chat.id
    )

    admin_ids = [
        admin.user.id
        for admin in admins
    ]

    if user.id in admin_ids:
        return


    remove = False
    media_type = ""


    # Photos
    if message.photo:
        media_type = "photo"

        if not message.has_media_spoiler:
            remove = True


    # Videos
    elif message.video:
        media_type = "video"

        if not message.has_media_spoiler:
            remove = True


    # GIF / Animation
    elif message.animation:
        media_type = "animation"

        if not message.has_media_spoiler:
            remove = True


    # Documents containing media
    elif message.document:
        media_type = "document"

        if not message.has_media_spoiler:
            remove = True



    if remove:

        try:
            await message.delete()

            log_action(
                user.id,
                "MEDIA_REMOVED",
                media_type
            )


            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=WARNING
            )

        except Exception as e:

            print(
                f"Moderation error: {e}"
            )
