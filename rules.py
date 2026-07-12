# ==========================================================
# Melanated AZ Bot
# rules.py
# Community Guidelines
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes



# ==========================================================
# /rules COMMAND
# ==========================================================

async def rules(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

"""
👑 Welcome to Melanated AZ 👑

This space was created for networking, good vibes, and meeting like-minded adults.

Please introduce yourself when joining and review the pinned messages.

━━━━━━━━━━━━━━━

📸 PROFILE REQUIREMENTS

A profile picture is required.

Please include:

• Name
• Age
• Location
• Status
  (Single, Partnered, Poly, etc.)
• What you're here for
• DMs Open or Closed

Example:

King | 40 | Arizona | Partnered | Networking & connections | DMs Open

If we cannot identify you, you may be removed from the group.

━━━━━━━━━━━━━━━

📜 GROUP RULES 📜

1️⃣ Consent Is Everything

• No means no.
• Respect boundaries.
• No pressure, manipulation, or guilt trips.

━━━━━━━━━━━━━━━

2️⃣ Respect Everyone

• No bullying.
• No harassment.
• No discrimination.
• No personal attacks.

Different lifestyles, dynamics, and experience levels are welcome.

━━━━━━━━━━━━━━━

3️⃣ Keep Drama Out

• Personal issues stay private.
• Do not bring outside conflicts into the group.
• Contact admins if help is needed.

━━━━━━━━━━━━━━━

4️⃣ Privacy Matters

• What is shared here stays here.
• No screenshots or recordings without permission.
• Do not share personal information.

━━━━━━━━━━━━━━━

5️⃣ Adults Only

🔞 All members must be 18+.

No minors, discussion involving minors, or inappropriate content involving minors.

━━━━━━━━━━━━━━━

6️⃣ No Unsolicited Messages

• Ask before sending DMs.
• Respect someone's answer.
• Repeated unwanted contact may result in removal.

━━━━━━━━━━━━━━━

7️⃣ Verify Before You Trust

• Vet people appropriately.
• Prioritize safety when meeting.
• The group is not responsible for individual interactions.

━━━━━━━━━━━━━━━

8️⃣ No Predatory Behavior

Manipulation, coercion, intimidation, or abuse will not be tolerated.

━━━━━━━━━━━━━━━

9️⃣ Keep It Classy

Adult conversations are welcome.

Avoid:
• Spam
• Excessive explicit content
• Attention-seeking behavior

━━━━━━━━━━━━━━━

🔟 Community First

• Support each other.
• Help newcomers.
• Leave egos at the door.

━━━━━━━━━━━━━━━

🔒 NSFW MEDIA & SPOILERS

To hide text:

1. Type your message.
2. Highlight the text.
3. Select "Spoiler".
4. Send.

To hide photos/videos:

1. Attach your media.
2. Tap the three dots menu.
3. Select:

"Hide with Spoiler"

4. Send.

━━━━━━━━━━━━━━━

👑 ADMIN RULE

Admins reserve the right to remove anyone who negatively impacts the safety, privacy, or atmosphere of Melanated AZ.

Consent • Respect • Communication • Accountability
"""

    )
