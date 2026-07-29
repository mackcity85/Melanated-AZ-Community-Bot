# ==========================================================
# Melanated AZ Bot
# raffle_scheduler.py
# Automatic Raffle Scheduler
# ==========================================================

import random

from raffle_database import (
    get_expired_raffles,
    get_entries,
    close_raffle
)



# ==========================================================
# AUTO RAFFLE CHECK
# ==========================================================

async def raffle_check(application):

    while True:

        try:

            expired_raffles = get_expired_raffles()


            for raffle in expired_raffles:

                raffle_id = raffle[0]

                prize = raffle[1]


                entries = get_entries(
                    raffle_id
                )


                if entries:

                    winner = random.choice(
                        entries
                    )


                    await application.bot.send_message(

                        chat_id=raffle[2],

                        text=f"""
🎉 AUTOMATIC RAFFLE WINNER 🎉

🏆 Prize:
{prize}

👑 Winner:
{winner[1]}

Congratulations! 🎊
"""

                    )


                else:

                    await application.bot.send_message(

                        chat_id=raffle[2],

                        text=f"""
⚠️ Raffle Closed

🏆 Prize:
{prize}

No approved entries received.
"""

                    )


                close_raffle(
                    raffle_id
                )


        except Exception as e:

            print(
                f"Raffle Scheduler Error: {e}"
            )



        # Check every hour

        import asyncio

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
