# ==========================================================
# Melanated AZ Bot
# Welcome System
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes

from database import update_member


# ==========================================================
# WELCOME NEW MEMBERS
# ==========================================================

async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    for member in update.message.new_chat_members:


        # Ignore bot accounts

        if member.is_bot:
            continue



        update_member(
            member.id,
            update.effective_chat.id,
            member.username,
            member.first_name
        )



        welcome_message = f"""
👑 Welcome {member.first_name} to Melanated AZ 👑

🔥 We're glad you joined our community.

This is a space for adults to network, connect, socialize, and meet like-minded people.

Before participating, please complete your introduction.

━━━━━━━━━━━━━━━

📌 REQUIRED INTRODUCTION

Please share:

✅ Name
✅ Age
✅ Location
✅ Status
   (Single / Partnered / Poly / Other)
✅ What you're here for
✅ DMs Open or Closed

Example:

King | 40 | Arizona | Partnered |
Networking, friendships, connections |
DMs Open

━━━━━━━━━━━━━━━

📜 IMPORTANT

Please review:

/rules

Community standards:

✅ Respect everyone
✅ Respect boundaries
✅ No harassment
✅ No unwanted DMs
✅ No drama
✅ Adults 18+ only
✅ Protect privacy

━━━━━━━━━━━━━━━

🔒 MEDIA SPOILERS

Photos and videos must use Telegram spoiler protection.

How to hide media:

📸 Photos/Videos:

1️⃣ Attach media
2️⃣ Tap the ⋮ menu
3️⃣ Select:

👁 Hide with Spoiler

4️⃣ Send

Text spoilers:

1️⃣ Highlight text
2️⃣ Select "Spoiler"
3️⃣ Send

━━━━━━━━━━━━━━━

🎉 COMMUNITY FEATURES

Available commands:

📜 /rules
View group guidelines

🎂 /birthday
Save your birthday

🎲 /activities
View group activities

🎟 /raffle
Join upcoming giveaways

❓ /help
See all commands

━━━━━━━━━━━━━━━

👑 Have fun, introduce yourself, and enjoy the room!

Consent • Respect • Communication • Accountability
"""


        await update.message.reply_text(
            welcome_message
        )



# ==========================================================
# INTRO COMMAND
# ==========================================================

async def intro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    if not context.args:

        await update.message.reply_text(
            "Usage:\n\n"
            "/intro Your introduction"
        )

        return



    intro_text = " ".join(
        context.args
    )


    await update.message.reply_text(
        "✅ Introduction received!\n\n"
        f"{intro_text}"
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
                f"👋 {user.first_name},\n\n"
                "Please add a profile picture "
                "to complete your community profile."
            )


    except Exception:

        pass
