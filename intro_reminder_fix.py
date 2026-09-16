"""Reliable private reminders for members who still need an introduction.

The existing reminder job can only deliver a Telegram private message to a
member who has previously opened the bot. This module retries eligible
members regularly, logs delivery failures instead of hiding them, and also
nudges an eligible member when they open the bot.
"""

import logging
from datetime import timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

import bot

logger = logging.getLogger("melanated_az_intro_reminders")

JOB_NAME = "monthly-intro-reminders-fixed"
INITIAL_JOB_NAME = "monthly-intro-reminders-fixed-initial"


def _eligible_rows():
    main = bot.configured_main_group_id()
    if not main:
        return []
    now = bot.utc_now()
    cutoff = now - timedelta(days=30)
    with bot.community_db_connect() as conn:
        return conn.execute(
            """SELECT * FROM community_members
               WHERE chat_id=?
                 AND status NOT IN ('left','removed')
                 AND (intro_text IS NULL OR TRIM(intro_text)='')
                 AND (monthly_intro_reminder_at IS NULL
                      OR monthly_intro_reminder_at<=?)""",
            (main, cutoff.isoformat()),
        ).fetchall()


async def send_intro_reminders(context):
    main = bot.configured_main_group_id()
    if not main:
        logger.warning("Intro reminder skipped: MAIN_GROUP_ID is not configured.")
        return

    rows = _eligible_rows()
    logger.info("Intro reminder sweep started | eligible=%s", len(rows))

    bot_username = context.application.bot_data.get("bot_username")
    if not bot_username:
        try:
            me = await context.bot.get_me()
            bot_username = me.username
            if bot_username:
                context.application.bot_data["bot_username"] = bot_username
        except Exception:
            logger.exception("Could not get bot username for intro reminder links.")

    now = bot.utc_now()
    for row in rows:
        uid = int(row["user_id"])
        try:
            live = await context.bot.get_chat_member(main, uid)
            status = getattr(live, "status", "")
            if status not in {"member", "administrator", "creator"}:
                logger.info("Intro reminder skipped | user_id=%s | live_status=%s", uid, status)
                continue
            if await bot.is_admin(uid, context):
                continue

            first_name = (
                getattr(getattr(live, "user", None), "first_name", None)
                or row["first_name"]
                or "there"
            )
            keyboard = None
            if bot_username:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "👋🏾 Complete My Intro",
                        url=f"https://t.me/{bot_username}?start=intro",
                    )]
                ])

            text = (
                f"👋🏾 <b>Hey {bot.html.escape(first_name)}!</b> 💜\n\n"
                "We’d love to get to know you a little better. Your introduction is "
                "still missing, and it’s required for everyone in the Melanated AZ community.\n\n"
                "It only takes a few minutes and helps everyone know who’s part of the community.\n\n"
                "🎂 <b>Birthday is optional</b>, but if you add yours, we’ll make sure "
                "you get a birthday shoutout! 🎉\n\n"
                "Whenever you’re ready, tap below to complete your intro. 👇🏾"
            )

            await context.bot.send_message(
                chat_id=uid,
                text=text,
                reply_markup=keyboard,
                parse_mode=bot.ParseMode.HTML,
            )
            with bot.community_db_connect() as conn:
                conn.execute(
                    "UPDATE community_members SET monthly_intro_reminder_at=? "
                    "WHERE chat_id=? AND user_id=?",
                    (now.isoformat(), main, uid),
                )
                conn.commit()
            logger.info("Intro reminder delivered | user_id=%s", uid)

        except TelegramError as exc:
            # Do not update monthly_intro_reminder_at on failure. This leaves
            # the member eligible for the next sweep, including after they
            # open the bot and make private messaging possible.
            logger.warning("Intro reminder not delivered | user_id=%s | error=%s", uid, exc)
        except Exception:
            logger.exception("Intro reminder failed | user_id=%s", uid)


async def remind_on_private_start(update, context):
    """When an eligible member opens the bot, give them the intro link."""
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat or chat.type != "private" or user.is_bot:
        return
    if getattr(update, "message", None) and getattr(update.message, "text", "").startswith("/start "):
        return

    main = bot.configured_main_group_id()
    row = bot.community_member(main, user.id) if main else None
    if not row or row["status"] in {"left", "removed"} or row["intro_text"]:
        return
    if not row["verified_at"]:
        return

    try:
        await bot.send_private_intro_prompt(user, context)
    except TelegramError:
        logger.info("Could not send intro prompt on private /start | user_id=%s", user.id)


def _cancel_old_jobs(application):
    if not application.job_queue:
        return False
    cancelled = 0
    for name in ("monthly-intro-reminders", "monthly-intro-reminders-initial"):
        for job in application.job_queue.get_jobs_by_name(name):
            job.schedule_removal()
            cancelled += 1
    return cancelled


def _patch_post_init():
    original = bot.post_init
    if getattr(original, "_intro_reminder_fix_wrapped", False):
        return

    async def wrapped_post_init(application):
        await original(application)
        cancelled = _cancel_old_jobs(application)
        if not application.job_queue:
            logger.error("Intro reminders NOT started: JobQueue is unavailable.")
            return
        application.job_queue.run_once(
            send_intro_reminders,
            when=15,
            name=INITIAL_JOB_NAME,
        )
        # Check hourly so a member who starts the bot later can be reached
        # without waiting for a particular calendar day. Each member is still
        # limited to one successful reminder every 30 days by the DB timestamp.
        application.job_queue.run_repeating(
            send_intro_reminders,
            interval=60 * 60,
            first=60 * 60,
            name=JOB_NAME,
        )
        logger.info(
            "Fixed intro reminders enabled | cancelled_old_jobs=%s | initial=15s | sweep=hourly | per-member=30d",
            cancelled,
        )

    wrapped_post_init._intro_reminder_fix_wrapped = True
    bot.post_init = wrapped_post_init


def _patch_start_command():
    original = bot.start_command
    if getattr(original, "_intro_reminder_fix_wrapped", False):
        return

    async def wrapped_start_command(update, context):
        await original(update, context)
        try:
            await remind_on_private_start(update, context)
        except Exception:
            logger.exception("Private-start intro reminder failed.")

    wrapped_start_command._intro_reminder_fix_wrapped = True
    bot.start_command = wrapped_start_command


_patch_post_init()
_patch_start_command()
