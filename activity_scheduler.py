# ==========================================================
# Melanated AZ Bot
# activity_scheduler.py
# Member Activity Scheduler
# ==========================================================

import asyncio
from datetime import datetime, timedelta

from database import get_inactive_members, get_active_members



# ==========================================================
# SEND ACTIVITY CHECK
# ==========================================================

async def activity_check(
    application
):

    while True:

        try:

            chat_id = application.bot_data.get(
                "STARTUP_CHAT_ID"
            )


            if not chat_id:

                await asyncio.sleep(86400)
                continue



            inactive_members = get_inactive_members(
                days=30
            )


            for member in inactive_members:


                try:

                    await application.bot.send_message(

                        chat_id=member["user_id"],

                        text="""
👋 Hey!

We noticed you haven't been active in Melanated AZ recently.

We appreciate having you here!

If you would like to stay connected, jump back into the conversation anytime.

If you no longer wish to be part of the community, you can leave whenever you choose.

👑 Melanated AZ
"""
                    )


                except Exception:

                    pass



            # Thank active members

            active_members = get_active_members(
                days=30
            )


            for member in active_members:


                try:

                    await application.bot.send_message(

                        chat_id=member["user_id"],

                        text="""
🔥 Thank you!

We appreciate your activity and contribution to Melanated AZ.

Your participation helps keep this community active, welcoming, and connected.

👑 Keep bringing the good energy!
"""
                    )


                except Exception:

                    pass



        except Exception as e:

            print(
                "Activity scheduler error:",
                e
            )


        # Run once every 30 days

        await asyncio.sleep(
            60 * 60 * 24 * 30
        )
