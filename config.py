import os


# ==========================
# TELEGRAM BOT TOKEN
# ==========================

TOKEN = os.environ.get(
    "BOT_TOKEN"
)


# ==========================
# STARTUP MESSAGE CHAT ID
# ==========================

STARTUP_CHAT_ID = os.environ.get(
    "STARTUP_CHAT_ID"
)


# ==========================
# DATABASE
# ==========================

DB_FILE = "melanatedaz.db"


# ==========================
# RAFFLE SETTINGS
# ==========================

RAFFLE_COST = "$5"

RAFFLE_PAYMENT_INFO = """
💰 Raffle Payment Information

Entry Cost:
$5 per entry

Payment Options:

Cash App:
$YOUR_CASHAPP

Venmo:
@YOUR_VENMO

PayPal:
YOUR_PAYPAL

After payment, send confirmation to an admin.
"""


# ==========================
# COMMUNITY SETTINGS
# ==========================

BOT_NAME = "Melanated AZ Community Bot"

COMMUNITY_NAME = "Melanated AZ"
