# ==========================================================
# Melanated AZ Bot
# config.py
# ==========================================================

import os


# ==========================================================
# TELEGRAM BOT TOKEN
# ==========================================================

BOT_TOKEN = os.environ.get(
    "BOT_TOKEN"
)


# ==========================================================
# ADMIN USERS
# ==========================================================
#
# Render Environment Variable Example:
#
# ADMIN_IDS=5879167814,123456789
#
# ==========================================================


DEFAULT_ADMIN_IDS = "5879167814"


admin_ids = os.environ.get(
    "ADMIN_IDS",
    DEFAULT_ADMIN_IDS
)


ADMIN_IDS = [
    int(user_id.strip())
    for user_id in admin_ids.split(",")
    if user_id.strip().isdigit()
]


# ==========================================================
# DEBUG
# ==========================================================

if not BOT_TOKEN:
    print(
        "WARNING: BOT_TOKEN is not set"
    )


print(
    f"Loaded Admin IDs: {ADMIN_IDS}"
)
