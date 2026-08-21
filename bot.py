# ==========================================================
# Melanated AZ Bot
# bot.py
# ==========================================================

import os
import logging
import threading

from flask import Flask

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
)

from admin import (
    admin_menu,
    admin_button,
)

from raffle import (
    start_raffle,
    enter_raffle,
    payment_button,
    admin_payment_button,
    admin_raffle_button,
    pending_entries,
    raffle_status,
    raffle_entries,
    draw_raffle,
    cancel_raffle,
    bonus_entry,
    remove_raffle_entry,
    refresh_raffle,
)


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ==========================================================
# FLASK
# ==========================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "🔥 Melanated AZ Bot Online", 200


@app.route("/health")
def health():

    return "OK", 200


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update,
    context
):

    logger.error(
        "Exception while processing update:",
        exc_info=context.error
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    logger.info(
        "🔥 Melanated AZ Bot Started"
    )

    logger.info(
        "Loaded Admin IDs: %s",
        ADMIN_IDS
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ======================================================
    # ADMIN
    # ======================================================

    application.add_handler(
        CommandHandler(
            "admin",
            admin_menu
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            admin_button,
            pattern=r"^admin_"
        )
    )

    # ======================================================
    # RAFFLE COMMANDS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle
        )
    )

    application.add_handler(
        CommandHandler(
            "enter",
            enter_raffle
        )
    )

    application.add_handler(
        CommandHandler(
            "pending",
            pending_entries
        )
    )

    application.add_handler(
        CommandHandler(
            "rafflestatus",
            raffle_status
        )
    )

    application.add_handler(
        CommandHandler(
            "raffleentries",
            raffle_entries
        )
    )

    application.add_handler(
        CommandHandler(
            "draw",
            draw_raffle
        )
    )

    application.add_handler(
        CommandHandler(
            "cancelraffle",
            cancel_raffle
        )
    )

    application.add_handler(
        CommandHandler(
            "bonusentry",
            bonus_entry
        )
    )

    application.add_handler(
        CommandHandler(
            "removeentry",
            remove_raffle_entry
        )
    )

    application.add_handler(
        CommandHandler(
            "refreshraffle",
            refresh_raffle
        )
    )

    # ======================================================
    # ENTER RAFFLE BUTTON
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_enter_button_wrapper,
            pattern=r"^raffle_enter$"
        )
    )

    # ======================================================
    # PAYMENT BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            payment_button,
            pattern=r"^raffle_(cashapp|zelle)$"
        )
    )

    # ======================================================
    # ENTRY APPROVAL BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_payment_button,
            pattern=r"^(approve|deny)_\d+$"
        )
    )

    # ======================================================
    # RAFFLE APPROVAL / CANCEL BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_raffle_button,
            pattern=r"^(approve_raffle|cancel_raffle)_\d+$"
        )
    )

    # ======================================================
    # ERROR HANDLER
    # ======================================================

    application.add_error_handler(
        error_handler
    )

    # ======================================================
    # FLASK
    # ======================================================

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    logger.info(
        "🌐 Flask health server started"
    )

    # ======================================================
    # TELEGRAM
    # ======================================================

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


# ==========================================================
# BUTTON WRAPPER
# ==========================================================

async def raffle_enter_button_wrapper(
    update,
    context
):

    from raffle import enter_button

    await enter_button(
        update,
        context
    )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    main()
