from telegram import Update
from telegram.ext import ContextTypes


WELCOME_MESSAGE = """
🔥 Welcome to Melanated AZ 🔥

👑 Community Guidelines 👑

This space was created for networking, connection, good vibes, and meeting like-minded adults. Let's keep it respectful, safe, and enjoyable for everyone.

━━━━━━━━━━━━━━━

📌 BEFORE PARTICIPATING

📸 A profile picture is required.

Please introduce yourself with:

• Name
• Age
• Location
• Status (Single, Partnered, Poly, etc.)
• What you're here for
• DMs Open or Closed

Example:

King | 40 | Vail, AZ | Partnered | Looking to network, make connections, and meet like-minded people | DMs Open

━━━━━━━━━━━━━━━

📜 GROUP RULES 📜

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
• Prioritize your safety.

8️⃣ No Predatory Behavior
• Manipulation, coercion, intimidation, or abuse will not be tolerated.

9️⃣ Keep It Classy
• Adult conversations are welcome.
• Avoid spam or attention-seeking behavior.

🔟 Community First
• Support one another.
• Welcome new members.
• Leave egos at the door.

━━━━━━━━━━━━━━━

⚠️ MEDIA SPOILER REQUIREMENT ⚠️

All photos, videos, GIFs, and media must use Telegram:

👁 Hide With Spoiler

This helps prevent accidental exposure and keeps the community comfortable.

━━━━━━━━━━━━━━━

🤖 MELANATED AZ BOT FEATURES

🔥 Media protection
🎂 Birthday celebrations
📅 Community check-ins
👋 Welcome messages
📌 Group management tools

━━━━━━━━━━━━━━━

👑 ADMIN RULE 👑

Admins reserve the right to remove anyone whose behavior negatively impacts the safety, privacy, or atmosphere of the group.

━━━━━━━━━━━━━━━

Consent • Respect • Communication • Accountability

Thank you for helping make Melanated AZ a respectful and welcoming community. ❤️👑
"""


async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if chat:
        await context.bot.send_message(
            chat_id=chat.id,
            text=WELCOME_MESSAGE
        )
