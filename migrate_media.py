# ==========================================================
# Melanated AZ Bot - Historical Media Migration
#
# Scans topic 1 and copies photos/videos into topic 10286.
# Uses a Telegram USER session (Telethon), not the Bot API,
# because the Bot API cannot browse arbitrary old history.
#
# SAFE DEFAULT: copy only. Originals are NOT deleted.
# ==========================================================

import asyncio
import os
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto


API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ.get("TELEGRAM_SESSION", "melanated_media_migration")

CHAT_ID = int(os.environ.get("MEDIA_MIGRATION_CHAT_ID", "-1002697105809"))
SOURCE_TOPIC_ID = int(os.environ.get("MEDIA_SOURCE_TOPIC_ID", "1"))
TARGET_TOPIC_ID = int(os.environ.get("MEDIA_TARGET_TOPIC_ID", "11999"))

# Leave false for the first run. Set to true only after verifying the copies.
DELETE_ORIGINALS = os.environ.get("MEDIA_DELETE_ORIGINALS", "false").lower() == "true"

# Telegram's forum topic is represented by reply_to in the message history.


def is_photo_or_video(message):
    media = message.media
    if isinstance(media, MessageMediaPhoto):
        return True
    if isinstance(media, MessageMediaDocument):
        document = media.document
        mime = (getattr(document, "mime_type", "") or "").lower()
        return mime.startswith("video/")
    return False


async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()

    entity = await client.get_entity(CHAT_ID)

    scanned = 0
    found = 0
    copied = 0
    skipped = 0
    failed = 0
    deleted = 0

    print(f"Scanning chat={CHAT_ID} topic={SOURCE_TOPIC_ID} -> topic={TARGET_TOPIC_ID}")
    print(f"Delete originals: {DELETE_ORIGINALS}")

    async for message in client.iter_messages(entity, reply_to=SOURCE_TOPIC_ID, reverse=True):
        scanned += 1

        if not is_photo_or_video(message):
            continue

        found += 1
        print(f"MEDIA message_id={message.id} date={message.date} type={type(message.media).__name__}")

        try:
            # send_message with the existing media object preserves the media
            # and caption without downloading/re-uploading the file locally.
            await client.send_message(
                entity,
                message.media,
                message=message.message or "",
                reply_to=TARGET_TOPIC_ID,
            )
            copied += 1

            if DELETE_ORIGINALS:
                await client.delete_messages(entity, [message.id])
                deleted += 1

        except Exception as exc:
            failed += 1
            print(f"FAILED message_id={message.id}: {exc}")

    print("\n========== MIGRATION COMPLETE ==========")
    print(f"Scanned: {scanned}")
    print(f"Media found: {found}")
    print(f"Copied: {copied}")
    print(f"Failed: {failed}")
    print(f"Deleted originals: {deleted}")
    print("========================================")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
