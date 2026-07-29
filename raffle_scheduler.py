# ==========================================================
# Melanated AZ Bot
# raffle_scheduler.py
# Automatic Raffle Drawing
# ==========================================================

import asyncio
import random

from datetime import datetime

from raffle_database import (
    get_expired_raffles,
    get_entries,
    save_winner
)


async def raffle_checker(application):

    while True:

        try:

            raffles = get_expired_raffles()


            for raffle in raffles:


                entries = get_entries(
                    raffle["id"]
                )


                if not entries:

                    continue



                pool = []


                for entry in entries:

                    for _ in range(entry["entries"]):

                        pool.append(entry)



                winner = random.choice(pool)



                save_winner(

                    raffle["id"],

                    winner["user_id"],

                    winner["display_name"]

                )


                await application.bot.send_message(

                    chat_id=raffle["chat_id"],

                    text=

                    f"🎉 RAFFLE WINNER 🎉\n\n"

                    f"🏆 Prize:\n"

                    f"{raffle['prize']}\n\n"

                    f"👑 Winner:\n"

                    f"{winner['display_name']}\n\n"

                    f"Congratulations! 🎊"

                )



        except Exception as e:

            print(
                f"Raffle scheduler error: {e}"
            )



        await asyncio.sleep(
            300
        )





def start_raffle_scheduler(application):


    application.job_queue.run_once(

        lambda context:

        asyncio.create_task(
            raffle_checker(application)
        ),

        when=5

    )
