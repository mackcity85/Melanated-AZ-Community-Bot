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
# COMMUNITY / RAFFLE GROUP
# ==========================================================
# MAIN_GROUP_ID is the authoritative community supergroup.
# RAFFLE_CHAT_ID remains supported as an optional override so
# older deployments/configurations continue to work.
# ==========================================================

MAIN_GROUP_ID = None

_main_group_id = os.environ.get("MAIN_GROUP_ID", "").strip()

if _main_group_id:
    try:
        MAIN_GROUP_ID = int(_main_group_id)
    except ValueError:
        MAIN_GROUP_ID = None


RAFFLE_CHAT_ID = MAIN_GROUP_ID

_raffle_chat_id = os.environ.get(
    "RAFFLE_CHAT_ID",
    ""
).strip()

if _raffle_chat_id:
    try:
        RAFFLE_CHAT_ID = int(_raffle_chat_id)
    except ValueError:
        # If an invalid optional override is supplied, keep the
        # working MAIN_GROUP_ID fallback instead of setting None.
        RAFFLE_CHAT_ID = MAIN_GROUP_ID


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
    f"Main Group ID: {MAIN_GROUP_ID}"
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


# ==========================================================
# GLOBAL NOTIFICATION POLICY
# ==========================================================
# Import for its startup side effect: existing bot sends are
# centrally mirrored to ADMIN_GROUP_ID and temporary main-chat
# bot messages are automatically cleaned up.
# ==========================================================

import notification_policy  # noqa: E402,F401
