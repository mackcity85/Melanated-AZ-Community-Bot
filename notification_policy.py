import asyncio
import logging
import os
from telegram.ext import ExtBot
from telegram.error import TelegramError
logger = logging.getLogger("melanatedaz.notification_policy")
CLEAN_CHAT_SECONDS = int(os.environ.get("CLEAN_CHAT_SECONDS", "180") or "180")
ADMIN_GROUP_ID_ENV = os.environ.get("ADMIN_GROUP_ID", "") or ""
MAIN_GROUP_ID_ENV = os.environ.get("MAIN_GROUP_ID", "") or ""
PERMANENT_TOPIC_IDS = {8809, 9513, 10286, 11570, 11883, 11999, 12214}
_PATCHED = False
_ORIGINAL_SEND_MESSAGE = None

def _as_int(value, default=0):
    try:return int(value)
    except (TypeError, ValueError):return default

def _admin_group_id():return _as_int(ADMIN_GROUP_ID_ENV, 0)
def _main_group_id():return _as_int(MAIN_GROUP_ID_ENV, 0)
def _is_main_chat(chat_id):return bool(_main_group_id() and _as_int(chat_id)==_main_group_id())
def _is_admin_chat(chat_id):return bool(_admin_group_id() and _as_int(chat_id)==_admin_group_id())
def _is_permanent_launcher(kwargs):return _as_int(kwargs.get("message_thread_id"),0) in PERMANENT_TOPIC_IDS

async def _send_message_with_policy(self,*args,**kwargs):
    sent=await _ORIGINAL_SEND_MESSAGE(self,*args,**kwargs)
    chat_id=kwargs.get("chat_id")
    if chat_id is None and args:chat_id=args[0]
    if not _is_main_chat(chat_id) or _is_admin_chat(chat_id):return sent
    if not _is_permanent_launcher(kwargs) and CLEAN_CHAT_SECONDS>0:
        try:asyncio.create_task(_delete_message_later(self,chat_id,sent.message_id))
        except Exception:logger.exception("Could not schedule clean-chat deletion.")
    return sent

async def _delete_message_later(bot,chat_id,message_id):
    await asyncio.sleep(CLEAN_CHAT_SECONDS)
    try:await bot.delete_message(chat_id=chat_id,message_id=message_id)
    except TelegramError as exc:logger.debug("Clean-chat deletion skipped | chat=%s | message=%s | %s",chat_id,message_id,exc)
    except Exception:logger.exception("Unexpected clean-chat deletion failure | chat=%s | message=%s",chat_id,message_id)

def install_notification_policy():
    global _PATCHED,_ORIGINAL_SEND_MESSAGE
    if _PATCHED:return
    _ORIGINAL_SEND_MESSAGE=ExtBot.send_message
    ExtBot.send_message=_send_message_with_policy
    _PATCHED=True
    logger.info("Clean-chat policy enabled | delete_after=%ss | main_group=%s | permanent_topics=%s",CLEAN_CHAT_SECONDS,_main_group_id(),sorted(PERMANENT_TOPIC_IDS))

install_notification_policy()
