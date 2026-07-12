async def pin_cleanup_task(application):

    import asyncio
    import logging

    logging.info(
        "Pin cleanup scheduler started"
    )


    try:

        while True:

            await asyncio.sleep(
                86400
            )


    except asyncio.CancelledError:

        logging.info(
            "Pin cleanup scheduler stopped cleanly"
        )

        raise
