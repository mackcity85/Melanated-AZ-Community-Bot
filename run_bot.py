# ==========================================================
# Melanated AZ Bot launcher
# run_bot.py
#
# Adds the shared Question of the Day / After Dark controls
# without replacing the existing bot.py admin system.
#
# Shared destination:
#   Chat  : -1002697105809
#   Topic : 11999
#
# After Dark:
#   Daily: 10:30 AM Arizona time
# ==========================================================

import bot
import admin as admin_module

from topic_routing import install_all_topic_routing, TARGET_CHAT_ID, TARGET_TOPIC_ID

# Install routing before question_of_day.py is imported.
install_all_topic_routing()

from question_of_day import (
    ensure_qotd_submission_panel,
    register_question_of_day_handlers,
    start_question_of_day_scheduler,
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler


# ==========================================================
# ADMIN PANEL EXTENSION
# ==========================================================

_original_admin_keyboard = admin_module.admin_main_keyboard
_original_admin_menu_text = admin_module.admin_menu_text


def _admin_keyboard_with_questions():
    base = _original_admin_keyboard()
    rows = [list(row) for row in base.inline_keyboard]

    # Put the new controls immediately before Refresh.
    insert_at = len(rows)
    for index, row in enumerate(rows):
        if any(getattr(button, "callback_data", None) == "admin_refresh" for button in row):
            insert_at = index
            break

    rows[insert_at:insert_at] = [
        [InlineKeyboardButton("💭 Questions / QOTD", callback_data="admin_questions")],
        [InlineKeyboardButton("🌙 After Dark", callback_data="admin_after_dark")],
    ]

    return InlineKeyboardMarkup(rows)


def _admin_menu_text_with_questions():
    return (
        _original_admin_menu_text()
        + "\n\n"
        "💭 **QUESTIONS / QOTD**\n"
        "Manage the QOTD bank and shared question topic.\n\n"
        "🌙 **AFTER DARK**\n"
        "Dedicated After Dark content posts daily at **10:30 AM Arizona time**."
    )


admin_module.admin_main_keyboard = _admin_keyboard_with_questions
admin_module.admin_menu_text = _admin_menu_text_with_questions


# ==========================================================
# QUESTION CONTENT ADMIN CALLBACKS
# ==========================================================

async def _admin_question_content_callback(update, context):
    query = update.callback_query
    if not query:
        return

    data = query.data or ""

    # The existing admin_callback_router will perform its own authorization.
    # We also enforce it here because this handler runs before the generic
    # admin router (group -1).
    if not await admin_module.is_admin(update.effective_user.id, context):
        await query.answer("⛔ You are not authorized.", show_alert=True)
        return

    if data == "admin_questions":
        await query.answer()
        try:
            from question_of_day import queued_count, daily_post_already_done, qotd_enabled
            count = queued_count()
            posted = daily_post_already_done()
            enabled = qotd_enabled()
        except Exception:
            count, posted, enabled = 0, False, False

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 QOTD Bank Status", callback_data="admin_qotd_status")],
            [InlineKeyboardButton("▶️ Post Next QOTD Now", callback_data="admin_qotd_post_next")],
            [InlineKeyboardButton("📌 Recreate QOTD Panel", callback_data="admin_qotd_panel")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")],
        ])

        await query.edit_message_text(
            "💭 **QUESTION OF THE DAY**\n\n"
            f"📚 Queued: **{count} day{'s' if count != 1 else ''}**\n"
            f"📅 Today's post: **{'Posted' if posted else 'Not posted'}**\n"
            f"⚙️ System: **{'Enabled' if enabled else 'Not configured'}**\n\n"
            f"📍 Destination: `{TARGET_CHAT_ID}` / topic `{TARGET_TOPIC_ID}`",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        return

    if data == "admin_qotd_status":
        await query.answer()
        try:
            from question_of_day import queued_count, daily_post_already_done
            count = queued_count()
            posted = daily_post_already_done()
        except Exception:
            count, posted = 0, False

        await query.edit_message_text(
            "📚 **QOTD BANK STATUS**\n\n"
            f"Queued items: **{count}**\n"
            f"Today's QOTD: **{'Posted' if posted else 'Not posted'}**\n\n"
            "QOTD questions and polls use their own bank; After Dark remains separate.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_questions")],
                [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return

    if data == "admin_qotd_post_next":
        await query.answer("Posting next QOTD...")
        try:
            from question_of_day import publish_item, get_next_item
            item = get_next_item()
            if not item:
                text = "📚 **QOTD BANK EMPTY**\n\nThere is nothing queued to post."
            else:
                posted = await publish_item(context, int(item["id"]))
                text = (
                    "✅ **QOTD POSTED**\n\nThe next queued Question/Poll was posted to topic `11999`."
                    if posted else
                    "❌ **QOTD POST FAILED**\n\nCheck the Render logs."
                )
        except Exception:
            text = "❌ **QOTD POST FAILED**\n\nCheck the Render logs."

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💭 QOTD Controls", callback_data="admin_questions")],
                [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return

    if data == "admin_qotd_panel":
        await query.answer("Recreating QOTD panel...")
        try:
            await ensure_qotd_submission_panel(context.application)
            text = "📌 **QOTD PANEL READY**\n\nThe submission panel was created/re-pinned in topic `11999`."
        except Exception:
            text = "❌ **QOTD PANEL FAILED**\n\nCheck the Render logs."

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💭 QOTD Controls", callback_data="admin_questions")],
                [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return

    if data == "admin_after_dark":
        await query.answer()
        await query.edit_message_text(
            "🌙 **AFTER DARK**\n\n"
            "After Dark uses its own content bank and posts into the shared QOTD topic.\n\n"
            "🕥 **Daily:** 10:30 AM Arizona time\n"
            f"📍 **Destination:** `{TARGET_CHAT_ID}` / topic `{TARGET_TOPIC_ID}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🕥 Confirm 10:30 Schedule", callback_data="admin_after_dark_schedule")],
                [InlineKeyboardButton("🌙 Post After Dark Now", callback_data="admin_after_dark_now")],
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return

    if data == "admin_after_dark_schedule":
        await query.answer("Schedule confirmed")
        await query.edit_message_text(
            "🕥 **AFTER DARK SCHEDULE**\n\n"
            "Daily at **10:30 AM Arizona time**.\n\n"
            f"Posts to chat `{TARGET_CHAT_ID}`, topic `{TARGET_TOPIC_ID}`.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌙 After Dark Controls", callback_data="admin_after_dark")],
                [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return

    if data == "admin_after_dark_now":
        await query.answer("Posting After Dark...")
        try:
            from daily_messages import send_daily_community_message
            await send_daily_community_message(context)
            text = "🌙 **AFTER DARK POSTED**\n\nThe current After Dark prompt was posted to topic `11999`."
        except Exception:
            text = "❌ **AFTER DARK POST FAILED**\n\nCheck the Render logs."

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌙 After Dark Controls", callback_data="admin_after_dark")],
                [InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )
        return


async def _qotd_panel_startup_job(context):
    await ensure_qotd_submission_panel(context.application)


_original_build_application = bot.build_application


def build_application_with_qotd():
    application = _original_build_application()

    # Specific question-content callbacks must run before bot.py's generic
    # ^admin_ callback router.
    application.add_handler(
        CallbackQueryHandler(
            _admin_question_content_callback,
            pattern=r"^admin_(questions|qotd_|after_dark)",
        ),
        group=-1,
    )

    register_question_of_day_handlers(application)
    start_question_of_day_scheduler(application)

    if application.job_queue:
        application.job_queue.run_once(
            _qotd_panel_startup_job,
            when=2,
            name="qotd-submission-panel-startup",
        )

    return application


bot.build_application = build_application_with_qotd


if __name__ == "__main__":
    bot.main()
