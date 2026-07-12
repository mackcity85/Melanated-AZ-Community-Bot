# ==========================================================
# Melanated AZ Bot
# welcome.py
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes

from database import update_member



# ==========================================================
# NEW MEMBER WELCOME
# ==========================================================

async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    for member in update.message.new_chat_members:


        # Ignore bots joining

        if member.is_bot:
            continue


        update_member(
            member.id,
            update.effective_chat.id,
            member.username,
            member.first_name
        )


        welcome_message = f"""
👑 Welcome to Melanated AZ 👑

Welcome {member.first_name}! 🔥

This space was created for networking, good vibes, and meeting like-minded adults.

Please introduce yourself and review our guidelines.

━━━━━━━━━━━━━━━

📸 PROFILE REQUIREMENTS

A profile picture is required.

Please introduce yourself with:

• Name
• Age
• Location
• Status
  (Single, Partnered, Poly, etc.)
• What you're here for
• DMs Open or Closed


Example:

King | 40 | Arizona | Partnered |
Networking, connections, meeting people |
DMs Open


━━━━━━━━━━━━━━━

👑 GROUP GUIDELINES

• Respect everyone
• Consent is everything
• No means no
• Respect boundaries
• No harassment
• No unwanted messages
• No flooding DMs
• No drama
• No personal attacks
• Respect privacy
• What is shared here stays here
• Adults only (18+)


If someone says no or is not interested,
respect it and keep it moving.


━━━━━━━━━━━━━━━

🆘 BOT HELP

Need help?

/help


📜 View rules:

/rules


👋 Introduce yourself:

/intro Your introduction


━━━━━━━━━━━━━━━

🎉 COMMUNITY ACTIVITIES

Join the fun:

🎲 Trivia

/trivia


🔥 Truth or Dare

/truth

/dare


🎂 Birthdays

Save your birthday:

/birthday MM/DD


🎟️ Raffles

View active raffle:

/raffle


Enter a raffle:

/joinraffle


━━━━━━━━━━━━━━━

🔒 MEDIA SPOILER GUIDE

Sensitive photos and videos must use Telegram Spoiler protection.

📸 Hide Photos/Videos:

1. Attach your photo or video

2. Tap the ⋮ menu

3. Select:

"Hide with Spoiler"

4. Send your message


📝 Hide Text:

1. Type your message

2. Highlight the text

3. Select:

"Spoiler"

4. Send


Spoilers help everyone control what they view.

━━━━━━━━━━━━━━━

👑 ADMIN NOTE

Admins reserve the right to remove anyone whose behavior negatively impacts:

• Safety
• Privacy
• Respect
• The atmosphere of the group


I have no personal ties to anyone here.
I'm getting to know everyone just like everyone else.

This is a place for adults to connect,
network, communicate, and enjoy the community.

━━━━━━━━━━━━━━━

Consent • Respect • Communication • Accountability

🔥 Welcome to Melanated AZ 🔥
"""


        await update.message.reply_text(
            welcome_message
        )



# ==========================================================
# PROFILE CHECK
# ==========================================================

async def profile_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    user = update.effective_user


    try:

        photos = await context.bot.get_user_profile_photos(
            user.id,
            limit=1
        )


        if photos.total_count == 0:

            await update.message.reply_text(
                f"📸 {user.first_name}, "
                "please add a profile picture "
                "to complete your community profile."
            )


    except Exception:

        pass



# ==========================================================
# INTRO COMMAND
# ==========================================================

async def intro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            """
👋 Introduce yourself!

Please include:

• Name
• Age
• Location
• Status
• What you're here for
• DMs Open or Closed


Example:

King | 40 | Arizona | Partnered |
Networking and meeting like-minded people |
DMs Open
"""
        )

        return


    introduction = " ".join(
        context.args
    )


    await update.message.reply_text(
        "✅ Introduction received!\n\n"
        f"{introduction}"
    )



# ==========================================================
# HELP COMMAND
# ==========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
🆘 Melanated AZ Help

📜 Rules
/rules

👋 Introduction
/intro

🎲 Trivia
/trivia

🔥 Truth or Dare
/truth
/dare

🎂 Birthday
/birthday MM/DD

🎟️ Raffle
/raffle
/joinraffle


Need an admin?
Contact the moderators.
"""
    )
