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

ADMIN_IDS = []

_admin_ids = os.environ.get("ADMIN_IDS", "").strip()

if _admin_ids:
    try:
        ADMIN_IDS = [
            int(x.strip())
            for x in _admin_ids.split(",")
            if x.strip()
        ]
    except ValueError:
        ADMIN_IDS = []


# ==========================================================
# RAFFLE GROUP
# ==========================================================

RAFFLE_CHAT_ID = None

_raffle_chat_id = os.environ.get(
    "RAFFLE_CHAT_ID",
    ""
).strip()

if _raffle_chat_id:
    try:
        RAFFLE_CHAT_ID = int(_raffle_chat_id)
    except ValueError:
        RAFFLE_CHAT_ID = None


# ==========================================================
# RAFFLE DURATION
# ==========================================================

RAFFLE_DURATION_DAYS = int(
    os.environ.get(
        "RAFFLE_DURATION_DAYS",
        "7"
    )
)


# ==========================================================
# PAYMENTS
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
# LOGGING
# ==========================================================

print(
    f"Loaded Admin IDs: {ADMIN_IDS}"
)

print(
    f"Raffle Chat ID: {RAFFLE_CHAT_ID}"
)

print(
    "Cash App: Loaded"
    if CASHAPP_TAG
    else "Cash App: NOT configured"
)

print(
    "Zelle: Loaded"
    if ZELLE_PHONE
    else "Zelle: NOT configured"
)
