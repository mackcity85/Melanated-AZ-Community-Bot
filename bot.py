# ==========================================================
# Melanated AZ Bot
# bot.py
# ==========================================================

import logging
import threading
import os

from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    RAFFLE_CHAT_ID,
)

from admin import (
    admin_menu,
    admin_button,
)

from raffle import (
    start_raffle,
    handle_raffle_setup,
    raffle_approval_button,
    raffle_enter_button,
    payment_button,
    admin_payment_button,
    enter_raffle,
    paid_entry,
    pending_entries,
    raffle_status,
    raffle_entries,
    cancel_raffle,
    draw_raffle,
    reroll_raffle,
    bonus_entry,
    remove_raffle_entry,
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
# FLASK HEALTH SERVER
# ==========================================================

app = Flask(__name__)


@app.route("/")
def health():

    return "Melanated AZ Bot is running", 200


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            10000,
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ==========================================================
# TEXT MESSAGE HANDLER
# ==========================================================

async def text_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    handled = await handle_raffle_setup(
        update,
        context,
    )

    if handled:
        return


# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.exception(
        "Exception while processing update:",
        exc_info=context.error,
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    logger.info(
        "🔥 Melanated AZ Bot Started"
    )

    logger.info(
        "Loaded Admin IDs: %s",
        ADMIN_IDS,
    )

    logger.info(
        "Raffle Chat ID: %s",
        RAFFLE_CHAT_ID,
    )

    logger.info(
        "Cash App: Loaded"
    )

    logger.info(
        "Zelle: Loaded"
    )

    # ------------------------------------------------------
    # FLASK
    # ------------------------------------------------------

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )

    flask_thread.start()

    logger.info(
        "🌐 Flask health server started"
    )

    # ------------------------------------------------------
    # TELEGRAM APPLICATION
    # ------------------------------------------------------

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
            admin_menu,
        )
    )

    # ======================================================
    # START RAFFLE
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle,
        )
    )

    # ======================================================
    # ENTER RAFFLE
    # ======================================================

    application.add_handler(
        CommandHandler(
            ["raffle", "enterraffle"],
            enter_raffle,
        )
    )

    # ======================================================
    # PAID ENTRY
    # ======================================================

    application.add_handler(
        CommandHandler(
            "paid",
            paid_entry,
        )
    )

    # ======================================================
    # STATUS
    # ======================================================

    application.add_handler(
        CommandHandler(
            ["status", "rafflestatus"],
            raffle_status,
        )
    )

    # ======================================================
    # ENTRIES
    # ======================================================

    application.add_handler(
        CommandHandler(
            "entries",
            raffle_entries,
        )
    )

    # ======================================================
    # PENDING
    # ======================================================

    application.add_handler(
        CommandHandler(
            "pending",
            pending_entries,
        )
    )

    # ======================================================
    # CANCEL
    # ======================================================

    application.add_handler(
        CommandHandler(
            "cancelraffle",
            cancel_raffle,
        )
    )

    # ======================================================
    # DRAW
    # ======================================================

    application.add_handler(
        CommandHandler(
            "draw",
            draw_raffle,
        )
    )

    # ======================================================
    # REROLL
    # ======================================================

    application.add_handler(
        CommandHandler(
            "reroll",
            reroll_raffle,
        )
    )

    # ======================================================
    # BONUS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "bonusentry",
            bonus_entry,
        )
    )

    # ======================================================
    # REMOVE ENTRY
    # ======================================================

    application.add_handler(
        CommandHandler(
            "removeentry",
            remove_raffle_entry,
        )
    )

    # ======================================================
    # ADMIN PANEL
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_button,
            pattern=r"^admin_",
        )
    )

    # ======================================================
    # RAFFLE APPROVAL / CANCELLATION
    #
    # Handles:
    # raffleapprove_123
    # rafflecancel_123
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_approval_button,
            pattern=r"^raffle(?:approve|cancel)_\d+$",
        )
    )

    # ======================================================
    # ADMIN PAYMENT
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_payment_button,
            pattern=r"^(approve|deny)_\d+$",
        )
    )

    # ======================================================
    # MEMBER ENTER
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_enter_button,
            pattern=r"^raffle_enter$",
        )
    )

    # ======================================================
    # PAYMENT
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            payment_button,
            pattern=r"^raffle_(cashapp|zelle)$",
        )
    )

    # ======================================================
    # RAFFLE SETUP TEXT
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message_handler,
        )
    )

    # ======================================================
    # ERROR HANDLER
    # ======================================================

    application.add_error_handler(
        error_handler
    )

    # ======================================================
    # POLLING
    # ======================================================

    logger.info(
        "Starting Telegram polling..."
    )

    application.run_polling(
        drop_pending_updates=False,
        allowed_updates=Update.ALL_TYPES,
    )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":
    main()
