"""Safe social-profile publishing/recovery.

Existing member profile messages are preserved. A new Telegram message is
created only when Telegram explicitly reports that the stored message is gone.
Transient API/network/permission failures never trigger a duplicate post.
"""

import logging

from telegram.error import TelegramError

logger = logging.getLogger("melanated_az_social_recovery_patch")


def _message_is_gone(exc):
    text = str(exc).lower()
    return any(
        phrase in text
        for phrase in (
            "message to edit not found",
            "message not found",
            "message identifier is not valid",
            "message_id_invalid",
        )
    )


async def safe_publish_member_profile(bot, user_id):
    import social_media

    rows = social_media._get_user_links(user_id)
    if not rows:
        return

    text = social_media._topic_profile_text(rows)
    markup = social_media._topic_profile_keyboard(rows)
    message_id = rows[0]["topic_message_id"]

    if message_id:
        try:
            await bot.edit_message_text(
                chat_id=social_media.CHAT_ID,
                message_id=int(message_id),
                text=text,
                reply_markup=markup,
                parse_mode="HTML",
            )
            return
        except TelegramError as exc:
            if "message is not modified" in str(exc).lower():
                logger.debug("Social profile already current; no edit needed | user_id=%s message=%s", user_id, message_id)
                return
            if not _message_is_gone(exc):
                logger.warning(
                    "Social profile edit failed; NOT reposting | user_id=%s message=%s error=%s",
                    user_id,
                    message_id,
                    exc,
                )
                return
            logger.info(
                "Stored social profile message is gone; recreating | user_id=%s old_message=%s",
                user_id,
                message_id,
            )

    try:
        message = await bot.send_message(
            chat_id=social_media.CHAT_ID,
            message_thread_id=social_media.TOPIC_ID,
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
        )
        with social_media._connect() as conn:
            conn.execute(
                "UPDATE social_links SET topic_message_id=? WHERE user_id=?",
                (message.message_id, user_id),
            )
            conn.commit()
        logger.info(
            "Social profile recreated | user_id=%s message=%s topic=%s",
            user_id,
            message.message_id,
            social_media.TOPIC_ID,
        )
    except TelegramError:
        logger.exception("Unable to recreate social profile | user_id=%s", user_id)


def install():
    import social_media
    social_media._publish_member_profile = safe_publish_member_profile
    logger.info("Safe Social Media profile recovery/publishing enabled")


install()
