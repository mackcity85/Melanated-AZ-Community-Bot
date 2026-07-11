import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Main Melanated AZ Supergroup ID
STARTUP_CHAT_ID = int(os.getenv("STARTUP_CHAT_ID", "0"))

# Optional settings
BOT_NAME = "Melanated AZ Community Bot v4"

# Database file
DATABASE_NAME = "melanated_az_bot.db"

# Check required settings
if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN is missing. Add it to your .env file."
    )

if STARTUP_CHAT_ID == 0:
    print(
        "WARNING: STARTUP_CHAT_ID not set. "
        "Use /getid in your Telegram group to find it."
    )
