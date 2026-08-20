import os


def required_env(name):
    value = os.getenv(name)

    if not value or not value.strip():
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value.strip()


# ==========================================================
# TELEGRAM
# ==========================================================

BOT_TOKEN = required_env("BOT_TOKEN")


# ==========================================================
# ADMIN IDS
# Render example:
# ADMIN_IDS=5879167814
# Multiple:
# ADMIN_IDS=5879167814,123456789
# ==========================================================

ADMIN_IDS = [
    int(x.strip())
    for x in required_env("ADMIN_IDS").split(",")
    if x.strip()
]


# ==========================================================
# PAYMENT INFORMATION
# ==========================================================

CASHAPP_TAG = os.getenv(
    "CASHAPP_TAG",
    ""
).strip()

CASHAPP_URL = os.getenv(
    "CASHAPP_URL",
    ""
).strip()

ZELLE_PHONE = os.getenv(
    "ZELLE_PHONE",
    ""
).strip()


print(f"Loaded Admin IDs: {ADMIN_IDS}")

print(
    "💳 Cash App: Loaded"
    if CASHAPP_TAG
    else "💳 Cash App: Not configured"
)

print(
    "💳 Zelle: Loaded"
    if ZELLE_PHONE
    else "💳 Zelle: Not configured"
)
