# ==========================================================
# Melanated AZ Bot
# raffle_scheduler.py
# Automatic Raffle Scheduler
# ==========================================================

import asyncio
import random

from raffle_database import (
    get_expired_raffles,
    get_entries,
    close_raffle
)


# ==========================================================
# AUTOMATIC RAFFLE CHECK
# ==========================================================

async def raffle_check(application):

    while True:

        try:

            raffles = get_expired_raffles()


            for raffle in raffles:

                raffle_id = raffle[0]

                prize = raffle[1]


                # --------------------------------------------------
                # Get approved entries
                # --------------------------------------------------

                entries = get_entries(
                    raffle_id
                )


                if entries:

                    winner = random.choice(
                        entries
                    )


                    winner_username = winner[1]

                    winner_user_id = winner[2]


                    # --------------------------------------------------
                    # Send winner announcement
                    # --------------------------------------------------

                    await application.bot.send_message(

                        chat_id=application.bot_data.get(
                            "raffle_chat_id"
                        ),

                        text=f"""
🎉 RAFFLE WINNER 🎉

🏆 Prize:
{prize}

👑 Winner:
{winner_username}

Congratulations! 🔥🎊
"""
                    )


                    # --------------------------------------------------
                    # Notify winner privately
                    # --------------------------------------------------

                    try:

                        await application.bot.send_message(

                            chat_id=winner_user_id,

                            text=f"""
🎉 CONGRATULATIONS!

You won the Melanated AZ raffle! 👑🔥

🏆 Prize:
{prize}

The raffle has officially been closed.

An administrator will contact you regarding your prize.
"""
                        )

                    except Exception as e:

                        print(
                            f"Winner notification failed: {e}"
                        )


                else:

                    chat_id = application.bot_data.get(
                        "raffle_chat_id"
                    )


                    if chat_id:

                        await application.bot.send_message(

                            chat_id=chat_id,

                            text=f"""
⚠️ RAFFLE CLOSED

🏆 Prize:
{prize}

No approved entries were received.
"""
                        )


                # --------------------------------------------------
                # Close raffle
                # --------------------------------------------------

                close_raffle(
                    raffle_id
                )


        except Exception as e:

            print(
                f"Raffle Scheduler Error: {e}"
            )


        # ------------------------------------------------------
        # Check again in one hour
        # ------------------------------------------------------

        await asyncio.sleep(
            3600
        )


# ==========================================================
# START SCHEDULER
# ==========================================================

async def start_raffle_scheduler(
    application
):

    application.create_task(

        raffle_check(
            application
        )

    )
