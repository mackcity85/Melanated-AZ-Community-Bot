# ==========================================================
# Melanated AZ Bot
# config.py
# ==========================================================

import os


BOT_TOKEN = os.environ.get("BOT_TOKEN", "")


ADMIN_IDS = [
    int(x.strip())
    for x in os.environ.get("ADMIN_IDS", "").split(",")
    if x.strip()
]


# Telegram group where approved raffles are posted
RAFFLE_CHAT_ID = int(
    os.environ.get("RAFFLE_CHAT_ID", "0")
)


# Payment settings
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


print(f"Loaded Admin IDs: {ADMIN_IDS}")
print(f"Raffle Chat ID: {RAFFLE_CHAT_ID}")
print(
    "💳 Cash App: "
    + ("Loaded" if CASHAPP_TAG else "Not configured")
)
print(
    "💳 Zelle: "
    + ("Loaded" if ZELLE_PHONE else "Not configured")
)
