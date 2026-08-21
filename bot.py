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

# ==========================================================
# CONFIG
# ==========================================================

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    CASHAPP_TAG,
    CASHAPP_URL,
    ZELLE_PHONE,
)

# ==========================================================
# ADMIN
# ==========================================================

from admin import (
    admin_menu,
    admin_button,
)

# ==========================================================
# RAFFLE
# ==========================================================

from raffle import (
    start_raffle,
    enter_raffle,
    raffle_enter_button,
    paid_entry,
    payment_button,
    admin_payment_button,
    raffle_approval_button,
    pending_entries,
    approve_raffle_entry,
    deny_raffle_entry,
    raffle_status,
    raffle_entries,
    draw_raffle,
    reroll_raffle,
    cancel_raffle,
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
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Exception while processing update:",
        exc_info=context.error,
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
        ADMIN_IDS,
    )

    # ======================================================
    # CREATE APPLICATION
    # ======================================================

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ======================================================
    # ADMIN COMMAND
    # ======================================================

    application.add_handler(
        CommandHandler(
            "admin",
            admin_menu,
        )
    )

    # ======================================================
    # ADMIN BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_button,
            pattern=r"^admin_",
        )
    )

    # ======================================================
    # RAFFLE COMMANDS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "startraffle",
            start_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "enter",
            enter_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "paid",
            paid_entry,
        )
    )

    application.add_handler(
        CommandHandler(
            "pending",
            pending_entries,
        )
    )

    application.add_handler(
        CommandHandler(
            "approveentry",
            approve_raffle_entry,
        )
    )

    application.add_handler(
        CommandHandler(
            "denyentry",
            deny_raffle_entry,
        )
    )

    application.add_handler(
        CommandHandler(
            "rafflestatus",
            raffle_status,
        )
    )

    application.add_handler(
        CommandHandler(
            "raffleentries",
            raffle_entries,
        )
    )

    application.add_handler(
        CommandHandler(
            "draw",
            draw_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "reroll",
            reroll_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "cancelraffle",
            cancel_raffle,
        )
    )

    application.add_handler(
        CommandHandler(
            "bonusentry",
            bonus_entry,
        )
    )

    application.add_handler(
        CommandHandler(
            "removeentry",
            remove_raffle_entry,
        )
    )

    # ======================================================
    # RAFFLE APPROVAL BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_approval_button,
            pattern=r"^raffle(approve|reject|reject)_\d+$|^raffalreject_\d+$",
        )
    )

    # ======================================================
    # RAFFLE ENTER BUTTON
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            raffle_enter_button,
            pattern=r"^raffle_enter$",
        )
    )

    # ======================================================
    # RAFFLE PAYMENT BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            payment_button,
            pattern=r"^raffle_(cashapp|zelle)$",
        )
    )

    # ======================================================
    # RAFFLE ENTRY APPROVAL BUTTONS
    # ======================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_payment_button,
            pattern=r"^(approve|deny)_\d+$",
        )
    )

    # ======================================================
    # ERROR HANDLER
    # ======================================================

    application.add_error_handler(
        error_handler
    )

    # ======================================================
    # START FLASK
    # ======================================================

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )

    flask_thread.start()

    logger.info(
        "🌐 Flask health server started"
    )

    # ======================================================
    # START TELEGRAM
    # ======================================================

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


# ==========================================================
# START PROGRAM
# ==========================================================

if __name__ == "__main__":
    main()
