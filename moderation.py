from telegram import Update
from telegram.ext import ContextTypes

from database import log_action


WARNING = """
⚠️ Media Removed

To help protect the community, pictures and videos must be sent using Telegram's "Hide With Spoiler" option.

Please resend your media with the spoiler setting enabled.

Thank you for helping keep Melanated AZ a safe space. ❤️
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
