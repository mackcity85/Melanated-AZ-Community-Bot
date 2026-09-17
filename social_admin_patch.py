"""Admin-only controls for manually reposting saved social profiles.

Automatic social-profile recovery is intentionally disabled. Reposting is now
an explicit admin action from the /admin panel.
"""

import logging

import admin

logger = logging.getLogger("melanated_az_social_admin_patch")


async def _repost_all_social_profiles(update, context):
    if not await admin.require_admin(update, context):
        return

    query = update.callback_query
    if not query:
        return

    try:
        await query.answer("🔄 Reposting social profiles...")
    except Exception:
        pass

    try:
        from social_media import _connect, _get_members, _publish_member_profile, initialize_social_media_database

        initialize_social_media_database()
        members = _get_members()

        if not members:
            await query.edit_message_text(
                "📱 **SOCIAL MEDIA REPOST**\n\n"
                "No saved social profiles were found.",
                reply_markup=admin.InlineKeyboardMarkup([
                    [admin.InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
                ]),
                parse_mode="Markdown",
            )
            return

        # Force a new Telegram message for each saved profile. This is the
        # ONLY path that intentionally clears topic_message_id and creates a
        # fresh copy. Normal member edits continue to update the existing post.
        with _connect() as conn:
            conn.execute("UPDATE social_links SET topic_message_id=NULL")
            conn.commit()

        reposted = 0
        for member in members:
            try:
                await _publish_member_profile(context.bot, int(member["user_id"]))
                reposted += 1
            except Exception:
                logger.exception(
                    "Manual social profile repost failed | user_id=%s",
                    member["user_id"],
                )

        await query.edit_message_text(
            "📱 **SOCIAL MEDIA REPOST COMPLETE**\n\n"
            f"✅ Reposted profiles: **{reposted}**\n\n"
            "Social profiles will NOT be automatically reposted anymore.",
            reply_markup=admin.InlineKeyboardMarkup([
                [admin.InlineKeyboardButton("📱 Repost Again", callback_data="admin_social_repost")],
                [admin.InlineKeyboardButton("⬅️ Back", callback_data="admin_back")],
            ]),
            parse_mode="Markdown",
        )

    except Exception:
        logger.exception("Manual social profile repost failed")
        try:
            await query.edit_message_text(
                "❌ **SOCIAL MEDIA REPOST FAILED**\n\n"
                "Check the Render logs.",
                reply_markup=admin.InlineKeyboardMarkup([
                    [admin.InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
                ]),
                parse_mode="Markdown",
            )
        except Exception:
            pass


def _patched_admin_main_keyboard():
    keyboard = admin._original_admin_main_keyboard()
    rows = list(keyboard.inline_keyboard)
    rows.insert(
        -1,
        [
            admin.InlineKeyboardButton(
                "📱 Repost Social Profiles",
                callback_data="admin_social_repost",
            )
        ],
    )
    return admin.InlineKeyboardMarkup(rows)


async def _patched_admin_button(update, context):
    query = update.callback_query
    if query and query.data == "admin_social_repost":
        await _repost_all_social_profiles(update, context)
        return
    await admin._original_admin_button(update, context)


def install():
    if getattr(admin, "_social_admin_patch_installed", False):
        return

    admin._original_admin_main_keyboard = admin.admin_main_keyboard
    admin._original_admin_button = admin.admin_button
    admin.admin_main_keyboard = _patched_admin_main_keyboard
    admin.admin_button = _patched_admin_button
    admin._social_admin_patch_installed = True
    logger.info("Social admin manual-repost controls installed")


install()
