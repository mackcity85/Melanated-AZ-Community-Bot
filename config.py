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

ADMIN_IDS = []


admin_ids = os.environ.get(
    "ADMIN_IDS",
    ""
)


if admin_ids:

    ADMIN_IDS = [
        int(user_id.strip())
        for user_id in admin_ids.split(",")
        if user_id.strip().isdigit()
    ]


# Local fallback admin
# Remove this after Render ADMIN_IDS is configured

if not ADMIN_IDS:

    ADMIN_IDS = [
        5879167814
    ]
