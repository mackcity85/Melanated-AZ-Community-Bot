"""Permanent launcher pins for the Games topic."""
import json
import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .truth_dare_pin import TEXT as TRUTH_DARE_TEXT, KEYBOARD as TRUTH_DARE_KEYBOARD

logger = logging.getLogger("melanated_az.game_topic_pins")

CHAT_ID = -1002697105809
TOPIC_ID = 11999
STATE_DIR = Path("/var/data")
GAME_CENTER_STATE = STATE_DIR / "game_center_pin_11999.json"
DIRTY_MINDS_STATE = STATE_DIR / "dirty_minds_pin_11999.json"
TRUTH_DARE_STATE = STATE_DIR / "truth_dare_games_pin_11999.json"


def _load_id(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        message_id = int(data.get("message_id", 0))
        topic_id = int(data.get("topic_id", 0))
        return message_id if message_id and topic_id == TOPIC_ID else None
    except Exception:
        return None


def _save_id(path, message_id):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"message_id": int(message_id), "topic_id": TOPIC_ID}),
        encoding="utf-8",
    )


async def _verify_pin_permission(bot):
    """Verify the bot can pin messages before trying to maintain the launchers."""
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id=CHAT_ID, user_id=me.id)
        can_pin = getattr(member, "can_pin_messages", None)
        logger.info(
            "Games-topic pin check | chat=%s topic=%s bot=%s status=%s can_pin_messages=%s",
            CHAT_ID,
            TOPIC_ID,
            me.username or me.id,
            getattr(member, "status", None),
            can_pin,
        )
        if can_pin is False:
            logger.error(
                "Games-topic pins cannot be created: bot does not have can_pin_messages "
                "permission in chat %s.",
                CHAT_ID,
            )
    except Exception:
        logger.exception("Unable to verify Games-topic pin permissions.")


async def _pin(bot, message_id, label):
    try:
        await bot.pin_chat_message(
            chat_id=CHAT_ID,
            message_id=message_id,
            disable_notification=True,
        )
        logger.info(
            "Games-topic launcher pinned | label=%s chat=%s topic=%s message=%s",
            label,
            CHAT_ID,
            TOPIC_ID,
            message_id,
        )
        return True
    except Exception:
        logger.exception(
            "FAILED to pin Games-topic launcher | label=%s chat=%s topic=%s message=%s",
            label,
            CHAT_ID,
            TOPIC_ID,
            message_id,
        )
        return False


async def _upsert_pin(bot, path, text, keyboard, label):
    message_id = _load_id(path)

    if message_id:
        try:
            msg = await bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=message_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            await _pin(bot, msg.message_id, label)
            return msg
        except Exception:
            logger.warning(
                "Existing %s launcher could not be updated; creating a fresh launcher in topic %s.",
                label,
                TOPIC_ID,
                exc_info=True,
            )

    msg = await bot.send_message(
        chat_id=CHAT_ID,
        message_thread_id=TOPIC_ID,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    _save_id(path, msg.message_id)
    await _pin(bot, msg.message_id, label)
    return msg


async def ensure_game_topic_pins(bot):
    """Keep three separate member-facing launchers pinned in Games topic 11999."""
    await _verify_pin_permission(bot)

    game_center_text = (
        "🎮🔥 <b>MELANATED AZ GAME CENTER</b> 🔥🎮\n\n"
        "🥊 <b>Fighting</b>\n"
        "🏆 <b>Sports</b>\n"
        "🟥 <b>Nintendo</b>\n"
        "🔵 <b>Sega</b>\n"
        "🟦 <b>PlayStation</b>\n"
        "🟩 <b>Xbox</b>\n\n"
        "👇🏾 <b>Open the Game Center.</b>"
    )
    game_center_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 OPEN GAME CENTER", callback_data="games_home")],
    ])

    dirty_minds_text = (
        "🎭🔥 <b>DIRTY MINDS</b> 🔥🎭\n\n"
        "Multiplayer Dirty Minds for the Melanated AZ community.\n\n"
        "👥 Up to 20 players\n"
        "🛡️ Admin approval required before the game starts\n"
        "🎮 The host starts the approved room\n\n"
        "👇🏾 <b>Request a Dirty Minds game.</b>"
    )
    dirty_minds_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎭 START DIRTY MINDS", callback_data="games_dirty_minds_start")],
    ])

    await _upsert_pin(
        bot,
        GAME_CENTER_STATE,
        game_center_text,
        game_center_keyboard,
        "Game Center",
    )
    await _upsert_pin(
        bot,
        DIRTY_MINDS_STATE,
        dirty_minds_text,
        dirty_minds_keyboard,
        "Dirty Minds",
    )
    await _upsert_pin(
        bot,
        TRUTH_DARE_STATE,
        TRUTH_DARE_TEXT,
        TRUTH_DARE_KEYBOARD,
        "Truth or Dare",
    )
