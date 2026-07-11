from telegram import Update
from telegram.ext import ContextTypes


RULES_MESSAGE = """
👑 Welcome to Melanated AZ 👑

📜 GROUP RULES 📜

1️⃣ Consent Is Everything
• Respect boundaries.
• No pressure, manipulation, or harassment.

2️⃣ Respect Everyone
• No bullying, discrimination, or personal attacks.
• Different lifestyles and dynamics are welcome.

3️⃣ Keep Drama Out
• Handle personal issues privately.
• Contact admins if needed.

4️⃣ Privacy Matters
• What is shared here stays here.
• No screenshots or sharing conversations without permission.

5️⃣ Adults Only
• All members must be 18+.

6️⃣ No Unsolicited Messages
• Ask before sending DMs.
• Respect people's answers.

7️⃣ Verify Before You Trust
• Protect yourself when meeting others.

8️⃣ No Predatory Behavior
• Manipulation or coercion will not be tolerated.

9️⃣ Keep It Classy
• Adult conversations are welcome.
• Avoid spam and excessive content.

🔟 Community First
• Support each other.
• Welcome new members.

━━━━━━━━━━━━━━━

⚠️ MEDIA SPOILER REQUIREMENT ⚠️

Photos, videos, and GIFs must use:

👁 Hide With Spoiler

Consent • Respect • Communication • Accountability
"""


INTRO_MESSAGE = """
👋 Melanated AZ Introduction

Please introduce yourself:

Name:
Age:
Location:
Status:
What you're here for:
DMs Open or Closed:
"""


SPOILER_MESSAGE = """
⚠️ Media Spoiler Reminder

All photos, videos, and GIFs must use:

👁 Hide With Spoiler

This helps keep the community comfortable.
"""


HELP_MESSAGE = """
🤖 Melanated AZ Bot Commands

/rules
View community rules

/intro
Introduction format

/spoiler
Media instructions

/help
Show commands
"""


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_MESSAGE)


async def intro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INTRO_MESSAGE)


async def spoiler_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(SPOILER_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_MESSAGE)


def get_command_handlers():

    from telegram.ext import CommandHandler

    return [
        CommandHandler("rules", rules_command),
        CommandHandler("intro", intro_command),
        CommandHandler("spoiler", spoiler_command),
        CommandHandler("help", help_command),
    ]
