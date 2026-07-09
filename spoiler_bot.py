import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

WARNING = Media Removed

Please resend your picture or video using Telegram's Hide with Spoiler option.

How to do it:

1. Select your photo or video.
2. Before sending, tap the ⋮ menu (or options button).
3. Choose Hide with Spoiler.
4. Send the media again.

Thank you for helping keep the group comfortable for everyone. 
"""

async def check_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message.photo or message.video:
        if not message.has_media_spoiler:
            try:
                await message.delete()
                await update.effective_chat.send_message(WARNING)
            except Exception as e:
                print(e)

app = Application.builder().token(TOKEN).build()

app.add_handler(
    MessageHandler(filters.PHOTO | filters.VIDEO, check_media)
)

print("Spoiler moderation bot is running...")
app.run_polling()
