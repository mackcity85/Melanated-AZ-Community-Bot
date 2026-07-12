# ==========================================================
# Melanated AZ Bot
# activities.py
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes


# ==========================================================
# /activities
# ==========================================================

async def activities(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
"""
🎉 Melanated AZ Activities

We regularly host community events including:

🎲 Games & Ice Breakers
• Trivia
• Would You Rather
• Truth or Dare
• Polls

🎟 Community Events
• Raffles
• Meet & Greets
• Group Outings
• Happy Hours
• Kickbacks

🎂 Community Recognition
• Birthday Shoutouts
• Member Appreciation

━━━━━━━━━━━━━━━

Useful Commands

📜 /rules
View the community rules

🎂 /setbirthday MM-DD-YYYY
Save your birthday

🎟 /raffle
View the current raffle

🎟 /enter
Enter the active raffle

❓ /help
See all commands

We add new activities regularly.
"""
    )


# ==========================================================
# /help
# ==========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
"""
👋 Melanated AZ Bot

General

/rules
Community Rules

/activities
Upcoming activities

/help
Bot commands

🎂 Birthdays

/setbirthday MM-DD-YYYY

🎟 Raffles

/raffle
Current raffle

/enter
Enter raffle

━━━━━━━━━━━━━━━

Admins

/startraffle

/drawraffle

/cancelraffle

/admin
Admin commands
"""
    )
