"""Admin-only controls for manually reposting saved social profiles.

Automatic social-profile recovery is intentionally disabled. Reposting is now
an explicit admin action from the /admin panel.
"""

import logging

import admin
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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


def _install_games_admin_compatibility():
    """Keep Admin Panel -> Games working even if an older Game Center module is deployed."""
    try:
        import games.game_center as game_center

        if getattr(game_center, "games_admin_menu", None):
            return

        async def games_admin_menu(update, context):
            query = update.callback_query
            user = update.effective_user

            if not user:
                return

            if not await admin.is_admin(user.id, context):
                if query:
                    try:
                        await query.answer("⛔ You are not authorized.", show_alert=True)
                    except Exception:
                        pass
                return

            if query:
                try:
                    await query.answer()
                except Exception:
                    pass

                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎮 Open Game Center", callback_data="games_home")],
                    [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")],
                ])

                await query.edit_message_text(
                    "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
                    "✅ Admin access confirmed.\n\n"
                    "Use the Game Center below to view and launch the available games.",
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )

        game_center.games_admin_menu = games_admin_menu
        logger.info("Games admin compatibility handler installed")

    except Exception:
        logger.exception("Unable to install Games admin compatibility handler")


def install():
    if getattr(admin, "_social_admin_patch_installed", False):
        _install_games_admin_compatibility()
        return

    admin._original_admin_main_keyboard = admin.admin_main_keyboard
    admin._original_admin_button = admin.admin_button
    admin.admin_main_keyboard = _patched_admin_main_keyboard
    admin.admin_button = _patched_admin_button

    try:
        import bot
        bot.admin_button = _patched_admin_button
    except Exception:
        logger.exception("Unable to patch bot.admin_button reference")

    admin._social_admin_patch_installed = True
    _install_games_admin_compatibility()
    logger.info("Social admin manual-repost controls installed")


install()
