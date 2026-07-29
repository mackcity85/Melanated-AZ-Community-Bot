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
# CHECK EXPIRED RAFFLES
# ==========================================================

async def raffle_check():

    while True:

        try:

            expired = get_expired_raffles()


            for raffle in expired:

                raffle_id = raffle[0]
                prize = raffle[1]


                entries = get_entries(
                    raffle_id
                )


                if entries:

                    winner = random.choice(
                        entries
                    )


                    print(
                        f"🎉 Auto Winner: {winner[1]} won {prize}"
                    )


                else:

                    print(
                        f"⚠️ No entries for {prize}"
                    )


                close_raffle(
                    raffle_id
                )


        except Exception as e:

            print(
                f"Raffle Scheduler Error: {e}"
            )


        # Check every hour

        await asyncio.sleep(
            3600
        )



# ==========================================================
# START SCHEDULER
# ==========================================================

def start_raffle_scheduler(
    application
):

    application.create_task(
        raffle_check()
    )
