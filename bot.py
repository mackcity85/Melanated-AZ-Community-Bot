# ==========================================================
# Melanated AZ Bot v2.0
# Part 1 - Foundation
# ==========================================================

import os
import logging
import sqlite3
import asyncio
from datetime import datetime
from threading import Thread

from dotenv import load_dotenv
from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    JobQueue,
    filters
)


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN environment variable is missing"
    )


# ==========================================================
# LOGGING
# ==========================================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/bot.log",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)

logging.getLogger("").addHandler(console)

logger = logging.getLogger(__name__)


# ==========================================================
# DATABASE
# ==========================================================

os.makedirs("database", exist_ok=True)

DB_FILE = "database/bot.db"


def get_db():

    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )

    return conn


def initialize_database():

    conn = get_db()
    cursor = conn.cursor()


    # Members

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (

        user_id INTEGER PRIMARY KEY,

        username TEXT,

        first_name TEXT,

        joined_date TEXT,

        last_active TEXT,

        chat_id INTEGER

    )
    """)


    # Birthdays

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays (

        user_id INTEGER PRIMARY KEY,

        birthday TEXT,

        username TEXT

    )
    """)


    # Statistics

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (

        name TEXT PRIMARY KEY,

        value INTEGER DEFAULT 0

    )
    """)


    default_stats = [

        ("photos_removed", 0),

        ("videos_removed", 0),

        ("birthdays_saved", 0)

    ]


    for stat in default_stats:

        cursor.execute(
            """
            INSERT OR IGNORE INTO stats
            (name,value)
            VALUES (?,?)
            """,
            stat
        )


    conn.commit()
    conn.close()


    logger.info(
        "Database initialized"
    )



# ==========================================================
# FLASK HEALTH CHECK
# ==========================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def health():

    return (
        "🔥 Melanated AZ Bot v2.0 is running"
    )



def run_flask():

    flask_app.run(

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                10000
            )
        )

    )


# ==========================================================
# BASIC CONFIGURATION
# ==========================================================

BOT_NAME = "Melanated AZ Bot"

START_TIME = datetime.now()


logger.info(
    f"{BOT_NAME} loading..."
)
# ==========================================================
# PART 2 - COMMAND SYSTEM
# ==========================================================


RULES_MESSAGE = """
👑 Welcome to Melanated AZ 👑

This space was created for networking, good vibes, and meeting like-minded adults.

Please introduce yourself and review the pinned messages.

📸 Profile picture required.

Include:

• Name
• Age
• Location
• Status
• What you're here for
• DMs Open or Closed

Example:

King | 40 | Vail, AZ | Partnered | Networking and meeting like-minded people | DMs Open


━━━━━━━━━━━━━━━

📜 GROUP RULES 📜


1️⃣ Consent Is Everything

• No means no.
• Respect boundaries.
• No pressure, manipulation, or guilt trips.


2️⃣ Respect Everyone

• No bullying.
• No harassment.
• Different lifestyles and dynamics are welcome.


3️⃣ Keep Drama Out

• Handle personal issues privately.
• Contact admins when needed.


4️⃣ Privacy Matters

• What is shared here stays here.
• No screenshots or sharing conversations without permission.


5️⃣ Adults Only

• All members must be 18+.


6️⃣ No Unsolicited Messages

• Ask before sending DMs.
• Respect someone's answer.


7️⃣ Verify Before You Trust

• Take your time getting to know people.
• Prioritize safety.


8️⃣ No Predatory Behavior

• Manipulation, coercion, intimidation, or abuse will not be tolerated.


9️⃣ Keep It Classy

• Adult conversations are welcome.
• Avoid spam and excessive explicit content.


🔟 Community First

• Support each other.
• Welcome newcomers.


━━━━━━━━━━━━━━━

🔒 SPOILER MEDIA RULES

Photos and videos must use:

👁 Hide With Spoiler


📱 Mobile:

1. Select photo/video
2. Open options
3. Select Hide With Spoiler
4. Send


💻 Desktop:

1. Select media
2. Right-click preview
3. Choose Hide With Spoiler


━━━━━━━━━━━━━━━

👑 ADMIN RULE

Admins may remove anyone who negatively impacts the safety, privacy, or atmosphere of the group.


Consent • Respect • Communication • Accountability
"""


HELP_MESSAGE = """
👑 Melanated AZ Bot Commands

/community

/rules
Show group rules

/intro
How to introduce yourself

/spoiler
How to send hidden media

/birthday MM/DD
Save your birthday

/birthdays
View upcoming birthdays

/status
Bot status

/getid
Show chat ID
"""


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.message:

        await update.message.reply_text(
            HELP_MESSAGE
        )



async def rules_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        RULES_MESSAGE
    )



async def intro_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
👑 Introduce Yourself 👑

Please include:

Name:
Age:
Location:
Status:
What you're here for:
DMs Open or Closed:

Example:

King | 40 | Vail AZ | Partnered | Networking | DMs Open
"""
    )



async def spoiler_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
👁 How To Send Spoiler Media

📱 Mobile:

1. Choose your photo/video
2. Open media options
3. Select "Hide With Spoiler"
4. Send


💻 Desktop:

1. Attach your media
2. Right-click preview
3. Select "Hide With Spoiler"
4. Send


All photos and videos must use spoilers.
"""
    )



async def getid_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"Chat ID: {update.effective_chat.id}"
    )



async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM members"
    )

    members = cursor.fetchone()[0]

    conn.close()


    await update.message.reply_text(
        f"""
🤖 Melanated AZ Bot

Status: Online

Members Tracked:
{members}

Database:
Connected

Started:
{START_TIME}
"""
    )
    





    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT birthday, username
        FROM birthdays
        ORDER BY birthday
        """
    )


    results = cursor.fetchall()

    conn.close()


    if not results:

        await update.message.reply_text(
            "No birthdays saved yet."
        )

        return


    message = "🎂 Upcoming Birthdays\n\n"


    for birthday, username in results:

        name = username or "Member"

        message += (
            f"🎉 {name} - {birthday}\n"
        )


    await update.message.reply_text(
        message
    )



def update_activity(user, chat_id):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT OR REPLACE INTO members
        VALUES (?,?,?,?,?,?)
        """,
        (
            user.id,
            user.username,
            user.first_name,
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d"),
            chat_id
        )
    )


    conn.commit()
    conn.close()
# ==========================================================
# STATUS COMMAND
# ==========================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM members"
    )

    members = cursor.fetchone()[0]

    conn.close()


    await update.message.reply_text(
        f"""
🤖 Melanated AZ Bot

Status: Online ✅

Members Tracked:
{members}

Database:
Connected ✅

Started:
{START_TIME}
"""
    )

# ==========================================================
# UPDATE MEMBER ACTIVITY
# ==========================================================

def update_activity(user, chat_id):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT OR REPLACE INTO members
        VALUES (?,?,?,?,?,?)
        """,
        (
            user.id,
            user.username,
            user.first_name,
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d"),
            chat_id
        )
    )


    conn.commit()
    conn.close()
# ==========================================================
# PART 3 - WELCOME SYSTEM & MEDIA PROTECTION
# ==========================================================


WELCOME_MESSAGE = """
👑 Welcome to Melanated AZ 👑

This space was created for networking, connection, good energy, and meeting like-minded adults.

Before participating:

📸 Profile picture required

Please introduce yourself:

• Name
• Age
• Location
• Status
• What you're here for
• DMs Open or Closed


━━━━━━━━━━━━━━━

⚠️ MEDIA SPOILER REQUIREMENT ⚠️

All photos and videos must be sent using:

👁 Hide With Spoiler


📱 Mobile:

1. Select photo/video
2. Open media options
3. Choose "Hide With Spoiler"
4. Send


💻 Desktop:

1. Select media
2. Right-click preview
3. Choose "Hide With Spoiler"
4. Send


━━━━━━━━━━━━━━━

Remember:

Consent • Respect • Communication • Accountability

Enjoy the room! ❤️👑
"""



MEDIA_WARNING = """
⚠️ Sorry, your media was removed!⚠️

For everyone's security photos and videos in Melanated AZ must be sent using:

👁 Hide With Spoiler


📱 Mobile:

1️⃣ Select your photo or video
2️⃣ Tap the ⋮ (three dots) menu
3️⃣ Select "Hide With Spoiler"
4️⃣ Send your media


💻 Desktop:

1️⃣ Attach your photo or video
2️⃣ Right-click the media preview
3️⃣ Select "Hide With Spoiler"
4️⃣ Send your media


Thank you for helping keep Melanated AZ comfortable and respectful for everyone. 👑

Consent • Respect • Communication • Accountability
"""

# ==========================================================
# AUTO DELETE WARNING MESSAGE
# ==========================================================

async def send_temporary_warning(
    context,
    chat_id
):

    try:

        warning = await context.bot.send_message(

            chat_id=chat_id,

            text=MEDIA_WARNING

        )


        logger.info(
            "Media warning sent"
        )


        await asyncio.sleep(60)


        try:

            await context.bot.delete_message(

                chat_id=chat_id,

                message_id=warning.message_id

            )


            logger.info(
                "✅ Media warning deleted after 60 seconds"
            )


        except Exception as e:

            logger.error(
                f"❌ Warning delete failed: {e}"
            )


    except Exception as e:

        logger.error(
            f"❌ Warning send failed: {e}"
        )
# ==========================================================
# WELCOME NEW MEMBERS
# ==========================================================

async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.chat_member:
        return


    member = update.chat_member.new_chat_member


    if member.status == "member":

        user = member.user


        await context.bot.send_message(

            chat_id=update.effective_chat.id,

            text=WELCOME_MESSAGE

        )


        update_activity(

            user,

            update.effective_chat.id

        )


        logger.info(

            f"Welcomed {user.id}"

        )
# ==========================================================
# TRACK ALL MEMBER ACTIVITY
# ==========================================================


async def track_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user:

        update_activity(

            update.effective_user,

            update.effective_chat.id

        )



# ==========================================================
# ADMIN CHECK
# ==========================================================


async def is_admin(
    update,
    context
):

    try:

        member = await context.bot.get_chat_member(

            update.effective_chat.id,

            update.effective_user.id

        )


        return member.status in [

            "administrator",

            "creator"

        ]

    except:

        return False



# ==========================================================
# MEDIA SPOILER PROTECTION
# PHOTOS AND VIDEOS
# ==========================================================


async def media_protection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    if not message:
        return


    media_type = None


    if message.photo:

        media_type = "PHOTO"


    elif message.video:

        media_type = "VIDEO"


    else:

        return



    spoiler = getattr(
        message,
        "has_media_spoiler",
        False
    )


    logger.info(
        f"{media_type} RECEIVED | Spoiler={spoiler}"
    )



    # Allow spoiler media

    if spoiler:

        logger.info(
            f"{media_type} ALLOWED | Spoiler"
        )

        return



    # Allow admins

    if await is_admin(update, context):

        logger.info(
            f"{media_type} ALLOWED | Admin"
        )

        return



    try:

        await message.delete()


        logger.info(
            f"{media_type} REMOVED | No Spoiler"
        )


        conn = get_db()

        cursor = conn.cursor()


        if media_type == "PHOTO":

            cursor.execute(
                """
                UPDATE stats
                SET value=value+1
                WHERE name='photos_removed'
                """
            )

        else:

            cursor.execute(
                """
                UPDATE stats
                SET value=value+1
                WHERE name='videos_removed'
                """
            )


        conn.commit()

        conn.close()



        await send_temporary_warning(

            context,

            update.effective_chat.id

        )


    except Exception as e:

        logger.error(
            f"{media_type} ERROR: {e}"
        )
# ==========================================================
# PART 4 - SCHEDULER, STARTUP & MAIN BOT
# ==========================================================


from telegram.ext import JobQueue



# ==========================================================
# BIRTHDAY SYSTEM (MM/DD FORMAT)
# ==========================================================

async def birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    if not context.args:

        await update.message.reply_text(
            """
🎂 Birthday Setup

Use:

/birthday MM/DD

Example:

/birthday 07/25
"""
        )

        return


    birthday = context.args[0]


    try:

        datetime.strptime(
            birthday,
            "%m/%d"
        )


    except ValueError:

        await update.message.reply_text(
            """
❌ Invalid format.

Please use:

/birthday MM/DD

Example:

/birthday 07/25
"""
        )

        return



    user = update.effective_user


    username = (
        user.username
        or user.first_name
        or "Member"
    )


    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT OR REPLACE INTO birthdays
        (
            user_id,
            birthday,
            username
        )
        VALUES (?,?,?)
        """,
        (
            user.id,
            birthday,
            username
        )
    )


    cursor.execute(
        """
        UPDATE stats
        SET value=value+1
        WHERE name='birthdays_saved'
        """
    )


    conn.commit()
    conn.close()


    await update.message.reply_text(
        f"""
🎂 Birthday saved!

👑 {username}
📅 {birthday}

You have been added to the Melanated AZ birthday list.
"""
    )



# ==========================================================
# VIEW BIRTHDAYS
# ==========================================================

async def birthdays_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT username, birthday
        FROM birthdays
        ORDER BY birthday
        """
    )


    birthdays = cursor.fetchall()

    conn.close()


    if not birthdays:

        await update.message.reply_text(
            "🎂 No birthdays saved yet."
        )

        return


    message = "🎂 Melanated AZ Birthdays 🎂\n\n"


    for username, birthday in birthdays:

        message += (
            f"👑 {username} - {birthday}\n"
        )


    await update.message.reply_text(
        message
    )
# ==========================================================
# DAILY BIRTHDAY CHECK
# ==========================================================


async def birthday_check(
    context: ContextTypes.DEFAULT_TYPE
):

    today = datetime.now().strftime(
        "%m/%d"
    )


    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT username

        FROM birthdays

        WHERE birthday=?
        """,

        (
            today,
        )
    )


    birthdays = cursor.fetchall()


    conn.close()



    chat_id = os.getenv(
        "STARTUP_CHAT_ID"
    )


    if not chat_id:
        logger.warning(
            "STARTUP_CHAT_ID missing. Birthday announcement skipped."
        )
        return



    for birthday in birthdays:

        username = birthday[0] or "Member"


        await context.bot.send_message(

            chat_id=chat_id,

            text=f"""
🎂🎉 Happy Birthday {username}! 🎉🎂

The Melanated AZ family wishes you an amazing birthday!

Enjoy your special day. 👑❤️
"""

        )
# ==========================================================
# COMMUNITY CHECK-IN
# ==========================================================


async def community_check(
    context: ContextTypes.DEFAULT_TYPE
):

    logger.info(
        "Running community check"
    )


    # Future expansion:
    #
    # Find members inactive 30 days
    # Send friendly reminder
    # Thank active members
    #

    return





# ==========================================================
# PIN CLEANUP
# ==========================================================


async def pin_cleanup(
    context: ContextTypes.DEFAULT_TYPE
):

    logger.info(

        "Pin cleanup check completed"

    )


    # Telegram limits pin history access.
    # Framework added for future cleanup rules.





# ==========================================================
# COMMAND LOADER
# ==========================================================


def register_commands(app):


    app.add_handler(

        CommandHandler(

            "help",

            help_command

        )

    )


    app.add_handler(

        CommandHandler(

            "rules",

            rules_command

        )

    )


    app.add_handler(

        CommandHandler(

            "intro",

            intro_command

        )

    )


    app.add_handler(

        CommandHandler(

            "spoiler",

            spoiler_command

        )

    )


    app.add_handler(

        CommandHandler(

            "getid",

            getid_command

        )

    )


    app.add_handler(

        CommandHandler(

            "status",

            status_command

        )

    )


    app.add_handler(

        CommandHandler(

            "birthday",

            birthday_command

        )

    )


    app.add_handler(

        CommandHandler(

            "birthdays",

            birthdays_command

        )

    )


    logger.info(

        "Commands loaded"

    )





# ==========================================================
# STARTUP
# ==========================================================


async def startup(
    app: Application
):


    logger.info(

        "🔥 Melanated AZ Bot Started"

    )


    logger.info(

        "✅ Commands Active"

    )


    logger.info(

        "✅ Welcome System Active"

    )


    logger.info(

        "✅ Media Protection Active"

    )


    logger.info(

        "✅ Birthday System Active"

    )



# ==========================================================
# MAIN
# ==========================================================


def main():


    initialize_database()


    Thread(

        target=run_flask,

        daemon=True

    ).start()



    app = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .post_init(startup)

        .build()

    )



    register_commands(app)



    # Welcome new members

    app.add_handler(

        ChatMemberHandler(

            welcome_new_member,

            ChatMemberHandler.CHAT_MEMBER

        )

    )



    # Track messages

    app.add_handler(

        MessageHandler(

            filters.ALL,

            track_messages

        ),

        group=10

    )



    # ==========================================================
    # PHOTOS AND VIDEOS
    # ==========================================================

    app.add_handler(

        MessageHandler(

            filters.PHOTO | filters.VIDEO,

            media_protection

        ),

        group=1

    )


    # ==========================================================
    # SCHEDULER
    # ==========================================================

    if app.job_queue:

        app.job_queue.run_daily(

            birthday_check,

            time=datetime.strptime(
                "09:00",
                "%H:%M"
            ).time()

        )


        app.job_queue.run_repeating(

            community_check,

            interval=2592000,

            first=60

        )


        app.job_queue.run_repeating(

            pin_cleanup,

            interval=604800,

            first=300

        )


    logger.info(
        "🚀 Starting Telegram polling"
    )


    app.run_polling(

    allowed_updates=[

        Update.MESSAGE,

        Update.CHAT_MEMBER

    ],

    drop_pending_updates=True

)
if __name__ == "__main__":
    main()
