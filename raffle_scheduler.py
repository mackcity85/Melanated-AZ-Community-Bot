# ==========================================================
# Melanated AZ Bot
# raffle_scheduler.py
# ==========================================================

import asyncio

from raffle_database import (
    get_expired_raffles,
    close_raffle
)



async def raffle_check():

    while True:

        try:

            expired = get_expired_raffles()


            for raffle in expired:

                raffle_id = raffle[0]


                close_raffle(
                    raffle_id
                )


        except Exception as e:

            print(
                f"Raffle scheduler error: {e}"
            )


        await asyncio.sleep(
            3600
        )



def start_raffle_scheduler(
    application
):

    application.create_task(
        raffle_check()
    )
