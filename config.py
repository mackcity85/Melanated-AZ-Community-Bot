# ==========================================================
# Melanated AZ Bot
# config.py
# ==========================================================

import os
from dotenv import load_dotenv

load_dotenv()


# ==========================================================
# BOT
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
# ADMIN
# ==========================================================

ADMIN_IDS = [

    int(x)

    for x in os.getenv(
        "ADMIN_IDS",
        ""
    ).split(",")

    if x.strip().isdigit()

]



# ==========================================================
# RAFFLE SETTINGS
# ==========================================================

RAFFLE_ENTRY_COST = float(
    os.getenv(
        "RAFFLE_ENTRY_COST",
        "5"
    )
)


DEFAULT_RAFFLE_ENTRY = RAFFLE_ENTRY_COST



# Payment accounts
CASHAPP_TAG = os.getenv(
    "CASHAPP_TAG",
    "$MelanatedAZ"
)


ZELLE_EMAIL = os.getenv(
    "ZELLE_EMAIL",
    "change-me@example.com"
)



# ==========================================================
# TRUTH OR DARE
# ==========================================================

TRUTH_DARE_ENABLED = True
