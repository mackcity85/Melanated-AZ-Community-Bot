# ==========================================================
# Melanated AZ Bot
# config.py
# ==========================================================

import os


# ==========================================================
# TELEGRAM
# ==========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")


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

RAFFLE_CHAT_ID = int(
    os.environ.get("RAFFLE_CHAT_ID", "0")
)


# ==========================================================
# PAYMENT
# ==========================================================

CASHAPP_TAG = os.environ.get(
    "CASHAPP_TAG",
    ""
)

CASHAPP_URL = os.environ.get(
    "CASHAPP_URL",
    ""
)

ZELLE_PHONE = os.environ.get(
    "ZELLE_PHONE",
    ""
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
    "💳 Cash App: "
    + ("Loaded" if CASHAPP_TAG else "Not configured")
)

print(
    "💳 Zelle: "
    + ("Loaded" if ZELLE_PHONE else "Not configured")
)
