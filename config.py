# ==========================================================
# Melanated AZ Bot
# config.py
# Configuration Settings
# ==========================================================

import os


# ==========================================================
# DATABASE
# ==========================================================

DB_NAME = os.getenv(
    "DB_NAME",
    "melanated_az.db"
)



# ==========================================================
# BOT ADMINS
# ==========================================================

ADMIN_IDS = [

    5879167814

]



# ==========================================================
# RAFFLE PAYMENT SETTINGS
# ==========================================================

CASHAPP_TAG = os.getenv(
    "CASHAPP_TAG",
    "$YourCashApp"
)


ZELLE_INFO = os.getenv(
    "ZELLE_INFO",
    "your@email.com"
)



# ==========================================================
# RAFFLE ENTRY COST
# ==========================================================

RAFFLE_ENTRY_COST = os.getenv(
    "RAFFLE_ENTRY_COST",
    "$5"
)


# Backwards compatibility
DEFAULT_RAFFLE_ENTRY = RAFFLE_ENTRY_COST



# ==========================================================
# RAFFLE SETTINGS
# ==========================================================

RAFFLE_DURATION_HOURS = int(
    os.getenv(
        "RAFFLE_DURATION_HOURS",
        "24"
    )
)



# ==========================================================
# BOT SETTINGS
# ==========================================================

BOT_NAME = "Melanated AZ Bot"



# ==========================================================
# STARTUP CHAT
# ==========================================================

STARTUP_CHAT_ID = os.getenv(
    "STARTUP_CHAT_ID"
)
