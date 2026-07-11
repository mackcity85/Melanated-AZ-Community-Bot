from telegram import Update
from telegram.ext import ContextTypes


RULES_MESSAGE = """
👑 Welcome to Melanated AZ 👑

📜 GROUP RULES 📜

Please review the community guidelines:

━━━━━━━━━━━━━━━

1️⃣ Consent Is Everything
• No means no.
• Respect boundaries at all times.
• No pressure, manipulation, or guilt trips.

2️⃣ Respect Everyone
• No bullying, harassment, discrimination, or personal attacks.
• Different lifestyles, dynamics, interests, and experience levels are welcome.
• Disagreements are okay. Disrespect is not.

3️⃣ Keep Drama Out
• Personal issues stay private.
• Do not bring outside conflicts into the group.
• Contact an admin if help is needed.

4️⃣ Privacy Matters
• What is shared here stays here.
• No screenshots, recordings, or sharing conversations without permission.

5️⃣ Adults Only
• All members must be 18+.

6️⃣ No Unsolicited Messages
• Ask before sending DMs.
• Respect someone's answer if they decline.

7️⃣ Verify Before You Trust
• Take time to get to know people.
• Prioritize your safety when meeting others.

8️⃣ No Predatory Behavior
• Manipulation, coercion, intimidation, or abuse will not be tolerated.
• Consent always comes first.

9️⃣ Keep It Classy
• Adult conversations are welcome.
• Avoid spam, excessive explicit content, and attention-seeking behavior.

🔟 Community First
• Support one another.
• Welcome new members.
• Leave egos at the door.

━━━━━━━━━━━━━━━

⚠️ MEDIA SPOILER REQUIREMENT ⚠️

All photos, videos, GIFs, and media must use:

👁 Hide With Spoiler

This helps keep the community comfortable and prevents accidental exposure.

━━━━━━━━━━━━━━━

👑 ADMIN RULE 👑

Admins reserve the right to remove anyone whose behavior negatively impacts the safety, privacy, or atmosphere of the group.

Consent • Respect • Communication • Accountability
"""


INTRO_MESSAGE = """
👋 Melanated AZ Introduction Format

Please introduce yourself:

👤 Name:
🎂 Age:
📍 Location:
💞 Status:
🎯 What you're here for:
📩 DMs Open or Closed:

Example:

King | 40 | Vail, AZ | Partnered | Networking and meeting like-minded people | DMs Open
"""


SPOILER_MESSAGE = """
⚠️ Media Spoiler Reminder ⚠️

All photos, videos, GIFs, and media must be sent using Telegram's:

👁 Hide With Spoiler

📱 Mobile:
1. Select your media
2. Open media options
3. Choose "Hide With Spoiler"
4. Send

💻 Desktop:
1. Select your media
2. Right-click the preview
3. Choose "Hide With Spoiler"
4. Send

Thank you for helping keep Melanated AZ comfortable for everyone. ❤️
"""


HELP_MESSAGE = """
🤖 Melanated AZ Bot

Available Commands:

📜 /rules
View community guidelines

👋 /intro
View introduction format

⚠️ /spoiler
View media spoiler instructions

🔥 Media Protection
🎂 Birthday Celebrations
📅 Community Check-ins
👑 Group Management Tools
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
