from telegram import Update
from telegram.ext import ContextTypes


WELCOME_MESSAGE = """
🔥 Welcome to Melanated AZ 🔥

👑 Welcome everyone!

This space was created for networking, good vibes, and meeting like-minded adults.

Please introduce yourself and review the group guidelines.

━━━━━━━━━━━━━━━

📸 PROFILE REQUIREMENT

A profile picture is required.

Please introduce yourself with:

• Name
• Age
• Location
• Status
• What you're here for
• DMs Open or Closed

Example:

King | 40 | Vail, AZ | Partnered | Networking and meeting like-minded people | DMs Open

━━━━━━━━━━━━━━━

📜 COMMUNITY EXPECTATIONS

• Respect everyone and their boundaries.
• No harassment, unwanted messages, or drama.
• If someone says no, respect it.
• Protect privacy.

━━━━━━━━━━━━━━━

🔒 NSFW MEDIA & SPOILERS

All photos and videos must use:

👁 Hide With Spoiler

How to use:

📱 Mobile:
1. Select photo/video
2. Open options
3. Choose "Hide With Spoiler"
4. Send

💻 Desktop:
1. Select media
2. Right-click preview
3. Choose "Hide With Spoiler"
4. Send

━━━━━━━━━━━━━━━

Use /rules for the complete community guidelines.

Consent • Respect • Communication • Accountability

Welcome to Melanated AZ ❤️👑
"""


async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.chat_member:
        return


    new_member = update.chat_member.new_chat_member


    if new_member.status == "member":

        user = new_member.user


        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Welcome {user.first_name}! 👑\n\n{WELCOME_MESSAGE}"
        )
