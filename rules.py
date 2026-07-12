# ==========================================================
# Melanated AZ Bot
# rules.py
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes



async def rules(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    rules_message = """

👑 Welcome to Melanated AZ 👑

Please review our community guidelines.

━━━━━━━━━━━━━━━

📸 MEMBER INTRODUCTION

A profile picture is required.

Please include:

• Name
• Age
• Location
• Status
• What you're here for
• DMs Open or Closed


━━━━━━━━━━━━━━━

📜 GROUP RULES

1️⃣ Consent Is Everything

• No means no.
• Respect boundaries.
• No pressure, manipulation, or guilt trips.


2️⃣ Respect Everyone

• No bullying.
• No harassment.
• No discrimination.
• Different lifestyles and dynamics are welcome.


3️⃣ Keep Drama Out

• Personal issues stay private.
• Do not bring outside conflicts into the group.
• Contact admins when needed.


4️⃣ Privacy Matters

• What is shared here stays here.
• No screenshots or recordings without permission.
• Protect everyone's information.


5️⃣ Adults Only

• Members must be 18+.
• No minors or inappropriate involvement.


6️⃣ No Unwanted Messages

• Ask before sending DMs.
• Respect someone's answer.
• Repeated unwanted contact may result in removal.


7️⃣ Verify Before You Trust

• Protect yourself.
• Meet safely.
• The group is not responsible for individual interactions.


8️⃣ No Predatory Behavior

• No manipulation.
• No coercion.
• No intimidation.
• Consent always comes first.


9️⃣ Keep It Classy

• Adult conversations are welcome.
• No spam.
• No attention-seeking behavior.


🔟 Community First

• Support each other.
• Help newcomers.
• Leave egos at the door.


━━━━━━━━━━━━━━━

🔒 NSFW MEDIA & SPOILERS

Photos and videos must use Telegram spoiler protection.

📸 Images/Videos:

1. Attach media
2. Tap ⋮ menu
3. Select:

"Hide with Spoiler"

4. Send


📝 Text Spoilers:

1. Type your message
2. Highlight text
3. Select:

"Spoiler"

4. Send


━━━━━━━━━━━━━━━

👑 ADMIN RULE

Admins may remove anyone who negatively impacts:

• Safety
• Privacy
• Respect
• Community atmosphere


Consent • Respect • Communication • Accountability

"""

    await update.message.reply_text(
        rules_message
    )
