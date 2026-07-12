# ==========================================================
# Melanated AZ Bot
# welcome.py
# New Member Welcome System
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes


# ==========================================================
# WELCOME NEW MEMBERS
# ==========================================================

async def welcome(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.chat_member:
        return


    new_member = update.chat_member.new_chat_member


    old_member = update.chat_member.old_chat_member



    # Only welcome new joins

    if old_member.status in (
        "left",
        "kicked"
    ) and new_member.status == "member":


        user = update.chat_member.from_user


        name = user.first_name or "New Member"



        message = f"""
👋 Welcome {name}!

Welcome to **Melanated AZ** 🖤

Please take a moment to:

✅ Read the group rules
✅ Introduce yourself
✅ Add a profile picture
✅ Respect everyone's boundaries

This is a community built on respect, communication, and good energy.

Enjoy the group!
"""


        await context.bot.send_message(

            chat_id=update.chat_member.chat.id,

            text=message,

            parse_mode="Markdown"

        )
