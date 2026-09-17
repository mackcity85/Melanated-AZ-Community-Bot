"""Permanent member-facing Truth or Dare panel for the Games topic."""
import json
import logging
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder

logger = logging.getLogger("melanated_az.truth_dare_pin")
CHAT_ID = -1002697105809
TOPIC_ID = 11999
STATE_FILE = Path("/var/data/truth_dare_games_pin_11999.json")
MARKER = "_melanated_az_truth_dare_pin_installed"

TEXT = (
    "🔥 <b>TRUTH OR DARE</b> 🔥\n\n"
    "Ready to play? Pick your vibe and jump in.\n\n"
    "🟢 <b>Mild</b> — fun & flirty\n"
    "🌶️ <b>Spicy</b> — adult-community vibes\n"
    "🔥 <b>Extreme</b> — bold & adventurous\n\n"
    "😈 <b>PASS is always allowed.</b>\n\n"
    "👇🏾 Tap below to start playing."
)

KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔥 START TRUTH OR DARE", callback_data="truthdare_menu")],
])


def _load_id():
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return int(data.get("message_id")) if int(data.get("topic_id", 0)) == TOPIC_ID else None
    except Exception:
        return None


def _save_id(message_id):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"message_id": int(message_id), "topic_id": TOPIC_ID}), encoding="utf-8")


async def ensure_truth_dare_pin(bot):
    message_id = _load_id()
    if message_id:
        try:
            msg = await bot.edit_message_text(chat_id=CHAT_ID, message_id=message_id, text=TEXT, reply_markup=KEYBOARD, parse_mode="HTML")
            await bot.pin_chat_message(chat_id=CHAT_ID, message_id=msg.message_id, disable_notification=True)
            return msg
        except Exception:
            pass
    msg = await bot.send_message(chat_id=CHAT_ID, message_thread_id=TOPIC_ID, text=TEXT, reply_markup=KEYBOARD, parse_mode="HTML")
    _save_id(msg.message_id)
    try:
        await bot.pin_chat_message(chat_id=CHAT_ID, message_id=msg.message_id, disable_notification=True)
    except Exception:
        logger.exception("Could not pin Truth or Dare panel.")
    return msg


_original_build = ApplicationBuilder.build

def _patched_build(self, *args, **kwargs):
    app = _original_build(self, *args, **kwargs)
    if getattr(app, MARKER, False):
        return app
    original_post_init = getattr(app, "post_init", None)

    async def post_init(application):
        if original_post_init:
            await original_post_init(application)
        try:
            if application.job_queue:
                for job in application.job_queue.get_jobs_by_name("truth-dare-games-pin"):
                    job.schedule_removal()
                application.job_queue.run_once(lambda context: ensure_truth_dare_pin(context.bot), when=8, name="truth-dare-games-pin")
            else:
                await ensure_truth_dare_pin(application.bot)
        except Exception:
            logger.exception("Truth or Dare Games-topic pin startup failed.")

    app.post_init = post_init
    setattr(app, MARKER, True)
    return app

if not getattr(ApplicationBuilder, MARKER, False):
    ApplicationBuilder.build = _patched_build
    setattr(ApplicationBuilder, MARKER, True)
