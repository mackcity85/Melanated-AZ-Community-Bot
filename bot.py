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
    MessageHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
)

from admin import (
    admin_menu,
    admin_button,
)

from raffle import (
    start_raffle,
    enter_raffle,
    paid_entry,
    payment_button,
    raffle_enter_button,
    raffle_approval_button,
    admin_payment_button,
    pending_entries,
    raffle_status,
    raffle_entries,
    draw_raffle,
    reroll_raffle,
    cancel_raffle,
    bonus_entry,
    remove_raffle_entry,
    create_pending_raffle,
)


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
# ADMIN RAFFLE INPUT
# ==========================================================

async def raffle_setup_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:

        return

    if not context.user_data.get(
        "awaiting_raffle_setup"
    ):

        return

    from config import ADMIN_IDS

    if update.effective_user.id not in ADMIN_IDS:

        return

    text = (
        update.message.text
        if update.message
        else ""
    ).strip()

    if "|" not in text:

        await update.message.reply_text(
            "❌ Use this format:\n\n"
            "Prize | Entry Price\n\n"
            "Example:\n"
            "$100 Cash Prize | $5"
        )

        return

    prize, price = text.split(
        "|",
        1
    )

    prize = prize.strip()
    price = price.strip()

    context.user_data[
        "awaiting_raffle_setup"
    ] = False

    await create_pending_raffle(
        update,
        context,
        prize,
        price,
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

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ------------------------------------------------------
    # ADMIN
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # RAFFLE COMMANDS
    # ------------------------------------------------------

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
            "paid",
            paid_entry
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
            "reroll",
            reroll_raffle
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

    # ------------------------------------------------------
    # ADMIN RAFFLE APPROVAL
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            raffle_approval_button,
            pattern=r"^raffle(approve|cancel)_\d+$"
        )
    )

    # ------------------------------------------------------
    # MEMBER ENTER BUTTON
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            raffle_enter_button,
            pattern=r"^raffle_enter$"
        )
    )

    # ------------------------------------------------------
    # PAYMENT BUTTONS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            payment_button,
            pattern=r"^raffle_(cashapp|zelle)$"
        )
    )

    # ------------------------------------------------------
    # PAYMENT APPROVAL
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            admin_payment_button,
            pattern=r"^(approve|deny)_\d+$"
        )
    )

    # ------------------------------------------------------
    # ADMIN RAFFLE SETUP MESSAGE
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            raffle_setup_message
        )
    )

    # ------------------------------------------------------
    # ERROR HANDLER
    # ------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    # ------------------------------------------------------
    # FLASK
    # ------------------------------------------------------

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    logger.info(
        "🌐 Flask health server started"
    )

    # ------------------------------------------------------
    # TELEGRAM
    # ------------------------------------------------------

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":

    main()
