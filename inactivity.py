import sqlite3
import logging

from datetime import datetime, timedelta

from config import DB_FILE


# ==========================
# SETTINGS
# ==========================

INACTIVE_DAYS = 30



# ==========================
# TRACK MEMBER ACTIVITY
# ==========================

async def track_activity(update, context):

    message = update.effective_message

    if not message or not message.from_user:
        return


    user = message.from_user


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO user_activity
        (
            user_id,
            username,
            last_seen
        )
        VALUES (?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            last_seen = excluded.last_seen
        """,
        (
            user.id,
            user.first_name,
            datetime.now().isoformat()
        )
    )


    conn.commit()
    conn.close()



# ==========================
# CHECK INACTIVE MEMBERS
# ==========================

async def check_inactive_members(app):

    cutoff = datetime.now() - timedelta(
        days=INACTIVE_DAYS
    )


    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT user_id, username
        FROM user_activity
        WHERE last_seen < ?
        """,
        (
            cutoff.isoformat(),
        )
    )


    users = cursor.fetchall()


    for user_id, username in users:

        try:

            await app.bot.send_message(
                chat_id=user_id,
                text=(
                    "💜 Melanated AZ Check-In\n\n"
                    "Hey! We noticed you haven't been active "
                    "in the community recently.\n\n"
                    "We just wanted to check in and see if "
                    "you would like to continue being part "
                    "of the group.\n\n"
                    "No action is needed — we appreciate "
                    "having you here! 💜"
                )
            )


            logging.info(
                "Sent inactivity message to %s",
                username
            )


        except Exception as e:

            logging.warning(
                "Could not message %s: %s",
                username,
                e
            )


    conn.close()
