# ==========================================================
# Melanated AZ Bot
# config.py
# ==========================================================

import os


# ==========================================================
# TELEGRAM
# ==========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()


# ==========================================================
# ADMINS
# ==========================================================

ADMIN_IDS = [
    int(x.strip())
    for x in os.environ.get("ADMIN_IDS", "").split(",")
    if x.strip()
]


# ==========================================================
# RAFFLE GROUP
# ==========================================================

RAFFLE_CHAT_ID = os.environ.get(
    "RAFFLE_CHAT_ID",
    ""
).strip()


# ==========================================================
# PAYMENT
# ==========================================================

CASHAPP_TAG = os.environ.get(
    "CASHAPP_TAG",
    ""
).strip()

CASHAPP_URL = os.environ.get(
    "CASHAPP_URL",
    ""
).strip()

ZELLE_PHONE = os.environ.get(
    "ZELLE_PHONE",
    ""
).strip()


# ==========================================================
# RAFFLE SETTINGS
# ==========================================================

# Raffle duration in days.
# This is NOT the entry price.
# The entry price is set when the raffle is created.

RAFFLE_DURATION_DAYS = int(
    os.environ.get(
        "RAFFLE_DURATION_DAYS",
        "7"
    )
)


# ==========================================================
# STARTUP LOGGING
# ==========================================================

print(
    f"Loaded Admin IDs: {ADMIN_IDS}"
)

print(
    f"Raffle Chat ID: {RAFFLE_CHAT_ID}"
)

print(
    "Cash App:",
    "Loaded" if CASHAPP_TAG else "NOT SET"
)

print(
    "Zelle:",
    "Loaded" if ZELLE_PHONE else "NOT SET"
)
