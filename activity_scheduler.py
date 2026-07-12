# ==========================================================
# Melanated AZ Bot
# activity_scheduler.py
# ==========================================================

import asyncio
import logging

from datetime import datetime, timedelta


from database import get_db



logger = logging.getLogger(__name__)



# ==========================================================
# GET ACTIVE MEMBERS
# ==========================================================

def get_member_activity():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM members
        """
    )


    members = cursor.fetchall()


    conn.close()


    return members



# ==========================================================
# ACTIVITY CHECK LOOP
# ==========================================================

async def activity_check(
    application
):


    logger.info(
        "Activity scheduler started"
    )



    while True:


        try:


            members = get_member_activity()



            cutoff = datetime.now() - timedelta(
                days=30
            )



            for member in members:


                last_active = datetime.fromisoformat(
                    member["last_active"]
                )



                # Active members

                if last_active >= cutoff:


                    try:


                        await application.bot.send_message(

                            chat_id=member["user_id"],

                            text=(

                                "👑 Thank you for being an active "
                                "part of Melanated AZ!\n\n"

                                "Your participation helps keep "
                                "the community alive."

                            )

                        )


                    except Exception:


                        pass



                # Inactive members

                else:


                    try:


                        await application.bot.send_message(

                            chat_id=member["user_id"],

                            text=(

                                "👋 Hey! We noticed you haven't "
                                "been active in Melanated AZ recently.\n\n"

                                "We would love to see you back!\n\n"

                                "Jump into the conversations, "
                                "activities, and community events."

                            )

                        )


                    except Exception:


                        pass




            # Run every 30 days

            await asyncio.sleep(
                2592000
            )



        except asyncio.CancelledError:


            logger.info(
                "Activity scheduler stopped"
            )


            break



        except Exception as e:


            logger.error(
                f"Activity scheduler error: {e}"
            )


            await asyncio.sleep(
                300
            )
