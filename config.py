# ==========================================================
# Melanated AZ Bot
# config.py
# Main Configuration
# ==========================================================

import os

from dotenv import load_dotenv

load_dotenv()



# ==========================================================
# BOT SETTINGS
# ==========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)


STARTUP_CHAT_ID = os.getenv(
    "STARTUP_CHAT_ID"
)



# ==========================================================
# DATABASE
# ==========================================================

DB_NAME = os.getenv(
    "DB_NAME",
    "melanated_az.db"
)



# ==========================================================
# ADMIN SETTINGS
# ==========================================================

ADMIN_IDS = [

    int(admin)

    for admin in os.getenv(
        "ADMIN_IDS",
        "5879167814"
    ).split(",")

]



# ==========================================================
# RAFFLE SETTINGS
# ==========================================================

RAFFLE_ENTRY_COST = os.getenv(
    "RAFFLE_ENTRY_COST",
    "$5"
)


DEFAULT_RAFFLE_ENTRY = RAFFLE_ENTRY_COST


RAFFLE_DURATION_HOURS = int(
    os.getenv(
        "RAFFLE_DURATION_HOURS",
        "24"
    )
)



# ==========================================================
# PAYMENT SETTINGS
# ==========================================================

CASHAPP_TAG = os.getenv(
    "CASHAPP_TAG",
    "$YourCashApp"
)


ZELLE_INFO = os.getenv(
    "ZELLE_INFO",
    "Your Zelle Information"
)



# ==========================================================
# TRUTH / DARE
# ==========================================================

TRUTH_DARE_ENABLED = True



# ==========================================================
# COMMUNITY SETTINGS
# ==========================================================

GROUP_NAME = (
    "Melanated AZ"
)
