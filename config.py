# ==========================================================
# Melanated AZ Bot
# config.py
# ==========================================================

import os


# ==========================================================
# BOT
# ==========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is not set."
    )


STARTUP_CHAT_ID = int(
    os.getenv(
        "STARTUP_CHAT_ID",
        "-1002697105809"
    )
)


# ==========================================================
# DATABASE
# ==========================================================

DB_NAME = os.getenv(
    "DB_NAME",
    "melanated_az.db"
)


# ==========================================================
# ADMINS
# ==========================================================

ADMIN_IDS = [
    5879167814
]


# ==========================================================
# RAFFLE
# ==========================================================

RAFFLE_ENTRY_COST = float(
    os.getenv(
        "RAFFLE_ENTRY_COST",
        "5.00"
    )
)

DEFAULT_RAFFLE_ENTRY = float(
    os.getenv(
        "DEFAULT_RAFFLE_ENTRY",
        "5.00"
    )
)


# ==========================================================
# PAYMENTS
# ==========================================================

# --------------------------
# Cash App
# --------------------------

CASHAPP_TAG = os.getenv(
    "CASHAPP_TAG",
    "$MelanatedAZ"
)

CASHAPP_URL = os.getenv(
    "CASHAPP_URL",
    "https://cash.app/$MelanatedAZ"
)


# --------------------------
# Zelle
# --------------------------

ZELLE_PHONE = os.getenv(
    "ZELLE_PHONE",
    "619-328-8725"
)

# Compatibility with existing raffle.py
ZELLE_EMAIL = os.getenv(
    "ZELLE_EMAIL",
    ZELLE_PHONE
)


# ==========================================================
# TRUTH OR DARE
# ==========================================================

TRUTH_DARE_ENABLED = True

TRUTH_DARE_LEVEL = "adult"


# ==========================================================
# STARTUP LOGGING
# ==========================================================

print(
    f"Loaded Admin IDs: {ADMIN_IDS}"
)

print(
    "🤖 BOT_TOKEN: Loaded"
)

print(
    "💳 Cash App: Loaded"
)

print(
    "💳 Zelle: Loaded"
)
